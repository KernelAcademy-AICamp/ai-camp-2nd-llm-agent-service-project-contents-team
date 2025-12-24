"""
AI 비디오 생성 서비스
- Master Planning Agent: 4단계 Context Engineering 파이프라인으로 스토리보드 생성
  1. ProductAnalysisAgent: 제품 이미지 분석
  2. StoryPlanningAgent: 스토리 구조 선택
  3. SceneDirectorAgent: 장면별 연출 설계
  4. QualityValidatorAgent: 품질 검증 및 자동 수정
- Image Generation: Gemini 2.5 Flash Image (일반) / Gemini 3 Pro Image (텍스트 특화)
- Video Generation: Kling 2.1 Standard (via fal.ai) - Image-to-Video 트랜지션 생성
- Video Composition: moviepy로 최종 비디오 합성 (빠른 컷 전환)
"""
import os
import json
import base64
import httpx
import asyncio
import random
from typing import List, Dict, Any, Optional
from pathlib import Path
import anthropic
import google.generativeai as genai
import vertexai
from vertexai.generative_models import GenerativeModel as VertexGenerativeModel, Part
from sqlalchemy.orm import Session
import fal_client

from ..models import VideoGenerationJob, User, BrandAnalysis
from ..logger import get_logger

logger = get_logger(__name__)

# Google Gemini 설정 (기존 코드와의 호환성 유지)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Vertex AI 지역 설정 (멀티 리전 로테이션으로 쿼터 분산)
# 미국과 유럽 지역만 사용
AVAILABLE_REGIONS = [
    "europe-west4",      # 네덜란드
    "us-west1",          # 오레곤
    "us-east4"           # 버지니아
]

# 선택된 지역을 저장할 전역 변수
SELECTED_LOCATION = None

# Vertex AI 초기화 (GOOGLE_APPLICATION_CREDENTIALS 사용)
try:
    # 환경변수가 설정되어 있고 사용 가능한 지역이면 사용, 아니면 랜덤 선택
    location = os.getenv("GOOGLE_CLOUD_LOCATION")
    if not location or location not in AVAILABLE_REGIONS:
        location = random.choice(AVAILABLE_REGIONS)
        logger.info(f"🌍 Random region selected for quota distribution: {location}")

    SELECTED_LOCATION = location  # 전역 변수에 저장

    vertexai.init(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=location
    )
    logger.info(f"Vertex AI initialized: project={os.getenv('GOOGLE_CLOUD_PROJECT')}, location={location}")
except Exception as e:
    logger.warning(f"Failed to initialize Vertex AI: {e}")


