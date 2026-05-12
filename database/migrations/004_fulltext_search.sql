-- Migration 004: Full-Text Search PostgreSQL (Phase 1)
-- Ajoute la recherche textuelle full-text à la table annonces

-- 1. Ajouter la colonne search_vector
ALTER TABLE annonces ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- 2. Créer la fonction trigger pour maintenir le vecteur de recherche
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

-- 3. Créer le trigger
DROP TRIGGER IF EXISTS trg_update_annonce_search_vector ON annonces;
CREATE TRIGGER trg_update_annonce_search_vector
BEFORE INSERT OR UPDATE ON annonces
FOR EACH ROW
EXECUTE FUNCTION update_annonce_search_vector();

-- 4. Créer l'index GIN pour la recherche rapide
CREATE INDEX IF NOT EXISTS idx_annonces_search_vector ON annonces USING GIN(search_vector);

-- 5. Remplir le vecteur pour les annonces existantes (à faire une seule fois)
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
