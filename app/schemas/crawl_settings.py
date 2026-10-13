from pydantic import BaseModel, Field, field_validator

from app.core.keywords import MAX_KEYWORDS
from app.services.gcp_scheduler_service import VALID_SCHEDULE_HOURS


class CrawlSettingsOut(BaseModel):
    keywords: list[str] = Field(..., description="크롤링 키워드 목록")
    max_results: int = Field(..., description="1회 최대 수집 건수")
    crawl_enabled: bool = Field(..., description="자동 크롤링 활성화 여부")
    schedule_hours: int = Field(..., description="크롤링 주기 (시간)")


class CrawlSettingsUpdate(BaseModel):
    keywords: list[str] | None = Field(
        None,
        description=f"크롤링 키워드 목록 (최대 {MAX_KEYWORDS}개)",
    )
    max_results: int | None = Field(
        None,
        ge=10,
        le=100,
        description="1회 최대 수집 건수 (10~100)",
    )
    schedule_hours: int | None = Field(
        None,
        description=f"크롤링 주기 (시간, 선택 가능: {VALID_SCHEDULE_HOURS})",
    )

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: list[str] | None) -> list[str] | None:
        if v is not None and len(v) > MAX_KEYWORDS:
            raise ValueError(f"키워드는 최대 {MAX_KEYWORDS}개까지 가능합니다")
        return v

    @field_validator("schedule_hours")
    @classmethod
    def validate_schedule_hours(cls, v: int | None) -> int | None:
        if v is not None and v not in VALID_SCHEDULE_HOURS:
            raise ValueError(f"주기는 {VALID_SCHEDULE_HOURS} 중 하나여야 합니다")
        return v


class CrawlEnabledToggle(BaseModel):
    crawl_enabled: bool = Field(..., description="자동 크롤링 활성화 여부")
