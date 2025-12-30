import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def drop_tables():
    """
    Supprime toutes les tables si elles existent.
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
                DROP TABLE IF EXISTS
                    annonces,
                    dvf_raw,
                    dvf_stats,
                    dvf_stats_multi_annees
                CASCADE;
            """)

    conn.close()
    print("Tables supprimées avec succès")

if __name__ == "__main__":
    drop_tables()
