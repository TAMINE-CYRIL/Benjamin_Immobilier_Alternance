import psycopg2, csv, os
from dotenv import load_dotenv

load_dotenv()

dsv_file_path = os.getenv("DVF_CSV_PATH", "data/ValeursFoncieres2023.csv")

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

def import_dvf_csv():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("TRUNCATE TABLE dvf_raw;")
    conn.commit()

    with open(dsv_file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter="|")

        rows = []
        for row in reader:
            try:
                valeur = row["Valeur fonciere"]
                surface = row["Surface reelle bati"]

                if not valeur or not surface:
                    continue

                valeur = float(valeur.replace(",", "."))
                surface = float(surface.replace(",", "."))

                if valeur <= 0 or surface <= 0:
                    continue

                rows.append((
                    valeur,
                    row["Code postal"],
                    row["Code departement"],
                    row["Type local"],
                    surface
                ))

            except Exception:
                continue

            if len(rows) >= 10_000:
                cur.executemany("""
                    INSERT INTO dvf_raw
                    (date_mutation, valeur_fonciere, code_postal,
                     code_departement, type_local, surface_reelle_bati)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, rows)
                conn.commit()
                rows.clear()

        if rows:
            cur.executemany("""
                INSERT INTO dvf_raw
                (date_mutation, valeur_fonciere, code_postal,
                 code_departement, type_local, surface_reelle_bati)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, rows)
            conn.commit()


    cur.close()
    conn.close()

def aggregate_dvf():
    conn = get_connection()
    cur = conn.cursor()


    cur.execute("""
        INSERT INTO dvf_stats
        SELECT
            code_postal,
            code_departement,
            EXTRACT(YEAR FROM date_mutation)::INT AS annee,
            type_local,
            ROUND(AVG(valeur_fonciere / surface_reelle_bati), 2) AS prix_m2_moyen,
            COUNT(*) AS nb_transactions
        FROM dvf_raw
        GROUP BY code_postal, code_departement, annee, type_local
        ON CONFLICT (code_commune, annee, type_local)
        DO UPDATE SET
            prix_m2_moyen = EXCLUDED.prix_m2_moyen,
            nb_transactions = EXCLUDED.nb_transactions;
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("Agrégation terminée")

if __name__ == "__main__":
    import_dvf_csv()
    aggregate_dvf()