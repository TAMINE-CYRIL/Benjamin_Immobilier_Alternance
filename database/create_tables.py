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
        search_vector tsvector,
        UNIQUE(url, city, zip_code)             
    );
    """)

    # Ajouter colonne search_vector si elle n'existe pas (pour tables existantes)
    cursor.execute("""
    ALTER TABLE annonces ADD COLUMN IF NOT EXISTS search_vector tsvector;
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
        "CREATE INDEX IF NOT EXISTS idx_annonces_search_vector ON annonces USING GIN(search_vector);",
    ]
    for statement in index_statements:
        cursor.execute(statement)

    connexion.commit()
    cursor.close()
    connexion.close()


def create_fulltext_search_trigger():
    """
    Crée la fonction de trigger et le trigger pour maintenir le vecteur search_vector
    dans la table annonces lors des INSERT/UPDATE.
    """
    connexion = get_connection()
    cursor = connexion.cursor()

    # Créer la fonction trigger
    cursor.execute("""
    CREATE OR REPLACE FUNCTION update_annonce_search_vector() RETURNS trigger AS $$
    BEGIN
        NEW.search_vector := 
            setweight(to_tsvector('french', COALESCE(NEW.title, '')), 'A') ||
            setweight(to_tsvector('french', COALESCE(NEW.city, '')), 'B') ||
            setweight(to_tsvector('french', COALESCE(NEW.type_bien, '')), 'B') ||
            setweight(to_tsvector('french', COALESCE(NEW.source_site, '')), 'C') ||
            setweight(to_tsvector('french', COALESCE(NEW.agency, '')), 'C') ||
            setweight(to_tsvector('french', COALESCE(NEW.department, '')), 'C') ||
            setweight(to_tsvector('french', COALESCE(NEW.zip_code, '')), 'C');
        RETURN NEW;
    END
    $$ LANGUAGE plpgsql;
    """)

    # Créer le trigger
    cursor.execute("""
    DROP TRIGGER IF EXISTS trg_update_annonce_search_vector ON annonces;
    """)

    cursor.execute("""
    CREATE TRIGGER trg_update_annonce_search_vector
    BEFORE INSERT OR UPDATE ON annonces
    FOR EACH ROW
    EXECUTE FUNCTION update_annonce_search_vector();
    """)

    connexion.commit()
    cursor.close()
    connexion.close()
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
        locked_until TIMESTAMP(0),
        created_at TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP(0);
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    """)

    connexion.commit()
    cursor.close()
    connexion.close()


def create_login_attempts_table():
    """
    Cree l'historique des tentatives de connexion pour detecter le brute force.
    """
    connexion = get_connection()
    cursor = connexion.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS login_attempts (
        id SERIAL PRIMARY KEY,
        email TEXT NOT NULL,
        ip_address TEXT,
        success BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP
    );
    """)

    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_login_attempts_email_created_at ON login_attempts(lower(email), created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_created_at ON login_attempts(ip_address, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_login_attempts_success ON login_attempts(success);",
    ]
    for statement in index_statements:
        cursor.execute(statement)

    connexion.commit()
    cursor.close()
    connexion.close()


def populate_fulltext_search_vector():
    """
    Remplit la colonne search_vector pour toutes les annonces existantes.
    À appeler une seule fois après create_fulltext_search_trigger().
    """
    connexion = get_connection()
    cursor = connexion.cursor()

    cursor.execute("""
    UPDATE annonces
    SET search_vector = 
        setweight(to_tsvector('french', COALESCE(title, '')), 'A') ||
        setweight(to_tsvector('french', COALESCE(city, '')), 'B') ||
        setweight(to_tsvector('french', COALESCE(type_bien, '')), 'B') ||
        setweight(to_tsvector('french', COALESCE(source_site, '')), 'C') ||
        setweight(to_tsvector('french', COALESCE(agency, '')), 'C') ||
        setweight(to_tsvector('french', COALESCE(department, '')), 'C') ||
        setweight(to_tsvector('french', COALESCE(zip_code, '')), 'C')
    WHERE search_vector IS NULL;
    """)

    cursor.execute("SELECT ROW_COUNT() as count;")
    row_count = cursor.fetchone()
    
    connexion.commit()
    cursor.close()
    connexion.close()
    
    return row_count[0] if row_count else 0
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


def create_enrichment_tables():
    """
    Cree les tables d'enrichissement cadastre et urbanisme.
    Les geometries sont stockees en JSONB pour rester utilisables sans extension PostGIS.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS parcelles (
        id SERIAL PRIMARY KEY,
        parcel_key TEXT NOT NULL UNIQUE,
        commune_code TEXT,
        section TEXT,
        numero TEXT,
        contenance NUMERIC,
        centroid_lat NUMERIC,
        centroid_lon NUMERIC,
        geometry_json JSONB,
        raw_data JSONB,
        created_at TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS annonce_enrichments (
        id SERIAL PRIMARY KEY,
        annonce_id INTEGER NOT NULL UNIQUE REFERENCES annonces(id) ON DELETE CASCADE,
        status TEXT NOT NULL DEFAULT 'pending',
        latitude NUMERIC,
        longitude NUMERIC,
        parcel_id INTEGER REFERENCES parcelles(id),
        parcel_key TEXT,
        zip_code TEXT,
        zonage TEXT,
        prescriptions JSONB DEFAULT '[]'::jsonb,
        servitudes JSONB DEFAULT '[]'::jsonb,
        documents JSONB DEFAULT '[]'::jsonb,
        raw_geocode JSONB,
        raw_cadastre JSONB,
        raw_gpu JSONB,
        geocode_status TEXT,
        cadastre_status TEXT,
        gpu_status TEXT,
        geocode_score NUMERIC,
        geocode_type TEXT,
        geocode_query TEXT,
        diagnostic_message TEXT,
        error_message TEXT,
        enriched_at TIMESTAMP(0),
        created_at TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP
    );
    """)

    alter_statements = [
        "ALTER TABLE annonce_enrichments ADD COLUMN IF NOT EXISTS geocode_status TEXT;",
        "ALTER TABLE annonce_enrichments ADD COLUMN IF NOT EXISTS cadastre_status TEXT;",
        "ALTER TABLE annonce_enrichments ADD COLUMN IF NOT EXISTS gpu_status TEXT;",
        "ALTER TABLE annonce_enrichments ADD COLUMN IF NOT EXISTS geocode_score NUMERIC;",
        "ALTER TABLE annonce_enrichments ADD COLUMN IF NOT EXISTS geocode_type TEXT;",
        "ALTER TABLE annonce_enrichments ADD COLUMN IF NOT EXISTS geocode_query TEXT;",
        "ALTER TABLE annonce_enrichments ADD COLUMN IF NOT EXISTS diagnostic_message TEXT;",
    ]
    for statement in alter_statements:
        cur.execute(statement)

    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_parcelles_commune_code ON parcelles(commune_code);",
        "CREATE INDEX IF NOT EXISTS idx_annonce_enrichments_annonce_id ON annonce_enrichments(annonce_id);",
        "CREATE INDEX IF NOT EXISTS idx_annonce_enrichments_zip_code ON annonce_enrichments(zip_code);",
        "CREATE INDEX IF NOT EXISTS idx_annonce_enrichments_parcel_id ON annonce_enrichments(parcel_id);",
        "CREATE INDEX IF NOT EXISTS idx_annonce_enrichments_status ON annonce_enrichments(status);",
        "CREATE INDEX IF NOT EXISTS idx_annonce_enrichments_zonage ON annonce_enrichments(zonage);",
    ]
    for statement in index_statements:
        cur.execute(statement)

    conn.commit()
    cur.close()
    conn.close()


