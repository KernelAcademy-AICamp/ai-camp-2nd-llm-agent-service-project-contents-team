"""
AI 비디오 생성 서비스
- Master Planning Agent: 제품 분석 + 스토리보드 생성
- Image Generation: Vertex AI Gemini 2.5 Flash로 각 컷 이미지 생성
- Video Generation: Veo 3.1로 컷 사이 트랜지션 비디오 생성
- Video Composition: moviepy/ffmpeg로 최종 비디오 합성
"""
import os
import json
import base64
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import anthropic
import google.generativeai as genai
import vertexai
from vertexai.generative_models import GenerativeModel as VertexGenerativeModel, Part
from sqlalchemy.orm import Session

from ..models import VideoGenerationJob, User, BrandAnalysis
from ..logger import get_logger

logger = get_logger(__name__)

# Google Gemini 설정 (기존 코드와의 호환성 유지)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Vertex AI 초기화 (GOOGLE_APPLICATION_CREDENTIALS 사용)
try:
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
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
    - 제품 이미지와 정보를 분석
    - 브랜드 분석 데이터 활용
    - 스토리보드 생성 (컷 수, 각 컷의 장면 설명, 이미지 프롬프트)
    """

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model

    async def analyze_and_plan(
        self,
        job: VideoGenerationJob,
        user: User,
        brand_analysis: Optional[BrandAnalysis],
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        제품을 분석하고 스토리보드 생성

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
            # Job 상태 업데이트
            job.status = "planning"
            job.current_step = "Analyzing product and generating storyboard"
            db.commit()

            logger.info(f"Starting Master Planning Agent for job {job.id}")

            # 제품 이미지 다운로드 및 base64 인코딩
            image_data = await self._download_and_encode_image(job.uploaded_image_url)

            # 브랜드 정보 준비
            brand_context = self._prepare_brand_context(user, brand_analysis)

            # Claude에게 스토리보드 생성 요청
            storyboard = await self._generate_storyboard(
                product_name=job.product_name,
                product_description=job.product_description,
                cut_count=job.cut_count,
                duration_seconds=job.duration_seconds,
                image_data=image_data,
                brand_context=brand_context
            )

            # 스토리보드 저장
            job.storyboard = storyboard
            db.commit()

            logger.info(f"Storyboard generated for job {job.id}: {len(storyboard)} cuts")
            return storyboard

        except Exception as e:
            logger.error(f"Error in Master Planning Agent for job {job.id}: {str(e)}")
            job.status = "failed"
            job.error_message = f"Planning failed: {str(e)}"
            db.commit()
            raise

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

    def _prepare_brand_context(
        self,
        user: User,
        brand_analysis: Optional[BrandAnalysis]
    ) -> str:
        """브랜드 분석 데이터를 컨텍스트로 준비"""
        context_parts = []

        # 사용자 기본 정보
        if user.brand_name:
            context_parts.append(f"브랜드명: {user.brand_name}")
        if user.business_type:
            context_parts.append(f"업종: {user.business_type}")
        if user.business_description:
            context_parts.append(f"비즈니스 설명: {user.business_description}")

        # 브랜드 분석 정보
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

        # 각 컷의 평균 길이 계산
        avg_duration_per_cut = duration_seconds / cut_count

        # 프롬프트 구성
        system_prompt = f"""당신은 제품 마케팅 비디오의 스토리보드를 생성하는 전문가입니다.

주어진 제품 이미지와 정보를 분석하여, {cut_count}개의 컷으로 구성된 약 {duration_seconds}초 길이의 마케팅 비디오 스토리보드를 생성해주세요.

**중요: 비용 최적화를 고려하여 컷 정보와 전환 정보를 모두 포함해주세요.**

각 요소의 구조:

