from connection import get_connection
from pathlib import Path


def import_dvf_with_staging(dvf_path: Path, year: int):
    """
    Import un fichier DVF dans la table dvf_raw via une table de staging.
    Les données brutes sont conservées avec l'année pour permettre des calculs multi-années.
    
    Args:
        dvf_path: Chemin vers le fichier DVF à importer
        year: Année des données DVF
    """
    conn = get_connection()
    cur = conn.cursor()

    print(f"Import DVF : {dvf_path.name} (année {year})")

    # Table de staging pour l'import des données DVF
    print("   Création de la table de staging...")
    cur.execute("DROP TABLE IF EXISTS dvf_staging;")
    cur.execute("""
        CREATE TABLE dvf_staging (
            identifiant_document TEXT,
            reference_document TEXT,
            article_cgi_1 TEXT,
            article_cgi_2 TEXT,
            article_cgi_3 TEXT,
            article_cgi_4 TEXT,
            article_cgi_5 TEXT,
            no_disposition TEXT,
            date_mutation TEXT,
            nature_mutation TEXT,
            valeur_fonciere TEXT,
            no_voie TEXT,
            btq TEXT,
            type_voie TEXT,
            code_voie TEXT,
            voie TEXT,
            code_postal TEXT,
            commune TEXT,
            code_departement TEXT,
            code_commune TEXT,
            prefixe_section TEXT,
            section TEXT,
            no_plan TEXT,
            no_volume TEXT,
            lot_1 TEXT,
            surface_carrez_1 TEXT,
            lot_2 TEXT,
            surface_carrez_2 TEXT,
            lot_3 TEXT,
            surface_carrez_3 TEXT,
            lot_4 TEXT,
            surface_carrez_4 TEXT,
            lot_5 TEXT,
            surface_carrez_5 TEXT,
            nb_lots TEXT,
            code_type_local TEXT,
            type_local TEXT,
            identifiant_local TEXT,
            surface_reelle_bati TEXT,
            nb_pieces TEXT,
            nature_culture TEXT,
            nature_culture_speciale TEXT,
            surface_terrain TEXT
        );
    """)
    conn.commit()

    print(f"Copie des données depuis {dvf_path.name}...")
    with open(dvf_path, "r", encoding="utf-8") as f:
        cur.copy_expert("""
            COPY dvf_staging
            FROM STDIN
            WITH (FORMAT csv, HEADER true, DELIMITER '|');
        """, f)
    conn.commit()

    print(f"Suppression des données existantes pour l'année {year}...")
    cur.execute("""
        DELETE FROM dvf_raw WHERE annee = %s;
    """, (year,))
    conn.commit()

    print("Insertion des colonnes utiles dans dvf_raw...")
    cur.execute("""
        INSERT INTO dvf_raw (
            annee,
            valeur_fonciere,
            code_postal,
            code_departement,
            type_local,
            surface_reelle_bati
        )
        SELECT
            %s,
            valeur_fonciere,
            LPAD(code_postal, 5, '0'),
            LPAD(code_departement, 2, '0'),
            type_local,
            surface_reelle_bati
        FROM dvf_staging
        WHERE
            valeur_fonciere IS NOT NULL
            AND surface_reelle_bati IS NOT NULL
            AND type_local IS NOT NULL
            AND code_postal ~ '^[0-9]+$'
            AND code_departement ~ '^[0-9A-B]+$'
            AND code_departement IN ('13','06','83');
    """, (year,)) # On limite notre recherche à ces 3 départements
    
    rows_inserted = cur.rowcount
    conn.commit()

    print("Nettoyage de la table de staging...")
    cur.execute("DROP TABLE IF EXISTS dvf_staging;")
    conn.commit()

    cur.close()
    conn.close()

    print(f"Import {year} terminé : {rows_inserted:,} lignes insérées\n")