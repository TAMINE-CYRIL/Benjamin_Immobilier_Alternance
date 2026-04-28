import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def cleanup(days=14, logger=None):
    """
    Supprime les annonces qui n'ont pas ete vues depuis plus de N jours.
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
            cur.execute(
                """
                DELETE FROM annonces
                WHERE last_seen < NOW() - (%s * INTERVAL '1 day')
                """,
                (days,),
            )
            deleted = cur.rowcount

    conn.close()
    message = f"{deleted} annonces supprimees"
    if logger:
        logger(message)
    else:
        print(message)
    return deleted


if __name__ == "__main__":
    cleanup()
