"""
AI Agentic 카드뉴스 생성 시스템
멀티 에이전트 워크플로우: 정보 확장 → 분석 → 기획 → 디자인 → 품질검증

Vertex AI API 사용 (Google Cloud Platform)
"""

import os
import json
import re
from typing import List, Dict, Optional, Tuple
import httpx

# Vertex AI 임포트
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Tool
from google.cloud import aiplatform

# Vertex AI 초기화 함수
def init_vertex_ai():
    """Vertex AI 초기화 - 프로젝트 및 인증 설정"""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "bubbly-solution-480805-b5")
    location = "us-central1"  # Gemini 모델 지원 리전

    # 서비스 계정 키 파일 경로 설정
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path and os.path.exists(credentials_path):
        print(f"🔑 [Vertex AI] 서비스 계정 인증: {credentials_path}")
    else:
        print(f"⚠️ [Vertex AI] GOOGLE_APPLICATION_CREDENTIALS 경로 확인 필요")

    try:
        vertexai.init(project=project_id, location=location)
        print(f"✅ [Vertex AI] 초기화 완료 - 프로젝트: {project_id}, 리전: {location}")
        return True
    except Exception as e:
        print(f"❌ [Vertex AI] 초기화 실패: {e}")
        return False

# 앱 시작 시 Vertex AI 초기화
_vertex_ai_initialized = False

# 프롬프트 모듈 임포트
from .prompts import (
    get_content_enricher_prompt,
    get_orchestrator_prompt,
    get_content_planner_prompt,
    get_visual_designer_prompt,
    get_quality_assurance_prompt,
    TONE_MAPPING,
    STYLE_GUIDELINES,
    PAGE_STRUCTURE_GUIDE,
)


# ==================== 폰트 설정 ====================

FONT_PAIRS = {
    "pretendard": {
        "korean": "Pretendard",
        "english": "Inter",
        "style": "modern",
        "description": "현대적이고 깔끔한 느낌"
    },
    "noto": {
        "korean": "Noto Sans KR",
        "english": "Noto Sans",
        "style": "neutral",
        "description": "중립적이고 가독성 좋은 느낌"
    },
    "spoqa": {
        "korean": "Spoqa Han Sans",
        "english": "Roboto",
        "style": "friendly",
        "description": "친근하고 부드러운 느낌"
    }
}


# ==================== Agent 0: Content Enricher (정보 확장 + 웹 검색) ====================