class MasterPlanningAgent:
    """
    Master Planning Agent
    - 4단계 Context Engineering 파이프라인으로 스토리보드 생성
    - 1단계: 제품 이미지 분석 (ProductAnalysisAgent)
    - 2단계: 스토리 구조 선택 (StoryPlanningAgent)
    - 3단계: 장면별 연출 설계 (SceneDirectorAgent)
    - 4단계: 품질 검증 및 자동 수정 (QualityValidatorAgent)
    """

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        # 새로운 4단계 파이프라인 오케스트레이터
        from ..video_agents import VideoStoryboardOrchestrator
        self.orchestrator = VideoStoryboardOrchestrator()

    async def analyze_and_plan(
        self,
        job: VideoGenerationJob,
        user: User,
        brand_analysis: Optional[BrandAnalysis],
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        4단계 Context Engineering 파이프라인으로 스토리보드 생성

        Args:
            job: VideoGenerationJob 인스턴스
            user: User 인스턴스
            brand_analysis: BrandAnalysis 인스턴스 (있는 경우)
            db: Database session

        Returns:
            List[Dict]: 스토리보드 컷 리스트
            [
                {
                    "cut": 1,
                    "scene_description": "...",
                    "image_prompt": "...",
                    "duration": 4.0
                },
                ...
            ]
        """
        try:
            logger.info(f"Starting Master Planning Agent (4-Stage Pipeline) for job {job.id}")

            # 4단계 파이프라인 실행
            storyboard_result = await self.orchestrator.generate_storyboard(
                job=job,
                user=user,
                brand_analysis=brand_analysis,
                db=db
            )

            # 새 구조: {shared_visual_context: {...}, storyboard: [...]}
            # DB에 전체 구조 저장 (shared_visual_context 포함)
            job.storyboard = storyboard_result
            db.commit()

            # storyboard 배열 추출 (하위 처리용)
            storyboard = storyboard_result.get("storyboard", storyboard_result if isinstance(storyboard_result, list) else [])
            shared_context = storyboard_result.get("shared_visual_context", {})

            logger.info(f"Storyboard generated for job {job.id}: {len([s for s in storyboard if 'cut' in s])} cuts")
            if shared_context:
                logger.info(f"Shared visual context: {shared_context.get('primary_setting', 'N/A')}")

            return storyboard_result

        except Exception as e:
            logger.error(f"Error in Master Planning Agent for job {job.id}: {str(e)}")
            job.status = "failed"
            job.error_message = f"Planning failed: {str(e)}"
            db.commit()
            raise

    async def analyze_uploaded_image(self, image_data: Dict[str, str]) -> Dict[str, Any]:
        """
        업로드된 제품 이미지의 비주얼 특징 분석

        Args:
            image_data: base64 인코딩된 이미지 데이터

        Returns:
            Dict: 제품의 비주얼 특징
            {
                "colors": ["white", "gold", "minimalist"],
                "style": "luxury premium aesthetic",
                "lighting": "soft natural lighting",
                "composition": "centered, minimalist",
                "key_elements": "golden cap, white bottle, marble background",
                "mood": "elegant, sophisticated"
            }
        """
        try:
            logger.info("Analyzing uploaded product image for visual features...")

            # Vertex AI Gemini 모델 초기화
            gemini_model = VertexGenerativeModel("gemini-2.5-flash")

            # image_data를 PIL Image로 변환 후 Vertex AI Part 객체로 변환
            from PIL import Image
            import io

            image_bytes = base64.b64decode(image_data["data"])
            pil_image = Image.open(io.BytesIO(image_bytes))

            # PIL Image → Vertex AI Part 객체 변환
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()

            image_part = Part.from_data(
                data=img_bytes,
                mime_type="image/jpeg"
            )

            # 이미지 분석 프롬프트
            analysis_prompt = """이 제품 이미지를 분석하여 비주얼 특징을 추출해주세요.

다음 형식의 JSON으로 반환하세요:
{
  "colors": ["주요 색상 1", "주요 색상 2", "주요 색상 3"],
  "style": "전체적인 스타일 (예: luxury premium, casual modern, minimalist, vintage 등)",
  "lighting": "조명 스타일 (예: soft natural lighting, dramatic studio lighting, bright daylight 등)",
  "composition": "구도 및 레이아웃 (예: centered, off-center, close-up, full view 등)",
  "key_elements": "주요 시각적 요소들 (예: golden cap, white bottle, marble background)",
  "mood": "전체적인 분위기 (예: elegant sophisticated, playful fun, professional clean 등)",
  "background": "배경 스타일 (예: marble texture, plain white, wooden surface 등)"
}

제품의 핵심 비주얼 정체성을 유지하기 위한 정보를 추출하는 것이 목적입니다.
다른 설명 없이 JSON만 반환해주세요."""

            # Vertex AI Gemini API 호출
            response = gemini_model.generate_content([analysis_prompt, image_part])

            # 응답 파싱
            response_text = response.text
            logger.info(f"Image analysis response: {response_text[:200]}...")

            # JSON 파싱
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            visual_features = json.loads(response_text)

            logger.info(f"✅ Image analysis completed: {visual_features}")
            return visual_features

        except Exception as e:
            logger.error(f"Failed to analyze uploaded image: {str(e)}")
            # 분석 실패 시 기본값 반환
            return {
                "colors": ["natural"],
                "style": "professional",
                "lighting": "natural lighting",
                "composition": "centered",
                "key_elements": "product",
                "mood": "clean professional",
                "background": "neutral"
            }

    async def _download_and_encode_image(self, image_url: str) -> Dict[str, str]:
        """이미지 다운로드 (HTTP/HTTPS) 또는 로컬 파일 읽기 및 base64 인코딩"""

        if image_url.startswith(("http://", "https://")):
            # HTTP/HTTPS URL - 기존 방식으로 다운로드
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "image/jpeg")
                media_type = content_type.split("/")[-1]
                image_content = response.content
        else:
            # 로컬 파일 경로 - 파일 시스템에서 읽기
            import mimetypes

            # 상대 경로를 절대 경로로 변환 (프로젝트 루트 기준)
            # image_url이 "/uploads/..."로 시작하므로 앞의 "/" 제거
            file_path = Path(__file__).parent.parent.parent / image_url.lstrip("/")

            logger.info(f"Reading image from local filesystem: {file_path}")

            if not file_path.exists():
                raise FileNotFoundError(f"Image file not found: {file_path}")

            # 파일 읽기
            image_content = file_path.read_bytes()

            # MIME 타입 추측
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type and mime_type.startswith("image/"):
                media_type = mime_type.split("/")[-1]
            else:
                # 확장자로 추측
                extension = file_path.suffix.lstrip(".")
                media_type = extension if extension else "jpeg"

            logger.info(f"Image loaded from filesystem: {len(image_content)} bytes, type: image/{media_type}")

        # base64 인코딩
        image_base64 = base64.b64encode(image_content).decode("utf-8")

        return {
            "type": "base64",
            "media_type": f"image/{media_type}",
            "data": image_base64
        }

    def _validate_visual_consistency(
        self,
        storyboard: List[Dict[str, Any]],
        visual_features: Dict[str, Any]
    ) -> None:
        """
        생성된 스토리보드의 비주얼 일관성 검증

        Args:
            storyboard: 생성된 스토리보드
            visual_features: 추출된 비주얼 특징

        Raises:
            경고 로그만 출력 (실패하지 않음)
        """
        try:
            logger.info("Validating visual consistency of generated storyboard...")

            # 컷만 필터링
            cuts = [item for item in storyboard if 'cut' in item]

            # AI가 생성할 컷들만 검증 (use_uploaded_image가 False인 것들)
            ai_generated_cuts = [cut for cut in cuts if not cut.get('use_uploaded_image', False)]

            if not ai_generated_cuts:
                logger.info("No AI-generated cuts to validate (all cuts use uploaded image)")
                return

            # 비주얼 특징의 주요 키워드 추출
            keywords_to_check = []

            # 색상
            if visual_features.get("colors"):
                colors = visual_features["colors"] if isinstance(visual_features["colors"], list) else [visual_features["colors"]]
                keywords_to_check.extend([c.lower() for c in colors])

            # 스타일 키워드
            if visual_features.get("style"):
                style_keywords = visual_features["style"].lower().split()
                keywords_to_check.extend(style_keywords)

            # 조명 키워드
            if visual_features.get("lighting"):
                lighting_keywords = visual_features["lighting"].lower().split()
                keywords_to_check.extend(lighting_keywords)

            logger.info(f"Checking for visual consistency keywords: {keywords_to_check[:10]}...")

            # 각 AI 생성 컷 검증
            inconsistent_cuts = []
            for cut in ai_generated_cuts:
                cut_number = cut.get('cut', 'unknown')
                image_prompt = cut.get('image_prompt', '').lower()

                # 주요 키워드 중 일부라도 포함되어 있는지 확인
                found_keywords = [kw for kw in keywords_to_check if kw in image_prompt]

                if len(found_keywords) < max(1, len(keywords_to_check) // 3):
                    # 주요 키워드의 1/3 미만만 포함되어 있으면 경고
                    inconsistent_cuts.append({
                        'cut': cut_number,
                        'prompt': cut.get('image_prompt', '')[:100] + '...',
                        'found_keywords': found_keywords
                    })

            # 검증 결과 로그
            if inconsistent_cuts:
                logger.warning(f"⚠️  {len(inconsistent_cuts)}/{len(ai_generated_cuts)} cuts may lack visual consistency:")
                for item in inconsistent_cuts[:3]:  # 처음 3개만 출력
                    logger.warning(f"  - Cut {item['cut']}: found only {item['found_keywords']}")
                logger.warning(f"  Visual features may not be fully reflected in image prompts")
            else:
                logger.info(f"✅ Visual consistency validated: {len(ai_generated_cuts)} AI-generated cuts checked")

        except Exception as e:
            logger.warning(f"Failed to validate visual consistency: {str(e)}")
            # 검증 실패해도 계속 진행

    def _prepare_brand_context(
        self,
        user: User,
        brand_analysis: Optional[BrandAnalysis],
        visual_features: Optional[Dict[str, Any]] = None
    ) -> str:
        """브랜드 분석 데이터 및 제품 비주얼 특징을 컨텍스트로 준비 (brand_profile_json 우선 사용)"""
        context_parts = []

        # brand_profile_json 우선 사용
        if brand_analysis and brand_analysis.brand_profile_json:
            profile = brand_analysis.brand_profile_json

            # Identity
            identity = profile.get('identity', {})
            if identity.get('brand_name'):
                context_parts.append(f"브랜드명: {identity['brand_name']}")
            elif user.brand_name:
                context_parts.append(f"브랜드명: {user.brand_name}")

            if identity.get('business_type'):
                context_parts.append(f"업종: {identity['business_type']}")
            elif user.business_type:
                context_parts.append(f"업종: {user.business_type}")

            if user.business_description:
                context_parts.append(f"비즈니스 설명: {user.business_description}")

            if identity.get('brand_personality'):
                context_parts.append(f"브랜드 성격: {identity['brand_personality']}")
            if identity.get('target_audience'):
                context_parts.append(f"타겟 고객: {identity['target_audience']}")
            if identity.get('emotional_tone'):
                context_parts.append(f"감정적 톤: {identity['emotional_tone']}")
            if identity.get('brand_values'):
                values = ", ".join(identity['brand_values']) if isinstance(identity['brand_values'], list) else identity['brand_values']
                context_parts.append(f"브랜드 가치: {values}")

            # Tone of Voice (수치화된 정보 활용)
            tone = profile.get('tone_of_voice', {})
            if tone.get('formality') is not None:
                context_parts.append(f"격식도: {tone['formality']}/100 (0=매우 캐주얼, 100=매우 격식있는)")
            if tone.get('warmth') is not None:
                context_parts.append(f"따뜻함: {tone['warmth']}/100 (0=차가운, 100=매우 따뜻한)")
            if tone.get('enthusiasm') is not None:
                context_parts.append(f"열정도: {tone['enthusiasm']}/100 (0=차분한, 100=열정적인)")
            if tone.get('sentence_style'):
                context_parts.append(f"문장 스타일: {tone['sentence_style']}")
            if tone.get('signature_phrases'):
                phrases = ", ".join(tone['signature_phrases']) if isinstance(tone['signature_phrases'], list) else tone['signature_phrases']
                context_parts.append(f"시그니처 표현: {phrases}")

            # Content Strategy
            strategy = profile.get('content_strategy', {})
            if strategy.get('primary_topics'):
                topics = ", ".join(strategy['primary_topics']) if isinstance(strategy['primary_topics'], list) else strategy['primary_topics']
                context_parts.append(f"주요 주제: {topics}")
            if strategy.get('content_structure'):
                context_parts.append(f"콘텐츠 구조: {strategy['content_structure']}")
            if strategy.get('call_to_action_style'):
                context_parts.append(f"행동 유도 방식: {strategy['call_to_action_style']}")

            # Visual Style (영상/이미지 생성에 중요!)
            visual = profile.get('visual_style', {})
            if visual.get('color_palette'):
                colors = ", ".join(visual['color_palette']) if isinstance(visual['color_palette'], list) else visual['color_palette']
                context_parts.append(f"브랜드 컬러 팔레트: {colors}")
            if visual.get('image_style'):
                context_parts.append(f"이미지 스타일: {visual['image_style']}")
            if visual.get('composition_style'):
                context_parts.append(f"구도 스타일: {visual['composition_style']}")
            if visual.get('filter_preference'):
                context_parts.append(f"필터 선호도: {visual['filter_preference']}")

        else:
            # Fallback: User 테이블 및 개별 필드 사용
            if user.brand_name:
                context_parts.append(f"브랜드명: {user.brand_name}")
            if user.business_type:
                context_parts.append(f"업종: {user.business_type}")
            if user.business_description:
                context_parts.append(f"비즈니스 설명: {user.business_description}")

            # 브랜드 분석 정보 (개별 필드)
            if brand_analysis:
                if brand_analysis.brand_tone:
                    context_parts.append(f"브랜드 톤앤매너: {brand_analysis.brand_tone}")
                if brand_analysis.target_audience:
                    context_parts.append(f"타겟 고객: {brand_analysis.target_audience}")
                if brand_analysis.emotional_tone:
                    context_parts.append(f"감정적 톤: {brand_analysis.emotional_tone}")
                if brand_analysis.brand_values:
                    values = ", ".join(brand_analysis.brand_values) if isinstance(brand_analysis.brand_values, list) else brand_analysis.brand_values
                    context_parts.append(f"브랜드 가치: {values}")

        # 제품 비주얼 특징 (이미지 분석 결과)
        if visual_features:
            context_parts.append("\n[제품 비주얼 특징 - 모든 컷에서 일관되게 유지해야 함]")

            if visual_features.get("colors"):
                colors = ", ".join(visual_features["colors"]) if isinstance(visual_features["colors"], list) else visual_features["colors"]
                context_parts.append(f"주요 색상: {colors}")

            if visual_features.get("style"):
                context_parts.append(f"비주얼 스타일: {visual_features['style']}")

            if visual_features.get("lighting"):
                context_parts.append(f"조명 스타일: {visual_features['lighting']}")

            if visual_features.get("composition"):
                context_parts.append(f"구도: {visual_features['composition']}")

            if visual_features.get("key_elements"):
                context_parts.append(f"핵심 시각적 요소: {visual_features['key_elements']}")

            if visual_features.get("mood"):
                context_parts.append(f"분위기: {visual_features['mood']}")

            if visual_features.get("background"):
                context_parts.append(f"배경 스타일: {visual_features['background']}")

        if not context_parts:
            return "브랜드 정보가 제공되지 않았습니다. 제품 이미지와 설명만을 기반으로 스토리보드를 생성해주세요."

        return "\n".join(context_parts)

    async def _generate_storyboard(
        self,
        product_name: str,
        product_description: Optional[str],
        cut_count: int,
        duration_seconds: int,
        image_data: Dict[str, str],
        brand_context: str
    ) -> List[Dict[str, Any]]:
        """Claude를 사용하여 스토리보드 생성"""

        # 트랜지션 평균 길이 계산 (컷 수 - 1 = 트랜지션 수)
        num_transitions = cut_count - 1
        avg_transition_duration = duration_seconds / num_transitions if num_transitions > 0 else 5.0
        cut_duration = 0.3  # 컷 이미지는 짧게 고정

        # 프롬프트 구성
        system_prompt = f"""당신은 제품 마케팅 비디오의 스토리보드를 생성하는 전문가입니다.

주어진 제품 이미지와 정보를 분석하여, {cut_count}개의 컷으로 구성된 약 {duration_seconds}초 길이의 마케팅 비디오 스토리보드를 생성해주세요.

**⏱️ 타이밍 구조:**
- 각 컷 이미지: {cut_duration}초 (고정) - 키 프레임을 짧게 표시
- 트랜지션: 평균 {avg_transition_duration:.1f}초 - 실제 움직임과 전환이 일어나는 부분
- 총 길이: 약 {duration_seconds}초

**📖 스토리텔링 프레임워크 (필수 선택):**

제품과 브랜드 특성을 분석하여 다음 중 **가장 적합한 스토리 구조 1가지**를 선택하고 따르세요:

**1. Problem-Solution (문제-해결)**
- 적합한 제품: 기능성 제품, 생활용품, 건강식품, 에너지 드링크
- 구조: 문제 상황 제시 → 제품 등장 → 해결 과정 → 긍정적 결과
- 예시: 피곤한 아침 → 에너지 드링크 → 활기찬 하루

**2. Before-After (변화)**
- 적합한 제품: 화장품, 피트니스, 청소용품, 에너지 드링크
- 구조: 사용 전 상태 → 제품 사용 → 변화 과정 → 사용 후 결과
- 예시: 지친 피부 → 스킨케어 → 촉촉한 피부

**3. Process/Creation (제작 과정)**
- 적합한 제품: 수제 음식, 카페 음료, 디저트, 수제품, 아티즌 제품
- 구조: 재료/준비 → 제작 과정 (역동적 순간) → 완성품
- 특징: ASMR 요소, 시각적 만족감 (층 나뉘기, 색 변화, 질감)
- 예시: 딸기 + 우유 → 퐁당 섞이기 → 말차 폼 올리기 → 완성된 음료
- 키워드: "만들다", "붓다", "섞다", "craft", "handmade"

**4. Hero's Journey (제품의 여정)**
- 적합한 제품: 브랜드 스토리가 강한 제품, 프리미엄 제품
- 구조: 제품 소개 → 특별한 특징 → 제품이 만드는 임팩트
- 예시: 명품 시계 소개 → 정밀한 무브먼트 → 시간의 가치

**5. Emotional Arc (감정 곡선)**
- 적합한 제품: 럭셔리, 감성적 제품, 선물
- 구조: 감성적 Hook → 감정 연결 → 클라이맥스 → 만족스러운 결말
- 예시: 특별한 순간 → 선물 등장 → 감동의 순간

**6. Lifestyle/Moment (라이프스타일 순간)**
- 적합한 제품: 패션, 액세서리, 라이프스타일 제품
- 구조: 일상 속 순간 → 제품과 함께하는 모습 → 완성된 라이프스타일
- 예시: 카페에서 → 시계 착용 → 세련된 일상

**스토리 복잡도 가이드:**
- {cut_count}개 컷: {"간결하고 빠른 전개 (핵심 메시지만)" if cut_count <= 4 else "중간 깊이 전개 (감정 연결 + 제품 특징)" if cut_count <= 6 else "상세한 스토리 (깊은 감정적 여정)"}

**👥 캐릭터/모델 가이드라인 (사람 등장 시 필수):**

사람이 등장하는 컷에서는 브랜드 컨텍스트의 "타겟 고객" 정보를 반드시 확인하고:
- **국적**: 반드시 한국인 (Korean)으로 설정
- **성별**: 타겟 성별과 일치 (남성/여성/중성)
- **나이대**: 타겟 나이대와 일치 (예: 20대 초반, 30대, 40-50대 등)
- **외모 특징**: 한국인의 자연스러운 외모, 피부톤, 헤어스타일 포함

예시:
- 타겟이 "20-30대 여성" → image_prompt에 "Korean woman in her 20s-30s, natural Korean beauty" 포함
- 타겟이 "40대 남성" → image_prompt에 "Korean man in his 40s, professional appearance" 포함

**🎯 핵심 원칙: 비주얼 일관성 및 제품 정확성**

**모든 컷 이미지는 AI로 9:16 비율로 생성됩니다.**

업로드된 제품 이미지를 참고하여:
1. **제품의 정확한 외관**: 형태, 패키징, 디자인을 정확히 반영
2. **색상**: 제품의 정확한 색상, 색조, 그라데이션 유지
3. **디테일**: 로고, 라벨, 질감 등 세부 요소 재현
4. **비주얼 특징**: 조명, 스타일, 분위기를 일관되게 유지

브랜드 컨텍스트의 "제품 비주얼 특징"을 반드시 확인하고, 모든 컷의 image_prompt에 이를 반영하세요.

**중요: 비용 최적화를 고려하여 컷 정보와 전환 정보를 모두 포함해주세요.**

각 요소의 구조:

**컷 정보:**
1. cut: 컷 번호 (1부터 시작)
2. scene_description: 장면 설명 (한국어, 2-3문장)
3. image_prompt: 이미지 생성 AI 프롬프트 (영어, 상세하게)
4. duration: 컷 길이 (초, **고정 {cut_duration}초** - 키 프레임만 짧게 표시)
5. is_hero_shot: true/false
   - 첫 컷, 마지막 컷, 가장 중요한 핵심 컷은 true
   - 나머지는 false
6. resolution: "1080p" (hero shot) 또는 "720p" (일반)
7. needs_text: true/false (텍스트 렌더링 필요 여부)

   ⚠️ CRITICAL: needs_text는 매우 제한적으로만 true로 설정하세요.

   **needs_text: true인 경우 (매우 제한적):**
   - CTA 메시지가 화면에 표시되어야 하는 경우
     * 예: "50% 할인", "지금 구매", "NEW", "LIMITED"
   - 핵심 제품 정보가 텍스트로 명확히 표시되어야 하는 경우
     * 예: 영양 성분표의 "칼로리 0", 성분명 "비타민C 500mg"
   - 인포그래픽 스타일의 텍스트 설명
     * 예: "3단계 과정", "Before → After" 라벨

   **needs_text: false인 경우 (대부분, 기본값):**
   - 제품 패키지의 브랜드명/로고 (AI가 재현하므로 별도 텍스트 렌더링 불필요)
   - 배경의 간판, 메뉴판, 표지판 (읽을 필요 없는 배경 요소)
   - 흐릿하거나 장식적인 텍스트
   - 순수 비주얼 장면 (사람, 제품, 사용 장면 등)

   **원칙**: "텍스트가 없으면 영상이 성립 안 되는 경우"만 needs_text: true
   **기본값**: needs_text: false

**전환 정보 (컷과 컷 사이):**
1. method: "kling" 또는 "ffmpeg"
   - **kling**: 역동적 움직임 또는 실제 액션이 필요한 경우 - Kling 2.1 AI 비디오 생성
     * 카메라 움직임: 줌인/아웃, 회전, 복잡한 패닝
     * 객체 동작: 휘젓기, 붓기, 들기, 움직이는 손/사람
     * 역동적 장면 전환: 빠른 모션, 유체 움직임
   - **ffmpeg**: 정적 장면 간 단순 전환만 필요한 경우 - 기본 효과
     * 디졸브, 페이드, 크로스페이드
     * 비슷한 구도의 정적 컷 사이
   - **사용 전략**: 전체 전환의 50-70%는 kling 사용 (퀄리티 우선)
   - **kling 비용**: $0.25/video (5초)
2. effect: 전환 효과명 (참고용)
   - kling: "dynamic_zoom_in", "dynamic_zoom_out", "dynamic_pan", "complex_transition"
   - ffmpeg: "dissolve", "fade", "zoom_in", "zoom_out", "pan_left", "pan_right"
3. video_prompt: **구체적인 비디오 생성 프롬프트** (kling 사용 시 필수!)
   - 제품 특징, 브랜드 톤, 장면 설명 포함
   - 카메라 움직임, 조명, 분위기 상세히 기술
   - 앞 컷과 뒤 컷의 연결을 자연스럽게 설명
   - 예: "Camera smoothly zooms out from close-up of luxury bottle's golden cap, gradually revealing the full pristine white bottle against minimalist marble background, maintaining soft professional lighting throughout"

   **⚠️ 사람의 동작이 포함될 때 (필수 준수):**
   - 모든 동작은 **자연스럽고 일반적인 방식**으로 표현
   - 과장되거나 어색한 동작 금지, 실제 사람이 하는 그대로 묘사
   - 예시:
     * 가방 메기: "casually swings bag over shoulder in one smooth motion" (어깨에 툭 메는 자연스러운 동작)
     * 음료 마시기: "lifts cup naturally to lips, takes a gentle sip"
     * 제품 들기: "picks up product with relaxed hand movement"
     * 걷기: "walks with natural, easy stride"
   - 동작의 속도와 리듬이 현실적이어야 함

   **⚠️ 재료/소재를 다루는 장면 (도구 사용 필수):**
   - 손으로 직접 다루기 어려운 재료는 **적절한 도구를 반드시 명시**
   - 도구의 종류와 사용 방법을 구체적으로 작성
   - 예시:
     * 딸기 퓨레 담기: "using a long thin spoon to scoop strawberry puree"
     * 라떼 붓기: "pouring latte from stainless steel milk jug with steady hand"
     * 시럽 뿌리기: "drizzling syrup using squeeze bottle in circular motion"
     * 가루 뿌리기: "using small mesh sifter to dust matcha powder"
     * 휘핑크림 올리기: "piping whipped cream using pastry bag with star tip"
     * 재료 섞기: "stirring ingredients with wooden stirrer/long spoon"
   - 도구 없이 손으로만 하는 것은 비현실적 → 반드시 도구 사용

   - ffmpeg 사용 시에는 간단히 작성 (효과명만 참고)
4. duration: 전환 길이 (초)
   - **kling**: 평균 {avg_transition_duration:.1f}초 (5초 권장)
   - **ffmpeg**: 0.5-2초
5. reason: 이 방식을 선택한 이유 (한 줄)

**스토리보드 작성 가이드라인:**
- 첫 번째 컷: 임팩트 있는 오프닝 (hero shot)
- 중간 컷들: 제품 특징, 사용 시나리오, 혜택
- 마지막 컷: CTA 또는 브랜드 메시지 (hero shot)
- **전환 전략 (퀄리티 우선):**
  * 실제 동작/액션이 있는 장면 → 무조건 kling 사용
  * 역동적 카메라 움직임 필요 → kling 사용
  * 정적 컷 간 단순 전환만 → ffmpeg 사용 가능
  * 전체의 50-70%는 kling으로 구성하여 영상의 퀘리티 확보
- **동작 및 도구 사용 (중요!):**
  * 사람의 모든 동작은 자연스럽고 일반적인 방식으로 (과장 금지)
  * 재료/소재를 다룰 때는 적절한 도구를 구체적으로 명시 (손으로만 하는 것 금지)
- 전체 흐름의 리듬감 유지
- **image_prompt 작성 시 필수 사항:**
  * 브랜드 컨텍스트의 "제품 비주얼 특징"에 명시된 색상, 스타일, 조명, 분위기를 **반드시** 포함
  * 예: "주요 색상: white, gold" → image_prompt에 "white and gold color scheme" 포함
  * 예: "조명 스타일: soft natural lighting" → 모든 컷에 "soft natural lighting" 포함
  * 예: "배경 스타일: marble texture" → 배경이 있는 컷에는 "marble background" 포함
  * 조명, 각도, 분위기, 색감을 상세하게 작성하되, 일관성을 최우선으로
- video_prompt는 앞뒤 컷의 맥락을 고려하여 구체적이고 일관성 있게 작성

**응답 형식 (JSON):**
{{
  "story_structure": "선택한 스토리 구조명 (예: Process/Creation, Before-After 등)",
  "story_rationale": "이 스토리 구조를 선택한 이유 (1-2문장, 한국어)",
  "storyboard": [
    {{
      "cut": 1,
      "scene_description": "[스토리 역할] 장면 설명",
      "story_role": "이 컷이 스토리에서 맡는 역할 (예: 문제 제시, 재료 소개 등)",
      "image_prompt": "...",
      "duration": {cut_duration},
      "is_hero_shot": true,
      "resolution": "1080p",
      "needs_text": false
    }},
  {{
    "transition": {{
      "method": "kling",
      "effect": "dynamic_zoom_out",
      "video_prompt": "Camera smoothly zooms out from extreme close-up of product detail, gradually revealing full product in elegant setting with professional lighting",
      "duration": {avg_transition_duration:.1f},
      "reason": "제품 디테일에서 전체로, 강렬한 전환 필요"
    }}
  }},
  {{
    "cut": 2,
    "scene_description": "[스토리 역할] 장면 설명",
    "story_role": "이 컷이 스토리에서 맡는 역할",
    "image_prompt": "...",
    "duration": {cut_duration},
    "is_hero_shot": false,
    "resolution": "720p",
    "needs_text": false
  }},
    ...
  ]
}}

다른 설명 없이 위 형식의 JSON만 반환해주세요."""

        user_message = f"""제품명: {product_name}
제품 설명: {product_description or '제공되지 않음'}

브랜드 컨텍스트:
{brand_context}

위 제품 이미지를 분석하고, {cut_count}개의 컷으로 구성된 약 {duration_seconds}초 길이의 마케팅 비디오 스토리보드를 JSON 배열로 생성해주세요."""

        # Vertex AI Gemini API 호출
        logger.info(f"Calling Vertex AI Gemini API for storyboard generation ({cut_count} cuts, {duration_seconds}s)")

        # Vertex AI Gemini 모델 초기화
        gemini_model = VertexGenerativeModel(self.model)

        # image_data를 PIL Image로 변환 후 Vertex AI Part 객체로 변환
        from PIL import Image
        import io

        image_bytes = base64.b64decode(image_data["data"])
        pil_image = Image.open(io.BytesIO(image_bytes))

        # PIL Image → Vertex AI Part 객체 변환
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()

        image_part = Part.from_data(
            data=img_bytes,
            mime_type="image/jpeg"
        )

        # System prompt와 user message를 결합 (Gemini는 system 파라미터 미지원)
        combined_prompt = f"""{system_prompt}

---

{user_message}"""

        # Vertex AI Gemini API 호출 (Part 객체 사용)
        response = gemini_model.generate_content([combined_prompt, image_part])

        # 응답 파싱
        response_text = response.text
        logger.info(f"Gemini response: {response_text[:200]}...")

        # JSON 파싱
        try:
            # JSON 코드 블록이 있다면 추출
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            response_json = json.loads(response_text)

            # 새 형식 (객체) 또는 구 형식 (배열) 모두 지원
            if isinstance(response_json, dict):
                # 새 형식: {uploaded_image_placement: {...}, storyboard: [...]}
                uploaded_image_placement = response_json.get('uploaded_image_placement', {})
                storyboard = response_json.get('storyboard', [])

                # 로그 출력
                if uploaded_image_placement:
                    logger.info(f"Uploaded image placement: {uploaded_image_placement.get('position')} (cut {uploaded_image_placement.get('cut_number')})")
                    logger.info(f"Reason: {uploaded_image_placement.get('reason')}")
            elif isinstance(response_json, list):
                # 구 형식: 배열만
                storyboard = response_json
                uploaded_image_placement = {}
                logger.warning("Old format storyboard (array only)")
            else:
                raise ValueError("Invalid storyboard format")

            # 유효성 검증
            if not isinstance(storyboard, list):
                raise ValueError("Storyboard must be a list")

            # 컷과 전환을 분리하여 검증
            cuts = [item for item in storyboard if 'cut' in item]
            transitions = [item for item in storyboard if 'transition' in item]

            if len(cuts) != cut_count:
                logger.warning(f"Expected {cut_count} cuts but got {len(cuts)}")

            # 각 컷 검증
            for i, cut in enumerate(cuts, 1):
                required_fields = ["cut", "scene_description", "image_prompt", "duration", "is_hero_shot", "resolution"]
                for field in required_fields:
                    if field not in cut:
                        raise ValueError(f"Cut {i} missing required field: {field}")

            # 각 전환 검증
            for i, item in enumerate(transitions, 1):
                transition = item.get('transition', {})
                required_fields = ["method", "effect", "duration", "reason"]
                for field in required_fields:
                    if field not in transition:
                        logger.warning(f"Transition {i} missing field: {field}")

            logger.info(f"Storyboard validated: {len(cuts)} cuts, {len(transitions)} transitions")
            return storyboard

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {str(e)}")
            logger.error(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from Claude: {str(e)}")


class ImageGenerationAgent:
    """
    Image Generation Agent
    - Vertex AI Gemini 2.5 Flash Image 모델을 사용하여 스토리보드 각 컷의 이미지 생성
    - 9:16 세로 비율 (숏폼 최적화)
    - 생성된 이미지를 로컬 파일 시스템에 PNG로 저장
    """

    def __init__(self, model: str = "gemini-2.5-flash-image-ga"):
        self.model = model
        logger.info(f"ImageGenerationAgent initialized with Vertex AI model: {self.model}")

    async def generate_images(
        self,
        job: VideoGenerationJob,
        storyboard: List[Dict[str, Any]],
        db: Session
    ) -> List[Dict[str, str]]:
        """
        스토리보드의 각 컷에 대한 이미지 생성

        Args:
            job: VideoGenerationJob 인스턴스
            storyboard: 스토리보드 데이터 (컷과 전환이 혼합된 배열)
            db: Database session

        Returns:
            List[Dict]: 생성된 이미지 URL 리스트
            [{"cut": 1, "url": "https://...", "resolution": "1080p", "is_hero_shot": true}, ...]
        """
        try:
            # 스토리보드에서 컷만 필터링
            cuts = [item for item in storyboard if 'cut' in item]

            # Job 상태 업데이트
            job.status = "generating_images"
            job.current_step = f"Generating images for {len(cuts)} cuts"
            db.commit()

            logger.info(f"Starting image generation for job {job.id}: {len(cuts)} cuts")
            logger.info(f"Using Vertex AI Gemini model: {self.model}")

            generated_images = []

            # 단일 이미지 생성 헬퍼 함수
            async def generate_single_image(cut, cut_index):
                """단일 이미지 생성 및 업로드"""
                try:
                    cut_number = cut['cut']
                    resolution = cut.get('resolution', '720p')
                    is_hero_shot = cut.get('is_hero_shot', False)
                    needs_text = cut.get('needs_text', False)

                    logger.info(f"Generating image for cut {cut_number}/{len(cuts)}: {cut['image_prompt'][:50]}... (resolution: {resolution}, hero: {is_hero_shot}, needs_text: {needs_text})")

                    # Gemini로 이미지 생성
                    image_bytes = await self._generate_with_gemini_image(cut['image_prompt'], needs_text=needs_text)

                    if not image_bytes:
                        raise ValueError(f"Failed to generate image for cut {cut_number}")

                    # 이미지를 Supabase Storage에 저장
                    image_url = await self._upload_to_supabase(
                        image_bytes,
                        job.user_id,
                        job.id,
                        cut_number,
                        job.session_id
                    )

                    logger.info(f"Image generated and uploaded for cut {cut_number}: {image_url}")

                    return {
                        "cut": cut_number,
                        "url": image_url,
                        "prompt": cut['image_prompt'],
                        "resolution": resolution,
                        "is_hero_shot": is_hero_shot,
                        "source": "generated"
                    }

                except Exception as e:
                    logger.error(f"Error generating image for cut {cut.get('cut', cut_index)}: {str(e)}")
                    return {
                        "cut": cut.get('cut', cut_index),
                        "url": None,
                        "error": str(e),
                        "prompt": cut.get('image_prompt', ''),
                        "resolution": cut.get('resolution', '720p'),
                        "is_hero_shot": cut.get('is_hero_shot', False)
                    }

            # 2개씩 병렬 처리
            batch_size = 2
            for batch_start in range(0, len(cuts), batch_size):
                batch_end = min(batch_start + batch_size, len(cuts))
                batch_cuts = cuts[batch_start:batch_end]
                batch_num = (batch_start // batch_size) + 1
                total_batches = (len(cuts) + batch_size - 1) // batch_size

                # Job 상태 업데이트
                job.current_step = f"Generating images batch {batch_num}/{total_batches} (cuts {batch_start+1}-{batch_end})"
                db.commit()

                logger.info(f"Processing batch {batch_num}/{total_batches}: cuts {batch_start+1}-{batch_end}")

                # 배치 내 이미지들을 병렬로 생성
                batch_tasks = [
                    generate_single_image(cut, batch_start + i + 1)
                    for i, cut in enumerate(batch_cuts)
                ]
                batch_results = await asyncio.gather(*batch_tasks)
                generated_images.extend(batch_results)

                # 다음 배치 전 쿼터 초과 방지를 위한 대기
                if batch_end < len(cuts):
                    wait_time = 1  # 1초 대기 (기존 3초에서 단축)
                    logger.info(f"다음 배치 생성 전 {wait_time}초 대기 중... (쿼터 최적화)")
                    await asyncio.sleep(wait_time)

            # 생성된 이미지 저장
            job.generated_image_urls = generated_images
            db.commit()

            logger.info(f"Image generation completed for job {job.id}: {len([img for img in generated_images if img.get('url')])} successful")
            return generated_images

        except Exception as e:
            logger.error(f"Error in image generation for job {job.id}: {str(e)}")
            job.status = "failed"
            job.error_message = f"Image generation failed: {str(e)}"
            db.commit()
            raise

    async def _generate_with_gemini_image(self, prompt: str, needs_text: bool = False) -> bytes:
        """
        Google Gen AI SDK를 사용하여 Gemini 이미지 생성
        Vertex AI 백엔드 사용, 9:16 aspect ratio 지원
        Exponential backoff 재시도 로직 포함 (429 쿼터 에러 대응)

        Args:
            prompt: 이미지 생성 프롬프트
            needs_text: True면 gemini-3-pro-image-preview (텍스트 특화), False면 gemini-2.5-flash-image (일반)
        """
        from google import genai
        from google.genai import types
        from google.api_core.exceptions import ResourceExhausted, TooManyRequests

        # needs_text에 따라 모델 및 리전 선택
        # gemini-3-pro-image-preview는 global 리전만 지원
        model_name = 'gemini-3-pro-image-preview' if needs_text else 'gemini-2.5-flash-image'
        model_display = "Gemini 3 Pro Image (텍스트 특화)" if needs_text else "Gemini 2.5 Flash Image (일반)"
        model_location = "global" if needs_text else SELECTED_LOCATION

        max_retries = 5
        base_delay = 2  # 초기 대기 시간 (초)

        for attempt in range(max_retries):
            try:
                logger.info(f"Vertex AI {model_display}로 이미지 생성 중 (9:16, location={model_location})... (시도 {attempt + 1}/{max_retries}, 프롬프트: {prompt[:50]}...)")

                # Google Gen AI Client 초기화 (Vertex AI 백엔드 사용)
                client = genai.Client(
                    vertexai=True,
                    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                    location=model_location  # needs_text=True면 global, 아니면 기존 리전
                )

                # 이미지 생성 요청 (9:16 aspect ratio 지정)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(
                            aspect_ratio="9:16",  # 세로 비율 (short-form video)
                        ),
                    ),
                )

                # 응답에서 이미지 추출
                for part in response.parts:
                    if part.inline_data:
                        # inline_data에서 이미지 bytes 추출
                        if hasattr(part.inline_data, 'data'):
                            image_bytes = part.inline_data.data
                            mime_type = getattr(part.inline_data, 'mime_type', 'image/png')

                            logger.info(f"✅ 이미지 생성 완료 ({model_display}, 9:16 aspect ratio, 시도 {attempt + 1}, MIME type: {mime_type}, size: {len(image_bytes)} bytes)")
                            return image_bytes

                # 이미지를 찾지 못한 경우
                logger.error(f"Gemini 응답에서 이미지를 찾지 못함: {response}")
                raise ValueError("Gemini로부터 이미지를 추출하지 못했습니다.")

            except Exception as e:
                error_str = str(e)

                # 429 쿼터 에러인지 확인 (문자열로 검사)
                is_quota_error = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower()

                if is_quota_error:
                    # 429 쿼터 에러 발생 시 exponential backoff 재시도
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2 ** attempt)  # 2, 4, 8, 16, 32초
                        logger.warning(f"⚠️  429 쿼터 에러 발생 (시도 {attempt + 1}/{max_retries}): {error_str[:200]}")
                        logger.info(f"🔄 {wait_time}초 후 재시도... (exponential backoff)")
                        await asyncio.sleep(wait_time)
                        continue  # 다음 시도로
                    else:
                        logger.error(f"❌ 최대 재시도 횟수({max_retries})에 도달. 이미지 생성 실패: {error_str[:200]}")
                        raise
                else:
                    # 429 외의 에러는 즉시 실패
                    logger.error(f"❌ {model_display} 생성 실패: {error_str}")
                    raise

    async def _upload_to_supabase(
        self,
        image_data: bytes,
        user_id: int,
        job_id: int,
        cut_number: int,
        session_id: str
    ) -> str:
        """이미지를 Supabase Storage에 PNG로 저장"""
        try:
            from app.services.supabase_storage import get_storage_service
            storage = get_storage_service()

            # 파일 경로 생성
            file_path = f"{user_id}/{session_id}/cut_{cut_number}.png"

            # Supabase Storage에 업로드
            file_url = storage.upload_file(
                bucket="ai-video-cuts",
                file_path=file_path,
                file_data=image_data,
                content_type="image/png"
            )

            logger.info(f"Image saved to Supabase Storage: {file_url}")
            return file_url
        except Exception as e:
            logger.error(f"Failed to save image to Supabase Storage: {str(e)}")
            raise


class KlingVideoGenerationAgent:
    """
    Kling v2.1 Standard Video Generation Agent
    - fal.ai API를 사용하여 이미지 간 트랜지션 비디오 생성
    - Image-to-Video 방식
    - Front-Last Frame 지원
    """

    def __init__(self, model: str = "fal-ai/kling-video/v2.1/standard/image-to-video"):
        self.model = model
        self.api_key = os.getenv("FAL_KEY")
        if not self.api_key:
            raise ValueError("FAL_KEY not found in environment variables")
        logger.info(f"KlingVideoGenerationAgent initialized with model: {self.model}")

    def image_to_data_url(self, image_path: str) -> str:
        """
        로컬 이미지 파일을 data URL로 변환

        Args:
            image_path: 이미지 파일 경로

        Returns:
            data URL 형식의 문자열 (data:image/png;base64,...)
        """
        try:
            # 1. 이미지 읽기
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            # 2. base64 인코딩
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")

            # 3. MIME type 결정
            ext = Path(image_path).suffix.lower()
            mime_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp"
            }
            mime_type = mime_map.get(ext, "image/png")

            # 4. data URL 생성
            data_url = f"data:{mime_type};base64,{image_b64}"
            logger.info(f"Image converted to data URL: {image_path} ({len(data_url)} chars)")
            return data_url

        except Exception as e:
            logger.error(f"Failed to convert image to data URL: {str(e)}")
            raise

    async def download_video(self, video_url: str, save_path: str) -> bool:
        """
        fal.ai에서 생성된 비디오 다운로드

        Args:
            video_url: 비디오 다운로드 URL
            save_path: 저장할 경로

        Returns:
            성공 여부
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.info(f"Downloading video from: {video_url}")
                response = await client.get(video_url)
                response.raise_for_status()

                # 디렉토리 생성
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)

                # 파일 저장
                with open(save_path, "wb") as f:
                    f.write(response.content)

                file_size_mb = len(response.content) / (1024 * 1024)
                logger.info(f"Video downloaded: {save_path} ({file_size_mb:.2f} MB)")
                return True

        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            return False

    async def generate_transition_video(
        self,
        start_image_path: str,
        end_image_path: str,
        prompt: str,
        duration: int = 5,
        user_id: int = None,
        job_id: int = None,
        transition_name: str = "transition"
    ) -> dict:
        """
        두 이미지 사이의 전환 비디오 생성

        Args:
            start_image_path: 시작 이미지 경로
            end_image_path: 종료 이미지 경로
            prompt: 비디오 생성 프롬프트
            duration: 비디오 길이 (초)
            user_id: 사용자 ID
            job_id: 작업 ID
            transition_name: 전환 이름 (예: "1-2")

        Returns:
            {
                "transition": "1-2",
                "url": "/uploads/...",
                "method": "kling",
                "effect": "...",
                "error": None
            }
        """
        try:
            logger.info(f"Generating Kling video for {transition_name}: {prompt}")

            # 1. 시작 이미지를 data URL로 변환 (Kling은 시작 이미지만 사용)
            image_data_url = self.image_to_data_url(start_image_path)

            # 2. fal.ai API 호출
            logger.info(f"Calling fal.ai API...")

            # asyncio.to_thread를 사용하여 동기 함수를 비동기로 실행
            result = await asyncio.to_thread(
                fal_client.subscribe,
                self.model,
                arguments={
                    "image_url": image_data_url,
                    "prompt": prompt,
                    "duration": duration,
                    "aspect_ratio": "9:16"
                },
                with_logs=False
            )

            logger.info(f"Kling API response received")

            # 3. 응답에서 비디오 URL 추출
            if not result or "video" not in result:
                raise ValueError(f"Invalid API response: {result}")

            video_url = result["video"]["url"]
            logger.info(f"Video URL: {video_url}")

            # 4. 비디오 다운로드 및 Supabase Storage에 업로드
            # 먼저 비디오를 다운로드
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download video: HTTP {response.status}")
                    video_bytes = await response.read()

            # Supabase Storage에 업로드
            from app.services.supabase_storage import get_storage_service
            from app.database import SessionLocal

            # session_id 가져오기
            db = SessionLocal()
            try:
                from app import models
                job = db.query(models.VideoGenerationJob).filter(
                    models.VideoGenerationJob.id == job_id
                ).first()
                session_id = job.session_id if job else str(job_id)
            finally:
                db.close()

            storage = get_storage_service()
            file_path = f"{user_id}/{session_id}/{transition_name}.mp4"

            relative_url = storage.upload_file(
                bucket="ai-video-transitions",
                file_path=file_path,
                file_data=video_bytes,
                content_type="video/mp4"
            )

            logger.info(f"Kling video generated successfully: {relative_url}")

            return {
                "success": True,
                "transition": transition_name,
                "url": relative_url,
                "method": "kling",
                "effect": prompt,
                "error": None,
                "cost": 0.25  # USD
            }

        except Exception as e:
            logger.error(f"Failed to generate Kling video: {str(e)}")
            return {
                "success": False,
                "transition": transition_name,
                "url": None,
                "method": "kling",
                "effect": prompt,
                "error": str(e),
                "cost": 0
            }

    async def generate_transition_videos(
        self,
        job: VideoGenerationJob,
        storyboard: List[Dict[str, Any]],
        images: List[Dict[str, str]],
        db: Session
    ) -> List[Dict[str, str]]:
        """
        이미지 간 트랜지션 비디오 생성 (Kling 방식만 선택적으로)

        Args:
            job: VideoGenerationJob 인스턴스
            storyboard: 스토리보드 데이터 (전환 정보 포함)
            images: 생성된 이미지 리스트
            db: Database session

        Returns:
            List[Dict]: 생성된 비디오 URL 리스트 (Kling 전환만)
        """
        try:
            # 스토리보드에서 Kling 방식의 전환만 필터링
            kling_transitions = [
                item['transition'] for item in storyboard
                if 'transition' in item and item['transition'].get('method') == 'kling'
            ]

            # Job 상태 업데이트
            job.status = "generating_videos"
            job.current_step = f"Generating {len(kling_transitions)} Kling transition videos"
            db.commit()

            logger.info(f"Starting Kling video generation for job {job.id}: {len(kling_transitions)} transitions (FFmpeg transitions will be handled in composition)")

            if not kling_transitions:
                logger.info("No Kling transitions needed - all transitions will use FFmpeg")
                job.generated_video_urls = []
                db.commit()
                return []

            generated_videos = []

            # 유효한 이미지만 필터링
            valid_images = [img for img in images if img.get('url')]

            if len(valid_images) < 2:
                raise ValueError("Need at least 2 images to create transition videos")

            # 이미지를 cut 번호로 매핑
            image_by_cut = {img['cut']: img for img in valid_images}

            # 스토리보드에서 전환과 컷의 매핑 생성
            cuts = [item for item in storyboard if 'cut' in item]

            # 각 Kling 전환 비디오 생성
            for idx, transition_data in enumerate(kling_transitions, 1):
                try:
                    effect = transition_data.get('effect', 'smooth_transition')
                    duration = transition_data.get('duration', 5.0)
                    reason = transition_data.get('reason', '')

                    # Master Agent가 생성한 video_prompt 사용
                    video_prompt = transition_data.get('video_prompt',
                        'Smooth, cinematic transition from the first image to the second image.')

                    # 전환이 어느 컷 사이인지 추론 (스토리보드의 순서 기반)
                    transition_index = None
                    for i, item in enumerate(storyboard):
                        if 'transition' in item and item['transition'] == transition_data:
                            transition_index = i
                            break

                    if transition_index is None:
                        logger.warning(f"Could not find transition in storyboard, skipping")
                        continue

                    # 앞뒤 컷 찾기
                    from_cut = None
                    to_cut = None
                    for i in range(transition_index - 1, -1, -1):
                        if 'cut' in storyboard[i]:
                            from_cut = storyboard[i]['cut']
                            break
                    for i in range(transition_index + 1, len(storyboard)):
                        if 'cut' in storyboard[i]:
                            to_cut = storyboard[i]['cut']
                            break

                    if not from_cut or not to_cut:
                        logger.warning(f"Could not determine from/to cuts for transition, skipping")
                        continue

                    from_image = image_by_cut.get(from_cut)
                    to_image = image_by_cut.get(to_cut)

                    if not from_image or not to_image:
                        logger.warning(f"Missing images for transition {from_cut}-{to_cut}, skipping")
                        continue

                    transition_name = f"{from_cut}-{to_cut}"

                    logger.info(f"Generating Kling transition video {idx}/{len(kling_transitions)}: {transition_name} (prompt: {video_prompt[:80]}...)")

                    # Job 상태 업데이트
                    job.current_step = f"Generating Kling transition {idx}/{len(kling_transitions)}"
                    db.commit()

                    # 로컬 파일 시스템에서 이미지 경로 가져오기
                    from_image_path = from_image['url']  # 예: "/uploads/ai_video_images/1/18/cut_1.png"
                    to_image_path = to_image['url']

                    # 상대 경로를 절대 경로로 변환
                    from_image_abs = Path(__file__).parent.parent.parent / from_image_path.lstrip('/')
                    to_image_abs = Path(__file__).parent.parent.parent / to_image_path.lstrip('/')

                    # Kling API 호출
                    result = await self.generate_transition_video(
                        start_image_path=str(from_image_abs),
                        end_image_path=str(to_image_abs),
                        prompt=video_prompt,
                        duration=int(duration),
                        user_id=job.user_id,
                        job_id=job.id,
                        transition_name=transition_name
                    )

                    if result.get('success'):
                        generated_videos.append({
                            "transition": transition_name,
                            "url": result['url'],
                            "from_cut": from_cut,
                            "to_cut": to_cut,
                            "method": "kling",
                            "effect": effect,
                            "duration": duration,
                            "reason": reason,
                            "cost": result.get('cost', 0.25)
                        })
                        logger.info(f"Kling transition video generated: {transition_name} -> {result['url']}")
                    else:
                        logger.error(f"Failed to generate Kling video for {transition_name}: {result.get('error')}")
                        generated_videos.append({
                            "transition": transition_name,
                            "url": None,
                            "error": result.get('error'),
                            "method": "kling",
                            "effect": effect
                        })

                except Exception as e:
                    logger.error(f"Error generating Kling transition video: {str(e)}")
                    if 'transition_name' in locals():
                        generated_videos.append({
                            "transition": transition_name,
                            "url": None,
                            "error": str(e),
                            "method": "kling",
                            "effect": transition_data.get('effect', '')
                        })

            # 생성된 비디오 저장
            job.generated_video_urls = generated_videos
            db.commit()

            logger.info(f"Kling video generation completed for job {job.id}: {len([vid for vid in generated_videos if vid.get('url')])} successful")
            return generated_videos

        except Exception as e:
            logger.error(f"Error in video generation for job {job.id}: {str(e)}")
            job.status = "failed"
            job.error_message = f"Video generation failed: {str(e)}"
            db.commit()
            raise


