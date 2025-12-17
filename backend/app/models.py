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
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    youtube_connection = relationship("YouTubeConnection", back_populates="user", uselist=False, cascade="all, delete-orphan")
    facebook_connection = relationship("FacebookConnection", back_populates="user", uselist=False, cascade="all, delete-orphan")
    instagram_connection = relationship("InstagramConnection", back_populates="user", uselist=False, cascade="all, delete-orphan")
    x_connection = relationship("XConnection", back_populates="user", uselist=False, cascade="all, delete-orphan")
    threads_connection = relationship("ThreadsConnection", back_populates="user", uselist=False, cascade="all, delete-orphan")
    tiktok_connection = relationship("TikTokConnection", back_populates="user", uselist=False, cascade="all, delete-orphan")
    wordpress_connection = relationship("WordPressConnection", back_populates="user", uselist=False, cascade="all, delete-orphan")
    content_sessions = relationship("ContentGenerationSession", back_populates="user", cascade="all, delete-orphan")


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
    brand_name = Column(String, nullable=True)  # 블로그에서 추론한 브랜드명
    business_type = Column(String, nullable=True)  # 업종 (예: 카페/베이커리, IT/소프트웨어)
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


class ChatSession(Base):
    """
    채팅 세션 모델
    """
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True)  # 세션 제목 (첫 메시지 기반)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """
    채팅 메시지 모델
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    model = Column(String, nullable=True)  # AI 모델명 (gemini-1.5-pro 등)
    tokens_used = Column(Integer, nullable=True)  # 사용된 토큰 수

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class YouTubeConnection(Base):
    """
    YouTube 채널 연동 정보 모델
    - 사용자별 YouTube 채널 연동 및 토큰 관리
    """
    __tablename__ = "youtube_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # YouTube 채널 정보
    channel_id = Column(String, nullable=False, index=True)  # YouTube 채널 ID
    channel_title = Column(String, nullable=True)  # 채널명
    channel_description = Column(Text, nullable=True)  # 채널 설명
    channel_thumbnail_url = Column(String, nullable=True)  # 채널 썸네일
    channel_custom_url = Column(String, nullable=True)  # 커스텀 URL (@handle)
    subscriber_count = Column(Integer, nullable=True)  # 구독자 수
    video_count = Column(Integer, nullable=True)  # 동영상 수
    view_count = Column(Integer, nullable=True)  # 총 조회수

    # OAuth 토큰 정보 (암호화 저장 권장)
    access_token = Column(Text, nullable=False)  # YouTube API 액세스 토큰
    refresh_token = Column(Text, nullable=True)  # 리프레시 토큰
    token_expires_at = Column(DateTime(timezone=True), nullable=True)  # 토큰 만료 시간

    # 연동 상태
    is_active = Column(Boolean, default=True)  # 연동 활성화 상태
    last_synced_at = Column(DateTime(timezone=True), nullable=True)  # 마지막 동기화 시간

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="youtube_connection")
    videos = relationship("YouTubeVideo", back_populates="connection", cascade="all, delete-orphan")


