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
    HOW_TO_PAGE_STRUCTURE,
)


def get_nearest_page_structure(page_count: int, is_how_to: bool = False) -> dict:
    """
    주어진 페이지 수에 가장 가까운 페이지 구조를 반환합니다.
    정의되지 않은 페이지 수의 경우 가장 가까운 구조를 사용합니다.

    Args:
        page_count: 페이지 수
        is_how_to: How-To 콘텐츠 여부

    Returns:
        페이지 구조 딕셔너리
    """
    structure_guide = HOW_TO_PAGE_STRUCTURE if is_how_to else PAGE_STRUCTURE_GUIDE

    # 정확히 일치하는 구조가 있으면 반환
    if page_count in structure_guide:
        return structure_guide[page_count]

    # 가장 가까운 구조 찾기
    available_counts = sorted(structure_guide.keys())

    # 가장 가까운 값 찾기
    closest = min(available_counts, key=lambda x: abs(x - page_count))

    # 페이지 수가 더 많은 경우, 기본 구조를 확장
    if page_count > max(available_counts):
        base_structure = structure_guide[max(available_counts)]
        return _extend_page_structure(base_structure, page_count)

    return structure_guide[closest]


def _extend_page_structure(base_structure: dict, target_count: int) -> dict:
    """
    기본 구조를 확장하여 더 많은 페이지를 지원합니다.
    """
    base_count = len(base_structure['structure'])
    extra_pages = target_count - base_count

    # 구조 확장
    extended_structure = base_structure['structure'].copy()
    extended_roles = base_structure['page_roles'].copy()

    # CTA를 마지막으로 유지하면서 중간에 Detail 페이지 추가
    cta_structure = extended_structure[-1]
    cta_role = extended_roles.get(base_count, '행동 촉구 - 다음 단계')

    # CTA 제거 후 추가 페이지 삽입
    extended_structure = extended_structure[:-1]

    for i in range(extra_pages):
        page_num = base_count + i
        extended_structure.append(f'Details{i+1}')
        extended_roles[page_num] = f'추가 세부 정보 {i+1}'

    # CTA 다시 추가
    extended_structure.append(cta_structure)
    extended_roles[target_count] = cta_role

    return {
        'structure': extended_structure,
        'description': f'{target_count}장 확장 구성',
        'page_roles': extended_roles
    }


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

    # "~ 하는 방법" 패턴 감지를 위한 정규식
    HOW_TO_PATTERNS = [
        r'(.+?)\s*하는\s*방법',           # "~ 하는 방법"
        r'(.+?)\s*하는\s*법',             # "~ 하는 법"
        r'어떻게\s*(.+?)(?:\s*할까|\s*하나|\s*해요|\s*합니까)',  # "어떻게 ~ 할까/하나/해요"
        r'(.+?)\s*(?:방법|팁|노하우)',    # "~ 방법/팁/노하우"
        r'(.+?)\s*(?:가이드|튜토리얼)',   # "~ 가이드/튜토리얼"
    ]

    @staticmethod
    def _detect_how_to_pattern(user_input: str) -> Tuple[bool, str]:
        """
        "~ 하는 방법" 패턴 감지

        Returns:
            (is_how_to: bool, extracted_topic: str)
        """
        import re

        for pattern in ContentEnricherAgent.HOW_TO_PATTERNS:
            match = re.search(pattern, user_input)
            if match:
                topic = match.group(1).strip()
                print(f"🔍 [How-To 패턴 감지] 주제: '{topic}'")
                return True, topic

        return False, user_input

    @staticmethod
    def _ensure_vertex_ai():
        """Vertex AI 초기화 확인"""
        global _vertex_ai_initialized
        if not _vertex_ai_initialized:
            _vertex_ai_initialized = init_vertex_ai()
        return _vertex_ai_initialized

    @staticmethod
    async def _search_web_info(query: str, is_how_to: bool = False) -> str:
        """
        Google Search를 통해 주제에 대한 실제 정보를 검색
        Vertex AI Gemini + Google Search Grounding 사용

        Args:
            query: 검색 쿼리
            is_how_to: "~ 하는 방법" 패턴인지 여부
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

            # "~ 하는 방법" 패턴인 경우 단계별 가이드 검색
            if is_how_to:
                search_prompt = f"""다음 주제에 대해 실용적인 방법/가이드를 검색하고 정리해주세요.
주제: {query}

