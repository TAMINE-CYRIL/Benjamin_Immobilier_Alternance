from utils.cleaning import (
    classify_annonce,
    deduplicate_annonces,
    extract_number,
    normalisation_language,
    normalize_annonce,
    normalize_annonces,
)


def test_extract_number():
    assert extract_number("250 000 â‚¬") == 250000.0
    assert extract_number("1 200 000") == 1200000.0
    assert extract_number("450.75") == 450.75
    assert extract_number("1,200.50 â‚¬") == 1200.50
    assert extract_number("2.500,75 â‚¬") == 2500.75
    assert extract_number("300k") == 300000.0
    assert extract_number("1.2M") == 1200000.0
    assert extract_number("300 â‚¬/m2") == 300.0
    assert extract_number("Une chaine de caractere") is None
    assert extract_number("N/A") is None
    assert extract_number("") is None


def test_normalisation_language():
    assert normalisation_language("1,200.50") == "1200.50"
    assert normalisation_language("2.500,75") == "2500.75"
    assert normalisation_language("1.500.000") == "1500000"
    assert normalisation_language("1,500,000") == "1500000"
    assert normalisation_language("3.000.000,75") == "3000000.75"
    assert normalisation_language("3,000,000.75") == "3000000.75"


def test_normalize_annonce_keeps_existing_surface():
    annonce = normalize_annonce(
        {
            "url": "http://example.com",
            "price": "300000",
            "surface": "60",
            "price_square_meter": "4900",
            "zip_code": "13001",
            "type_bien": "Appartement",
        }
    )
    assert annonce["surface"] == 60.0
    assert annonce["price_square_meter"] == 4900.0
    assert annonce["department"] == "13"


def test_normalize_annonce_computes_missing_surface():
    annonce = normalize_annonce(
        {
            "url": "http://example.com",
            "price": "300000",
            "price_square_meter": "5000",
        }
    )
    assert annonce["surface"] == 60.0


def test_normalize_annonce_computes_missing_price_square_meter():
    annonce = normalize_annonce(
        {
            "url": "http://example.com",
            "price": "300000",
            "surface": "75",
        }
    )
    assert annonce["price_square_meter"] == 4000.0


def test_normalize_annonce_invalid_values_become_none():
    annonce = normalize_annonce(
        {
            "url": "http://example.com",
            "price": "-1",
            "surface": "0",
            "price_square_meter": "-4",
            "zip_code": "abc",
        }
    )
    assert annonce["price"] is None
    assert annonce["surface"] is None
    assert annonce["price_square_meter"] is None
    assert annonce["zip_code"] is None


def test_normalize_annonce_extracts_missing_zip_code_from_city():
    annonce = normalize_annonce(
        {
            "url": "http://example.com",
            "city": "Toulon (83200)",
            "type_bien": "Maison",
            "price_square_meter": "4280",
        }
    )
    assert annonce["zip_code"] == "83200"
    assert annonce["department"] == "83"
    assert classify_annonce(annonce) == "valid_scoring"


def test_classify_annonce_accepts_non_scorable_annonce():
    annonce = normalize_annonce(
        {
            "url": "http://example.com",
            "city": "Marseille",
            "price": "250000",
        }
    )
    assert classify_annonce(annonce) == "valid_no_scoring"


def test_normalize_annonces_summary_counts():
    annonces, summary = normalize_annonces(
        [
            {"url": "http://1", "zip_code": "13001", "type_bien": "Appartement", "price_square_meter": "4500"},
            {"url": "http://2", "city": "Marseille"},
            {"title": "Sans URL"},
        ]
    )
    assert len(annonces) == 3
    assert summary["valid_scoring"] == 1
    assert summary["valid_no_scoring"] == 1
    assert summary["skipped"] == 1


def test_deduplicate_annonces_removes_cross_site_duplicate():
    annonces, _ = normalize_annonces(
        [
            {
                "url": "https://www.logic-immo.com/detail",
                "source_site": "LogicImmo",
                "city": "Marseille",
                "zip_code": "13001",
                "price": "250000",
                "surface": "50",
                "rooms": "3",
                "type_bien": "Appartement",
            },
            {
                "url": "https://www.seloger.com/detail",
                "source_site": "SeLoger",
                "city": "marseille",
                "zip_code": "13001",
                "price": "250 000 EUR",
                "surface": "50 m2",
                "rooms": "3",
                "type_bien": "appartement",
            },
            {
                "url": "https://www.seloger.com/autre",
                "source_site": "SeLoger",
                "city": "Marseille",
                "zip_code": "13001",
                "price": "260000",
                "surface": "50",
                "rooms": "3",
                "type_bien": "Appartement",
            },
        ]
    )

    deduplicated, summary = deduplicate_annonces(annonces)

    assert len(deduplicated) == 2
    assert summary["removed"] == 1
    assert summary["input_total"] == 3
    assert summary["output_total"] == 2
    assert deduplicated[0]["url"] == "https://www.logic-immo.com/detail"
    assert summary["groups"][0]["duplicate_source"] == "SeLoger"
