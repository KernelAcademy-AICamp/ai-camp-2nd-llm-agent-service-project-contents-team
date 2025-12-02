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
    planning_model = Column(String, default="claude-3-5-sonnet-20241022")  # 스토리보드 생성 모델
    image_model = Column(String, default="gemini-2.0-flash-exp")  # 이미지 생성 모델
    video_model = Column(String, default="veo-3.1-fast-generate-preview")  # 비디오 생성 모델

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
