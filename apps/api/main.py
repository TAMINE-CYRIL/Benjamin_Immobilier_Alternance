import hmac
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from apps.api.auth import CSRF_COOKIE_NAME, validate_security_config
from apps.api.routes.auth import router as auth_router
from apps.api.routes.annonces import router as annonces_router
from apps.api.routes.jobs import router as jobs_router
from apps.api.routes.health import router as health_router
from utils.production import validate_production_config

load_dotenv()




@asynccontextmanager
async def lifespan(_app):
    validate_security_config()
    validate_production_config()
    yield


app = FastAPI(title="Benjamin Immobilier API", lifespan=lifespan)


def _csv_env(name):
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


def _env_bool(name, default=False):
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.lower() in {"1", "true", "yes", "on"}


if _env_bool("FORCE_HTTPS", default=False):
    app.add_middleware(HTTPSRedirectMiddleware)

allowed_hosts = _csv_env("ALLOWED_HOSTS")
if allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

cors_origins = _csv_env("API_CORS_ORIGINS")
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )


@app.middleware("http")
async def csrf_protection(request, call_next):
    unsafe_method = request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}
    csrf_exempt_paths = {
        "/api/auth/login",
        "/api/auth/password-reset/request",
        "/api/auth/password-reset/confirm",
    }
    if unsafe_method and request.url.path.startswith("/api") and request.url.path not in csrf_exempt_paths:
        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        csrf_header = request.headers.get("x-csrf-token")
        if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header):
            return JSONResponse(status_code=403, content={"detail": "Jeton CSRF invalide"})
    return await call_next(request)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    response.headers.setdefault("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'; base-uri 'self'")
    if _env_bool("FORCE_HTTPS", default=False) or os.getenv("APP_ENV", "").lower() in {"prod", "production"}:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


app.include_router(auth_router, prefix="/api")
app.include_router(annonces_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(health_router, prefix="/api")
