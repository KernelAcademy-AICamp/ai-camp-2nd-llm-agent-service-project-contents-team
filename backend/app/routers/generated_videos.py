from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from .. import models, auth
from ..database import get_db
from ..logger import get_logger
from pydantic import BaseModel

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/generated-videos",
    tags=["generated-videos"]
)


# ===== Pydantic 스키마 =====

class GeneratedVideoResponse(BaseModel):
    """생성된 비디오 응답"""
    id: int
    session_id: str
    user_id: int
    final_video_url: str
    product_name: str
    tier: str
    duration_seconds: int
    created_at: datetime

    class Config:
        from_attributes = True


# ===== API 엔드포인트 =====

@router.get("", response_model=List[GeneratedVideoResponse])
async def list_generated_videos(
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """
    사용자의 생성된 비디오 목록 조회
    - 최신순으로 정렬
    - 페이지네이션 지원
    """
    videos = db.query(models.GeneratedVideo).filter(
        models.GeneratedVideo.user_id == current_user.id
    ).order_by(
        models.GeneratedVideo.created_at.desc()
    ).offset(skip).limit(limit).all()

    return videos


@router.get("/{session_id}", response_model=GeneratedVideoResponse)
async def get_generated_video(
    session_id: str,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    특정 세션의 생성된 비디오 조회
    """
    video = db.query(models.GeneratedVideo).filter(
        models.GeneratedVideo.session_id == session_id,
        models.GeneratedVideo.user_id == current_user.id
    ).first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated video not found"
        )

    return video
