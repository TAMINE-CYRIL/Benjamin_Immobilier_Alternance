import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
)

with conn:
    with conn.cursor() as cur:
        cur.execute("""
            DELETE FROM annonces
            WHERE last_seen < NOW() - INTERVAL '30 days'
        """)
        deleted = cur.rowcount

print(f"[{datetime.now()}] {deleted} annonces supprimées")
