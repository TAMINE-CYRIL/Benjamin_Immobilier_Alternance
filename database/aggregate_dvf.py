from connection import get_connection


def aggregate_dvf(year: int):
    """
    Agrège les données DVF d'une année spécifique depuis dvf_raw vers dvf_stats.
    Calcule le prix moyen au m² et le nombre de transactions par zone géographique et type de local.
    
    Args:
        year: Année à agréger
    """
    conn = get_connection()
    cur = conn.cursor()

    print(f"Agrégation DVF pour l'année {year}")

    cur.execute("""
        INSERT INTO dvf_stats (
            code_postal,
            code_departement,
            annee,
            type_local,
            prix_m2_moyen,
            nb_transactions
        )
        SELECT
            code_postal,
            code_departement,
            %s AS annee,
            type_local,
            ROUND(
                AVG(
                    REPLACE(valeur_fonciere, ',', '.')::NUMERIC
                    /
                    REPLACE(surface_reelle_bati, ',', '.')::NUMERIC
                ),
                2
            ) AS prix_m2_moyen,
            COUNT(*) AS nb_transactions
        FROM dvf_raw
        WHERE
            annee = %s
            AND code_postal IS NOT NULL
            AND code_postal <> ''
            AND code_departement IS NOT NULL
            AND code_departement <> ''
            AND type_local IS NOT NULL
            AND valeur_fonciere ~ '^[0-9]+([.,][0-9]+)?$'
            AND surface_reelle_bati ~ '^[0-9]+([.,][0-9]+)?$'
            AND REPLACE(valeur_fonciere, ',', '.')::NUMERIC > 0
            AND REPLACE(surface_reelle_bati, ',', '.')::NUMERIC > 0
        GROUP BY
            code_postal,
            code_departement,
            type_local
        ON CONFLICT (code_postal, code_departement, annee, type_local)
        DO UPDATE SET
            prix_m2_moyen = EXCLUDED.prix_m2_moyen,
            nb_transactions = EXCLUDED.nb_transactions;
    """, (year, year))

    rows_affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    print(f"Agrégation {year} terminée : {rows_affected:,} lignes insérées/mises à jour\n")


def aggregate_dvf_multi_years(years: list[int]):
    """
    Calcule une moyenne du prix au m² sur plusieurs années.
    Cette fonction calcule une vraie moyenne à partir des transactions individuelles,
    pas une moyenne de moyennes.
    
    Args:
        years: Liste des années à inclure dans le calcul (ex: [2023, 2024, 2025])
    
    Returns:
        Le nombre de lignes insérées dans dvf_stats_multi_annees
    """
    conn = get_connection()
    cur = conn.cursor()

    years_str = ", ".join(map(str, years))
    print(f"Calcul de la moyenne multi-années : {years_str}")

    # Créer la table si elle n'existe pas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dvf_stats_multi_annees (
            code_postal VARCHAR(5),
            code_departement VARCHAR(2),
            annees TEXT,
            type_local TEXT,
            prix_m2_moyen NUMERIC(10, 2),
            nb_transactions INTEGER,
            PRIMARY KEY (code_postal, code_departement, annees, type_local)
        );
    """)
    conn.commit()

    # Supprimer les données existantes pour cette combinaison d'années
    annees_key = "-".join(map(str, sorted(years)))
    cur.execute("""
        DELETE FROM dvf_stats_multi_annees WHERE annees = %s;
    """, (annees_key,))
    conn.commit()

    # Calculer la vraie moyenne à partir des transactions individuelles
    placeholders = ", ".join(["%s"] * len(years))
    query = f"""
        INSERT INTO dvf_stats_multi_annees (
            code_postal,
            code_departement,
            annees,
            type_local,
            prix_m2_moyen,
            nb_transactions
        )
        SELECT
            code_postal,
            code_departement,
            %s AS annees,
            type_local,
            ROUND(
                AVG(
                    REPLACE(valeur_fonciere, ',', '.')::NUMERIC
                    /
                    REPLACE(surface_reelle_bati, ',', '.')::NUMERIC
                ),
                2
            ) AS prix_m2_moyen,
            COUNT(*) AS nb_transactions
        FROM dvf_raw
        WHERE
            annee IN ({placeholders})
            AND code_postal IS NOT NULL
            AND code_postal <> ''
            AND code_departement IS NOT NULL
            AND code_departement <> ''
            AND type_local IS NOT NULL
            AND valeur_fonciere ~ '^[0-9]+([.,][0-9]+)?$'
            AND surface_reelle_bati ~ '^[0-9]+([.,][0-9]+)?$'
            AND REPLACE(valeur_fonciere, ',', '.')::NUMERIC > 0
            AND REPLACE(surface_reelle_bati, ',', '.')::NUMERIC > 0
        GROUP BY
            code_postal,
            code_departement,
            type_local;
    """
    
    cur.execute(query, (annees_key, *years))
    rows_affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    print(f"Moyenne multi-années calculée : {rows_affected:,} lignes insérées\n")
    return rows_affected