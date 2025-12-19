"""
AI 생성 콘텐츠 API 라우터
- AI 글 생성 기능으로 생성된 블로그 및 SNS 콘텐츠 저장/조회
- v2: 플랫폼별 분리 저장 구조
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from ..database import get_db
from ..models import (
    User,
    ContentGenerationSession, GeneratedBlogContent, GeneratedSNSContent,
    GeneratedXContent, GeneratedThreadsContent, GeneratedImage, GeneratedCardnewsContent
)
from ..auth import get_current_user

router = APIRouter(prefix="/api/ai-content", tags=["ai-content"])


# ============================================
# Pydantic 모델
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
    style: Optional[str] = None  # casual, professional, friendly, etc.
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
    """콘텐츠 생성 세션 목록 응답 (미리보기용 콘텐츠 포함)"""
    id: int
    user_id: int
    topic: str
    content_type: str
    style: Optional[str] = None
    selected_platforms: List[str]
    generation_attempts: int
    status: str
    created_at: str
    requested_image_count: int = 0

    # 플랫폼별 콘텐츠 (미리보기용 content_preview 포함)
    blog: Optional[Dict[str, Any]] = None
    sns: Optional[Dict[str, Any]] = None
    x: Optional[Dict[str, Any]] = None
    threads: Optional[Dict[str, Any]] = None
    cardnews: Optional[Dict[str, Any]] = None  # 카드뉴스

    # 이미지 (첫 번째 이미지 URL 포함)
    image_count: int = 0
    images: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True


class ContentSessionResponse(BaseModel):
    """콘텐츠 생성 세션 상세 응답 (v2)"""
    id: int
    user_id: int
    topic: str
    content_type: str
    style: Optional[str] = None
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
    cardnews: Optional[Dict[str, Any]] = None  # 카드뉴스

    # 생성된 이미지
    images: Optional[List[Dict[str, Any]]] = None
    requested_image_count: int = 0  # 요청한 이미지 갯수

    class Config:
        from_attributes = True


# ============================================
# V2 API 엔드포인트
# ============================================

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
        db.flush()

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

        return _build_session_response(session)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"콘텐츠 저장에 실패했습니다: {str(e)}")


@router.get("/v2/list", response_model=List[ContentSessionListResponse])
async def list_content_sessions(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    콘텐츠 생성 세션 목록 조회 (v2) - 최적화 버전
    - 2단계 쿼리로 분리하여 원격 DB 성능 최적화
    """
    # 1단계: 세션 기본 정보만 빠르게 조회 (JOIN 없이)
    sessions = db.query(ContentGenerationSession).filter(
        ContentGenerationSession.user_id == current_user.id
    ).order_by(
        ContentGenerationSession.created_at.desc()
    ).offset(skip).limit(limit).all()

    if not sessions:
        return []

    session_ids = [s.id for s in sessions]

    # 2단계: 관련 데이터를 IN 쿼리로 한번에 조회
    blog_contents = {
        b.session_id: b for b in
        db.query(GeneratedBlogContent).filter(
            GeneratedBlogContent.session_id.in_(session_ids)
        ).all()
    }

    sns_contents = {
        s.session_id: s for s in
        db.query(GeneratedSNSContent).filter(
            GeneratedSNSContent.session_id.in_(session_ids)
        ).all()
    }

    x_contents = {
        x.session_id: x for x in
        db.query(GeneratedXContent).filter(
            GeneratedXContent.session_id.in_(session_ids)
        ).all()
    }

    threads_contents = {
        t.session_id: t for t in
        db.query(GeneratedThreadsContent).filter(
            GeneratedThreadsContent.session_id.in_(session_ids)
        ).all()
    }

    # 카드뉴스 콘텐츠 - 필요한 컬럼만 조회 (대용량 JSON 제외)
    cardnews_results = db.query(
        GeneratedCardnewsContent.session_id,
        GeneratedCardnewsContent.id,
        GeneratedCardnewsContent.title,
        GeneratedCardnewsContent.page_count,
        GeneratedCardnewsContent.purpose
    ).filter(
        GeneratedCardnewsContent.session_id.in_(session_ids)
    ).all()
    cardnews_contents = {
        c.session_id: {'id': c.id, 'title': c.title, 'page_count': c.page_count, 'purpose': c.purpose}
        for c in cardnews_results
    }

    # 3단계: 이미지 카운트만 조회
    image_counts = db.query(
        GeneratedImage.session_id,
        func.count(GeneratedImage.id).label('count')
    ).filter(
        GeneratedImage.session_id.in_(session_ids)
    ).group_by(GeneratedImage.session_id).all()

    image_data = {
        stat.session_id: {'count': stat.count, 'first_url': None}
        for stat in image_counts
    }

    # 응답 생성
    response = []
    for session in sessions:
        img_info = image_data.get(session.id, {'count': 0, 'first_url': None})
        response.append(_build_session_list_response_v2(
            session=session,
            blog=blog_contents.get(session.id),
            sns=sns_contents.get(session.id),
            x=x_contents.get(session.id),
            threads=threads_contents.get(session.id),
            cardnews=cardnews_contents.get(session.id),
            image_count=img_info['count'],
            first_image_url=img_info['first_url']
        ))

    return response


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
        joinedload(ContentGenerationSession.cardnews_content),
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

    return {"message": "콘텐츠가 삭제되었습니다."}


# ============================================
# 헬퍼 함수
# ============================================

def _build_session_list_response_v2(
    session: ContentGenerationSession,
    blog: GeneratedBlogContent = None,
    sns: GeneratedSNSContent = None,
    x: GeneratedXContent = None,
    threads: GeneratedThreadsContent = None,
    cardnews: Dict[str, Any] = None,  # 이미 dict로 전달됨
    image_count: int = 0,
    first_image_url: str = None
) -> ContentSessionListResponse:
    """목록용 세션 응답 객체 생성 (v2 최적화 버전) - 별도 조회된 콘텐츠 사용"""
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
        blog={
            "id": blog.id,
            "title": blog.title,
            "content": blog.content[:200] if blog.content else "",
            "tags": blog.tags
        } if blog else None,
        sns={
            "id": sns.id,
            "content": sns.content[:200] if sns.content else "",
            "hashtags": sns.hashtags
        } if sns else None,
        x={
            "id": x.id,
            "content": x.content[:200] if x.content else "",
            "hashtags": x.hashtags
        } if x else None,
        threads={
            "id": threads.id,
            "content": threads.content[:200] if threads.content else "",
            "hashtags": threads.hashtags
        } if threads else None,
        cardnews=cardnews,  # 이미 dict 형태로 전달됨
        image_count=image_count,
        images=[{"image_url": first_image_url}] if first_image_url else None
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
        cardnews={
            "id": session.cardnews_content.id,
            "title": session.cardnews_content.title,
            "prompt": session.cardnews_content.prompt,
            "purpose": session.cardnews_content.purpose,
            "page_count": session.cardnews_content.page_count,
            "card_image_urls": session.cardnews_content.card_image_urls,
            "pages_data": session.cardnews_content.pages_data,
            "design_settings": session.cardnews_content.design_settings,
            "quality_score": session.cardnews_content.quality_score,
            "score": session.cardnews_content.score
        } if session.cardnews_content else None,
        images=[
            {"id": img.id, "image_url": img.image_url, "prompt": img.prompt}
            for img in session.images
        ] if session.images else None,
        requested_image_count=session.requested_image_count or 0
    )