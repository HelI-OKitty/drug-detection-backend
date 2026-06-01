from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AdminCreate(BaseModel):
    email: EmailStr = Field(
        ...,
        description="관리자 이메일",
        examples=["admin@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="비밀번호 (8자 이상)",
        examples=["securePass123!"],
    )
    name: str = Field(
        ...,
        min_length=1,
        description="관리자 이름",
        examples=["홍길동"],
    )


class AdminLogin(BaseModel):
    email: EmailStr = Field(
        ...,
        description="로그인 이메일",
        examples=["admin@example.com"],
    )
    password: str = Field(
        ...,
        description="비밀번호",
        examples=["securePass123!"],
    )


class AdminOut(BaseModel):
    id: str = Field(
        ...,
        description="관리자 ID",
        examples=["665abc1234567890abcdef01"],
    )
    email: EmailStr = Field(
        ...,
        description="이메일",
        examples=["admin@example.com"],
    )
    name: str = Field(
        ...,
        description="이름",
        examples=["홍길동"],
    )
    created_at: datetime = Field(..., description="가입일시")


class AdminUpdate(BaseModel):
    name: str | None = Field(
        None,
        min_length=1,
        description="변경할 이름",
        examples=["김철수"],
    )
    password: str | None = Field(
        None,
        min_length=8,
        description="변경할 비밀번호",
        examples=["newPass456!"],
    )
