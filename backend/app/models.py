from sqlalchemy import Column, Integer, String, Boolean, DateTime
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
