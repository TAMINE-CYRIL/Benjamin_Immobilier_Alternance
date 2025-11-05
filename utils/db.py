import psycopg2, os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """
    Établit une connexion à la base de données PostgreSQL en utilisant les variables d'environnement.
    """
    return psycopg2.connect(
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", "5432"),
    )

def create_tables():
    """
    Crée les tables nécessaires dans la base de données si elles n'existent pas déjà.
    """
    connexion = get_connection()
    cursor = connexion.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS annonces (
        id SERIAL PRIMARY KEY,
        title TEXT,
        url TEXT UNIQUE,
        address TEXT,
        surface NUMERIC,
        price NUMERIC,
        zip_code INTEGER,
        rooms INTEGER,
        price_square_meter NUMERIC,
        agency TEXT,
        source_site TEXT,
        type_bien TEXT,
        sale_date TEXT,    
        visit_date TEXT              
    );
    """)

    connexion.commit()
    cursor.close()
    connexion.close()

def insert_annonces(annonces):
    """
    Insère ou met à jour les annonces avec logs détaillés.
    """
    connexion = get_connection()
    cursor = connexion.cursor()

    insert_query = """
    INSERT INTO annonces (
        title, url, address, surface, price, zip_code, rooms, 
        price_square_meter, agency, source_site, type_bien, 
        sale_date, visit_date
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (url) DO UPDATE
    SET title = EXCLUDED.title,
        address = EXCLUDED.address,
        surface = EXCLUDED.surface,
        price = EXCLUDED.price,
        zip_code = EXCLUDED.zip_code,
        rooms = EXCLUDED.rooms,
        price_square_meter = EXCLUDED.price_square_meter,
        agency = EXCLUDED.agency,
        source_site = EXCLUDED.source_site,
        type_bien = EXCLUDED.type_bien,
        sale_date = EXCLUDED.sale_date,
        visit_date = EXCLUDED.visit_date;
    """

    inserted = 0
    updated = 0
    skipped = 0

    for annonce in annonces:
        url = annonce.get("url")
        
        if not url or url.strip() == "":
            skipped += 1
            print(f"[SKIPPED] Annonce sans URL : {annonce.get('title')}")
            continue

        try:
            cursor.execute(insert_query, (
                annonce.get("title"),
                url,
                annonce.get("address"),
                annonce.get("surface"),
                annonce.get("price"),
                annonce.get("zip_code"),
                annonce.get("rooms"),
                annonce.get("price_square_meter"),
                annonce.get("agency"),
                annonce.get("source_site"), 
                annonce.get("type_bien"),    
                annonce.get("sale_date"),
                annonce.get("visit_date"),
            ))

            if cursor.rowcount == 1:
                inserted += 1
                print(f"[INSERT] {url}")
            else:
                updated += 1
                print(f"[UPDATE] {url}")

        except Exception as e:
            skipped += 1
            print(f"[ERROR] {url} -> {e}")
            connexion.rollback()
            continue

    connexion.commit()
    cursor.close()
    connexion.close()

    print("\n========== SUMMARY ==========")
    print(f"Total annonces traitées : {len(annonces)}")
    print(f"Insertions : {inserted}")
    print(f"Mises à jour : {updated}")
    print(f"Skipped/Errors : {skipped}")
    print("================================\n")
