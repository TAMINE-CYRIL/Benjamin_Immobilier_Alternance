import json
import os

from services.enrichment.cadastre import point_geometry
from services.enrichment.http_client import JsonHttpClient


GPU_API_BASE_URL = os.getenv("GPU_API_BASE_URL", "https://apicarto.ign.fr/api/gpu")
MAX_GET_GEOMETRY_CHARS = 1800


def _features(payload):
    if isinstance(payload, dict):
        return payload.get("features") or []
    return []


def _pick_property(properties, names):
    for name in names:
        value = properties.get(name)
        if value not in (None, ""):
            return value
    return None


def _short_items(payload, kind):
    items = []
    for feature in _features(payload):
        properties = feature.get("properties") or {}
        items.append(
            {
                "kind": kind,
                "label": _pick_property(properties, ["libelle", "libelong", "nom", "nomfic", "txt"]),
                "code": _pick_property(properties, ["code", "type", "typepsc", "typesup", "id"]),
                "raw": properties,
            }
        )
    return items


def _zone_label(zone_payload):
    for feature in _features(zone_payload):
        properties = feature.get("properties") or {}
        label = _pick_property(properties, ["libelle", "libelong", "typezone", "destdomi", "nomfic"])
        if label:
            return str(label)
    return None


class GpuClient:
    def __init__(self, http_client=None, base_url=GPU_API_BASE_URL):
        self.http = http_client or JsonHttpClient()
        self.base_url = base_url.rstrip("/")

    def _endpoint(self, name):
        return f"{self.base_url}/{name}"

    def _get_by_geom(self, endpoint, geometry):
        return self.http.get_json(self._endpoint(endpoint), params={"geom": json.dumps(geometry)})

    def fetch_urbanism(self, latitude, longitude, geometry=None):
        geom = geometry or point_geometry(latitude, longitude)
        if len(json.dumps(geom)) > MAX_GET_GEOMETRY_CHARS:
            geom = point_geometry(latitude, longitude)
        raw = {}

        zone_payload = self._get_by_geom("zone-urba", geom)
        raw["zone_urba"] = zone_payload

        prescriptions = []
        for endpoint in ("prescription-surf", "prescription-lin", "prescription-pct"):
            payload = self._get_by_geom(endpoint, geom)
            raw[endpoint] = payload
            prescriptions.extend(_short_items(payload, endpoint))

        servitudes = []
        for endpoint in ("sup-surf", "sup-lin", "sup-pct"):
            payload = self._get_by_geom(endpoint, geom)
            raw[endpoint] = payload
            servitudes.extend(_short_items(payload, endpoint))

        documents = _short_items(zone_payload, "zone-urba")

        return {
            "zonage": _zone_label(zone_payload),
            "prescriptions": prescriptions,
            "servitudes": servitudes,
            "documents": documents,
            "raw": raw,
        }