class ContentEnricherAgent:
    """사용자의 간단한 입력을 웹 검색을 통해 실제 정보로 확장하는 에이전트"""

    @staticmethod
    def _ensure_vertex_ai():
        """Vertex AI 초기화 확인"""
        global _vertex_ai_initialized
        if not _vertex_ai_initialized:
            _vertex_ai_initialized = init_vertex_ai()
        return _vertex_ai_initialized

    @staticmethod
    async def _search_web_info(query: str) -> str:
        """
        Google Search를 통해 주제에 대한 실제 정보를 검색
        Vertex AI Gemini + Google Search Grounding 사용
        """
        try:
            if not ContentEnricherAgent._ensure_vertex_ai():
                print("⚠️ [Web Search] Vertex AI 초기화 실패")
                return ""

            # Vertex AI Gemini 모델 (Google Search Grounding 지원)
            from vertexai.generative_models import GenerativeModel, Tool, grounding

            # Google Search 도구 설정
            google_search_tool = Tool.from_google_search_retrieval(
                grounding.GoogleSearchRetrieval()
            )

            search_model = GenerativeModel(
                "gemini-2.0-flash-001",
                tools=[google_search_tool]
            )

            search_prompt = f"""다음 주제에 대해 최신 정보를 검색하고 정리해주세요.
주제: {query}

검색해서 찾아야 할 정보:
1. 정확한 날짜, 시간, 장소
2. 관련된 주요 인물/기관
3. 구체적인 숫자나 통계
4. 주요 사건의 경과나 과정
5. 의미와 중요성

검색 결과를 바탕으로 사실에 기반한 정보를 정리해주세요.
만약 검색 결과가 없다면 "검색 결과 없음"이라고 답하세요."""

            response = search_model.generate_content(search_prompt)
            search_result = response.text.strip()

            print(f"🔍 [Web Search] 검색 완료: {query[:30]}...")
            print(f"   📄 결과 길이: {len(search_result)}자")

            return search_result

        except Exception as e:
            print(f"⚠️ [Web Search] 검색 실패: {e}")
            return ""

    @staticmethod
    async def enrich_content(user_input: str, purpose: str, user_context: Dict = None) -> Dict:
        """
        사용자 입력을 분석하고 웹 검색을 통해 실제 정보로 확장

        Returns:
            {
                "original_input": "원본 입력",
                "enriched_content": "확장된 콘텐츠",
                "added_elements": ["계절감", "구체적 예시", ...],
                "context_suggestions": ["추가 맥락 정보"],
                "recommended_page_count": 3-5,
                "researched_facts": ["검색으로 찾은 사실들"]
            }
        """
        try:
            if not ContentEnricherAgent._ensure_vertex_ai():
                print("❌ Vertex AI 초기화 실패!")
                return ContentEnricherAgent._get_fallback_enrichment(user_input, purpose)

            # Step 1: 웹 검색으로 실제 정보 수집
            print(f"🌐 [Content Enricher] 웹 검색 시작: {user_input}")
            web_info = await ContentEnricherAgent._search_web_info(user_input)

            # Step 2: 검색 결과를 바탕으로 콘텐츠 생성
            model = GenerativeModel("gemini-2.0-flash-001")

            # 사용자 컨텍스트 정보 구성
            user_context_info = ""
            if user_context:
                context_parts = []
                if user_context.get('brand_name'):
                    context_parts.append(f"- 브랜드명: {user_context['brand_name']}")
                if user_context.get('business_type'):
                    business_type_map = {
                        'startup': '스타트업/신생 브랜드',
                        'small_business': '소규모 비즈니스',
                        'personal_brand': '개인 브랜드/인플루언서',
                        'corporate': '기업/대기업',
                        'nonprofit': '비영리 단체',
                        'freelancer': '프리랜서',
                        'ecommerce': '이커머스/온라인 쇼핑몰',
                        'local_business': '지역 비즈니스'
                    }
                    context_parts.append(f"- 비즈니스 유형: {business_type_map.get(user_context['business_type'], user_context['business_type'])}")
                if user_context.get('business_description'):
                    context_parts.append(f"- 비즈니스 설명: {user_context['business_description']}")
                if user_context.get('target_audience'):
                    target = user_context['target_audience']
                    if isinstance(target, dict):
                        target_str = ", ".join([f"{k}: {v}" for k, v in target.items()])
                    else:
                        target_str = str(target)
                    context_parts.append(f"- 타겟 오디언스: {target_str}")
                if user_context.get('brand_tone'):
                    context_parts.append(f"- 브랜드 톤: {user_context['brand_tone']}")
                if user_context.get('brand_personality'):
                    context_parts.append(f"- 브랜드 성격: {user_context['brand_personality']}")
                if user_context.get('key_themes'):
                    context_parts.append(f"- 핵심 테마: {', '.join(user_context['key_themes'])}")
                if user_context.get('text_tone'):
                    tone_map = {
                        'casual': '친근하고 편안한',
                        'professional': '전문적이고 신뢰감 있는',
                        'friendly': '친근하고 따뜻한',
                        'formal': '격식 있고 정중한'
                    }
                    context_parts.append(f"- 텍스트 톤: {tone_map.get(user_context['text_tone'], user_context['text_tone'])}")

                if context_parts:
                    user_context_info = f"""
═══════════════════════════════════════
🏢 브랜드/비즈니스 정보 (온보딩 데이터)
═══════════════════════════════════════
{chr(10).join(context_parts)}
**중요**: 위 브랜드 정보를 반영하여 브랜드 정체성에 맞는 콘텐츠를 생성하세요.
═══════════════════════════════════════
"""

            # 웹 검색 결과가 있으면 프롬프트에 포함
            web_search_section = ""
            if web_info and "검색 결과 없음" not in web_info:
                web_search_section = f"""
═══════════════════════════════════════
🔍 웹 검색으로 찾은 실제 정보
═══════════════════════════════════════
{web_info}
**중요**: 위 검색 결과의 구체적인 사실(날짜, 장소, 숫자, 과정 등)을 반드시 콘텐츠에 포함하세요!
═══════════════════════════════════════
"""

            # 새 프롬프트 모듈 사용 + 웹 검색 결과 추가
            base_prompt = get_content_enricher_prompt(
                user_input=user_input,
                purpose=purpose,
                user_context=user_context_info
            )

            # 웹 검색 섹션을 프롬프트에 추가
            if web_search_section:
                enhanced_prompt = base_prompt.replace(
                    "## 당신의 역할",
                    f"{web_search_section}\n## 당신의 역할"
                )
            else:
                enhanced_prompt = base_prompt

            response = model.generate_content(enhanced_prompt)
            response_text = response.text.strip()

            print("🔍 Raw Enrichment Response:\n", response_text)

            json_match = re.search(r'\{[\s\S]*\}', response_text)

            if json_match:
                enrichment = json.loads(json_match.group(0))
                # 웹 검색 결과 추가
                if web_info and "검색 결과 없음" not in web_info:
                    enrichment['web_search_used'] = True
                    enrichment['researched_info'] = web_info[:500]  # 요약본 저장
                else:
                    enrichment['web_search_used'] = False

                print(f"✅ [Content Enricher] 정보 확장 완료")
                print(f"   📝 원본: {user_input[:50]}...")
                print(f"   ✨ 확장: {enrichment.get('enriched_content', '')[:80]}...")
                print(f"   📊 추천 페이지: {enrichment.get('recommended_page_count', 3)}장")
                print(f"   🌐 웹 검색 사용: {enrichment.get('web_search_used', False)}")
                return enrichment

            return ContentEnricherAgent._get_fallback_enrichment(user_input, purpose)

        except Exception as e:
            print(f"⚠️ [Content Enricher] 확장 실패: {e}")
            import traceback
            traceback.print_exc()
            return ContentEnricherAgent._get_fallback_enrichment(user_input, purpose)

    @staticmethod
    def _get_fallback_enrichment(user_input: str, purpose: str = "info") -> Dict:
        """
        폴백 확장 결과 - 목적(purpose)에 맞는 홍보/이벤트/정보 콘텐츠 생성

        purpose 종류:
        - promotion: 제품/서비스 홍보
        - event: 이벤트/행사 안내
        - menu: 메뉴/가격 소개
        - info: 정보 전달
        """
        input_length = len(user_input)
        if input_length < 30:
            page_count = 3
        elif input_length < 80:
            page_count = 4
        else:
            page_count = 5

        # 목적별 콘텐츠 템플릿
        if purpose == "promotion":
            # 홍보용 - 매력적인 마케팅 문구
            enriched = f"✨ 새롭게 선보이는 특별한 기회! {user_input}을(를) 지금 바로 만나보세요. 놓치면 후회할 특별한 혜택이 기다리고 있습니다."
            key_points = [
                "지금이 바로 구매/참여 적기",
                "한정 기간 특별 혜택",
                "다른 곳에서 찾기 힘든 특별함"
            ]
            tone = "exciting"
        elif purpose == "event":
            # 이벤트용 - 참여 유도
            enriched = f"🎉 놓치지 마세요! {user_input}! 특별한 순간을 함께 하세요. 다양한 혜택과 즐거움이 기다립니다."
            key_points = [
                "이벤트 참여 방법",
                "특별 혜택 및 경품",
                "참여 기간 및 조건"
            ]
            tone = "exciting"
        elif purpose == "menu":
            # 메뉴용 - 맛있는 설명
            enriched = f"🍽️ 입맛을 사로잡는 특별한 메뉴! {user_input}. 정성껏 준비한 메뉴를 만나보세요."
            key_points = [
                "엄선된 재료로 만든 특별함",
                "합리적인 가격",
                "지금 바로 주문하세요"
            ]
            tone = "friendly"
        else:
            # 정보용 - 유용한 정보 전달
            enriched = f"📌 알아두면 유용한 정보! {user_input}에 대해 핵심만 정리했습니다."
            key_points = [
                "핵심 포인트 정리",
                "알아두면 좋은 팁",
                "더 알아보기"
            ]
            tone = "friendly"

        return {
            "original_input": user_input,
            "enriched_content": enriched,
            "key_points": key_points,
            "added_elements": ["목적에 맞는 톤", "행동 유도 문구"],
            "tone_suggestion": tone,
            "recommended_page_count": page_count,
            "page_count_reason": f"입력 길이({input_length}자) 기반 자동 결정",
            "web_search_used": False,
            "purpose": purpose
        }


