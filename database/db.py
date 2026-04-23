import os

from database.connection import get_connection
from database.create_tables import create_tables

def insert_annonces(annonces):
    """
    Insère ou met à jour les annonces avec logs détaillés et stockage dans logs.txt.
    Args:
        annonces: Liste des dictionnaires représentant les annonces à insérer ou mettre à jour.

    """
    connexion = get_connection()
    cursor = connexion.cursor()

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
        last_seen = CURRENT_TIMESTAMP;

    """

    inserted = 0
    updated = 0
    skipped = 0

    os.makedirs("logs", exist_ok=True)
    with open("logs/logs.txt", "a", encoding="utf-8") as log:

        def log_write(message):
            print(message)         
            log.write(message + "\n") 

        for annonce in annonces:
            url = annonce.get("url")

            if not url or url.strip() == "":
                skipped += 1
                log_write(f"[SKIPPED] Annonce sans URL : {annonce.get('title')}")
                continue

            try:
                cursor.execute(insert_query, (
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
                ))

                if cursor.rowcount == 1:
                    inserted += 1
                else:
                    updated += 1
                    log_write(f"[UPDATE] {url}")

            except Exception as e:
                skipped += 1
                log_write(f"[ERROR] {url} -> {e}")
                connexion.rollback()
                continue

        connexion.commit()
        cursor.close()
        connexion.close()

        log_write(f"Total annonces traitées : {len(annonces)}")
        log_write(f"Insertions : {inserted}")
        log_write(f"Mises à jour : {updated}")
        log_write(f"Skipped/Errors : {skipped}")
