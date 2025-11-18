from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
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
    instagram_accounts = relationship("InstagramAccount", back_populates="user", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    scheduled_posts = relationship("ScheduledPost", back_populates="user", cascade="all, delete-orphan")


class InstagramAccount(Base):
    """
    Instagram 계정 연동 정보
    """
    __tablename__ = "instagram_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Instagram Business Account 정보
    instagram_business_account_id = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False)
    profile_picture_url = Column(String, nullable=True)

    # Facebook 페이지 정보 (Instagram Business Account는 Facebook 페이지와 연동됨)
    facebook_page_id = Column(String, nullable=False)
    facebook_page_name = Column(String, nullable=True)

    # Access Token (암호화 권장)
    access_token = Column(Text, nullable=False)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="instagram_accounts")


class Post(Base):
    """
    발행된 게시물 기록
    """
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 플랫폼 정보
    platform = Column(String, nullable=False)  # instagram, facebook, twitter 등
    platform_post_id = Column(String, nullable=True)  # 플랫폼에서 생성된 게시물 ID

    # 콘텐츠
    content_type = Column(String, nullable=False)  # image, video, carousel, text
    caption = Column(Text, nullable=True)
    media_url = Column(String, nullable=True)  # 이미지/비디오 URL

    # 상태
    status = Column(String, nullable=False)  # published, failed, deleted
    error_message = Column(Text, nullable=True)

    # 통계 (선택사항)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)

    published_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="posts")


class ScheduledPost(Base):
    """
    예약된 게시물
    """
    __tablename__ = "scheduled_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 플랫폼 정보
    platform = Column(String, nullable=False)  # instagram, facebook, twitter 등

    # 콘텐츠
    content_type = Column(String, nullable=False)  # image, video, carousel, text
    caption = Column(Text, nullable=True)
    media_url = Column(String, nullable=True)  # 이미지/비디오 URL

    # 예약 시간
    scheduled_time = Column(DateTime(timezone=True), nullable=False)

    # 상태
    status = Column(String, nullable=False, default="pending")  # pending, processing, published, failed, cancelled
    error_message = Column(Text, nullable=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)  # 발행 후 연결

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="scheduled_posts")
