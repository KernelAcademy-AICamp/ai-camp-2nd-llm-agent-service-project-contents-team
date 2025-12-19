"""
Brand Profile Synthesizer

분석 결과를 통합하여 최종 BrandProfile 생성
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from .schemas import (
    BrandProfile,
    BrandIdentity,
    ToneOfVoice,
    ContentStrategy,
    VisualStyle,
    GenerationPrompts,
    UnifiedContent,
    BrandProfileSource,
    ConfidenceLevel
)
from ..utils.vertex_ai_client import get_vertex_client

logger = logging.getLogger(__name__)


# ===== Layer 4: Brand Profile Synthesizer =====

class BrandProfileSynthesizer:
    """분석 결과를 통합하여 브랜드 프로필 생성"""

    def __init__(self):
        self.vertex_client = get_vertex_client()

    async def synthesize(
        self,
        user_id: str,
        text_analysis: Dict[str, Any],
        visual_analysis: Dict[str, Any],
        engagement_analysis: Dict[str, Any],
        unified_contents: List[UnifiedContent],
        analyzed_platforms: List[str]
    ) -> BrandProfile:
        """
        분석 결과를 통합하여 BrandProfile 생성

        Args:
            user_id: 사용자 ID
            text_analysis: 텍스트 분석 결과
            visual_analysis: 비주얼 분석 결과
            engagement_analysis: 참여 지표 분석 결과
            unified_contents: 통합 콘텐츠 리스트
            analyzed_platforms: 분석된 플랫폼 목록

        Returns:
            BrandProfile 객체
        """
        try:
            logger.info(f"🔮 [Brand Profile Synthesizer] 브랜드 프로필 통합 시작")

            # ===== 1. Brand Identity 생성 =====
            brand_identity = await self._synthesize_identity(
                text_analysis,
                unified_contents
            )

            # ===== 2. Tone of Voice 생성 =====
            tone_of_voice = self._synthesize_tone_of_voice(text_analysis)

            # ===== 3. Content Strategy 생성 =====
            content_strategy = self._synthesize_content_strategy(text_analysis)

            # ===== 4. Visual Style 생성 =====
            visual_style = self._synthesize_visual_style(visual_analysis)

            # ===== 5. Generation Prompts 생성 =====
            generation_prompts = await self._synthesize_generation_prompts(
                brand_identity,
                tone_of_voice,
                content_strategy,
                visual_style
            )

            # ===== 6. BrandProfile 조립 =====
            brand_profile = BrandProfile(
                brand_id=user_id,
                brand_name=brand_identity.brand_name,
                identity=brand_identity,
                tone_of_voice=tone_of_voice,
                content_strategy=content_strategy,
                visual_style=visual_style,
                generation_prompts=generation_prompts,
                analyzed_platforms=analyzed_platforms,
                total_contents_analyzed=len(unified_contents),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            logger.info("✅ [Brand Profile Synthesizer] 브랜드 프로필 생성 완료")
            return brand_profile

        except Exception as e:
            logger.error(f"❌ [Brand Profile Synthesizer] 통합 실패: {e}")
            raise Exception(f"브랜드 프로필 생성 실패: {str(e)}")

    async def _synthesize_identity(
        self,
        text_analysis: Dict[str, Any],
        unified_contents: List[UnifiedContent]
    ) -> BrandIdentity:
        """Brand Identity 생성"""
        try:
            # 콘텐츠에서 브랜드 정보 추출을 위한 프롬프트
            sample_texts = [c.body_text[:500] for c in unified_contents if c.body_text]
            combined_text = "\n\n".join(sample_texts[:5])  # 처음 5개 샘플만

            prompt = f"""아래 브랜드의 콘텐츠를 분석하여 브랜드 아이덴티티를 파악해주세요.

===== 콘텐츠 샘플 =====
{combined_text}
=======================

다음 정보를 JSON 형식으로 추출해주세요:

