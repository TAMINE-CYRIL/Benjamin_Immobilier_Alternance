from fastapi.testclient import TestClient
from unittest.mock import patch

from apps.api.auth import get_current_user
from apps.api.main import app


def test_security_headers_are_added_to_api_responses():
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "email": "a@example.com", "is_active": True}
    client = TestClient(app, base_url="http://localhost")

    try:
        with patch("apps.api.routes.annonces.search_annonces") as mock_search:
            mock_search.return_value = {"items": [], "total": 0, "page": 1, "page_size": 25}
            response = client.get("/api/annonces")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


def test_csrf_is_required_for_mutating_api_routes():
    client = TestClient(app, base_url="http://localhost")

    response = client.post("/api/auth/logout")

    assert response.status_code == 403
    assert response.json()["detail"] == "Jeton CSRF invalide"


def test_csrf_accepts_double_submit_token_for_mutating_api_routes():
    client = TestClient(app, base_url="http://localhost")
    client.cookies.set("csrf_token", "known-token")

    response = client.post("/api/auth/logout", headers={"X-CSRF-Token": "known-token"})

    assert response.status_code == 200


def test_password_reset_confirm_is_exempt_from_csrf():
    client = TestClient(app, base_url="http://localhost")

    with patch("apps.api.routes.auth.consume_password_reset_token", return_value=None):
        response = client.post(
            "/api/auth/password-reset/confirm",
            json={"token": "bad-token", "new_password": "nouveau-mdp"},
        )

    assert response.status_code == 400


def test_password_reset_request_is_exempt_from_csrf():
    client = TestClient(app, base_url="http://localhost")

    with patch("apps.api.routes.auth.create_password_reset_token", return_value=None):
        response = client.post(
            "/api/auth/password-reset/request",
            json={"email": "user@example.com"},
        )

    assert response.status_code == 200


def test_jobs_runs_requires_authenticated_user():
    client = TestClient(app, base_url="http://localhost")

    response = client.get("/api/jobs/runs")

    assert response.status_code == 401


def test_jobs_runs_authenticated_access_is_audited():
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1,
        "email": "user@example.com",
        "is_active": True,
    }
    client = TestClient(app, base_url="http://localhost")

    try:
        with patch("apps.api.routes.jobs.list_runs", return_value=[]) as list_runs:
            with patch("apps.api.routes.jobs.record_audit_event") as audit_event:
                response = client.get("/api/jobs/runs?limit=5")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    list_runs.assert_called_once_with(limit=5)
    audit_event.assert_called_once()
