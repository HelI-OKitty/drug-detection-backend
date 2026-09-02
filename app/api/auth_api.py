from fastapi import APIRouter, Depends

from app.core.security import get_current_admin
from app.schemas.admin import AdminCreate, AdminLogin, AdminOut, AdminUpdate
from app.schemas.auth import Token, TokenRefresh
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AdminOut, status_code=201)
async def signup(data: AdminCreate) -> AdminOut:
    return await auth_service.signup(data)


@router.post("/login", response_model=Token)
async def login(data: AdminLogin) -> Token:
    return await auth_service.login(data)


@router.post("/refresh", response_model=Token)
async def refresh(data: TokenRefresh) -> Token:
    return await auth_service.refresh_access_token(data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(
    data: TokenRefresh,
    _admin_id: str = Depends(get_current_admin),
) -> None:
    await auth_service.logout(data.refresh_token)


@router.get("/me", response_model=AdminOut)
async def get_me(admin_id: str = Depends(get_current_admin)) -> AdminOut:
    return await auth_service.get_admin(admin_id)


@router.patch("/me", response_model=AdminOut)
async def update_me(
    data: AdminUpdate,
    admin_id: str = Depends(get_current_admin),
) -> AdminOut:
    return await auth_service.update_admin(admin_id, data)
