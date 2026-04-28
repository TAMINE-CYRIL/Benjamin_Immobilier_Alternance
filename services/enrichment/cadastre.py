import json
import os

from services.enrichment.http_client import JsonHttpClient


CADASTRE_API_URL = os.getenv("CADASTRE_API_URL", "https://apicarto.ign.fr/api/cadastre/parcelle")


def point_geometry(latitude, longitude):
    return {
        "type": "Point",
        "coordinates": [float(longitude), float(latitude)],
    }


def first_feature(payload):
    features = payload.get("features") if isinstance(payload, dict) else None
    if features:
        return features[0]
    return None


def parcel_key_from_properties(properties):
    for key in ("id", "idu", "id_parcelle", "numero_complet", "parcelle"):
        value = properties.get(key)
        if value:
            return str(value)

    parts = [
        properties.get("code_insee") or properties.get("commune"),
        properties.get("prefixe"),
        properties.get("section"),
        properties.get("numero"),
    ]
    key = "-".join(str(part) for part in parts if part not in (None, ""))
    return key or None


def parse_parcel(feature):
    properties = feature.get("properties") or {}
    geometry = feature.get("geometry")
    parcel_key = parcel_key_from_properties(properties)
    if not parcel_key:
        return None

    return {
        "parcel_key": parcel_key,
        "commune_code": properties.get("code_insee") or properties.get("commune"),
        "section": properties.get("section"),
        "numero": properties.get("numero"),
        "contenance": properties.get("contenance") or properties.get("contenance_cadastrale"),
        "geometry_json": geometry,
        "raw_data": feature,
    }


class CadastreClient:
    def __init__(self, http_client=None, base_url=CADASTRE_API_URL):
        self.http = http_client or JsonHttpClient()
        self.base_url = base_url

    def find_parcel(self, latitude, longitude):
        geom = point_geometry(latitude, longitude)
        payload = self.http.get_json(self.base_url, params={"geom": json.dumps(geom)})
        feature = first_feature(payload)
        if not feature:
            return None
        parcel = parse_parcel(feature)
        if parcel:
            parcel["raw_response"] = payload
        return parcel
