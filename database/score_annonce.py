from database.connection import get_connection
from psycopg2.extras import Json

from services.deals import SCORE_VERSION, evaluate_opportunity, load_nb_transaction_stats


def _reference_from_row(row):
    if not row:
        return None
    return {
        "prix_m2_med": row[0],
        "prix_m2_q1": row[1],
        "prix_m2_q3": row[2],
        "nb_transactions": row[3],
    }


def score_annonce_payloads(annonces, min_score=None, logger=None):
    """
    Calcule un score préliminaire avant insertion. Toutes les annonces sont
    conservées afin de permettre l'audit et le recalibrage du scoring.
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
    scored_annonces = []

    def log(message):
        if logger:
            logger(message)

    if not annonces:
        return scored_annonces, summary

    transaction_stats = load_nb_transaction_stats()
    conn = get_connection()
    cur = conn.cursor()

    try:
        for annonce in annonces:
            prix_m2 = annonce.get("price_square_meter")
            zip_code = annonce.get("zip_code")
            type_bien = annonce.get("type_bien")
            if not prix_m2 or not zip_code or not type_bien:
                summary["not_scored_missing_fields"] += 1
                reference = None
            else:
                summary["eligible_for_scoring"] += 1
                cur.execute(
                    """
                    SELECT prix_m2_med, prix_m2_q1, prix_m2_q3, nb_transactions
                    FROM dvf_stats_multi_annees
                    WHERE code_postal = %s AND type_local = %s
                    LIMIT 1
                    """,
                    (zip_code, type_bien),
                )
                reference = _reference_from_row(cur.fetchone())
                if not reference:
                    summary["not_scored_no_reference"] += 1

            try:
                details = evaluate_opportunity(
                    annonce,
                    dvf_reference=reference,
                    transaction_stats=transaction_stats,
                )
                annonce["score"] = details["total"]
                annonce["score_details"] = details
                annonce["score_confidence"] = details["confidence"]
                annonce["score_risk_level"] = details["risk_level"]
                annonce["score_version"] = details["version"]
                summary["scored"] += 1
            except Exception as exc:
                summary["errors"] += 1
                log(f"[SCORING ERROR] url={annonce.get('url')} -> {exc}")

            scored_annonces.append(annonce)
            summary["retained"] += 1
    finally:
        cur.close()
        conn.close()

    log(
        "Pre-scoring V2 termine - scores: {scored}, conserves: {retained}, "
        "manque champs: {missing}, sans reference: {no_ref}, erreurs: {errors}".format(
            scored=summary["scored"],
            retained=summary["retained"],
            missing=summary["not_scored_missing_fields"],
            no_ref=summary["not_scored_no_reference"],
            errors=summary["errors"],
        )
    )
    return scored_annonces, summary


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
                a.energy_class,
                a.title,
                a.description,
                a.surface,
                p.contenance,
                e.zonage,
                e.prescriptions,
                e.servitudes
            FROM annonces a
            LEFT JOIN annonce_enrichments e ON e.annonce_id = a.id
            LEFT JOIN parcelles p ON p.id = e.parcel_id
            WHERE a.id IS NOT NULL
            {where_sql}
            """,
            params,
        )
        annonces = cur.fetchall()

        transaction_stats = load_nb_transaction_stats()
        for row in annonces:
            (
                annonce_id,
                prix_m2,
                zip_code,
                type_bien,
                energy_class,
                title,
                description,
                surface,
                parcel_surface,
                zonage,
                prescriptions,
                servitudes,
            ) = row
            reference = None
            if prix_m2 and zip_code and type_bien:
                summary["eligible_for_scoring"] += 1
                cur.execute(
                    """
                    SELECT prix_m2_med, prix_m2_q1, prix_m2_q3, nb_transactions
                    FROM dvf_stats_multi_annees
                    WHERE code_postal = %s AND type_local = %s
                    LIMIT 1
                    """,
                    (zip_code, type_bien),
                )
                reference = _reference_from_row(cur.fetchone())
                if not reference:
                    summary["not_scored_no_reference"] += 1
            else:
                summary["not_scored_missing_fields"] += 1

            annonce = {
                "price_square_meter": prix_m2,
                "type_bien": type_bien,
                "energy_class": energy_class,
                "title": title,
                "description": description,
                "surface": surface,
                "parcel_surface": parcel_surface,
                "zonage": zonage,
                "prescriptions": prescriptions or [],
                "servitudes": servitudes or [],
            }
            try:
                details = evaluate_opportunity(
                    annonce,
                    dvf_reference=reference,
                    transaction_stats=transaction_stats,
                )
            except Exception as exc:
                summary["errors"] += 1
                log(f"[SCORING ERROR] annonce_id={annonce_id} -> {exc}")
                continue

            cur.execute(
                """
                UPDATE annonces
                SET score = %s,
                    score_confidence = %s,
                    score_risk_level = %s,
                    score_details = %s,
                    score_version = %s,
                    scored_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    details["total"],
                    details["confidence"],
                    details["risk_level"],
                    Json(details),
                    SCORE_VERSION,
                    annonce_id,
                ),
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


if __name__ == "__main__":
    print(score_annonces(logger=print))
