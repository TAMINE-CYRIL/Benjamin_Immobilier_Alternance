CREATE EXTENSION IF NOT EXISTS postgis;

ALTER TABLE annonce_enrichments
ADD COLUMN IF NOT EXISTS location geography(Point, 4326);

ALTER TABLE parcelles
ADD COLUMN IF NOT EXISTS geom geometry(Geometry, 4326);

CREATE INDEX IF NOT EXISTS idx_annonce_enrichments_location
ON annonce_enrichments USING GIST(location);

CREATE INDEX IF NOT EXISTS idx_parcelles_geom
ON parcelles USING GIST(geom);

UPDATE annonce_enrichments
SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
WHERE latitude IS NOT NULL
  AND longitude IS NOT NULL
  AND location IS NULL;

CREATE OR REPLACE FUNCTION safe_geom_from_geojson(geojson JSONB)
RETURNS geometry AS $$
BEGIN
    IF geojson IS NULL THEN
        RETURN NULL;
    END IF;

    RETURN ST_SetSRID(ST_MakeValid(ST_GeomFromGeoJSON(geojson::text)), 4326);
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

UPDATE parcelles
SET geom = safe_geom_from_geojson(geometry_json)
WHERE geometry_json IS NOT NULL
  AND geom IS NULL;
