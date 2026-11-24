from pydantic import BaseModel, Field

from app.services.x_crawl_service import DEFAULT_MAX_RESULTS


class CrawlRequest(BaseModel):
    admin_id: str = Field(..., description="크롤링 결과를 귀속시킬 관리자 ID")
    max_results: int = Field(
        DEFAULT_MAX_RESULTS,
        ge=10,
        le=100,
        description="이번 크롤링 최대 수집 건수 (10~100)",
    )


class CrawlResponse(BaseModel):
    total: int = Field(..., description="수집된 전체 게시글 수")
    saved: int = Field(..., description="새로 저장된 탐지 결과 수")
    skipped: int = Field(..., description="중복으로 건너뛴 게시글 수")
