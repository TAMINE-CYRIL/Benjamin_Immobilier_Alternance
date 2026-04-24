import json
from pathlib import Path

import pytest

from utils.cleaning import normalize_annonce


def test_espace_atypique_schema_extracts_city_and_zip_from_listing_html():
    bs4 = pytest.importorskip("bs4")

    schema = json.loads(Path("schema/immobilier/espace_atypique.json").read_text(encoding="utf-8"))
    fields = {field["name"]: field["selector"] for field in schema["fields"]}

    html = """
    <div class="preview-annonce">
      <div class="infos">
        <span class="info upc orange localisation font2">
          <span class="ville">HYERES</span>
          <span>83400</span>
        </span>
      </div>
    </div>
    """

    soup = bs4.BeautifulSoup(html, "html.parser")
    card = soup.select_one(schema["baseSelector"])

    assert card.select_one(fields["city"]).get_text(strip=True) == "HYERES"
    assert card.select_one(fields["zip_code"]).get_text(strip=True) == "83400"


def test_normalize_annonce_keeps_listing_zip_code_and_computes_department():
    annonce = normalize_annonce(
        {
            "url": "https://example.com/annonce",
            "city": "HYERES",
            "zip_code": "83400",
            "price": "1990000",
            "surface": "170",
            "type_bien": "Maison",
        }
    )

    assert annonce["zip_code"] == "83400"
    assert annonce["department"] == "83"
