from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import replicate
import os
import re
import httpx
import urllib.parse
import google.generativeai as genai

from .. import models, auth
from ..database import get_db
from ..logger import get_logger
from pydantic import BaseModel

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/video",
    tags=["video"]
)


# Pydantic 스키마
class VideoGenerateRequest(BaseModel):
    title: str = "AI 생성 동영상"
    description: str = None
    prompt: str
    model: str = "stable-video-diffusion"
    source_image_url: str = None


class VideoResponse(BaseModel):
    id: int
    title: str
    description: str = None
    prompt: str
    model: str
    source_image_url: str = None
    video_url: str = None
    thumbnail_url: str = None
    status: str
    error_message: str = None
    created_at: datetime

    class Config:
        from_attributes = True


# ===== 비디오 스크립트 생성 스키마 =====
class ScriptGenerateRequest(BaseModel):
    topic: str
    duration: int = 60  # 초 단위
    tone: str = "informative"  # informative, casual, professional, entertaining, educational
    target_audience: Optional[str] = None


class SceneInfo(BaseModel):
    time: str
    type: str
    description: str
    visual_suggestion: Optional[str] = None


class ScriptGenerateResponse(BaseModel):
    title: str
    duration: int
    script: str
    scenes: List[SceneInfo]
    hashtags: List[str]
    thumbnail_ideas: List[str]


