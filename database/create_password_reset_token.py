import argparse
import sys
from pathlib import Path

from apps.database.audit_repo import record_audit_event
from apps.database.password_reset_repo import create_password_reset_token
from database.create_tables import create_audit_events_table, create_password_reset_tokens_table, create_users_table

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(description="Genere un token de reinitialisation de mot de passe.")
    parser.add_argument("email", help="Email de l'utilisateur a reinitialiser")
    parser.add_argument("--ttl-minutes", type=int, default=60, help="Duree de validite du token")
    parser.add_argument("--created-by-email", default=None, help="Email de la personne qui genere le token")
    args = parser.parse_args()

    if args.ttl_minutes < 1:
        raise SystemExit("La duree de validite doit etre positive.")

    create_users_table()
    create_audit_events_table()
    create_password_reset_tokens_table()
    reset = create_password_reset_token(
        args.email,
        ttl_minutes=args.ttl_minutes,
        created_by_email=args.created_by_email,
    )
    if not reset:
        raise SystemExit("Utilisateur actif introuvable.")

    try:
        record_audit_event(
            "password_reset_token_created",
            user_id=reset["user_id"],
            email=reset["email"],
            metadata={"created_by_email": args.created_by_email, "ttl_minutes": args.ttl_minutes},
        )
    except Exception:
        pass

    print(f"Token de reinitialisation pour {reset['email']}:")
    print(reset["token"])
    print(f"Expire le: {reset['expires_at']}")


if __name__ == "__main__":
    main()
