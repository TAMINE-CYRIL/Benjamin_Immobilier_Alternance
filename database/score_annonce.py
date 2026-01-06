from database.connection import get_connection
from service.deals import evaluate_annonce  

def score_annonces():
    conn = get_connection()
    cur = conn.cursor()



    cur.execute("""
        SELECT
            a.id,
            a.price_square_meter,
            a.zip_code,
            a.department,
            a.type_bien
        FROM annonces a
        WHERE a.price_square_meter IS NOT NULL AND zip_code IS NOT NULL
    """)
    annonces = cur.fetchall()

    for annonce in annonces:
        annonce_id, prix_m2, zip_code, department, type_bien = annonce

        cur.execute("""
            SELECT prix_m2_moyen, nb_transactions
            FROM dvf_stats
            WHERE code_postal = %s
              AND type_local = %s
            ORDER BY annee DESC
            LIMIT 1
        """, (zip_code, type_bien))

        ref = cur.fetchone()

        if not ref:
            continue
        prix_marche_m2, nb_transactions = ref

        # Calcul du score
        score = evaluate_annonce(
            prix_annonce_m2=prix_m2,
            prix_marche_m2=prix_marche_m2,
            nb_transactions=nb_transactions,
        )

        cur.execute("""
            UPDATE annonces
            SET score = %s
            WHERE id = %s
        """, (score, annonce_id))

    conn.commit()
    cur.close()
    conn.close()

    print("Scoring terminé")
