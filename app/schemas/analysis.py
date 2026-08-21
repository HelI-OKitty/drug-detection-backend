from pydantic import BaseModel, Field


class AnalysisTextRequest(BaseModel):
    source_url: str = Field(..., description="원본 URL", examples=["https://example.com/post/1"])
    content: str = Field(..., description="분석할 텍스트", examples=["의심 게시글 내용"])


class AnalysisImageRequest(BaseModel):
    source_url: str = Field(..., description="원본 URL", examples=["https://example.com/post/1"])
    image_url: str = Field(..., description="이미지 URL", examples=["https://img.example.com/1.jpg"])


class AnalysisMultimodalRequest(BaseModel):
    source_url: str = Field(..., description="원본 URL", examples=["https://example.com/post/1"])
    content: str = Field(..., description="분석할 텍스트", examples=["의심 게시글 내용"])
    image_url: str = Field(..., description="이미지 URL", examples=["https://img.example.com/1.jpg"])


class AnalysisResult(BaseModel):
    detection_id: str = Field(..., description="생성된 탐지 결과 ID")
    score: float = Field(..., description="최종 판별 점수 (Late Fusion 가중합)")
    is_drug: bool = Field(..., description="마약 관련 여부 (임계값 초과 시 True)")
    text_score: float | None = Field(None, description="텍스트 모델 점수")
    image_score: float | None = Field(None, description="이미지 모델 점수")
