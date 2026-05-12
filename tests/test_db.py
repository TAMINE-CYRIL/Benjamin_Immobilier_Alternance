import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from database.db import create_tables, get_connection, insert_annonces
from database.reset_db import cleanup
from database.score_annonce import score_annonces
from main_immo import _scrape_with_optional_max_pages, run_pipeline


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


def test_cleanup_archives_before_deleting_old_annonces():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.__enter__.return_value = mock_conn
    mock_cursor.rowcount = 3

    with patch("database.reset_db.create_annonces_archive_table") as mock_create_archive:
        with patch("database.reset_db.get_connection", return_value=mock_conn):
            deleted = cleanup(days=30, logger=MagicMock())

    assert deleted == 3
    assert mock_create_archive.called
    assert mock_cursor.execute.call_count == 2
    archive_sql = mock_cursor.execute.call_args_list[0].args[0]
    delete_sql = mock_cursor.execute.call_args_list[1].args[0]
    assert "INSERT INTO annonces_archive" in archive_sql
    assert "DELETE FROM annonces" in delete_sql
    assert mock_cursor.execute.call_args_list[0].args[1] == ("last_seen older than 30 days", 30)
    assert mock_cursor.execute.call_args_list[1].args[1] == (30,)


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


def test_run_pipeline_deduplicates_before_db_insert():
    args = SimpleNamespace(
        source=None,
        max_pages=1,
        no_db=False,
        no_score=True,
        output_json=None,
    )

    async def logic_builder(_max_pages):
        return [
            {
                "url": "https://www.logic-immo.com/detail",
                "city": "Marseille",
                "zip_code": "13001",
                "price": "250000",
                "surface": "50",
                "rooms": "3",
                "type_bien": "Appartement",
            }
        ]

    async def seloger_builder(_max_pages):
        return [
            {
                "url": "https://www.seloger.com/detail",
                "city": "Marseille",
                "zip_code": "13001",
                "price": "250 000 EUR",
                "surface": "50 m2",
                "rooms": "3",
                "type_bien": "Appartement",
            }
        ]

    with patch(
        "main_immo.build_source_registry",
        return_value=[
            {"name": "LogicImmo", "enabled": True, "builder": logic_builder},
            {"name": "SeLoger", "enabled": True, "builder": seloger_builder},
        ],
    ), patch("main_immo.insert_annonces") as mock_insert:
        mock_insert.return_value = {
            "total": 1,
            "inserted": 1,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "skip_reasons": {},
            "processed_ids": [42],
        }
        annonces, summary = __import__("asyncio").run(run_pipeline(args))

    assert len(annonces) == 1
    assert summary["normalized_before_dedup"] == 2
    assert summary["normalized_total"] == 1
    assert summary["deduplicated"] == 1
    mock_insert.assert_called_once()
    assert len(mock_insert.call_args.args[0]) == 1


def test_optional_max_pages_preserves_scraper_default_when_not_overridden():
    async def fake_scraper(max_pages=7, use_proxies=False):
        return max_pages, use_proxies

    default_result = __import__("asyncio").run(
        _scrape_with_optional_max_pages(fake_scraper, max_pages=None, use_proxies=True)
    )
    overridden_result = __import__("asyncio").run(
        _scrape_with_optional_max_pages(fake_scraper, max_pages=3, use_proxies=True)
    )

    assert default_result == (7, True)
    assert overridden_result == (3, True)