class YouTubeVideo(Base):
    """
    YouTube 동영상 정보 모델
    - 연동된 채널의 동영상 목록 및 분석 데이터
    """
    __tablename__ = "youtube_videos"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("youtube_connections.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # YouTube 동영상 기본 정보
    video_id = Column(String, nullable=False, unique=True, index=True)  # YouTube 동영상 ID
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    thumbnail_url = Column(String, nullable=True)  # 썸네일 URL
    published_at = Column(DateTime(timezone=True), nullable=True)  # 게시 일시
    duration = Column(String, nullable=True)  # ISO 8601 형식 (PT4M13S)
    duration_seconds = Column(Integer, nullable=True)  # 초 단위

    # 동영상 상태
    privacy_status = Column(String, nullable=True)  # public, private, unlisted
    upload_status = Column(String, nullable=True)  # uploaded, processed, failed

    # 동영상 통계 (최신 데이터)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)

    # 태그 및 카테고리
    tags = Column(JSON, nullable=True)  # ["tag1", "tag2"]
    category_id = Column(String, nullable=True)  # YouTube 카테고리 ID

    # 동기화 정보
    last_stats_updated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    connection = relationship("YouTubeConnection", back_populates="videos")
    analytics = relationship("YouTubeAnalytics", back_populates="video", cascade="all, delete-orphan")


class YouTubeAnalytics(Base):
    """
    YouTube 동영상별 분석 데이터 모델
    - 일별/주별 성과 데이터 저장
    """
    __tablename__ = "youtube_analytics"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("youtube_videos.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 분석 기간
    date = Column(DateTime(timezone=True), nullable=False)  # 해당 날짜

    # 조회 지표
    views = Column(Integer, default=0)  # 조회수
    watch_time_minutes = Column(Float, default=0)  # 시청 시간 (분)
    average_view_duration = Column(Float, default=0)  # 평균 시청 시간 (초)
    average_view_percentage = Column(Float, default=0)  # 평균 시청 비율 (%)

    # 참여 지표
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)

    # 구독 지표
    subscribers_gained = Column(Integer, default=0)
    subscribers_lost = Column(Integer, default=0)

    # 트래픽 소스 (JSON)
    traffic_sources = Column(JSON, nullable=True)  # {"search": 30, "suggested": 40, "external": 20}

    # 시청자 정보 (JSON)
    demographics = Column(JSON, nullable=True)  # {"age_group": {...}, "gender": {...}, "country": {...}}

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    video = relationship("YouTubeVideo", back_populates="analytics")


class FacebookConnection(Base):
    """
    Facebook 페이지 연동 정보 모델
    - 사용자별 Facebook 페이지 연동 및 토큰 관리
    """
    __tablename__ = "facebook_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Facebook 사용자 정보
    facebook_user_id = Column(String, nullable=False, index=True)  # Facebook 사용자 ID
    facebook_user_name = Column(String, nullable=True)  # Facebook 사용자 이름

    # 연동된 Facebook 페이지 정보
    page_id = Column(String, nullable=True, index=True)  # Facebook 페이지 ID
    page_name = Column(String, nullable=True)  # 페이지 이름
    page_category = Column(String, nullable=True)  # 페이지 카테고리
    page_picture_url = Column(String, nullable=True)  # 페이지 프로필 사진
    page_fan_count = Column(Integer, nullable=True)  # 페이지 팬(좋아요) 수
    page_followers_count = Column(Integer, nullable=True)  # 페이지 팔로워 수

    # OAuth 토큰 정보
    user_access_token = Column(Text, nullable=False)  # 사용자 액세스 토큰
    page_access_token = Column(Text, nullable=True)  # 페이지 액세스 토큰 (장기 토큰)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)  # 토큰 만료 시간

    # 관리 가능한 페이지 목록 (캐싱)
    available_pages = Column(JSON, nullable=True)  # [{"id": "...", "name": "...", ...}, ...]

    # 연동 상태
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="facebook_connection")
    posts = relationship("FacebookPost", back_populates="connection", cascade="all, delete-orphan")


class FacebookPost(Base):
    """
    Facebook 페이지 게시물 모델
    - 연동된 페이지의 게시물 목록 및 통계
    """
    __tablename__ = "facebook_posts"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("facebook_connections.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Facebook 게시물 기본 정보
    post_id = Column(String, nullable=False, unique=True, index=True)  # Facebook 게시물 ID
    message = Column(Text, nullable=True)  # 게시물 텍스트
    story = Column(String, nullable=True)  # 스토리 텍스트
    full_picture = Column(String, nullable=True)  # 게시물 이미지 URL
    permalink_url = Column(String, nullable=True)  # 게시물 링크
    post_type = Column(String, nullable=True)  # link, status, photo, video
    created_time = Column(DateTime(timezone=True), nullable=True)  # 게시 시간

    # 게시물 상태
    is_published = Column(Boolean, default=True)
    is_hidden = Column(Boolean, default=False)

    # 게시물 통계
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    reactions_count = Column(Integer, default=0)  # 전체 반응 수

    # 동기화 정보
    last_stats_updated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    connection = relationship("FacebookConnection", back_populates="posts")


class InstagramConnection(Base):
    """
    Instagram 비즈니스 계정 연동 정보 모델
    - Facebook 페이지와 연결된 Instagram 비즈니스/크리에이터 계정
    """
    __tablename__ = "instagram_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Facebook 사용자 정보
    facebook_user_id = Column(String, nullable=True)  # Facebook 사용자 ID
    facebook_user_name = Column(String, nullable=True)  # Facebook 사용자 이름

    # 연동된 Facebook 페이지 정보
    page_id = Column(String, nullable=True, index=True)  # Facebook 페이지 ID
    page_name = Column(String, nullable=True)  # 페이지 이름

    # Instagram 계정 정보
    instagram_account_id = Column(String, nullable=True, index=True)  # Instagram 비즈니스 계정 ID
    instagram_username = Column(String, nullable=True)  # Instagram 사용자명 (@username)
    instagram_name = Column(String, nullable=True)  # 표시 이름
    instagram_profile_picture_url = Column(String, nullable=True)  # 프로필 사진 URL
    instagram_biography = Column(Text, nullable=True)  # 자기소개
    instagram_website = Column(String, nullable=True)  # 웹사이트 URL

    # 계정 통계
    followers_count = Column(Integer, default=0)  # 팔로워 수
    follows_count = Column(Integer, default=0)  # 팔로잉 수
    media_count = Column(Integer, default=0)  # 게시물 수

    # OAuth 토큰 정보
    user_access_token = Column(Text, nullable=True)  # 사용자 액세스 토큰
    page_access_token = Column(Text, nullable=True)  # 페이지 액세스 토큰
    token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # 연동 상태
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="instagram_connection")
    posts = relationship("InstagramPost", back_populates="connection", cascade="all, delete-orphan")


