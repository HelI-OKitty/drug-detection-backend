from pydantic import BaseModel, Field, field_validator

from app.core.keywords import MAX_KEYWORDS


class CrawlSettingsOut(BaseModel):
    keywords: list[str] = Field(..., description="크롤링 키워드 목록")
    max_results: int = Field(..., description="1회 최대 수집 건수")
    crawl_enabled: bool = Field(..., description="자동 크롤링 활성화 여부")


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

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: list[str] | None) -> list[str] | None:
        if v is not None and len(v) > MAX_KEYWORDS:
            raise ValueError(f"키워드는 최대 {MAX_KEYWORDS}개까지 가능합니다")
        return v
