from psycopg2.extras import Json

from database.connection import get_connection


ANNONCE_SELECT = """
    a.id,
    a.title,
    a.city,
    a.zip_code,
    a.department,
    a.url,
    a.source_site
"""


def fetch_annonces_to_enrich(limit=100, refresh_days=30):
    sql = f"""
        SELECT {ANNONCE_SELECT}
        FROM annonces a
        LEFT JOIN annonce_enrichments e ON e.annonce_id = a.id
        WHERE e.id IS NULL
           OR e.status IN ('pending', 'failed')
           OR e.enriched_at IS NULL
           OR e.enriched_at < CURRENT_TIMESTAMP - (%s * INTERVAL '1 day')
        ORDER BY a.last_seen DESC NULLS LAST, a.id DESC
        LIMIT %s
    """

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, (refresh_days, limit))
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "city": row[2],
            "zip_code": row[3],
            "department": row[4],
            "url": row[5],
            "source_site": row[6],
        }
        for row in rows
    ]


def upsert_parcelle(parcel, latitude=None, longitude=None):
    sql = """
        INSERT INTO parcelles (
            parcel_key, commune_code, section, numero, contenance,
            centroid_lat, centroid_lon, geometry_json, raw_data, updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (parcel_key) DO UPDATE
        SET commune_code = EXCLUDED.commune_code,
            section = EXCLUDED.section,
            numero = EXCLUDED.numero,
            contenance = EXCLUDED.contenance,
            centroid_lat = EXCLUDED.centroid_lat,
            centroid_lon = EXCLUDED.centroid_lon,
            geometry_json = EXCLUDED.geometry_json,
            raw_data = EXCLUDED.raw_data,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id;
    """

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            sql,
            (
                parcel["parcel_key"],
                parcel.get("commune_code"),
                parcel.get("section"),
                parcel.get("numero"),
                parcel.get("contenance"),
                latitude,
                longitude,
                Json(parcel.get("geometry_json")),
                Json(parcel.get("raw_data")),
            ),
        )
        parcel_id = cur.fetchone()[0]
        conn.commit()
        return parcel_id
    finally:
        cur.close()
        conn.close()


def upsert_enrichment(enrichment):
    sql = """
        INSERT INTO annonce_enrichments (
            annonce_id, status, latitude, longitude, parcel_id, parcel_key, zip_code,
            zonage, prescriptions, servitudes, documents,
            raw_geocode, raw_cadastre, raw_gpu,
            geocode_status, cadastre_status, gpu_status,
            geocode_score, geocode_type, geocode_query, diagnostic_message,
            error_message, enriched_at, updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        ON CONFLICT (annonce_id) DO UPDATE
        SET status = EXCLUDED.status,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            parcel_id = EXCLUDED.parcel_id,
            parcel_key = EXCLUDED.parcel_key,
            zip_code = EXCLUDED.zip_code,
            zonage = EXCLUDED.zonage,
            prescriptions = EXCLUDED.prescriptions,
            servitudes = EXCLUDED.servitudes,
            documents = EXCLUDED.documents,
            raw_geocode = EXCLUDED.raw_geocode,
            raw_cadastre = EXCLUDED.raw_cadastre,
            raw_gpu = EXCLUDED.raw_gpu,
            geocode_status = EXCLUDED.geocode_status,
            cadastre_status = EXCLUDED.cadastre_status,
            gpu_status = EXCLUDED.gpu_status,
            geocode_score = EXCLUDED.geocode_score,
            geocode_type = EXCLUDED.geocode_type,
            geocode_query = EXCLUDED.geocode_query,
            diagnostic_message = EXCLUDED.diagnostic_message,
            error_message = EXCLUDED.error_message,
            enriched_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id;
    """

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            sql,
            (
                enrichment["annonce_id"],
                enrichment["status"],
                enrichment.get("latitude"),
                enrichment.get("longitude"),
                enrichment.get("parcel_id"),
                enrichment.get("parcel_key"),
                enrichment.get("zip_code"),
                enrichment.get("zonage"),
                Json(enrichment.get("prescriptions") or []),
                Json(enrichment.get("servitudes") or []),
                Json(enrichment.get("documents") or []),
                Json(enrichment.get("raw_geocode")),
                Json(enrichment.get("raw_cadastre")),
                Json(enrichment.get("raw_gpu")),
                enrichment.get("geocode_status"),
                enrichment.get("cadastre_status"),
                enrichment.get("gpu_status"),
                enrichment.get("geocode_score"),
                enrichment.get("geocode_type"),
                enrichment.get("geocode_query"),
                enrichment.get("diagnostic_message"),
                enrichment.get("error_message"),
            ),
        )
        enrichment_id = cur.fetchone()[0]
        conn.commit()
        return enrichment_id
    finally:
        cur.close()
        conn.close()
