ALTER TABLE annonces
ADD COLUMN IF NOT EXISTS first_seen TIMESTAMP(0);

UPDATE annonces
SET first_seen = last_seen
WHERE first_seen IS NULL;

ALTER TABLE annonces
ALTER COLUMN first_seen SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE annonces_archive
ADD COLUMN IF NOT EXISTS first_seen TIMESTAMP(0);

UPDATE annonces_archive
SET first_seen = last_seen
WHERE first_seen IS NULL;

CREATE INDEX IF NOT EXISTS idx_annonces_first_seen
ON annonces(first_seen);

CREATE INDEX IF NOT EXISTS idx_annonces_rooms
ON annonces(rooms);

CREATE INDEX IF NOT EXISTS idx_annonces_price_square_meter
ON annonces(price_square_meter);

CREATE INDEX IF NOT EXISTS idx_annonces_energy_class
ON annonces(energy_class);

CREATE INDEX IF NOT EXISTS idx_parcelles_contenance
ON parcelles(contenance);
