"""
Analysis Agents

Text, Visual, Engagement 분석을 수행하는 Agent들
"""

import logging
from typing import List, Dict, Any
from .schemas import UnifiedContent
from ..utils.vertex_ai_client import get_vertex_client

logger = logging.getLogger(__name__)


# ===== Layer 3: Analysis Agents =====

class TextAnalyzerAgent:
    """텍스트 분석 Agent"""

    def __init__(self):
        self.vertex_client = get_vertex_client()

    async def analyze(self, contents: List[UnifiedContent]) -> Dict[str, Any]:
        """
        텍스트 콘텐츠 분석

        Args:
            contents: 통합된 콘텐츠 리스트

        Returns:
            텍스트 분석 결과
            {
                "writing_style": str,
                "tone": str,
                "sentence_patterns": List[str],
                "formality_score": int,
                "warmth_score": int,
                "enthusiasm_score": int,
                "signature_phrases": List[str],
                "emoji_usage": Dict[str, Any],
                "keyword_frequency": Dict[str, int]
            }
        """
        try:
            if not contents:
                logger.warning("⚠️ [Text Analyzer] 분석할 콘텐츠가 없습니다")
                return self._get_default_analysis()

            logger.info(f"📝 [Text Analyzer] {len(contents)}개 콘텐츠 텍스트 분석 시작")

            # 텍스트 추출 및 결합
            texts = []
            for content in contents:
                text_parts = []
                if content.title:
                    text_parts.append(f"제목: {content.title}")
                if content.body_text:
                    text_parts.append(f"본문: {content.body_text[:1000]}")  # 각 본문은 최대 1000자

                if text_parts:
                    texts.append("\n".join(text_parts))

            if not texts:
                logger.warning("⚠️ [Text Analyzer] 추출된 텍스트가 없습니다")
                return self._get_default_analysis()

            # 텍스트를 하나로 결합 (최대 20000자)
            combined_text = "\n\n---\n\n".join(texts)[:20000]

            # Gemini로 텍스트 분석
            prompt = f"""당신은 브랜드 톤앤매너 전문 분석가입니다.

아래 브랜드의 콘텐츠 텍스트들을 분석하여 글쓰기 스타일과 톤을 파악해주세요.

===== 콘텐츠 텍스트 =====
{combined_text}
============================

다음 항목을 JSON 형식으로 분석해주세요:

{{
  "writing_style": "글쓰기 스타일 (예: 스토리텔링 중심, 정보 전달형, 대화형)",
  "tone": "전체적인 톤 (예: 친근하고 따뜻한, 전문적이고 신뢰감 있는)",
  "sentence_patterns": ["문장 패턴 1 (예: ~해요체)", "문장 패턴 2"],
  "formality_score": 격식 수준 (0-100, 0=매우 캐주얼, 100=매우 격식),
  "warmth_score": 따뜻함 수준 (0-100, 0=차가운, 100=매우 따뜻한),
  "enthusiasm_score": 열정 수준 (0-100, 0=차분한, 100=열정적인),
  "signature_phrases": ["시그니처 표현 1", "시그니처 표현 2", "시그니처 표현 3"],
  "emoji_usage": {{
    "frequency": "사용 빈도 (높음/중간/낮음/없음)",
    "preferred_emojis": ["자주 쓰는 이모지 1", "이모지 2"]
  }},
  "keyword_frequency": {{
    "키워드1": 빈도수,
    "키워드2": 빈도수
  }}
}}

**중요**: 반드시 위 JSON 형식으로만 응답하세요. 추가 설명은 포함하지 마세요.
"""

            analysis_result = await self.vertex_client.generate_json(prompt, temperature=0.3)
            logger.info("✅ [Text Analyzer] 텍스트 분석 완료")
            return analysis_result

        except Exception as e:
            logger.error(f"❌ [Text Analyzer] 분석 실패: {e}")
            return self._get_default_analysis()

    def _get_default_analysis(self) -> Dict[str, Any]:
        """기본 분석 결과"""
        return {
            "writing_style": "정보 전달형",
            "tone": "중립적",
            "sentence_patterns": ["표준어체"],
            "formality_score": 50,
            "warmth_score": 50,
            "enthusiasm_score": 50,
            "signature_phrases": [],
            "emoji_usage": {"frequency": "없음", "preferred_emojis": []},
            "keyword_frequency": {}
        }


