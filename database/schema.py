from database.connection import get_connection

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
        url TEXT,
        address TEXT,
        surface NUMERIC,
        price NUMERIC,
        adjuged_price NUMERIC,
        zip_code TEXT,
        department TEXT,
        rooms INTEGER,
        price_square_meter NUMERIC,
        agency TEXT,
        source_site TEXT,
        type_bien TEXT,
        energy_class TEXT,
        sale_date TEXT,    
        visit_date TEXT,
        last_seen TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(url, address, zip_code)             
    );
    """)

    connexion.commit()
    cursor.close()
    connexion.close()

def create_dvf_tables():
    conn = get_connection()
    cur = conn.cursor()

    # Table brute temporaire pour les données DVF
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dvf_raw (
        date_mutation DATE,
        valeur_fonciere NUMERIC,
        code_commune TEXT,
        code_departement TEXT,
        type_local TEXT,
        surface_reelle_bati NUMERIC
    );
    """)

    # Table agrégée pour les statistiques DVF
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dvf_stats (
        code_commune TEXT,
        code_departement TEXT,
        annee INTEGER,
        type_local TEXT,
        prix_m2_moyen NUMERIC,
        nb_transactions INTEGER,
        PRIMARY KEY (code_commune, annee, type_local)
    );
    """)


    conn.commit()
    cur.close()
    conn.close()

def create_all_tables():
    create_tables()
    create_dvf_tables()