try:
    from database.connection import get_connection
except ImportError:
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
        city TEXT,
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
        UNIQUE(url, city, zip_code)             
    );
    """)

    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_annonces_score ON annonces(score);",
        "CREATE INDEX IF NOT EXISTS idx_annonces_city ON annonces(city);",
        "CREATE INDEX IF NOT EXISTS idx_annonces_zip_code ON annonces(zip_code);",
        "CREATE INDEX IF NOT EXISTS idx_annonces_department ON annonces(department);",
        "CREATE INDEX IF NOT EXISTS idx_annonces_type_bien ON annonces(type_bien);",
        "CREATE INDEX IF NOT EXISTS idx_annonces_price ON annonces(price);",
        "CREATE INDEX IF NOT EXISTS idx_annonces_surface ON annonces(surface);",
        "CREATE INDEX IF NOT EXISTS idx_annonces_last_seen ON annonces(last_seen);",
    ]
    for statement in index_statements:
        cursor.execute(statement)

    connexion.commit()
    cursor.close()
    connexion.close()


def create_users_table():
    """
    Cree la table des utilisateurs qui peuvent acceder au dashboard prive.
    """
    connexion = get_connection()
    cursor = connexion.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
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
        prix_m2_med NUMERIC(10, 2),
        prix_m2_q1 NUMERIC(10, 2),
        prix_m2_q3 NUMERIC(10, 2),
        prix_m2_min NUMERIC(10, 2),
        prix_m2_max NUMERIC(10, 2),
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
        prix_m2_q1 NUMERIC(10, 2),
        prix_m2_q3 NUMERIC(10, 2),
        prix_m2_min NUMERIC(10, 2),
        prix_m2_max NUMERIC(10, 2),
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


def create_table_stats():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dvf_nb_transactions_stats (
    scope TEXT PRIMARY KEY,
    q1 INTEGER,
    median INTEGER,
    q3 INTEGER,
    updated_at TIMESTAMP DEFAULT NOW()
    );
    """)
    conn.commit()
    cur.close()
    conn.close()


def create_all_tables():
    """
    Crée toutes les tables nécessaires dans la base de données.
    """
    create_tables()
    create_users_table()
    create_dvf_tables()
    create_table_stats()

if __name__ == "__main__":
    create_all_tables()
    print("Tables créées avec succès")