@router.post("/generate-script", response_model=ScriptGenerateResponse)
async def generate_video_script(
    request: ScriptGenerateRequest,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    AI 비디오 스크립트 생성 (Gemini API)

    - topic: 영상 주제
    - duration: 영상 길이 (초)
    - tone: 톤앤매너 (informative, casual, professional, entertaining, educational)
    - target_audience: 타겟 시청자 (선택)
    """
    google_api_key = os.getenv('REACT_APP_GEMINI_API_KEY')
    if not google_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google API 키가 설정되지 않았습니다."
        )

    logger.info(f"비디오 스크립트 생성 시작 (user_id: {current_user.id}, topic: {request.topic})")

    try:
        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # 톤 한글 변환
        tone_map = {
            "informative": "정보 전달형 (명확하고 객관적인)",
            "casual": "친근한 대화형 (편안하고 가벼운)",
            "professional": "전문가형 (권위 있고 신뢰감 있는)",
            "entertaining": "엔터테인먼트형 (재미있고 유머러스한)",
            "educational": "교육형 (쉽게 설명하고 단계별로)"
        }
        tone_description = tone_map.get(request.tone, request.tone)

        # 영상 길이에 따른 씬 구성 가이드
        if request.duration <= 30:
            scene_guide = "숏폼: 인트로(3초) - 핵심메시지(20초) - CTA(7초)"
        elif request.duration <= 60:
            scene_guide = "1분: 인트로(5초) - 본론1(20초) - 본론2(25초) - 아웃트로(10초)"
        elif request.duration <= 180:
            scene_guide = "3분: 인트로(10초) - 본론1(50초) - 본론2(50초) - 본론3(50초) - 아웃트로(20초)"
        else:
            scene_guide = "장편: 인트로(15초) - 본론1-4 (각 60-90초) - 아웃트로(30초)"

        target_info = f"타겟 시청자: {request.target_audience}" if request.target_audience else "타겟 시청자: 일반 대중"

        prompt = f"""당신은 전문 영상 스크립트 작가입니다. 아래 조건에 맞는 영상 스크립트를 작성해주세요.

## 영상 정보
- 주제: {request.topic}
- 영상 길이: {request.duration}초 (약 {request.duration // 60}분 {request.duration % 60}초)
- 톤앤매너: {tone_description}
- {target_info}

## 구성 가이드
{scene_guide}

## 요청사항
1. 영상 시간에 맞는 분량의 스크립트 작성 (1분당 약 150-180단어)
2. 각 씬(Scene)별로 시간, 유형, 설명, 영상 제안을 포함
3. 시청자의 관심을 끄는 후킹 멘트로 시작
4. 구독/좋아요 유도는 자연스럽게

## 출력 형식 (반드시 아래 JSON 형식으로만 응답)
{{
  "title": "영상 제목 (클릭을 유도하는)",
  "script": "전체 스크립트 (씬 구분 포함, [씬1 - 시간] 형식으로)",
  "scenes": [
    {{
      "time": "0:00-0:10",
      "type": "intro",
      "description": "씬 설명",
      "visual_suggestion": "이 씬에서 보여줄 영상/이미지 제안"
    }}
  ],
  "hashtags": ["해시태그1", "해시태그2", "해시태그3", "해시태그4", "해시태그5"],
  "thumbnail_ideas": ["썸네일 아이디어1", "썸네일 아이디어2"]
}}

JSON만 출력하고 다른 텍스트는 포함하지 마세요."""

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # JSON 파싱
        import json

        # ```json ... ``` 형식 제거
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}, 응답: {response_text[:500]}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI 응답 파싱에 실패했습니다. 다시 시도해주세요."
            )

        # 응답 구성
        scenes = [
            SceneInfo(
                time=scene.get("time", ""),
                type=scene.get("type", ""),
                description=scene.get("description", ""),
                visual_suggestion=scene.get("visual_suggestion")
            )
            for scene in result.get("scenes", [])
        ]

        logger.info(f"비디오 스크립트 생성 완료 (user_id: {current_user.id})")

        return ScriptGenerateResponse(
            title=result.get("title", request.topic),
            duration=request.duration,
            script=result.get("script", ""),
            scenes=scenes,
            hashtags=result.get("hashtags", []),
            thumbnail_ideas=result.get("thumbnail_ideas", [])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"비디오 스크립트 생성 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"스크립트 생성 중 오류가 발생했습니다: {str(e)}"
        )


class FreeVideoGenerateRequest(BaseModel):
    prompt: str
    title: str = "AI 생성 동영상"
    description: Optional[str] = None


class FreeVideoGenerateResponse(BaseModel):
    success: bool
    video_url: str
    title: str
    prompt: str
    translated_prompt: Optional[str] = None


@router.post("/generate-free", response_model=FreeVideoGenerateResponse)
async def generate_free_video(
    request: FreeVideoGenerateRequest,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    저렴한 AI 동영상 생성 (Replicate Wan 2.1 모델)

    - Replicate API 사용 (저렴한 오픈소스 모델)
    - 텍스트 프롬프트 기반 동영상 생성
    - 한글 프롬프트 자동 번역 지원
    """
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Replicate API token이 설정되지 않았습니다."
        )

    if not request.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="프롬프트를 입력해주세요."
        )

    logger.info(f"Wan 2.1 동영상 생성 시작 (user_id: {current_user.id}, prompt: {request.prompt[:50]}...)")

    try:
        translated_prompt = request.prompt

        # 한글이 포함되어 있으면 영어로 번역
        google_api_key = os.getenv('REACT_APP_GEMINI_API_KEY')
        if google_api_key and re.search(r'[가-힣]', request.prompt):
            logger.info("한글 프롬프트 감지 - 영어로 번역 중...")
            try:
                genai.configure(api_key=google_api_key)
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                translation_response = model.generate_content(
                    f"Translate this Korean text to English for a video generation prompt. "
                    f"Make it descriptive and cinematic. Only return the English translation:\n\n{request.prompt}"
                )
                translated_prompt = translation_response.text.strip()
                logger.info(f"번역된 프롬프트: {translated_prompt}")
            except Exception as e:
                logger.warning(f"번역 실패 (원본 프롬프트 사용): {e}")

        # Replicate API 호출 (Wan 2.1 - 저렴한 오픈소스 Text-to-Video 모델)
        os.environ["REPLICATE_API_TOKEN"] = replicate_token

        output = replicate.run(
            "wan-video/wan-2.1-t2v-480p:6006396d8de8e4766d1f556fd8ca3db699e6d12dfb6fc24249a2eaed3721ce18",
            input={
                "prompt": translated_prompt,
                "negative_prompt": "blurry, low quality, distorted, ugly, bad anatomy",
                "num_frames": 81,  # 약 3초 (27fps)
                "guidance_scale": 5.0,
                "num_inference_steps": 30
            }
        )

        # 결과 처리
        if output:
            if isinstance(output, list):
                video_url = output[0] if output else None
            else:
                video_url = str(output)

            # DB에 기록 저장
            video = models.Video(
                user_id=current_user.id,
                title=request.title,
                description=request.description,
                prompt=request.prompt,
                model="wan-2.1",
                video_url=video_url,
                status="completed"
            )
            db.add(video)
            db.commit()

            logger.info(f"Wan 2.1 동영상 생성 완료 (user_id: {current_user.id})")

            return FreeVideoGenerateResponse(
                success=True,
                video_url=video_url,
                title=request.title,
                prompt=request.prompt,
                translated_prompt=translated_prompt if translated_prompt != request.prompt else None
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="동영상 생성 결과가 없습니다."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Wan 2.1 동영상 생성 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"동영상 생성 중 오류가 발생했습니다: {str(e)}"
        )


class ImageToVideoRequest(BaseModel):
    title: str = "AI 생성 동영상"
    description: Optional[str] = None
    prompt: Optional[str] = None
    image_data: str  # Base64 인코딩된 이미지


class ImageToVideoResponse(BaseModel):
    success: bool
    video_url: str
    title: str
    status: str


@router.post("/generate-from-image", response_model=ImageToVideoResponse)
async def generate_video_from_image(
    request: ImageToVideoRequest,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    이미지 업로드 → 동영상 생성 (Stable Video Diffusion via Replicate)

    - image_data: Base64 인코딩된 이미지 데이터 (data:image/...;base64,... 형식)
    """
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Replicate API token이 설정되지 않았습니다."
        )

    if not request.image_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미지 데이터가 필요합니다."
        )

    logger.info(f"이미지 → 동영상 생성 시작 (user_id: {current_user.id})")

    try:
        os.environ["REPLICATE_API_TOKEN"] = replicate_token

        # Base64 데이터에서 data URI prefix 처리
        image_data = request.image_data
        if image_data.startswith('data:'):
            # data:image/png;base64,xxxxx 형식에서 base64 부분만 추출
            image_data = image_data.split(',')[1] if ',' in image_data else image_data

        # Data URI 형식으로 변환 (Replicate가 요구하는 형식)
        data_uri = f"data:image/png;base64,{image_data}"

        # Stable Video Diffusion 호출
        output = replicate.run(
            "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438",
            input={
                "input_image": data_uri,
                "sizing_strategy": "maintain_aspect_ratio",
                "frames_per_second": 6,
                "motion_bucket_id": 127,
                "cond_aug": 0.02
            }
        )

        # 결과 처리
        if output:
            if isinstance(output, list):
                video_url = output[0] if output else None
            else:
                video_url = str(output)

            # DB에 저장
            video = models.Video(
                user_id=current_user.id,
                title=request.title,
                description=request.description,
                prompt=request.prompt or "Image to Video",
                model="stable-video-diffusion",
                video_url=video_url,
                status="completed"
            )
            db.add(video)
            db.commit()

            logger.info(f"이미지 → 동영상 생성 완료 (user_id: {current_user.id})")

            return ImageToVideoResponse(
                success=True,
                video_url=video_url,
                title=request.title,
                status="completed"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="동영상 생성 결과가 없습니다."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이미지 → 동영상 생성 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"동영상 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/generate", response_model=VideoResponse)
async def generate_video(
    request: VideoGenerateRequest,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    AI 동영상 생성 (Replicate API)

    지원 모델:
    - stable-video-diffusion: 이미지 → 동영상 (고품질, source_image_url 필요)
    - text-to-video: 텍스트 → 동영상 (실험적)
    """
    logger.info(f"동영상 생성 시작 (user_id: {current_user.id}, model: {request.model})")

    # Replicate API 토큰 확인
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_token:
        logger.error("REPLICATE_API_TOKEN이 설정되지 않았습니다.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Replicate API token not configured"
        )

    try:
        # 동영상 레코드 생성
        logger.info("DB에 동영상 레코드 생성 중...")
        video = models.Video(
            user_id=current_user.id,
            title=request.title,
            description=request.description,
            prompt=request.prompt,
            model=request.model,
            source_image_url=request.source_image_url,
            status="processing"
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        logger.info(f"DB 레코드 생성 완료 (video_id: {video.id})")

        # Replicate API 호출
        os.environ["REPLICATE_API_TOKEN"] = replicate_token

        if request.model == "stable-video-diffusion":
            # Image-to-Video 모델
            if not request.source_image_url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="source_image_url is required for stable-video-diffusion"
                )

            logger.info("Stable Video Diffusion API 호출 중...")
            output = replicate.run(
                "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438",
                input={
                    "input_image": request.source_image_url,
                    "sizing_strategy": "maintain_aspect_ratio",
                    "frames_per_second": 6,
                    "motion_bucket_id": 127,
                    "cond_aug": 0.02
                }
            )

        elif request.model == "text-to-video":
            # Text-to-Video 모델 (LTX-Video)
            logger.info(f"LTX-Video API 호출 중... (prompt: {request.prompt[:50]}...)")
            output = replicate.run(
                "lightricks/ltx-video:b6b9c8a9e03e8dcc6a9ecbd60b4c62b7cc3abfba24df7f21bea81bd6f31d6ee0",
                input={
                    "prompt": request.prompt,
                    "num_frames": 121,
                    "aspect_ratio": "16:9",
                    "num_inference_steps": 30
                }
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported model: {request.model}"
            )

        logger.info(f"Replicate API 응답: {type(output)} - {output}")

        # 결과 처리
        if output:
            # output은 URL 또는 URL 리스트일 수 있음
            if isinstance(output, list):
                video_url = output[0] if output else None
            else:
                video_url = str(output)

            video.video_url = video_url
            video.status = "completed"
            logger.info(f"동영상 생성 완료 (video_url: {video_url})")
        else:
            video.status = "failed"
            video.error_message = "No output from Replicate API"
            logger.warning("Replicate API에서 출력이 없습니다.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"동영상 생성 실패: {e}", exc_info=True)
        video.status = "failed"
        video.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video generation failed: {str(e)}"
        )

    db.commit()
    db.refresh(video)

    return video


@router.get("/list", response_model=List[VideoResponse])
async def list_videos(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """
    사용자의 동영상 목록 조회
    """
    videos = db.query(models.Video).filter(
        models.Video.user_id == current_user.id
    ).order_by(
        models.Video.created_at.desc()
    ).offset(skip).limit(limit).all()

    return videos


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    특정 동영상 조회
    """
    video = db.query(models.Video).filter(
        models.Video.id == video_id,
        models.Video.user_id == current_user.id
    ).first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    return video


@router.delete("/{video_id}")
async def delete_video(
    video_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    동영상 삭제
    """
    video = db.query(models.Video).filter(
        models.Video.id == video_id,
        models.Video.user_id == current_user.id
    ).first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    db.delete(video)
    db.commit()

    return {"message": "Video deleted successfully"}
