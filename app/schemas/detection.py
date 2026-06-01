from datetime import datetime

from pydantic import BaseModel, Field


class DetectionCreate(BaseModel):
    source_url: str = Field(
        ...,
        description="탐지 원본 URL",
        examples=["https://example.com/post/123"],
    )
    content: str = Field(
        ...,
        description="탐지 대상 텍스트",
        examples=["의심 게시글 내용"],
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI 탐지 점수",
        examples=[0.95],
    )
    admin_id: str = Field(
        ...,
        description="담당 관리자 ID",
        examples=["665abc1234567890abcdef01"],
    )


class DetectionOut(BaseModel):
    id: str = Field(
        ...,
        description="탐지 결과 ID",
        examples=["665def1234567890abcdef02"],
    )
    source_url: str = Field(
        ...,
        description="탐지 원본 URL",
        examples=["https://example.com/post/123"],
    )
    content: str = Field(
        ...,
        description="탐지 대상 텍스트",
        examples=["의심 게시글 내용"],
    )
    score: float = Field(
        ...,
        description="AI 탐지 점수",
        examples=[0.95],
    )
    review_status: str = Field(
        ...,
        description="검토 상태",
        examples=["pending"],
    )
    admin_id: str = Field(
        ...,
        description="담당 관리자 ID",
        examples=["665abc1234567890abcdef01"],
    )
    detected_at: datetime = Field(..., description="탐지 일시")


class DetectionListItem(BaseModel):
    id: str = Field(
        ...,
        description="탐지 결과 ID",
        examples=["665def1234567890abcdef02"],
    )
    source_url: str = Field(
        ...,
        description="탐지 원본 URL",
        examples=["https://example.com/post/123"],
    )
    score: float = Field(
        ...,
        description="AI 탐지 점수",
        examples=[0.95],
    )
    review_status: str = Field(
        ...,
        description="검토 상태",
        examples=["pending"],
    )
    detected_at: datetime = Field(..., description="탐지 일시")


class ReviewStatusUpdate(BaseModel):
    review_status: str = Field(
        ...,
        description="변경할 검토 상태",
        examples=["confirmed"],
    )
