from services.enrichment.cadastre import CadastreClient, parse_parcel
from services.enrichment.geo import AddressClient, build_search_queries
from services.enrichment.gpu import GpuClient
from services.enrichment.orchestrator import EnrichmentService


class FakeHttpClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get_json(self, url, params=None):
        self.calls.append((url, params))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_address_client_geocodes_first_feature():
    client = AddressClient(
        http_client=FakeHttpClient(
            [
                {
                    "features": [
                        {
                            "geometry": {"coordinates": [5.3698, 43.2965]},
                            "properties": {"label": "Marseille"},
                        }
                    ]
                }
            ]
        )
    )

    result = client.geocode_annonce({"title": "Appartement", "city": "Marseille", "zip_code": "13001"})

    assert result["status"] == "success"
    assert result["latitude"] == 43.2965
    assert result["longitude"] == 5.3698


def test_address_client_prefers_street_then_city_zip_queries():
    queries = build_search_queries(
        {
            "title": "Maison avenue de la Republique avec jardin",
            "city": "Marseille",
            "zip_code": "13001",
        }
    )

    assert queries[0] == "avenue de la Republique avec jardin Marseille 13001"
    assert "Marseille 13001" in queries


def test_address_client_rejects_low_score():
    client = AddressClient(
        http_client=FakeHttpClient(
            [
                {
                    "features": [
                        {
                            "geometry": {"coordinates": [5.3698, 43.2965]},
                            "properties": {"label": "Marseille", "score": 0.2, "type": "municipality"},
                        }
                    ]
                }
            ]
        ),
        min_score=0.45,
    )

    result = client.geocode_annonce({"city": "Marseille", "zip_code": "13001"})

    assert result["status"] == "low_confidence"
    assert result["score"] == 0.2


def test_parse_parcel_uses_properties_identifier():
    parcel = parse_parcel(
        {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": []},
            "properties": {
                "id": "13055-001-A-42",
                "code_insee": "13055",
                "section": "A",
                "numero": "42",
                "contenance": 800,
            },
        }
    )

    assert parcel["parcel_key"] == "13055-001-A-42"
    assert parcel["contenance"] == 800


def test_cadastre_client_returns_none_when_no_feature():
    client = CadastreClient(http_client=FakeHttpClient([{"features": []}]))

    assert client.find_parcel(43.2965, 5.3698) is None


def test_gpu_client_collects_zone_prescriptions_and_servitudes():
    client = GpuClient(
        http_client=FakeHttpClient(
            [
                {"features": [{"properties": {"libelle": "Zone UA"}}]},
                {"features": [{"properties": {"libelle": "Prescription surf"}}]},
                {"features": []},
                {"features": []},
                {"features": [{"properties": {"libelle": "SUP surf"}}]},
                {"features": []},
                {"features": []},
            ]
        )
    )

    result = client.fetch_urbanism(43.2965, 5.3698)

    assert result["zonage"] == "Zone UA"
    assert len(result["prescriptions"]) == 1
    assert len(result["servitudes"]) == 1


def test_enrichment_service_stores_not_found(monkeypatch):
    stored = []

    monkeypatch.setattr("services.enrichment.orchestrator.upsert_enrichment", lambda enrichment: stored.append(enrichment))

    class EmptyAddressClient:
        def geocode_annonce(self, annonce):
            return {"status": "not_found", "diagnostic": "Aucun resultat"}

    service = EnrichmentService(address_client=EmptyAddressClient())
    result = service.enrich_annonce({"id": 12, "city": "Inconnue"})

    assert result["status"] == "not_found"
    assert result["geocode_status"] == "not_found"
    assert result["diagnostic_message"] == "Aucun resultat"
    assert stored[0]["annonce_id"] == 12


