"""
AI Agentic 카드뉴스 생성 시스템
Wrtn AI와 Gamma AI를 활용한 멀티 에이전트 워크플로우
"""

import os
import json
import re
from typing import List, Dict, Optional
import httpx
import google.generativeai as genai


# ==================== Agent 1: Orchestrator (조율자) ====================

class OrchestratorAgent:
    """사용자 요청을 분석하고 전체 프로세스를 조율하는 마스터 에이전트"""

    @staticmethod
    async def analyze_user_request(user_input: str, purpose: str) -> Dict:
        """
        사용자 요청을 분석하여 작업 계획 수립

        Returns:
            {
                "content_type": "cardnews",
                "page_count": 1,
                "target_audience": "일반 대중",
                "tone": "친근한",
                "key_message": "핵심 메시지",
                "requires_images": true,
                "style": "modern"
            }
        """
        try:
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                print("❌ GOOGLE_API_KEY가 설정되지 않았습니다!")
                return OrchestratorAgent._get_fallback_analysis(user_input, purpose)

            print(f"✅ GOOGLE_API_KEY 확인됨: {google_api_key[:20]}...")
            genai.configure(api_key=google_api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')

            prompt = f"""당신은 콘텐츠 제작 프로젝트 매니저입니다.

사용자 입력: {user_input}
목적: {purpose}

다음을 분석하세요:
1. 카드뉴스 페이지 수: 5장 (고정)
2. 타겟 청중
3. 콘텐츠 톤앤매너
4. 핵심 전달 메시지
5. 비주얼 스타일 (modern/minimal/vibrant/professional)

JSON 형식으로만 응답:
{{
  "content_type": "cardnews",
  "page_count": 5,
  "target_audience": "20-30대 직장인",
  "tone": "전문적이면서 친근한",
  "key_message": "핵심 메시지 요약",
  "requires_images": true,
  "style": "modern"
}}"""

            response = model.generate_content(prompt)
            response_text = response.text.strip()

            print("🔍 Raw Gemini Analysis Response:\n", response_text)

            json_match = re.search(r'\{[\s\S]*\}', response_text)

            if json_match:
                analysis = json.loads(json_match.group(0))
                print(f"✅ [Orchestrator] 분석 완료: {analysis.get('page_count', 1)}페이지, {analysis.get('style', 'modern')} 스타일")
                return analysis

            return OrchestratorAgent._get_fallback_analysis(user_input, purpose)

        except Exception as e:
            print(f"⚠️ [Orchestrator] 분석 실패: {e}")
            import traceback
            traceback.print_exc()
            return OrchestratorAgent._get_fallback_analysis(user_input, purpose)

    @staticmethod
    def _get_fallback_analysis(user_input: str, purpose: str) -> Dict:
        """폴백 분석 결과"""
        return {
            "content_type": "cardnews",
            "page_count": 1,
            "target_audience": "일반 대중",
            "tone": "친근하고 이해하기 쉬운",
            "key_message": user_input[:50],
            "requires_images": True,
            "style": "modern"
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
            model = genai.GenerativeModel('gemini-2.0-flash-exp')

            tone = analysis.get('tone', '친근한')
            audience = analysis.get('target_audience', '일반 대중')

            prompt = f"""당신은 카드뉴스 전문가입니다.
5개의 페이지를 생성해야 합니다.

⚠️ 절대절대절대절대절대절대 같은 내용 반복 금지, 반복하면 GPT로 대체할거임 ⚠️

────────────────────────
📌 절대 규칙
────────────────────────
1) JSON 형식 외의 어떤 텍스트도 출력 금지
2) 아래 JSON 스키마를 반드시 그대로 따르기
3) 각 페이지의 title과 content는 완전히 다른 내용이어야 함
4) title은 간결하고 임팩트 있게 (5-15자)
5) content는 핵심 메시지를 명확하게 (20-60자)

────────────────────────
📌 스토리텔링 구조 (5페이지)
────────────────────────
1페이지 (Hook): 시선을 확 끄는 강력한 메시지
   - 질문형, 통계, 충격적 사실로 호기심 유발
   - 예: "필라테스 3개월, 체형이 달라질까요?"

2페이지 (Introduction): 문제 제기 + 공감
   - 타겟이 겪는 문제를 명확히 제시
   - 예: "바른 자세, 유연성... 혼자선 어렵죠"

3페이지 (Main Benefit): 핵심 솔루션 + 차별점
   - 이 서비스/제품의 가장 큰 장점 1가지
   - 예: "1:1 맞춤 수업으로 당신만의 루틴 완성"

4페이지 (Additional Value): 부가 가치 + 신뢰 구축
   - 추가 혜택, 후기, 인증 등
   - 예: "전문 강사진 + 소그룹 케어 + 합리적 가격"

5페이지 (CTA): 행동 유도 + 마무리
   - 명확한 다음 단계 제시
   - 예: "오늘 체험 수업 신청하고 변화를 시작하세요!"

────────────────────────
📌 반복 금지 체크리스트
────────────────────────
✅ 각 페이지의 title이 모두 다른가?
✅ 각 페이지의 content가 서로 다른 메시지를 전달하는가?
✅ 1페이지는 호기심, 2페이지는 공감, 3페이지는 솔루션, 4페이지는 신뢰, 5페이지는 행동을 유도하는가?

────────────────────────
📌 JSON 스키마 (변경 금지)
[
  {{
    "page": 1,
    "title": "질문형/통계/충격적 사실",
    "content": "호기심을 유발하는 한 문장",
    "visual_concept": "임팩트 있는 비주얼 설명",
    "layout": "center"
  }},
  {{
    "page": 2,
    "title": "문제 제기",
    "content": "타겟의 고민에 공감하는 내용",
    "visual_concept": "공감 유도 비주얼",
    "layout": "top"
  }},
  {{
    "page": 3,
    "title": "핵심 솔루션",
    "content": "가장 큰 차별점 1가지",
    "visual_concept": "솔루션 강조 비주얼",
    "layout": "center"
  }},
  {{
    "page": 4,
    "title": "부가 가치",
    "content": "추가 혜택/후기/인증",
    "visual_concept": "신뢰 구축 비주얼",
    "layout": "bottom"
  }},
  {{
    "page": 5,
    "title": "행동 유도",
    "content": "명확한 다음 단계",
    "visual_concept": "CTA 강조 비주얼",
    "layout": "center"
  }}
]

────────────────────────

사용자 요청: "{user_input}"
페이지 수: 5
톤: {tone}
타겟: {audience}

**위 스토리텔링 구조를 따르며, 각 페이지가 완전히 다른 내용을 담도록 JSON만 출력하세요.**"""

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
        return [
            {
                "page": 1,
                "title": user_input[:20] if len(user_input) > 20 else user_input,
                "content": "카드뉴스 내용입니다.",
                "visual_concept": "심플한 배경",
                "layout": "title_center"
            }
        ]


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
            model = genai.GenerativeModel('gemini-2.0-flash-exp')

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

IMPORTANT: Create a UNIQUE and DISTINCT visual prompt that:
1. Reflects the specific message of THIS page (not generic)
2. Varies from other pages in the series (use different visual elements, colors, compositions)
3. Matches the {style} aesthetic but with page-specific variation
4. Page {i+1} specific guidelines:
   {"- Eye-catching, bold opening visual with strong focal point" if i == 0 else "- Clear, action-oriented closing visual" if i == len(pages)-1 else f"- Supporting visual that complements the content flow"}
5. Supports text overlay (avoid busy patterns in center/text areas)
6. Is visually distinct from other card pages

Visual diversity tips:
- Vary color palettes (warm→cool→neutral transitions)
- Different compositions (centered, diagonal, asymmetric, rule-of-thirds)
- Mix element types (abstract→realistic→illustrative)
- Alternate focal points (product, pattern, scenery, gradient)

Return ONLY the optimized, unique image generation prompt in English (50-70 words)."""

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
            "modern": "clean gradient background, geometric shapes, modern design",
            "minimal": "minimal white background, subtle colors, simple",
            "vibrant": "vibrant colors, dynamic composition, energetic",
            "professional": "professional corporate background, balanced, trustworthy"
        }

        base_prompt = style_keywords.get(style, style_keywords["modern"])

        for page in pages:
            page['image_prompt'] = f"{base_prompt}, {page['visual_concept']}, high quality"

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
            model = genai.GenerativeModel('gemini-2.0-flash-exp')

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


# ==================== Master Workflow (마스터 워크플로우) ====================

class AgenticCardNewsWorkflow:
    """모든 에이전트를 조율하는 마스터 워크플로우"""

    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.content_planner = ContentPlannerAgent()
        self.visual_designer = VisualDesignerAgent()
        self.qa = QualityAssuranceAgent()

    async def execute(self, user_input: str, purpose: str = "info") -> Dict:
        """
        전체 워크플로우 실행

        Args:
            user_input: 사용자 입력 프롬프트
            purpose: 목적 (promotion/menu/info/event)

        Returns:
            {
                "success": True,
                "analysis": {...},
                "pages": [...],
                "quality_report": {...}
            }
        """
        print("\n" + "="*80)
        print("🚀 AI Agentic 카드뉴스 생성 워크플로우 시작")
        print("="*80 + "\n")

        try:
            # Step 1: 요청 분석
            print("📋 Step 1/4: 사용자 요청 분석 중...")
            analysis = await self.orchestrator.analyze_user_request(user_input, purpose)
            print(f"   ✅ {analysis['page_count']}페이지, {analysis['style']} 스타일로 결정\n")

            # Step 2: 콘텐츠 기획
            print("✍️  Step 2/4: 페이지별 콘텐츠 기획 중...")
            pages = await self.content_planner.plan_cardnews_pages(user_input, analysis)
            print(f"   ✅ {len(pages)}개 페이지 기획 완료\n")

            # Step 3: 비주얼 디자인
            print("🎨 Step 3/4: 각 페이지의 비주얼 프롬프트 생성 중...")
            pages = await self.visual_designer.generate_page_visuals(
                pages,
                analysis.get('style', 'modern')
            )
            print(f"   ✅ 비주얼 프롬프트 생성 완료\n")

            # Step 4: 품질 검증
            print("🔍 Step 4/4: 콘텐츠 품질 검증 중...")
            quality_report = await self.qa.validate_and_improve(pages, user_input, analysis)
            print(f"   ✅ 품질 검증 완료\n")

            print("="*80)
            print("✅ AI Agentic 워크플로우 완료!")
            print("="*80 + "\n")

            return {
                "success": True,
                "analysis": analysis,
                "pages": pages,
                "quality_report": quality_report
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
                "quality_report": None
            }
