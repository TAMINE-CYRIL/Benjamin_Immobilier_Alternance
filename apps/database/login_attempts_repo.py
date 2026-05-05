from database.connection import get_connection


def record_login_attempt(email, ip_address, success):
    sql = """
        INSERT INTO login_attempts (email, ip_address, success)
        VALUES (%s, %s, %s)
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (email, ip_address, success))
        conn.commit()


def count_recent_failed_attempts(email, window_minutes):
    sql = """
        SELECT COUNT(*)
        FROM login_attempts
        WHERE lower(email) = lower(%s)
          AND success = FALSE
          AND created_at >= NOW() - (%s * INTERVAL '1 minute')
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (email, window_minutes))
            row = cur.fetchone()

    return row[0] if row else 0


def count_recent_failed_attempts_by_ip(ip_address, window_minutes):
    if not ip_address:
        return 0

    sql = """
        SELECT COUNT(*)
        FROM login_attempts
        WHERE ip_address = %s
          AND success = FALSE
          AND created_at >= NOW() - (%s * INTERVAL '1 minute')
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (ip_address, window_minutes))
            row = cur.fetchone()

    return row[0] if row else 0


def clear_failed_attempts(email):
    sql = """
        DELETE FROM login_attempts
        WHERE lower(email) = lower(%s)
          AND success = FALSE
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (email,))
        conn.commit()
