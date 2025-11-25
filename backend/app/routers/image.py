from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os
import base64
from typing import Optional
import google.generativeai as genai
from ..logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["image"]
)


class ImageGenerateRequest(BaseModel):
    prompt: str
    model: str = "nanovana"
    referenceImage: Optional[str] = None  # Base64 encoded image for image-to-image


class ImageGenerateResponse(BaseModel):
    success: bool
    imageUrl: str
    optimizedPrompt: Optional[str] = None
    usedClaudeOptimization: bool = False
    usedNanovanaAPI: bool = False
    usedWhiskAPI: bool = False


async def optimize_prompt_with_gemini(user_prompt: str) -> str:
    """Gemini를 사용하여 프롬프트 최적화"""
    try:
        google_api_key = os.getenv('REACT_APP_GEMINI_API_KEY')
        if not google_api_key:
            return user_prompt

        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        optimization_prompt = f"""You are an expert at creating detailed, high-quality image generation prompts for Stable Diffusion.

User's prompt: "{user_prompt}"

Transform this into an optimized Stable Diffusion prompt with style, lighting, quality, and composition. Under 75 words. English only. Return ONLY the optimized prompt."""

        response = model.generate_content(optimization_prompt)
        return response.text.strip()
    except Exception as e:
        logger.warning(f"Gemini 프롬프트 최적화 실패: {e}")
        return user_prompt


