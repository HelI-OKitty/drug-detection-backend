from pydantic import BaseModel, Field, model_validator

from app.schemas.ai import DetectedObject


class PublicAnalyzeRequest(BaseModel):
    text: str | None = Field(None, description="분석할 텍스트")
    image: str | None = Field(None, description="이미지 base64 문자열")

    @model_validator(mode="after")
    def check_text_or_image(self) -> "PublicAnalyzeRequest":
        if not self.text and not self.image:
            raise ValueError("text 또는 image 중 하나는 필수입니다.")
        return self


class PublicAnalyzeResponse(BaseModel):
    is_drug: bool = Field(..., description="마약 게시글 여부")
    detected_objects: list[DetectedObject] | None = Field(
        None, description="이미지에서 탐지된 객체 목록 (이미지 마약 탐지 시)"
    )
    ocr_text: str | None = Field(None, description="이미지에서 추출된 OCR 텍스트")
    prob_drug: float | None = Field(None, description="텍스트 마약 확률")
    prob_non_drug: float | None = Field(None, description="텍스트 비마약 확률")
