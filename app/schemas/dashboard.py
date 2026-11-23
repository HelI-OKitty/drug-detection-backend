from pydantic import BaseModel, Field


class VerdictCount(BaseModel):
    positive: int = Field(..., description="마약 탐지 건수 (is_drug=True)")
    negative: int = Field(..., description="비마약 건수 (is_drug=False)")


class DashboardSummary(BaseModel):
    total: int = Field(..., description="전체 탐지 건수 (is_drug=True)")
    today: int = Field(..., description="당일 탐지 건수 (is_drug=True)")
    unreviewed: int = Field(..., description="미검토 탐지 건수")
    verdict: VerdictCount = Field(..., description="판정 분포")
