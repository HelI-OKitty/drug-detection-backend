from typing import Literal

from pydantic import BaseModel, Field


class TextAIResponse(BaseModel):
    prediction: int  # 0: 비마약, 1: 마약
    source: str  # "rule" or "model"
    text_score: float | None
    matched_terms: list[str]
    matched_intents: list[str]


class DetectedObject(BaseModel):
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)


class ImageAIResult(BaseModel):
    """이미지 AI 분석 결과 (URL 없는 공통 스키마)"""

    prediction: int  # 0: 비마약, 1: 마약
    image_score: float = Field(ge=0.0, le=1.0)
    detected_objects: list[DetectedObject]
    ocr_text: str


class ImageAIResponse(BaseModel):
    success: Literal[True] = True
    prediction: int  # 0: 비마약, 1: 마약
    image_score: float = Field(ge=0.0, le=1.0)
    detected_objects: list[DetectedObject]
    ocr_text: str
