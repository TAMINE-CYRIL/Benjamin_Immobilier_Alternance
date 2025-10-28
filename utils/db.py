import psycopg2, os
from dotenv import load_dotenv


load_dotenv()

def get_connection():
    """
    Établit une connexion à la base de données PostgreSQL en utilisant les variables d'environnement.
    """
    return psycopg2.connect(
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", "5432"),
    )

def create_tables():
    """
    Crée les tables nécessaires dans la base de données si elles n'existent pas déjà.
    """
    connexion = get_connection()
    cursor = connexion.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS annonces (
            id SERIAL PRIMARY KEY,
            name TEXT,
            price INT,
            surface INT,
            url TEXT);
        """)

    connexion.commit()

    cursor.close()
    connexion.close()