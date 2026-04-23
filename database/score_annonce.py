from database.connection import get_connection
from services.deals import evaluate_annonce  

def score_annonces():
    conn = get_connection()
    cur = conn.cursor()

    # 1. Récupération des annonces à scorer
    cur.execute("""
        SELECT
            a.id,
            a.price_square_meter,
            a.zip_code,
            a.type_bien,
            a.energy_class
        FROM annonces a
        WHERE
            a.price_square_meter IS NOT NULL
            AND a.zip_code IS NOT NULL
            AND a.type_bien IS NOT NULL
    """)
    annonces = cur.fetchall()

    for annonce in annonces:
        annonce_id, prix_m2, zip_code, type_bien, energy_class = annonce

        # 2. Référence DVF MULTI-ANNÉES (robuste)
        cur.execute("""
            SELECT
                prix_m2_med,
                prix_m2_q1,
                prix_m2_q3,
                nb_transactions
            FROM dvf_stats_multi_annees
            WHERE code_postal = %s
              AND type_local = %s
            LIMIT 1
        """, (zip_code, type_bien))

        ref = cur.fetchone()
        if not ref:
            continue

        prix_m2_med, prix_m2_q1, prix_m2_q3, nb_transactions = ref

        # 3. Calcul du score A v2

        score = evaluate_annonce(
            prix_annonce_m2=prix_m2,
            prix_m2_med=prix_m2_med,
            prix_m2_q1=prix_m2_q1,
            prix_m2_q3=prix_m2_q3,
            nb_transactions=nb_transactions,
        )

        # Ajout du bonus/malus DPE
        dpe_bonus = 0
        if energy_class:
            if energy_class.upper() in ["A", "B"]:
                dpe_bonus = 5
            elif energy_class.upper() in ["E"]:
                dpe_bonus = -3
            elif energy_class.upper() in ["F"]:
                dpe_bonus = -5
            elif energy_class.upper() in ["G"]:
                dpe_bonus = -8
            # C/D = neutre
        if score is not None:
            score += dpe_bonus
            score = max(0, min(100, round(score, 1)))

        if score is None:
            continue

        # 4. Mise à jour de l’annonce
        cur.execute("""
            UPDATE annonces
            SET score = %s
            WHERE id = %s
        """, (score, annonce_id))

    conn.commit()
    cur.close()
    conn.close()

    print("Scoring terminé")
