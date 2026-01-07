from connection import get_connection


def aggregate_dvf(year: int):
    """
    Agrège les données DVF d'une année spécifique depuis dvf_raw vers dvf_stats.
    Calcule le prix médian au m² (plus robuste que la moyenne) et le nombre de transactions 
    par zone géographique et type de local.
    
    Filtres appliqués pour éviter les valeurs aberrantes :
    - Prix au m² entre 500€ et 20000€
    - Surface entre 10m² et 500m²
    - Prix de vente entre 10000€ et 5000000€
    - Uniquement Maisons et Appartements
    - Exclusion des ventes de lots multiples (qui faussent les prix)
    
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
            prix_m2_med,
            prix_m2_q1,
            prix_m2_q3,
            prix_m2_min,
            prix_m2_max,
            nb_transactions
        )
        SELECT
            code_postal,
            code_departement,
            %s AS annee,
            type_local,
            
            -- Utilisation de la MÉDIANE au lieu de la MOYENNE pour plus de robustesse
            ROUND(
                PERCENTILE_CONT(0.5) WITHIN GROUP (
                    ORDER BY (
                        REPLACE(valeur_fonciere, ',', '.')::NUMERIC
                        /
                        REPLACE(surface_reelle_bati, ',', '.')::NUMERIC
                    )
                )::NUMERIC,
                2
            ) AS prix_m2_med,

            ROUND(
                PERCENTILE_CONT(0.25) WITHIN GROUP (
                    ORDER BY (
                        REPLACE(valeur_fonciere, ',', '.')::NUMERIC
                        /
                        REPLACE(surface_reelle_bati, ',', '.')::NUMERIC
                    )
                )::NUMERIC,
                2
            ) AS prix_m2_q1,

            ROUND(
                PERCENTILE_CONT(0.75) WITHIN GROUP (
                    ORDER BY (
                        REPLACE(valeur_fonciere, ',', '.')::NUMERIC
                        /
                        REPLACE(surface_reelle_bati, ',', '.')::NUMERIC
                    )
                )::NUMERIC,
                2
            ) AS prix_m2_q3,

            ROUND(
                PERCENTILE_CONT(0.0) WITHIN GROUP (
                    ORDER BY (
                        REPLACE(valeur_fonciere, ',', '.')::NUMERIC
                        /
                        REPLACE(surface_reelle_bati, ',', '.')::NUMERIC
                    )
                )::NUMERIC,
                2
            ) AS prix_m2_min,

            ROUND(
                PERCENTILE_CONT(1.0) WITHIN GROUP (
                    ORDER BY (
                        REPLACE(valeur_fonciere, ',', '.')::NUMERIC
                        /
                        REPLACE(surface_reelle_bati, ',', '.')::NUMERIC
                    )
                )::NUMERIC,
                2
            ) AS prix_m2_max,

            COUNT(*) AS nb_transactions
        FROM dvf_raw
        WHERE
            annee = %s
            AND code_postal IS NOT NULL
            AND code_postal <> ''
            AND code_departement IS NOT NULL
            AND code_departement <> ''
            AND type_local IN ('Maison', 'Appartement')  -- IMPORTANT: Filtrer les types
            AND valeur_fonciere ~ '^[0-9]+([.,][0-9]+)?$'
            AND surface_reelle_bati ~ '^[0-9]+([.,][0-9]+)?$'
            AND REPLACE(valeur_fonciere, ',', '.')::NUMERIC > 0
            AND REPLACE(surface_reelle_bati, ',', '.')::NUMERIC > 0
            
            -- Filtres pour éliminer les valeurs aberrantes
            AND REPLACE(valeur_fonciere, ',', '.')::NUMERIC BETWEEN 10000 AND 5000000  -- Prix entre 10k€ et 5M€
            AND REPLACE(surface_reelle_bati, ',', '.')::NUMERIC BETWEEN 10 AND 500    -- Surface entre 10m² et 500m²
            AND (
                REPLACE(valeur_fonciere, ',', '.')::NUMERIC
                /
                REPLACE(surface_reelle_bati, ',', '.')::NUMERIC
            ) BETWEEN 500 AND 20000  -- Prix au m² entre 500€ et 20000€
            
        GROUP BY
            code_postal,
            code_departement,
            type_local
        HAVING COUNT(*) >= 3  -- Minimum 3 transactions pour calculer une statistique fiable
        ON CONFLICT (code_postal, code_departement, annee, type_local)
        DO UPDATE SET
            prix_m2_med = EXCLUDED.prix_m2_med,
            nb_transactions = EXCLUDED.nb_transactions;
    """, (year, year))

    rows_affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    print(f"Agrégation {year} terminée : {rows_affected:,} lignes insérées/mises à jour\n")


