import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional

import bcrypt
from fastapi import Cookie, Depends, HTTPException, Response, status

from apps.database.users_repo import get_user_by_id


COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME", "access_token")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", "86400"))
COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"


def hash_password(password):
    """
    Hash le mot de passe en utilisant bcrypt et retourne la version hachée.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password, password_hash):
    """
    Vérifie que le mot de passe correspond au hash stocké en utilisant bcrypt.
    """
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _b64encode(payload):
    """
    Renvoie une chaîne encodée en base64 URL-safe sans les caractères de padding "=".
    """
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _b64decode(payload):
    """
    Renvoie les données décodées à partir d'une chaîne encodée en base64 URL-safe, en ajoutant les caractères de padding "=" si nécessaire.
    """
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding)


def create_access_token(user_id):
    """
    Crée un token d'accès JWT pour l'utilisateur.
    """
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    body = {"sub": str(user_id), "iat": now, "exp": now + JWT_TTL_SECONDS}

    signing_input = ".".join([
        _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
        _b64encode(json.dumps(body, separators=(",", ":")).encode("utf-8")),
    ])
    signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_b64encode(signature)}"


def decode_access_token(token):
    """
    Décode un token d'accès JWT et retourne le payload.
    """
    try:
        header_b64, body_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from exc

    signing_input = f"{header_b64}.{body_b64}"
    expected_signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()

    try:
        signature = _b64decode(signature_b64)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from exc

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = json.loads(_b64decode(body_b64))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from exc

    if payload.get("exp", 0) < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return payload


def set_auth_cookie(response, token):
    """
    Met en place le cookie de connexion avec le token d'accès JWT.
    """
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=JWT_TTL_SECONDS,
        path="/",
    )


def clear_auth_cookie(response):
    """
    Efface le cookie de connexion.
    """
    response.delete_cookie(COOKIE_NAME, path="/")


def get_current_user(access_token: Optional[str] = Cookie(default=None, alias=COOKIE_NAME)):
    """
    Récupère l'utilisateur actuellement authentifié à partir du cookie d'authentification.
    Si le token est invalide ou expiré, ou si l'utilisateur n'existe pas
    """
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    payload = decode_access_token(access_token)
    user = get_user_by_id(payload.get("sub"))

    if not user or not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return user
