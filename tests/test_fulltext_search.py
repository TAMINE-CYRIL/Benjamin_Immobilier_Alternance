"""
Tests pour le full-text search PostgreSQL (Phase 1).
"""

import pytest
from unittest.mock import MagicMock, patch
from apps.database.annonces_repo import search_annonces, _fulltext_tsquery, _build_filters


def test_fulltext_tsquery_valid():
    """Test de la fonction _fulltext_tsquery avec une requête valide."""
    query = "maison marseille"
    result = _fulltext_tsquery(query)
    assert result is not None
    assert "plainto_tsquery" in result


def test_fulltext_tsquery_empty():
    """Test de la fonction _fulltext_tsquery avec une requête vide."""
    result = _fulltext_tsquery("")
    assert result is None
    
    result = _fulltext_tsquery(None)
    assert result is None


def test_build_filters_with_fulltext_query():
    """Test que _build_filters utilise le full-text search pour les requêtes textuelle."""
    filters = {"query": "maison duplex"}
    clauses, params = _build_filters(filters)
    
    # Vérifier que clauses contient la requête full-text
    assert len(clauses) > 0
    assert "search_vector @@" in clauses[0]
    assert "plainto_tsquery" in clauses[0]
    
    # Vérifier les paramètres
    assert len(params) > 0
    assert params[0] == "maison duplex"


def test_build_filters_with_city():
    """Test que _build_filters gère le filtre city correctement."""
    filters = {"city": "marseille"}
    clauses, params = _build_filters(filters)
    
    # Doit contenir un filtre pour la ville
    assert len(clauses) > 0
    assert any("city" in clause.lower() for clause in clauses)


def test_build_filters_with_price_range():
    """Test que _build_filters gère les filtres price_min et price_max."""
    filters = {"price_min": 100000, "price_max": 500000}
    clauses, params = _build_filters(filters)
    
    # Doit contenir des clauses pour price
    assert len(clauses) >= 2
    assert any(">=" in clause for clause in clauses)
    assert any("<=" in clause for clause in clauses)
    
    # Vérifier les paramètres
    assert 100000 in params
    assert 500000 in params


def test_build_filters_with_module3_business_filters():
    clauses, params = _build_filters({
        "rooms_min": 2,
        "rooms_max": 5,
        "price_m2_min": 2500,
        "price_m2_max": 6000,
        "score_max": 80,
        "energy_class": "d",
        "parcel_surface_min": 300,
        "parcel_surface_max": 1200,
        "has_parcel": True,
        "recent_days": 7,
    })

    sql = " ".join(clauses)
    assert "a.rooms >= %s" in sql
    assert "a.rooms <= %s" in sql
    assert "a.price_square_meter >= %s" in sql
    assert "a.score <= %s" in sql
    assert "UPPER(a.energy_class) = %s" in sql
    assert "p.contenance >= %s" in sql
    assert "e.parcel_id IS NOT NULL" in sql
    assert "a.first_seen >= CURRENT_TIMESTAMP" in sql
    assert params == [ "D", 80, 2, 5, 2500, 6000, 300, 1200, 7]


def test_search_annonces_basic():
    """Test basique de search_annonces sans filtre."""
    with patch("apps.database.annonces_repo.get_connection") as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [0]  # COUNT
        mock_cursor.fetchall.return_value = []  # SELECT
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = search_annonces({})
        
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert result["total"] == 0
        assert result["items"] == []


def test_search_annonces_with_sort_relevance():
    """Test que search_annonces accepte le tri 'relevance'."""
    with patch("apps.database.annonces_repo.get_connection") as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [1]
        # Mock une ligne retournée avec les colonnes attendues (38 colonnes + relevance_rank)
        mock_row = list(range(38)) + [0.8]
        mock_cursor.fetchall.return_value = [tuple(mock_row)]
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        search_annonces({
            "query": "maison",
            "sort": "relevance",
            "direction": "desc"
        })
        
        # Vérifier que la requête a été exécutée (on ne peut pas vérifier le contenu exact 
        # car c'est très complexe avec le mock)
        assert mock_cursor.execute.called


def test_search_annonces_pagination():
    """Test que la pagination fonctionne correctement."""
    with patch("apps.database.annonces_repo.get_connection") as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [100]  # Total
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = search_annonces({"page": 2, "page_size": 50})
        
        assert result["page"] == 2
        assert result["page_size"] == 50
        assert result["total"] == 100


def test_search_annonces_page_size_limits():
    """Test que page_size est limité au maximum."""
    with patch("apps.database.annonces_repo.get_connection") as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [0]
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Demander page_size trop grand
        result = search_annonces({"page_size": 500})
        
        # Doit être limité à 100
        assert result["page_size"] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