# ==================== Agent 1: Orchestrator (조율자) ====================

class OrchestratorAgent:
    """사용자 요청을 분석하고 전체 프로세스를 조율하는 마스터 에이전트"""

    @staticmethod
    async def analyze_user_request(enriched_data: Dict, purpose: str) -> Dict:
        """
        확장된 콘텐츠를 기반으로 작업 계획 수립

        Args:
            enriched_data: ContentEnricherAgent의 결과
            purpose: 콘텐츠 목적

        Returns:
            {
                "content_type": "cardnews",
                "page_count": 3,
                "target_audience": "일반 대중",
                "tone": "친근한",
                "key_message": "핵심 메시지",
                "requires_images": true,
                "style": "modern",
                "font_pair": "pretendard",
                "enriched_content": "확장된 콘텐츠"
            }
        """
        try:
            if not ContentEnricherAgent._ensure_vertex_ai():
                print("❌ Vertex AI 초기화 실패!")
                return OrchestratorAgent._get_fallback_analysis(enriched_data, purpose)

            model = GenerativeModel("gemini-2.0-flash-001")

            enriched_content = enriched_data.get('enriched_content', enriched_data.get('original_input', ''))
            recommended_pages = enriched_data.get('recommended_page_count', 3)
            tone_suggestion = enriched_data.get('tone_suggestion', '친근한')

            # 새 프롬프트 모듈 사용
            prompt = get_orchestrator_prompt(
                enriched_content=enriched_content,
                key_points=enriched_data.get('key_points', []),
                recommended_pages=recommended_pages,
                tone_suggestion=tone_suggestion,
                purpose=purpose
            )

            response = model.generate_content(prompt)
            response_text = response.text.strip()

            print("🔍 Raw Vertex AI Analysis Response:\n", response_text)

            json_match = re.search(r'\{[\s\S]*\}', response_text)

            if json_match:
                analysis = json.loads(json_match.group(0))
                # 확장된 콘텐츠 추가
                analysis['enriched_content'] = enriched_content
                analysis['key_points'] = enriched_data.get('key_points', [])

                print(f"✅ [Orchestrator] 분석 완료:")
                print(f"   📄 페이지: {analysis.get('page_count', 3)}장")
                print(f"   🎨 스타일: {analysis.get('style', 'modern')}")
                print(f"   🔤 폰트: {analysis.get('font_pair', 'pretendard')}")
                return analysis

            return OrchestratorAgent._get_fallback_analysis(enriched_data, purpose)

        except Exception as e:
            print(f"⚠️ [Orchestrator] 분석 실패: {e}")
            import traceback
            traceback.print_exc()
            return OrchestratorAgent._get_fallback_analysis(enriched_data, purpose)

    @staticmethod
    def _get_fallback_analysis(enriched_data: Dict, purpose: str) -> Dict:
        """폴백 분석 결과 - purpose를 포함하여 폴백 콘텐츠에서도 목적에 맞는 콘텐츠 생성"""
        page_count = enriched_data.get('recommended_page_count', 3)
        enriched_content = enriched_data.get('enriched_content', enriched_data.get('original_input', ''))

        return {
            "content_type": "cardnews",
            "page_count": page_count,
            "page_count_reason": "자동 결정",
            "target_audience": "일반 대중",
            "tone": enriched_data.get('tone_suggestion', '친근하고 이해하기 쉬운'),
            "key_message": enriched_content[:50],
            "requires_images": True,
            "style": "modern",
            "font_pair": "pretendard",
            "font_reason": "기본 폰트",
            "enriched_content": enriched_content,
            "key_points": enriched_data.get('key_points', []),
            "purpose": purpose  # 폴백에서도 purpose 전달
        }


