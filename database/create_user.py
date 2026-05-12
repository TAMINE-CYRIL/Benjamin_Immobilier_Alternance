import argparse
import getpass
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.auth import hash_password
from apps.database.users_repo import create_user, get_user_by_email
from database.create_tables import create_users_table


def main():
    parser = argparse.ArgumentParser(description="Cree un utilisateur pour le dashboard prive.")
    parser.add_argument("email", help="Email de connexion")
    parser.add_argument("password", nargs="?", help="Mot de passe. Si absent, il sera demande.")
    args = parser.parse_args()

    password = args.password
    if not password:
        password = getpass.getpass("Mot de passe: ")

    if len(password) < 8:
        raise SystemExit("Le mot de passe doit contenir au moins 8 caracteres.")

    create_users_table()

    if get_user_by_email(args.email):
        raise SystemExit("Un utilisateur avec cet email existe deja.")

    user = create_user(args.email, hash_password(password))
    print(f"Utilisateur cree: {user['email']} (id={user['id']})")


if __name__ == "__main__":
    main()