**컷 정보:**
1. cut: 컷 번호 (1부터 시작)
2. scene_description: 장면 설명 (한국어, 2-3문장)
3. image_prompt: 이미지 생성 AI 프롬프트 (영어, 상세하게)
4. duration: 컷 길이 (초, 평균 {avg_duration_per_cut:.1f}초)
5. is_hero_shot: true/false
   - 첫 컷, 마지막 컷, 가장 중요한 핵심 컷은 true
   - 나머지는 false
6. resolution: "1080p" (hero shot) 또는 "720p" (일반)

**전환 정보 (컷과 컷 사이):**
1. method: "veo" 또는 "ffmpeg"
   - **veo**: 역동적 움직임 필요 (줌인/아웃, 회전, 복잡한 카메라 무브)
   - **ffmpeg**: 심플한 전환 충분 (디졸브, 페이드, 단순 패닝)
   - **비용 최적화**: 전체 전환의 30-40%만 veo 사용 (가장 임팩트 있는 부분)
2. effect: 전환 효과명
   - veo: "dynamic_zoom_in", "dynamic_zoom_out", "dynamic_pan", "complex_transition"
   - ffmpeg: "dissolve", "fade", "zoom_in", "zoom_out", "pan_left", "pan_right"
3. duration: 전환 길이 (veo: 4-6초, ffmpeg: 0.5-2초)
4. reason: 이 방식을 선택한 이유 (한 줄)

**스토리보드 작성 가이드라인:**
- 첫 번째 컷: 임팩트 있는 오프닝 (hero shot)
- 중간 컷들: 제품 특징, 사용 시나리오, 혜택
- 마지막 컷: CTA 또는 브랜드 메시지 (hero shot)
- 첫 전환과 마지막 전환은 강렬하게 (veo 추천)
- 중간 전환 중 비슷한 분위기면 ffmpeg 사용
- 전체 흐름의 리듬감 유지
- image_prompt는 조명, 각도, 분위기, 색감 포함하여 상세하게

**응답 형식 (JSON 배열):**
[
  {{
    "cut": 1,
    "scene_description": "...",
    "image_prompt": "...",
    "duration": 4.0,
    "is_hero_shot": true,
    "resolution": "1080p"
  }},
  {{
    "transition": {{
      "method": "veo",
      "effect": "dynamic_zoom_out",
      "duration": 4.0,
      "reason": "제품 디테일에서 전체로, 강렬한 전환 필요"
    }}
  }},
  {{
    "cut": 2,
    "scene_description": "...",
    "image_prompt": "...",
    "duration": 4.0,
    "is_hero_shot": false,
    "resolution": "720p"
  }},
  ...
]

