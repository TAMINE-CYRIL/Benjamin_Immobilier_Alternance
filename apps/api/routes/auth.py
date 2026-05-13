import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

from apps.api.auth import clear_auth_cookie, create_access_token, set_auth_cookie, verify_password
from apps.api.auth import get_current_user
from apps.database.login_attempts_repo import (
    clear_failed_attempts,
    count_recent_failed_attempts,
    count_recent_failed_attempts_by_ip,
    record_login_attempt,
)
from apps.database.users_repo import clear_user_lock, get_user_by_email, lock_user_for_minutes


router = APIRouter(prefix="/auth", tags=["auth"])

MAX_FAILED_LOGIN_ATTEMPTS = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
MAX_FAILED_LOGIN_ATTEMPTS_PER_IP = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS_PER_IP", "20"))
LOGIN_ATTEMPT_WINDOW_MINUTES = int(os.getenv("LOGIN_ATTEMPT_WINDOW_MINUTES", "15"))
ACCOUNT_LOCK_MINUTES = int(os.getenv("ACCOUNT_LOCK_MINUTES", str(LOGIN_ATTEMPT_WINDOW_MINUTES)))
LOGIN_BLOCK_MESSAGE = "Trop de tentatives. Reessayez plus tard."
IP_BLOCK_MESSAGE = "Trop de tentatives depuis cette adresse IP. Reessayez plus tard."
ACCOUNT_LOCK_MESSAGE = "Compte temporairement bloque. Reessayez plus tard."


class LoginRequest(BaseModel):
    """
    Classe de données pour la requête de login, avec validation des champs email et password.
    """
    email: str
    password: str


def public_user(user):
    """
    Retourne une représentation publique d'un utilisateur.
    """
    return {
        "id": user["id"],
        "email": user["email"],
        "is_active": user["is_active"],
        "created_at": user["created_at"],
    }


def _client_ip(request: Request):
    """
    Récupère l'adresse IP du client à partir de l'en-tête "x-forwarded-for" ou de la connexion directe.
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _assert_login_allowed(email):
    """
    Vérifie si l'adresse email n'a pas dépassé le nombre maximum de tentatives de connexion échouées.
    Si le nombre de tentatives échouées est trop élevé, lève une exception HTTP 429 Too Many Requests.
    """
    failed_attempts = count_recent_failed_attempts(email, LOGIN_ATTEMPT_WINDOW_MINUTES)
    if failed_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=LOGIN_BLOCK_MESSAGE,
        )


def _assert_ip_allowed(ip_address):
    """
    Vérifie si l'adresse IP n'a pas dépassé le nombre maximum de tentatives de connexion échouées.
    Si le nombre de tentatives échouées est trop élevé, lève une exception HTTP 429 Too Many Requests.
    """
    failed_attempts = count_recent_failed_attempts_by_ip(ip_address, LOGIN_ATTEMPT_WINDOW_MINUTES)
    if failed_attempts >= MAX_FAILED_LOGIN_ATTEMPTS_PER_IP:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=IP_BLOCK_MESSAGE,
        )


def _assert_account_unlocked(user):
    """
    Bloque l'accès si le compte de l'utilisateur est temporairement verrouillé en raison de trop nombreuses tentatives de connexion échouées.
    Si le compte est verrouillé, lève une exception HTTP 429 Too Many Requests.
    """
    locked_until = user.get("locked_until")
    if locked_until and locked_until > datetime.now():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ACCOUNT_LOCK_MESSAGE,
        )


def _record_failed_login(email, ip_address, user=None):
    """
    Enregistre une tentative de connexion échouée pour l'adresse email et l'adresse IP données.
    Si un utilisateur est fourni, vérifie si le compte doit être verrouillé en raison de trop nombreuses tentatives échouées, et verrouille le compte si nécessaire.
    """
    record_login_attempt(email, ip_address, success=False)
    failed_attempts = count_recent_failed_attempts(email, LOGIN_ATTEMPT_WINDOW_MINUTES)

    if user and failed_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
        lock_user_for_minutes(user["id"], ACCOUNT_LOCK_MINUTES)

    _assert_ip_allowed(ip_address)

    if failed_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=LOGIN_BLOCK_MESSAGE,
        )


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response):
    email = payload.email.strip()
    ip_address = _client_ip(request)

    _assert_ip_allowed(ip_address)
    _assert_login_allowed(email)

    user = get_user_by_email(email)

    if not user or not user.get("is_active"):
        _record_failed_login(email, ip_address)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")

    _assert_account_unlocked(user)

    if not verify_password(payload.password, user["password_hash"]):
        _record_failed_login(email, ip_address, user=user)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")

    record_login_attempt(email, ip_address, success=True)
    clear_failed_attempts(email)
    clear_user_lock(user["id"])
    token = create_access_token(user["id"])
    set_auth_cookie(response, token)
    return {"user": public_user(user)}


@router.post("/logout")
def logout(response: Response):
    """
    Déconnecte l'utilisateur en effaçant le cookie d'authentification.
    """
    clear_auth_cookie(response)
    return {"ok": True}


@router.get("/me")
def me(user=Depends(get_current_user)):
    """
    Retourne les informations de l'utilisateur actuellement authentifié.
    """
    return {"user": public_user(user)}
