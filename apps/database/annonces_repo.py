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
}

SORT_DIRECTIONS = {
    "asc": "ASC",
    "desc": "DESC",
}


def _escape_like(value):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _row_to_annonce(row):
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
    clauses = []
    params = []

    text_filters = {
        "city": "a.city",
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

    count_sql = f"SELECT COUNT(*) FROM annonces a {joins} {where_sql}"
    data_sql = f"""
        SELECT {ANNONCE_FIELDS}
        FROM annonces a
        {joins}
        {where_sql}
        ORDER BY {sort} {direction} NULLS LAST, a.id DESC
        LIMIT %s OFFSET %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(count_sql, params)
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

