from connection import get_connection

def compute_nb_transactions_quartiles():
    """
    Ajoute ou met à jour une ligne dans la table dvf_nb_transactions_stats avec les quartiles du nombre de transactions
    calculés à partir de la table dvf_stats_multi_annees.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO dvf_nb_transactions_stats (scope, q1, median, q3)
        SELECT
            'global',
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY nb_transactions)::INTEGER,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY nb_transactions)::INTEGER,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY nb_transactions)::INTEGER
        FROM dvf_stats_multi_annees
        ON CONFLICT (scope) DO UPDATE
        SET
            q1 = EXCLUDED.q1,
            median = EXCLUDED.median,
            q3 = EXCLUDED.q3,
            updated_at = NOW();
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Calcul des quartiles du nombre de transactions terminé")