class InstagramPost(Base):
    """
    Instagram 게시물 모델
    - 연동된 비즈니스 계정의 게시물 목록 및 통계
    """
    __tablename__ = "instagram_posts"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("instagram_connections.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Instagram 게시물 기본 정보
    media_id = Column(String, nullable=False, unique=True, index=True)  # Instagram 미디어 ID
    media_type = Column(String, nullable=True)  # IMAGE, VIDEO, CAROUSEL_ALBUM
    media_url = Column(String, nullable=True)  # 미디어 URL
    thumbnail_url = Column(String, nullable=True)  # 썸네일 URL (비디오용)
    permalink = Column(String, nullable=True)  # 게시물 링크
    caption = Column(Text, nullable=True)  # 캡션
    timestamp = Column(DateTime(timezone=True), nullable=True)  # 게시 시간

    # 게시물 통계
    like_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    saved_count = Column(Integer, default=0)  # 저장 수 (비즈니스 계정만)
    reach_count = Column(Integer, default=0)  # 도달 수 (비즈니스 계정만)
    impressions_count = Column(Integer, default=0)  # 노출 수 (비즈니스 계정만)
    engagement_count = Column(Integer, default=0)  # 참여 수

    # 동기화 정보
    last_stats_updated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    connection = relationship("InstagramConnection", back_populates="posts")


class VideoGenerationJob(Base):
    """
    AI 비디오 생성 작업 모델
    - 사용자가 업로드한 제품 사진과 정보를 기반으로
    - 스토리보드 생성 → 이미지 생성 → 비디오 트랜지션 생성 → 최종 합성
    """
    __tablename__ = "video_generation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 제품 정보
    product_name = Column(String, nullable=False)  # 제품명
    product_description = Column(Text, nullable=True)  # 제품 설명
    uploaded_image_url = Column(String, nullable=False)  # 업로드된 제품 이미지 URL

    # 영상 설정
    tier = Column(String, nullable=False)  # short, standard, premium
    cut_count = Column(Integer, nullable=False)  # 4, 6, 8
    duration_seconds = Column(Integer, nullable=False)  # 15, 25, 40
    cost = Column(Float, nullable=False)  # 3.90, 5.90, 7.90

    # 생성 단계별 데이터
    storyboard = Column(JSON, nullable=True)  # [{"cut": 1, "scene": "...", "image_prompt": "...", "duration": 5}, ...]
    generated_image_urls = Column(JSON, nullable=True)  # [{"cut": 1, "url": "..."}, ...]
    generated_video_urls = Column(JSON, nullable=True)  # [{"transition": "1-2", "url": "..."}, ...]
    final_video_url = Column(String, nullable=True)  # 최종 합성된 비디오 URL
    thumbnail_url = Column(String, nullable=True)  # 썸네일 이미지 URL

    # 상태 추적
    status = Column(String, nullable=False, default="pending")
    # pending: 대기 중
    # planning: 스토리보드 생성 중
    # generating_images: 이미지 생성 중
    # generating_videos: 비디오 트랜지션 생성 중
    # composing: 최종 비디오 합성 중
    # completed: 완료
    # failed: 실패

    current_step = Column(String, nullable=True)  # 현재 진행 중인 단계 상세 설명
    error_message = Column(Text, nullable=True)  # 에러 메시지

    # AI 모델 사용 정보
    planning_model = Column(String, default="gemini-2.5-flash")  # 스토리보드 생성 모델 (Vertex AI)
    image_model = Column(String, default="gemini-2.5-flash-image")  # 이미지 생성 모델 (Vertex AI)
    video_model = Column(String, default="veo-3.1-fast-generate-001")  # 비디오 생성 모델 (Vertex AI)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")


class XConnection(Base):
    """
    X(구 Twitter) 계정 연동 정보 모델
    - X API v2를 사용한 OAuth 2.0 연동
    """
    __tablename__ = "x_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # X 사용자 정보
    x_user_id = Column(String, nullable=False, index=True)  # X 사용자 ID
    username = Column(String, nullable=True)  # @username (handle)
    name = Column(String, nullable=True)  # 표시 이름
    description = Column(Text, nullable=True)  # 자기소개
    profile_image_url = Column(String, nullable=True)  # 프로필 이미지 URL
    verified = Column(Boolean, default=False)  # 인증 계정 여부

    # 계정 통계
    followers_count = Column(Integer, default=0)  # 팔로워 수
    following_count = Column(Integer, default=0)  # 팔로잉 수
    post_count = Column(Integer, default=0)  # 포스트 수
    listed_count = Column(Integer, default=0)  # 리스트에 추가된 수

    # OAuth 2.0 토큰 정보
    access_token = Column(Text, nullable=False)  # 액세스 토큰
    refresh_token = Column(Text, nullable=True)  # 리프레시 토큰
    token_expires_at = Column(DateTime(timezone=True), nullable=True)  # 토큰 만료 시간

    # 연동 상태
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="x_connection")
    posts = relationship("XPost", back_populates="connection", cascade="all, delete-orphan")


