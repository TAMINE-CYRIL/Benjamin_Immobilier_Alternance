from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException, Response

from apps.api.routes.auth import (
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    confirm_password_reset,
    login,
    request_password_reset,
)
from apps.api.auth import create_access_token, set_auth_cookie


def _request(ip="127.0.0.1"):
    return SimpleNamespace(headers={}, client=SimpleNamespace(host=ip))


def test_login_records_failed_attempt_for_bad_password():
    user = {
        "id": 1,
        "email": "test@example.com",
        "password_hash": "hash",
        "is_active": True,
        "created_at": "now",
        "locked_until": None,
    }

    with patch("apps.api.routes.auth.count_recent_failed_attempts", return_value=0):
        with patch("apps.api.routes.auth.count_recent_failed_attempts_by_ip", return_value=0):
            with patch("apps.api.routes.auth.get_user_by_email", return_value=user):
                with patch("apps.api.routes.auth.verify_password", return_value=False):
                    with patch("apps.api.routes.auth.record_audit_event") as audit_event:
                        with patch("apps.api.routes.auth.record_login_attempt") as record_attempt:
                            with pytest.raises(HTTPException) as exc:
                                login(
                                    LoginRequest(email="test@example.com", password="bad"),
                                    _request(),
                                    Response(),
                                )

    assert exc.value.status_code == 401
    record_attempt.assert_called_once_with("test@example.com", "127.0.0.1", success=False)
    audit_event.assert_called_once()


def test_login_blocks_when_failed_attempt_limit_is_reached():
    with patch("apps.api.routes.auth.count_recent_failed_attempts", return_value=5):
        with patch("apps.api.routes.auth.count_recent_failed_attempts_by_ip", return_value=0):
            with pytest.raises(HTTPException) as exc:
                login(
                    LoginRequest(email="test@example.com", password="bad"),
                    _request(),
                    Response(),
                )

    assert exc.value.status_code == 429


def test_login_blocks_when_ip_limit_is_reached():
    with patch("apps.api.routes.auth.count_recent_failed_attempts_by_ip", return_value=20):
        with pytest.raises(HTTPException) as exc:
            login(
                LoginRequest(email="test@example.com", password="bad"),
                _request(),
                Response(),
            )

    assert exc.value.status_code == 429


def test_login_blocks_locked_account_before_password_check():
    user = {
        "id": 1,
        "email": "test@example.com",
        "password_hash": "hash",
        "is_active": True,
        "created_at": "now",
        "locked_until": datetime.now() + timedelta(minutes=10),
    }

    with patch("apps.api.routes.auth.count_recent_failed_attempts", return_value=0):
        with patch("apps.api.routes.auth.count_recent_failed_attempts_by_ip", return_value=0):
            with patch("apps.api.routes.auth.get_user_by_email", return_value=user):
                with patch("apps.api.routes.auth.verify_password") as verify_password:
                    with pytest.raises(HTTPException) as exc:
                        login(
                            LoginRequest(email="test@example.com", password="good"),
                            _request(),
                            Response(),
                        )

    assert exc.value.status_code == 429
    verify_password.assert_not_called()


def test_failed_login_locks_account_at_limit():
    user = {
        "id": 1,
        "email": "test@example.com",
        "password_hash": "hash",
        "is_active": True,
        "created_at": "now",
        "locked_until": None,
    }

    with patch("apps.api.routes.auth.count_recent_failed_attempts", side_effect=[0, 5]):
        with patch("apps.api.routes.auth.count_recent_failed_attempts_by_ip", return_value=0):
            with patch("apps.api.routes.auth.get_user_by_email", return_value=user):
                with patch("apps.api.routes.auth.verify_password", return_value=False):
                    with patch("apps.api.routes.auth.record_audit_event"):
                        with patch("apps.api.routes.auth.record_login_attempt"):
                            with patch("apps.api.routes.auth.lock_user_for_minutes") as lock_user:
                                with pytest.raises(HTTPException) as exc:
                                    login(
                                        LoginRequest(email="test@example.com", password="bad"),
                                        _request(),
                                        Response(),
                                    )

    assert exc.value.status_code == 429
    lock_user.assert_called_once()


