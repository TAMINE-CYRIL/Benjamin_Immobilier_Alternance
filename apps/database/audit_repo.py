import json

from database.connection import get_connection


def record_audit_event(event_type, user_id=None, email=None, ip_address=None, metadata=None):
    """
    Enregistre une action sensible dans le journal d'audit.
    """
    sql = """
        INSERT INTO audit_events (event_type, user_id, email, ip_address, metadata)
        VALUES (%s, %s, %s, %s, %s::jsonb)
    """
    payload = json.dumps(metadata or {}, ensure_ascii=False, default=str)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (event_type, user_id, email, ip_address, payload))
        conn.commit()
