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


# Instagram 관련 스키마
class InstagramAccountBase(BaseModel):
    """Instagram 계정 기본 스키마"""
    instagram_business_account_id: str
    username: str
    profile_picture_url: Optional[str] = None
    facebook_page_id: str
    facebook_page_name: Optional[str] = None


class InstagramAccountCreate(BaseModel):
    """Instagram 계정 생성 스키마"""
    access_token: str
    facebook_page_id: str


class InstagramAccount(InstagramAccountBase):
    """Instagram 계정 응답 스키마"""
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 게시물 관련 스키마
class PostBase(BaseModel):
    """게시물 기본 스키마"""
    platform: str
    content_type: str
    caption: Optional[str] = None
    media_url: Optional[str] = None


class PostCreate(PostBase):
    """게시물 생성 스키마"""
    publish_now: bool = True
    scheduled_time: Optional[datetime] = None


class Post(PostBase):
    """게시물 응답 스키마"""
    id: int
    user_id: int
    platform_post_id: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    published_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 예약 게시물 관련 스키마
class ScheduledPostBase(BaseModel):
    """예약 게시물 기본 스키마"""
    platform: str
    content_type: str
    caption: Optional[str] = None
    media_url: Optional[str] = None
    scheduled_time: datetime


class ScheduledPostCreate(ScheduledPostBase):
    """예약 게시물 생성 스키마"""
    pass


class ScheduledPost(ScheduledPostBase):
    """예약 게시물 응답 스키마"""
    id: int
    user_id: int
    status: str
    error_message: Optional[str] = None
    post_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Instagram 게시물 발행 요청
class InstagramPublishRequest(BaseModel):
    """Instagram 게시물 발행 요청"""
    caption: str
    image_url: str
    scheduled_time: Optional[datetime] = None