def aggregate_dvf_multi_years(years: list[int]):
    """
    Calcule la médiane du prix au m² sur plusieurs années, par type de logement.
    Cette fonction calcule la médiane à partir des prix MÉDIANS annuels de chaque zone,
    en séparant les Maisons des Appartements.
    
    Args:
        years: Liste des années à inclure dans le calcul (ex: [2023, 2024, 2025])
    
    Returns:
        Le nombre de lignes insérées dans dvf_stats_multi_annees
    """
    conn = get_connection()
    cur = conn.cursor()

    years_str = ", ".join(map(str, years))
    print(f"Calcul de la médiane multi-années : {years_str}")

    # Créer la table si elle n'existe pas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dvf_stats_multi_annees (
            code_postal VARCHAR(5),
            code_departement VARCHAR(2),
            annees TEXT,
            type_local TEXT,
            prix_m2_med NUMERIC(10, 2),
            prix_m2_q1 NUMERIC(10, 2),
            prix_m2_q3 NUMERIC(10, 2), 
            prix_m2_min NUMERIC(10, 2),
            prix_m2_max NUMERIC(10, 2),
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

    # Calculer la médiane à partir des prix médians annuels
    placeholders = ", ".join(["%s"] * len(years))
    query = f"""
        INSERT INTO dvf_stats_multi_annees (
            code_postal,
            code_departement,
            annees,
            type_local,
            prix_m2_med,
            prix_m2_q1,
            prix_m2_q3,
            prix_m2_min,
            prix_m2_max,
            nb_transactions
        )
        SELECT
            code_postal,
            MIN(code_departement) AS code_departement,
            %s AS annees,
            type_local,

            ROUND(
                PERCENTILE_CONT(0.5)
                WITHIN GROUP (ORDER BY prix_m2_med)
                ::NUMERIC,
                2
            ) AS prix_m2_med,

            ROUND(
                PERCENTILE_CONT(0.25)
                WITHIN GROUP (ORDER BY prix_m2_med)
                ::NUMERIC,
                2
            ) AS prix_m2_q1,

            ROUND(
                PERCENTILE_CONT(0.75)
                WITHIN GROUP (ORDER BY prix_m2_med)
                ::NUMERIC,
                2
            ) AS prix_m2_q3,

            MIN(prix_m2_med) AS prix_m2_min,
            MAX(prix_m2_med) AS prix_m2_max,

            SUM(nb_transactions) AS nb_transactions
        FROM dvf_stats
        WHERE
            type_local IN ('Maison', 'Appartement')
            AND annee IN ({placeholders})
        GROUP BY
            code_postal,
            type_local
        HAVING SUM(nb_transactions) >= 5
        ON CONFLICT (code_postal, code_departement, annees, type_local)
        DO UPDATE SET
            prix_m2_med = EXCLUDED.prix_m2_med,
            prix_m2_q1  = EXCLUDED.prix_m2_q1,
            prix_m2_q3  = EXCLUDED.prix_m2_q3,
            prix_m2_min = EXCLUDED.prix_m2_min,
            prix_m2_max = EXCLUDED.prix_m2_max,
            nb_transactions = EXCLUDED.nb_transactions;

    """
    
    cur.execute(query, (annees_key, *years))
    rows_affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    print(f"Médiane multi-années calculée : {rows_affected:,} lignes insérées\n")
    return rows_affected


def analyze_outliers(year: int, code_postal: str = None):
    """
    Fonction utilitaire pour analyser les valeurs aberrantes dans les données DVF.
    Permet de diagnostiquer pourquoi certaines communes ont des prix aberrants.
    
    Args:
        year: Année à analyser
        code_postal: Code postal spécifique à analyser (optionnel)
    """
    conn = get_connection()
    cur = conn.cursor()
    
    where_clause = "annee = %s"
    params = [year]
    
    if code_postal:
        where_clause += " AND code_postal = %s"
        params.append(code_postal)
    
    query = f"""
        SELECT
            code_postal,
            type_local,
            COUNT(*) as nb_total,
            COUNT(*) FILTER (
                WHERE type_local NOT IN ('Maison', 'Appartement')
            ) as nb_autres_types,
            COUNT(*) FILTER (
                WHERE (
                    REPLACE(valeur_fonciere, ',', '.')::NUMERIC
                    /
                    REPLACE(surface_reelle_bati, ',', '.')::NUMERIC
                ) > 20000
            ) as nb_prix_trop_haut,
            COUNT(*) FILTER (
                WHERE (
                    REPLACE(valeur_fonciere, ',', '.')::NUMERIC
                    /
                    REPLACE(surface_reelle_bati, ',', '.')::NUMERIC
                ) < 500
            ) as nb_prix_trop_bas,
            ROUND(AVG(
                REPLACE(valeur_fonciere, ',', '.')::NUMERIC
                /
                REPLACE(surface_reelle_bati, ',', '.')::NUMERIC
            ), 2) as prix_m2_med_brut,
            ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY (
                    REPLACE(valeur_fonciere, ',', '.')::NUMERIC
                    /
                    REPLACE(surface_reelle_bati, ',', '.')::NUMERIC
                )
            ), 2) as prix_m2_median_brut
        FROM dvf_raw
        WHERE
            {where_clause}
            AND valeur_fonciere ~ '^[0-9]+([.,][0-9]+)?$'
            AND surface_reelle_bati ~ '^[0-9]+([.,][0-9]+)?$'
            AND REPLACE(valeur_fonciere, ',', '.')::NUMERIC > 0
            AND REPLACE(surface_reelle_bati, ',', '.')::NUMERIC > 0
        GROUP BY code_postal, type_local
        ORDER BY nb_total DESC
        LIMIT 20;
    """
    
    cur.execute(query, params)
    results = cur.fetchall()
    
    print(f"\nAnalyse des valeurs pour l'année {year}")
    if code_postal:
        print(f"Code postal: {code_postal}")
    print("-" * 100)
    print(f"{'CP':<6} {'Type':<12} {'Total':<8} {'Autres':<8} {'>20k€':<8} {'<500€':<8} {'Moy':<10} {'Méd':<10}")
    print("-" * 100)
    
    for row in results:
        print(f"{row[0]:<6} {row[1]:<12} {row[2]:<8} {row[3]:<8} {row[4]:<8} {row[5]:<8} {row[6]:<10} {row[7]:<10}")
    
    cur.close()
    conn.close()