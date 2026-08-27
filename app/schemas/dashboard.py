from pydantic import BaseModel, Field


class DailyCount(BaseModel):
    date: str = Field(..., description="날짜 (YYYY-MM-DD)", examples=["2026-08-27"])
    count: int = Field(..., description="해당 날짜 탐지 건수")


class DashboardSummary(BaseModel):
    total: int = Field(..., description="전체 탐지 건수")
    today: int = Field(..., description="당일 탐지 건수")
    unconfirmed: int = Field(..., description="미확인(pending) 탐지 건수")
    trend: list[DailyCount] = Field(..., description="최근 7일간 일별 탐지 추이")
