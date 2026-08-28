from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_admin
from app.schemas.dashboard import DashboardSummary
from app.schemas.detection import DetectionListItem
from app.services.dashboard_service import get_recent, get_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(admin_id: str = Depends(get_current_admin)):
    return await get_summary(admin_id)


@router.get("/recent", response_model=list[DetectionListItem])
async def dashboard_recent(
    limit: int = Query(default=10, ge=1, le=50, description="조회할 최근 탐지 건수"),
    admin_id: str = Depends(get_current_admin),
):
    return await get_recent(admin_id, limit)