{{
  "brand_name": "브랜드명 (콘텐츠에서 반복 언급되는 이름, 없으면 null)",
  "business_type": "업종 - 반드시 다음 중 하나만 선택: food, fashion, health, education, tech, retail, service",
  "brand_personality": "브랜드 성격을 2-3문장으로 설명",
  "brand_values": ["브랜드 가치 1", "가치 2", "가치 3"],
  "target_audience": "타겟 고객 - 반드시 구체적으로 (예: 20-30대 직장인 여성)",
  "emotional_tone": "감정적 톤 (예: 따뜻한, 유머러스한, 진지한)"
}}

**업종 분류 기준:**
- food: 음식점, 카페, 베이커리, 식음료 관련
- fashion: 패션, 뷰티, 화장품, 의류 관련
- health: 헬스, 피트니스, 요가, 운동, 건강 관련
- education: 학원, 교육, 강의, 학습 관련
- tech: IT, 소프트웨어, 기술, 개발 관련
- retail: 소매, 유통, 쇼핑몰, 제품 판매 관련
- service: 서비스업 전반 (위 카테고리에 해당하지 않는 모든 서비스)

**중요 규칙:**
1. business_type은 반드시 위 7개 중 하나의 영문 코드만 사용
2. target_audience는 '전체', '모든 연령' 같은 모호한 답변 금지. 반드시 연령대나 특성을 포함하세요.
"""

            identity_data = await self.vertex_client.generate_json(prompt, temperature=0.3)

            # 업종 검증: 허용된 카테고리만 사용
            valid_business_types = ['food', 'fashion', 'health', 'education', 'tech', 'retail', 'service']
            business_type = identity_data.get("business_type", "service")
            if business_type not in valid_business_types:
                logger.warning(f"⚠️ 유효하지 않은 업종: {business_type}, 기본값 'service'로 설정")
                business_type = "service"

            return BrandIdentity(
                brand_name=identity_data.get("brand_name"),
                business_type=business_type,
                brand_personality=identity_data.get("brand_personality", ""),
                brand_values=identity_data.get("brand_values", []),
                target_audience=identity_data.get("target_audience", "일반 대중"),
                emotional_tone=identity_data.get("emotional_tone", "중립적")
            )

        except Exception as e:
            logger.error(f"❌ Identity 생성 실패: {e}")
            return BrandIdentity(
                brand_name=None,
                business_type="service",
                brand_personality="정의되지 않음",
                brand_values=[],
                target_audience="일반 대중",
                emotional_tone="중립적"
            )

    def _synthesize_tone_of_voice(self, text_analysis: Dict[str, Any]) -> ToneOfVoice:
        """Tone of Voice 생성"""
        try:
            return ToneOfVoice(
                formality=text_analysis.get("formality_score", 50),
                warmth=text_analysis.get("warmth_score", 50),
                enthusiasm=text_analysis.get("enthusiasm_score", 50),
                sentence_style=text_analysis.get("sentence_patterns", ["표준어체"])[0],
                signature_phrases=text_analysis.get("signature_phrases", []),
                emoji_usage=text_analysis.get("emoji_usage", {"frequency": "없음", "preferred_emojis": []})
            )
        except Exception as e:
            logger.error(f"❌ Tone of Voice 생성 실패: {e}")
            return ToneOfVoice(
                formality=50,
                warmth=50,
                enthusiasm=50,
                sentence_style="표준어체",
                signature_phrases=[],
                emoji_usage={"frequency": "없음", "preferred_emojis": []}
            )

    def _synthesize_content_strategy(self, text_analysis: Dict[str, Any]) -> ContentStrategy:
        """Content Strategy 생성"""
        try:
            # keyword_frequency에서 상위 5개 추출
            keyword_freq = text_analysis.get("keyword_frequency", {})

            return ContentStrategy(
                primary_topics=list(keyword_freq.keys())[:5] if keyword_freq else [],
                content_structure=text_analysis.get("writing_style", "정보 전달형"),
                call_to_action_style="표준형",
                keyword_usage=keyword_freq,
                posting_frequency=None
            )
        except Exception as e:
            logger.error(f"❌ Content Strategy 생성 실패: {e}")
            return ContentStrategy(
                primary_topics=[],
                content_structure="정보 전달형",
                call_to_action_style="표준형",
                keyword_usage={},
                posting_frequency=None
            )

    def _synthesize_visual_style(self, visual_analysis: Dict[str, Any]) -> VisualStyle:
        """Visual Style 생성"""
        try:
            return VisualStyle(
                color_palette=visual_analysis.get("color_palette", []),
                image_style=visual_analysis.get("image_style"),
                composition_style=visual_analysis.get("composition_style"),
                filter_preference=None
            )
        except Exception as e:
            logger.error(f"❌ Visual Style 생성 실패: {e}")
            return VisualStyle(
                color_palette=[],
                image_style=None,
                composition_style=None,
                filter_preference=None
            )

    async def _synthesize_generation_prompts(
        self,
        identity: BrandIdentity,
        tone: ToneOfVoice,
        strategy: ContentStrategy,
        visual: VisualStyle
    ) -> GenerationPrompts:
        """콘텐츠 생성용 프롬프트 템플릿 생성"""
        try:
            # 텍스트 생성 프롬프트
            text_prompt = f"""다음 브랜드 특성에 맞춰 콘텐츠를 작성하세요:

