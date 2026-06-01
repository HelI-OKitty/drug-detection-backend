from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str = Field(
        ...,
        description="JWT 액세스 토큰",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: str = Field(
        default="bearer",
        description="토큰 타입",
        examples=["bearer"],
    )


class TokenRefresh(BaseModel):
    refresh_token: str = Field(
        ...,
        description="JWT 리프레시 토큰",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )


class TokenPayload(BaseModel):
    sub: str = Field(
        ...,
        description="토큰 주체 (관리자 ID)",
        examples=["665abc1234567890abcdef01"],
    )
    exp: int = Field(
        ...,
        description="토큰 만료 시간 (Unix timestamp)",
        examples=[1717344000],
    )
