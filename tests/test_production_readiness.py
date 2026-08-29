from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routes.auth import _client_ip
from services.jobs.validate_production import run_validation, validate_database, validate_frontend
from utils.production import validate_production_config


PRODUCTION_ENV = {
    "APP_ENV": "production",
    "PG_DB": "app",
    "PG_USER": "app",
    "PG_PASSWORD": "a-strong-database-password",
    "PG_HOST": "database.internal",
    "SMTP_HOST": "smtp.example.com",
    "SMTP_FROM": "notifications@example.com",
    "SMTP_USERNAME": "notifications@example.com",
    "SMTP_PASSWORD": "a-strong-smtp-password",
    "SMTP_USE_TLS": "true",
    "ALLOWED_HOSTS": "app.example.com",
    "API_CORS_ORIGINS": "https://app.example.com",
    "FRONTEND_BASE_URL": "https://app.example.com",
    "PASSWORD_RESET_BASE_URL": "https://app.example.com",
    "FORCE_HTTPS": "true",
    "AUTH_COOKIE_SECURE": "true",
    "ENRICHMENT_SSL_VERIFY": "true",
}


def _set_production_env(monkeypatch):
    for name, value in PRODUCTION_ENV.items():
        monkeypatch.setenv(name, value)


def test_production_config_accepts_hardened_settings(monkeypatch):
    _set_production_env(monkeypatch)

    validate_production_config()


def test_production_config_rejects_http_and_placeholder_password(monkeypatch):
    _set_production_env(monkeypatch)
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://app.example.com")
    monkeypatch.setenv("PG_PASSWORD", "change-me")

    with pytest.raises(RuntimeError) as exc:
        validate_production_config()

    assert "FRONTEND_BASE_URL" in str(exc.value)
    assert "PG_PASSWORD" in str(exc.value)


def test_production_validation_refuses_development_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")

    with pytest.raises(RuntimeError, match="APP_ENV"):
        run_validation(check_database=False, check_frontend=False)


def test_forwarded_ip_is_only_used_when_proxy_is_trusted(monkeypatch):
    request = SimpleNamespace(
        headers={"x-forwarded-for": "203.0.113.5, 10.0.0.2"},
        client=SimpleNamespace(host="10.0.0.10"),
    )
    monkeypatch.setenv("TRUST_PROXY", "false")
    assert _client_ip(request) == "10.0.0.10"

    monkeypatch.setenv("TRUST_PROXY", "true")
    assert _client_ip(request) == "203.0.113.5"


def test_health_endpoints_report_liveness_and_database_readiness():
    client = TestClient(app, base_url="http://localhost")
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value.fetchone.return_value = (1,)

    with patch("apps.api.routes.health.get_connection", return_value=connection):
        assert client.get("/api/health/live").json() == {"status": "ok"}
        assert client.get("/api/health/ready").json() == {"status": "ok"}


def test_health_readiness_hides_database_error_details():
    client = TestClient(app, base_url="http://localhost")

    with patch("apps.api.routes.health.get_connection", side_effect=RuntimeError("secret details")):
        response = client.get("/api/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


def test_database_validation_rejects_missing_migrations():
    cursor = MagicMock()
    cursor.fetchall.return_value = []
    cursor.fetchone.side_effect = [(1,), (1,)]
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor

    with patch("services.jobs.validate_production.get_connection", return_value=connection):
        with pytest.raises(RuntimeError, match="Migrations non appliquées"):
            validate_database()


def test_frontend_validation_requires_built_index(tmp_path):
    with pytest.raises(RuntimeError, match="Build frontend absent"):
        validate_frontend(tmp_path)

    index = tmp_path / "apps" / "web" / "dist" / "index.html"
    index.parent.mkdir(parents=True)
    index.write_text("ok", encoding="utf-8")
    validate_frontend(tmp_path)
