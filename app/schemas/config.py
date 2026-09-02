from pydantic import BaseModel, Field


class ThresholdConfig(BaseModel):
    threshold: float = Field(
        ..., ge=0.0, le=1.0, description="마약 판별 임계값", examples=[0.5]
    )


class WeightsConfig(BaseModel):
    text_weight: float = Field(
        ..., ge=0.0, le=1.0, description="텍스트 모델 가중치", examples=[0.6]
    )
    image_weight: float = Field(
        ..., ge=0.0, le=1.0, description="이미지 모델 가중치", examples=[0.4]
    )
