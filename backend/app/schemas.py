from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserBase(BaseModel):
    """사용자 기본 스키마 (OAuth2.0 소셜 로그인 전용)"""
    email: str  # OAuth 임시 이메일 허용을 위해 str 타입 사용
    username: str = Field(..., min_length=1, max_length=50)
    full_name: Optional[str] = None


class UserOnboardingUpdate(BaseModel):
    """온보딩 정보 업데이트 스키마"""
    brand_name: Optional[str] = None
    business_type: Optional[str] = None
    business_description: Optional[str] = None
    target_audience: Optional[Dict[str, Any]] = None  # {"age_range": "20-30", "gender": "all", "interests": [...]}


class User(UserBase):
    """사용자 응답 스키마"""
    id: int
    is_active: bool
    is_superuser: bool
    oauth_provider: Optional[str] = None
    profile_image: Optional[str] = None
    brand_name: Optional[str] = None
    business_type: Optional[str] = None
    business_description: Optional[str] = None
    target_audience: Optional[Dict[str, Any]] = None
    onboarding_completed: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 사용자 선호도 스키마
class UserPreferenceBase(BaseModel):
    """사용자 선호도 기본 스키마"""
    text_style_sample: Optional[str] = None
    text_tone: Optional[str] = None  # casual, professional, friendly, formal
    image_style_description: Optional[str] = None
    image_color_palette: Optional[List[str]] = None
    video_style_description: Optional[str] = None
    video_duration_preference: Optional[str] = None  # short, medium, long


class UserPreferenceCreate(UserPreferenceBase):
    """사용자 선호도 생성 스키마"""
    pass


class UserPreferenceUpdate(UserPreferenceBase):
    """사용자 선호도 업데이트 스키마"""
    pass


class ProfileUpdate(BaseModel):
    """프로필 업데이트 스키마 (Settings 페이지용)"""
    # 비즈니스 정보
    brand_name: Optional[str] = None
    business_type: Optional[str] = None
    business_description: Optional[str] = None
    # 타겟 고객
    target_audience: Optional[Dict[str, Any]] = None
    # 스타일 선호도
    preferences: Optional[UserPreferenceBase] = None


class UserPreference(UserPreferenceBase):
    """사용자 선호도 응답 스키마"""
    id: int
    user_id: int
    image_style_sample_url: Optional[str] = None
    video_style_sample_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """사용자 프로필 전체 응답 스키마 (마이페이지용)"""
    user: User
    preferences: Optional[UserPreference] = None

    class Config:
        from_attributes = True


# 브랜드 분석 스키마
class BrandAnalysisBase(BaseModel):
    """브랜드 분석 기본 스키마"""
    # 전반적 브랜드 요소
    brand_name: Optional[str] = None
    business_type: Optional[str] = None
    brand_tone: Optional[str] = None
    brand_values: Optional[List[str]] = None
    target_audience: Optional[str] = None
    brand_personality: Optional[str] = None
    key_themes: Optional[List[str]] = None
    emotional_tone: Optional[str] = None

    # 블로그 플랫폼 특성
    blog_writing_style: Optional[str] = None
    blog_content_structure: Optional[str] = None
    blog_call_to_action: Optional[str] = None

    # 인스타그램 플랫폼 특성
    instagram_caption_style: Optional[str] = None
    instagram_image_style: Optional[str] = None
    instagram_hashtag_pattern: Optional[str] = None
    instagram_color_palette: Optional[List[str]] = None

    # 유튜브 플랫폼 특성
    youtube_content_style: Optional[str] = None
    youtube_title_pattern: Optional[str] = None
    youtube_description_style: Optional[str] = None


