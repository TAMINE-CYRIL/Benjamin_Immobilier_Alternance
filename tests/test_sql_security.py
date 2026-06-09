from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from apps.api.auth import get_current_user
from apps.api.main import app
from apps.database.annonces_repo import search_annonces


def _mock_connection():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (0,)
    mock_cursor.fetchall.return_value = []
    return mock_conn, mock_cursor


def test_search_annonces_keeps_text_filter_in_sql_parameters():
    mock_conn, mock_cursor = _mock_connection()
    payload = "%' OR 1=1; DROP TABLE users; --"

    with patch("apps.database.annonces_repo.get_connection", return_value=mock_conn):
        search_annonces({"source_site": payload})

    count_sql = mock_cursor.execute.call_args_list[0].args[0]
    count_params = mock_cursor.execute.call_args_list[0].args[1]

    assert payload not in count_sql
    assert "ILIKE %s" in count_sql
    assert "ESCAPE '\\'" in count_sql
    assert count_params == [r"%\%' OR 1=1; DROP TABLE users; --%"]


def test_search_annonces_normalizes_city_filter():
    mock_conn, mock_cursor = _mock_connection()

    with patch("apps.database.annonces_repo.get_connection", return_value=mock_conn):
        search_annonces({"city": "Aix en Provence"})

    count_sql = mock_cursor.execute.call_args_list[0].args[0]
    count_params = mock_cursor.execute.call_args_list[0].args[1]

    assert "regexp_replace" in count_sql
    assert "translate(lower(COALESCE(a.city, ''))" in count_sql
    assert count_params[-1] == "%aix%en%provence%"


def test_search_annonces_builds_global_query_with_parameters():
    mock_conn, mock_cursor = _mock_connection()
    payload = "Marseille % _"

    with patch("apps.database.annonces_repo.get_connection", return_value=mock_conn):
        search_annonces({"query": payload})

    count_sql = mock_cursor.execute.call_args_list[0].args[0]
    count_params = mock_cursor.execute.call_args_list[0].args[1]

    assert payload not in count_sql
    assert "a.search_vector @@ plainto_tsquery('french', %s)" in count_sql
    assert count_params == [payload]


def test_search_annonces_ignores_malicious_sort_and_direction_values():
    mock_conn, mock_cursor = _mock_connection()

    with patch("apps.database.annonces_repo.get_connection", return_value=mock_conn):
        search_annonces({
            "sort": "price; DROP TABLE users; --",
            "direction": "asc; DROP TABLE users; --",
        })

    data_sql = mock_cursor.execute.call_args_list[1].args[0]

    assert "DROP TABLE" not in data_sql
    assert "ORDER BY a.score DESC" in data_sql


def test_annonces_route_rejects_invalid_sort_parameter():
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "is_active": True}
    client = TestClient(app, base_url="http://localhost")

    try:
        response = client.get("/api/annonces?sort=price;DROP TABLE users")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_annonces_route_rejects_invalid_zip_code_parameter():
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "is_active": True}
    client = TestClient(app, base_url="http://localhost")

    try:
        response = client.get("/api/annonces?zip_code=75000';DROP TABLE users")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_annonces_route_accepts_global_query_parameter():
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "is_active": True}
    client = TestClient(app, base_url="http://localhost")

    try:
        with patch("apps.api.routes.annonces.search_annonces") as mock_search:
            mock_search.return_value = {"items": [], "total": 0, "page": 1, "page_size": 25}
            response = client.get("/api/annonces?query=Marseille")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert mock_search.call_args.args[0]["query"] == "Marseille"


def test_annonces_route_validates_ranges_and_relevance_sort():
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "is_active": True}
    client = TestClient(app, base_url="http://localhost")

    try:
        invalid_range = client.get("/api/annonces?rooms_min=5&rooms_max=2")
        missing_query = client.get("/api/annonces?sort=relevance")
        with patch("apps.api.routes.annonces.search_annonces") as mock_search:
            mock_search.return_value = {"items": [], "total": 0, "page": 1, "page_size": 25}
            valid = client.get(
                "/api/annonces?query=terrain&sort=relevance&energy_class=D"
                "&recent_days=7&has_parcel=true&parcel_surface_min=300"
            )
    finally:
        app.dependency_overrides.clear()

    assert invalid_range.status_code == 422
    assert missing_query.status_code == 422
    assert valid.status_code == 200
    filters = mock_search.call_args.args[0]
    assert filters["sort"] == "relevance"
    assert filters["energy_class"] == "D"
    assert filters["recent_days"] == 7
    assert filters["has_parcel"] is True
    assert filters["parcel_surface_min"] == 300