def test_successful_login_records_success_and_clears_failed_attempts():
    user = {
        "id": 1,
        "email": "test@example.com",
        "password_hash": "hash",
        "is_active": True,
        "created_at": "now",
        "locked_until": None,
    }

    with patch("apps.api.routes.auth.count_recent_failed_attempts", return_value=0):
        with patch("apps.api.routes.auth.count_recent_failed_attempts_by_ip", return_value=0):
            with patch("apps.api.routes.auth.get_user_by_email", return_value=user):
                with patch("apps.api.routes.auth.verify_password", return_value=True):
                        with patch("apps.api.routes.auth.create_access_token", return_value="token"):
                            with patch("apps.api.routes.auth.set_auth_cookie"):
                                with patch("apps.api.routes.auth.record_audit_event") as audit_event:
                                    with patch("apps.api.routes.auth.record_login_attempt") as record_attempt:
                                        with patch("apps.api.routes.auth.clear_failed_attempts") as clear_attempts:
                                            with patch("apps.api.routes.auth.clear_user_lock") as clear_lock:
                                                result = login(
                                                    LoginRequest(email="test@example.com", password="good"),
                                                    _request(),
                                                    Response(),
                                                )

    assert result["user"]["email"] == "test@example.com"
    record_attempt.assert_called_once_with("test@example.com", "127.0.0.1", success=True)
    audit_event.assert_called_once()
    clear_attempts.assert_called_once_with("test@example.com")
    clear_lock.assert_called_once_with(1)


def test_jwt_secret_default_is_rejected_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(RuntimeError):
        create_access_token(1)


def test_auth_cookie_is_secure_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "x" * 40)
    monkeypatch.delenv("AUTH_COOKIE_SECURE", raising=False)

    response = Response()
    set_auth_cookie(response, "token")

    set_cookie_headers = [
        value.decode("latin-1").lower()
        for key, value in response.raw_headers
        if key.decode("latin-1").lower() == "set-cookie"
    ]
    assert all("secure" in header for header in set_cookie_headers)
    assert any("httponly" in header for header in set_cookie_headers)


def test_password_reset_confirm_updates_password_and_audits():
    reset_target = {"user_id": 1, "email": "test@example.com"}

    with patch("apps.api.routes.auth.consume_password_reset_token", return_value=reset_target):
        with patch("apps.api.routes.auth.hash_password", return_value="new-hash") as hash_password_mock:
            with patch("apps.api.routes.auth.update_user_password") as update_password:
                with patch("apps.api.routes.auth.record_audit_event") as audit_event:
                    result = confirm_password_reset(
                        PasswordResetConfirmRequest(token="reset-token", new_password="nouveau-mdp"),
                        _request(),
                    )

    assert result == {"ok": True}
    hash_password_mock.assert_called_once_with("nouveau-mdp")
    update_password.assert_called_once_with(1, "new-hash")
    audit_event.assert_called_once()


def test_password_reset_confirm_rejects_invalid_token():
    with patch("apps.api.routes.auth.consume_password_reset_token", return_value=None):
        with patch("apps.api.routes.auth.record_audit_event") as audit_event:
            with pytest.raises(HTTPException) as exc:
                confirm_password_reset(
                    PasswordResetConfirmRequest(token="bad-token", new_password="nouveau-mdp"),
                    _request(),
                )

    assert exc.value.status_code == 400
    audit_event.assert_called_once()


def test_password_reset_confirm_rejects_short_password():
    with pytest.raises(HTTPException) as exc:
        confirm_password_reset(
            PasswordResetConfirmRequest(token="reset-token", new_password="short"),
            _request(),
        )

    assert exc.value.status_code == 422


def test_password_reset_request_sends_email_when_user_exists():
    reset = {
        "user_id": 1,
        "email": "test@example.com",
        "token": "reset-token",
        "expires_at": "later",
    }

    with patch("apps.api.routes.auth.create_password_reset_token", return_value=reset) as create_token:
        with patch("apps.api.routes.auth.send_email") as send_email:
            with patch("apps.api.routes.auth.record_audit_event") as audit_event:
                result = request_password_reset(
                    PasswordResetRequest(email="test@example.com"),
                    _request(),
                )

    assert result == {"ok": True}
    create_token.assert_called_once()
    send_email.assert_called_once()
    assert "reset-token" in send_email.call_args.args[2]
    audit_event.assert_called_once()


def test_password_reset_request_does_not_reveal_unknown_email():
    with patch("apps.api.routes.auth.create_password_reset_token", return_value=None):
        with patch("apps.api.routes.auth.send_email") as send_email:
            with patch("apps.api.routes.auth.record_audit_event") as audit_event:
                result = request_password_reset(
                    PasswordResetRequest(email="missing@example.com"),
                    _request(),
                )

    assert result == {"ok": True}
    send_email.assert_not_called()
    audit_event.assert_called_once()
