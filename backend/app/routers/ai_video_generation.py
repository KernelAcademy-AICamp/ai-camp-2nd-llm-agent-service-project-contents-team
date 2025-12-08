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
        # 1. 이미지를 로컬 파일 시스템에 저장 (backend/uploads/)
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
            status="pending",
            # 실제 사용하는 모델명 명시
            planning_model="gemini-2.5-flash",
            image_model="gemini-2.5-flash-image",
            video_model="veo-3.1-fast-generate-001"
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
