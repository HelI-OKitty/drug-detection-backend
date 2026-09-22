from typing import Literal

from pydantic import BaseModel, Field


class TextAIResponse(BaseModel):
    text: str
    clean_text: str
    prediction: int  # 0: 비마약, 1: 마약
    label: str
    source: str  # "rule" or "model"
    rule_triggered: bool
    prob_drug: float | None
    prob_non_drug: float | None
    prob_drug_percent: float | None
    prob_non_drug_percent: float | None
    matched_terms: list[str]
    matched_intents: list[str]


class DetectedObject(BaseModel):
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)


class ImageAIResponse(BaseModel):
    success: Literal[True] = True
    prediction: int  # 0: 비마약, 1: 마약
    image_score: float = Field(ge=0.0, le=1.0)
    detected_objects: list[DetectedObject]
    ocr_text: str
