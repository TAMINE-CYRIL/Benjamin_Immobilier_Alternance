from database.connection import get_connection
from services.deals import evaluate_annonce


MIN_SCORE_TO_SAVE = 20


def _apply_dpe_bonus(score, energy_class):
    dpe_bonus = 0
    if energy_class:
        energy_class = energy_class.upper()
        if energy_class in ["A", "B"]:
            dpe_bonus = 5
        elif energy_class == "E":
            dpe_bonus = -3
        elif energy_class == "F":
            dpe_bonus = -5
        elif energy_class == "G":
            dpe_bonus = -8

    return max(0, min(100, round(score + dpe_bonus, 1)))


def score_annonce_payloads(annonces, min_score=MIN_SCORE_TO_SAVE, logger=None):
    """
    Calcule les scores avant insertion et ne conserve que les annonces dont le
    score est strictement supérieur au seuil demandé.
    """
    summary = {
        "eligible_for_scoring": 0,
        "scored": 0,
        "retained": 0,
        "filtered_below_min_score": 0,
        "not_scored_missing_fields": 0,
        "not_scored_no_reference": 0,
        "errors": 0,
    }
    retained_annonces = []

    def log(message):
        if logger:
            logger(message)

    if not annonces:
        return retained_annonces, summary

    conn = get_connection()
    cur = conn.cursor()

    try:
        for annonce in annonces:
            prix_m2 = annonce.get("price_square_meter")
            zip_code = annonce.get("zip_code")
            type_bien = annonce.get("type_bien")
            energy_class = annonce.get("energy_class")

            if not prix_m2 or not zip_code or not type_bien:
                summary["not_scored_missing_fields"] += 1
                continue

            summary["eligible_for_scoring"] += 1
            cur.execute(
                """
                SELECT
                    prix_m2_med,
                    prix_m2_q1,
                    prix_m2_q3,
                    nb_transactions
                FROM dvf_stats_multi_annees
                WHERE code_postal = %s
                  AND type_local = %s
                LIMIT 1
                """,
                (zip_code, type_bien),
            )
            ref = cur.fetchone()
            if not ref:
                summary["not_scored_no_reference"] += 1
                continue

            try:
                score = evaluate_annonce(
                    prix_annonce_m2=prix_m2,
                    prix_m2_med=ref[0],
                    prix_m2_q1=ref[1],
                    prix_m2_q3=ref[2],
                    nb_transactions=ref[3],
                )
            except Exception as exc:
                summary["errors"] += 1
                log(f"[SCORING ERROR] url={annonce.get('url')} -> {exc}")
                continue

            if score is None:
                summary["not_scored_no_reference"] += 1
                continue

            score = _apply_dpe_bonus(score, energy_class)
            summary["scored"] += 1
            if score <= min_score:
                summary["filtered_below_min_score"] += 1
                continue

            annonce["score"] = score
            retained_annonces.append(annonce)
            summary["retained"] += 1
    finally:
        cur.close()
        conn.close()

    log(
        "Pre-scoring termine - scores: {scored}, conserves (> {min_score}): {retained}, "
        "filtres: {filtered}, manque champs: {missing}, sans reference: {no_ref}, erreurs: {errors}".format(
            scored=summary["scored"],
            min_score=min_score,
            retained=summary["retained"],
            filtered=summary["filtered_below_min_score"],
            missing=summary["not_scored_missing_fields"],
            no_ref=summary["not_scored_no_reference"],
            errors=summary["errors"],
        )
    )
    return retained_annonces, summary


def score_annonces(annonce_ids=None, logger=None):
    """
    Calcule un score pour chaque annonce en fonction de ses caractéristiques et de références statistiques.
    - annonce_ids : liste des IDs des annonces à noter (si None, toutes les annonces sont prises en compte)
    - logger : fonction de journalisation (optionnelle)
    """
    summary = {
        "eligible_for_scoring": 0,
        "scored": 0,
        "not_scored_missing_fields": 0,
        "not_scored_no_reference": 0,
        "errors": 0,
    }

    def log(message):
        if logger:
            logger(message)

    conn = get_connection()
    cur = conn.cursor()

    try:
        where_sql = ""
        params = []
        if annonce_ids:
            where_sql = "AND a.id = ANY(%s)"
            params.append(list(annonce_ids))

        cur.execute(
            f"""
            SELECT
                a.id,
                a.price_square_meter,
                a.zip_code,
                a.type_bien,
                a.energy_class
            FROM annonces a
            WHERE a.id IS NOT NULL
            {where_sql}
            """,
            params,
        )
        annonces = cur.fetchall()

        for annonce_id, prix_m2, zip_code, type_bien, energy_class in annonces:
            if not prix_m2 or not zip_code or not type_bien:
                summary["not_scored_missing_fields"] += 1
                continue

            summary["eligible_for_scoring"] += 1
            cur.execute(
                """
                SELECT
                    prix_m2_med,
                    prix_m2_q1,
                    prix_m2_q3,
                    nb_transactions
                FROM dvf_stats_multi_annees
                WHERE code_postal = %s
                  AND type_local = %s
                LIMIT 1
                """,
                (zip_code, type_bien),
            )

            ref = cur.fetchone()
            if not ref:
                summary["not_scored_no_reference"] += 1
                continue

            prix_m2_med, prix_m2_q1, prix_m2_q3, nb_transactions = ref

            try:
                score = evaluate_annonce(
                    prix_annonce_m2=prix_m2,
                    prix_m2_med=prix_m2_med,
                    prix_m2_q1=prix_m2_q1,
                    prix_m2_q3=prix_m2_q3,
                    nb_transactions=nb_transactions,
                )
            except Exception as exc:
                summary["errors"] += 1
                log(f"[SCORING ERROR] annonce_id={annonce_id} -> {exc}")
                continue

            if score is None:
                summary["not_scored_no_reference"] += 1
                continue

            score = _apply_dpe_bonus(score, energy_class)
            cur.execute(
                """
                UPDATE annonces
                SET score = %s
                WHERE id = %s
                """,
                (score, annonce_id),
            )
            summary["scored"] += 1

        conn.commit()
    finally:
        cur.close()
        conn.close()

    log(
        "Scoring termine - eligibles: {eligible}, scores: {scored}, manque champs: {missing}, "
        "sans reference: {no_ref}, erreurs: {errors}".format(
            eligible=summary["eligible_for_scoring"],
            scored=summary["scored"],
            missing=summary["not_scored_missing_fields"],
            no_ref=summary["not_scored_no_reference"],
            errors=summary["errors"],
        )
    )
    return summary
