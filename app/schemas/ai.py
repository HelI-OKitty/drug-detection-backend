from pydantic import BaseModel


class TextAIResponse(BaseModel):
    text: str
    clean_text: str
    prediction: int                     # 0: 비마약, 1: 마약
    label: str
    source: str                         # "rule" or "model"
    rule_triggered: bool
    prob_drug: float | None
    prob_non_drug: float | None
    prob_drug_percent: float | None
    prob_non_drug_percent: float | None
    matched_terms: list[str]
    matched_intents: list[str]


# TODO: 이미지 AI 응답 구조 확정 후 추가
# class ImageAIResponse(BaseModel):
#     ...
