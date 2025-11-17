from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """사용자 기본 스키마 (OAuth2.0 소셜 로그인 전용)"""
    email: str  # OAuth 임시 이메일 허용을 위해 str 타입 사용
    username: str = Field(..., min_length=1, max_length=50)
    full_name: Optional[str] = None


class User(UserBase):
    """사용자 응답 스키마"""
    id: int
    is_active: bool
    is_superuser: bool
    oauth_provider: Optional[str] = None
    profile_image: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """토큰 응답 스키마"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """토큰 데이터 스키마"""
    username: Optional[str] = None
