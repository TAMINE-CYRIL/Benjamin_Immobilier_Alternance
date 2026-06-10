from services.deals import COMPONENT_WEIGHTS, evaluate_opportunity


STATS = {"q1": 10, "median": 20, "q3": 40}


def test_scoring_v2_is_explainable_and_components_match_total():
    result = evaluate_opportunity(
        {
            "title": "Terrain divisible à fort potentiel",
            "description": "Maison à rénover avec dépendance",
            "price_square_meter": 2800,
            "surface": 120,
            "parcel_surface": 900,
            "type_bien": "Maison",
            "energy_class": "E",
        },
        dvf_reference={"prix_m2_med": 3500, "nb_transactions": 30},
        transaction_stats=STATS,
    )

    assert result["version"] == "2.1"
    assert result["total"] == round(sum(result["components"].values()), 1)
    assert set(result["components"]) == set(COMPONENT_WEIGHTS)
    assert "urbanism" not in result["components"]
    assert result["confidence"] >= 80
    assert result["risk_level"] == "low"
    assert any("médiane DVF" in reason for reason in result["reasons"])
    for name, value in result["components"].items():
        assert 0 <= value <= COMPONENT_WEIGHTS[name]


def test_scoring_v2_reports_low_confidence_and_risks():
    result = evaluate_opportunity(
        {
            "title": "Terrain non constructible en indivision",
            "price_square_meter": None,
            "type_bien": "Terrain",
        },
        dvf_reference=None,
        transaction_stats=STATS,
    )

    assert result["confidence"] < 50
    assert result["risk_level"] == "high"
    assert "Terrain annoncé comme non constructible" in result["risks"]
    assert result["reasons"]


def test_scoring_v2_ignores_legacy_urbanism_data():
    annonce = {
        "title": "Maison avec jardin",
        "price_square_meter": 3000,
        "surface": 100,
        "parcel_surface": 500,
        "energy_class": "D",
    }
    reference = {"prix_m2_med": 3500, "nb_transactions": 30}

    without_zoning = evaluate_opportunity(annonce, reference, STATS)
    with_zoning = evaluate_opportunity(
        {**annonce, "zonage": "N", "servitudes": [{"label": "Passage"}]},
        reference,
        STATS,
    )

    assert with_zoning == without_zoning
