import os
import re

from services.enrichment.http_client import JsonHttpClient


ADDRESS_API_URL = os.getenv("ADDRESS_API_URL", "https://data.geopf.fr/geocodage/search")
LEGACY_ADDRESS_API_URL = "https://api-adresse.data.gouv.fr/search/"
MIN_GEOCODE_SCORE = float(os.getenv("MIN_GEOCODE_SCORE", "0.45"))

STREET_PATTERN = re.compile(
    r"\b(?:rue|avenue|av\.?|boulevard|bd|chemin|impasse|route|allee|allée|quai|cours|place)\s+"
    r"[A-Za-zÀ-ÖØ-öø-ÿ0-9' -]{3,}",
    re.IGNORECASE,
)


def _clean_text(value):
    return " ".join(str(value or "").replace("\n", " ").split())


def _city_zip(annonce):
    return " ".join(part for part in [_clean_text(annonce.get("city")), _clean_text(annonce.get("zip_code"))] if part)


def extract_street_candidate(text):
    match = STREET_PATTERN.search(_clean_text(text))
    if not match:
        return None
    return match.group(0).strip(" ,-")


def build_search_queries(annonce):
    city_zip = _city_zip(annonce)
    queries = []

    for source in ("title", "city"):
        street = extract_street_candidate(annonce.get(source))
        if street:
            queries.append(" ".join(part for part in [street, city_zip] if part))

    if city_zip:
        queries.append(city_zip)

    title = _clean_text(annonce.get("title"))
    if title and city_zip:
        queries.append(f"{title} {city_zip}")

    deduped = []
    seen = set()
    for query in queries:
        normalized = query.lower()
        if query and normalized not in seen:
            deduped.append(query)
            seen.add(normalized)
    return deduped


def build_search_text(annonce):
    queries = build_search_queries(annonce)
    return queries[0] if queries else ""


def _feature_properties(feature):
    return feature.get("properties") or {}


def _feature_score(feature):
    properties = _feature_properties(feature)
    score = properties.get("score") or feature.get("score")
    try:
        return float(score) if score is not None else None
    except (TypeError, ValueError):
        return None


def _feature_type(feature):
    properties = _feature_properties(feature)
    return properties.get("type") or properties.get("classification") or feature.get("type")


def _feature_coordinates(feature):
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates") or []
    if len(coordinates) >= 2:
        return coordinates
    properties = _feature_properties(feature)
    lon = properties.get("lon") or properties.get("longitude")
    lat = properties.get("lat") or properties.get("latitude")
    if lon is not None and lat is not None:
        return [lon, lat]
    return []


class AddressClient:
    def __init__(self, http_client=None, base_url=ADDRESS_API_URL, min_score=MIN_GEOCODE_SCORE):
        self.http = http_client or JsonHttpClient()
        self.base_url = base_url
        self.min_score = min_score

    def geocode_annonce(self, annonce):
        queries = build_search_queries(annonce)
        if not queries:
            return {
                "status": "not_found",
                "diagnostic": "Aucune ville, code postal ou rue exploitable pour le geocodage",
                "attempts": [],
            }

        attempts = []
        for query in queries:
            params = {"q": query, "limit": 1}
            if annonce.get("zip_code"):
                params["postcode"] = annonce["zip_code"]

            payload = self.http.get_json(self.base_url, params=params)
            features = payload.get("features") or []
            attempts.append({"query": query, "feature_count": len(features)})
            if not features:
                continue

            feature = features[0]
            coordinates = _feature_coordinates(feature)
            if len(coordinates) < 2:
                continue

            score = _feature_score(feature)
            result_type = _feature_type(feature)
            if score is not None and score < self.min_score:
                return {
                    "status": "low_confidence",
                    "score": score,
                    "result_type": result_type,
                    "query": query,
                    "raw": feature,
                    "attempts": attempts,
                    "diagnostic": f"Geocodage rejete: score {score:.2f} inferieur au seuil {self.min_score:.2f}",
                }

            return {
                "status": "success",
                "latitude": coordinates[1],
                "longitude": coordinates[0],
                "score": score,
                "result_type": result_type,
                "query": query,
                "raw": feature,
                "attempts": attempts,
            }

        return {
            "status": "not_found",
            "attempts": attempts,
            "diagnostic": "Aucun resultat geocode exploitable",
        }