검색해서 찾아야 할 정보:
1. **단계별 방법** (Step 1, Step 2, ... 형태로 정리)
2. **필요한 준비물/조건** (있다면)
3. **주의사항 및 팁**
4. **예상 소요 시간/비용** (해당되는 경우)
5. **자주 하는 실수와 해결법**

검색 결과를 바탕으로 실제로 도움이 되는 단계별 가이드를 정리해주세요.
각 단계는 구체적이고 실행 가능해야 합니다.
만약 검색 결과가 없다면 "검색 결과 없음"이라고 답하세요."""
            else:
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

            print(f"🔍 [Web Search] 검색 완료: {query[:30]}... (How-To: {is_how_to})")
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
                "researched_facts": ["검색으로 찾은 사실들"],
                "is_how_to": True/False,
                "content_mode": "how_to" | "general"
            }
        """
        try:
            if not ContentEnricherAgent._ensure_vertex_ai():
                print("❌ Vertex AI 초기화 실패!")
                return ContentEnricherAgent._get_fallback_enrichment(user_input, purpose)

            # Step 0: "~ 하는 방법" 패턴 감지
            is_how_to, extracted_topic = ContentEnricherAgent._detect_how_to_pattern(user_input)

            if is_how_to:
                print(f"📚 [Content Enricher] How-To 모드 활성화: '{extracted_topic}'")
                # How-To 패턴인 경우 purpose를 'how_to'로 변경
                purpose = "how_to"

            # Step 1: 웹 검색으로 실제 정보 수집
            print(f"🌐 [Content Enricher] 웹 검색 시작: {user_input}")
            web_info = await ContentEnricherAgent._search_web_info(user_input, is_how_to=is_how_to)

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

            # 새 프롬프트 모듈 사용 + 웹 검색 결과 추가 (How-To 모드 전달)
            base_prompt = get_content_enricher_prompt(
                user_input=user_input,
                purpose=purpose,
                user_context=user_context_info,
                is_how_to=is_how_to
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

                # How-To 모드 플래그 추가
                enrichment['is_how_to'] = is_how_to
                enrichment['content_mode'] = 'how_to' if is_how_to else 'general'

                # How-To 콘텐츠는 기본적으로 4-5페이지 권장
                if is_how_to and enrichment.get('recommended_page_count', 3) < 4:
                    enrichment['recommended_page_count'] = 4
                    enrichment['page_count_reason'] = "How-To 콘텐츠: 단계별 설명을 위해 4페이지 이상 필요"

                print(f"✅ [Content Enricher] 정보 확장 완료")
                print(f"   📝 원본: {user_input[:50]}...")
                print(f"   ✨ 확장: {enrichment.get('enriched_content', '')[:80]}...")
                print(f"   📊 추천 페이지: {enrichment.get('recommended_page_count', 3)}장")
                print(f"   🌐 웹 검색 사용: {enrichment.get('web_search_used', False)}")
                print(f"   📚 How-To 모드: {is_how_to}")
                return enrichment

            return ContentEnricherAgent._get_fallback_enrichment(user_input, purpose, is_how_to)

        except Exception as e:
            print(f"⚠️ [Content Enricher] 확장 실패: {e}")
            import traceback
            traceback.print_exc()
            is_how_to_fallback, _ = ContentEnricherAgent._detect_how_to_pattern(user_input)
            return ContentEnricherAgent._get_fallback_enrichment(user_input, purpose, is_how_to_fallback)

    @staticmethod
    def _get_fallback_enrichment(user_input: str, purpose: str = "info", is_how_to: bool = False) -> Dict:
        """
        폴백 확장 결과 - 목적(purpose)에 맞는 전문적인 콘텐츠 생성

        purpose 종류:
        - promotion: 제품/서비스 홍보 (AIDA 구조)
        - event: 이벤트/행사 안내 (5W1H 구조)
        - menu: 메뉴/가격 소개 (감각적 묘사)
        - info: 정보 전달 (가치 중심)
        - how_to: 방법/가이드 설명 (단계별)
        """
        input_length = len(user_input)

        # 콘텐츠 길이 기반 페이지 수 결정 (최대 20장)
        if is_how_to:
            if input_length < 50:
                page_count = 4
            elif input_length < 100:
                page_count = 5
            elif input_length < 200:
                page_count = 6
            elif input_length < 400:
                page_count = 8
            else:
                page_count = 10
        elif input_length < 30:
            page_count = 3
        elif input_length < 80:
            page_count = 4
        elif input_length < 150:
            page_count = 5
        elif input_length < 300:
            page_count = 7
        elif input_length < 500:
            page_count = 10
        elif input_length < 800:
            page_count = 15
        else:
            page_count = 20

        # 목적별 전문 콘텐츠 템플릿
        if is_how_to or purpose == "how_to":
            # How-To: 실용적인 단계별 가이드
            enriched = f"'{user_input}'을(를) 처음 시작하시는 분들을 위한 실전 가이드입니다. 복잡해 보이지만 핵심만 알면 누구나 쉽게 따라할 수 있어요."
            key_points = [
                "시작 전 필수 체크리스트: 준비물과 기본 조건 확인",
                "핵심 단계 1: 기초부터 탄탄하게 시작하기",
                "핵심 단계 2: 실전 적용과 반복 연습",
                "핵심 단계 3: 완성도 높이기와 마무리",
                "실수 방지 팁: 흔히 하는 실수와 해결법",
                "다음 단계: 더 발전하기 위한 추천 리소스"
            ]
            tone = "friendly"
        elif purpose == "promotion":
            # 홍보: AIDA 구조 (Attention → Interest → Desire → Action)
            enriched = f"지금까지 경험해보지 못한 새로운 가치를 만나보세요. {user_input}이(가) 여러분의 일상을 특별하게 바꿔드립니다. 이미 수많은 분들이 만족하고 계십니다."
            key_points = [
                "주목할 가치: 다른 것과 확실히 다른 차별화 포인트",
                "핵심 혜택: 고객이 얻게 되는 구체적인 이점",
                "사회적 증거: 실제 사용자들의 만족 후기",
                "한정 혜택: 지금 선택하면 얻는 특별한 기회",
                "행동 촉구: 망설이면 놓치는 혜택"
            ]
            tone = "professional"
        elif purpose == "event":
            # 이벤트: 5W1H 구조 (What, When, Where, Who, Why, How)
            enriched = f"특별한 순간을 함께 만들어갑니다. {user_input}에 여러분을 초대합니다. 참여하시는 분들께 잊지 못할 경험과 특별한 혜택을 드립니다."
            key_points = [
                "이벤트 소개: 무엇을 경험할 수 있는지",
                "일정 안내: 언제, 어디서 진행되는지",
                "참여 대상: 누구나 환영 또는 특별 조건",
                "참여 혜택: 참가자가 얻는 구체적인 보상",
                "참여 방법: 지금 바로 할 수 있는 행동"
            ]
            tone = "exciting"
        elif purpose == "menu":
            # 메뉴: 감각적 묘사와 스토리텔링
            enriched = f"정성과 전문성으로 준비한 특별한 메뉴입니다. {user_input}의 진정한 맛을 경험해보세요. 엄선된 재료와 장인의 손길이 만나 탄생한 맛입니다."
            key_points = [
                "메뉴 스토리: 이 메뉴가 특별한 이유",
                "재료의 품격: 엄선된 신선한 재료 소개",
                "맛의 특징: 풍미와 식감의 조화",
                "추천 조합: 함께 즐기면 좋은 페어링",
                "주문 안내: 가격과 주문 방법"
            ]
            tone = "friendly"
        else:
            # 정보: 가치 중심 정보 전달
            enriched = f"알아두면 확실히 도움이 되는 정보입니다. {user_input}에 대해 핵심만 정리했습니다. 복잡한 내용을 쉽고 명확하게 이해할 수 있도록 구성했습니다."
            key_points = [
                "핵심 개념: 가장 중요한 것부터 이해하기",
                "왜 중요한가: 이 정보가 필요한 이유",
                "실전 활용법: 일상에서 바로 적용하는 방법",
                "주의사항: 알아두면 피할 수 있는 실수",
                "추가 정보: 더 알고 싶다면 참고할 자료"
            ]
            tone = "professional"

        return {
            "original_input": user_input,
            "enriched_content": enriched,
            "key_points": key_points,
            "added_elements": ["목적별 전문 구조", "구체적 가치 제안", "행동 유도 문구"],
            "tone_suggestion": tone,
            "recommended_page_count": page_count,
            "page_count_reason": f"입력 길이({input_length}자) 기반 자동 결정" if not is_how_to else "How-To 콘텐츠: 단계별 설명 필요",
            "web_search_used": False,
            "purpose": "how_to" if is_how_to else purpose,
            "is_how_to": is_how_to,
            "content_mode": "how_to" if is_how_to else "general"
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
                # How-To 모드 플래그 전달
                analysis['is_how_to'] = enriched_data.get('is_how_to', False)
                analysis['content_mode'] = enriched_data.get('content_mode', 'general')

                print(f"✅ [Orchestrator] 분석 완료:")
                print(f"   📄 페이지: {analysis.get('page_count', 3)}장")
                print(f"   🎨 스타일: {analysis.get('style', 'modern')}")
                print(f"   🔤 폰트: {analysis.get('font_pair', 'pretendard')}")
                print(f"   📚 How-To: {analysis.get('is_how_to', False)}")
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
        is_how_to = enriched_data.get('is_how_to', False)

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
            "purpose": purpose,  # 폴백에서도 purpose 전달
            "is_how_to": is_how_to,  # How-To 모드 플래그
            "content_mode": enriched_data.get('content_mode', 'general')
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
            is_how_to = analysis.get('is_how_to', False) or analysis.get('content_mode') == 'how_to'

            # 새 프롬프트 모듈 사용 (How-To 모드 및 목적 전달)
            purpose = analysis.get('purpose', 'info')
            prompt = get_content_planner_prompt(
                page_count=page_count,
                enriched_content=enriched_content,
                key_points=key_points,
                tone=tone,
                audience=audience,
                style=style,
                is_how_to=is_how_to,
                purpose=purpose
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
        how_to: 단계별 방법 가이드 (신규)
        """
        page_count = analysis.get('page_count', 3)
        pages = []

        # 사용자 입력에서 핵심 키워드 추출
        topic = analysis.get('enriched_content', user_input.strip())[:50]  # enriched_content 활용
        key_points = analysis.get('key_points', [])
        purpose = analysis.get('purpose', 'info')
        is_how_to = analysis.get('is_how_to', False) or analysis.get('content_mode') == 'how_to'

        # How-To 콘텐츠 전용 템플릿
        if is_how_to or purpose == "how_to":
            page_count = max(page_count, 4)  # How-To는 최소 4페이지
            first_page = {
                "title": f"{topic[:15]}... 하는 법" if len(topic) > 15 else f"{topic} 하는 법",
                "subtitle": "쉽게 따라할 수 있는 완벽 가이드",
                "hook": "📚 초보자도 OK!",
                "visual_concept": "밝고 긍정적인 교육/가이드 느낌의 이미지"
            }
            middle_templates = [
                {"title": "Step 1: 준비하기", "content": ["• 필요한 것들 확인", "• 기본 환경 설정", "• 시작 전 체크리스트"], "content_type": "step"},
                {"title": "Step 2: 시작하기", "content": ["• 첫 번째 단계 실행", "• 중요 포인트 확인", "• 진행 상황 체크"], "content_type": "step"},
                {"title": "Step 3: 마무리", "content": ["• 결과 확인하기", "• 오류 점검", "• 최종 완료"], "content_type": "step"}
            ]
            last_page = {
                "title": "Pro Tip",
                "content": ["💡 더 잘하는 비결", "⚠️ 주의할 점", "✅ 핵심 요약"],
                "cta": "성공!"
            }

            # key_points가 있으면 적용
            if key_points and len(key_points) >= 3:
                for i, template in enumerate(middle_templates):
                    if i < len(key_points) - 1:  # 마지막 하나는 Pro Tip용
                        template["content"] = [f"• {key_points[i]}"]

            # 페이지 생성 (How-To 전용)
            for i in range(page_count):
                if i == 0:
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
                    page = {
                        "page": i + 1,
                        "title": last_page["title"],
                        "content": last_page["content"],
                        "content_type": "tips",
                        "visual_concept": "성공/달성을 상징하는 긍정적 이미지",
                        "layout": "center"
                    }
                else:
                    template_idx = (i - 1) % len(middle_templates)
                    template = middle_templates[template_idx]
                    page = {
                        "page": i + 1,
                        "title": template["title"],
                        "content": template["content"],
                        "content_type": template.get("content_type", "step"),
                        "visual_concept": f"단계 {i}를 상징하는 진행 중인 이미지",
                        "layout": "center"
                    }
                pages.append(page)

            return pages

        # 목적별 전문 콘텐츠 템플릿 (AIDA/5W1H 구조 적용)
        if purpose == "promotion":
            # 홍보용 템플릿 - AIDA 구조 (Attention → Interest → Desire → Action)
            first_page = {
                "title": "지금 주목하세요",
                "subtitle": "당신이 찾던 바로 그것",
                "hook": "다른 곳에서 찾기 힘든 특별함",
                "visual_concept": "제품/서비스의 핵심 가치를 시각적으로 표현한 프리미엄 이미지"
            }
            middle_templates = [
                {"title": "왜 특별한가", "content": ["• 차별화된 핵심 가치", "• 전문가가 인정한 품질", "• 고객이 선택한 이유"]},
                {"title": "어떤 혜택이 있나", "content": ["• 시간/비용 절약", "• 품질 보장", "• 만족도 100%"]},
                {"title": "고객의 선택", "content": ["• 실제 사용자 후기", "• 재구매율 높은 이유", "• 추천하는 이유"]},
                {"title": "지금만 가능한 혜택", "content": ["• 한정 기간 특가", "• 추가 혜택 제공", "• 선착순 마감"]}
            ]
            last_page = {
                "title": "지금 시작하세요",
                "content": ["지금 선택하면 특별 혜택", "문의/구매 바로가기"],
                "cta": "기회를 잡으세요"
            }
        elif purpose == "event":
            # 이벤트용 템플릿 - 5W1H 구조
            first_page = {
                "title": "특별한 초대",
                "subtitle": "당신을 위한 이벤트",
                "hook": "참여하면 누구나 받는 혜택",
                "visual_concept": "이벤트의 핵심 가치와 혜택을 강조하는 역동적인 이미지"
            }
            middle_templates = [
                {"title": "무엇을 경험하나요", "content": ["• 이벤트 핵심 내용", "• 참여 시 얻는 가치", "• 특별한 경험"]},
                {"title": "언제, 어디서", "content": ["• 이벤트 기간", "• 참여 장소/방법", "• 마감 일정"]},
                {"title": "누가 참여할 수 있나요", "content": ["• 참여 대상", "• 참여 조건", "• 특별 우대"]},
                {"title": "어떤 혜택이 있나요", "content": ["• 참여자 전원 혜택", "• 추첨 경품", "• 특별 보너스"]}
            ]
            last_page = {
                "title": "지금 참여하세요",
                "content": ["참여 방법 안내", "마감 전 서두르세요"],
                "cta": "참여하기"
            }
        elif purpose == "menu":
            # 메뉴용 템플릿 - 감각적 묘사와 스토리텔링
            first_page = {
                "title": "오늘의 추천",
                "subtitle": "정성을 담은 특별한 맛",
                "hook": "셰프가 자신있게 추천하는 메뉴",
                "visual_concept": "메뉴의 풍미와 품격을 느낄 수 있는 고급스러운 음식 이미지"
            }
            middle_templates = [
                {"title": "이 메뉴의 이야기", "content": ["• 탄생 비화", "• 셰프의 철학", "• 특별한 의미"]},
                {"title": "엄선된 재료", "content": ["• 신선함의 비결", "• 산지 직송 재료", "• 프리미엄 품질"]},
                {"title": "맛의 특징", "content": ["• 풍미와 식감", "• 조리법의 비밀", "• 추천 페어링"]},
                {"title": "가격 안내", "content": ["• 합리적인 가격", "• 세트 구성 혜택", "• 주문 옵션"]}
            ]
            last_page = {
                "title": "주문 안내",
                "content": ["예약/주문 방법", "오늘의 혜택"],
                "cta": "맛있는 경험을 시작하세요"
            }
        else:
            # 정보용 템플릿 - 가치 중심 정보 전달
            first_page = {
                "title": "알아두면 좋은 정보",
                "subtitle": "핵심만 쏙쏙 정리했어요",
                "hook": "이것만 알면 충분해요",
                "visual_concept": "정보의 가치와 신뢰감을 전달하는 깔끔한 이미지"
            }
            middle_templates = [
                {"title": "핵심 포인트", "content": ["• 가장 중요한 내용", "• 꼭 알아야 할 것", "• 핵심 요약"]},
                {"title": "왜 중요한가요", "content": ["• 이 정보가 필요한 이유", "• 알면 얻는 이점", "• 실생활 적용"]},
                {"title": "실전 활용법", "content": ["• 바로 적용하는 방법", "• 실용적인 팁", "• 주의사항"]},
                {"title": "더 알아보기", "content": ["• 추가 정보", "• 참고 자료", "• 관련 링크"]}
            ]
            last_page = {
                "title": "요약 정리",
                "content": ["핵심 내용 한눈에", "더 궁금하면 문의하세요"],
                "cta": "도움이 되셨나요?"
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
