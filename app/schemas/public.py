from pydantic import BaseModel, Field, model_validator

from app.schemas.ai import ImageAIResult, TextAIResponse


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
    text_ai_result: TextAIResponse | None = Field(
        None, description="텍스트 AI 분석 결과"
    )
    image_ai_result: ImageAIResult | None = Field(
        None, description="이미지 AI 분석 결과"
    )
