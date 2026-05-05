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

CREATE INDEX IF NOT EXISTS idx_annonces_archive_annonce_id ON annonces_archive(annonce_id);
CREATE INDEX IF NOT EXISTS idx_annonces_archive_url ON annonces_archive(url);
CREATE INDEX IF NOT EXISTS idx_annonces_archive_zip_code ON annonces_archive(zip_code);
CREATE INDEX IF NOT EXISTS idx_annonces_archive_archived_at ON annonces_archive(archived_at DESC);
CREATE INDEX IF NOT EXISTS idx_annonces_archive_last_seen ON annonces_archive(last_seen DESC);
