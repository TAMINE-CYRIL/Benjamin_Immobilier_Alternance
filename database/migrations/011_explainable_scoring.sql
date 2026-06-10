ALTER TABLE annonces
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS score_confidence NUMERIC,
ADD COLUMN IF NOT EXISTS score_risk_level TEXT,
ADD COLUMN IF NOT EXISTS score_details JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS score_version TEXT,
ADD COLUMN IF NOT EXISTS scored_at TIMESTAMP(0);

ALTER TABLE annonces_archive
ADD COLUMN IF NOT EXISTS description TEXT,
ADD COLUMN IF NOT EXISTS score_confidence NUMERIC,
ADD COLUMN IF NOT EXISTS score_risk_level TEXT,
ADD COLUMN IF NOT EXISTS score_details JSONB,
ADD COLUMN IF NOT EXISTS score_version TEXT,
ADD COLUMN IF NOT EXISTS scored_at TIMESTAMP(0);

CREATE INDEX IF NOT EXISTS idx_annonces_score_confidence
ON annonces(score_confidence);

CREATE INDEX IF NOT EXISTS idx_annonces_score_risk_level
ON annonces(score_risk_level);
