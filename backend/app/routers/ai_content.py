"""
AI 생성 콘텐츠 API 라우터
- AI 글 생성 기능으로 생성된 블로그 및 SNS 콘텐츠 저장/조회
- v2: 플랫폼별 분리 저장 구조
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from ..database import get_db
from ..models import (
    User, AIGeneratedContent,
    ContentGenerationSession, GeneratedBlogContent, GeneratedSNSContent,
    GeneratedXContent, GeneratedThreadsContent, GeneratedImage
)
from ..auth import get_current_user

router = APIRouter(prefix="/api/ai-content", tags=["ai-content"])
logger = logging.getLogger(__name__)


class AIContentSaveRequest(BaseModel):
    """AI 콘텐츠 저장 요청"""
    # 입력 데이터
    input_text: Optional[str] = None
    input_image_count: int = 0

    # 생성된 이미지 URL 목록
    generated_image_urls: Optional[List[str]] = None

    # 블로그 콘텐츠
    blog_title: str
    blog_content: str
    blog_tags: Optional[List[str]] = None

    # SNS 콘텐츠
    sns_content: Optional[str] = None
    sns_hashtags: Optional[List[str]] = None

    # X 콘텐츠
    x_content: Optional[str] = None
    x_hashtags: Optional[List[str]] = None

    # Threads 콘텐츠
    threads_content: Optional[str] = None
    threads_hashtags: Optional[List[str]] = None

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
    generated_image_urls: Optional[List[str]]
    blog_title: str
    blog_content: str
    blog_tags: Optional[List[str]]
    sns_content: Optional[str]
    sns_hashtags: Optional[List[str]]
    x_content: Optional[str]
    x_hashtags: Optional[List[str]]
    threads_content: Optional[str]
    threads_hashtags: Optional[List[str]]
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
        # 디버깅: 수신된 X/Threads 데이터 확인
        logger.info(f"📦 수신된 X 콘텐츠: {request.x_content[:50] if request.x_content else 'NULL'}")
        logger.info(f"📦 수신된 Threads 콘텐츠: {request.threads_content[:50] if request.threads_content else 'NULL'}")

        content = AIGeneratedContent(
            user_id=current_user.id,
            input_text=request.input_text,
            input_image_count=request.input_image_count,
            generated_image_urls=request.generated_image_urls,
            blog_title=request.blog_title,
            blog_content=request.blog_content,
            blog_tags=request.blog_tags,
            sns_content=request.sns_content,
            sns_hashtags=request.sns_hashtags,
            x_content=request.x_content,
            x_hashtags=request.x_hashtags,
            threads_content=request.threads_content,
            threads_hashtags=request.threads_hashtags,
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
            generated_image_urls=content.generated_image_urls,
            blog_title=content.blog_title,
            blog_content=content.blog_content,
            blog_tags=content.blog_tags,
            sns_content=content.sns_content,
            sns_hashtags=content.sns_hashtags,
            x_content=content.x_content,
            x_hashtags=content.x_hashtags,
            threads_content=content.threads_content,
            threads_hashtags=content.threads_hashtags,
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
            generated_image_urls=c.generated_image_urls,
            blog_title=c.blog_title,
            blog_content=c.blog_content,
            blog_tags=c.blog_tags,
            sns_content=c.sns_content,
            sns_hashtags=c.sns_hashtags,
            x_content=c.x_content,
            x_hashtags=c.x_hashtags,
            threads_content=c.threads_content,
            threads_hashtags=c.threads_hashtags,
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
        generated_image_urls=content.generated_image_urls,
        blog_title=content.blog_title,
        blog_content=content.blog_content,
        blog_tags=content.blog_tags,
        sns_content=content.sns_content,
        sns_hashtags=content.sns_hashtags,
        x_content=content.x_content,
        x_hashtags=content.x_hashtags,
        threads_content=content.threads_content,
        threads_hashtags=content.threads_hashtags,
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


# ============================================
# V2 API - 플랫폼별 분리 저장 구조
# ============================================

class BlogContentData(BaseModel):
    """블로그 콘텐츠 데이터"""
    title: str
    content: str
    tags: Optional[List[str]] = None
    score: Optional[int] = None


class SNSContentData(BaseModel):
    """SNS 콘텐츠 데이터"""
    content: str
    hashtags: Optional[List[str]] = None
    score: Optional[int] = None


class XContentData(BaseModel):
    """X 콘텐츠 데이터"""
    content: str
    hashtags: Optional[List[str]] = None
    score: Optional[int] = None


class ThreadsContentData(BaseModel):
    """Threads 콘텐츠 데이터"""
    content: str
    hashtags: Optional[List[str]] = None
    score: Optional[int] = None


class ImageData(BaseModel):
    """이미지 데이터"""
    image_url: str
    prompt: Optional[str] = None


class ContentSessionSaveRequest(BaseModel):
    """콘텐츠 생성 세션 저장 요청 (v2)"""
    # 사용자 입력값
    topic: str
    content_type: str  # text, image, both
    style: str  # casual, professional, friendly, etc.
    selected_platforms: List[str]  # ["blog", "sns", "x", "threads"]

    # 플랫폼별 콘텐츠 (선택한 플랫폼만)
    blog: Optional[BlogContentData] = None
    sns: Optional[SNSContentData] = None
    x: Optional[XContentData] = None
    threads: Optional[ThreadsContentData] = None

    # 생성된 이미지
    images: Optional[List[ImageData]] = None
    requested_image_count: int = 0  # 요청한 이미지 갯수

    # AI 분석/평가 결과
    analysis_data: Optional[Dict[str, Any]] = None
    critique_data: Optional[Dict[str, Any]] = None

    # 메타데이터
    generation_attempts: int = 1


class ContentSessionListResponse(BaseModel):
    """콘텐츠 생성 세션 목록 응답 (경량화 - 이미지 제외)"""
    id: int
    user_id: int
    topic: str
    content_type: str
    style: str
    selected_platforms: List[str]
    generation_attempts: int
    status: str
    created_at: str
    requested_image_count: int = 0

    # 플랫폼별 콘텐츠 존재 여부만 (상세 내용 제외)
    blog: Optional[Dict[str, Any]] = None
    sns: Optional[Dict[str, Any]] = None
    x: Optional[Dict[str, Any]] = None
    threads: Optional[Dict[str, Any]] = None

    # 이미지 갯수만
    image_count: int = 0

    class Config:
        from_attributes = True


class ContentSessionResponse(BaseModel):
    """콘텐츠 생성 세션 상세 응답 (v2)"""
    id: int
    user_id: int
    topic: str
    content_type: str
    style: str
    selected_platforms: List[str]
    analysis_data: Optional[Dict[str, Any]]
    critique_data: Optional[Dict[str, Any]]
    generation_attempts: int
    status: str
    created_at: str

    # 플랫폼별 콘텐츠
    blog: Optional[Dict[str, Any]] = None
    sns: Optional[Dict[str, Any]] = None
    x: Optional[Dict[str, Any]] = None
    threads: Optional[Dict[str, Any]] = None

    # 생성된 이미지
    images: Optional[List[Dict[str, Any]]] = None
    requested_image_count: int = 0  # 요청한 이미지 갯수

    class Config:
        from_attributes = True


@router.post("/v2/save", response_model=ContentSessionResponse)
async def save_content_session(
    request: ContentSessionSaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    콘텐츠 생성 세션 저장 (v2)
    - 플랫폼별로 분리하여 저장
    """
    try:
        # 1. 세션 생성
        session = ContentGenerationSession(
            user_id=current_user.id,
            topic=request.topic,
            content_type=request.content_type,
            style=request.style,
            selected_platforms=request.selected_platforms,
            requested_image_count=request.requested_image_count,
            analysis_data=request.analysis_data,
            critique_data=request.critique_data,
            generation_attempts=request.generation_attempts,
            status="generated"
        )
        db.add(session)
        db.flush()  # ID 생성을 위해 flush

        # 2. 플랫폼별 콘텐츠 저장
        if request.blog and "blog" in request.selected_platforms:
            blog_content = GeneratedBlogContent(
                session_id=session.id,
                user_id=current_user.id,
                title=request.blog.title,
                content=request.blog.content,
                tags=request.blog.tags,
                score=request.blog.score
            )
            db.add(blog_content)

        if request.sns and "sns" in request.selected_platforms:
            sns_content = GeneratedSNSContent(
                session_id=session.id,
                user_id=current_user.id,
                content=request.sns.content,
                hashtags=request.sns.hashtags,
                score=request.sns.score
            )
            db.add(sns_content)

        if request.x and "x" in request.selected_platforms:
            x_content = GeneratedXContent(
                session_id=session.id,
                user_id=current_user.id,
                content=request.x.content,
                hashtags=request.x.hashtags,
                score=request.x.score
            )
            db.add(x_content)

        if request.threads and "threads" in request.selected_platforms:
            threads_content = GeneratedThreadsContent(
                session_id=session.id,
                user_id=current_user.id,
                content=request.threads.content,
                hashtags=request.threads.hashtags,
                score=request.threads.score
            )
            db.add(threads_content)

        # 3. 이미지 저장
        if request.images:
            for img in request.images:
                image = GeneratedImage(
                    session_id=session.id,
                    user_id=current_user.id,
                    image_url=img.image_url,
                    prompt=img.prompt
                )
                db.add(image)

        db.commit()
        db.refresh(session)

        logger.info(f"콘텐츠 세션 저장 완료: user_id={current_user.id}, session_id={session.id}")

        # 응답 생성
        return _build_session_response(session)

    except Exception as e:
        db.rollback()
        logger.error(f"콘텐츠 세션 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=f"콘텐츠 저장에 실패했습니다: {str(e)}")


@router.get("/v2/list", response_model=List[ContentSessionListResponse])
async def list_content_sessions(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    콘텐츠 생성 세션 목록 조회 (v2)
    - 이미지 데이터 제외하여 빠른 로딩 (이미지 갯수만 포함)
    """
    sessions = db.query(ContentGenerationSession).options(
        selectinload(ContentGenerationSession.blog_content),
        selectinload(ContentGenerationSession.sns_content),
        selectinload(ContentGenerationSession.x_content),
        selectinload(ContentGenerationSession.threads_content)
        # images는 로드하지 않음 (Base64 데이터가 너무 큼)
    ).filter(
        ContentGenerationSession.user_id == current_user.id
    ).order_by(
        ContentGenerationSession.created_at.desc()
    ).offset(skip).limit(limit).all()

    return [_build_session_list_response(s, db) for s in sessions]


@router.get("/v2/{session_id}", response_model=ContentSessionResponse)
async def get_content_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 콘텐츠 생성 세션 조회 (v2)
    """
    session = db.query(ContentGenerationSession).options(
        joinedload(ContentGenerationSession.blog_content),
        joinedload(ContentGenerationSession.sns_content),
        joinedload(ContentGenerationSession.x_content),
        joinedload(ContentGenerationSession.threads_content),
        joinedload(ContentGenerationSession.images)
    ).filter(
        ContentGenerationSession.id == session_id,
        ContentGenerationSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없습니다.")

    return _build_session_response(session)


@router.delete("/v2/{session_id}")
async def delete_content_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    콘텐츠 생성 세션 삭제 (v2)
    - 연관된 모든 플랫폼 콘텐츠와 이미지도 함께 삭제됨 (CASCADE)
    """
    session = db.query(ContentGenerationSession).filter(
        ContentGenerationSession.id == session_id,
        ContentGenerationSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없습니다.")

    db.delete(session)
    db.commit()

    logger.info(f"콘텐츠 세션 삭제: user_id={current_user.id}, session_id={session_id}")

    return {"message": "콘텐츠가 삭제되었습니다."}


def _build_session_list_response(session: ContentGenerationSession, db: Session) -> ContentSessionListResponse:
    """목록용 세션 응답 객체 생성 (경량화 - 이미지 갯수만)"""
    # 이미지 갯수만 조회 (Base64 데이터 로드 안함)
    image_count = db.query(GeneratedImage).filter(
        GeneratedImage.session_id == session.id
    ).count()

    return ContentSessionListResponse(
        id=session.id,
        user_id=session.user_id,
        topic=session.topic,
        content_type=session.content_type,
        style=session.style,
        selected_platforms=session.selected_platforms,
        generation_attempts=session.generation_attempts,
        status=session.status,
        created_at=session.created_at.isoformat(),
        requested_image_count=session.requested_image_count or 0,
        blog={"id": session.blog_content.id, "title": session.blog_content.title} if session.blog_content else None,
        sns={"id": session.sns_content.id} if session.sns_content else None,
        x={"id": session.x_content.id} if session.x_content else None,
        threads={"id": session.threads_content.id} if session.threads_content else None,
        image_count=image_count
    )


def _build_session_response(session: ContentGenerationSession) -> ContentSessionResponse:
    """세션 응답 객체 생성 헬퍼"""
    return ContentSessionResponse(
        id=session.id,
        user_id=session.user_id,
        topic=session.topic,
        content_type=session.content_type,
        style=session.style,
        selected_platforms=session.selected_platforms,
        analysis_data=session.analysis_data,
        critique_data=session.critique_data,
        generation_attempts=session.generation_attempts,
        status=session.status,
        created_at=session.created_at.isoformat(),
        blog={
            "id": session.blog_content.id,
            "title": session.blog_content.title,
            "content": session.blog_content.content,
            "tags": session.blog_content.tags,
            "score": session.blog_content.score
        } if session.blog_content else None,
        sns={
            "id": session.sns_content.id,
            "content": session.sns_content.content,
            "hashtags": session.sns_content.hashtags,
            "score": session.sns_content.score
        } if session.sns_content else None,
        x={
            "id": session.x_content.id,
            "content": session.x_content.content,
            "hashtags": session.x_content.hashtags,
            "score": session.x_content.score
        } if session.x_content else None,
        threads={
            "id": session.threads_content.id,
            "content": session.threads_content.content,
            "hashtags": session.threads_content.hashtags,
            "score": session.threads_content.score
        } if session.threads_content else None,
        images=[
            {"id": img.id, "image_url": img.image_url, "prompt": img.prompt}
            for img in session.images
        ] if session.images else None,
        requested_image_count=session.requested_image_count or 0
    )
