from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_admin
from app.schemas.crawl_settings import (
    CrawlEnabledToggle,
    CrawlSettingsOut,
    CrawlSettingsUpdate,
)
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
    """현재 관리자의 크롤링 설정 수정 (키워드, max_results, schedule_hours)"""
    try:
        return await crawl_settings_service.update_settings(admin_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/toggle", response_model=CrawlSettingsOut)
async def toggle_crawl_enabled(
    data: CrawlEnabledToggle,
    admin_id: str = Depends(get_current_admin),
) -> CrawlSettingsOut:
    """자동 크롤링 활성화/비활성화 토글

    - true: detections 최신 source_id로 since_id 복원 + GCP Scheduler job 생성
    - false: GCP Scheduler job 삭제
    """
    try:
        return await crawl_settings_service.toggle_crawl_enabled(admin_id, data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
