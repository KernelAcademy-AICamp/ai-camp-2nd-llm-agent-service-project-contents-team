from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import replicate
import os

from .. import models, auth
from ..database import get_db
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/video",
    tags=["video"]
)


# Pydantic 스키마
class VideoGenerateRequest(BaseModel):
    title: str
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
    created_at: str

    class Config:
        from_attributes = True


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
    # Replicate API 토큰 확인
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Replicate API token not configured"
        )

    # 동영상 레코드 생성
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

    try:
        # Replicate API 호출
        os.environ["REPLICATE_API_TOKEN"] = replicate_token

        if request.model == "stable-video-diffusion":
            # Image-to-Video 모델
            if not request.source_image_url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="source_image_url is required for stable-video-diffusion"
                )

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

        # 결과 처리
        if output:
            # output은 URL 또는 URL 리스트일 수 있음
            if isinstance(output, list):
                video_url = output[0] if output else None
            else:
                video_url = str(output)

            video.video_url = video_url
            video.status = "completed"
        else:
            video.status = "failed"
            video.error_message = "No output from Replicate API"

    except Exception as e:
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
