from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.ai import (
    DetectedObject,
    ImageAIResponse,
    OcrTextAnalysis,
    TextAIResponse,
)

ReviewStatus = Literal["unreviewed", "reviewing", "confirmed"]


class ImageAIResultWithUrl(BaseModel):
    """내부/DB 저장용 이미지 AI 결과"""

    image_url: str
    prediction: int
    image_score: float = Field(..., ge=0.0, le=1.0)
    detected_objects: list[DetectedObject] = Field(default_factory=list)
    ocr_text: str = Field(default="", description="이미지 AI 추출 OCR 원문 (DB 저장용)")
    ocr_text_results: list[OcrTextAnalysis] = Field(
        default_factory=list, description="OCR 분석 결과 (API 응답용)"
    )


class ImageAIDetailResponse(ImageAIResponse):
    """탐지 상세 FE 응답용 이미지 AI 결과 (image_url 포함)"""

    image_url: str


class ImageAISummary(BaseModel):
    """탐지 목록 FE 응답용 이미지 AI 요약"""

    prediction: int
    image_score: float = Field(..., ge=0.0, le=1.0)
    has_ocr_text: bool


class DetectionOut(BaseModel):
    id: str
    platform: str
    source_id: str
    source_url: str
    content: str
    created_at_source: datetime
    keyword: list[str]
    author_id: str
    is_drug: bool
    review_status: ReviewStatus
    text_ai_result: TextAIResponse | None = None
    image_ai_results: list[ImageAIDetailResponse] = Field(default_factory=list)
    admin_id: str
    detected_at: datetime


class DetectionListItem(BaseModel):
    id: str
    platform: str
    source_id: str
    source_url: str
    content: str
    created_at_source: datetime
    keyword: list[str]
    author_id: str
    is_drug: bool
    review_status: ReviewStatus
    text_ai_result: TextAIResponse | None = None
    image_ai_results: list[ImageAISummary] = Field(default_factory=list)
    detected_at: datetime


class ReviewStatusUpdate(BaseModel):
    review_status: ReviewStatus
