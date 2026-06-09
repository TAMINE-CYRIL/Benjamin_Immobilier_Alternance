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
    a.first_seen,
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


def _geo_values(filters):
    center_lat = filters.get("center_lat")
    center_lon = filters.get("center_lon")
    radius_km = filters.get("radius_km")
    if center_lat is None or center_lon is None or radius_km is None:
        return None
    return float(center_lat), float(center_lon), float(radius_km) * 1000


def _distance_expression():
    return "ST_Distance(e.location, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography)"


def _row_to_annonce(row, include_distance=False):
    """
    Convertit une ligne de résultat en SQL en un dictionnaire d'annonce structuré.
    """
    annonce = {
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
        "first_seen": row[17],
        "last_seen": row[18],
        "enrichment": {
            "status": row[19] or "pending",
            "latitude": row[20],
            "longitude": row[21],
            "parcel_key": row[22],
            "zonage": row[23],
            "prescriptions": row[24] or [],
            "servitudes": row[25] or [],
            "documents": row[26] or [],
            "error": row[27],
            "enriched_at": row[28],
            "geocode_status": row[29],
            "cadastre_status": row[30],
            "gpu_status": row[31],
            "geocode_score": row[32],
            "geocode_type": row[33],
            "geocode_query": row[34],
            "diagnostic_message": row[35],
            "parcel_surface": row[36],
            "parcel_commune_code": row[37],
        },
    }

    if include_distance:
        annonce["distance_m"] = row[38]

    return annonce


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

    energy_class = filters.get("energy_class")
    if energy_class:
        clauses.append("UPPER(a.energy_class) = %s")
        params.append(energy_class.upper())

    range_filters = [
        ("price_min", "a.price", ">="),
        ("price_max", "a.price", "<="),
        ("surface_min", "a.surface", ">="),
        ("surface_max", "a.surface", "<="),
        ("score_min", "a.score", ">="),
        ("score_max", "a.score", "<="),
        ("rooms_min", "a.rooms", ">="),
        ("rooms_max", "a.rooms", "<="),
        ("price_m2_min", "a.price_square_meter", ">="),
        ("price_m2_max", "a.price_square_meter", "<="),
        ("parcel_surface_min", "p.contenance", ">="),
        ("parcel_surface_max", "p.contenance", "<="),
    ]
    for key, column, operator in range_filters:
        value = filters.get(key)
        if value is not None:
            clauses.append(f"{column} {operator} %s")
            params.append(value)

    has_parcel = filters.get("has_parcel")
    if has_parcel is True:
        clauses.append("e.parcel_id IS NOT NULL")
    elif has_parcel is False:
        clauses.append("e.parcel_id IS NULL")

    recent_days = filters.get("recent_days")
    if recent_days is not None:
        clauses.append("a.first_seen >= CURRENT_TIMESTAMP - (%s * INTERVAL '1 day')")
        params.append(recent_days)

    geo_values = _geo_values(filters)
    if geo_values:
        center_lat, center_lon, radius_m = geo_values
        clauses.append(
            "e.location IS NOT NULL AND "
            "ST_DWithin(e.location, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)"
        )
        params.extend([center_lon, center_lat, radius_m])

    return clauses, params


def search_annonces(filters):
    """
    Recherche des annonces selon les filtres fournis.
    """
    page = max(filters.get("page") or 1, 1)
    page_size = min(max(filters.get("page_size") or 25, 1), 100)
    offset = (page - 1) * page_size

    clauses, where_params = _build_filters(filters)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    sort = SORT_COLUMNS.get(filters.get("sort") or "score", SORT_COLUMNS["score"])
    direction = SORT_DIRECTIONS.get(filters.get("direction") or "desc", SORT_DIRECTIONS["desc"])
    geo_values = _geo_values(filters)

    joins = """
        LEFT JOIN annonce_enrichments e ON e.annonce_id = a.id
        LEFT JOIN parcelles p ON p.id = e.parcel_id
    """

    # Si tri par pertinence et requête textuelle présente, calculer le rang
    query_text = filters.get("query") or filters.get("q")
    select_fields = ANNONCE_FIELDS
    select_params = []
    order_params = []
    include_distance = bool(geo_values)
    order_by = f"{sort} {direction} NULLS LAST, a.id DESC"

    if geo_values:
        center_lat, center_lon, _radius_m = geo_values
        distance_sql = _distance_expression()
        select_fields = f"""
            {select_fields},
            {distance_sql} AS distance_m
        """
        select_params.extend([center_lon, center_lat])

        if filters.get("sort") == "distance":
            order_by = "distance_m ASC NULLS LAST, a.id DESC"
    
    if sort == "relevance_rank" and query_text:
        # Inclure le calcul de pertinence dans la requête SELECT
        select_fields = f"""
            {select_fields},
            ts_rank_cd(a.search_vector, plainto_tsquery('french', %s), 32) as relevance_rank
        """
        order_by = (
            "ts_rank_cd(a.search_vector, plainto_tsquery('french', %s), 32) DESC, "
            "a.score DESC NULLS LAST, a.id DESC"
        )
        select_params.append(query_text)
        order_params.append(query_text)

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
            cur.execute(count_sql, where_params)
            total = cur.fetchone()[0]

            cur.execute(data_sql, [*select_params, *where_params, *order_params, page_size, offset])
            rows = cur.fetchall()

    return {
        "items": [_row_to_annonce(row, include_distance=include_distance) for row in rows],
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
