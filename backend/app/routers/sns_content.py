"""
SNS 발행 콘텐츠 라우터
- 인스타그램/페이스북 발행 콘텐츠 CRUD
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import User, SNSPublishedContent
from .auth import get_current_user

router = APIRouter(prefix="/api/sns-content", tags=["SNS Content"])


# Pydantic Schemas
class SNSContentCreate(BaseModel):
    platform: str  # instagram, facebook
    caption: str
    hashtags: Optional[List[str]] = None
    image_urls: Optional[List[str]] = None
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    ai_content_id: Optional[int] = None
    status: Optional[str] = "published"


class SNSContentResponse(BaseModel):
    id: int
    platform: str
    caption: str
    hashtags: Optional[List[str]]
    image_urls: Optional[List[str]]
    post_id: Optional[str]
    post_url: Optional[str]
    ai_content_id: Optional[int]
    status: str
    published_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/save", response_model=SNSContentResponse)
async def save_sns_content(
    data: SNSContentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """SNS 발행 콘텐츠 저장"""
    content = SNSPublishedContent(
        user_id=current_user.id,
        platform=data.platform,
        caption=data.caption,
        hashtags=data.hashtags,
        image_urls=data.image_urls,
        post_id=data.post_id,
        post_url=data.post_url,
        ai_content_id=data.ai_content_id,
        status=data.status,
        published_at=datetime.now() if data.status == "published" else None
    )

    db.add(content)
    db.commit()
    db.refresh(content)

    return content


@router.get("/list", response_model=List[SNSContentResponse])
async def list_sns_contents(
    platform: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """SNS 발행 콘텐츠 목록 조회"""
    query = db.query(SNSPublishedContent).filter(
        SNSPublishedContent.user_id == current_user.id
    )

    if platform:
        query = query.filter(SNSPublishedContent.platform == platform)

    contents = query.order_by(
        SNSPublishedContent.created_at.desc()
    ).offset(skip).limit(limit).all()

    return contents


@router.get("/{content_id}", response_model=SNSContentResponse)
async def get_sns_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """SNS 발행 콘텐츠 상세 조회"""
    content = db.query(SNSPublishedContent).filter(
        SNSPublishedContent.id == content_id,
        SNSPublishedContent.user_id == current_user.id
    ).first()

    if not content:
        raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없습니다.")

    return content


@router.delete("/{content_id}")
async def delete_sns_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """SNS 발행 콘텐츠 삭제"""
    content = db.query(SNSPublishedContent).filter(
        SNSPublishedContent.id == content_id,
        SNSPublishedContent.user_id == current_user.id
    ).first()

    if not content:
        raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없습니다.")

    db.delete(content)
    db.commit()

    return {"message": "콘텐츠가 삭제되었습니다."}