@router.post("/generate-image", response_model=ImageGenerateResponse)
async def generate_image(request: ImageGenerateRequest):
    """
    이미지 생성 엔드포인트
    - model: 'whisk' (Imagen 3), 'nanovana' (Gemini 2.0 Flash) 또는 'gemini' (Stable Diffusion 2.1)
    """
    if not request.prompt:
        raise HTTPException(status_code=400, detail="프롬프트가 필요합니다.")

    try:
        optimized_prompt = request.prompt
        used_claude_optimization = False
        used_nanovana_api = False
        used_whisk_api = False
        image_url = None

        # Whisk AI (Pollinations - 무료, API 키 불필요)
        if request.model == "whisk":
            logger.info(f"Whisk AI 이미지 생성 시작")
            logger.debug(f"프롬프트: {request.prompt}")

            # 한글 프롬프트를 영어로 번역 (Gemini 사용)
            translated_prompt = request.prompt
            google_api_key = os.getenv('REACT_APP_GEMINI_API_KEY')
            if google_api_key:
                try:
                    # 한글이 포함되어 있는지 확인
                    import re
                    if re.search(r'[가-힣]', request.prompt):
                        logger.info("한글 프롬프트 감지 - 영어로 번역 중...")
                        genai.configure(api_key=google_api_key)
                        model = genai.GenerativeModel('gemini-2.0-flash-exp')
                        translation_response = model.generate_content(
                            f"Translate this Korean text to English for an image generation prompt. Only return the English translation, nothing else:\n\n{request.prompt}"
                        )
                        translated_prompt = translation_response.text.strip()
                        logger.info(f"번역된 프롬프트: {translated_prompt}")
                except Exception as e:
                    logger.warning(f"번역 실패 (원본 프롬프트 사용): {e}")

            # URL 인코딩된 프롬프트
            import urllib.parse
            encoded_prompt = urllib.parse.quote(translated_prompt)
            logger.debug(f"인코딩된 프롬프트: {encoded_prompt}")

            # Pollinations AI는 GET 요청으로 이미지를 직접 반환합니다
            # enhance=false로 설정하여 사용자의 정확한 프롬프트를 사용합니다
            image_generation_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&nologo=true&enhance=false"

            async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
                response = await client.get(image_generation_url)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Whisk AI (Pollinations) 오류: 상태 코드 {response.status_code}"
                )

            # 이미지를 base64로 인코딩
            image_data = base64.b64encode(response.content).decode('utf-8')
            image_url = f"data:image/png;base64,{image_data}"
            used_whisk_api = True
            logger.info("Whisk AI 이미지 생성 완료")

        # Nanovana (Gemini 2.5 Flash Image with Thinking)
        elif request.model == "nanovana":
            google_api_key = os.getenv('REACT_APP_GEMINI_API_KEY')
            if not google_api_key:
                raise HTTPException(
                    status_code=500,
                    detail="Google API 키가 필요합니다. (Gemini 2.5 Flash Image)"
                )

            # 레퍼런스 이미지가 있는지 확인
            if request.referenceImage:
                logger.info("Nanovana (Gemini 2.5 Flash) Image-to-Image 생성 시작")
                logger.debug(f"프롬프트: {request.prompt}")
                logger.debug("레퍼런스 이미지 사용")

                # Base64에서 data:image/...;base64, 접두사 제거
                image_data = request.referenceImage
                if ',' in image_data:
                    image_data = image_data.split(',')[1]

                # 요청에 레퍼런스 이미지 포함
                request_body = {
                    "contents": [{
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": image_data
                                }
                            },
                            {
                                "text": f"Based on this reference image, generate a new image: {request.prompt}"
                            }
                        ]
                    }]
                }
            else:
                logger.info("Nanovana (Gemini 2.5 Flash) Text-to-Image 생성 시작")
                logger.debug(f"프롬프트: {request.prompt}")

                # 텍스트만 사용
                request_body = {
                    "contents": [{
                        "parts": [{
                            "text": f"Generate an image: {request.prompt}"
                        }]
                    }]
                }

            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={google_api_key}",
                    json=request_body,
                    headers={"Content-Type": "application/json"}
                )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Gemini API 오류: {response.text}"
                )

            data = response.json()

            # 디버깅: API 응답 구조 확인
            logger.debug(f"Gemini API 응답 구조: {list(data.keys())}")
            if data.get("candidates"):
                logger.debug(f"Candidates 수: {len(data['candidates'])}")
                if len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    logger.debug(f"첫 번째 candidate 키: {list(candidate.keys())}")
                    if candidate.get("content"):
                        logger.debug(f"Content 키: {list(candidate['content'].keys())}")
                        if candidate["content"].get("parts"):
                            logger.debug(f"Parts 수: {len(candidate['content']['parts'])}")
                            for i, part in enumerate(candidate["content"]["parts"]):
                                logger.debug(f"Part {i} 키: {list(part.keys())}")

            # 응답에서 이미지 추출
            if data.get("candidates") and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]

                if candidate.get("content") and candidate["content"].get("parts"):
                    for part in candidate["content"]["parts"]:
                        # Gemini API는 camelCase를 사용 (inlineData)
                        if part.get("inlineData") and part["inlineData"].get("data"):
                            mime_type = part["inlineData"].get("mimeType", "image/png")
                            image_data = part["inlineData"]["data"]
                            image_url = f"data:{mime_type};base64,{image_data}"
                            break

                if not image_url:
                    logger.error(f"Gemini API 응답: {data}")
                    raise HTTPException(
                        status_code=500,
                        detail="Gemini API로부터 이미지를 추출하지 못했습니다."
                    )
            else:
                logger.error(f"Gemini API 응답: {data}")
                raise HTTPException(
                    status_code=500,
                    detail="Gemini API로부터 유효한 응답을 받지 못했습니다."
                )

            used_nanovana_api = True
            logger.info("Nanovana 이미지 생성 완료")

        # Gemini + Stable Diffusion 2.1
        elif request.model == "gemini":
            hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
            if not hf_api_key:
                raise HTTPException(
                    status_code=500,
                    detail="Hugging Face API 키가 없습니다."
                )

            # Gemini로 프롬프트 최적화
            if os.getenv('REACT_APP_GEMINI_API_KEY'):
                optimized_prompt = await optimize_prompt_with_gemini(request.prompt)
                used_claude_optimization = True

            logger.info("Stable Diffusion 2.1 이미지 생성 시작")
            logger.debug(f"프롬프트: {optimized_prompt}")

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://router.huggingface.co/hf-inference/v1/models/stabilityai/stable-diffusion-2-1",
                    json={"inputs": optimized_prompt},
                    headers={
                        "Authorization": f"Bearer {hf_api_key}",
                        "Content-Type": "application/json"
                    }
                )

            if response.status_code == 503:
                raise HTTPException(
                    status_code=503,
                    detail="모델이 로딩 중입니다. 잠시 후 다시 시도하세요."
                )
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="API 인증 실패 (API 키 확인)."
                )
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"API 오류: {response.status_code}"
                )

            # 이미지를 base64로 인코딩
            image_data = base64.b64encode(response.content).decode('utf-8')
            image_url = f"data:image/png;base64,{image_data}"
            logger.info("Stable Diffusion 이미지 생성 완료")

        else:
            raise HTTPException(
                status_code=400,
                detail="지원하지 않는 AI 모델입니다. (whisk, nanovana, gemini 중 선택)"
            )

        return ImageGenerateResponse(
            success=True,
            imageUrl=image_url,
            optimizedPrompt=optimized_prompt if optimized_prompt != request.prompt else None,
            usedClaudeOptimization=used_claude_optimization,
            usedNanovanaAPI=used_nanovana_api,
            usedWhiskAPI=used_whisk_api
        )

    except HTTPException:
        raise
    except httpx.TimeoutException:
        logger.error("이미지 생성 요청 시간 초과")
        raise HTTPException(
            status_code=504,
            detail="요청 시간이 초과되었습니다."
        )
    except Exception as e:
        logger.error(f"이미지 생성 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"이미지 생성 중 오류가 발생했습니다: {str(e)}"
        )
