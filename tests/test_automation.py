from unittest.mock import MagicMock, patch

from database.automation_runs import create_run, finish_run, list_runs
from services.jobs.run_automation import _status_from_stages


def test_automation_status_detects_partial_success():
    status = _status_from_stages(
        {
            "scraping": {"status": "partial_success"},
            "enrichment": {"status": "success"},
            "cleanup": {"status": "success"},
        }
    )

    assert status == "partial_success"


def test_automation_status_detects_failed_stage():
    status = _status_from_stages(
        {
            "scraping": {"status": "success"},
            "enrichment": {"status": "failed"},
        }
    )

    assert status == "failed"


def test_create_run_inserts_running_record():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (12, "2026-04-28 10:00:00")

    with patch("database.automation_runs.get_connection", return_value=mock_conn):
        run = create_run(log_path="logs/run.log")

    assert run["id"] == 12
    mock_conn.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_finish_run_updates_status_and_summary():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch("database.automation_runs.get_connection", return_value=mock_conn):
        finish_run(12, "success", summary={"ok": True})

    assert mock_cursor.execute.call_args.args[1][0] == "success"
    assert mock_cursor.execute.call_args.args[1][-1] == 12
    mock_conn.commit.assert_called_once()


def test_list_runs_caps_limit():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        (1, "full", "success", "start", "end", 10, "logs/run.log", {"status": "success"}, None)
    ]

    with patch("database.automation_runs.get_connection", return_value=mock_conn):
        runs = list_runs(limit=500)

    assert len(runs) == 1
    assert runs[0]["status"] == "success"
    assert mock_cursor.execute.call_args.args[1] == (100,)