class VideoGenerationAgent:
    """
    Video Generation Agent
    - Vertex AI Veo 3.1을 사용하여 이미지 간 트랜지션 비디오 생성
    - 생성된 비디오를 Cloudinary에 업로드
    """

    def __init__(self, model: str = "veo-3.1-fast-generate-001"):
        self.model = model
        logger.info(f"VideoGenerationAgent initialized with Vertex AI model: {self.model}")

    async def generate_transition_videos(
        self,
        job: VideoGenerationJob,
        storyboard: List[Dict[str, Any]],
        images: List[Dict[str, str]],
        db: Session
    ) -> List[Dict[str, str]]:
        """
        이미지 간 트랜지션 비디오 생성 (Veo 방식만 선택적으로)

        Args:
            job: VideoGenerationJob 인스턴스
            storyboard: 스토리보드 데이터 (전환 정보 포함)
            images: 생성된 이미지 리스트
            db: Database session

        Returns:
            List[Dict]: 생성된 비디오 URL 리스트 (Veo 전환만)
            [{"transition": "1-2", "url": "https://...", "method": "veo", "effect": "..."}, ...]
        """
        try:
            # 스토리보드에서 Veo 방식의 전환만 필터링
            veo_transitions = [
                item['transition'] for item in storyboard
                if 'transition' in item and item['transition'].get('method') == 'veo'
            ]

            # Job 상태 업데이트
            job.status = "generating_videos"
            job.current_step = f"Generating {len(veo_transitions)} Veo transition videos"
            db.commit()

            logger.info(f"Starting Veo video generation for job {job.id}: {len(veo_transitions)} transitions (FFmpeg transitions will be handled in composition)")

            if not veo_transitions:
                logger.info("No Veo transitions needed - all transitions will use FFmpeg")
                job.generated_video_urls = []
                db.commit()
                return []

            generated_videos = []

            # Vertex AI Veo 모델 초기화
            try:
                veo_model = VertexGenerativeModel(self.model)
                logger.info(f"✅ Using Vertex AI Veo model: {self.model}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Veo model: {str(e)}")
                raise ValueError(f"Failed to initialize Veo model '{self.model}': {str(e)}")

            # 유효한 이미지만 필터링
            valid_images = [img for img in images if img.get('url')]

            if len(valid_images) < 2:
                raise ValueError("Need at least 2 images to create transition videos")

            # 이미지를 cut 번호로 매핑
            image_by_cut = {img['cut']: img for img in valid_images}

            # 스토리보드에서 전환과 컷의 매핑 생성
            cuts = [item for item in storyboard if 'cut' in item]

            # 각 Veo 전환 비디오 생성
            for idx, transition_data in enumerate(veo_transitions, 1):
                try:
                    effect = transition_data.get('effect', 'smooth_transition')
                    duration = transition_data.get('duration', 4.0)
                    reason = transition_data.get('reason', '')

                    # 전환이 어느 컷 사이인지 추론 (스토리보드의 순서 기반)
                    # 스토리보드에서 전환의 위치를 찾아 앞뒤 컷 번호 추출
                    transition_index = None
                    for i, item in enumerate(storyboard):
                        if 'transition' in item and item['transition'] == transition_data:
                            transition_index = i
                            break

                    if transition_index is None:
                        logger.warning(f"Could not find transition in storyboard, skipping")
                        continue

                    # 앞뒤 컷 찾기
                    from_cut = None
                    to_cut = None
                    for i in range(transition_index - 1, -1, -1):
                        if 'cut' in storyboard[i]:
                            from_cut = storyboard[i]['cut']
                            break
                    for i in range(transition_index + 1, len(storyboard)):
                        if 'cut' in storyboard[i]:
                            to_cut = storyboard[i]['cut']
                            break

                    if not from_cut or not to_cut:
                        logger.warning(f"Could not determine from/to cuts for transition, skipping")
                        continue

                    from_image = image_by_cut.get(from_cut)
                    to_image = image_by_cut.get(to_cut)

                    if not from_image or not to_image:
                        logger.warning(f"Missing images for transition {from_cut}-{to_cut}, skipping")
                        continue

                    transition_name = f"{from_cut}-{to_cut}"

                    logger.info(f"Generating Veo transition video {idx}/{len(veo_transitions)}: {transition_name} (effect: {effect})")

                    # Job 상태 업데이트
                    job.current_step = f"Generating Veo transition {idx}/{len(veo_transitions)} ({effect})"
                    db.commit()

                    # 효과에 따른 프롬프트 생성
                    video_prompt = self._create_veo_prompt(effect, duration)
                    logger.info(f"Video prompt: {video_prompt}")

                    # 이미지 다운로드 및 base64 인코딩
                    from_image_data = await self._download_image(from_image['url'])

                    logger.info(f"Downloaded from_image: {len(from_image_data)} bytes")

                    # PIL로 이미지 처리
                    from PIL import Image
                    import io

                    # 첫 번째 이미지를 reference image로 사용
                    pil_image = Image.open(io.BytesIO(from_image_data))

                    # PIL Image → bytes 변환
                    img_byte_arr = io.BytesIO()
                    pil_image.save(img_byte_arr, format='PNG')
                    reference_image_bytes = img_byte_arr.getvalue()

                    # Veo 3.1 API 호출 (with exponential backoff for rate limiting)
                    # 참조 이미지를 기반으로 비디오 생성
                    logger.info(f"Calling Veo API with prompt: {video_prompt}")

                    # Exponential backoff 설정
                    max_retries = 5
                    base_delay = 2  # seconds
                    response = None

                    for attempt in range(max_retries):
                        try:
                            response = veo_model.generate_content([
                                Part.from_data(data=reference_image_bytes, mime_type="image/png"),
                                f"{video_prompt}. Duration: {int(duration)} seconds. Aspect ratio: 9:16 vertical video for social media."
                            ])

                            # 성공하면 루프 탈출
                            logger.info(f"Veo API call successful (attempt {attempt + 1}/{max_retries})")
                            break

                        except Exception as api_error:
                            error_str = str(api_error)

                            # 429 (Resource Exhausted) 또는 503 (Service Unavailable) 에러인 경우 재시도
                            if '429' in error_str or 'ResourceExhausted' in error_str or '503' in error_str:
                                if attempt < max_retries - 1:
                                    delay = base_delay * (2 ** attempt)  # exponential backoff: 2s, 4s, 8s, 16s, 32s
                                    logger.warning(f"Rate limit/throttling detected (attempt {attempt + 1}/{max_retries}), retrying in {delay}s...")
                                    await asyncio.sleep(delay)
                                else:
                                    logger.error(f"Max retries ({max_retries}) reached for {transition_name}, giving up")
                                    raise
                            else:
                                # 다른 에러는 재시도하지 않고 바로 raise
                                raise

                    # 비디오 데이터 추출
                    if not response or not response.candidates:
                        raise ValueError(f"No response from Veo API for transition {transition_name}")

                    # 응답 구조 확인
                    logger.info(f"Veo response type: {type(response)}")

                    # 비디오 데이터 찾기
                    video_data = None
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            # MIME 타입이 video인지 확인
                            if 'video' in part.inline_data.mime_type:
                                video_data = part.inline_data.data
                                logger.info(f"Found video data: mime_type={part.inline_data.mime_type}")
                                break

                    if not video_data:
                        raise ValueError(f"No video data in Veo response for transition {transition_name}")

                    # 비디오 저장 (Supabase Storage)
                    from app.services.supabase_storage import get_storage_service
                    storage = get_storage_service()

                    # base64 디코딩
                    video_bytes = base64.b64decode(video_data)

                    # Supabase Storage에 업로드
                    file_path = f"{job.user_id}/{job.session_id}/{transition_name}.mp4"
                    video_url = storage.upload_file(
                        bucket="ai-video-transitions",
                        file_path=file_path,
                        file_data=video_bytes,
                        content_type="video/mp4"
                    )

                    logger.info(f"Veo video saved to Supabase Storage: {video_url} ({len(video_bytes)} bytes)")

                    generated_videos.append({
                        "transition": transition_name,
                        "url": video_url,
                        "from_cut": from_cut,
                        "to_cut": to_cut,
                        "method": "veo",
                        "effect": effect,
                        "duration": duration,
                        "reason": reason
                    })

                    logger.info(f"Veo transition video generated and uploaded: {transition_name} -> {video_url}")

                except Exception as e:
                    logger.error(f"Error generating Veo transition video: {str(e)}")
                    # 일부 비디오 생성 실패해도 계속 진행
                    if 'transition_name' in locals():
                        generated_videos.append({
                            "transition": transition_name,
                            "url": None,
                            "error": str(e),
                            "method": "veo",
                            "effect": transition_data.get('effect', '')
                        })

            # 생성된 비디오 저장
            job.generated_video_urls = generated_videos
            db.commit()

            logger.info(f"Veo video generation completed for job {job.id}: {len([vid for vid in generated_videos if vid.get('url')])} successful")
            return generated_videos

        except Exception as e:
            logger.error(f"Error in video generation for job {job.id}: {str(e)}")
            job.status = "failed"
            job.error_message = f"Video generation failed: {str(e)}"
            db.commit()
            raise

    def _create_veo_prompt(self, effect: str, duration: float) -> str:
        """효과에 따른 Veo 프롬프트 생성"""
        prompts = {
            "dynamic_zoom_in": "Smooth, cinematic zoom in from the first image to the second image. Professional camera movement with elegant transition.",
            "dynamic_zoom_out": "Smooth, cinematic zoom out from the first image to the second image. Professional camera movement with elegant transition.",
            "dynamic_pan": "Smooth, cinematic panning from the first image to the second image. Professional lateral camera movement.",
            "complex_transition": "Dynamic, creative transition from the first image to the second image. Cinematic and engaging camera movement."
        }
        return prompts.get(effect, "Smooth transition from the first image to the second image. Professional, cinematic camera movement.")

    async def _download_image(self, url: str) -> bytes:
        """
        이미지 다운로드 (Supabase Storage URL에서 HTTP 다운로드)
        """
        try:
            logger.info(f"Downloading image from Supabase Storage: {url}")
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                logger.info(f"Successfully downloaded image: {len(response.content)} bytes")
                return response.content
        except Exception as e:
            logger.error(f"Failed to download image from {url}: {str(e)}")
            raise

    async def _save_transition_to_local(
        self,
        video_data: bytes,
        user_id: int,
        job_id: int,
        transition_name: str
    ) -> str:
        """전환 비디오를 로컬 파일 시스템에 임시 저장"""
        try:
            # 저장 경로 생성
            save_dir = Path("uploads") / "ai_video_transitions" / str(user_id) / str(job_id)
            save_dir.mkdir(parents=True, exist_ok=True)

            # 파일 저장
            file_path = save_dir / f"transition_{transition_name}.mp4"
            with open(file_path, 'wb') as f:
                f.write(video_data)

            # URL 반환 (FastAPI static files 경로)
            file_url = f"/uploads/ai_video_transitions/{user_id}/{job_id}/transition_{transition_name}.mp4"
            logger.info(f"Video saved to local filesystem: {file_url}")
            return file_url
        except Exception as e:
            logger.error(f"Failed to save video to local filesystem: {str(e)}")
            raise


