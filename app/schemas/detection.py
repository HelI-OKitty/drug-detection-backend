from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.ai import DetectedObject, TextAIResponse

ReviewStatus = Literal["unreviewed", "reviewing", "confirmed"]


class ImageAIResultWithUrl(BaseModel):
    image_url: str = Field(..., description="원본 이미지 URL")
    prediction: int = Field(..., description="0: 비마약, 1: 마약")
    image_score: float = Field(..., ge=0.0, le=1.0, description="이미지 AI 탐지 점수")
    detected_objects: list[DetectedObject] = Field(default_factory=list)
    ocr_text: str = Field(default="")


class DetectionOut(BaseModel):
    id: str = Field(..., description="탐지 결과 ID")
    platform: str = Field(..., description="플랫폼 구분 (예: x, instagram)")
    source_id: str = Field(..., description="플랫폼 내 게시글 고유 ID (중복 방지용)")
    source_url: str = Field(..., description="원본 게시글 URL")
    content: str = Field(..., description="게시글 텍스트")
    created_at_source: datetime = Field(
        ..., description="게시글 작성 일시 (플랫폼 기준)"
    )
    keyword: list[str] = Field(..., description="매칭된 키워드 목록")
    author_id: str = Field(..., description="작성자 username")
    score: float = Field(..., ge=0.0, le=1.0, description="종합 AI 탐지 점수")
    review_status: ReviewStatus = Field(..., description="검토 상태")
    text_ai_result: TextAIResponse | None = Field(
        None, description="텍스트 AI 분석 결과"
    )
    image_ai_results: list[ImageAIResultWithUrl] = Field(
        default_factory=list, description="이미지별 AI 분석 결과"
    )
    admin_id: str = Field(..., description="담당 관리자 ID")
    detected_at: datetime = Field(..., description="탐지 저장 일시")


class DetectionListItem(BaseModel):
    id: str = Field(..., description="탐지 결과 ID")
    platform: str = Field(..., description="플랫폼 구분")
    source_id: str = Field(..., description="플랫폼 내 게시글 고유 ID")
    source_url: str = Field(..., description="원본 게시글 URL")
    content: str = Field(..., description="게시글 텍스트")
    created_at_source: datetime = Field(
        ..., description="게시글 작성 일시 (플랫폼 기준)"
    )
    keyword: list[str] = Field(..., description="매칭된 키워드 목록")
    author_id: str = Field(..., description="작성자 username")
    score: float = Field(..., description="종합 AI 탐지 점수")
    review_status: ReviewStatus = Field(..., description="검토 상태")
    detected_at: datetime = Field(..., description="탐지 저장 일시")


class ReviewStatusUpdate(BaseModel):
    review_status: ReviewStatus = Field(..., description="변경할 검토 상태")
