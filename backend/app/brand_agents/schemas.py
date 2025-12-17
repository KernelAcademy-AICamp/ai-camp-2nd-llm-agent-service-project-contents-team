"""
Brand Analysis Schemas

브랜드 분석을 위한 데이터 스키마 정의
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass


# ===== 데이터 출처 및 신뢰도 상수 =====

class BrandProfileSource:
    """BrandProfile 데이터 출처"""
    INFERRED = "inferred_from_business_info"  # 비즈니스 정보에서 추론
    SNS_ANALYSIS = "analyzed_from_sns"        # SNS 실제 분석
    MANUAL_SAMPLES = "analyzed_from_samples"  # 수동 샘플 분석
    USER_EDITED = "user_edited"               # 사용자 직접 수정


class ConfidenceLevel:
    """BrandProfile 신뢰도 수준"""
    LOW = "low"        # 추론 기반
    MEDIUM = "medium"  # 소량 샘플 분석
    HIGH = "high"      # 충분한 데이터 분석


# ===== Layer 2: Unified Content Schema =====

@dataclass
class MediaInfo:
    """미디어 정보"""
    type: str  # 'image', 'video', 'none'
    urls: List[str]
    count: int


@dataclass
class EngagementMetrics:
    """참여 지표"""
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0


@dataclass
class UnifiedContent:
    """
    플랫폼 간 통합 콘텐츠 구조

    모든 플랫폼 (블로그, 인스타그램, 유튜브)의 데이터를 통합된 형식으로 변환
    """
    platform: str  # 'naver_blog', 'instagram', 'youtube'
    title: Optional[str]
    body_text: str
    media: Optional[MediaInfo]
    tags: List[str]
    engagement: Optional[EngagementMetrics]
    created_at: Optional[datetime]
    platform_specific: Dict[str, Any]  # 플랫폼별 고유 정보


# ===== Layer 4: Brand Profile Schema =====

class ToneOfVoice(BaseModel):
    """톤 & 보이스 특성"""
    formality: int = Field(..., ge=0, le=100, description="격식 수준 (0: 매우 캐주얼, 100: 매우 격식있는)")
    warmth: int = Field(..., ge=0, le=100, description="따뜻함 (0: 차가운, 100: 매우 따뜻한)")
    enthusiasm: int = Field(..., ge=0, le=100, description="열정 (0: 차분한, 100: 열정적인)")
    sentence_style: str = Field(..., description="문장 스타일 (예: '~해요체', '~합니다체', '반말체')")
    signature_phrases: List[str] = Field(default_factory=list, description="시그니처 표현")
    emoji_usage: Dict[str, Any] = Field(
        default_factory=dict,
        description="이모지 사용 패턴 (frequency, preferred_emojis)"
    )


class ContentStrategy(BaseModel):
    """콘텐츠 전략"""
    primary_topics: List[str] = Field(..., description="주요 주제")
    content_structure: str = Field(..., description="콘텐츠 구조 (예: 도입-본론-결론)")
    call_to_action_style: str = Field(..., description="행동 유도 방식")
    keyword_usage: Dict[str, int] = Field(default_factory=dict, description="핵심 키워드 및 빈도")
    posting_frequency: Optional[str] = Field(None, description="게시 빈도 (예: '주 2-3회')")


class VisualStyle(BaseModel):
    """시각적 스타일 (이미지/영상)"""
    color_palette: List[str] = Field(default_factory=list, description="주요 색상 팔레트 (HEX 코드)")
    image_style: Optional[str] = Field(None, description="이미지 스타일 (예: '밝고 화사한', '미니멀')")
    composition_style: Optional[str] = Field(None, description="구도 스타일 (예: '중앙 정렬', '그리드 레이아웃')")
    filter_preference: Optional[str] = Field(None, description="필터 선호도")


class BrandIdentity(BaseModel):
    """브랜드 아이덴티티"""
    brand_name: Optional[str] = Field(None, description="브랜드명")
    business_type: Optional[str] = Field(None, description="업종")
    brand_personality: str = Field(..., description="브랜드 성격 (2-3문장)")
    brand_values: List[str] = Field(..., description="브랜드 가치")
    target_audience: str = Field(..., description="타겟 고객 (구체적으로)")
    emotional_tone: str = Field(..., description="감정적 톤")


class GenerationPrompts(BaseModel):
    """콘텐츠 생성용 프롬프트 템플릿"""
    text_generation_prompt: str = Field(..., description="텍스트 생성용 시스템 프롬프트")
    image_generation_prompt: str = Field(..., description="이미지 생성용 프롬프트")
    video_generation_prompt: Optional[str] = Field(None, description="비디오 생성용 프롬프트")


class BrandProfile(BaseModel):
    """
    최종 브랜드 프로필

    브랜드 분석 결과를 구조화된 형태로 저장
    """
    brand_id: str
    brand_name: Optional[str] = None

    # ===== 브랜드 아이덴티티 =====
    identity: BrandIdentity

    # ===== 톤 & 보이스 =====
    tone_of_voice: ToneOfVoice

    # ===== 콘텐츠 전략 =====
    content_strategy: ContentStrategy

    # ===== 시각적 스타일 =====
    visual_style: VisualStyle

    # ===== 생성용 프롬프트 템플릿 =====
    generation_prompts: GenerationPrompts

    # ===== 메타데이터 =====
    analyzed_platforms: List[str] = Field(..., description="분석된 플랫폼 목록")
    total_contents_analyzed: int = Field(..., description="분석된 총 콘텐츠 수")

    # ===== 데이터 출처 및 신뢰도 =====
    source: str = Field(
        default="unknown",
        description="데이터 출처 (inferred_from_business_info, analyzed_from_sns, analyzed_from_samples, user_edited)"
    )
    confidence_level: str = Field(
        default="low",
        description="신뢰도 수준 (low: 추론 기반, medium: 소량 샘플, high: 충분한 데이터)"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "brand_id": "user_123",
                "brand_name": "카페 블루밍",
                "identity": {
                    "brand_name": "카페 블루밍",
                    "business_type": "카페/베이커리",
                    "brand_personality": "따뜻하고 친근한 동네 카페. 고객과의 소통을 중시하며 수제 디저트의 가치를 전달합니다.",
                    "brand_values": ["정성", "소통", "수제"],
                    "target_audience": "20-30대 직장인 여성",
                    "emotional_tone": "따뜻하고 친근한"
                },
                "tone_of_voice": {
                    "formality": 30,
                    "warmth": 85,
                    "enthusiasm": 70,
                    "sentence_style": "~해요체",
                    "signature_phrases": ["정성껏 준비했어요", "오늘도 맛있게"],
                    "emoji_usage": {
                        "frequency": "높음",
                        "preferred_emojis": ["☕", "🍰", "💕"]
                    }
                },
                "content_strategy": {
                    "primary_topics": ["신메뉴 소개", "제조 과정", "고객 후기"],
                    "content_structure": "스토리텔링 중심",
                    "call_to_action_style": "질문형",
                    "keyword_usage": {"수제": 15, "디저트": 12, "카페": 20}
                },
                "visual_style": {
                    "color_palette": ["#FFE5CC", "#FFC9A6", "#8B4513"],
                    "image_style": "밝고 따뜻한 톤",
                    "composition_style": "중앙 정렬"
                },
                "generation_prompts": {
                    "text_generation_prompt": "20-30대 여성을 위한 친근하고 따뜻한 톤으로 작성...",
                    "image_generation_prompt": "밝고 따뜻한 톤의 카페 이미지..."
                },
                "analyzed_platforms": ["naver_blog", "instagram"],
                "total_contents_analyzed": 25
            }
        }
