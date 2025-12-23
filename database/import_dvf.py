from connection import get_connection
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DVF_CSV_PATH = BASE_DIR / "data" / "ValeursFoncieres-2023.csv"


def import_dvf_copy():
    conn = get_connection()
    cur = conn.cursor()

    print("🧹 Nettoyage dvf_raw...")
    cur.execute("TRUNCATE TABLE dvf_raw;")
    conn.commit()

    print("📥 Import DVF via COPY...")
    with open(DVF_CSV_PATH, "r", encoding="utf-8") as f:
        cur.copy_expert("""
            COPY dvf_raw (
                valeur_fonciere,
                code_postal,
                code_departement,
                type_local,
                surface_reelle_bati
            )
            FROM STDIN
            WITH (FORMAT csv, HEADER true, DELIMITER '|')
        """, f)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Import DVF terminé")


if __name__ == "__main__":
    import_dvf_copy()
