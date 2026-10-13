from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_admin
from app.schemas.crawl_settings import CrawlSettingsOut, CrawlSettingsUpdate
from app.services import crawl_settings_service

router = APIRouter(prefix="/crawl-settings", tags=["crawl-settings"])


@router.get("", response_model=CrawlSettingsOut)
async def get_crawl_settings(
    admin_id: str = Depends(get_current_admin),
) -> CrawlSettingsOut:
    """현재 관리자의 크롤링 설정 조회"""
    return await crawl_settings_service.get_settings(admin_id)


@router.patch("", response_model=CrawlSettingsOut)
async def update_crawl_settings(
    data: CrawlSettingsUpdate,
    admin_id: str = Depends(get_current_admin),
) -> CrawlSettingsOut:
    """현재 관리자의 크롤링 설정 수정 (키워드, max_results)"""
    try:
        return await crawl_settings_service.update_settings(admin_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
