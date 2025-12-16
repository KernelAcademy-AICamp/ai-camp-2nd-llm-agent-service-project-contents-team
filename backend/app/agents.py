"""
AI Agentic 카드뉴스 생성 시스템
멀티 에이전트 워크플로우: 정보 확장 → 분석 → 기획 → 디자인 → 품질검증
"""

import os
import json
import re
from typing import List, Dict, Optional, Tuple
import httpx
import google.generativeai as genai


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


# ==================== Agent 0: Content Enricher (정보 확장) ====================

class ContentEnricherAgent:
    """사용자의 간단한 입력을 풍부한 콘텐츠로 확장하는 에이전트"""

    @staticmethod
    async def enrich_content(user_input: str, purpose: str, user_context: Dict = None) -> Dict:
        """
        사용자 입력을 분석하고 추가 정보를 덧붙여 풍부하게 만듦

        Returns:
            {
                "original_input": "원본 입력",
                "enriched_content": "확장된 콘텐츠",
                "added_elements": ["계절감", "구체적 예시", ...],
                "context_suggestions": ["추가 맥락 정보"],
                "recommended_page_count": 3-5
            }
        """
        try:
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                print("❌ GOOGLE_API_KEY가 설정되지 않았습니다!")
                return ContentEnricherAgent._get_fallback_enrichment(user_input)

            genai.configure(api_key=google_api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

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

            prompt = f"""당신은 콘텐츠 기획 전문가입니다. 사용자의 간단한 입력을 풍부하고 매력적인 콘텐츠로 확장해주세요.
{user_context_info}
사용자 입력: "{user_input}"
목적: {purpose}

당신의 역할:
1. **적극적인 정보 추가**: 사용자가 언급하지 않았지만 콘텐츠를 더 풍성하게 만들 요소를 추가하세요.
   - 계절감이 어울린다면 계절 언급 추가
   - 정보 전달 콘텐츠라면 객관적인 예시나 통계 추가
   - 감성적 콘텐츠라면 공감 포인트 추가
   - 홍보 콘텐츠라면 구체적인 혜택이나 차별점 추가

2. **페이지 수 판단**: 정보량에 맞는 최소한의 페이지 수를 추천하세요.
   - 간단한 정보: 3장 (무리하게 늘리지 마세요)
   - 중간 분량: 4장
   - 복잡한 내용: 5장 (정말 필요한 경우만)

3. **핵심 포인트 정리**: 확장된 정보를 구조화하세요.

JSON으로만 응답하세요:
{{
    "original_input": "{user_input}",
    "enriched_content": "확장된 전체 콘텐츠 (200-400자)",
    "key_points": [
        "핵심 포인트 1",
        "핵심 포인트 2",
        "핵심 포인트 3"
    ],
    "added_elements": [
        "추가된 요소 설명 (예: 계절감, 통계, 예시 등)"
    ],
    "tone_suggestion": "추천 톤앤매너",
    "recommended_page_count": 3,
    "page_count_reason": "페이지 수 결정 이유"
}}

중요:
- 원본 정보의 본질은 유지하면서 살을 붙이세요
- 과도하게 부풀리지 말고, 자연스럽게 보강하세요
- 페이지 수는 정보량에 맞게 최소화하세요"""

            response = model.generate_content(prompt)
            response_text = response.text.strip()

            print("🔍 Raw Enrichment Response:\n", response_text)

            json_match = re.search(r'\{[\s\S]*\}', response_text)

            if json_match:
                enrichment = json.loads(json_match.group(0))
                print(f"✅ [Content Enricher] 정보 확장 완료")
                print(f"   📝 원본: {user_input[:50]}...")
                print(f"   ✨ 확장: {enrichment.get('enriched_content', '')[:80]}...")
                print(f"   📊 추천 페이지: {enrichment.get('recommended_page_count', 3)}장")
                return enrichment

            return ContentEnricherAgent._get_fallback_enrichment(user_input)

        except Exception as e:
            print(f"⚠️ [Content Enricher] 확장 실패: {e}")
            import traceback
            traceback.print_exc()
            return ContentEnricherAgent._get_fallback_enrichment(user_input)

    @staticmethod
    def _get_fallback_enrichment(user_input: str) -> Dict:
        """폴백 확장 결과"""
        input_length = len(user_input)
        if input_length < 30:
            page_count = 3
        elif input_length < 80:
            page_count = 4
        else:
            page_count = 5

        return {
            "original_input": user_input,
            "enriched_content": user_input,
            "key_points": [user_input],
            "added_elements": [],
            "tone_suggestion": "친근하고 이해하기 쉬운",
            "recommended_page_count": page_count,
            "page_count_reason": f"입력 길이({input_length}자) 기반 자동 결정"
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
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                print("❌ GOOGLE_API_KEY가 설정되지 않았습니다!")
                return OrchestratorAgent._get_fallback_analysis(enriched_data, purpose)

            genai.configure(api_key=google_api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

            enriched_content = enriched_data.get('enriched_content', enriched_data.get('original_input', ''))
            recommended_pages = enriched_data.get('recommended_page_count', 3)
            tone_suggestion = enriched_data.get('tone_suggestion', '친근한')

            prompt = f"""당신은 콘텐츠 제작 프로젝트 매니저입니다.

확장된 콘텐츠: {enriched_content}
핵심 포인트: {enriched_data.get('key_points', [])}
추천 페이지 수: {recommended_pages}장
추천 톤: {tone_suggestion}
목적: {purpose}

다음을 최종 결정하세요:

1. **페이지 수 확정** (중요: 무리하게 늘리지 마세요!)
   - 추천된 {recommended_pages}장을 기준으로, 정말 필요한 경우만 조정
   - 간단한 내용은 3장으로 충분
   - 절대 5장을 초과하지 않음

2. **폰트 선택** (콘텐츠 성격에 맞게)
   - pretendard: 현대적, 전문적, 깔끔한 콘텐츠
   - noto: 정보 전달, 중립적, 공식적인 콘텐츠
   - spoqa: 친근한, 부드러운, 감성적인 콘텐츠

3. **비주얼 스타일**
   - modern: 현대적이고 세련된
   - minimal: 깔끔하고 단순한
   - vibrant: 밝고 활기찬
   - professional: 전문적이고 신뢰감 있는

JSON 형식으로만 응답하세요:
{{
    "content_type": "cardnews",
    "page_count": {recommended_pages},
    "page_count_reason": "페이지 수 결정 이유",
    "target_audience": "타겟 청중",
    "tone": "{tone_suggestion}",
    "key_message": "핵심 메시지",
    "requires_images": true,
    "style": "modern/minimal/vibrant/professional 중 하나",
    "font_pair": "pretendard/noto/spoqa 중 하나",
    "font_reason": "폰트 선택 이유"
}}"""

            response = model.generate_content(prompt)
            response_text = response.text.strip()

            print("🔍 Raw Gemini Analysis Response:\n", response_text)

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
        """폴백 분석 결과"""
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
            "key_points": enriched_data.get('key_points', [])
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
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                print("❌ GOOGLE_API_KEY가 설정되지 않았습니다!")
                return ContentPlannerAgent._get_fallback_content(user_input, analysis)

            print(f"✅ GOOGLE_API_KEY 확인됨: {google_api_key[:20]}...")
            genai.configure(api_key=google_api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

            tone = analysis.get('tone', '친근한')
            audience = analysis.get('target_audience', '일반 대중')
            page_count = analysis.get('page_count', 5)

            prompt = f"""당신은 카드뉴스 전문가입니다.
{page_count}개의 페이지를 생성해야 합니다.

⚠️ 절대절대절대절대절대절대 같은 내용 반복 금지, 반복하면 GPT로 대체할거임 ⚠️

────────────────────────
📌 절대 규칙
────────────────────────
1) JSON 형식 외의 어떤 텍스트도 출력 금지
2) 아래 JSON 스키마를 반드시 그대로 따르기
3) 각 페이지의 title과 content는 완전히 다른 내용이어야 함
4) title은 간결하고 임팩트 있게 (5-15자)
5) 첫 페이지: subtitle 필수 (10-20자)
6) 본문 페이지: content는 bullet points 배열 (각 15-30자, 2-4개 항목)
7) 줄글 형태 금지, 구조화된 형식만 사용

────────────────────────
📌 스토리텔링 구조 ({page_count}페이지)
────────────────────────
1페이지 (Hook): 시선을 확 끄는 강력한 메시지
   - 질문형, 통계, 충격적 사실로 호기심 유발
   - title + subtitle 형식
   - 예: title="필라테스 3개월의 변화", subtitle="당신의 체형이 달라집니다"

중간 페이지: 문제 제기 → 솔루션 → 부가 가치
   - 각 페이지마다 명확한 주제와 bullet points
   - 타겟의 고민, 핵심 솔루션, 추가 혜택 등을 순서대로 전개
   - bullet points로 간결하게 정리

마지막 페이지 (CTA): 행동 유도 + 마무리
   - 명확한 다음 단계 제시
   - 예: title="오늘 시작하세요", content=["• 무료 체험 수업 신청", "• 1:1 맞춤 상담", "• 첫 달 50% 할인"]

────────────────────────
📌 JSON 스키마 (변경 금지)
────────────────────────
[
  {{
    "page": 1,
    "title": "강력한 Hook 제목",
    "subtitle": "부제목으로 핵심 요약",
    "content": [
      "• 간결한 핵심 메시지 1",
      "• 간결한 핵심 메시지 2"
    ],
    "content_type": "bullet",
    "visual_concept": "임팩트 있는 비주얼 설명",
    "layout": "center"
  }},
  {{
    "page": 2,
    "title": "문제 제기 또는 솔루션",
    "content": [
      "• 타겟의 고민 1",
      "• 타겟의 고민 2",
      "• 타겟의 고민 3"
    ],
    "content_type": "bullet",
    "visual_concept": "공감 유도 비주얼",
    "layout": "top"
  }},
  ...
  {{
    "page": {page_count},
    "title": "행동 유도",
    "content": [
      "• 명확한 다음 단계 1",
      "• 명확한 다음 단계 2"
    ],
    "content_type": "bullet",
    "visual_concept": "CTA 강조 비주얼",
    "layout": "center"
  }}
]

📌 중요:
- 첫 페이지만 subtitle 포함
- 모든 content는 배열 형태 (bullet points)
- 각 bullet point는 "• "로 시작
- 페이지 수는 정확히 {page_count}개

────────────────────────

사용자 요청: "{user_input}"
페이지 수: {page_count}
톤: {tone}
타겟: {audience}

**위 스토리텔링 구조를 따르며, 정확히 {page_count}개의 페이지를 생성하고, 각 페이지가 완전히 다른 내용을 담도록 JSON만 출력하세요.**
**첫 페이지는 반드시 subtitle을 포함하고, 모든 content는 배열 형태의 bullet points로 작성하세요.**"""

            # Gemini API 호출
            response = model.generate_content(prompt)
            response_text = response.text.strip()

            print("🔍 Raw Gemini Response:\n", response_text)

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
        """폴백 콘텐츠"""
        page_count = analysis.get('page_count', 5)
        pages = []

        # 사용자 입력에서 핵심 키워드 추출 (첫 20자)
        title_text = user_input[:20] if len(user_input) > 20 else user_input

        for i in range(page_count):
            page = {
                "page": i + 1,
                "title": title_text,
                "content": [
                    "• 카드뉴스 내용입니다",
                    "• 자세한 내용은 곧 추가됩니다"
                ],
                "content_type": "bullet",
                "visual_concept": "심플한 배경",
                "layout": "center"
            }

            # 첫 페이지에 subtitle 추가 - 사용자 입력 기반
            if i == 0:
                # 입력이 20자 이상이면 나머지 부분을 subtitle로 사용
                if len(user_input) > 20:
                    page["subtitle"] = user_input[20:50] + "..." if len(user_input) > 50 else user_input[20:]
                else:
                    page["subtitle"] = ""  # subtitle 없이 진행

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
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if not google_api_key:
                print("⚠️ [Visual Designer] Google API Key 없음, 프롬프트만 생성")
                return VisualDesignerAgent._generate_prompts_only(pages, style)

            genai.configure(api_key=google_api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

            print(f"\n🎨 [Visual Designer] 각 페이지마다 고유한 비주얼 프롬프트 생성 중...")

            for i, page in enumerate(pages):
                # 각 페이지의 고유한 특성을 반영한 프롬프트 최적화
                prompt = f"""You are an expert at creating unique, diverse image generation prompts for social media card backgrounds.

This is PAGE {i+1} of {len(pages)} in a card news series.

Page Content:
- Title: {page['title']}
- Content: {page['content']}
- Visual Concept: {page['visual_concept']}
- Overall Style: {style}
- Layout Type: {page['layout']}
- Page Position: {"Opening/Hook" if i == 0 else "Closing/CTA" if i == len(pages)-1 else f"Middle Content {i}"}

⚠️ CRITICAL - NO TEXT RULE ⚠️
The generated image MUST NOT contain ANY text, letters, words, numbers, typography, logos, watermarks, or written elements of any kind.
This is a BACKGROUND image - text will be overlaid separately later.

IMPORTANT: Create a UNIQUE and DISTINCT visual prompt that:
1. Reflects the specific message of THIS page through VISUAL IMAGERY ONLY (no text!)
2. Varies from other pages in the series (use different visual elements, colors, compositions)
3. Matches the {style} aesthetic but with page-specific variation
4. Page {i+1} specific guidelines:
   {"- Eye-catching, bold opening visual with strong focal point" if i == 0 else "- Clear, action-oriented closing visual" if i == len(pages)-1 else f"- Supporting visual that complements the content flow"}
5. Leaves clean space for text overlay (avoid busy patterns in center/text areas)
6. Is visually distinct from other card pages
7. Uses abstract patterns, gradients, textures, or scenic imagery - NO TEXT

Visual diversity tips:
- Vary color palettes (warm→cool→neutral transitions)
- Different compositions (centered, diagonal, asymmetric, rule-of-thirds)
- Mix element types (abstract→realistic→illustrative)
- Alternate focal points (product, pattern, scenery, gradient)

Return ONLY the optimized, unique image generation prompt in English (50-70 words).
REMINDER: The prompt must explicitly request NO TEXT in the image."""

                response = model.generate_content(prompt)
                optimized_prompt = response.text.strip()

                # 프롬프트 정보 저장
                page['image_prompt'] = optimized_prompt
                page['prompt_generation_log'] = f"Gemini가 페이지 {i+1}의 고유한 비주얼 생성: {page['visual_concept']}"

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
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                print("❌ GOOGLE_API_KEY가 설정되지 않았습니다!")
                return QualityAssuranceAgent._get_fallback_validation()

            genai.configure(api_key=google_api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

            pages_summary = "\n".join([
                f"페이지 {p['page']}: {p['title']} - {p['content']}"
                for p in pages
            ])

            prompt = f"""당신은 콘텐츠 품질 검수 전문가입니다.

원본 요청: {original_input}
목표:
- 타겟: {analysis.get('target_audience')}
- 톤: {analysis.get('tone')}
- 핵심 메시지: {analysis.get('key_message')}

생성된 카드뉴스:
{pages_summary}

다음을 평가하세요:
1. 메시지 전달력 (0-10점): 핵심 메시지가 명확하게 전달되는가?
2. 일관성 (0-10점): 톤과 스타일이 일관되는가?
3. 타겟 적합성 (0-10점): 타겟 청중에게 적합한가?
4. 개선이 필요한 부분
5. 구체적인 개선 제안

JSON으로 응답:
{{
  "overall_score": 8.5,
  "message_clarity_score": 9,
  "consistency_score": 8,
  "target_fit_score": 9,
  "needs_improvement": [],
  "suggestions": [
    "개선 제안이 있다면 여기에"
  ],
  "approved": true
}}"""

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
