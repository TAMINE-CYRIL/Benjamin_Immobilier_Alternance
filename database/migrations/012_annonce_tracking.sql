ALTER TABLE annonces
ADD COLUMN IF NOT EXISTS business_status TEXT NOT NULL DEFAULT 'new',
ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMP(0);

UPDATE annonces SET business_status = 'new' WHERE business_status IS NULL;
UPDATE annonces SET is_favorite = FALSE WHERE is_favorite IS NULL;

CREATE INDEX IF NOT EXISTS idx_annonces_business_status ON annonces(business_status);
CREATE INDEX IF NOT EXISTS idx_annonces_is_favorite ON annonces(is_favorite);

ALTER TABLE annonces_archive
ADD COLUMN IF NOT EXISTS business_status TEXT,
ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN,
ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMP(0);