**브랜드 특성**
- 브랜드명: {identity.brand_name or '(브랜드명)'}
- 업종: {identity.business_type}
- 타겟 고객: {identity.target_audience}
- 브랜드 성격: {identity.brand_personality}
- 감정적 톤: {identity.emotional_tone}

**글쓰기 스타일**
- 톤앤매너: 격식 수준 {tone.formality}/100, 따뜻함 {tone.warmth}/100, 열정 {tone.enthusiasm}/100
- 문장 스타일: {tone.sentence_style}
- 시그니처 표현: {', '.join(tone.signature_phrases[:3]) if tone.signature_phrases else '없음'}

**콘텐츠 구조**
- {strategy.content_structure}
"""

            # 이미지 생성 프롬프트
            image_prompt = f"""다음 브랜드의 비주얼 스타일에 맞춰 이미지를 생성하세요:

**비주얼 스타일**
- 이미지 스타일: {visual.image_style or '표준 스타일'}
- 구도: {visual.composition_style or '표준 레이아웃'}
- 색상 팔레트: {', '.join(visual.color_palette[:5]) if visual.color_palette else '기본 색상'}

**브랜드 정체성**
- {identity.brand_personality}
- 타겟: {identity.target_audience}
"""

            return GenerationPrompts(
                text_generation_prompt=text_prompt,
                image_generation_prompt=image_prompt,
                video_generation_prompt=None
            )

        except Exception as e:
            logger.error(f"❌ Generation Prompts 생성 실패: {e}")
            return GenerationPrompts(
                text_generation_prompt="표준 스타일로 작성하세요.",
                image_generation_prompt="표준 이미지를 생성하세요.",
                video_generation_prompt=None
            )

    async def synthesize_from_business_info(
        self,
        user_id: str,
        brand_name: str,
        business_type: str,
        business_description: str,
        target_audience: str,
        selected_styles: Optional[List[str]] = None,
        brand_values: Optional[List[str]] = None
    ) -> BrandProfile:
        """
        비즈니스 정보만으로 기본 BrandProfile 생성 (샘플 없음)

        Args:
            user_id: 사용자 ID
            brand_name: 브랜드명
            business_type: 업종
            business_description: 비즈니스 설명
            target_audience: 타겟 고객
            selected_styles: 사용자가 선택한 스타일 (예: ['따뜻한', '친근한'])
            brand_values: 사용자가 입력한 브랜드 가치 (예: ['친환경', '고품질'])

        Returns:
            BrandProfile (source=INFERRED, confidence_level=LOW)
        """
        try:
            logger.info(f"🔮 [Synthesizer] 비즈니스 정보 기반 BrandProfile 생성 시작")

            # AI로 브랜드 특성 추론
            styles_hint = f"사용자가 선택한 스타일: {', '.join(selected_styles)}" if selected_styles else ""
            values_hint = f"사용자가 입력한 브랜드 가치: {', '.join(brand_values)}" if brand_values else ""

            prompt = f"""당신은 브랜드 전략 전문가입니다.
아래 비즈니스 정보를 바탕으로 브랜드 프로필을 추론해주세요:

