from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import httpx
import os
import base64
from typing import Optional
import google.generativeai as genai

from ..database import get_db
from ..models import BrandAnalysis

router = APIRouter(
    prefix="/api",
    tags=["image"]
)


class ImageGenerateRequest(BaseModel):
    prompt: str
    model: str = "nanovana"
    referenceImage: Optional[str] = None  # Base64 encoded image for image-to-image
    userId: Optional[int] = None  # 사용자 ID (브랜드 분석 정보 조회용)


class ImageGenerateResponse(BaseModel):
    success: bool
    imageUrl: str
    optimizedPrompt: Optional[str] = None
    usedClaudeOptimization: bool = False
    usedNanovanaAPI: bool = False
    usedWhiskAPI: bool = False
    usedBrandAnalysis: bool = False


def get_brand_analysis(db: Session, user_id: int) -> Optional[BrandAnalysis]:
    """사용자의 브랜드 분석 정보 조회"""
    return db.query(BrandAnalysis).filter(BrandAnalysis.user_id == user_id).first()


def enhance_prompt_with_brand(prompt: str, brand_analysis: BrandAnalysis) -> str:
    """브랜드 분석 정보를 프롬프트에 반영"""
    brand_elements = []

    # emotional_tone: 감정적 톤 (예: 따뜻한, 유머러스한)
    if brand_analysis.emotional_tone:
        brand_elements.append(f"emotional mood: {brand_analysis.emotional_tone}")

    # brand_personality: 브랜드 성격 종합 설명
    if brand_analysis.brand_personality:
        # 너무 길면 요약
        personality = brand_analysis.brand_personality[:100] if len(brand_analysis.brand_personality) > 100 else brand_analysis.brand_personality
        brand_elements.append(f"brand personality: {personality}")

    # brand_tone: 브랜드 톤앤매너 (예: 친근하고 전문적인)
    if brand_analysis.brand_tone:
        brand_elements.append(f"style tone: {brand_analysis.brand_tone}")

    # 인스타그램 이미지 스타일이 있으면 추가
    if brand_analysis.instagram_image_style:
        brand_elements.append(f"visual style: {brand_analysis.instagram_image_style}")

    # 색상 팔레트가 있으면 추가
    if brand_analysis.instagram_color_palette:
        colors = ", ".join(brand_analysis.instagram_color_palette[:3])  # 최대 3개 색상
        brand_elements.append(f"color palette: {colors}")

    if brand_elements:
        brand_context = ", ".join(brand_elements)
        enhanced_prompt = f"{prompt}. Brand context: {brand_context}"
        return enhanced_prompt

    return prompt


