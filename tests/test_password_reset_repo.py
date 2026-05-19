from unittest.mock import MagicMock, patch

from apps.database.password_reset_repo import consume_password_reset_token, create_password_reset_token


def _mock_connection():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    return mock_conn, mock_cursor


def test_create_password_reset_token_stores_hash_not_plain_token():
    mock_conn, mock_cursor = _mock_connection()
    mock_cursor.fetchone.side_effect = [
        (1, "user@example.com"),
        (10, "2026-05-19 12:00:00"),
    ]

    with patch("apps.database.password_reset_repo.get_connection", return_value=mock_conn):
        with patch("apps.database.password_reset_repo.secrets.token_urlsafe", return_value="plain-token"):
            reset = create_password_reset_token("user@example.com")

    insert_params = mock_cursor.execute.call_args_list[1].args[1]
    assert reset["token"] == "plain-token"
    assert "plain-token" not in insert_params
    assert len(insert_params[1]) == 64
    mock_conn.commit.assert_called_once()


def test_create_password_reset_token_returns_none_for_unknown_user():
    mock_conn, mock_cursor = _mock_connection()
    mock_cursor.fetchone.return_value = None

    with patch("apps.database.password_reset_repo.get_connection", return_value=mock_conn):
        reset = create_password_reset_token("missing@example.com")

    assert reset is None
    assert mock_cursor.execute.call_count == 1


def test_consume_password_reset_token_returns_user_when_valid():
    mock_conn, mock_cursor = _mock_connection()
    mock_cursor.fetchone.return_value = (1, "user@example.com")

    with patch("apps.database.password_reset_repo.get_connection", return_value=mock_conn):
        user = consume_password_reset_token("plain-token")

    assert user == {"user_id": 1, "email": "user@example.com"}
    sql = mock_cursor.execute.call_args.args[0]
    assert "used_at IS NULL" in sql
    assert "expires_at > CURRENT_TIMESTAMP" in sql
    mock_conn.commit.assert_called_once()
