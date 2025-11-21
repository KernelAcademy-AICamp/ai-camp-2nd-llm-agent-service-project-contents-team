from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """
    사용자 모델 (OAuth2.0 소셜 로그인 전용)
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # OAuth2.0 소셜 로그인 필드
    oauth_provider = Column(String, nullable=False)  # google, kakao, facebook, apple
    oauth_id = Column(String, nullable=False, index=True)  # 각 플랫폼의 고유 ID
    profile_image = Column(String, nullable=True)  # 프로필 이미지 URL

    # 비즈니스 정보
    brand_name = Column(String, nullable=True)  # 브랜드명
    business_type = Column(String, nullable=True)  # 업종
    business_description = Column(Text, nullable=True)  # 비즈니스 설명

    # 타겟 고객 정보 (JSON)
    target_audience = Column(JSON, nullable=True)  # {"age_range": "20-30", "gender": "all", "interests": ["fashion", "beauty"]}

    # 온보딩 완료 여부
    onboarding_completed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    contents = relationship("Content", back_populates="user", cascade="all, delete-orphan")


class UserPreference(Base):
    """
    사용자 콘텐츠 선호도 모델 (샘플 저장)
    """
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # 글 스타일 샘플
    text_style_sample = Column(Text, nullable=True)  # 선호하는 글 스타일 샘플
    text_tone = Column(String, nullable=True)  # casual, professional, friendly, formal

    # 이미지 스타일 샘플
    image_style_sample_url = Column(String, nullable=True)  # 샘플 이미지 URL (Cloudinary 등)
    image_style_description = Column(Text, nullable=True)  # 이미지 스타일 설명
    image_color_palette = Column(JSON, nullable=True)  # ["#FF5733", "#C70039", "#900C3F"]

    # 영상 스타일 샘플
    video_style_sample_url = Column(String, nullable=True)  # 샘플 영상 URL
    video_style_description = Column(Text, nullable=True)  # 영상 스타일 설명
    video_duration_preference = Column(String, nullable=True)  # short (15s), medium (30s), long (60s+)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="preferences")


class Content(Base):
    """
    통합 콘텐츠 모델 (블로그 + 이미지 + 영상)
    """
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 콘텐츠 기본 정보
    title = Column(String, nullable=False)
    goal = Column(Text, nullable=False)  # 사용자가 입력한 목표/의도
    keywords = Column(JSON, nullable=True)  # ["keyword1", "keyword2"]
    platforms = Column(JSON, nullable=True)  # ["instagram", "blog", "youtube"]

    # 생성된 콘텐츠
    blog_content = Column(Text, nullable=True)  # 블로그 포스트 내용
    blog_seo_keywords = Column(JSON, nullable=True)  # SEO 키워드

    image_urls = Column(JSON, nullable=True)  # 생성된 이미지 URL 목록
    image_prompts = Column(JSON, nullable=True)  # 각 이미지의 프롬프트

    video_url = Column(String, nullable=True)  # 생성된 영상 URL
    video_prompt = Column(Text, nullable=True)  # 영상 생성 프롬프트
    video_thumbnail_url = Column(String, nullable=True)

    # SNS별 카피
    instagram_caption = Column(Text, nullable=True)
    facebook_post = Column(Text, nullable=True)
    youtube_description = Column(Text, nullable=True)

    # 상태
    status = Column(String, nullable=False, default="draft")  # draft, published, scheduled
    generation_status = Column(String, nullable=False, default="pending")  # pending, generating, completed, failed
    error_message = Column(Text, nullable=True)

    # 발행 정보
    published_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="contents")


class Video(Base):
    """
    AI 생성 동영상 모델
    """
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 동영상 정보
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    prompt = Column(Text, nullable=False)  # 생성에 사용된 프롬프트

    # 생성 설정
    model = Column(String, nullable=False)  # stable-video-diffusion, ltx-video, etc.
    source_image_url = Column(String, nullable=True)  # 원본 이미지 URL (image-to-video)

    # 동영상 메타데이터
    video_url = Column(String, nullable=True)  # 생성된 동영상 URL
    thumbnail_url = Column(String, nullable=True)  # 썸네일 이미지 URL
    duration = Column(Float, nullable=True)  # 동영상 길이 (초)
    width = Column(Integer, nullable=True)  # 해상도 너비
    height = Column(Integer, nullable=True)  # 해상도 높이
    fps = Column(Integer, nullable=True)  # 프레임 레이트

    # 상태
    status = Column(String, nullable=False, default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    replicate_id = Column(String, nullable=True)  # Replicate prediction ID

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="videos")
