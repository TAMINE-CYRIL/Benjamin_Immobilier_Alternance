from database.connection import get_connection

ANNONCE_FIELDS = """
    id,
    title,
    url,
    city,
    zip_code,
    department,
    price,
    surface,
    rooms,
    price_square_meter,
    score,
    agency,
    source_site,
    type_bien,
    energy_class,
    sale_date,
    visit_date,
    last_seen
"""

SORT_COLUMNS = {
    "score": "score",
    "price": "price",
    "surface": "surface",
    "price_m2": "price_square_meter",
    "last_seen": "last_seen",
}


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
    }


def _build_filters(filters):
    clauses = []
    params = []

    text_filters = {
        "city": "city",
        "zip_code": "zip_code",
        "department": "department",
        "type_bien": "type_bien",
        "source_site": "source_site",
    }
    for key, column in text_filters.items():
        value = filters.get(key)
        if value:
            clauses.append(f"{column} ILIKE %s")
            params.append(f"%{value}%")

    range_filters = [
        ("price_min", "price", ">="),
        ("price_max", "price", "<="),
        ("surface_min", "surface", ">="),
        ("surface_max", "surface", "<="),
        ("score_min", "score", ">="),
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

    sort = SORT_COLUMNS.get(filters.get("sort") or "score", "score")
    direction = "ASC" if filters.get("direction") == "asc" else "DESC"

    count_sql = f"SELECT COUNT(*) FROM annonces {where_sql}"
    data_sql = f"""
        SELECT {ANNONCE_FIELDS}
        FROM annonces
        {where_sql}
        ORDER BY {sort} {direction} NULLS LAST, id DESC
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
        FROM annonces
        WHERE id = %s
        LIMIT 1
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (annonce_id,))
            row = cur.fetchone()

    if not row:
        return None

    return _row_to_annonce(row)

