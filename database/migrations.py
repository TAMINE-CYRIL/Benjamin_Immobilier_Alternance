from pathlib import Path

from database.connection import get_connection


MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def create_schema_migrations_table(cur):
    """
    Crée la table schema_migrations si elle n'existe pas déjà, pour suivre les migrations appliquées.
    """
    cur.execute("""
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version TEXT PRIMARY KEY,
        applied_at TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP
    );
    """)


def apply_pending_migrations(logger=None):
    """
    Applique les fichiers SQL versionnes de database/migrations dans l'ordre.
    """
    migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    applied = []

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                create_schema_migrations_table(cur)
                cur.execute("SELECT version FROM schema_migrations")
                existing = {row[0] for row in cur.fetchall()}

                for migration in migrations:
                    version = migration.stem
                    if version in existing:
                        continue

                    sql = migration.read_text(encoding="utf-8")
                    cur.execute(sql)
                    cur.execute(
                        "INSERT INTO schema_migrations (version) VALUES (%s)",
                        (version,),
                    )
                    applied.append(version)
                    if logger:
                        logger(f"Migration appliquee: {version}")
    finally:
        conn.close()

    return applied


if __name__ == "__main__":
    applied_versions = apply_pending_migrations()
    if applied_versions:
        print("Migrations appliquees: " + ", ".join(applied_versions))
    else:
        print("Aucune migration en attente")
