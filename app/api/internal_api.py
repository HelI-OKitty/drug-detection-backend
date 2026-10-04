from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings
from app.schemas.internal import CrawlRequest, CrawlResponse
from app.services.crawl_pipeline_service import run_crawl_pipeline

router = APIRouter(prefix="/internal", tags=["internal"])

_api_key_header = APIKeyHeader(name="X-Internal-Key", auto_error=False)


def _verify_internal_key(api_key: str | None = Security(_api_key_header)) -> None:
    if not settings.INTERNAL_API_KEY or api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="유효하지 않은 내부 API 키입니다",
        )


@router.post(
    "/crawl",
    response_model=CrawlResponse,
    status_code=status.HTTP_200_OK,
)
async def trigger_crawl(
    body: CrawlRequest,
    _: None = Depends(_verify_internal_key),
) -> CrawlResponse:
    """GCP Cloud Scheduler에서 1시간마다 호출하는 크롤링 트리거 엔드포인트"""
    result = await run_crawl_pipeline(body.admin_id, max_results=body.max_results)
    return CrawlResponse(**result)
