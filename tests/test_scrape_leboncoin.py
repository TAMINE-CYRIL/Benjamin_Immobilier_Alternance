from scrapers.immobilier.scrape_leboncoin import (
    extract_property_details,
    normalize_leboncoin_location,
    site,
)


def test_leboncoin_schema_uses_current_ad_card_selector():
    assert site["wait_for"] == "css:div[data-qa-id='aditem_container']"
    assert site["schema"]["baseSelector"] == "div[data-qa-id='aditem_container']"


def test_extract_property_details_from_current_card_title():
    type_bien, rooms, surface = extract_property_details("Maison · 11 pièces · 824m²")

    assert type_bien == "Maison"
    assert rooms == 11
    assert surface == 824


def test_normalize_leboncoin_location_extracts_city_and_zip_code():
    city, zip_code = normalize_leboncoin_location("Nice 06100 Libération")

    assert city == "Nice"
    assert zip_code == "06100"
