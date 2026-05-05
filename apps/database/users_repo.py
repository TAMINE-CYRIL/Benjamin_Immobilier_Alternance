from database.connection import get_connection


def get_user_by_email(email):
    sql = """
        SELECT id, email, password_hash, is_active, created_at, locked_until
        FROM users
        WHERE lower(email) = lower(%s)
        LIMIT 1
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (email,))
            row = cur.fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "email": row[1],
        "password_hash": row[2],
        "is_active": row[3],
        "created_at": row[4],
        "locked_until": row[5],
    }


def get_user_by_id(user_id):
    sql = """
        SELECT id, email, is_active, created_at, locked_until
        FROM users
        WHERE id = %s
        LIMIT 1
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            row = cur.fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "email": row[1],
        "is_active": row[2],
        "created_at": row[3],
        "locked_until": row[4],
    }


def create_user(email, password_hash, is_active=True):
    sql = """
        INSERT INTO users (email, password_hash, is_active)
        VALUES (%s, %s, %s)
        RETURNING id, email, is_active, created_at
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (email, password_hash, is_active))
            row = cur.fetchone()
        conn.commit()

    return {
        "id": row[0],
        "email": row[1],
        "is_active": row[2],
        "created_at": row[3],
    }


def lock_user_for_minutes(user_id, minutes):
    sql = """
        UPDATE users
        SET locked_until = NOW() + (%s * INTERVAL '1 minute')
        WHERE id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (minutes, user_id))
        conn.commit()


def clear_user_lock(user_id):
    sql = """
        UPDATE users
        SET locked_until = NULL
        WHERE id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
        conn.commit()
