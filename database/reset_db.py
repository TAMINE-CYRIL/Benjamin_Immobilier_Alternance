from database.connection import get_connection
from database.create_tables import create_annonces_archive_table


def cleanup(days=14, logger=None, archive=True):
    """
    Archive puis supprime les annonces qui n'ont pas ete vues depuis plus de N jours.
    """
    if archive:
        create_annonces_archive_table()

    conn = get_connection()
    archived = 0

    with conn:
        with conn.cursor() as cur:
            if archive:
                cur.execute(
                    """
                    INSERT INTO annonces_archive (
                        annonce_id,
                        title,
                        url,
                        city,
                        surface,
                        price,
                        adjuged_price,
                        zip_code,
                        score,
                        score_confidence,
                        score_risk_level,
                        score_details,
                        score_version,
                        scored_at,
                        department,
                        rooms,
                        price_square_meter,
                        agency,
                        source_site,
                        type_bien,
                        energy_class,
                        sale_date,
                        visit_date,
                        description,
                        business_status,
                        is_favorite,
                        status_updated_at,
                        first_seen,
                        last_seen,
                        enrichment_snapshot,
                        purge_reason
                    )
                    SELECT
                        a.id,
                        a.title,
                        a.url,
                        a.city,
                        a.surface,
                        a.price,
                        a.adjuged_price,
                        a.zip_code,
                        a.score,
                        a.score_confidence,
                        a.score_risk_level,
                        a.score_details,
                        a.score_version,
                        a.scored_at,
                        a.department,
                        a.rooms,
                        a.price_square_meter,
                        a.agency,
                        a.source_site,
                        a.type_bien,
                        a.energy_class,
                        a.sale_date,
                        a.visit_date,
                        a.description,
                        a.business_status,
                        a.is_favorite,
                        a.status_updated_at,
                        a.first_seen,
                        a.last_seen,
                        CASE
                            WHEN e.id IS NULL THEN NULL
                            ELSE to_jsonb(e)
                        END,
                        %s
                    FROM annonces a
                    LEFT JOIN annonce_enrichments e ON e.annonce_id = a.id
                    WHERE a.last_seen < NOW() - (%s * INTERVAL '1 day')
                    ON CONFLICT (annonce_id, last_seen) DO NOTHING
                    """,
                    (f"last_seen older than {days} days", days),
                )
                archived = cur.rowcount

            cur.execute(
                """
                DELETE FROM annonces
                WHERE last_seen < NOW() - (%s * INTERVAL '1 day')
                """,
                (days,),
            )
            deleted = cur.rowcount

    conn.close()
    message = f"{deleted} annonces supprimees"
    if archive:
        message = f"{archived} annonces archivees, {message}"
    if logger:
        logger(message)
    else:
        print(message)
    return deleted


if __name__ == "__main__":
    cleanup()
