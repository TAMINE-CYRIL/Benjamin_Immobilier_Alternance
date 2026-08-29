import os
from urllib.parse import urlparse


PRODUCTION_ENVS = {"prod", "production"}
PLACEHOLDER_VALUES = {
    "change-me",
    "replace-me",
    "password",
    "postgres",
}


def _env_bool(name, default=False):
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.lower() in {"1", "true", "yes", "on"}


def _csv_env(name):
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


def _is_https_url(value):
    parsed = urlparse(value or "")
    return parsed.scheme == "https" and bool(parsed.netloc)


def _is_placeholder(value):
    normalized = (value or "").strip().lower()
    return normalized in PLACEHOLDER_VALUES or "replace" in normalized or "change-me" in normalized


def validate_production_config():
    """Refuse un démarrage de production avec une configuration incomplète ou faible."""
    if os.getenv("APP_ENV", "development").lower() not in PRODUCTION_ENVS:
        return

    errors = []
    required = [
        "PG_DB",
        "PG_USER",
        "PG_PASSWORD",
        "PG_HOST",
        "SMTP_HOST",
        "SMTP_FROM",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "ALLOWED_HOSTS",
        "API_CORS_ORIGINS",
        "FRONTEND_BASE_URL",
        "PASSWORD_RESET_BASE_URL",
    ]
    for name in required:
        if not os.getenv(name, "").strip():
            errors.append(f"{name} est obligatoire")

    if not _env_bool("FORCE_HTTPS"):
        errors.append("FORCE_HTTPS doit être true")
    if not _env_bool("AUTH_COOKIE_SECURE"):
        errors.append("AUTH_COOKIE_SECURE doit être true")
    if not _env_bool("ENRICHMENT_SSL_VERIFY", default=True):
        errors.append("ENRICHMENT_SSL_VERIFY doit être true")
    if not _env_bool("SMTP_USE_TLS", default=True):
        errors.append("SMTP_USE_TLS doit être true")

    allowed_hosts = _csv_env("ALLOWED_HOSTS")
    if "*" in allowed_hosts:
        errors.append("ALLOWED_HOSTS ne doit pas contenir *")
    if any(host.lower() in {"localhost", "127.0.0.1"} for host in allowed_hosts):
        errors.append("ALLOWED_HOSTS doit utiliser le domaine de production")

    for name in ("FRONTEND_BASE_URL", "PASSWORD_RESET_BASE_URL"):
        value = os.getenv(name, "")
        if value and not _is_https_url(value):
            errors.append(f"{name} doit être une URL HTTPS")

    cors_origins = _csv_env("API_CORS_ORIGINS")
    if any(not _is_https_url(origin) for origin in cors_origins):
        errors.append("API_CORS_ORIGINS ne doit contenir que des origines HTTPS")

    database_password = os.getenv("PG_PASSWORD", "").strip()
    if _is_placeholder(database_password) or len(database_password) < 12:
        errors.append("PG_PASSWORD doit être un secret fort d'au moins 12 caractères")

    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    if _is_placeholder(smtp_password):
        errors.append("SMTP_PASSWORD ne doit pas être une valeur d'exemple")

    if errors:
        raise RuntimeError("Configuration production invalide : " + "; ".join(errors))
