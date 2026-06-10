import os

from services.enrichment.cadastre import CadastreClient
from services.enrichment.geo import AddressClient
from services.enrichment.gpu import GpuClient
from services.enrichment.repository import fetch_annonces_to_enrich, upsert_enrichment, upsert_parcelle


STATUS_PENDING = "pending"
STATUS_SUCCESS = "success"
STATUS_PARTIAL = "partial_success"
STATUS_FAILED = "failed"
STATUS_NOT_FOUND = "not_found"


def _base_enrichment(annonce):
    return {
        "annonce_id": annonce["id"],
        "status": STATUS_PENDING,
        "zip_code": annonce.get("zip_code"),
        "geocode_status": "pending",
        "cadastre_status": "pending",
        "gpu_status": "disabled",
        "prescriptions": [],
        "servitudes": [],
        "documents": [],
    }


def _diagnostic(enrichment):
    if enrichment.get("status") == STATUS_NOT_FOUND:
        return enrichment.get("error_message") or "Aucune coordonnee exploitable"
    if enrichment.get("status") == STATUS_FAILED:
        return enrichment.get("error_message") or "Erreur technique pendant l'enrichissement"
    if enrichment.get("status") == STATUS_SUCCESS:
        if enrichment.get("parcel_id"):
            return "Coordonnees et parcelle cadastrale trouvees"
        return "Coordonnees trouvees"

    missing = []
    if enrichment.get("geocode_status") != "success":
        missing.append("geocodage incomplet")
    if enrichment.get("cadastre_status") != "success":
        missing.append("parcelle introuvable")
    return "Enrichissement partiel: " + ", ".join(missing)


def _final_status(enrichment):
    if enrichment.get("geocode_status") != "success":
        return STATUS_NOT_FOUND
    if enrichment.get("cadastre_status") == "success":
        return STATUS_SUCCESS
    return STATUS_PARTIAL


class EnrichmentService:
    def __init__(self, address_client=None, cadastre_client=None, gpu_client=None, logger=None, gpu_enabled=None):
        self.address_client = address_client or AddressClient()
        self.cadastre_client = cadastre_client or CadastreClient()
        if gpu_enabled is None:
            gpu_enabled = os.getenv("ENABLE_GPU_ENRICHMENT", "false").lower() in {"1", "true", "yes", "on"}
        self.gpu_enabled = gpu_enabled
        self.gpu_client = (gpu_client or GpuClient()) if gpu_enabled else None
        self.logger = logger

    def log(self, message):
        if self.logger:
            self.logger(message)

    def enrich_annonce(self, annonce):
        enrichment = _base_enrichment(annonce)

        try:
            geocode = self.address_client.geocode_annonce(annonce)
            enrichment["geocode_status"] = geocode.get("status") if geocode else "not_found"
            enrichment["geocode_score"] = geocode.get("score") if geocode else None
            enrichment["geocode_type"] = geocode.get("result_type") if geocode else None
            enrichment["geocode_query"] = geocode.get("query") if geocode else None
            enrichment["raw_geocode"] = geocode.get("raw") if geocode else None

            if not geocode or geocode.get("status") != "success":
                enrichment["status"] = STATUS_NOT_FOUND
                enrichment["error_message"] = (geocode or {}).get("diagnostic") or "Adresse non geocodable"
                enrichment["cadastre_status"] = "skipped"
                enrichment["gpu_status"] = "skipped"
                enrichment["diagnostic_message"] = _diagnostic(enrichment)
                upsert_enrichment(enrichment)
                return enrichment

            latitude = geocode["latitude"]
            longitude = geocode["longitude"]
            enrichment["latitude"] = latitude
            enrichment["longitude"] = longitude

            parcel = None
            try:
                parcel = self.cadastre_client.find_parcel(latitude, longitude)
                enrichment["cadastre_status"] = "success" if parcel else "not_found"
            except Exception as exc:
                enrichment["cadastre_status"] = "failed"
                enrichment["error_message"] = f"Cadastre indisponible: {exc}"

            if parcel:
                parcel_id = upsert_parcelle(parcel, latitude=latitude, longitude=longitude)
                enrichment["parcel_id"] = parcel_id
                enrichment["parcel_key"] = parcel["parcel_key"]
                enrichment["raw_cadastre"] = parcel.get("raw_response") or parcel.get("raw_data")

            if self.gpu_enabled:
                geometry = parcel.get("geometry_json") if parcel else None
                try:
                    urbanism = self.gpu_client.fetch_urbanism(latitude, longitude, geometry=geometry)
                    enrichment["zonage"] = urbanism.get("zonage")
                    enrichment["prescriptions"] = urbanism.get("prescriptions") or []
                    enrichment["servitudes"] = urbanism.get("servitudes") or []
                    enrichment["documents"] = urbanism.get("documents") or []
                    enrichment["raw_gpu"] = urbanism.get("raw")
                    enrichment["gpu_status"] = "success" if enrichment.get("zonage") else "not_found"
                except Exception:
                    enrichment["gpu_status"] = "failed"

            enrichment["status"] = _final_status(enrichment)
            enrichment["diagnostic_message"] = _diagnostic(enrichment)

            upsert_enrichment(enrichment)
            return enrichment
        except Exception as exc:
            enrichment["status"] = STATUS_FAILED
            enrichment["error_message"] = str(exc)
            enrichment["diagnostic_message"] = _diagnostic(enrichment)
            upsert_enrichment(enrichment)
            return enrichment

    def run(self, limit=100, refresh_days=30):
        annonces = fetch_annonces_to_enrich(limit=limit, refresh_days=refresh_days)
        summary = {
            "total": len(annonces),
            STATUS_SUCCESS: 0,
            STATUS_PARTIAL: 0,
            STATUS_FAILED: 0,
            STATUS_NOT_FOUND: 0,
        }

        for annonce in annonces:
            result = self.enrich_annonce(annonce)
            status = result["status"]
            if status in summary:
                summary[status] += 1
            self.log(f"[{status}] annonce_id={annonce['id']} parcel={result.get('parcel_key') or '-'}")

        return summary
