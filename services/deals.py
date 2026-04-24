from database.connection import get_connection


NB_TRANSACTION_STATS = None


def load_nb_transaction_stats(force_reload=False):
    global NB_TRANSACTION_STATS

    if NB_TRANSACTION_STATS is not None and not force_reload:
        return NB_TRANSACTION_STATS

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT q1, median, q3
            FROM dvf_nb_transactions_stats
            WHERE scope = 'global'
            """
        )
        row = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if not row:
        raise RuntimeError("Quartiles nb_transactions non initialises")

    NB_TRANSACTION_STATS = {
        "q1": row[0],
        "median": row[1],
        "q3": row[2],
    }
    return NB_TRANSACTION_STATS


def evaluate_annonce(
    prix_annonce_m2,
    prix_m2_med,
    prix_m2_q1,
    prix_m2_q3,
    nb_transactions,
    nb_transaction_stats=None,
):
    if not all([prix_annonce_m2, prix_m2_med, prix_m2_q1, prix_m2_q3]):
        return None

    ecart = (prix_annonce_m2 - prix_m2_med) / prix_m2_med

    if ecart <= -0.30:
        score_decote = 80
    elif ecart <= -0.20:
        score_decote = 72
    elif ecart <= -0.10:
        score_decote = 64
    elif ecart <= -0.05:
        score_decote = 58
    elif ecart <= 0.05:
        score_decote = 50
    elif ecart <= 0.15:
        score_decote = 35
    else:
        score_decote = 20

    bonus_quartile = 0
    if prix_m2_q3 > prix_m2_q1:
        position = (prix_annonce_m2 - prix_m2_q1) / (prix_m2_q3 - prix_m2_q1)

        if position < 0:
            bonus_quartile = 15
        elif position < 0.5:
            bonus_quartile = 8
        elif position < 1:
            bonus_quartile = 0
        elif position < 1.5:
            bonus_quartile = -10
        else:
            bonus_quartile = -20

    stats = nb_transaction_stats or load_nb_transaction_stats()
    q1 = stats["q1"]
    median = stats["median"]
    q3 = stats["q3"]

    if nb_transactions <= q1:
        confidence = 0.6
    elif nb_transactions <= median:
        confidence = 0.8
    elif nb_transactions <= q3:
        confidence = 1.0
    else:
        confidence = 1.1

    score = 50 + (score_decote - 50) * confidence
    score += bonus_quartile * confidence

    return max(0, min(100, round(score, 1)))
