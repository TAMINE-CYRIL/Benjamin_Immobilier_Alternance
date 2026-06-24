from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Literal, Optional

from pydantic import BaseModel

from apps.api.auth import get_current_user
from apps.database.audit_repo import record_audit_event
from apps.database.annonces_repo import fetch_annonce_by_id, search_annonces, update_annonce_tracking

router = APIRouter()

TEXT_FILTER = Query(None, min_length=1, max_length=100)
ZIP_FILTER = Query(None, min_length=2, max_length=10, pattern=r"^[0-9A-Za-z -]+$")
DEPARTMENT_FILTER = Query(None, min_length=1, max_length=3, pattern=r"^[0-9A-Za-z]+$")
BusinessStatus = Literal["new", "to_review", "contacted", "visit_planned", "follow_up", "rejected"]


class AnnonceTrackingPayload(BaseModel):
    business_status: Optional[BusinessStatus] = None
    is_favorite: Optional[bool] = None


def _validate_range(label, minimum, maximum):
    if minimum is not None and maximum is not None and minimum > maximum:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"{label}: le minimum ne peut pas dépasser le maximum",
        )


@router.get("/annonces")
def get_annonces(
    user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    query: Optional[str] = TEXT_FILTER,
    q: Optional[str] = TEXT_FILTER,
    city: Optional[str] = TEXT_FILTER,
    zip_code: Optional[str] = ZIP_FILTER,
    department: Optional[str] = DEPARTMENT_FILTER,
    price_min: Optional[float] = Query(None, ge=0),
    price_max: Optional[float] = Query(None, ge=0),
    surface_min: Optional[float] = Query(None, ge=0),
    surface_max: Optional[float] = Query(None, ge=0),
    type_bien: Optional[str] = TEXT_FILTER,
    score_min: Optional[float] = Query(None, ge=0, le=100),
    score_max: Optional[float] = Query(None, ge=0, le=100),
    rooms_min: Optional[int] = Query(None, ge=0, le=100),
    rooms_max: Optional[int] = Query(None, ge=0, le=100),
    price_m2_min: Optional[float] = Query(None, ge=0),
    price_m2_max: Optional[float] = Query(None, ge=0),
    energy_class: Optional[Literal["A", "B", "C", "D", "E", "F", "G"]] = None,
    source_site: Optional[str] = TEXT_FILTER,
    enrichment_status: Optional[Literal["pending", "success", "partial_success", "not_found", "failed"]] = None,
    business_status: Optional[BusinessStatus] = None,
    is_favorite: Optional[bool] = None,
    parcel_surface_min: Optional[float] = Query(None, ge=0),
    parcel_surface_max: Optional[float] = Query(None, ge=0),
    has_parcel: Optional[bool] = None,
    recent_days: Optional[int] = Query(None, ge=1, le=30),
    center_lat: Optional[float] = Query(None, ge=-90, le=90),
    center_lon: Optional[float] = Query(None, ge=-180, le=180),
    radius_km: Optional[float] = Query(None, ge=0.1, le=100),
    sort: Literal["score", "price", "surface", "price_m2", "last_seen", "relevance", "distance"] = "score",
    direction: Literal["asc", "desc"] = "desc",
):
    """
    Recherche des annonces immobilières avec pagination, filtres avancés et tri.
     - `page` et `page_size` pour la pagination.
    """
    geo_values = [center_lat, center_lon, radius_km]
    has_partial_geo_filter = any(value is not None for value in geo_values) and not all(value is not None for value in geo_values)
    if has_partial_geo_filter:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="center_lat, center_lon et radius_km doivent etre fournis ensemble",
        )

    if sort == "distance" and not all(value is not None for value in geo_values):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Le tri par distance necessite center_lat, center_lon et radius_km",
        )

    if sort == "relevance" and not (query or q):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Le tri par pertinence nécessite une recherche textuelle",
        )

    _validate_range("Prix", price_min, price_max)
    _validate_range("Surface", surface_min, surface_max)
    _validate_range("Score", score_min, score_max)
    _validate_range("Pièces", rooms_min, rooms_max)
    _validate_range("Prix au m²", price_m2_min, price_m2_max)
    _validate_range("Surface cadastrale", parcel_surface_min, parcel_surface_max)
    if recent_days is not None and recent_days not in {1, 3, 7, 14, 30}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="L'ancienneté doit être de 1, 3, 7, 14 ou 30 jours",
        )

    return search_annonces({
        "page": page,
        "page_size": page_size,
        "query": query or q,
        "city": city,
        "zip_code": zip_code,
        "department": department,
        "price_min": price_min,
        "price_max": price_max,
        "surface_min": surface_min,
        "surface_max": surface_max,
        "type_bien": type_bien,
        "score_min": score_min,
        "score_max": score_max,
        "rooms_min": rooms_min,
        "rooms_max": rooms_max,
        "price_m2_min": price_m2_min,
        "price_m2_max": price_m2_max,
        "energy_class": energy_class,
        "source_site": source_site,
        "enrichment_status": enrichment_status,
        "business_status": business_status,
        "is_favorite": is_favorite,
        "parcel_surface_min": parcel_surface_min,
        "parcel_surface_max": parcel_surface_max,
        "has_parcel": has_parcel,
        "recent_days": recent_days,
        "center_lat": center_lat,
        "center_lon": center_lon,
        "radius_km": radius_km,
        "sort": sort,
        "direction": direction,
    })


@router.get("/annonces/{annonce_id}")
def get_annonce(annonce_id: int, user=Depends(get_current_user)):
    """
    Récupère une annonce par son ID.
    Si l'annonce n'existe pas, retourne une erreur 404.
    """
    annonce = fetch_annonce_by_id(annonce_id)
    if not annonce:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annonce introuvable")

    try:
        record_audit_event(
            "annonce_detail_viewed",
            user_id=user["id"],
            email=user.get("email"),
            metadata={"annonce_id": annonce_id},
        )
    except Exception:
        pass

    return annonce


@router.patch("/annonces/{annonce_id}/tracking")
def patch_annonce_tracking(
    annonce_id: int,
    payload: AnnonceTrackingPayload,
    user=Depends(get_current_user),
):
    if payload.business_status is None and payload.is_favorite is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Au moins un champ de suivi doit etre fourni",
        )

    annonce = update_annonce_tracking(
        annonce_id,
        business_status=payload.business_status,
        is_favorite=payload.is_favorite,
    )
    if not annonce:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annonce introuvable")

    try:
        record_audit_event(
            "annonce_tracking_updated",
            user_id=user["id"],
            email=user.get("email"),
            metadata={
                "annonce_id": annonce_id,
                "business_status": payload.business_status,
                "is_favorite": payload.is_favorite,
            },
        )
    except Exception:
        pass

    return annonce
