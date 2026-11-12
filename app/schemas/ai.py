from typing import Literal

from pydantic import BaseModel, Field


class OcrTextResult(BaseModel):
    """OCR 텍스트 개별 분석 결과"""

    text: str
    clean_text: str
    prediction: int
    label: str
    prob_non_drug: float | None = None
    prob_drug: float | None = None
    prob_non_drug_percent: float | None = None
    prob_drug_percent: float | None = None
    source: str
    rule_triggered: bool = False
    matched_terms: list[str]
    matched_intents: list[str]


class TextAIModelResponse(BaseModel):
    """텍스트 AI 서버 응답 스키마"""

    text: str
    clean_text: str
    prediction: int | None  # 0: 비마약, 1: 마약, None: 분석 불가
    label: str  # "마약" or "비마약" or "분석 불가"
    prob_non_drug: float | None = None
    prob_drug: float | None = None
    prob_non_drug_percent: float | None = None
    prob_drug_percent: float | None = None
    source: str  # "rule" or "model"
    rule_triggered: bool = False
    matched_terms: list[str]
    matched_intents: list[str]
    ocr_text_results: list[OcrTextResult] = Field(default_factory=list)


class TextAIResponse(BaseModel):
    """프론트엔드 응답용 스키마"""

    prediction: int | None  # 0: 비마약, 1: 마약, None: 분석 불가
    source: str  # "rule" or "model"
    text_score: float | None
    matched_terms: list[str]
    matched_intents: list[str]


class DetectedObject(BaseModel):
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)


class ImageAIModelResponse(BaseModel):
    """이미지 AI 서버 응답 스키마"""

    success: Literal[True] = True
    prediction: int  # 0: 비마약, 1: 마약
    image_score: float = Field(ge=0.0, le=1.0)
    detected_objects: list[DetectedObject]
    ocr_text: str


class OcrTextAnalysis(BaseModel):
    """프론트엔드 응답용 OCR 텍스트 분석 결과"""

    ocr_text: str
    prediction: int  # 0: 비마약, 1: 마약
    ocr_text_score: float | None
    matched_terms: list[str]
    matched_intents: list[str]


class ImageAIResponse(BaseModel):
    """프론트엔드 응답용 이미지 AI 결과 (URL 없는 공통 스키마)"""

    prediction: int  # 0: 비마약, 1: 마약
    image_score: float = Field(ge=0.0, le=1.0)
    detected_objects: list[DetectedObject]
    ocr_text_results: list[OcrTextAnalysis] = Field(default_factory=list)