class KlingVideoGenerationAgent:
    """
    Kling 2.1 Standard Video Generation Agent (via fal.ai)
    - fal.ai API를 통해 Kling 2.1 Standard 모델로 트랜지션 비디오 생성
    - Image-to-Video 방식 (First Frame → Motion → Last Frame)
    - 9:16 세로 비율 네이티브 지원
    - 생성 시간: 5초 영상 약 30초 (MiniMax 대비 33% 단축)
    - 비용: $0.25/5초 (MiniMax 대비 10% 절감)
    """

    def __init__(
        self,
        duration: str = "5",  # "5" or "10" seconds
        aspect_ratio: str = "9:16"
    ):
        self.duration = duration
        self.aspect_ratio = aspect_ratio
        self.api_key = os.getenv("FAL_KEY")
        self.model_id = "fal-ai/kling-video/v2.1/standard/image-to-video"

        if not self.api_key:
            raise ValueError("FAL_KEY not found in environment variables")

        # API Key 디버깅 (처음 10자만 표시)
        api_key_preview = self.api_key[:10] + "..." if len(self.api_key) > 10 else self.api_key
        logger.info(f"KlingVideoGenerationAgent initialized: model=Kling 2.1 Standard, duration={self.duration}s, aspect_ratio={self.aspect_ratio}")
        logger.info(f"FAL API Key loaded: {api_key_preview} (length: {len(self.api_key)})")

    async def generate_transition_videos(
        self,
        job: VideoGenerationJob,
        storyboard: List[Dict[str, Any]],
        images: List[Dict[str, str]],
        db: Session
    ) -> List[Dict[str, str]]:
        """
        이미지 간 트랜지션 비디오 생성 (Kling 2.1 via fal.ai)
        """
        try:
            # 스토리보드에서 AI 비디오 방식의 전환만 필터링 (minimax → kling으로 처리)
            transitions = [
                item['transition'] for item in storyboard
                if 'transition' in item and item['transition'].get('method') in ['minimax', 'kling']
            ]

            # Job 상태 업데이트
            job.status = "generating_videos"
            job.current_step = f"Generating {len(transitions)} Kling 2.1 transition videos"
            db.commit()

            logger.info(f"Starting Kling 2.1 video generation for job {job.id}: {len(transitions)} transitions")

            if not transitions:
                logger.info("No transitions needed - all transitions will use FFmpeg")
                job.generated_video_urls = []
                db.commit()
                return []

            generated_videos = []

            # 유효한 이미지만 필터링
            valid_images = [img for img in images if img.get('url')]

            if len(valid_images) < 2:
                raise ValueError("Need at least 2 images to create transition videos")

            # 이미지를 cut 번호로 매핑
            image_by_cut = {img['cut']: img for img in valid_images}

            # 전환 정보 준비 (from_cut, to_cut, 기타 정보 추출)
            transition_tasks = []
            for idx, transition_data in enumerate(transitions, 1):
                video_prompt = transition_data.get('video_prompt', '')
                effect = transition_data.get('effect', 'smooth_transition')
                duration = transition_data.get('duration', 5)
                reason = transition_data.get('reason', '')

                # 전환이 어느 컷 사이인지 추론
                transition_index = None
                for i, item in enumerate(storyboard):
                    if 'transition' in item and item['transition'] == transition_data:
                        transition_index = i
                        break

                if transition_index is None:
                    logger.warning(f"Could not find transition in storyboard, skipping")
                    continue

                # 앞뒤 컷 찾기
                from_cut = None
                to_cut = None

                for i in range(transition_index - 1, -1, -1):
                    if 'cut' in storyboard[i]:
                        from_cut = storyboard[i]['cut']
                        break

                for i in range(transition_index + 1, len(storyboard)):
                    if 'cut' in storyboard[i]:
                        to_cut = storyboard[i]['cut']
                        break

                if not from_cut or not to_cut:
                    logger.warning(f"Could not determine from/to cuts, skipping transition")
                    continue

                if from_cut not in image_by_cut or to_cut not in image_by_cut:
                    logger.warning(f"Images for transition {from_cut}-{to_cut} not found, skipping")
                    continue

                transition_name = f"{from_cut}-{to_cut}"
                start_image_url = image_by_cut[from_cut]['url']

                transition_tasks.append({
                    "idx": idx,
                    "transition_name": transition_name,
                    "from_cut": from_cut,
                    "to_cut": to_cut,
                    "image_url": start_image_url,
                    "video_prompt": video_prompt,
                    "effect": effect,
                    "duration": duration,
                    "reason": reason
                })

            # 2개씩 배치로 병렬 처리 (fal.ai 동시 2개 제한)
            batch_size = 2
            total_tasks = len(transition_tasks)

            async def generate_single_video(task_info):
                """단일 전환 영상 생성"""
                try:
                    video_url = await self._generate_video_with_retry(
                        image_url=task_info["image_url"],
                        prompt=task_info["video_prompt"],
                        job=job,
                        transition_name=task_info["transition_name"]
                    )

                    cost = 0.25 if self.duration == "5" else 0.50

                    return {
                        "transition": task_info["transition_name"],
                        "url": video_url,
                        "from_cut": task_info["from_cut"],
                        "to_cut": task_info["to_cut"],
                        "method": "kling",
                        "effect": task_info["effect"],
                        "duration": int(self.duration),
                        "reason": task_info["reason"],
                        "cost": cost
                    }
                except Exception as e:
                    logger.error(f"Error generating Kling 2.1 video {task_info['transition_name']}: {str(e)}")
                    return {
                        "transition": task_info["transition_name"],
                        "url": None,
                        "error": str(e),
                        "method": "kling",
                        "effect": task_info["effect"]
                    }

            for batch_start in range(0, total_tasks, batch_size):
                batch_end = min(batch_start + batch_size, total_tasks)
                batch = transition_tasks[batch_start:batch_end]
                batch_num = (batch_start // batch_size) + 1
                total_batches = (total_tasks + batch_size - 1) // batch_size

                logger.info(f"Processing Kling 2.1 batch {batch_num}/{total_batches}: {len(batch)} videos")
                job.current_step = f"Generating Kling 2.1 transitions batch {batch_num}/{total_batches}"
                db.commit()

                # 배치 내 병렬 처리
                batch_results = await asyncio.gather(*[
                    generate_single_video(task) for task in batch
                ])
                generated_videos.extend(batch_results)

                logger.info(f"Batch {batch_num}/{total_batches} completed")

            # 생성된 비디오 저장
            job.generated_video_urls = generated_videos
            db.commit()

            logger.info(f"Kling 2.1 video generation completed for job {job.id}: {len([v for v in generated_videos if v.get('url')])} successful")
            return generated_videos

        except Exception as e:
            logger.error(f"Error in Kling 2.1 video generation for job {job.id}: {str(e)}")
            job.status = "failed"
            job.error_message = f"Kling 2.1 video generation failed: {str(e)}"
            db.commit()
            raise

    async def _generate_video_with_retry(
        self,
        image_url: str,
        prompt: str,
        job: VideoGenerationJob,
        transition_name: str,
        max_retries: int = 3
    ) -> str:
        """
        fal.ai Kling API 호출 with retry
        """
        import fal_client

        base_delay = 2

        for attempt in range(max_retries):
            try:
                logger.info(f"Calling fal.ai Kling 2.1 API (attempt {attempt + 1}/{max_retries})")

                # fal.ai subscribe (동기 대기)
                result = await asyncio.to_thread(
                    fal_client.subscribe,
                    self.model_id,
                    arguments={
                        "prompt": prompt,
                        "image_url": image_url,
                        "duration": self.duration,
                        "aspect_ratio": self.aspect_ratio
                    }
                )

                # 결과에서 비디오 URL 추출
                video_data = result.get("video", {})
                fal_video_url = video_data.get("url")

                if not fal_video_url:
                    raise Exception(f"No video URL in fal.ai response: {result}")

                logger.info(f"Kling 2.1 video generated via fal.ai: {fal_video_url}")

                # 비디오를 다운로드하여 Supabase Storage에 저장
                video_url = await self._download_and_store_video(
                    fal_video_url=fal_video_url,
                    job=job,
                    transition_name=transition_name
                )

                return video_url

            except Exception as e:
                error_str = str(e)

                # Rate limit 에러인 경우 재시도
                if '429' in error_str or 'rate limit' in error_str.lower() or 'quota' in error_str.lower():
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limit detected (attempt {attempt + 1}/{max_retries}), retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Max retries ({max_retries}) reached, giving up")
                        raise
                else:
                    raise

    async def _download_and_store_video(
        self,
        fal_video_url: str,
        job: VideoGenerationJob,
        transition_name: str
    ) -> str:
        """
        fal.ai에서 생성된 비디오를 다운로드하여 Supabase Storage에 저장
        """
        # 비디오 다운로드
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(fal_video_url)

            if response.status_code != 200:
                raise Exception(f"Failed to download video from fal.ai: {response.status_code}")

            video_bytes = response.content

        # Supabase Storage에 저장
        from app.services.supabase_storage import get_storage_service
        storage = get_storage_service()

        file_path = f"{job.user_id}/{job.session_id}/{transition_name}.mp4"

        video_url = storage.upload_file(
            bucket="ai-video-transitions",
            file_path=file_path,
            file_data=video_bytes,
            content_type="video/mp4"
        )

        logger.info(f"Kling video saved to Supabase Storage: {video_url} ({len(video_bytes)} bytes)")

        return video_url


class VideoCompositionAgent:
    """
    Video Composition Agent
    - moviepy/ffmpeg를 사용하여 이미지와 트랜지션 비디오를 최종 비디오로 합성
    - AI 비디오 (Kling) + FFmpeg 기반 간단한 전환 효과 혼합 지원
    - 생성된 최종 비디오를 로컬 파일 시스템에 저장
    """

    def __init__(self):
        pass

    def _create_ffmpeg_transition(
        self,
        from_clip,
        to_clip,
        effect: str,
        duration: float
    ):
        """
        FFmpeg 기반 전환 효과 생성

        Args:
            from_clip: 시작 클립
            to_clip: 종료 클립
            effect: 전환 효과명 (dissolve, fade, zoom_in, zoom_out, pan_left, pan_right)
            duration: 전환 길이 (초)

        Returns:
            전환 클립
        """
        from moviepy import CompositeVideoClip, concatenate_videoclips

        try:
            if effect == "dissolve":
                # Crossfade 효과
                from_clip_end = from_clip.subclip(max(0, from_clip.duration - duration), from_clip.duration)
                to_clip_start = to_clip.subclip(0, min(duration, to_clip.duration))

                # Fade out과 fade in 합성
                from_clip_fading = from_clip_end.fadein(0).fadeout(duration)
                to_clip_fading = to_clip_start.fadein(duration).fadeout(0)

                transition = CompositeVideoClip([
                    from_clip_fading,
                    to_clip_fading.set_start(0)
                ]).set_duration(duration)

                return transition

            elif effect == "fade":
                # 검은 화면을 통한 페이드 전환
                from moviepy import ColorClip

                fade_duration = duration / 2
                from_clip_fade = from_clip.subclip(max(0, from_clip.duration - fade_duration), from_clip.duration).fadeout(fade_duration)
                to_clip_fade = to_clip.subclip(0, min(fade_duration, to_clip.duration)).fadein(fade_duration)

                # 두 클립을 연결
                transition = concatenate_videoclips([from_clip_fade, to_clip_fade], method="compose")
                return transition.set_duration(duration)

            elif effect == "zoom_in":
                # 줌인 효과 (첫 번째 클립의 마지막 프레임에서 시작)
                # 간단한 구현: to_clip을 서서히 크게 시작
                to_clip_short = to_clip.subclip(0, min(duration, to_clip.duration))

                def zoom_effect(get_frame, t):
                    # t: 0 to duration
                    scale = 0.8 + (0.2 * (t / duration))  # 0.8에서 1.0으로 확대
                    frame = get_frame(t)
                    from PIL import Image
                    import numpy as np

                    img = Image.fromarray(frame)
                    w, h = img.size
                    new_w, new_h = int(w * scale), int(h * scale)

                    # 리사이즈 후 중앙 크롭
                    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                    # 중앙 크롭하여 원래 크기로
                    left = (new_w - w) // 2
                    top = (new_h - h) // 2

                    if new_w < w or new_h < h:
                        # 패딩 필요
                        result = Image.new('RGB', (w, h), (0, 0, 0))
                        result.paste(img_resized, ((w - new_w) // 2, (h - new_h) // 2))
                        return np.array(result)
                    else:
                        img_cropped = img_resized.crop((left, top, left + w, top + h))
                        return np.array(img_cropped)

                # 간단하게 그냥 페이드인으로 대체 (복잡한 zoom 효과는 구현 어려움)
                return to_clip_short.fadein(duration * 0.3)

            elif effect == "zoom_out":
                # 줌아웃 효과
                to_clip_short = to_clip.subclip(0, min(duration, to_clip.duration))
                return to_clip_short.fadein(duration * 0.3)

            elif effect in ["pan_left", "pan_right"]:
                # 패닝 효과 (간단한 구현: 페이드 전환)
                to_clip_short = to_clip.subclip(0, min(duration, to_clip.duration))
                return to_clip_short.fadein(duration * 0.3)

            else:
                # 기본: 간단한 크로스페이드
                to_clip_short = to_clip.subclip(0, min(duration, to_clip.duration))
                return to_clip_short.fadein(min(0.5, duration))

        except Exception as e:
            logger.error(f"Error creating FFmpeg transition effect '{effect}': {str(e)}")
            # 폴백: 간단한 페이드인
            to_clip_short = to_clip.subclip(0, min(duration, to_clip.duration))
            return to_clip_short.fadein(0.5)

    async def compose_final_video(
        self,
        job: VideoGenerationJob,
        storyboard: List[Dict[str, Any]],
        images: List[Dict[str, str]],
        transition_videos: List[Dict[str, str]],
        db: Session
    ) -> str:
        """
        최종 비디오 합성 (AI 전환 + FFmpeg 전환 혼합)

        Args:
            job: VideoGenerationJob 인스턴스
            storyboard: 스토리보드 데이터 (컷과 전환이 혼합된 배열)
            images: 생성된 이미지 리스트
            transition_videos: 생성된 AI 트랜지션 비디오 리스트 (Kling)
            db: Database session

        Returns:
            str: 최종 비디오 URL
        """
        import tempfile
        import os
        from moviepy import (
            ImageClip,
            VideoFileClip,
            concatenate_videoclips,
            CompositeVideoClip
        )
        from PIL import Image
        import io

        try:
            # Job 상태 업데이트
            job.status = "composing"
            job.current_step = "Composing final video with mixed transitions"
            db.commit()

            logger.info(f"Starting video composition for job {job.id}")

            # 임시 디렉토리 생성
            temp_dir = tempfile.mkdtemp()
            logger.info(f"Created temp directory: {temp_dir}")

            # 스토리보드에서 컷과 전환 분리
            cuts = [item for item in storyboard if 'cut' in item]
            transitions_data = {}  # {index: transition_info}

            for i, item in enumerate(storyboard):
                if 'transition' in item:
                    transitions_data[i] = item['transition']

            logger.info(f"Storyboard: {len(cuts)} cuts, {len(transitions_data)} transitions")

            # 유효한 이미지만 필터링 및 매핑
            image_by_cut = {img['cut']: img for img in images if img.get('url')}

            if not image_by_cut:
                raise ValueError("No valid images to compose video")

            # AI 트랜지션 비디오 매핑 (Kling)
            ai_videos = {
                tv['transition']: tv
                for tv in transition_videos
                if tv.get('url')
            }

            logger.info(f"Processing {len(image_by_cut)} images, {len(ai_videos)} AI-generated transitions")

            clips = []
            image_clips_cache = {}  # 이미지 클립 캐시 (FFmpeg 전환에 재사용)

            # 스토리보드 순서대로 클립 생성
            for i, item in enumerate(storyboard):
                if 'cut' in item:
                    # 컷 처리
                    cut = item
                    cut_number = cut['cut']

                    if cut_number not in image_by_cut:
                        logger.warning(f"Image for cut {cut_number} not found, skipping")
                        continue

                    try:
                        # 이미지 다운로드
                        image_path = os.path.join(temp_dir, f"image_{cut_number}.jpg")
                        image_bytes = await self._download_file(image_by_cut[cut_number]['url'])

                        with open(image_path, 'wb') as f:
                            f.write(image_bytes)

                        # ImageClip 생성
                        # 컷 이미지는 키 프레임만 짧게 표시 (0.3초 고정)
                        duration = 0.3
                        image_clip = ImageClip(image_path, duration=duration)
                        clips.append(image_clip)

                        # 캐시에 저장 (FFmpeg 전환용)
                        image_clips_cache[cut_number] = image_clip

                        logger.info(f"Added image clip {cut_number} with duration {duration}s")

                    except Exception as e:
                        logger.error(f"Error processing image {cut_number}: {str(e)}")
                        continue

                elif 'transition' in item:
                    # 전환 처리
                    transition = item['transition']
                    method = transition.get('method', 'ffmpeg')
                    effect = transition.get('effect', 'dissolve')
                    duration = transition.get('duration', 1.0)

                    # 앞뒤 컷 찾기
                    from_cut = None
                    to_cut = None

                    for j in range(i - 1, -1, -1):
                        if 'cut' in storyboard[j]:
                            from_cut = storyboard[j]['cut']
                            break

                    for j in range(i + 1, len(storyboard)):
                        if 'cut' in storyboard[j]:
                            to_cut = storyboard[j]['cut']
                            break

                    if not from_cut or not to_cut:
                        logger.warning(f"Could not determine from/to cuts for transition, skipping")
                        continue

                    transition_key = f"{from_cut}-{to_cut}"

                    try:
                        if method in ["veo", "minimax", "kling"]:
                            # AI 생성 비디오 사용 (Kling)
                            if transition_key in ai_videos:
                                transition_path = os.path.join(temp_dir, f"ai_transition_{transition_key}.mp4")
                                video_bytes = await self._download_file(ai_videos[transition_key]['url'])

                                with open(transition_path, 'wb') as f:
                                    f.write(video_bytes)

                                transition_clip = VideoFileClip(transition_path)
                                clips.append(transition_clip)

                                logger.info(f"Added {method.upper()} transition {transition_key} ({effect})")
                            else:
                                logger.warning(f"{method.upper()} video for {transition_key} not found, falling back to FFmpeg")
                                # FFmpeg 폴백
                                if from_cut in image_clips_cache and to_cut in image_clips_cache:
                                    ffmpeg_transition = self._create_ffmpeg_transition(
                                        image_clips_cache[from_cut],
                                        image_clips_cache[to_cut],
                                        effect,
                                        duration
                                    )
                                    clips.append(ffmpeg_transition)
                                    logger.info(f"Added FFmpeg fallback transition {transition_key} ({effect})")

                        elif method == "ffmpeg":
                            # FFmpeg 전환 생성
                            if from_cut in image_clips_cache and to_cut in image_clips_cache:
                                ffmpeg_transition = self._create_ffmpeg_transition(
                                    image_clips_cache[from_cut],
                                    image_clips_cache[to_cut],
                                    effect,
                                    duration
                                )
                                clips.append(ffmpeg_transition)
                                logger.info(f"Added FFmpeg transition {transition_key} ({effect})")
                            else:
                                logger.warning(f"Image clips for {transition_key} not found in cache")

                        else:
                            # 예상치 못한 method 값 - FFmpeg로 폴백
                            logger.warning(f"Unknown transition method '{method}' for {transition_key}, falling back to FFmpeg")
                            if from_cut in image_clips_cache and to_cut in image_clips_cache:
                                ffmpeg_transition = self._create_ffmpeg_transition(
                                    image_clips_cache[from_cut],
                                    image_clips_cache[to_cut],
                                    effect,
                                    duration
                                )
                                clips.append(ffmpeg_transition)
                                logger.info(f"Added FFmpeg fallback transition {transition_key} (unknown method: {method})")

                    except Exception as e:
                        logger.error(f"Error processing transition {transition_key}: {str(e)}")
                        # 전환 실패해도 계속 진행

            if not clips:
                raise ValueError("No clips to compose")

            # Job 상태 업데이트
            job.current_step = f"Concatenating {len(clips)} clips"
            db.commit()

            # 모든 클립 합성
            logger.info(f"Concatenating {len(clips)} clips...")
            final_video = concatenate_videoclips(clips, method="compose")

            # 최종 비디오 저장
            output_path = os.path.join(temp_dir, f"final_video_{job.id}.mp4")
            logger.info(f"Writing final video to {output_path}")

            job.current_step = "Rendering final video"
            db.commit()

            final_video.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio=False,
                preset='medium',
                threads=4
            )

            logger.info(f"Final video rendered: {output_path}")

            # Supabase Storage에 업로드
            job.current_step = "Uploading final video to Supabase Storage"
            db.commit()

            with open(output_path, 'rb') as f:
                video_url = await self._upload_final_to_supabase(
                    f.read(),
                    job.user_id,
                    job.id,
                    job.session_id
                )

            # 임시 파일 정리
            logger.info("Cleaning up temporary files...")
            final_video.close()
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass

            # 임시 디렉토리 삭제
            import shutil
            shutil.rmtree(temp_dir)
            logger.info("Temporary files cleaned up")

            # Job 업데이트
            from sqlalchemy import func
            job.final_video_url = video_url
            job.status = "completed"
            job.current_step = "Video generation completed"
            job.completed_at = func.now()
            db.commit()

            # GeneratedVideo 레코드 생성 (완료된 비디오 결과 저장)
            from app import models
            generated_video = models.GeneratedVideo(
                session_id=job.session_id,
                user_id=job.user_id,
                final_video_url=video_url,
                product_name=job.product_name,
                tier=job.tier,
                duration_seconds=job.duration_seconds
            )
            db.add(generated_video)
            db.commit()
            logger.info(f"GeneratedVideo record created for session {job.session_id}")

            logger.info(f"Video composition completed for job {job.id}: {video_url}")
            return video_url

        except Exception as e:
            logger.error(f"Error in video composition for job {job.id}: {str(e)}")
            job.status = "failed"
            job.error_message = f"Video composition failed: {str(e)}"
            db.commit()

            # 임시 디렉토리 정리 시도
            try:
                if 'temp_dir' in locals():
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

            raise

    async def _download_file(self, url: str) -> bytes:
        """
        파일 다운로드 (로컬 파일 또는 HTTP)
        - 상대 경로(/uploads/...)인 경우: 로컬 파일 시스템에서 직접 읽기
        - 절대 URL(http://, https://)인 경우: HTTP로 다운로드
        """
        # 상대 경로인 경우 로컬 파일 시스템에서 직접 읽기
        if url.startswith('/uploads/'):
            try:
                # /uploads/ 경로를 실제 파일 시스템 경로로 변환
                # 파일 위치 기준 절대 경로 사용 (환경 독립적)
                # backend/app/services/ → backend/app/ → backend/ → 프로젝트루트/
                file_path = Path(__file__).parent.parent.parent / url.lstrip('/')

                logger.info(f"Reading file from local filesystem: {file_path}")

                with open(file_path, 'rb') as f:
                    file_data = f.read()

                logger.info(f"Successfully read local file: {len(file_data)} bytes")
                return file_data

            except Exception as e:
                logger.error(f"Failed to read local file {file_path}: {str(e)}")
                raise
        else:
            # 절대 URL인 경우 HTTP로 다운로드
            try:
                logger.info(f"Downloading file from URL: {url}")
                async with httpx.AsyncClient() as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    logger.info(f"Successfully downloaded file: {len(response.content)} bytes")
                    return response.content
            except Exception as e:
                logger.error(f"Failed to download file from {url}: {str(e)}")
                raise

    async def _upload_final_to_supabase(
        self,
        video_data: bytes,
        user_id: int,
        job_id: int,
        session_id: str
    ) -> str:
        """최종 비디오를 Supabase Storage에 저장"""
        try:
            from app.services.supabase_storage import get_storage_service
            storage = get_storage_service()

            # 파일 경로 생성
            file_path = f"{user_id}/{session_id}.mp4"

            # Supabase Storage에 업로드
            file_url = storage.upload_file(
                bucket="ai-video-finals",
                file_path=file_path,
                file_data=video_data,
                content_type="video/mp4"
            )

            logger.info(f"Final video saved to Supabase Storage: {file_url}")
            return file_url
        except Exception as e:
            logger.error(f"Failed to save final video to Supabase Storage: {str(e)}")
            raise


# 비디오 생성 파이프라인 실행 함수
async def run_video_generation_pipeline(job_id: int, db: Session):
    """
    비디오 생성 파이프라인 실행 (백그라운드 작업)

    1. Master Planning Agent: 스토리보드 생성
    2. Image Generation: 각 컷의 이미지 생성
    3. Video Generation: 컷 사이 트랜지션 비디오 생성
    4. Video Composition: 최종 비디오 합성
    """
    try:
        # Job 조회
        job = db.query(VideoGenerationJob).filter(VideoGenerationJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        # User 조회
        user = db.query(User).filter(User.id == job.user_id).first()
        if not user:
            logger.error(f"User {job.user_id} not found for job {job_id}")
            job.status = "failed"
            job.error_message = "User not found"
            db.commit()
            return

        # BrandAnalysis 조회 (있는 경우)
        brand_analysis = db.query(BrandAnalysis).filter(
            BrandAnalysis.user_id == user.id
        ).first()

        # 1. Master Planning Agent 실행
        logger.info(f"Step 1/4: Running Master Planning Agent for job {job_id}")
        planning_agent = MasterPlanningAgent()
        storyboard_result = await planning_agent.analyze_and_plan(job, user, brand_analysis, db)

        # 새 구조: {shared_visual_context: {...}, storyboard: [...]}
        storyboard = storyboard_result.get("storyboard", storyboard_result if isinstance(storyboard_result, list) else [])

        # 2. Image Generation
        cuts = [item for item in storyboard if 'cut' in item]
        logger.info(f"Step 2/4: Generating images for {len(cuts)} cuts")
        image_agent = ImageGenerationAgent()
        images = await image_agent.generate_images(job, storyboard, db)

        # 3. Video Generation (Kling 2.1 Standard transitions via fal.ai)
        logger.info(f"Step 3/4: Generating Kling 2.1 transition videos")
        video_agent = KlingVideoGenerationAgent()  # ← Kling 2.1 Standard via fal.ai
        videos = await video_agent.generate_transition_videos(job, storyboard, images, db)

        # 4. Video Composition (mixed: Kling + FFmpeg transitions)
        logger.info(f"Step 4/4: Composing final video with mixed transitions")
        composition_agent = VideoCompositionAgent()
        final_video_url = await composition_agent.compose_final_video(
            job, storyboard, images, videos, db
        )

        logger.info(f"Video generation pipeline completed for job {job_id}: {final_video_url}")

    except Exception as e:
        logger.error(f"Error in video generation pipeline for job {job_id}: {str(e)}")
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
