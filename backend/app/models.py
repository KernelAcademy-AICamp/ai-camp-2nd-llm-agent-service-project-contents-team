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
    brand_analysis = relationship("BrandAnalysis", back_populates="user", uselist=False, cascade="all, delete-orphan")


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


class BrandAnalysis(Base):
    """
    브랜드 분석 모델 (멀티 플랫폼 지원)
    - 전반적인 브랜드 특성: 모든 플랫폼에 공통으로 적용
    - 플랫폼별 특성: 블로그, 인스타그램, 유튜브 각각의 스타일
    """
    __tablename__ = "brand_analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # ===== 전반적인 브랜드 요소 (Overall Brand Elements) =====
    # 모든 플랫폼에 공통으로 적용되는 브랜드 특성
    brand_tone = Column(String, nullable=True)  # 브랜드 톤앤매너 (예: 친근하고 전문적인)
    brand_values = Column(JSON, nullable=True)  # 브랜드 가치 ["진정성", "혁신"]
    target_audience = Column(String, nullable=True)  # 타겟 고객층 (예: 20-30대 여성)
    brand_personality = Column(Text, nullable=True)  # 브랜드 성격 종합 설명
    key_themes = Column(JSON, nullable=True)  # 주요 주제 ["건강", "라이프스타일"]
    emotional_tone = Column(String, nullable=True)  # 감정적 톤 (예: 따뜻한, 유머러스한)

    # ===== 블로그 플랫폼 특성 (Blog Platform Specifics) =====
    blog_url = Column(String, nullable=True)  # 분석된 블로그 URL
    blog_writing_style = Column(String, nullable=True)  # 글쓰기 스타일 (예: ~해요체, 스토리텔링 중심)
    blog_content_structure = Column(String, nullable=True)  # 콘텐츠 구조 (예: 도입-본론-결론)
    blog_call_to_action = Column(String, nullable=True)  # 행동 유도 방식 (예: 질문형, 직접적)
    blog_keyword_usage = Column(JSON, nullable=True)  # 자주 사용하는 키워드와 빈도
    blog_analyzed_posts = Column(Integer, default=0)  # 분석된 포스트 수
    blog_analyzed_at = Column(DateTime(timezone=True), nullable=True)  # 마지막 분석 시간
    blog_analysis_status = Column(String, default="pending")  # pending, analyzing, completed, failed

    # ===== 인스타그램 플랫폼 특성 (Instagram Platform Specifics) =====
    instagram_url = Column(String, nullable=True)  # 분석된 인스타그램 URL
    instagram_caption_style = Column(String, nullable=True)  # 캡션 작성 스타일 (예: 짧고 임팩트 있는)
    instagram_image_style = Column(String, nullable=True)  # 이미지 느낌 (예: 밝고 화사한, 미니멀)
    instagram_hashtag_pattern = Column(String, nullable=True)  # 해시태그 사용 패턴 (예: 5-10개, 브랜드명 포함)
    instagram_color_palette = Column(JSON, nullable=True)  # 주요 색상 팔레트 ["#FF5733", "#C70039"]
    instagram_analyzed_posts = Column(Integer, default=0)  # 분석된 포스트 수
    instagram_analyzed_at = Column(DateTime(timezone=True), nullable=True)
    instagram_analysis_status = Column(String, default="pending")

    # ===== 유튜브 플랫폼 특성 (YouTube Platform Specifics) =====
    youtube_url = Column(String, nullable=True)  # 분석된 유튜브 채널 URL
    youtube_content_style = Column(String, nullable=True)  # 콘텐츠 스타일 (예: 튜토리얼, 브이로그)
    youtube_title_pattern = Column(String, nullable=True)  # 제목 패턴 (예: 숫자 활용, 질문형)
    youtube_description_style = Column(String, nullable=True)  # 설명 작성 스타일
    youtube_thumbnail_style = Column(String, nullable=True)  # 썸네일 스타일 (예: 텍스트 오버레이, 밝은 배경)
    youtube_analyzed_videos = Column(Integer, default=0)  # 분석된 영상 수
    youtube_analyzed_at = Column(DateTime(timezone=True), nullable=True)
    youtube_analysis_status = Column(String, default="pending")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    user = relationship("User", back_populates="brand_analysis")