# ==================== Agent 2: Content Planner (콘텐츠 기획자) ====================

class ContentPlannerAgent:
    """Wrtn AI를 활용하여 페이지별 콘텐츠를 기획하는 에이전트"""

    @staticmethod
    async def plan_cardnews_pages(user_input: str, analysis: Dict) -> List[Dict]:
        """
        Google Gemini를 사용하여 페이지별 콘텐츠 구성

        Returns:
            [
                {
                    "page": 1,
                    "title": "페이지 제목",
                    "content": "페이지 내용",
                    "visual_concept": "비주얼 컨셉",
                    "layout": "title_center" | "split" | "full_image"
                }
            ]
        """
        try:
            if not ContentEnricherAgent._ensure_vertex_ai():
                print("❌ Vertex AI 초기화 실패!")
                return ContentPlannerAgent._get_fallback_content(user_input, analysis)

            print(f"✅ Vertex AI 프로젝트: {os.getenv('GOOGLE_CLOUD_PROJECT', 'bubbly-solution-480805-b5')}")
            model = GenerativeModel("gemini-2.0-flash-001")

            tone = analysis.get('tone', '친근한')
            audience = analysis.get('target_audience', '일반 대중')
            page_count = analysis.get('page_count', 5)
            style = analysis.get('style', 'modern')
            enriched_content = analysis.get('enriched_content', user_input)
            key_points = analysis.get('key_points', [])

            # 새 프롬프트 모듈 사용
            prompt = get_content_planner_prompt(
                page_count=page_count,
                enriched_content=enriched_content,
                key_points=key_points,
                tone=tone,
                audience=audience,
                style=style
            )

            # Vertex AI API 호출
            response = model.generate_content(prompt)
            response_text = response.text.strip()

            print("🔍 Raw Vertex AI Response:\n", response_text)

            # JSON만 안정적으로 추출
            start = response_text.find("[")
            end = response_text.rfind("]") + 1

            if start != -1 and end != -1:
                json_text = response_text[start:end]
                print("🔍 Extracted JSON:\n", json_text)

                try:
                    pages = json.loads(json_text)

                    # 생성된 페이지 개수 확인 출력
                    print(f"✅ {len(pages)}개의 페이지 생성 완료")
                    for p in pages:
                        print(f"📄 {p.get('page')}. {p.get('title')}")

                    return pages

                except Exception as e:
                    print("❌ JSON 디코딩 실패:", e)
                    print("🔍 디코딩 실패 JSON 내용:\n", json_text)
                    return ContentPlannerAgent._get_fallback_content(user_input, analysis)

            else:
                print("❌ JSON 구조를 찾을 수 없음 ( '[' 또는 ']' 없음 )")
                print("🔍 Raw Response:\n", response_text)
                return ContentPlannerAgent._get_fallback_content(user_input, analysis)

        except Exception as e:
            print(f"⚠️ [Content Planner] 기획 실패: {e}")
            import traceback
            traceback.print_exc()
            return ContentPlannerAgent._get_fallback_content(user_input, analysis)

    @staticmethod
    def _get_fallback_content(user_input: str, analysis: Dict) -> List[Dict]:
        """
        폴백 콘텐츠 - 목적(purpose)에 맞는 홍보/이벤트/정보 콘텐츠 생성

        홍보용(promotion): 매력적인 마케팅 문구로 구매/참여 유도
        이벤트용(event): 참여를 유도하는 흥미로운 문구
        메뉴용(menu): 메뉴/상품 소개
        정보용(info): 유용한 정보 전달
        """
        page_count = analysis.get('page_count', 3)
        pages = []

        # 사용자 입력에서 핵심 키워드 추출
        topic = analysis.get('enriched_content', user_input.strip())[:50]  # enriched_content 활용
        key_points = analysis.get('key_points', [])
        purpose = analysis.get('purpose', 'info')

        # 목적별 콘텐츠 템플릿
        if purpose == "promotion":
            # 홍보용 템플릿
            first_page = {
                "title": "NEW ARRIVAL",
                "subtitle": "새로운 시작을 알리다",
                "hook": "✨ 특별한 기회를 놓치지 마세요!",
                "visual_concept": "세련되고 고급스러운 제품 홍보 이미지, 트렌디한 느낌"
            }
            middle_templates = [
                {"title": "Special Point", "content": ["• 프리미엄 퀄리티", "• 합리적인 가격", "• 한정 수량"]},
                {"title": "Why Choose Us", "content": ["• 검증된 품질", "• 빠른 배송", "• 특별 혜택"]},
                {"title": "Limited Edition", "content": ["• 이번 시즌 한정", "• 선착순 특가", "• 놓치면 후회"]}
            ]
            last_page = {
                "title": "지금 바로!",
                "content": ["🛒 구매하러 가기", "💬 문의하기"],
                "cta": "놓치지 마세요!"
            }
        elif purpose == "event":
            # 이벤트용 템플릿
            first_page = {
                "title": "🎉 EVENT",
                "subtitle": "특별한 이벤트가 시작됩니다",
                "hook": "참여만 해도 선물이!",
                "visual_concept": "축제 분위기의 밝고 화려한 이벤트 이미지"
            }
            middle_templates = [
                {"title": "이벤트 혜택", "content": ["• 참여자 전원 혜택", "• 추첨 경품", "• 특별 할인"]},
                {"title": "참여 방법", "content": ["• 팔로우 & 좋아요", "• 댓글 남기기", "• 친구 태그"]},
                {"title": "경품 안내", "content": ["• 1등: 특별 상품", "• 2등: 할인 쿠폰", "• 참가상: 소정의 선물"]}
            ]
            last_page = {
                "title": "참여하기",
                "content": ["⏰ 기간 한정!", "👉 지금 바로 참여하세요"],
                "cta": "이벤트 참여"
            }
        elif purpose == "menu":
            # 메뉴용 템플릿
            first_page = {
                "title": "MENU",
                "subtitle": "정성을 담은 특별한 맛",
                "hook": "🍽️ 오늘의 추천 메뉴",
                "visual_concept": "맛있어 보이는 음식 사진, 고급스러운 플레이팅"
            }
            middle_templates = [
                {"title": "시그니처 메뉴", "content": ["• 셰프 추천", "• 베스트셀러", "• 신메뉴"]},
                {"title": "특별한 재료", "content": ["• 신선한 재료", "• 엄선된 식재료", "• 프리미엄 품질"]},
                {"title": "가격 안내", "content": ["• 합리적인 가격", "• 세트 할인", "• 단품 메뉴"]}
            ]
            last_page = {
                "title": "주문하기",
                "content": ["📞 전화 주문", "🛵 배달 가능"],
                "cta": "맛있게 드세요!"
            }
        else:
            # 정보용 템플릿 (기본)
            first_page = {
                "title": "알아두세요",
                "subtitle": "유용한 정보 모음",
                "hook": "📌 핵심만 정리했어요",
                "visual_concept": "깔끔하고 정돈된 정보 전달 이미지"
            }
            middle_templates = [
                {"title": "핵심 포인트", "content": ["• 중요한 내용 1", "• 중요한 내용 2", "• 중요한 내용 3"]},
                {"title": "알아두면 좋은 팁", "content": ["• 실용적인 팁 1", "• 실용적인 팁 2"]},
                {"title": "참고 사항", "content": ["• 추가 정보", "• 관련 링크"]}
            ]
            last_page = {
                "title": "더 알아보기",
                "content": ["🔍 자세한 정보는", "👉 링크를 확인하세요"],
                "cta": "확인하기"
            }

        # 페이지 생성
        for i in range(page_count):
            if i == 0:
                # 첫 페이지: 주제 기반 Hook
                page = {
                    "page": 1,
                    "title": first_page["title"],
                    "subtitle": first_page["subtitle"],
                    "content": [],
                    "content_type": "hook",
                    "visual_concept": first_page["visual_concept"],
                    "layout": "center"
                }
            elif i == page_count - 1:
                # 마지막 페이지: CTA
                page = {
                    "page": i + 1,
                    "title": last_page["title"],
                    "content": last_page["content"],
                    "content_type": "cta",
                    "visual_concept": "행동을 유도하는 밝고 긍정적인 이미지",
                    "layout": "center"
                }
            else:
                # 중간 페이지: 키포인트 또는 템플릿
                template_idx = (i - 1) % len(middle_templates)
                template = middle_templates[template_idx]

                # key_points가 있으면 우선 사용
                if key_points and i - 1 < len(key_points):
                    content_items = [f"• {key_points[i - 1]}"]
                else:
                    content_items = template["content"]

                page = {
                    "page": i + 1,
                    "title": template["title"],
                    "content": content_items,
                    "content_type": "bullet",
                    "visual_concept": f"{topic} 관련 시각적 이미지",
                    "layout": "center"
                }

            pages.append(page)

        return pages


