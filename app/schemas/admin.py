from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator


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
    id: str = Field(..., description="관리자 ID")
    email: EmailStr = Field(..., description="로그인 이메일 (변경 불가)")
    name: str = Field(..., description="이름")
    site_url: str | None = Field(None, description="관리 대상 사이트 URL")
    notification_enabled: bool = Field(False, description="알림 수신 여부")
    notification_email: EmailStr | None = Field(None, description="알림 수신 이메일")
    created_at: datetime = Field(..., description="가입일시")


class AdminUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, description="변경할 이름")
    current_password: str | None = Field(
        None, description="현재 비밀번호 (비밀번호 변경 시 필수)"
    )
    new_password: str | None = Field(None, min_length=8, description="변경할 비밀번호")
    site_url: str | None = Field(None, description="관리 대상 사이트 URL")
    notification_enabled: bool | None = Field(None, description="알림 수신 여부")
    notification_email: EmailStr | None = Field(None, description="알림 수신 이메일")

    @model_validator(mode="after")
    def check_password_fields(self) -> "AdminUpdate":
        if self.new_password and not self.current_password:
            raise ValueError("비밀번호 변경 시 현재 비밀번호가 필요합니다.")
        return self
