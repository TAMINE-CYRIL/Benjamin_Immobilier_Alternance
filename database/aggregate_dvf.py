from database.connection import get_connection

def aggregate_dvf(year: int):
    conn = get_connection()
    cur = conn.cursor()

    print("📊 Agrégation DVF...")

    cur.execute("""
        INSERT INTO dvf_stats
        SELECT
            code_postal,
            code_departement,
            %s AS annee,
            type_local,
            ROUND(
                AVG(
                    valeur_fonciere::NUMERIC /
                    surface_reelle_bati::NUMERIC
                ), 2
            ) AS prix_m2_moyen,
            COUNT(*) AS nb_transactions
        FROM dvf_raw
        WHERE
            valeur_fonciere ~ '^[0-9]+([.,][0-9]+)?$'
            AND surface_reelle_bati ~ '^[0-9]+([.,][0-9]+)?$'
            AND surface_reelle_bati::NUMERIC > 0
            AND valeur_fonciere::NUMERIC > 0
        GROUP BY code_postal, code_departement, type_local
        ON CONFLICT (code_postal, annee, type_local)
        DO UPDATE SET
            prix_m2_moyen = EXCLUDED.prix_m2_moyen,
            nb_transactions = EXCLUDED.nb_transactions;
    """, (year,))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Agrégation terminée")
