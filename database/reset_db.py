import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def cleanup():
    """
    Fonction pour supprimer les annonces n'ayant pas été vues depuis plus de 30 jours.
    """
    conn = psycopg2.connect(
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
    )

    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM annonces
                WHERE last_seen < NOW() - INTERVAL '14 days'
            """)
            deleted = cur.rowcount

    conn.close()
    print(f"{deleted} annonces supprimées")

if __name__ == "__main__":
    cleanup()
