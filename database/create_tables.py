from connection import get_connection

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
        score NUMERIC,
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
    """
    Crée les tables nécessaires pour les données DVF dans la base de données si elles n'existent pas déjà.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Table brute pour les données DVF (avec colonne annee)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dvf_raw (
        id SERIAL PRIMARY KEY,
        annee INTEGER NOT NULL,
        valeur_fonciere TEXT,
        code_postal VARCHAR(5),
        code_departement VARCHAR(2),
        type_local TEXT,
        surface_reelle_bati TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Index pour améliorer les performances
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_dvf_raw_annee ON dvf_raw(annee);
    """)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_dvf_raw_code_postal ON dvf_raw(code_postal);
    """)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_dvf_raw_code_departement ON dvf_raw(code_departement);
    """)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_dvf_raw_type_local ON dvf_raw(type_local);
    """)
    
    conn.commit()

    # Table agrégée pour les statistiques DVF par année
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dvf_stats (
        code_postal VARCHAR(5) NOT NULL,
        code_departement VARCHAR(2) NOT NULL,
        annee INTEGER NOT NULL,
        type_local TEXT NOT NULL,
        prix_m2_moyen NUMERIC(10, 2),
        nb_transactions INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (code_postal, code_departement, annee, type_local)
    );
    """)
    
    # Index pour améliorer les performances
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_dvf_stats_annee ON dvf_stats(annee);
    """)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_dvf_stats_code_postal ON dvf_stats(code_postal);
    """)

    conn.commit()

    # Table agrégée pour les statistiques DVF multi-années
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dvf_stats_multi_annees (
        code_postal VARCHAR(5) NOT NULL,
        code_departement VARCHAR(2) NOT NULL,
        annees TEXT NOT NULL,
        type_local TEXT NOT NULL,
        prix_m2_med NUMERIC(10, 2),
        nb_transactions INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (code_postal, code_departement, annees, type_local)
    );
    """)
    
    # Index pour améliorer les performances
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_dvf_stats_multi_code_postal ON dvf_stats_multi_annees(code_postal);
    """)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_dvf_stats_multi_annees ON dvf_stats_multi_annees(annees);
    """)

    conn.commit()
    cur.close()
    conn.close()

def create_all_tables():
    """
    Crée toutes les tables nécessaires dans la base de données.
    """
    create_tables()
    create_dvf_tables()

if __name__ == "__main__":
    create_all_tables()
    print("Tables créées avec succès")