**제공된 정보:**
- 브랜드명: {brand_name}
- 업종: {business_type}
- 설명: {business_description}
- 타겟 고객: {target_audience}
{styles_hint}
{values_hint}

**업종별 일반적 특성을 고려하여** 다음 항목을 JSON 형식으로 제공해주세요:

{{
  "brand_personality": "브랜드 성격을 2-3문장으로 설명 (업종 + 타겟 + 선택 스타일 반영)",
  "brand_values": {brand_values if brand_values else '["추론된 가치1", "가치2", "가치3"]'},
  "emotional_tone": "감정적 톤 (예: 따뜻하고 친근한)",
  "formality_score": 0-100 (업종 평균 기반 추정. 예: 카페 40-50, IT 60-70),
  "warmth_score": 0-100 (선택 스타일 + 타겟 기반. 따뜻한/친근한 선택 시 높게),
  "enthusiasm_score": 0-100 (업종 + 스타일 기반),
  "writing_style": "예상 글쓰기 스타일",
  "sentence_style": "예상 문장 스타일 (예: ~해요체, ~합니다체)",
  "primary_topics": ["업종 특성상 다룰 주제1", "주제2", "주제3"],
  "color_palette": ["업종에 일반적으로 사용되는 HEX 색상 3개"],
  "image_style": "업종 특성상 어울리는 이미지 스타일"
}}

**중요 규칙:**
1. 모든 값은 업종 특성 기반 합리적 추정
2. 사용자가 선택한 스타일이 있으면 반드시 반영 (warmth_score 등)
3. 극단적 값(0, 100) 피하기
4. brand_values는 사용자 입력이 있으면 그대로 사용
"""

            ai_result = await self.vertex_client.generate_json(prompt, temperature=0.5)

            # BrandIdentity 생성
            brand_identity = BrandIdentity(
                brand_name=brand_name,
                business_type=business_type,
                brand_personality=ai_result.get('brand_personality', '정의되지 않음'),
                brand_values=brand_values if brand_values else ai_result.get('brand_values', []),
                target_audience=target_audience,
                emotional_tone=ai_result.get('emotional_tone', '중립적')
            )

            # ToneOfVoice 생성
            tone_of_voice = ToneOfVoice(
                formality=ai_result.get('formality_score', 50),
                warmth=ai_result.get('warmth_score', 50),
                enthusiasm=ai_result.get('enthusiasm_score', 50),
                sentence_style=ai_result.get('sentence_style', '표준어체'),
                signature_phrases=[],
                emoji_usage={"frequency": "보통", "preferred_emojis": []}
            )

            # ContentStrategy 생성
            content_strategy = ContentStrategy(
                primary_topics=ai_result.get('primary_topics', []),
                content_structure=ai_result.get('writing_style', '정보 전달형'),
                call_to_action_style="표준형",
                keyword_usage={},
                posting_frequency=None
            )

            # VisualStyle 생성
            visual_style = VisualStyle(
                color_palette=ai_result.get('color_palette', []),
                image_style=ai_result.get('image_style', '표준 스타일'),
                composition_style="표준 레이아웃",
                filter_preference=None
            )

            # GenerationPrompts 생성
            generation_prompts = await self._synthesize_generation_prompts(
                brand_identity, tone_of_voice, content_strategy, visual_style
            )

            # BrandProfile 조립
            brand_profile = BrandProfile(
                brand_id=user_id,
                brand_name=brand_name,
                identity=brand_identity,
                tone_of_voice=tone_of_voice,
                content_strategy=content_strategy,
                visual_style=visual_style,
                generation_prompts=generation_prompts,
                analyzed_platforms=[],
                total_contents_analyzed=0,
                source=BrandProfileSource.INFERRED,
                confidence_level=ConfidenceLevel.LOW,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            logger.info("✅ [Synthesizer] 기본 BrandProfile 생성 완료 (추론 기반)")
            return brand_profile

        except Exception as e:
            logger.error(f"❌ [Synthesizer] 기본 BrandProfile 생성 실패: {e}")
            raise Exception(f"기본 브랜드 프로필 생성 실패: {str(e)}")