class XPost(Base):
    """
    X 포스트 모델
    - 연동된 계정의 포스트 목록 및 통계
    """
    __tablename__ = "x_posts"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("x_connections.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 포스트 기본 정보
    post_id = Column(String, nullable=False, unique=True, index=True)  # X 포스트 ID
    text = Column(Text, nullable=True)  # 포스트 텍스트
    created_at_x = Column(DateTime(timezone=True), nullable=True)  # 포스트 작성 시간

    # 미디어 정보
    media_type = Column(String, nullable=True)  # photo, video, animated_gif
    media_url = Column(String, nullable=True)  # 첫 번째 미디어 URL
    media_urls = Column(JSON, nullable=True)  # 모든 미디어 URL 목록

    # 포스트 통계
    repost_count = Column(Integer, default=0)  # 리포스트 수
    reply_count = Column(Integer, default=0)  # 답글 수
    like_count = Column(Integer, default=0)  # 좋아요 수
    quote_count = Column(Integer, default=0)  # 인용 포스트 수
    bookmark_count = Column(Integer, default=0)  # 북마크 수
    impression_count = Column(Integer, default=0)  # 노출 수

    # 포스트 메타데이터
    conversation_id = Column(String, nullable=True)  # 대화 ID (스레드)
    in_reply_to_user_id = Column(String, nullable=True)  # 답글 대상 사용자 ID
    referenced_posts = Column(JSON, nullable=True)  # 참조된 포스트 목록

    # 동기화 정보
    last_stats_updated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    connection = relationship("XConnection", back_populates="posts")


# ============================================
# 새로운 콘텐츠 생성 테이블 구조 (v2)
# ============================================

class ContentGenerationSession(Base):
    """
    콘텐츠 생성 세션 (사용자 입력값 저장)
    - 사용자가 입력한 주제, 생성 타입, 스타일, 선택한 플랫폼 등 저장
    - 각 플랫폼별 결과 테이블과 연결
    """
    __tablename__ = "content_generation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 사용자 입력값
    topic = Column(Text, nullable=False)  # 주제
    content_type = Column(String, nullable=False)  # text, image, both
    style = Column(String, nullable=False)  # casual, professional, friendly, etc.
    selected_platforms = Column(JSON, nullable=False)  # ["blog", "sns", "x", "threads"]

    # AI 분석 결과
    analysis_data = Column(JSON, nullable=True)  # 분석 결과 전체 (JSON)
    critique_data = Column(JSON, nullable=True)  # 평가 결과 전체 (JSON)

    # 이미지 설정
    requested_image_count = Column(Integer, default=0)  # 요청한 이미지 갯수

    # 메타데이터
    generation_attempts = Column(Integer, default=1)  # 생성 시도 횟수
    status = Column(String, default="generated")  # generated, published, archived

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="content_sessions")
    blog_content = relationship("GeneratedBlogContent", back_populates="session", uselist=False, cascade="all, delete-orphan")
    sns_content = relationship("GeneratedSNSContent", back_populates="session", uselist=False, cascade="all, delete-orphan")
    x_content = relationship("GeneratedXContent", back_populates="session", uselist=False, cascade="all, delete-orphan")
    threads_content = relationship("GeneratedThreadsContent", back_populates="session", uselist=False, cascade="all, delete-orphan")
    cardnews_content = relationship("GeneratedCardnewsContent", back_populates="session", uselist=False, cascade="all, delete-orphan")
    images = relationship("GeneratedImage", back_populates="session", cascade="all, delete-orphan")


