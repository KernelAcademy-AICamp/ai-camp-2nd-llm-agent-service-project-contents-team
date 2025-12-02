from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import google.generativeai as genai
import os
import json
import io
import uuid
import asyncio

from .. import models, auth
from ..database import get_db, SessionLocal
from ..logger import get_logger
from pydantic import BaseModel
from ..services.ai_video_service import run_video_generation_pipeline

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/ai-video",
    tags=["ai-video"]
)

# Cloudinary 설정 - 함수 내부에서 동적으로 설정
# (모듈 레벨에서 설정하면 .env 로드 전에 실행되어 환경변수를 찾지 못함)

# Google Gemini 설정
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


# ===== Pydantic 스키마 =====

class TierInfo(BaseModel):
    """영상 생성 티어 정보"""
    tier: str  # short, standard, premium
    cut_count: int  # 4, 6, 8
    duration_seconds: int  # 15, 25, 40
    cost: float  # 3.90, 5.90, 7.90
    description: str


class VideoGenerationCreateRequest(BaseModel):
    """비디오 생성 작업 생성 요청"""
    product_name: str
    product_description: Optional[str] = None
    tier: str  # short, standard, premium


class StoryboardCut(BaseModel):
    """스토리보드 각 컷 정보"""
    cut: int
    scene_description: str
    image_prompt: str
    duration: float


class VideoGenerationJobResponse(BaseModel):
    """비디오 생성 작업 응답"""
    id: int
    user_id: int
    product_name: str
    product_description: Optional[str]
    uploaded_image_url: str
    tier: str
    cut_count: int
    duration_seconds: int
    cost: float
    storyboard: Optional[List[dict]]
    generated_image_urls: Optional[List[dict]]
    generated_video_urls: Optional[List[dict]]
    final_video_url: Optional[str]
    thumbnail_url: Optional[str]
    status: str
    current_step: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProductAnalysisResponse(BaseModel):
    """제품 분석 결과 응답"""
    recommended_tier: str  # short, standard, premium
    confidence: float  # 0.0 ~ 1.0
    reason: str
    analysis: dict  # 제품 특징, 복잡도 등


# ===== 티어 설정 =====

TIER_CONFIG = {
    "short": {
        "cut_count": 4,
        "duration_seconds": 15,
        "cost": 0.99,
        "description": "빠르고 간결한 15초 영상 (4컷)"
    },
    "standard": {
        "cut_count": 6,
        "duration_seconds": 25,
        "cost": 1.49,
        "description": "표준 25초 영상 (6컷)"
    },
    "premium": {
        "cut_count": 8,
        "duration_seconds": 40,
        "cost": 1.99,
        "description": "프리미엄 40초 영상 (8컷)"
    }
}


# ===== API 엔드포인트 =====

@router.get("/tiers", response_model=List[TierInfo])
async def get_tier_options():
    """
    영상 생성 티어 옵션 조회
    - Short: 15초, 4컷, $3.90
    - Standard: 25초, 6컷, $5.90
    - Premium: 40초, 8컷, $7.90
    """
    return [
        TierInfo(
            tier=tier,
            cut_count=config["cut_count"],
            duration_seconds=config["duration_seconds"],
            cost=config["cost"],
            description=config["description"]
        )
        for tier, config in TIER_CONFIG.items()
    ]


