from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException, Response

from apps.api.routes.auth import LoginRequest, login


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
                    with patch("apps.api.routes.auth.record_login_attempt") as record_attempt:
                        with pytest.raises(HTTPException) as exc:
                            login(
                                LoginRequest(email="test@example.com", password="bad"),
                                _request(),
                                Response(),
                            )

    assert exc.value.status_code == 401
    record_attempt.assert_called_once_with("test@example.com", "127.0.0.1", success=False)


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
    clear_attempts.assert_called_once_with("test@example.com")
    clear_lock.assert_called_once_with(1)
