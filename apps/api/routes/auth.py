from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from apps.api.auth import clear_auth_cookie, create_access_token, set_auth_cookie, verify_password
from apps.api.auth import get_current_user
from apps.database.users_repo import get_user_by_email


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


def public_user(user):
    return {
        "id": user["id"],
        "email": user["email"],
        "is_active": user["is_active"],
        "created_at": user["created_at"],
    }


@router.post("/login")
def login(payload: LoginRequest, response: Response):
    user = get_user_by_email(payload.email)

    if not user or not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")

    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")

    token = create_access_token(user["id"])
    set_auth_cookie(response, token)
    return {"user": public_user(user)}


@router.post("/logout")
def logout(response: Response):
    clear_auth_cookie(response)
    return {"ok": True}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"user": public_user(user)}
