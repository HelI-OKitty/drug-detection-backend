import logging
import secrets

from fastapi import APIRouter, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from app.core.config import settings
from app.db.mongo import db
from app.services.crawl_pipeline_service import run_crawl_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crawl", tags=["crawl"])

_crawl_secret_header = APIKeyHeader(name="X-Internal-Key", auto_error=False)


def _verify_crawl_secret(secret: str | None = Security(_crawl_secret_header)) -> None:
    if not settings.INTERNAL_API_KEY or not secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="유효하지 않은 내부 API 키입니다",
        )
    if not secrets.compare_digest(
        secret.encode("utf-8"), settings.INTERNAL_API_KEY.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="유효하지 않은 내부 API 키입니다",
        )


class TriggerRequest(BaseModel):
    max_results: int | None = Field(
        None,
        ge=10,
        le=100,
        description="최대 수집 건수 (10~100). 미지정 시 관리자 DB 설정값 사용.",
    )


class AdminCrawlResult(BaseModel):
    admin_id: str
    total: int
    saved: int
    skipped: int
    error: str | None = None


class TriggerResponse(BaseModel):
    admins_processed: int = Field(..., description="처리된 관리자 수")
    total_saved: int = Field(..., description="전체 저장된 탐지 건수")
    results: list[AdminCrawlResult] = Field(..., description="관리자별 상세 결과")


@router.post(
    "/trigger",
    response_model=TriggerResponse,
    status_code=status.HTTP_200_OK,
    summary="전체 관리자 크롤링 트리거",
    description=(
        "DB에 등록된 모든 관리자에 대해 X API 크롤링을 실행한다. "
        "GCP Cloud Scheduler가 주기적으로 호출한다."
    ),
)
async def trigger_crawl(
    body: TriggerRequest,
    _: None = Security(_verify_crawl_secret),
) -> TriggerResponse:
    """GCP Cloud Scheduler → 전체 관리자 크롤링 트리거"""
    admins = await db.admins.find({}, {"_id": 1}).to_list(length=None)

    results: list[AdminCrawlResult] = []
    total_saved = 0

    for admin in admins:
        admin_id = str(admin["_id"])
        try:
            result = await run_crawl_pipeline(admin_id, max_results=body.max_results)
            results.append(AdminCrawlResult(admin_id=admin_id, **result))
            total_saved += result["saved"]
        except Exception:
            logger.exception("admin_id=%s 크롤링 파이프라인 오류", admin_id)
            results.append(
                AdminCrawlResult(
                    admin_id=admin_id,
                    total=0,
                    saved=0,
                    skipped=0,
                    error="크롤링 중 오류가 발생했습니다",
                )
            )

    return TriggerResponse(
        admins_processed=len(admins),
        total_saved=total_saved,
        results=results,
    )
