from apps.database.annonces_repo import ANNONCE_FIELDS, _build_filters


def test_new_business_status_only_matches_annonces_seen_within_one_day():
    clauses, params = _build_filters({"business_status": "new"})

    sql = " ".join(clauses)
    assert "a.first_seen >= CURRENT_TIMESTAMP - INTERVAL '1 day'" in sql
    assert "THEN 'to_review'" in sql
    assert params == ["new"]


def test_returned_business_status_uses_the_same_one_day_rule():
    assert "a.first_seen >= CURRENT_TIMESTAMP - INTERVAL '1 day'" in ANNONCE_FIELDS
    assert "AS business_status" in ANNONCE_FIELDS
