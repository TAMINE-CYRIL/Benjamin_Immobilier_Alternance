from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional

from apps.api.auth import get_current_user
from apps.database.annonces_repo import fetch_annonce_by_id, search_annonces

router = APIRouter()

@router.get("/annonces")
def get_annonces(
    user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    city: Optional[str] = None,
    zip_code: Optional[str] = None,
    department: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    surface_min: Optional[float] = None,
    surface_max: Optional[float] = None,
    type_bien: Optional[str] = None,
    score_min: Optional[float] = None,
    source_site: Optional[str] = None,
    sort: str = "score",
    direction: str = "desc",
):
    return search_annonces({
        "page": page,
        "page_size": page_size,
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
        "sort": sort,
        "direction": direction,
    })


@router.get("/annonces/{annonce_id}")
def get_annonce(annonce_id: int, user=Depends(get_current_user)):
    annonce = fetch_annonce_by_id(annonce_id)
    if not annonce:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annonce introuvable")

    return annonce