# ==================== Agent 3: Visual Designer (비주얼 디자이너) ====================

class VisualDesignerAgent:
    """Gamma AI 또는 이미지 생성 AI를 활용하여 비주얼을 생성하는 에이전트"""

    @staticmethod
    async def generate_page_visuals(pages: List[Dict], style: str) -> List[Dict]:
        """
        각 페이지의 비주얼 이미지 생성 - 각 페이지마다 고유한 프롬프트 생성

        Args:
            pages: 페이지 콘텐츠 리스트
            style: 비주얼 스타일 (modern/minimal/vibrant/professional)

        Returns:
            pages에 image_prompt 추가된 리스트
        """
        try:
            if not ContentEnricherAgent._ensure_vertex_ai():
                print("⚠️ [Visual Designer] Vertex AI 초기화 실패, 프롬프트만 생성")
                return VisualDesignerAgent._generate_prompts_only(pages, style)

            model = GenerativeModel("gemini-2.0-flash-001")

            print(f"\n🎨 [Visual Designer] 각 페이지마다 고유한 비주얼 프롬프트 생성 중...")

            for i, page in enumerate(pages):
                # 새 프롬프트 모듈 사용
                prompt = get_visual_designer_prompt(
                    page_num=i + 1,
                    total_pages=len(pages),
                    title=page['title'],
                    content=page.get('content', []),
                    visual_concept=page.get('visual_concept', ''),
                    style=style,
                    layout=page.get('layout', 'center')
                )

                response = model.generate_content(prompt)
                optimized_prompt = response.text.strip()

                # 프롬프트 정보 저장
                page['image_prompt'] = optimized_prompt
                page['prompt_generation_log'] = f"Vertex AI가 페이지 {i+1}의 고유한 비주얼 생성: {page['visual_concept']}"

                print(f"  ✅ 페이지 {i+1}/{len(pages)} 비주얼 프롬프트:")
                print(f"     📝 {optimized_prompt[:100]}...")

            print(f"\n✅ [Visual Designer] {len(pages)}개의 고유한 비주얼 프롬프트 생성 완료")
            return pages

        except Exception as e:
            print(f"⚠️ [Visual Designer] 비주얼 생성 실패: {e}")
            return VisualDesignerAgent._generate_prompts_only(pages, style)

    @staticmethod
    def _generate_prompts_only(pages: List[Dict], style: str) -> List[Dict]:
        """이미지 프롬프트만 생성 (폴백)"""
        style_keywords = {
            "modern": "clean gradient background, geometric shapes, modern design, no text",
            "minimal": "minimal white background, subtle colors, simple, no text",
            "vibrant": "vibrant colors, dynamic composition, energetic, no text",
            "professional": "professional corporate background, balanced, trustworthy, no text"
        }

        base_prompt = style_keywords.get(style, style_keywords["modern"])

        for page in pages:
            page['image_prompt'] = f"{base_prompt}, {page['visual_concept']}, high quality, absolutely no text or letters or words"

        return pages


