from database.connection import get_connection
from database.create_tables import create_tables

def insert_annonces(annonces, logger=None):
    """
    Insére une liste d'annonces dans la base de données avec gestion des conflits et logging.
    """
    summary = {
        "total": len(annonces or []),
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
        "skip_reasons": {
            "missing_url": 0,
            "invalid_payload": 0,
            "sql_error": 0,
        },
        "processed_ids": [],
    }

    if not annonces:
        return summary

    insert_query = """
    INSERT INTO annonces (
        title, url, city, surface, price, adjuged_price, zip_code, department, rooms,
        price_square_meter, agency, source_site, type_bien, energy_class,
        sale_date, visit_date
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (url, city, zip_code) DO UPDATE
    SET title = EXCLUDED.title,
        city = EXCLUDED.city,
        surface = EXCLUDED.surface,
        price = EXCLUDED.price,
        adjuged_price = EXCLUDED.adjuged_price,
        zip_code = EXCLUDED.zip_code,
        department = EXCLUDED.department,
        rooms = EXCLUDED.rooms,
        price_square_meter = EXCLUDED.price_square_meter,
        agency = EXCLUDED.agency,
        source_site = EXCLUDED.source_site,
        type_bien = EXCLUDED.type_bien,
        energy_class = EXCLUDED.energy_class,
        sale_date = EXCLUDED.sale_date,
        visit_date = EXCLUDED.visit_date,
        last_seen = CURRENT_TIMESTAMP
    RETURNING id, (xmax = 0) AS inserted;
    """

    def log(message):
        if logger:
            logger(message)

    connexion = get_connection()
    cursor = connexion.cursor()

    try:
        for annonce in annonces:
            if not isinstance(annonce, dict):
                summary["skipped"] += 1
                summary["skip_reasons"]["invalid_payload"] += 1
                log("[SKIPPED] Invalid payload encountered")
                continue

            url = (annonce.get("url") or "").strip()
            if not url:
                summary["skipped"] += 1
                summary["skip_reasons"]["missing_url"] += 1
                log(f"[SKIPPED] Missing URL for annonce: {annonce.get('title')}")
                continue

            try:
                cursor.execute("SAVEPOINT annonce_upsert")
                cursor.execute(
                    insert_query,
                    (
                        annonce.get("title"),
                        url,
                        annonce.get("city"),
                        annonce.get("surface"),
                        annonce.get("price"),
                        annonce.get("adjuged_price"),
                        annonce.get("zip_code"),
                        annonce.get("department"),
                        annonce.get("rooms"),
                        annonce.get("price_square_meter"),
                        annonce.get("agency"),
                        annonce.get("source_site"),
                        annonce.get("type_bien"),
                        annonce.get("energy_class"),
                        annonce.get("sale_date"),
                        annonce.get("visit_date"),
                    ),
                )

                annonce_id, inserted = cursor.fetchone()
                summary["processed_ids"].append(annonce_id)
                if inserted:
                    summary["inserted"] += 1
                else:
                    summary["updated"] += 1
                    log(f"[UPDATE] {url}")
                cursor.execute("RELEASE SAVEPOINT annonce_upsert")
            except Exception as exc:
                summary["skipped"] += 1
                summary["errors"] += 1
                summary["skip_reasons"]["sql_error"] += 1
                log(f"[ERROR] {url or 'unknown-url'} -> {exc}")
                cursor.execute("ROLLBACK TO SAVEPOINT annonce_upsert")

        connexion.commit()
    finally:
        cursor.close()
        connexion.close()

    log(f"Total annonces traitees : {summary['total']}")
    log(f"Insertions : {summary['inserted']}")
    log(f"Mises a jour : {summary['updated']}")
    log(f"Skipped : {summary['skipped']}")
    log(f"Erreurs SQL : {summary['errors']}")
    return summary