def test_enrichment_service_success_does_not_duplicate_parcel(monkeypatch):
    stored = []
    parcels = []

    monkeypatch.setattr("services.enrichment.orchestrator.upsert_enrichment", lambda enrichment: stored.append(enrichment))
    monkeypatch.setattr("services.enrichment.orchestrator.upsert_parcelle", lambda parcel, latitude, longitude: parcels.append(parcel) or 99)

    class OkAddressClient:
        def geocode_annonce(self, annonce):
            return {
                "status": "success",
                "latitude": 43.2965,
                "longitude": 5.3698,
                "score": 0.91,
                "result_type": "housenumber",
                "query": "1 rue Test Marseille",
                "raw": {"label": "Marseille"},
            }

    class OkCadastreClient:
        def find_parcel(self, latitude, longitude):
            return {
                "parcel_key": "13055-A-42",
                "geometry_json": {"type": "Polygon", "coordinates": []},
                "raw_response": {"features": []},
            }

    class OkGpuClient:
        def fetch_urbanism(self, latitude, longitude, geometry=None):
            return {
                "zonage": "UA",
                "prescriptions": [],
                "servitudes": [],
                "documents": [],
                "raw": {},
            }

    service = EnrichmentService(
        address_client=OkAddressClient(),
        cadastre_client=OkCadastreClient(),
        gpu_client=OkGpuClient(),
    )
    result = service.enrich_annonce({"id": 42, "city": "Marseille"})

    assert result["status"] == "success"
    assert result["geocode_status"] == "success"
    assert result["cadastre_status"] == "success"
    assert result["gpu_status"] == "success"
    assert result["parcel_id"] == 99
    assert parcels[0]["parcel_key"] == "13055-A-42"
    assert stored[0]["zonage"] == "UA"


def test_enrichment_service_success_with_zonage_without_parcel(monkeypatch):
    stored = []

    monkeypatch.setattr("services.enrichment.orchestrator.upsert_enrichment", lambda enrichment: stored.append(enrichment))

    class OkAddressClient:
        def geocode_annonce(self, annonce):
            return {"status": "success", "latitude": 43.2965, "longitude": 5.3698, "raw": {}}

    class EmptyCadastreClient:
        def find_parcel(self, latitude, longitude):
            return None

    class OkGpuClient:
        def fetch_urbanism(self, latitude, longitude, geometry=None):
            return {"zonage": "UB", "prescriptions": [], "servitudes": [], "documents": [], "raw": {}}

    service = EnrichmentService(
        address_client=OkAddressClient(),
        cadastre_client=EmptyCadastreClient(),
        gpu_client=OkGpuClient(),
    )
    result = service.enrich_annonce({"id": 43, "city": "Marseille"})

    assert result["status"] == "success"
    assert result["cadastre_status"] == "not_found"
    assert result["gpu_status"] == "success"
    assert "zonage urbanisme trouves" in result["diagnostic_message"]


def test_enrichment_service_partial_with_only_coordinates(monkeypatch):
    stored = []

    monkeypatch.setattr("services.enrichment.orchestrator.upsert_enrichment", lambda enrichment: stored.append(enrichment))

    class OkAddressClient:
        def geocode_annonce(self, annonce):
            return {"status": "success", "latitude": 43.2965, "longitude": 5.3698, "raw": {}}

    class EmptyCadastreClient:
        def find_parcel(self, latitude, longitude):
            return None

    class EmptyGpuClient:
        def fetch_urbanism(self, latitude, longitude, geometry=None):
            return {"zonage": None, "prescriptions": [], "servitudes": [], "documents": [], "raw": {}}

    service = EnrichmentService(
        address_client=OkAddressClient(),
        cadastre_client=EmptyCadastreClient(),
        gpu_client=EmptyGpuClient(),
    )
    result = service.enrich_annonce({"id": 44, "city": "Marseille"})

    assert result["status"] == "partial"
    assert result["diagnostic_message"] == "Enrichissement partiel: parcelle introuvable, zonage urbanisme absent"
