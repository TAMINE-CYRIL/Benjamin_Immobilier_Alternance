from database.connection import get_connection


def get_user_by_email(email):
    """
    Récupère un utilisateur par son adresse email. Retourne None si l'utilisateur n'existe pas.
    """
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
    """
    Récupère un utilisateur par son ID. Retourne None si l'utilisateur n'existe pas.
    """
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


def list_users(limit=50):
    """
    Liste les utilisateurs du dashboard, du plus recent au plus ancien.
    """
    sql = """
        SELECT id, email, is_active, created_at, locked_until
        FROM users
        ORDER BY created_at DESC, id DESC
        LIMIT %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "email": row[1],
            "is_active": row[2],
            "created_at": row[3],
            "locked_until": row[4],
        }
        for row in rows
    ]


def create_user(email, password_hash, is_active=True):
    """
    Crée un nouvel utilisateur avec l'email, le hash de mot de passe et le statut actif spécifiés. Retourne les informations de l'utilisateur créé.
    """
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


def update_user_password(user_id, password_hash):
    """
    Met a jour le hash de mot de passe d'un utilisateur et retire un blocage eventuel.
    """
    sql = """
        UPDATE users
        SET password_hash = %s,
            locked_until = NULL
        WHERE id = %s
        RETURNING id, email, is_active, created_at
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (password_hash, user_id))
            row = cur.fetchone()
        conn.commit()

    if not row:
        return None

    return {
        "id": row[0],
        "email": row[1],
        "is_active": row[2],
        "created_at": row[3],
    }


def lock_user_for_minutes(user_id, minutes):
    """
    Verrouille un utilisateur pour un nombre de minutes spécifié en mettant à jour le champ locked_until.
    """
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
    """
    Retire le verouillage d'un utilisateur en mettant à jour le champ locked_until à NULL.
    """
    sql = """
        UPDATE users
        SET locked_until = NULL
        WHERE id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
        conn.commit()
