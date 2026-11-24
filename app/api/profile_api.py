from fastapi import APIRouter, Depends

from app.core.security import get_current_admin
from app.schemas.admin import AdminOut, AdminUpdate
from app.services import profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=AdminOut)
async def get_profile(admin_id: str = Depends(get_current_admin)) -> AdminOut:
    return await profile_service.get_profile(admin_id)


@router.patch("", response_model=AdminOut)
async def update_profile(
    data: AdminUpdate,
    admin_id: str = Depends(get_current_admin),
) -> AdminOut:
    return await profile_service.update_profile(admin_id, data)
