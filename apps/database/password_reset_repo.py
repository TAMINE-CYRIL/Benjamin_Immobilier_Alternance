import hashlib
import secrets

from database.connection import get_connection


def _hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_password_reset_token(email, ttl_minutes=60, created_by_user_id=None, created_by_email=None, ip_address=None):
    """
    Cree un token de réinitialisation a usage unique pour un utilisateur existant.
    Le token clair est retourne une seule fois et seul son hash est stocke.
    """
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, email
                FROM users
                WHERE lower(email) = lower(%s)
                  AND is_active = TRUE
                LIMIT 1
            """, (email,))
            user = cur.fetchone()
            if not user:
                return None

            cur.execute("""
                INSERT INTO password_reset_tokens (
                    user_id, token_hash, expires_at, created_by_user_id, created_by_email, ip_address
                )
                VALUES (%s, %s, NOW() + (%s * INTERVAL '1 minute'), %s, %s, %s)
                RETURNING id, expires_at
            """, (user[0], token_hash, ttl_minutes, created_by_user_id, created_by_email, ip_address))
            row = cur.fetchone()
        conn.commit()

    return {
        "id": row[0],
        "token": token,
        "expires_at": row[1],
        "user_id": user[0],
        "email": user[1],
    }


def consume_password_reset_token(token):
    """
    Marque un token valide comme utilise et retourne l'utilisateur associe.
    """
    token_hash = _hash_token(token)
    sql = """
        UPDATE password_reset_tokens prt
        SET used_at = CURRENT_TIMESTAMP
        FROM users u
        WHERE prt.user_id = u.id
          AND prt.token_hash = %s
          AND prt.used_at IS NULL
          AND prt.expires_at > CURRENT_TIMESTAMP
          AND u.is_active = TRUE
        RETURNING u.id, u.email
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (token_hash,))
            row = cur.fetchone()
        conn.commit()

    if not row:
        return None

    return {
        "user_id": row[0],
        "email": row[1],
    }