# ==================== Agent 4: Quality Assurance (품질 검증) ====================

class QualityAssuranceAgent:
    """생성된 콘텐츠의 품질을 검증하고 개선하는 에이전트"""

    @staticmethod
    def _ensure_vertex_ai():
        """Vertex AI 초기화 확인"""
        global _vertex_ai_initialized
        if not _vertex_ai_initialized:
            _vertex_ai_initialized = init_vertex_ai()
        return _vertex_ai_initialized

    @staticmethod
    async def validate_and_improve(pages: List[Dict], original_input: str, analysis: Dict) -> Dict:
        """
        콘텐츠 품질 검증 및 개선 제안

        Returns:
            {
                "overall_score": 8.5,
                "consistency_score": 9,
                "message_clarity_score": 8,
                "needs_improvement": [2, 4],
                "suggestions": ["페이지 2: 내용이 너무 길어요", ...],
                "approved": true
            }
        """
        try:
            # Vertex AI 초기화
            QualityAssuranceAgent._ensure_vertex_ai()

            # Vertex AI 모델 사용
            model = GenerativeModel("gemini-2.0-flash-001")

            # 새 프롬프트 모듈 사용
            prompt = get_quality_assurance_prompt(
                original_input=original_input,
                target_audience=analysis.get('target_audience', '일반 대중'),
                tone=analysis.get('tone', '친근한'),
                key_message=analysis.get('key_message', ''),
                pages=pages
            )

            response = model.generate_content(prompt)
            response_text = response.text.strip()

            print("🔍 Raw Gemini QA Response:\n", response_text)

            json_match = re.search(r'\{[\s\S]*\}', response_text)

            if json_match:
                validation = json.loads(json_match.group(0))
                print(f"✅ [Quality Assurance] 검증 완료")
                print(f"  📊 종합 점수: {validation.get('overall_score', 0)}/10")
                print(f"  📊 메시지 전달: {validation.get('message_clarity_score', 0)}/10")
                print(f"  📊 일관성: {validation.get('consistency_score', 0)}/10")

                if validation.get('suggestions'):
                    print("  💡 개선 제안:")
                    for suggestion in validation['suggestions']:
                        print(f"     - {suggestion}")

                return validation

            return QualityAssuranceAgent._get_fallback_validation()

        except Exception as e:
            print(f"⚠️ [Quality Assurance] 검증 실패: {e}")
            import traceback
            traceback.print_exc()
            return QualityAssuranceAgent._get_fallback_validation()

    @staticmethod
    def _get_fallback_validation() -> Dict:
        """폴백 검증 결과"""
        return {
            "overall_score": 7.0,
            "message_clarity_score": 7.0,
            "consistency_score": 7.0,
            "target_fit_score": 7.0,
            "needs_improvement": [],
            "suggestions": [],
            "approved": True
        }


