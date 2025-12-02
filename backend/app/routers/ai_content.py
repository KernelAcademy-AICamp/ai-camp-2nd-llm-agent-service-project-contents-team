"""
AI 생성 콘텐츠 API 라우터
- AI 글 생성 기능으로 생성된 블로그 및 SNS 콘텐츠 저장/조회
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from ..database import get_db
from ..models import User, AIGeneratedContent
from ..auth import get_current_user

router = APIRouter(prefix="/api/ai-content", tags=["ai-content"])
logger = logging.getLogger(__name__)


class AIContentSaveRequest(BaseModel):
    """AI 콘텐츠 저장 요청"""
    # 입력 데이터
    input_text: Optional[str] = None
    input_image_count: int = 0

    # 블로그 콘텐츠
    blog_title: str
    blog_content: str
    blog_tags: Optional[List[str]] = None

    # SNS 콘텐츠
    sns_content: Optional[str] = None
    sns_hashtags: Optional[List[str]] = None

    # AI 분석 결과
    analysis_data: Optional[Dict[str, Any]] = None

    # 평가 점수
    blog_score: Optional[int] = None
    sns_score: Optional[int] = None
    critique_data: Optional[Dict[str, Any]] = None

    # 메타데이터
    generation_attempts: int = 1


class AIContentResponse(BaseModel):
    """AI 콘텐츠 응답"""
    id: int
    user_id: int
    input_text: Optional[str]
    input_image_count: int
    blog_title: str
    blog_content: str
    blog_tags: Optional[List[str]]
    sns_content: Optional[str]
    sns_hashtags: Optional[List[str]]
    analysis_data: Optional[Dict[str, Any]]
    blog_score: Optional[int]
    sns_score: Optional[int]
    critique_data: Optional[Dict[str, Any]]
    generation_attempts: int
    status: str
    created_at: str

    class Config:
        from_attributes = True


@router.post("/save", response_model=AIContentResponse)
async def save_ai_content(
    request: AIContentSaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI 생성 콘텐츠 저장

    - 블로그 및 SNS 콘텐츠를 DB에 저장
    """
    try:
        content = AIGeneratedContent(
            user_id=current_user.id,
            input_text=request.input_text,
            input_image_count=request.input_image_count,
            blog_title=request.blog_title,
            blog_content=request.blog_content,
            blog_tags=request.blog_tags,
            sns_content=request.sns_content,
            sns_hashtags=request.sns_hashtags,
            analysis_data=request.analysis_data,
            blog_score=request.blog_score,
            sns_score=request.sns_score,
            critique_data=request.critique_data,
            generation_attempts=request.generation_attempts,
            status="generated"
        )

        db.add(content)
        db.commit()
        db.refresh(content)

        logger.info(f"AI 콘텐츠 저장 완료: user_id={current_user.id}, content_id={content.id}")

        return AIContentResponse(
            id=content.id,
            user_id=content.user_id,
            input_text=content.input_text,
            input_image_count=content.input_image_count,
            blog_title=content.blog_title,
            blog_content=content.blog_content,
            blog_tags=content.blog_tags,
            sns_content=content.sns_content,
            sns_hashtags=content.sns_hashtags,
            analysis_data=content.analysis_data,
            blog_score=content.blog_score,
            sns_score=content.sns_score,
            critique_data=content.critique_data,
            generation_attempts=content.generation_attempts,
            status=content.status,
            created_at=content.created_at.isoformat()
        )

    except Exception as e:
        logger.error(f"AI 콘텐츠 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=f"콘텐츠 저장에 실패했습니다: {str(e)}")


@router.get("/list", response_model=List[AIContentResponse])
async def list_ai_contents(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자의 AI 생성 콘텐츠 목록 조회
    """
    contents = db.query(AIGeneratedContent).filter(
        AIGeneratedContent.user_id == current_user.id
    ).order_by(
        AIGeneratedContent.created_at.desc()
    ).offset(skip).limit(limit).all()

    return [
        AIContentResponse(
            id=c.id,
            user_id=c.user_id,
            input_text=c.input_text,
            input_image_count=c.input_image_count,
            blog_title=c.blog_title,
            blog_content=c.blog_content,
            blog_tags=c.blog_tags,
            sns_content=c.sns_content,
            sns_hashtags=c.sns_hashtags,
            analysis_data=c.analysis_data,
            blog_score=c.blog_score,
            sns_score=c.sns_score,
            critique_data=c.critique_data,
            generation_attempts=c.generation_attempts,
            status=c.status,
            created_at=c.created_at.isoformat()
        )
        for c in contents
    ]


@router.get("/{content_id}", response_model=AIContentResponse)
async def get_ai_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 AI 생성 콘텐츠 조회
    """
    content = db.query(AIGeneratedContent).filter(
        AIGeneratedContent.id == content_id,
        AIGeneratedContent.user_id == current_user.id
    ).first()

    if not content:
        raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없습니다.")

    return AIContentResponse(
        id=content.id,
        user_id=content.user_id,
        input_text=content.input_text,
        input_image_count=content.input_image_count,
        blog_title=content.blog_title,
        blog_content=content.blog_content,
        blog_tags=content.blog_tags,
        sns_content=content.sns_content,
        sns_hashtags=content.sns_hashtags,
        analysis_data=content.analysis_data,
        blog_score=content.blog_score,
        sns_score=content.sns_score,
        critique_data=content.critique_data,
        generation_attempts=content.generation_attempts,
        status=content.status,
        created_at=content.created_at.isoformat()
    )


@router.delete("/{content_id}")
async def delete_ai_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI 생성 콘텐츠 삭제
    """
    content = db.query(AIGeneratedContent).filter(
        AIGeneratedContent.id == content_id,
        AIGeneratedContent.user_id == current_user.id
    ).first()

    if not content:
        raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없습니다.")

    db.delete(content)
    db.commit()

    logger.info(f"AI 콘텐츠 삭제: user_id={current_user.id}, content_id={content_id}")

    return {"message": "콘텐츠가 삭제되었습니다."}