class GeneratedBlogContent(Base):
    """
    생성된 블로그 콘텐츠
    """
    __tablename__ = "generated_blog_contents"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("content_generation_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 블로그 콘텐츠
    title = Column(String, nullable=False)  # 블로그 제목
    content = Column(Text, nullable=False)  # 블로그 본문 (마크다운)
    tags = Column(JSON, nullable=True)  # ["태그1", "태그2"]

    # 평가 점수
    score = Column(Integer, nullable=True)  # 블로그 품질 점수 (0-100)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ContentGenerationSession", back_populates="blog_content")
    user = relationship("User")


class GeneratedSNSContent(Base):
    """
    생성된 SNS 콘텐츠 (Instagram/Facebook)
    """
    __tablename__ = "generated_sns_contents"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("content_generation_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # SNS 콘텐츠
    content = Column(Text, nullable=False)  # SNS 본문
    hashtags = Column(JSON, nullable=True)  # ["#해시태그1", "#해시태그2"]

    # 평가 점수
    score = Column(Integer, nullable=True)  # SNS 품질 점수 (0-100)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ContentGenerationSession", back_populates="sns_content")
    user = relationship("User")


class GeneratedXContent(Base):
    """
    생성된 X(Twitter) 콘텐츠
    """
    __tablename__ = "generated_x_contents"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("content_generation_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # X 콘텐츠
    content = Column(Text, nullable=False)  # X 본문 (280자 이내)
    hashtags = Column(JSON, nullable=True)  # ["#해시태그1", "#해시태그2"]

    # 평가 점수
    score = Column(Integer, nullable=True)  # X 품질 점수 (0-100)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ContentGenerationSession", back_populates="x_content")
    user = relationship("User")


class GeneratedThreadsContent(Base):
    """
    생성된 Threads 콘텐츠
    """
    __tablename__ = "generated_threads_contents"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("content_generation_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Threads 콘텐츠
    content = Column(Text, nullable=False)  # Threads 본문 (500자 이내)
    hashtags = Column(JSON, nullable=True)  # ["#해시태그1", "#해시태그2"]

    # 평가 점수
    score = Column(Integer, nullable=True)  # Threads 품질 점수 (0-100)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ContentGenerationSession", back_populates="threads_content")
    user = relationship("User")


class GeneratedImage(Base):
    """
    생성된 이미지
    """
    __tablename__ = "generated_images"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("content_generation_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 이미지 정보
    image_url = Column(String, nullable=False)  # 이미지 URL
    prompt = Column(Text, nullable=True)  # 생성에 사용된 프롬프트

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ContentGenerationSession", back_populates="images")
    user = relationship("User")


class GeneratedCardnewsContent(Base):
    """
    생성된 카드뉴스 콘텐츠
    - 각 페이지 이미지와 메타데이터 저장
    """
    __tablename__ = "generated_cardnews_contents"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("content_generation_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 카드뉴스 기본 정보
    title = Column(String, nullable=False)  # 카드뉴스 제목 (첫 페이지 타이틀)
    prompt = Column(Text, nullable=False)  # 사용자 입력 프롬프트
    purpose = Column(String(20), nullable=True)  # promotion, menu, info, event
    page_count = Column(Integer, nullable=False)  # 페이지 수

    # 카드뉴스 페이지 이미지 URL (Supabase Storage)
    card_image_urls = Column(JSON, nullable=False)  # ["https://...", "https://..."]

    # AI 분석 결과
    analysis_data = Column(JSON, nullable=True)  # Orchestrator 분석 결과
    pages_data = Column(JSON, nullable=True)  # 각 페이지별 title, content, layout 등

    # 디자인 설정
    design_settings = Column(JSON, nullable=True)  # bg_color, text_color, font_pair, style 등

    # 품질 점수
    quality_score = Column(Float, nullable=True)  # QA Agent 평가 점수

    # 평가 점수 (통합 - 다른 콘텐츠와 일관성)
    score = Column(Integer, nullable=True)  # 품질 점수 (0-100)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ContentGenerationSession", back_populates="cardnews_content")
    user = relationship("User")


class ThreadsConnection(Base):
    """
    Threads 계정 연동 정보 모델
    - Meta의 Threads API를 사용한 OAuth 연동
    - Instagram 계정과 연결된 Threads 프로필
    """
    __tablename__ = "threads_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Threads 사용자 정보
    threads_user_id = Column(String, nullable=False, index=True)  # Threads 사용자 ID
    username = Column(String, nullable=True)  # @username
    name = Column(String, nullable=True)  # 표시 이름
    threads_profile_picture_url = Column(String, nullable=True)  # 프로필 이미지 URL
    threads_biography = Column(Text, nullable=True)  # 자기소개

    # 계정 통계
    followers_count = Column(Integer, default=0)  # 팔로워 수

    # OAuth 토큰 정보
    access_token = Column(Text, nullable=False)  # 액세스 토큰
    refresh_token = Column(Text, nullable=True)  # 리프레시 토큰 (장기 토큰)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)  # 토큰 만료 시간

    # 연동 상태
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="threads_connection")
    posts = relationship("ThreadsPost", back_populates="connection", cascade="all, delete-orphan")


class ThreadsPost(Base):
    """
    Threads 포스트 모델
    - 연동된 계정의 포스트 목록 및 통계
    """
    __tablename__ = "threads_posts"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("threads_connections.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 포스트 기본 정보
    threads_post_id = Column(String, nullable=False, unique=True, index=True)  # Threads 미디어 ID
    media_type = Column(String, nullable=True)  # TEXT_POST, IMAGE, VIDEO, CAROUSEL
    media_url = Column(String, nullable=True)  # 미디어 URL
    thumbnail_url = Column(String, nullable=True)  # 썸네일 URL (비디오용)
    permalink = Column(String, nullable=True)  # 포스트 링크
    text = Column(Text, nullable=True)  # 포스트 텍스트
    timestamp = Column(DateTime(timezone=True), nullable=True)  # 게시 시간

    # 포스트 상태
    is_quote_post = Column(Boolean, default=False)  # 인용 포스트 여부

    # 포스트 통계
    like_count = Column(Integer, default=0)  # 좋아요 수
    reply_count = Column(Integer, default=0)  # 답글 수
    repost_count = Column(Integer, default=0)  # 리포스트 수
    quote_count = Column(Integer, default=0)  # 인용 포스트 수
    views_count = Column(Integer, default=0)  # 조회수

    # 동기화 정보
    last_stats_updated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    connection = relationship("ThreadsConnection", back_populates="posts")


class PublishedContent(Base):
    """
    발행/임시저장 콘텐츠 모델
    - 생성된 콘텐츠를 편집하여 저장 (임시저장, 예약발행, 발행완료)
    - ContentGenerationSession의 원본을 보존하고 편집본을 별도 관리
    """
    __tablename__ = "published_contents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("content_generation_sessions.id"), nullable=True, index=True)

    # 플랫폼 정보
    platform = Column(String(20), nullable=False)  # 'blog', 'sns', 'x', 'threads'

    # 편집된 콘텐츠
    title = Column(String(500), nullable=True)  # 블로그용 제목
    content = Column(Text, nullable=False)  # 본문
    tags = Column(JSON, nullable=True)  # 태그/해시태그 배열

    # 이미지 참조
    image_ids = Column(JSON, nullable=True)  # generated_images ID 목록
    uploaded_image_url = Column(String(500), nullable=True)  # 직접 업로드한 이미지 URL

    # 상태 관리
    status = Column(String(20), nullable=False, default="draft")
    # 'draft' (임시저장/작성 중)
    # 'scheduled' (예약됨)
    # 'published' (발행됨)
    # 'failed' (발행 실패)

    # 예약/발행 정보
    scheduled_at = Column(DateTime(timezone=True), nullable=True)  # 예약 발행 시간
    published_at = Column(DateTime(timezone=True), nullable=True)  # 실제 발행 시간
    publish_url = Column(String(500), nullable=True)  # 발행된 게시물 URL
    platform_post_id = Column(String(100), nullable=True)  # 플랫폼별 게시물 ID (X post_id 등)
    publish_error = Column(Text, nullable=True)  # 발행 실패 에러 메시지

    # 통계 (발행 후 업데이트)
    views = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    session = relationship("ContentGenerationSession")


class TikTokConnection(Base):
    """
    TikTok 비즈니스 계정 연동 정보 모델
    - TikTok for Business API를 사용한 OAuth 2.0 연동
    """
    __tablename__ = "tiktok_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # TikTok 사용자 정보
    tiktok_user_id = Column(String, nullable=False, index=True)  # TikTok 사용자 ID (open_id)
    union_id = Column(String, nullable=True)  # TikTok Union ID
    username = Column(String, nullable=True)  # @username (display_name)
    avatar_url = Column(String, nullable=True)  # 프로필 이미지 URL
    bio_description = Column(Text, nullable=True)  # 자기소개
    profile_deep_link = Column(String, nullable=True)  # 프로필 딥링크

    # 계정 통계
    follower_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)  # 받은 좋아요 수
    video_count = Column(Integer, default=0)

    # OAuth 2.0 토큰 정보
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # 연동 상태
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="tiktok_connection")
    videos = relationship("TikTokVideo", back_populates="connection", cascade="all, delete-orphan")


class TikTokVideo(Base):
    """
    TikTok 동영상 모델
    - 연동된 계정의 동영상 목록 및 통계
    """
    __tablename__ = "tiktok_videos"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("tiktok_connections.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 동영상 기본 정보
    video_id = Column(String, nullable=False, unique=True, index=True)  # TikTok 동영상 ID
    title = Column(String, nullable=True)  # 동영상 제목
    description = Column(Text, nullable=True)  # 동영상 설명
    cover_image_url = Column(String, nullable=True)  # 커버 이미지 URL
    share_url = Column(String, nullable=True)  # 공유 URL
    embed_link = Column(String, nullable=True)  # 임베드 링크
    duration = Column(Integer, nullable=True)  # 동영상 길이 (초)
    create_time = Column(DateTime(timezone=True), nullable=True)  # 업로드 시간

    # 동영상 통계
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)

    # 동기화 정보
    last_stats_updated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    connection = relationship("TikTokConnection", back_populates="videos")


class WordPressConnection(Base):
    """
    WordPress 사이트 연동 정보 모델
    - WordPress REST API를 사용한 Application Password 또는 OAuth 연동
    """
    __tablename__ = "wordpress_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # WordPress 사이트 정보
    site_url = Column(String, nullable=False)  # WordPress 사이트 URL
    site_name = Column(String, nullable=True)  # 사이트 이름
    site_description = Column(Text, nullable=True)  # 사이트 설명
    site_icon_url = Column(String, nullable=True)  # 사이트 아이콘

    # WordPress 사용자 정보
    wp_user_id = Column(Integer, nullable=True)  # WordPress 사용자 ID
    wp_username = Column(String, nullable=True)  # WordPress 사용자명
    wp_display_name = Column(String, nullable=True)  # 표시 이름
    wp_email = Column(String, nullable=True)  # 이메일
    wp_avatar_url = Column(String, nullable=True)  # 아바타 URL

    # 인증 정보 (Application Password 방식)
    wp_app_password = Column(Text, nullable=True)  # Application Password (암호화 저장)

    # 사이트 통계
    post_count = Column(Integer, default=0)  # 게시물 수
    page_count = Column(Integer, default=0)  # 페이지 수
    category_count = Column(Integer, default=0)  # 카테고리 수

    # 카테고리 캐싱
    categories = Column(JSON, nullable=True)  # [{"id": 1, "name": "...", "slug": "..."}, ...]

    # 연동 상태
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="wordpress_connection")
    posts = relationship("WordPressPost", back_populates="connection", cascade="all, delete-orphan")


class WordPressPost(Base):
    """
    WordPress 게시물 모델
    - 연동된 사이트의 게시물 목록 및 통계
    """
    __tablename__ = "wordpress_posts"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("wordpress_connections.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 게시물 기본 정보
    wp_post_id = Column(Integer, nullable=False, index=True)  # WordPress 게시물 ID
    title = Column(String, nullable=False)  # 게시물 제목
    content = Column(Text, nullable=True)  # 게시물 본문
    excerpt = Column(Text, nullable=True)  # 요약
    slug = Column(String, nullable=True)  # URL 슬러그
    post_url = Column(String, nullable=True)  # 게시물 URL
    featured_image_url = Column(String, nullable=True)  # 대표 이미지 URL

    # 게시물 상태
    status = Column(String, nullable=True)  # publish, draft, pending, private
    post_type = Column(String, default="post")  # post, page

    # 카테고리/태그
    categories = Column(JSON, nullable=True)  # [{"id": 1, "name": "..."}]
    tags = Column(JSON, nullable=True)  # [{"id": 1, "name": "..."}]

    # 날짜 정보
    published_at = Column(DateTime(timezone=True), nullable=True)
    modified_at = Column(DateTime(timezone=True), nullable=True)

    # 통계 (있는 경우)
    comment_count = Column(Integer, default=0)

    # 동기화 정보
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    connection = relationship("WordPressConnection", back_populates="posts")


# ============================================
# 크레딧 시스템 테이블
# ============================================

class UserCredit(Base):
    """
    사용자 크레딧 잔액 모델
    - 각 사용자의 현재 크레딧 잔액 관리
    """
    __tablename__ = "user_credits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # 크레딧 잔액
    balance = Column(Integer, nullable=False, default=0)  # 현재 잔액

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="credit")
    transactions = relationship("CreditTransaction", back_populates="user_credit", cascade="all, delete-orphan")


class CreditTransaction(Base):
    """
    크레딧 거래 내역 모델
    - 모든 크레딧 충전/사용/보너스/환불 기록
    """
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_credit_id = Column(Integer, ForeignKey("user_credits.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 거래 정보
    amount = Column(Integer, nullable=False)  # +충전/보너스, -사용
    type = Column(String(20), nullable=False)  # charge, use, bonus, refund
    description = Column(String(255), nullable=True)  # 거래 설명 (예: '숏폼 영상 생성 (30초)', '회원가입 보너스')

    # 잔액 스냅샷
    balance_before = Column(Integer, nullable=False)  # 거래 전 잔액
    balance_after = Column(Integer, nullable=False)  # 거래 후 잔액

    # 참조 정보
    reference_type = Column(String(50), nullable=True)  # video_generation, image_generation, cardnews, package_charge
    reference_id = Column(String(100), nullable=True)  # 관련 콘텐츠/패키지 ID
    package_id = Column(Integer, ForeignKey("credit_packages.id"), nullable=True)  # 충전 패키지 ID (충전 시)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user_credit = relationship("UserCredit", back_populates="transactions")
    user = relationship("User")
    package = relationship("CreditPackage")


class CreditPackage(Base):
    """
    크레딧 충전 패키지 모델
    - 구매 가능한 크레딧 패키지 정의
    """
    __tablename__ = "credit_packages"

    id = Column(Integer, primary_key=True, index=True)

    # 패키지 정보
    name = Column(String(50), nullable=False)  # 패키지명 (스타터, 베이직, 프로, 엔터프라이즈)
    description = Column(String(255), nullable=True)  # 패키지 설명
    credits = Column(Integer, nullable=False)  # 기본 크레딧 수량
    bonus_credits = Column(Integer, nullable=False, default=0)  # 보너스 크레딧
    price = Column(Integer, nullable=False)  # 가격 (원화)

    # 표시 정보
    badge = Column(String(20), nullable=True)  # 뱃지 (인기, 추천, BEST 등)
    is_popular = Column(Boolean, default=False)  # 인기 패키지 여부

    # 상태
    is_active = Column(Boolean, default=True)  # 활성화 여부
    sort_order = Column(Integer, default=0)  # 정렬 순서

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ============================================
# 템플릿 갤러리 시스템
# ============================================

class TemplateTab(Base):
    """
    사용자별 템플릿 탭 모델
    - 사용자가 직접 생성/수정/삭제 가능한 템플릿 카테고리
    """
    __tablename__ = "template_tabs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 탭 정보
    tab_key = Column(String(50), nullable=False)  # 고유 키 (영문, 예: promotion, event)
    label = Column(String(50), nullable=False)  # 표시 이름 (예: 홍보, 이벤트)
    icon = Column(String(10), nullable=False, default="📁")  # 이모지 아이콘
    sort_order = Column(Integer, default=0)  # 정렬 순서

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    templates = relationship("Template", back_populates="tab", cascade="all, delete-orphan")


class Template(Base):
    """
    사용자별 프롬프트 템플릿 모델
    - 자주 사용하는 프롬프트를 템플릿으로 저장
    """
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tab_id = Column(Integer, ForeignKey("template_tabs.id"), nullable=False, index=True)

    # 템플릿 정보
    name = Column(String(100), nullable=False)  # 템플릿 이름
    category = Column(String(50), nullable=True)  # 세부 카테고리 (예: 신제품 출시)
    description = Column(String(255), nullable=True)  # 간단한 설명
    prompt = Column(Text, nullable=False)  # 프롬프트 내용
    icon = Column(String(10), nullable=False, default="📝")  # 이모지 아이콘

    # 통계
    uses = Column(Integer, default=0)  # 사용 횟수

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")
    tab = relationship("TemplateTab", back_populates="templates")
