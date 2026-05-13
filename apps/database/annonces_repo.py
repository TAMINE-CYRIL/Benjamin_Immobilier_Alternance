import unicodedata

from database.connection import get_connection

ANNONCE_FIELDS = """
    a.id,
    a.title,
    a.url,
    a.city,
    a.zip_code,
    a.department,
    a.price,
    a.surface,
    a.rooms,
    a.price_square_meter,
    a.score,
    a.agency,
    a.source_site,
    a.type_bien,
    a.energy_class,
    a.sale_date,
    a.visit_date,
    a.last_seen,
    e.status AS enrichment_status,
    e.latitude,
    e.longitude,
    e.parcel_key,
    e.zonage,
    e.prescriptions,
    e.servitudes,
    e.documents,
    e.error_message AS enrichment_error,
    e.enriched_at,
    e.geocode_status,
    e.cadastre_status,
    e.gpu_status,
    e.geocode_score,
    e.geocode_type,
    e.geocode_query,
    e.diagnostic_message,
    p.contenance AS parcel_surface,
    p.commune_code AS parcel_commune_code
"""

SORT_COLUMNS = {
    "score": "a.score",
    "price": "a.price",
    "surface": "a.surface",
    "price_m2": "a.price_square_meter",
    "last_seen": "a.last_seen",
    "zonage": "e.zonage",
    "relevance": "relevance_rank",
}

SORT_DIRECTIONS = {
    "asc": "ASC",
    "desc": "DESC",
}

ACCENTED_CHARS = "àáâãäåçèéêëìíîïñòóôõöøùúûüýÿ"
UNACCENTED_CHARS = "aaaaaaceeeeiiiinoooooouuuuyy"


def _escape_like(value):
    """
    Remplace les caractères spéciaux dans une chaîne pour une utilisation dans une clause LIKE SQL.
    """
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _normalize_like_pattern(value):
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    tokens = [token for token in "".join(char.lower() if char.isalnum() else " " for char in text).split() if token]
    if not tokens:
        return None
    return "%" + "%".join(_escape_like(token) for token in tokens) + "%"


def _normalized_column_expression(column):
    return (
        "regexp_replace("
        f"translate(lower(COALESCE({column}, '')), %s, %s), "
        "'[^a-z0-9]+', ' ', 'g'"
        ")"
    )


def _fulltext_tsquery(query_text):
    """
    Convertit un texte en tsquery PostgreSQL pour full-text search.
    Utilise plainto_tsquery pour une recherche simple et robuste en français.
    """
    if not query_text or not query_text.strip():
        return None
    return f"plainto_tsquery('french', {repr(query_text)})"


def _row_to_annonce(row):
    """
    Convertit une ligne de résultat en SQL en un dictionnaire d'annonce structuré.
    """
    return {
        "id": row[0],
        "title": row[1],
        "url": row[2],
        "city": row[3],
        "zip_code": row[4],
        "department": row[5],
        "price": row[6],
        "surface": row[7],
        "rooms": row[8],
        "price_m2": row[9],
        "score": row[10],
        "agency": row[11],
        "source_site": row[12],
        "type_bien": row[13],
        "energy_class": row[14],
        "sale_date": row[15],
        "visit_date": row[16],
        "last_seen": row[17],
        "enrichment": {
            "status": row[18] or "pending",
            "latitude": row[19],
            "longitude": row[20],
            "parcel_key": row[21],
            "zonage": row[22],
            "prescriptions": row[23] or [],
            "servitudes": row[24] or [],
            "documents": row[25] or [],
            "error": row[26],
            "enriched_at": row[27],
            "geocode_status": row[28],
            "cadastre_status": row[29],
            "gpu_status": row[30],
            "geocode_score": row[31],
            "geocode_type": row[32],
            "geocode_query": row[33],
            "diagnostic_message": row[34],
            "parcel_surface": row[35],
            "parcel_commune_code": row[36],
        },
    }


