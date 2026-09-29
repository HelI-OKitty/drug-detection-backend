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
    tweet_id: str = Field(..., description="X 게시글 ID")
    source_url: str = Field(..., description="원본 게시글 URL")
    content: str = Field(..., description="게시글 텍스트")
    keyword: str = Field(..., description="탐지에 사용된 키워드")
    author_name: str = Field(..., description="작성자 닉네임")
    score: float = Field(..., ge=0.0, le=1.0, description="종합 AI 탐지 점수")
    review_status: ReviewStatus = Field(..., description="검토 상태")
    text_ai_result: TextAIResponse | None = Field(None, description="텍스트 AI 분석 결과")
    image_ai_results: list[ImageAIResultWithUrl] = Field(
        default_factory=list, description="이미지별 AI 분석 결과"
    )
    admin_id: str = Field(..., description="담당 관리자 ID")
    detected_at: datetime = Field(..., description="탐지 일시")


class DetectionListItem(BaseModel):
    id: str = Field(..., description="탐지 결과 ID")
    tweet_id: str = Field(..., description="X 게시글 ID")
    source_url: str = Field(..., description="원본 게시글 URL")
    content: str = Field(..., description="게시글 텍스트")
    keyword: str = Field(..., description="탐지에 사용된 키워드")
    author_name: str = Field(..., description="작성자 닉네임")
    score: float = Field(..., description="종합 AI 탐지 점수")
    review_status: ReviewStatus = Field(..., description="검토 상태")
    detected_at: datetime = Field(..., description="탐지 일시")


class ReviewStatusUpdate(BaseModel):
    review_status: ReviewStatus = Field(..., description="변경할 검토 상태")