class BrandAnalysis(BrandAnalysisBase):
    """브랜드 분석 응답 스키마"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 콘텐츠 생성용 사용자 컨텍스트 스키마
class UserContext(BaseModel):
    """콘텐츠 생성 시 사용할 사용자 컨텍스트"""
    # 기본 정보
    brand_name: Optional[str] = None
    business_type: Optional[str] = None
    business_description: Optional[str] = None
    target_audience: Optional[Dict[str, Any]] = None

    # 스타일 선호도
    text_tone: Optional[str] = None  # casual, professional, friendly, formal
    text_style_sample: Optional[str] = None
    image_style_description: Optional[str] = None
    image_color_palette: Optional[List[str]] = None

    # 브랜드 분석 결과
    brand_tone: Optional[str] = None
    brand_personality: Optional[str] = None
    key_themes: Optional[List[str]] = None
    emotional_tone: Optional[str] = None
    blog_writing_style: Optional[str] = None
    instagram_caption_style: Optional[str] = None

    class Config:
        from_attributes = True


class UserProfileWithBrand(BaseModel):
    """사용자 프로필 + 브랜드 분석 전체 응답 스키마"""
    user: User
    preferences: Optional[UserPreference] = None
    brand_analysis: Optional[BrandAnalysis] = None
    context: Optional[UserContext] = None  # 콘텐츠 생성용 요약 정보

    class Config:
        from_attributes = True


# 통합 콘텐츠 스키마
class ContentBase(BaseModel):
    """통합 콘텐츠 기본 스키마"""
    title: str
    goal: str
    keywords: Optional[List[str]] = None
    platforms: Optional[List[str]] = None  # ["instagram", "blog", "youtube"]


class ContentCreate(ContentBase):
    """통합 콘텐츠 생성 요청"""
    generate_blog: bool = True
    generate_images: bool = True
    generate_video: bool = True
    num_images: int = 3  # 생성할 이미지 개수


class ContentUpdate(BaseModel):
    """통합 콘텐츠 업데이트"""
    title: Optional[str] = None
    blog_content: Optional[str] = None
    instagram_caption: Optional[str] = None
    facebook_post: Optional[str] = None
    youtube_description: Optional[str] = None
    status: Optional[str] = None  # draft, published, scheduled


class Content(ContentBase):
    """통합 콘텐츠 응답 스키마"""
    id: int
    user_id: int
    blog_content: Optional[str] = None
    blog_seo_keywords: Optional[List[str]] = None
    image_urls: Optional[List[str]] = None
    image_prompts: Optional[List[str]] = None
    video_url: Optional[str] = None
    video_prompt: Optional[str] = None
    video_thumbnail_url: Optional[str] = None
    instagram_caption: Optional[str] = None
    facebook_post: Optional[str] = None
    youtube_description: Optional[str] = None
    status: str
    generation_status: str
    error_message: Optional[str] = None
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
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


# ============================================
# 발행 콘텐츠 스키마 (PublishedContent)
# ============================================

class PublishedContentBase(BaseModel):
    """발행 콘텐츠 기본 스키마"""
    platform: str  # 'blog', 'sns', 'x', 'threads'
    title: Optional[str] = None  # 블로그용 제목
    content: str  # 본문
    tags: Optional[List[str]] = None  # 태그/해시태그


class PublishedContentCreate(PublishedContentBase):
    """발행 콘텐츠 생성 스키마 (임시저장)"""
    id: Optional[int] = None  # 기존 콘텐츠 ID (있으면 업데이트, 없으면 생성)
    session_id: Optional[int] = None  # 원본 세션 ID
    image_ids: Optional[List[int]] = None  # 이미지 ID 목록
    uploaded_image_url: Optional[str] = None  # 직접 업로드한 이미지 URL


class PublishedContentSchedule(PublishedContentCreate):
    """발행 콘텐츠 예약 스키마"""
    scheduled_at: datetime  # 예약 발행 시간


class PublishedContentUpdate(BaseModel):
    """발행 콘텐츠 수정 스키마"""
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    image_ids: Optional[List[int]] = None
    uploaded_image_url: Optional[str] = None  # 직접 업로드한 이미지 URL
    scheduled_at: Optional[datetime] = None


class PublishedContentResponse(PublishedContentBase):
    """발행 콘텐츠 응답 스키마"""
    id: int
    user_id: int
    session_id: Optional[int] = None
    image_ids: Optional[List[int]] = None
    uploaded_image_url: Optional[str] = None  # 직접 업로드한 이미지 URL
    status: str  # 'draft', 'scheduled', 'published', 'failed'
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    publish_url: Optional[str] = None
    platform_post_id: Optional[str] = None  # 플랫폼별 게시물 ID
    publish_error: Optional[str] = None
    views: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PublishedContentListResponse(BaseModel):
    """발행 콘텐츠 목록 응답 스키마 (콘텐츠 관리 페이지용)"""
    id: int
    platform: str
    title: Optional[str] = None
    content: str  # 본문 미리보기용
    status: str
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    views: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