@router.post("/analyze-product", response_model=ProductAnalysisResponse)
async def analyze_product(
    product_name: str = Form(...),
    product_description: Optional[str] = Form(None),
    image: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    제품 분석 및 티어 추천
    AI가 제품 이미지와 정보를 분석하여 최적의 티어를 추천합니다.
    """
    try:
        logger.info(f"Analyzing product for user {current_user.id}: {product_name}")
        logger.info(f"STEP 1: Reading uploaded image file")

        # 업로드된 이미지를 직접 읽어서 base64로 인코딩 (Cloudinary 사용 안 함)
        import base64

        # 파일 내용 읽기
        image_content = await image.read()
        logger.info(f"STEP 2: Image file read, size: {len(image_content)} bytes")

        # Content type 확인
        content_type = image.content_type or "image/jpeg"
        media_type = content_type.split("/")[-1]

        # base64 인코딩
        image_base64 = base64.b64encode(image_content).decode("utf-8")

        logger.info(f"STEP 3: Image encoded to base64, size: {len(image_base64)} chars")

        # Gemini API 호출하여 제품 분석
        logger.info(f"STEP 4: Using Gemini 2.5 Flash for product analysis")

        # Gemini 모델 초기화 (이미 모듈 레벨에서 genai.configure 되어있음)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # PIL Image 객체로 변환 (Gemini는 PIL Image를 선호)
        from PIL import Image as PILImage
        pil_image = PILImage.open(io.BytesIO(image_content))
        logger.info(f"STEP 5: Converted to PIL Image, size: {pil_image.size}")

        prompt = f"""당신은 마케팅 비디오 제작 전문가입니다.
제품 이미지와 정보를 분석하여 최적의 비디오 길이(티어)를 추천해주세요.

**제품 정보:**
- 제품명: {product_name}
- 제품 설명: {product_description or '제공되지 않음'}

**티어 옵션:**
- short: 15초, 4컷 - 심플한 제품, 단일 특징 강조
- standard: 25초, 6컷 - 일반적인 제품, 여러 특징 소개
- premium: 40초, 8컷 - 복잡한 제품, 스토리텔링 필요

**분석 기준:**
1. 제품 복잡도 (단순 vs 복잡)
2. 전달할 정보량 (적음 vs 많음)
3. 타겟 플랫폼 (숏폼 vs 일반)
4. 시각적 요소 (단순 vs 다양)

**응답 형식 (JSON만 반환):**
{{
  "recommended_tier": "standard",
  "confidence": 0.85,
  "reason": "이 제품은 여러 특징이 있어 6개 컷으로 충분히 소개할 수 있습니다.",
  "analysis": {{
    "complexity": "medium",
    "features_count": 3,
    "visual_richness": "high",
    "suggested_platform": "instagram_reels"
  }}
}}

위 제품 이미지를 분석하고 최적의 비디오 티어를 추천해주세요. JSON만 반환하세요."""

        # Gemini API 호출
        response = model.generate_content([prompt, pil_image])

        # 응답 파싱
        response_text = response.text
        logger.info(f"Gemini analysis response: {response_text[:200]}...")

        # JSON 파싱
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        result = json.loads(response_text)

        # 응답 검증
        if result["recommended_tier"] not in TIER_CONFIG:
            result["recommended_tier"] = "standard"  # 기본값

        logger.info(f"Recommended tier for '{product_name}': {result['recommended_tier']} (confidence: {result['confidence']})")

        return ProductAnalysisResponse(
            recommended_tier=result["recommended_tier"],
            confidence=result.get("confidence", 0.8),
            reason=result["reason"],
            analysis=result.get("analysis", {})
        )

    except Exception as e:
        logger.error(f"Error analyzing product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze product: {str(e)}"
        )


def run_pipeline_in_background(job_id: int):
    """
    백그라운드에서 비디오 생성 파이프라인을 실행하는 래퍼 함수
    새로운 DB 세션을 생성하여 사용
    """
    db = SessionLocal()
    try:
        # asyncio 이벤트 루프 생성 및 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_video_generation_pipeline(job_id, db))
        loop.close()
    except Exception as e:
        logger.error(f"Background task error for job {job_id}: {str(e)}")
    finally:
        db.close()


@router.post("/jobs", response_model=VideoGenerationJobResponse, status_code=status.HTTP_201_CREATED)
async def create_video_generation_job(
    background_tasks: BackgroundTasks,
    product_name: str = Form(...),
    product_description: Optional[str] = Form(None),
    tier: str = Form(...),
    image: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    새로운 AI 비디오 생성 작업 생성
    1. 제품 이미지 업로드 (Cloudinary)
    2. VideoGenerationJob 생성
    3. 백그라운드에서 비디오 생성 파이프라인 실행
    """
    # 티어 유효성 검증
    if tier not in TIER_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier. Must be one of: {', '.join(TIER_CONFIG.keys())}"
        )

    tier_config = TIER_CONFIG[tier]

    try:
        # 1. 이미지를 로컬 파일 시스템에 저장
        logger.info(f"Saving product image for user {current_user.id} to local filesystem")

        # 업로드 디렉토리 생성
        upload_dir = Path("uploads") / "ai_video_products" / str(current_user.id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 고유한 파일명 생성
        file_extension = image.filename.split(".")[-1] if "." in image.filename else "jpg"
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = upload_dir / unique_filename

        # 파일 저장
        with open(file_path, "wb") as f:
            content = await image.read()
            f.write(content)

        # 상대 경로를 URL 형식으로 저장 (나중에 접근할 수 있도록)
        uploaded_image_url = f"/uploads/ai_video_products/{current_user.id}/{unique_filename}"
        logger.info(f"Image saved to: {file_path} (URL: {uploaded_image_url})")

        # 2. VideoGenerationJob 생성
        job = models.VideoGenerationJob(
            user_id=current_user.id,
            product_name=product_name,
            product_description=product_description,
            uploaded_image_url=uploaded_image_url,
            tier=tier,
            cut_count=tier_config["cut_count"],
            duration_seconds=tier_config["duration_seconds"],
            cost=tier_config["cost"],
            status="pending"
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(f"Created VideoGenerationJob {job.id} for user {current_user.id}")

        # 3. 백그라운드에서 비디오 생성 파이프라인 실행
        background_tasks.add_task(run_pipeline_in_background, job.id)
        logger.info(f"Added background task for job {job.id}")

        return job

    except Exception as e:
        logger.error(f"Error creating video generation job: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create video generation job: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=VideoGenerationJobResponse)
async def get_video_generation_job(
    job_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    특정 비디오 생성 작업 조회
    """
    job = db.query(models.VideoGenerationJob).filter(
        models.VideoGenerationJob.id == job_id,
        models.VideoGenerationJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video generation job not found"
        )

    return job


@router.get("/jobs", response_model=List[VideoGenerationJobResponse])
async def list_video_generation_jobs(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """
    사용자의 비디오 생성 작업 목록 조회
    """
    jobs = db.query(models.VideoGenerationJob).filter(
        models.VideoGenerationJob.user_id == current_user.id
    ).order_by(
        models.VideoGenerationJob.created_at.desc()
    ).offset(skip).limit(limit).all()

    return jobs
