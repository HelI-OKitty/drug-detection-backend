from pydantic import BaseModel, Field


# --- summary ---


class VerdictCount(BaseModel):
    positive: int = Field(..., description="마약 탐지 건수 (is_drug=True)")
    negative: int = Field(..., description="비마약 건수 (is_drug=False)")


class DashboardSummary(BaseModel):
    total: int = Field(..., description="전체 탐지 건수 (is_drug=True)")
    today: int = Field(..., description="당일 탐지 건수 (is_drug=True)")
    unreviewed: int = Field(..., description="미검토 탐지 건수")
    verdict: VerdictCount = Field(..., description="판정 분포")


# --- analytics ---


class DailyTrend(BaseModel):
    date: str = Field(..., description="날짜 (YYYY-MM-DD)", examples=["2026-11-17"])
    positive: int = Field(..., description="양성 탐지 건수")
    negative: int = Field(..., description="음성 판정 건수")


class TermCount(BaseModel):
    term: str
    count: int


class IntentCount(BaseModel):
    intent: str
    count: int


class SourceDistribution(BaseModel):
    model: int = Field(..., description="모델 판정 건수")
    rule: int = Field(..., description="룰 판정 건수")


class TextAnalytics(BaseModel):
    analyzed: int = Field(..., description="텍스트 AI 분석 건수")
    top_terms: list[TermCount] = Field(..., description="상위 매칭 키워드")
    top_intents: list[IntentCount] = Field(..., description="상위 매칭 의도")
    source: SourceDistribution = Field(..., description="모델 vs 룰 판정 분포")


class ObjectCount(BaseModel):
    class_name: str
    count: int


class ImageAnalytics(BaseModel):
    total_images: int = Field(..., description="전체 이미지 수")
    objects: list[ObjectCount] = Field(..., description="탐지 객체 상위 목록")
    ocr_with_text: int = Field(..., description="OCR 텍스트 추출 성공 이미지 수")
    ocr_without_text: int = Field(..., description="OCR 텍스트 없는 이미지 수")


class DashboardAnalytics(BaseModel):
    trend: list[DailyTrend] = Field(..., description="최근 7일 일별 양성/음성 추이")
    text: TextAnalytics = Field(..., description="텍스트 AI 분석 통계")
    image: ImageAnalytics = Field(..., description="이미지 AI 분석 통계")
