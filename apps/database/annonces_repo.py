from database.connection import get_connection

def fetch_all_annonces():
    sql = """
        SELECT
            id,
            title,
            city,
            zip_code,
            price,
            surface,
            price_square_meter,
            score
        FROM annonces
        ORDER BY score DESC
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "title": r[1],
            "city": r[2],
            "zip_code": r[3],
            "price": r[4],
            "surface": r[5],
            "price_m2": r[6],
            "score": r[7],
        }
        for r in rows
    ]

