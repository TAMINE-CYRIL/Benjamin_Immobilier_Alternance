from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Literal, Optional

from apps.api.auth import get_current_user
from apps.database.audit_repo import record_audit_event
from apps.database.annonces_repo import fetch_annonce_by_id, search_annonces

router = APIRouter()

TEXT_FILTER = Query(None, min_length=1, max_length=100)
ZIP_FILTER = Query(None, min_length=2, max_length=10, pattern=r"^[0-9A-Za-z -]+$")
DEPARTMENT_FILTER = Query(None, min_length=1, max_length=3, pattern=r"^[0-9A-Za-z]+$")


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
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    type_bien: Optional[str] = TEXT_FILTER,
    score_min: Optional[float] = None,
    source_site: Optional[str] = TEXT_FILTER,
    enrichment_status: Optional[Literal["pending", "success", "partial_success", "failed"]] = None,
    zonage: Optional[str] = TEXT_FILTER,
    sort: Literal["score", "price", "surface", "price_m2", "last_seen", "zonage", "relevance"] = "score",
    direction: Literal["asc", "desc"] = "desc",
):
    """
    Recherche des annonces immobilières avec pagination, filtres avancés et tri.
     - `page` et `page_size` pour la pagination.
    """
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
        "source_site": source_site,
        "enrichment_status": enrichment_status,
        "zonage": zonage,
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
