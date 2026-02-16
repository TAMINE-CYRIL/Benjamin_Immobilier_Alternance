from fastapi import APIRouter
from typing import List

from apps.database.annonces_repo import fetch_all_annonces

router = APIRouter()

@router.get("/annonces")
def get_annonces():
    return fetch_all_annonces()
