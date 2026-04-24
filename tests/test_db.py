import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from database.db import create_tables, get_connection, insert_annonces
from database.score_annonce import score_annonces
from main_immo import run_pipeline


def test_get_connection():
    with patch("psycopg2.connect") as mock_connect:
        os.environ["PG_DB"] = "testdb"
        os.environ["PG_USER"] = "testuser"
        os.environ["PG_PASSWORD"] = "pwd"
        os.environ["PG_HOST"] = "localhost"
        os.environ["PG_PORT"] = "5432"

        get_connection()

        mock_connect.assert_called_once_with(
            dbname="testdb",
            user="testuser",
            password="pwd",
            host="localhost",
            port="5432",
        )


def test_create_tables():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch("psycopg2.connect", return_value=mock_conn):
        create_tables()

    assert mock_cursor.execute.call_count >= 1
    mock_conn.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_insert_annonces_returns_structured_summary():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (42, True)

    annonces = [
        {
            "title": "Test",
            "url": "http://example.com",
            "city": "Rue 123",
            "surface": 50,
            "price": 300000,
            "adjuged_price": 280000,
            "zip_code": "75000",
            "rooms": 2,
            "price_square_meter": 6000,
            "agency": "TestAgence",
            "source_site": "X",
            "type_bien": "Appartement",
            "energy_class": "D",
            "sale_date": "2024-01-01",
            "visit_date": "2024-01-05",
        }
    ]

    with patch("psycopg2.connect", return_value=mock_conn):
        summary = insert_annonces(annonces)

    assert summary["inserted"] == 1
    assert summary["updated"] == 0
    assert summary["processed_ids"] == [42]
    mock_conn.commit.assert_called_once()


def test_insert_annonces_skips_missing_url():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch("psycopg2.connect", return_value=mock_conn):
        summary = insert_annonces([{"title": "Sans URL", "url": ""}])

    mock_cursor.execute.assert_not_called()
    assert summary["skipped"] == 1
    assert summary["skip_reasons"]["missing_url"] == 1
    mock_conn.commit.assert_called_once()


def test_insert_annonces_handles_sql_error():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = [None, Exception("SQL ERROR"), None]

    with patch("psycopg2.connect", return_value=mock_conn):
        summary = insert_annonces([{"title": "Test", "url": "http://example.com"}])

    mock_conn.commit.assert_called_once()
    assert summary["errors"] == 1
    assert summary["skip_reasons"]["sql_error"] == 1


def test_score_annonces_ignores_missing_fields_without_error():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        (1, None, "13001", "Appartement", "C"),
        (2, 5000, None, "Appartement", "C"),
    ]

    with patch("database.score_annonce.get_connection", return_value=mock_conn):
        summary = score_annonces([1, 2])

    assert summary["eligible_for_scoring"] == 0
    assert summary["not_scored_missing_fields"] == 2
    assert summary["scored"] == 0


def test_score_annonces_handles_missing_reference():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [(1, 5000, "13001", "Appartement", "C")]
    mock_cursor.fetchone.return_value = None

    with patch("database.score_annonce.get_connection", return_value=mock_conn):
        summary = score_annonces([1])

    assert summary["eligible_for_scoring"] == 1
    assert summary["not_scored_no_reference"] == 1
    assert summary["scored"] == 0


def test_run_pipeline_respects_flags_and_avoids_duplicates():
    args = SimpleNamespace(
        source=None,
        max_pages=1,
        no_db=True,
        no_score=True,
        output_json=None,
    )

    async def success_builder(_max_pages):
        return [
            {"url": "http://1", "zip_code": "13001", "type_bien": "Appartement", "price_square_meter": "4000"},
            {"url": "http://2", "city": "Marseille"},
        ]

    async def failing_builder(_max_pages):
        raise RuntimeError("boom")

    with patch(
        "main_immo.build_source_registry",
        return_value=[
            {"name": "Success", "enabled": True, "builder": success_builder},
            {"name": "Fail", "enabled": True, "builder": failing_builder},
        ],
    ):
        annonces, summary = __import__("asyncio").run(run_pipeline(args))

    assert len(annonces) == 2
    assert summary["normalized_total"] == 2
    assert summary["failed_sources"] == ["Fail"]
    assert summary["status"] == "partial_success"
