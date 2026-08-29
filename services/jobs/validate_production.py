import argparse
import os
from pathlib import Path

from apps.api.auth import validate_security_config
from database.connection import get_connection
from database.migrations import MIGRATIONS_DIR
from utils.production import validate_production_config


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def validate_database():
    expected_migrations = {path.stem for path in MIGRATIONS_DIR.glob("*.sql")}
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.execute("SELECT version FROM schema_migrations")
            applied_migrations = {row[0] for row in cursor.fetchall()}
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_active IS TRUE")
            active_users = cursor.fetchone()[0]

    missing_migrations = sorted(expected_migrations - applied_migrations)
    if missing_migrations:
        raise RuntimeError("Migrations non appliquées : " + ", ".join(missing_migrations))
    if active_users < 1:
        raise RuntimeError("Aucun utilisateur actif n'est configuré")


def validate_frontend(project_root=PROJECT_ROOT):
    index_path = Path(project_root) / "apps" / "web" / "dist" / "index.html"
    if not index_path.is_file():
        raise RuntimeError("Build frontend absent : exécutez `npm run build` dans apps/web")


def run_validation(*, check_database=True, check_frontend=True, project_root=PROJECT_ROOT):
    if os.getenv("APP_ENV", "development").lower() not in {"prod", "production"}:
        raise RuntimeError("APP_ENV doit être défini à production")
    validate_security_config()
    validate_production_config()
    if check_database:
        validate_database()
    if check_frontend:
        validate_frontend(project_root)


def parse_args():
    parser = argparse.ArgumentParser(description="Validation avant mise en production")
    parser.add_argument("--skip-database", action="store_true")
    parser.add_argument("--skip-frontend", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    run_validation(
        check_database=not args.skip_database,
        check_frontend=not args.skip_frontend,
    )
    print("Validation production réussie")


if __name__ == "__main__":
    main()