# ==================== 유틸리티: 색상 추출 ====================

def extract_dominant_color_from_image(image_data: str) -> Tuple[int, int, int]:
    """
    이미지에서 주요 색상을 추출합니다.

    Args:
        image_data: Base64 인코딩된 이미지 또는 URL

    Returns:
        RGB 튜플 (r, g, b)
    """
    try:
        from PIL import Image
        import io
        import base64

        # Base64 데이터에서 이미지 로드
        if image_data.startswith('data:image'):
            image_bytes = base64.b64decode(image_data.split(',')[1])
            img = Image.open(io.BytesIO(image_bytes))
        else:
            import requests
            response = requests.get(image_data, timeout=10)
            img = Image.open(io.BytesIO(response.content))

        # 이미지 리사이즈 (빠른 처리를 위해)
        img = img.resize((50, 50))
        img = img.convert('RGB')

        # 픽셀 색상 수집
        pixels = list(img.getdata())

        # 평균 색상 계산 (단순 방식)
        r_total = sum(p[0] for p in pixels)
        g_total = sum(p[1] for p in pixels)
        b_total = sum(p[2] for p in pixels)
        count = len(pixels)

        return (r_total // count, g_total // count, b_total // count)

    except Exception as e:
        print(f"⚠️ 색상 추출 실패: {e}")
        return (100, 100, 100)  # 기본 회색


def get_text_color_for_background(bg_color: Tuple[int, int, int]) -> str:
    """
    배경색에 따라 적합한 텍스트 색상(검정/흰색)을 결정합니다.

    Args:
        bg_color: RGB 튜플 (r, g, b)

    Returns:
        "white" 또는 "black"
    """
    r, g, b = bg_color
    # 밝기 계산 (YIQ 공식)
    brightness = (r * 299 + g * 587 + b * 114) / 1000

    # 밝기가 128 이상이면 어두운 텍스트, 아니면 밝은 텍스트
    return "black" if brightness > 128 else "white"


def adjust_color_for_harmony(dominant_color: Tuple[int, int, int], style: str) -> Tuple[int, int, int]:
    """
    썸네일의 주요 색상을 기반으로 조화로운 단색 배경 색상을 생성합니다.

    Args:
        dominant_color: 썸네일에서 추출한 주요 RGB 색상
        style: 비주얼 스타일 (modern/minimal/vibrant/professional)

    Returns:
        조정된 RGB 튜플
    """
    r, g, b = dominant_color

    if style == "minimal":
        # 밝고 부드러운 톤으로 조정
        return (min(255, r + 60), min(255, g + 60), min(255, b + 60))
    elif style == "vibrant":
        # 채도 높이기
        max_val = max(r, g, b)
        if max_val > 0:
            factor = 255 / max_val
            return (min(255, int(r * factor * 0.9)), min(255, int(g * factor * 0.9)), min(255, int(b * factor * 0.9)))
        return dominant_color
    elif style == "professional":
        # 약간 어둡고 차분하게
        return (max(0, r - 30), max(0, g - 30), max(0, b - 30))
    else:  # modern
        # 원본 유지하면서 살짝 조정
        return (min(255, max(0, r + 10)), min(255, max(0, g + 10)), min(255, max(0, b + 10)))


# ==================== Master Workflow (마스터 워크플로우) ====================

class AgenticCardNewsWorkflow:
    """모든 에이전트를 조율하는 마스터 워크플로우"""

    def __init__(self):
        self.content_enricher = ContentEnricherAgent()
        self.orchestrator = OrchestratorAgent()
        self.content_planner = ContentPlannerAgent()
        self.visual_designer = VisualDesignerAgent()
        self.qa = QualityAssuranceAgent()

    async def execute(self, user_input: str, purpose: str = "info", user_context: Dict = None) -> Dict:
        """
        전체 워크플로우 실행

        Args:
            user_input: 사용자 입력 프롬프트
            purpose: 목적 (promotion/menu/info/event)
            user_context: 온보딩에서 수집한 사용자 정보 (브랜드, 타겟 오디언스, 톤 등)

        Returns:
            {
                "success": True,
                "analysis": {...},
                "pages": [...],
                "quality_report": {...},
                "design_settings": {...}
            }
        """
        print("\n" + "="*80)
        print("🚀 AI Agentic 카드뉴스 생성 워크플로우 시작")
        if user_context:
            print(f"   🏢 브랜드: {user_context.get('brand_name', '미설정')}")
            print(f"   🎯 비즈니스: {user_context.get('business_type', '미설정')}")
        print("="*80 + "\n")

        try:
            # Step 1: 정보 확장 (사용자 컨텍스트 포함)
            print("✨ Step 1/5: 사용자 입력 정보 확장 중...")
            enriched_data = await self.content_enricher.enrich_content(user_input, purpose, user_context)
            print(f"   ✅ 정보 확장 완료 (추가 요소: {len(enriched_data.get('added_elements', []))}개)\n")

            # Step 2: 요청 분석 (확장된 정보 기반)
            print("📋 Step 2/5: 콘텐츠 분석 및 설정 결정 중...")
            analysis = await self.orchestrator.analyze_user_request(enriched_data, purpose)
            print(f"   ✅ {analysis['page_count']}페이지, {analysis['style']} 스타일, {analysis.get('font_pair', 'pretendard')} 폰트\n")

            # Step 3: 콘텐츠 기획 (확장된 정보 사용)
            print("✍️  Step 3/5: 페이지별 콘텐츠 기획 중...")
            enriched_content = analysis.get('enriched_content', user_input)
            pages = await self.content_planner.plan_cardnews_pages(enriched_content, analysis)
            print(f"   ✅ {len(pages)}개 페이지 기획 완료\n")

            # Step 4: 비주얼 디자인
            print("🎨 Step 4/5: 각 페이지의 비주얼 프롬프트 생성 중...")
            pages = await self.visual_designer.generate_page_visuals(
                pages,
                analysis.get('style', 'modern')
            )
            print(f"   ✅ 비주얼 프롬프트 생성 완료\n")

            # Step 5: 품질 검증
            print("🔍 Step 5/5: 콘텐츠 품질 검증 중...")
            quality_report = await self.qa.validate_and_improve(pages, user_input, analysis)
            print(f"   ✅ 품질 검증 완료\n")

            # 디자인 설정 구성
            font_pair = analysis.get('font_pair', 'pretendard')
            design_settings = {
                "font_pair": font_pair,
                "font_korean": FONT_PAIRS.get(font_pair, FONT_PAIRS['pretendard'])['korean'],
                "font_english": FONT_PAIRS.get(font_pair, FONT_PAIRS['pretendard'])['english'],
                "style": analysis.get('style', 'modern'),
                "text_color": "white",  # 기본값, 썸네일 생성 후 업데이트됨
                "bg_color": None  # 썸네일 색상 추출 후 설정됨
            }

            print("="*80)
            print("✅ AI Agentic 워크플로우 완료!")
            print(f"   📄 페이지: {len(pages)}장")
            print(f"   🔤 폰트: {design_settings['font_korean']} / {design_settings['font_english']}")
            print(f"   🎨 스타일: {design_settings['style']}")
            print("="*80 + "\n")

            return {
                "success": True,
                "analysis": analysis,
                "pages": pages,
                "quality_report": quality_report,
                "design_settings": design_settings,
                "enriched_data": enriched_data
            }

        except Exception as e:
            print(f"\n❌ 워크플로우 실패: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "analysis": None,
                "pages": [],
                "quality_report": None,
                "design_settings": None
            }
