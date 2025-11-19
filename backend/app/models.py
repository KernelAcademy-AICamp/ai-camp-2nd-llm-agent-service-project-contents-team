from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
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

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")


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