다른 설명 없이 JSON 배열만 반환해주세요."""

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

            storyboard = json.loads(response_text)

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

    def __init__(self, model: str = "gemini-2.5-flash-image"):
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

            for i, cut in enumerate(cuts, 1):
                try:
                    cut_number = cut['cut']
                    resolution = cut.get('resolution', '720p')
                    is_hero_shot = cut.get('is_hero_shot', False)

                    logger.info(f"Generating image for cut {cut_number}/{len(cuts)}: {cut['image_prompt'][:50]}... (resolution: {resolution}, hero: {is_hero_shot})")

                    # Job 상태 업데이트
                    job.current_step = f"Generating image {i}/{len(cuts)}"
                    db.commit()

                    # Gemini 2.5 Flash Image로 이미지 생성
                    # TODO: 해상도 최적화 지원 시 resolution 파라미터 활용
                    image_bytes = await self._generate_with_gemini_image(cut['image_prompt'])

                    if not image_bytes:
                        raise ValueError(f"Failed to generate image for cut {cut_number}")

                    # 이미지를 Cloudinary에 업로드
                    image_url = await self._upload_to_cloudinary(
                        image_bytes,
                        job.user_id,
                        job.id,
                        cut_number
                    )

                    generated_images.append({
                        "cut": cut_number,
                        "url": image_url,
                        "prompt": cut['image_prompt'],
                        "resolution": resolution,
                        "is_hero_shot": is_hero_shot
                    })

                    logger.info(f"Image generated and uploaded for cut {cut_number}: {image_url}")

                    # 쿼터 초과 방지를 위한 요청 간격 추가
                    if i < len(cuts):
                        wait_time = 3  # 3초 대기
                        logger.info(f"다음 이미지 생성 전 {wait_time}초 대기 중... (쿼터 최적화)")
                        await asyncio.sleep(wait_time)

                except Exception as e:
                    logger.error(f"Error generating image for cut {cut.get('cut', i)}: {str(e)}")
                    # 일부 이미지 생성 실패해도 계속 진행
                    generated_images.append({
                        "cut": cut.get('cut', i),
                        "url": None,
                        "error": str(e),
                        "prompt": cut.get('image_prompt', ''),
                        "resolution": cut.get('resolution', '720p'),
                        "is_hero_shot": cut.get('is_hero_shot', False)
                    })

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

    async def _generate_with_gemini_image(self, prompt: str) -> bytes:
        """
        Vertex AI Gemini 2.5 Flash Image 모델을 사용하여 이미지 생성
        Exponential backoff 재시도 로직 포함 (429 쿼터 에러 대응)
        """
        import base64
        from vertexai.generative_models import GenerativeModel
        from google.api_core.exceptions import ResourceExhausted, TooManyRequests

        max_retries = 5
        base_delay = 2  # 초기 대기 시간 (초)

        for attempt in range(max_retries):
            try:
                logger.info(f"Vertex AI Gemini 2.5 Flash Image로 이미지 생성 중... (시도 {attempt + 1}/{max_retries}, 프롬프트: {prompt[:50]}...)")

                # Vertex AI Gemini 모델 초기화
                model = GenerativeModel("gemini-2.5-flash-image")

                # 이미지 생성 요청
                response = model.generate_content([
                    f"Generate an image with 9:16 aspect ratio (vertical, for short-form video): {prompt}"
                ])

                # 응답에서 이미지 추출
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]

                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            # inline_data 또는 inlineData 형식 확인
                            inline_data = getattr(part, 'inline_data', None) or getattr(part, 'inlineData', None)

                            if inline_data:
                                # Vertex AI는 inline_data.data에 bytes 형식으로 저장
                                if hasattr(inline_data, 'data'):
                                    image_bytes = inline_data.data
                                    mime_type = getattr(inline_data, 'mime_type', 'image/png')

                                    logger.info(f"✅ 이미지 생성 완료 (시도 {attempt + 1}, MIME type: {mime_type}, size: {len(image_bytes)} bytes)")
                                    return image_bytes
                                # 또는 Base64 문자열로 저장되어 있을 수도 있음
                                elif isinstance(inline_data.get('data') if hasattr(inline_data, 'get') else None, str):
                                    image_data_base64 = inline_data['data']
                                    image_bytes = base64.b64decode(image_data_base64)

                                    logger.info(f"✅ 이미지 생성 완료 (시도 {attempt + 1}, Base64 디코딩, size: {len(image_bytes)} bytes)")
                                    return image_bytes

                # 이미지를 찾지 못한 경우
                logger.error(f"Vertex AI Gemini 응답에서 이미지를 찾지 못함: {response}")
                raise ValueError("Vertex AI Gemini로부터 이미지를 추출하지 못했습니다.")

            except (ResourceExhausted, TooManyRequests) as e:
                # 429 쿼터 에러 발생 시 exponential backoff 재시도
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)  # 2, 4, 8, 16, 32초
                    logger.warning(f"⚠️  429 쿼터 에러 발생 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                    logger.info(f"🔄 {wait_time}초 후 재시도... (exponential backoff)")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ 최대 재시도 횟수({max_retries})에 도달. 이미지 생성 실패: {str(e)}")
                    raise

            except Exception as e:
                # 429 외의 에러는 즉시 실패
                logger.error(f"❌ Vertex AI Gemini 2.5 Flash Image 생성 실패: {str(e)}")
                raise

    async def _upload_to_cloudinary(
        self,
        image_data: bytes,
        user_id: int,
        job_id: int,
        cut_number: int
    ) -> str:
        """이미지를 로컬 파일 시스템에 PNG로 저장"""
        try:
            # 저장 경로 생성
            save_dir = Path("uploads") / "ai_video_images" / str(user_id) / str(job_id)
            save_dir.mkdir(parents=True, exist_ok=True)

            # 파일 저장 (PNG 형식)
            file_path = save_dir / f"cut_{cut_number}.png"
            with open(file_path, 'wb') as f:
                f.write(image_data)

            # URL 반환 (FastAPI static files 경로)
            file_url = f"/uploads/ai_video_images/{user_id}/{job_id}/cut_{cut_number}.png"
            logger.info(f"Image saved to local filesystem as PNG: {file_url}")
            return file_url
        except Exception as e:
            logger.error(f"Failed to save image to local filesystem: {str(e)}")
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
            # Vertex AI 모델 사용
            veo_model = VertexGenerativeModel(self.model)
            logger.info(f"Using Vertex AI Veo model: {self.model}")

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

                    # 이미지 다운로드
                    from_image_data = await self._download_image(from_image['url'])
                    to_image_data = await self._download_image(to_image['url'])

                    # Veo 3.1 API 호출 (Part 객체 사용)
                    response = veo_model.generate_content([
                        Part.from_data(data=from_image_data, mime_type="image/png"),
                        Part.from_data(data=to_image_data, mime_type="image/png"),
                        video_prompt
                    ])

                    # 비디오 데이터 추출
                    if not response.candidates or not response.candidates[0].content.parts:
                        raise ValueError(f"No video generated for transition {transition_name}")

                    video_data = response.candidates[0].content.parts[0].inline_data.data

                    # 비디오를 Cloudinary에 업로드
                    video_url = await self._upload_to_cloudinary(
                        base64.b64decode(video_data),
                        job.user_id,
                        job.id,
                        transition_name
                    )

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
        이미지 다운로드 (로컬 파일 또는 HTTP)
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

                logger.info(f"Reading image from local filesystem: {file_path}")

                with open(file_path, 'rb') as f:
                    image_data = f.read()

                logger.info(f"Successfully read local image: {len(image_data)} bytes")
                return image_data

            except Exception as e:
                logger.error(f"Failed to read local image {file_path}: {str(e)}")
                raise
        else:
            # 절대 URL인 경우 HTTP로 다운로드
            try:
                logger.info(f"Downloading image from URL: {url}")
                async with httpx.AsyncClient() as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    logger.info(f"Successfully downloaded image: {len(response.content)} bytes")
                    return response.content
            except Exception as e:
                logger.error(f"Failed to download image from {url}: {str(e)}")
                raise

    async def _upload_to_cloudinary(
        self,
        video_data: bytes,
        user_id: int,
        job_id: int,
        transition_name: str
    ) -> str:
        """비디오를 로컬 파일 시스템에 저장"""
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


class VideoCompositionAgent:
    """
    Video Composition Agent
    - moviepy/ffmpeg를 사용하여 이미지와 트랜지션 비디오를 최종 비디오로 합성
    - FFmpeg 기반 간단한 전환 효과 (dissolve, fade, zoom, pan) 지원
    - 생성된 최종 비디오를 Cloudinary에 업로드
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
        최종 비디오 합성 (Veo 전환 + FFmpeg 전환 혼합)

        Args:
            job: VideoGenerationJob 인스턴스
            storyboard: 스토리보드 데이터 (컷과 전환이 혼합된 배열)
            images: 생성된 이미지 리스트
            transition_videos: 생성된 Veo 트랜지션 비디오 리스트
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

            # Veo 트랜지션 비디오 매핑
            veo_videos = {
                tv['transition']: tv
                for tv in transition_videos
                if tv.get('url')
            }

            logger.info(f"Processing {len(image_by_cut)} images, {len(veo_videos)} Veo transitions")

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
                        duration = cut.get('duration', 4.0)
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
                        if method == "veo":
                            # Veo 비디오 사용
                            if transition_key in veo_videos:
                                transition_path = os.path.join(temp_dir, f"veo_transition_{transition_key}.mp4")
                                video_bytes = await self._download_file(veo_videos[transition_key]['url'])

                                with open(transition_path, 'wb') as f:
                                    f.write(video_bytes)

                                transition_clip = VideoFileClip(transition_path)
                                clips.append(transition_clip)

                                logger.info(f"Added Veo transition {transition_key} ({effect})")
                            else:
                                logger.warning(f"Veo video for {transition_key} not found, falling back to FFmpeg")
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

            # Cloudinary에 업로드
            job.current_step = "Uploading final video to cloud storage"
            db.commit()

            with open(output_path, 'rb') as f:
                video_url = await self._upload_to_cloudinary(
                    f.read(),
                    job.user_id,
                    job.id
                )

            # 썸네일 생성 및 업로드
            thumbnail_url = await self._generate_and_upload_thumbnail(
                final_video,
                temp_dir,
                job.user_id,
                job.id
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
            job.thumbnail_url = thumbnail_url
            job.status = "completed"
            job.current_step = "Video generation completed"
            job.completed_at = func.now()
            db.commit()

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

    async def _upload_to_cloudinary(
        self,
        video_data: bytes,
        user_id: int,
        job_id: int
    ) -> str:
        """최종 비디오를 로컬 파일 시스템에 저장"""
        try:
            # 저장 경로 생성
            save_dir = Path("uploads") / "ai_video_final" / str(user_id)
            save_dir.mkdir(parents=True, exist_ok=True)

            # 파일 저장
            file_path = save_dir / f"video_{job_id}.mp4"
            with open(file_path, 'wb') as f:
                f.write(video_data)

            # URL 반환 (FastAPI static files 경로)
            file_url = f"/uploads/ai_video_final/{user_id}/video_{job_id}.mp4"
            logger.info(f"Final video saved to local filesystem: {file_url}")
            return file_url
        except Exception as e:
            logger.error(f"Failed to save final video to local filesystem: {str(e)}")
            raise

    async def _generate_and_upload_thumbnail(
        self,
        video_clip,
        temp_dir: str,
        user_id: int,
        job_id: int
    ) -> str:
        """비디오에서 썸네일 생성 및 로컬 파일 시스템에 저장"""
        try:
            # 저장 경로 생성
            save_dir = Path("uploads") / "ai_video_thumbnails" / str(user_id)
            save_dir.mkdir(parents=True, exist_ok=True)

            # 첫 번째 프레임을 썸네일로 저장
            thumbnail_path = save_dir / f"thumbnail_{job_id}.jpg"
            video_clip.save_frame(str(thumbnail_path), t=0)

            # URL 반환 (FastAPI static files 경로)
            file_url = f"/uploads/ai_video_thumbnails/{user_id}/thumbnail_{job_id}.jpg"
            logger.info(f"Thumbnail saved to local filesystem: {file_url}")
            return file_url
        except Exception as e:
            logger.error(f"Failed to generate/save thumbnail: {str(e)}")
            return None


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
        storyboard = await planning_agent.analyze_and_plan(job, user, brand_analysis, db)

        # 2. Image Generation
        cuts = [item for item in storyboard if 'cut' in item]
        logger.info(f"Step 2/4: Generating images for {len(cuts)} cuts")
        image_agent = ImageGenerationAgent()
        images = await image_agent.generate_images(job, storyboard, db)

        # 3. Video Generation (Veo transitions only)
        logger.info(f"Step 3/4: Generating Veo transition videos")
        video_agent = VideoGenerationAgent()
        videos = await video_agent.generate_transition_videos(job, storyboard, images, db)

        # 4. Video Composition (mixed: Veo + FFmpeg transitions)
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