def _build_filters(filters):
    """
    Construit les clauses SQL et les paramètres pour la recherche d'annonces en fonction des filtres fournis.
    """
    clauses = []
    params = []

    query = filters.get("query") or filters.get("q")
    if query:
        # Essayer d'abord avec full-text search si search_vector est disponible
        # Sinon, fallback sur recherche ILIKE multi-colonnes
        clauses.append("a.search_vector @@ plainto_tsquery('french', %s)")
        params.append(query)

    city = filters.get("city")
    if city:
        city_pattern = _normalize_like_pattern(city)
        if city_pattern:
            clauses.append(f"{_normalized_column_expression('a.city')} LIKE %s ESCAPE '\\'")
            params.extend([ACCENTED_CHARS, UNACCENTED_CHARS, city_pattern])

    text_filters = {
        "zip_code": "a.zip_code",
        "department": "a.department",
        "type_bien": "a.type_bien",
        "source_site": "a.source_site",
        "zonage": "e.zonage",
    }
    for key, column in text_filters.items():
        value = filters.get(key)
        if value:
            clauses.append(f"{column} ILIKE %s ESCAPE '\\'")
            params.append(f"%{_escape_like(value)}%")

    enrichment_status = filters.get("enrichment_status")
    if enrichment_status:
        clauses.append("COALESCE(e.status, 'pending') = %s")
        params.append(enrichment_status)

    range_filters = [
        ("price_min", "a.price", ">="),
        ("price_max", "a.price", "<="),
        ("surface_min", "a.surface", ">="),
        ("surface_max", "a.surface", "<="),
        ("score_min", "a.score", ">="),
    ]
    for key, column, operator in range_filters:
        value = filters.get(key)
        if value is not None:
            clauses.append(f"{column} {operator} %s")
            params.append(value)

    return clauses, params


def search_annonces(filters):
    """
    Recherche des annonces selon les filtres fournis.
    """
    page = max(filters.get("page") or 1, 1)
    page_size = min(max(filters.get("page_size") or 25, 1), 100)
    offset = (page - 1) * page_size

    clauses, params = _build_filters(filters)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    sort = SORT_COLUMNS.get(filters.get("sort") or "score", SORT_COLUMNS["score"])
    direction = SORT_DIRECTIONS.get(filters.get("direction") or "desc", SORT_DIRECTIONS["desc"])

    joins = """
        LEFT JOIN annonce_enrichments e ON e.annonce_id = a.id
        LEFT JOIN parcelles p ON p.id = e.parcel_id
    """

    # Si tri par pertinence et requête textuelle présente, calculer le rang
    query_text = filters.get("query") or filters.get("q")
    select_fields = ANNONCE_FIELDS
    order_by = f"{sort} {direction} NULLS LAST, a.id DESC"
    
    if sort == "relevance_rank" and query_text:
        # Inclure le calcul de pertinence dans la requête SELECT
        select_fields = f"""
            {ANNONCE_FIELDS},
            ts_rank_cd(a.search_vector, plainto_tsquery('french', %s), 32) as relevance_rank
        """
        order_by = "ts_rank_cd(a.search_vector, plainto_tsquery('french', %s), 32) DESC, a.id DESC"
        # Ajouter les paramètres pour les deux occurrences de ts_rank_cd
        params = params + [query_text, query_text]

    count_sql = f"SELECT COUNT(*) FROM annonces a {joins} {where_sql}"
    data_sql = f"""
        SELECT {select_fields}
        FROM annonces a
        {joins}
        {where_sql}
        ORDER BY {order_by}
        LIMIT %s OFFSET %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(count_sql, params[:-2] if sort == "relevance_rank" and query_text else params)
            total = cur.fetchone()[0]

            cur.execute(data_sql, [*params, page_size, offset])
            rows = cur.fetchall()

    return {
        "items": [_row_to_annonce(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def fetch_annonce_by_id(annonce_id):
    """
    Fetch une annonce par son ID. Retourne None si l'annonce n'existe pas.
    """
    sql = f"""
        SELECT {ANNONCE_FIELDS}
        FROM annonces a
        LEFT JOIN annonce_enrichments e ON e.annonce_id = a.id
        LEFT JOIN parcelles p ON p.id = e.parcel_id
        WHERE a.id = %s
        LIMIT 1
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (annonce_id,))
            row = cur.fetchone()

    if not row:
        return None

    return _row_to_annonce(row)

