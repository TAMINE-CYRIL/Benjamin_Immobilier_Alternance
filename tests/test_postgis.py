from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from apps.api.auth import get_current_user
from apps.api.main import app
from apps.database.annonces_repo import _build_filters, search_annonces
from services.enrichment.repository import upsert_enrichment, upsert_parcelle


ROOT = Path(__file__).resolve().parents[1]


def _mock_connection():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (0,)
    mock_cursor.fetchall.return_value = []
    return mock_conn, mock_cursor


def test_postgis_migration_adds_extension_columns_indexes_and_backfill():
    sql = (ROOT / "database" / "migrations" / "008_postgis.sql").read_text(encoding="utf-8")

    assert "CREATE EXTENSION IF NOT EXISTS postgis" in sql
    assert "location geography(Point, 4326)" in sql
    assert "geom geometry(Geometry, 4326)" in sql
    assert "USING GIST(location)" in sql
    assert "USING GIST(geom)" in sql
    assert "ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography" in sql
    assert "safe_geom_from_geojson(geometry_json)" in sql


def test_build_filters_adds_radius_filter_only_with_complete_geo_parameters():
    clauses, params = _build_filters({
        "center_lat": 43.2965,
        "center_lon": 5.3698,
        "radius_km": 10,
    })

    assert any("ST_DWithin" in clause for clause in clauses)
    assert params == [5.3698, 43.2965, 10000.0]

    partial_clauses, partial_params = _build_filters({"center_lat": 43.2965})
    assert not any("ST_DWithin" in clause for clause in partial_clauses)
    assert partial_params == []


def test_search_annonces_returns_distance_and_sorts_nearest_first():
    mock_conn, mock_cursor = _mock_connection()
    mock_cursor.fetchone.return_value = (1,)
    mock_cursor.fetchall.return_value = [tuple(list(range(37)) + [1234.5])]

    with patch("apps.database.annonces_repo.get_connection", return_value=mock_conn):
        result = search_annonces({
            "center_lat": 43.2965,
            "center_lon": 5.3698,
            "radius_km": 10,
            "sort": "distance",
        })

    data_sql = mock_cursor.execute.call_args_list[1].args[0]
    data_params = mock_cursor.execute.call_args_list[1].args[1]

    assert "ST_Distance" in data_sql
    assert "AS distance_m" in data_sql
    assert "ORDER BY distance_m ASC" in data_sql
    assert data_params[:5] == [5.3698, 43.2965, 5.3698, 43.2965, 10000.0]
    assert result["items"][0]["distance_m"] == 1234.5


def test_annonces_route_validates_geo_filter_completeness_and_distance_sort():
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "is_active": True}
    client = TestClient(app, base_url="http://localhost")

    try:
        partial_response = client.get("/api/annonces?center_lat=43.2965")
        distance_response = client.get("/api/annonces?sort=distance")
        invalid_lat_response = client.get("/api/annonces?center_lat=120&center_lon=5.3698&radius_km=10")

        with patch("apps.api.routes.annonces.search_annonces") as mock_search:
            mock_search.return_value = {"items": [], "total": 0, "page": 1, "page_size": 25}
            valid_response = client.get(
                "/api/annonces?center_lat=43.2965&center_lon=5.3698&radius_km=10&sort=distance"
            )
    finally:
        app.dependency_overrides.clear()

    assert partial_response.status_code == 422
    assert distance_response.status_code == 422
    assert invalid_lat_response.status_code == 422
    assert valid_response.status_code == 200
    assert mock_search.call_args.args[0]["center_lat"] == 43.2965
    assert mock_search.call_args.args[0]["center_lon"] == 5.3698
    assert mock_search.call_args.args[0]["radius_km"] == 10
    assert mock_search.call_args.args[0]["sort"] == "distance"


def test_upsert_enrichment_writes_postgis_location_expression():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (12,)

    with patch("services.enrichment.repository.get_connection", return_value=mock_conn):
        upsert_enrichment({
            "annonce_id": 1,
            "status": "success",
            "latitude": 43.2965,
            "longitude": 5.3698,
        })

    sql = mock_cursor.execute.call_args.args[0]
    params = mock_cursor.execute.call_args.args[1]

    assert "location" in sql
    assert "ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography" in sql
    assert params[2:8] == (43.2965, 5.3698, 43.2965, 5.3698, 5.3698, 43.2965)


def test_upsert_parcelle_writes_postgis_geometry_expression():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (99,)

    with patch("services.enrichment.repository.get_connection", return_value=mock_conn):
        upsert_parcelle({
            "parcel_key": "13055-A-42",
            "geometry_json": {"type": "Polygon", "coordinates": []},
        })

    sql = mock_cursor.execute.call_args.args[0]

    assert "geom" in sql
    assert "safe_geom_from_geojson(%s::jsonb)" in sql