class VisualAnalyzerAgent:
    """비주얼 분석 Agent"""

    def __init__(self):
        self.vertex_client = get_vertex_client()

    async def analyze(self, contents: List[UnifiedContent]) -> Dict[str, Any]:
        """
        비주얼 콘텐츠 분석

        Args:
            contents: 통합된 콘텐츠 리스트

        Returns:
            비주얼 분석 결과
            {
                "has_visual_content": bool,
                "primary_visual_type": str,
                "color_palette": List[str],
                "image_style": str,
                "composition_style": str,
                "visual_themes": List[str]
            }
        """
        try:
            if not contents:
                logger.warning("⚠️ [Visual Analyzer] 분석할 콘텐츠가 없습니다")
                return self._get_default_analysis()

            logger.info(f"🎨 [Visual Analyzer] {len(contents)}개 콘텐츠 비주얼 분석 시작")

            # 비주얼 콘텐츠 추출
            visual_contents = [c for c in contents if c.media is not None]

            if not visual_contents:
                logger.info("ℹ️ [Visual Analyzer] 비주얼 콘텐츠가 없습니다 - 텍스트 기반 추론")
                return await self._analyze_from_text(contents)

            # 비주얼 콘텐츠 요약
            visual_summary = []
            for content in visual_contents:
                summary = f"""
플랫폼: {content.platform}
미디어 타입: {content.media.type}
미디어 개수: {content.media.count}
캡션/설명: {content.body_text[:200] if content.body_text else 'N/A'}
"""
                visual_summary.append(summary)

            combined_summary = "\n---\n".join(visual_summary)

            # Gemini로 비주얼 분석 (텍스트 기반 추론)
            prompt = f"""당신은 브랜드 비주얼 스타일 전문 분석가입니다.

아래 브랜드의 비주얼 콘텐츠 정보를 분석하여 시각적 스타일을 파악해주세요.

===== 비주얼 콘텐츠 정보 =====
{combined_summary}
===============================

캡션과 설명을 바탕으로 다음 항목을 JSON 형식으로 추론해주세요:

{{
  "has_visual_content": true,
  "primary_visual_type": "주요 비주얼 타입 (image/video)",
  "color_palette": ["추론된 HEX 색상 코드"],
  "image_style": "이미지 스타일 (예: 밝고 화사한, 미니멀, 빈티지)",
  "composition_style": "구도 스타일 (예: 중앙 정렬, 그리드 레이아웃)",
  "visual_themes": ["비주얼 테마 1", "비주얼 테마 2"]
}}

**중요**: 반드시 위 JSON 형식으로만 응답하세요.
"""

            analysis_result = await self.vertex_client.generate_json(prompt, temperature=0.3)
            logger.info("✅ [Visual Analyzer] 비주얼 분석 완료")
            return analysis_result

        except Exception as e:
            logger.error(f"❌ [Visual Analyzer] 분석 실패: {e}")
            return self._get_default_analysis()

    async def _analyze_from_text(self, contents: List[UnifiedContent]) -> Dict[str, Any]:
        """텍스트 기반 비주얼 스타일 추론"""
        # 비주얼 콘텐츠가 없는 경우 텍스트에서 추론
        texts = [c.body_text[:500] for c in contents if c.body_text]
        combined_text = "\n\n".join(texts)[:5000]

        prompt = f"""아래 텍스트를 읽고 이 브랜드가 선호할 것 같은 비주얼 스타일을 추론해주세요.

{combined_text}

JSON 형식으로 응답:
{{
  "has_visual_content": false,
  "primary_visual_type": "none",
  "color_palette": ["추천 색상 팔레트 HEX"],
  "image_style": "추론된 이미지 스타일",
  "composition_style": "추천 구도",
  "visual_themes": ["테마1", "테마2"]
}}
"""

        try:
            return await self.vertex_client.generate_json(prompt, temperature=0.5)
        except:
            return self._get_default_analysis()

    def _get_default_analysis(self) -> Dict[str, Any]:
        """기본 분석 결과"""
        return {
            "has_visual_content": False,
            "primary_visual_type": "none",
            "color_palette": ["#FFFFFF", "#000000"],
            "image_style": "기본 스타일",
            "composition_style": "표준 레이아웃",
            "visual_themes": []
        }


class EngagementAnalyzerAgent:
    """참여 지표 분석 Agent"""

    def __init__(self):
        self.vertex_client = get_vertex_client()

    async def analyze(self, contents: List[UnifiedContent]) -> Dict[str, Any]:
        """
        참여 지표 분석

        Args:
            contents: 통합된 콘텐츠 리스트

        Returns:
            참여 분석 결과
            {
                "has_engagement_data": bool,
                "avg_engagement_rate": float,
                "top_performing_content_types": List[str],
                "engagement_insights": str
            }
        """
        try:
            if not contents:
                logger.warning("⚠️ [Engagement Analyzer] 분석할 콘텐츠가 없습니다")
                return self._get_default_analysis()

            logger.info(f"📊 [Engagement Analyzer] {len(contents)}개 콘텐츠 참여 지표 분석 시작")

            # 참여 지표가 있는 콘텐츠 필터
            contents_with_engagement = [c for c in contents if c.engagement is not None]

            if not contents_with_engagement:
                logger.info("ℹ️ [Engagement Analyzer] 참여 지표가 없습니다")
                return {
                    "has_engagement_data": False,
                    "avg_engagement_rate": 0.0,
                    "top_performing_content_types": [],
                    "engagement_insights": "참여 지표 데이터 없음"
                }

            # 통계 계산
            total_likes = sum(c.engagement.likes for c in contents_with_engagement)
            total_comments = sum(c.engagement.comments for c in contents_with_engagement)
            total_views = sum(c.engagement.views for c in contents_with_engagement)

            avg_likes = total_likes / len(contents_with_engagement)
            avg_comments = total_comments / len(contents_with_engagement)

            # 플랫폼별 성과
            platform_performance = {}
            for content in contents_with_engagement:
                platform = content.platform
                if platform not in platform_performance:
                    platform_performance[platform] = []
                platform_performance[platform].append({
                    'likes': content.engagement.likes,
                    'comments': content.engagement.comments
                })

            # 성과 요약
            summary = f"""
총 콘텐츠 수: {len(contents_with_engagement)}
평균 좋아요: {avg_likes:.1f}
평균 댓글: {avg_comments:.1f}
총 조회수: {total_views}

플랫폼별 성과:
{platform_performance}
"""

            logger.info("✅ [Engagement Analyzer] 참여 지표 분석 완료")

            return {
                "has_engagement_data": True,
                "avg_engagement_rate": avg_likes + avg_comments,
                "top_performing_content_types": list(platform_performance.keys()),
                "engagement_insights": summary
            }

        except Exception as e:
            logger.error(f"❌ [Engagement Analyzer] 분석 실패: {e}")
            return self._get_default_analysis()

    def _get_default_analysis(self) -> Dict[str, Any]:
        """기본 분석 결과"""
        return {
            "has_engagement_data": False,
            "avg_engagement_rate": 0.0,
            "top_performing_content_types": [],
            "engagement_insights": "데이터 없음"
        }
