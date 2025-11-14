import os
from unittest.mock import mock_open, patch, MagicMock
from utils.db import create_tables, get_connection, insert_annonces


def test_get_connection():
    """
    Vérifie que psycopg2.connect est appelé avec les bonnes variables d'environnement.
    """
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
            port="5432"
        )


def test_create_tables():
    """
    Vérifie que la requête CREATE TABLE est bien exécutée.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch("psycopg2.connect", return_value=mock_conn):
        create_tables()

        mock_cursor.execute.assert_called_once() 
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()


def test_insert_annonces():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch("psycopg2.connect", return_value=mock_conn):
        annonces = [{
            "title": "Test",
            "url": "http://example.com",
            "address": "Rue 123",
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
        }]

        insert_annonces(annonces)

        assert mock_cursor.execute.call_count == 1

        mock_conn.commit.assert_called_once()

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()


def test_insert_annonces_skipped_no_url():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    annonces = [{"title": "Test", "url": ""}]  

    with patch("psycopg2.connect", return_value=mock_conn):
        with patch("builtins.open", mock_open()): 
            insert_annonces(annonces)

    mock_cursor.execute.assert_not_called()

    mock_conn.commit.assert_called_once()



def test_insert_annonces_insert():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.rowcount = 1

    annonces = [{
        "title": "Test",
        "url": "http://example.com",
        "address": "",
        "surface": None,
        "price": None,
        "adjuged_price": None,
        "zip_code": "",
        "rooms": None,
        "price_square_meter": None,
        "agency": "",
        "source_site": "",
        "type_bien": "",
        "energy_class": "",
        "sale_date": "",
        "visit_date": "",
    }]

    with patch("psycopg2.connect", return_value=mock_conn):
        with patch("builtins.open", mock_open()):
            insert_annonces(annonces)

    assert mock_cursor.execute.call_count == 1
    mock_conn.commit.assert_called_once()



def test_insert_annonces_update():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.rowcount = 0

    annonces = [{
        "title": "Test",
        "url": "http://example.com",
    }]

    with patch("psycopg2.connect", return_value=mock_conn):
        with patch("builtins.open", mock_open()):
            insert_annonces(annonces)

    assert mock_cursor.execute.call_count == 1
    mock_conn.commit.assert_called_once()



def test_insert_annonces_sql_error():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.execute.side_effect = Exception("SQL ERROR")

    annonces = [{
        "title": "Test",
        "url": "http://example.com",
    }]

    with patch("psycopg2.connect", return_value=mock_conn):
        with patch("builtins.open", mock_open()):
            insert_annonces(annonces)

    mock_conn.rollback.assert_called_once()

    mock_conn.commit.assert_called_once()
