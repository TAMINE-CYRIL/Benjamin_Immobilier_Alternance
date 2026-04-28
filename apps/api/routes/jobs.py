from fastapi import APIRouter, Depends, Query

from apps.api.auth import get_current_user
from database.automation_runs import list_runs


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/runs")
def get_runs(user=Depends(get_current_user), limit: int = Query(20, ge=1, le=100)):
    return {"items": list_runs(limit=limit)}