async def optimize_prompt_with_gemini(user_prompt: str, brand_analysis: Optional[BrandAnalysis] = None) -> str:
    """Gemini를 사용하여 프롬프트 최적화 (브랜드 분석 정보 반영)"""
    try:
        google_api_key = os.getenv('REACT_APP_GEMINI_API_KEY')
        if not google_api_key:
            return user_prompt

        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # 브랜드 분석 정보가 있으면 프롬프트에 반영
        brand_context = ""
        if brand_analysis:
            brand_elements = []
            if brand_analysis.emotional_tone:
                brand_elements.append(f"감정적 톤: {brand_analysis.emotional_tone}")
            if brand_analysis.brand_personality:
                brand_elements.append(f"브랜드 성격: {brand_analysis.brand_personality[:150]}")
            if brand_analysis.brand_tone:
                brand_elements.append(f"톤앤매너: {brand_analysis.brand_tone}")
            if brand_analysis.instagram_image_style:
                brand_elements.append(f"이미지 스타일: {brand_analysis.instagram_image_style}")
            if brand_analysis.instagram_color_palette:
                colors = ", ".join(brand_analysis.instagram_color_palette[:3])
                brand_elements.append(f"색상 팔레트: {colors}")

            if brand_elements:
                brand_context = "\n\nBrand Identity to reflect:\n" + "\n".join(brand_elements)

        optimization_prompt = f"""You are an expert at creating detailed, high-quality image generation prompts for AI image generators.

User's prompt: "{user_prompt}"{brand_context}

Transform this into an optimized image generation prompt that:
1. Reflects the brand identity and emotional tone if provided
2. Includes style, lighting, quality, and composition details
3. Maintains consistency with the brand's visual identity
4. Under 100 words. English only. Return ONLY the optimized prompt."""

        response = model.generate_content(optimization_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini 프롬프트 최적화 실패: {e}")
        return user_prompt


@router.post("/generate-image", response_model=ImageGenerateResponse)
async def generate_image(request: ImageGenerateRequest, db: Session = Depends(get_db)):
    """
    이미지 생성 엔드포인트
    - model: 'whisk' (Imagen 3), 'nanovana' (Gemini 2.0 Flash) 또는 'gemini' (Stable Diffusion 2.1)
    - userId: 사용자 ID를 전달하면 브랜드 분석 정보가 이미지 생성에 반영됩니다.
    """
    if not request.prompt:
        raise HTTPException(status_code=400, detail="프롬프트가 필요합니다.")

    try:
        optimized_prompt = request.prompt
        used_claude_optimization = False
        used_nanovana_api = False
        used_whisk_api = False
        used_brand_analysis = False
        image_url = None

        # 브랜드 분석 정보 조회
        brand_analysis = None
        if request.userId:
            brand_analysis = get_brand_analysis(db, request.userId)
            if brand_analysis:
                print(f"🏷️ 브랜드 분석 정보 발견!")
                print(f"   - emotional_tone: {brand_analysis.emotional_tone}")
                print(f"   - brand_personality: {brand_analysis.brand_personality[:50] if brand_analysis.brand_personality else 'N/A'}...")
                print(f"   - brand_tone: {brand_analysis.brand_tone}")
                used_brand_analysis = True

        # Whisk AI (Pollinations - 무료, API 키 불필요)
        if request.model == "whisk":
            print(f"✨ Whisk AI (Pollinations)로 창의적인 이미지 생성 중...")
            print(f"📝 받은 프롬프트: {request.prompt}")

            # 브랜드 분석 정보가 있으면 프롬프트 강화
            enhanced_prompt = request.prompt
            if brand_analysis:
                enhanced_prompt = enhance_prompt_with_brand(request.prompt, brand_analysis)
                print(f"🏷️ 브랜드 반영 프롬프트: {enhanced_prompt}")

            # 한글 프롬프트를 영어로 번역 (Gemini 사용)
            translated_prompt = enhanced_prompt
            google_api_key = os.getenv('REACT_APP_GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if google_api_key:
                try:
                    # 한글이 포함되어 있는지 확인
                    import re
                    if re.search(r'[가-힣]', enhanced_prompt):
                        print("🌐 한글 프롬프트 감지 - 영어로 번역 중...")
                        genai.configure(api_key=google_api_key)
                        model = genai.GenerativeModel('gemini-2.0-flash-exp')
                        translation_response = model.generate_content(
                            f"Translate this Korean text to English for an image generation prompt. Only return the English translation, nothing else:\n\n{enhanced_prompt}"
                        )
                        translated_prompt = translation_response.text.strip()
                        print(f"🌐 번역된 프롬프트: {translated_prompt}")
                except Exception as e:
                    print(f"번역 실패 (원본 프롬프트 사용): {e}")
                    translated_prompt = enhanced_prompt

            # URL 인코딩 (UTF-8로 명시적 인코딩)
            import urllib.parse
            # 특수문자와 공백을 안전하게 처리
            safe_prompt = translated_prompt.encode('utf-8').decode('utf-8')
            encoded_prompt = urllib.parse.quote(safe_prompt, safe='')
            print(f"🔗 인코딩된 프롬프트: {encoded_prompt}")

            # Pollinations AI는 GET 요청으로 이미지를 직접 반환합니다
            image_generation_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&nologo=true&enhance=false"
            print(f"🔗 요청 URL: {image_generation_url}")

            try:
                async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
                    response = await client.get(image_generation_url)

                    print(f"📡 응답 상태 코드: {response.status_code}")
                    print(f"📡 응답 Content-Type: {response.headers.get('content-type', 'unknown')}")

                    if response.status_code != 200:
                        error_text = response.text[:500] if response.text else "No error message"
                        print(f"❌ Pollinations 오류 응답: {error_text}")
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"Whisk AI (Pollinations) 오류: 상태 코드 {response.status_code}"
                        )

                    # Content-Type 확인
                    content_type = response.headers.get('content-type', '')
                    if 'image' not in content_type:
                        print(f"⚠️ 예상치 못한 Content-Type: {content_type}")
                        print(f"⚠️ 응답 내용: {response.text[:500]}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"이미지가 아닌 응답을 받았습니다: {content_type}"
                        )

                    # 이미지를 base64로 인코딩
                    image_data = base64.b64encode(response.content).decode('ascii')
                    image_url = f"data:image/png;base64,{image_data}"
                    used_whisk_api = True
                    print("✅ Whisk AI (Pollinations) 이미지 생성 완료!")

            except httpx.TimeoutException:
                print("⏰ Pollinations 요청 타임아웃")
                raise HTTPException(
                    status_code=504,
                    detail="이미지 생성 시간이 초과되었습니다. 다시 시도해주세요."
                )
            except httpx.RequestError as e:
                print(f"🔌 Pollinations 연결 오류: {e}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Pollinations 서버에 연결할 수 없습니다: {str(e)}"
                )

        # Nanovana (Gemini 2.5 Flash Image with Thinking)
        elif request.model == "nanovana":
            google_api_key = os.getenv('REACT_APP_GEMINI_API_KEY')
            if not google_api_key:
                raise HTTPException(
                    status_code=500,
                    detail="Google API 키가 필요합니다. (Gemini 2.5 Flash Image)"
                )

            # 브랜드 분석 정보가 있으면 프롬프트 강화
            enhanced_prompt = request.prompt
            if brand_analysis:
                enhanced_prompt = enhance_prompt_with_brand(request.prompt, brand_analysis)
                print(f"🏷️ 브랜드 반영 프롬프트: {enhanced_prompt}")

            # 레퍼런스 이미지가 있는지 확인
            if request.referenceImage:
                print("🍌 나노바나나(Gemini 2.5 Flash Image - Image-to-Image)로 이미지 생성 중...")
                print(f"📝 받은 프롬프트: {request.prompt}")
                print(f"🖼️  레퍼런스 이미지 사용")

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
                                "text": f"Based on this reference image, generate a new image: {enhanced_prompt}"
                            }
                        ]
                    }]
                }
            else:
                print("🍌 나노바나나(Gemini 2.5 Flash Image - Text-to-Image)로 이미지 생성 중...")
                print(f"📝 받은 프롬프트: {request.prompt}")
                if brand_analysis:
                    print(f"🏷️ 브랜드 반영 프롬프트: {enhanced_prompt}")

                # 텍스트만 사용
                request_body = {
                    "contents": [{
                        "parts": [{
                            "text": f"Generate an image: {enhanced_prompt}"
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
            print(f"📊 Gemini API 응답 구조: {list(data.keys())}")
            if data.get("candidates"):
                print(f"📊 Candidates 수: {len(data['candidates'])}")
                if len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    print(f"📊 첫 번째 candidate 키: {list(candidate.keys())}")
                    if candidate.get("content"):
                        print(f"📊 Content 키: {list(candidate['content'].keys())}")
                        if candidate["content"].get("parts"):
                            print(f"📊 Parts 수: {len(candidate['content']['parts'])}")
                            for i, part in enumerate(candidate["content"]["parts"]):
                                print(f"📊 Part {i} 키: {list(part.keys())}")

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
                    print(f"Gemini API 응답: {data}")
                    raise HTTPException(
                        status_code=500,
                        detail="Gemini API로부터 이미지를 추출하지 못했습니다."
                    )
            else:
                print(f"Gemini API 응답: {data}")
                raise HTTPException(
                    status_code=500,
                    detail="Gemini API로부터 유효한 응답을 받지 못했습니다."
                )

            used_nanovana_api = True
            print("✅ 나노바나나 이미지 생성 완료!")

        # Gemini + Stable Diffusion 2.1
        elif request.model == "gemini":
            hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
            if not hf_api_key:
                raise HTTPException(
                    status_code=500,
                    detail="Hugging Face API 키가 없습니다."
                )

            # Gemini로 프롬프트 최적화 (브랜드 분석 정보 포함)
            if os.getenv('REACT_APP_GEMINI_API_KEY'):
                optimized_prompt = await optimize_prompt_with_gemini(request.prompt, brand_analysis)
                used_claude_optimization = True
                if brand_analysis:
                    print(f"🏷️ 브랜드 분석 정보가 프롬프트 최적화에 반영됨")

            print(f"🎨 Stable Diffusion 2.1로 이미지 생성 중...")
            print(f"프롬프트: {optimized_prompt}")

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
            print("✅ Stable Diffusion 이미지 생성 완료!")

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
            usedWhiskAPI=used_whisk_api,
            usedBrandAnalysis=used_brand_analysis
        )

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="요청 시간이 초과되었습니다."
        )
    except Exception as e:
        print(f"이미지 생성 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"이미지 생성 중 오류가 발생했습니다: {str(e)}"
        )