def create_annonces_archive_table():
    """
    Cree une table d'archive pour conserver un historique des annonces purgees.
    Les enrichissements associes sont stockes en snapshot JSONB avant suppression.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS annonces_archive (
        archive_id SERIAL PRIMARY KEY,
        annonce_id INTEGER,
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
        last_seen TIMESTAMP(0),
        enrichment_snapshot JSONB,
        archived_at TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
        purge_reason TEXT,
        UNIQUE(annonce_id, last_seen)
    );
    """)

    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_annonces_archive_annonce_id ON annonces_archive(annonce_id);",
        "CREATE INDEX IF NOT EXISTS idx_annonces_archive_url ON annonces_archive(url);",
        "CREATE INDEX IF NOT EXISTS idx_annonces_archive_zip_code ON annonces_archive(zip_code);",
        "CREATE INDEX IF NOT EXISTS idx_annonces_archive_archived_at ON annonces_archive(archived_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_annonces_archive_last_seen ON annonces_archive(last_seen DESC);",
    ]
    for statement in index_statements:
        cur.execute(statement)

    conn.commit()
    cur.close()
    conn.close()


def create_automation_tables():
    """
    Cree la table de suivi des executions automatisees.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS automation_runs (
        id SERIAL PRIMARY KEY,
        run_type TEXT NOT NULL DEFAULT 'full',
        status TEXT NOT NULL DEFAULT 'running',
        started_at TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP(0),
        duration_seconds NUMERIC,
        log_path TEXT,
        summary JSONB DEFAULT '{}'::jsonb,
        error_message TEXT
    );
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_automation_runs_started_at
    ON automation_runs(started_at DESC);
    """)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_automation_runs_status
    ON automation_runs(status);
    """)

    conn.commit()
    cur.close()
    conn.close()


def create_all_tables():
    """
    Crée toutes les tables nécessaires dans la base de données.
    """
    create_tables()
    create_fulltext_search_trigger()
    create_users_table()
    create_login_attempts_table()
    create_dvf_tables()
    create_table_stats()
    create_enrichment_tables()
    create_annonces_archive_table()
    create_automation_tables()

if __name__ == "__main__":
    create_all_tables()
    print("Tables créées avec succès")
