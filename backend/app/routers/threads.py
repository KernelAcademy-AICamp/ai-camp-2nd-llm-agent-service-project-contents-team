"""
Threads Router
- Threads 계정 연동 및 포스트 관리 API
"""
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..auth import get_current_user
from ..models import User, ThreadsConnection, ThreadsPost
from ..services.threads_service import (
    ThreadsService,
    sync_threads_user_info,
    sync_threads_posts
)
from ..logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/threads", tags=["threads"])

# Threads API 설정
THREADS_APP_ID = os.getenv("THREADS_APP_ID")
THREADS_APP_SECRET = os.getenv("THREADS_APP_SECRET")
THREADS_REDIRECT_URI = os.getenv("THREADS_REDIRECT_URI", "http://localhost:8000/api/threads/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Threads OAuth URLs
THREADS_AUTH_URL = "https://threads.net/oauth/authorize"
THREADS_TOKEN_URL = "https://graph.threads.net/oauth/access_token"

# OAuth 상태 저장 (프로덕션에서는 Redis 등 사용)
oauth_state_store = {}


# ===== Pydantic 스키마 =====

class ThreadsPostCreate(BaseModel):
    text: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None


class ThreadsConnectionResponse(BaseModel):
    id: int
    threads_user_id: str
    username: Optional[str]
    name: Optional[str]
    threads_profile_picture_url: Optional[str]
    threads_biography: Optional[str]
    followers_count: int
    is_active: bool
    last_synced_at: Optional[datetime]

    class Config:
        from_attributes = True


class ThreadsPostResponse(BaseModel):
    id: int
    threads_post_id: str
    text: Optional[str]
    media_type: Optional[str]
    media_url: Optional[str]
    permalink: Optional[str]
    timestamp: Optional[datetime]
    like_count: int
    reply_count: int
    repost_count: int
    quote_count: int
    views_count: int

    class Config:
        from_attributes = True


# ===== OAuth 연동 엔드포인트 =====

@router.get("/connect")
async def connect_threads(user_id: int):
    """Threads OAuth 연동 시작"""
    if not THREADS_APP_ID:
        raise HTTPException(status_code=500, detail="Threads API credentials not configured")

    state = secrets.token_urlsafe(16)

    # 상태 저장
    oauth_state_store[state] = {
        "user_id": user_id,
        "created_at": datetime.utcnow()
    }

    # Threads OAuth 인증 URL 생성
    # 필요한 권한: threads_basic, threads_content_publish, threads_manage_insights
    scopes = "threads_basic,threads_content_publish,threads_manage_insights"
    auth_url = (
        f"{THREADS_AUTH_URL}"
        f"?client_id={THREADS_APP_ID}"
        f"&redirect_uri={THREADS_REDIRECT_URI}"
        f"&scope={scopes}"
        f"&response_type=code"
        f"&state={state}"
    )

    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def threads_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """Threads OAuth 콜백 처리"""
    # 상태 검증
    if state not in oauth_state_store:
        return RedirectResponse(url=f"{FRONTEND_URL}/threads?error=invalid_state")

    state_data = oauth_state_store.pop(state)
    user_id = state_data["user_id"]

    # 사용자 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url=f"{FRONTEND_URL}/threads?error=user_not_found")

    # 액세스 토큰 교환
    token_data = await ThreadsService.exchange_code_for_token(code, THREADS_REDIRECT_URI)
    if not token_data:
        return RedirectResponse(url=f"{FRONTEND_URL}/threads?error=token_error")

    access_token = token_data.get("access_token")
    threads_user_id = token_data.get("user_id")

    if not access_token:
        return RedirectResponse(url=f"{FRONTEND_URL}/threads?error=no_access_token")

    # 장기 토큰으로 교환
    long_lived_token_data = await ThreadsService.get_long_lived_token(access_token)
    if long_lived_token_data:
        access_token = long_lived_token_data.get("access_token", access_token)
        expires_in = long_lived_token_data.get("expires_in", 5184000)  # 기본 60일
    else:
        expires_in = 3600  # 단기 토큰 (1시간)

    # Threads 사용자 정보 조회
    service = ThreadsService(access_token, threads_user_id)
    user_info = await service.get_me()

    if not user_info:
        return RedirectResponse(url=f"{FRONTEND_URL}/threads?error=user_info_error")

    # 기존 연동 확인 및 업데이트/생성
    connection = db.query(ThreadsConnection).filter(
        ThreadsConnection.user_id == user_id
    ).first()

    if connection:
        # 기존 연동 업데이트
        connection.threads_user_id = user_info.get("id", threads_user_id)
        connection.username = user_info.get("username")
        connection.name = user_info.get("name")
        connection.threads_profile_picture_url = user_info.get("threads_profile_picture_url")
        connection.threads_biography = user_info.get("threads_biography")
        connection.access_token = access_token
        connection.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        connection.is_active = True
    else:
        # 새 연동 생성
        connection = ThreadsConnection(
            user_id=user_id,
            threads_user_id=user_info.get("id", threads_user_id),
            username=user_info.get("username"),
            name=user_info.get("name"),
            threads_profile_picture_url=user_info.get("threads_profile_picture_url"),
            threads_biography=user_info.get("threads_biography"),
            access_token=access_token,
            token_expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
            is_active=True
        )
        db.add(connection)

    connection.last_synced_at = datetime.utcnow()
    db.commit()

    logger.info(f"Threads connected for user {user_id}: @{connection.username}")
    return RedirectResponse(url=f"{FRONTEND_URL}/threads?connected=true")


# ===== 연동 상태 API =====

@router.get("/status", response_model=Optional[ThreadsConnectionResponse])
async def get_threads_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Threads 연동 상태 확인"""
    connection = db.query(ThreadsConnection).filter(
        ThreadsConnection.user_id == current_user.id,
        ThreadsConnection.is_active == True
    ).first()

    return connection


@router.delete("/disconnect")
async def disconnect_threads(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Threads 연동 해제"""
    connection = db.query(ThreadsConnection).filter(
        ThreadsConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Threads connection not found")

    # 연관된 포스트도 삭제
    db.query(ThreadsPost).filter(ThreadsPost.connection_id == connection.id).delete()
    db.delete(connection)
    db.commit()

    logger.info(f"Threads disconnected for user {current_user.id}")
    return {"message": "Threads disconnected successfully"}


@router.post("/refresh")
async def refresh_threads_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Threads 계정 정보 새로고침"""
    connection = db.query(ThreadsConnection).filter(
        ThreadsConnection.user_id == current_user.id,
        ThreadsConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Threads connection not found")

    # 토큰 만료 체크 및 갱신
    if connection.token_expires_at and connection.token_expires_at < datetime.utcnow() + timedelta(days=7):
        # 토큰 갱신
        new_token_data = await ThreadsService.refresh_long_lived_token(connection.access_token)
        if new_token_data:
            connection.access_token = new_token_data.get("access_token", connection.access_token)
            connection.token_expires_at = datetime.utcnow() + timedelta(
                seconds=new_token_data.get("expires_in", 5184000)
            )
            db.commit()

    service = ThreadsService(connection.access_token, connection.threads_user_id)
    success = await sync_threads_user_info(db, connection, service)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to refresh Threads info")

    db.refresh(connection)
    return connection


# ===== 포스트 API =====

@router.get("/posts")
async def get_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """포스트 목록 조회"""
    connection = db.query(ThreadsConnection).filter(
        ThreadsConnection.user_id == current_user.id,
        ThreadsConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Threads connection not found")

    posts = db.query(ThreadsPost).filter(
        ThreadsPost.connection_id == connection.id
    ).order_by(ThreadsPost.timestamp.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": p.id,
            "threads_post_id": p.threads_post_id,
            "text": p.text,
            "media_type": p.media_type,
            "media_url": p.media_url,
            "thumbnail_url": p.thumbnail_url,
            "permalink": p.permalink,
            "timestamp": p.timestamp,
            "like_count": p.like_count,
            "reply_count": p.reply_count,
            "repost_count": p.repost_count,
            "quote_count": p.quote_count,
            "views_count": p.views_count
        }
        for p in posts
    ]


@router.post("/posts/sync")
async def sync_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """포스트 동기화"""
    connection = db.query(ThreadsConnection).filter(
        ThreadsConnection.user_id == current_user.id,
        ThreadsConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Threads connection not found")

    service = ThreadsService(connection.access_token, connection.threads_user_id)
    synced_count = await sync_threads_posts(db, connection, service)

    return {"synced_count": synced_count, "message": f"Synced {synced_count} posts"}


@router.post("/posts/create")
async def create_post(
    post_data: ThreadsPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """새 Threads 포스트 작성"""
    connection = db.query(ThreadsConnection).filter(
        ThreadsConnection.user_id == current_user.id,
        ThreadsConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Threads connection not found")

    # 텍스트 길이 검증 (Threads는 500자 제한)
    if post_data.text and len(post_data.text) > 500:
        raise HTTPException(status_code=400, detail="Post exceeds 500 characters")

    # 최소 하나의 콘텐츠가 있어야 함
    if not post_data.text and not post_data.image_url and not post_data.video_url:
        raise HTTPException(status_code=400, detail="Post must have text, image, or video")

    service = ThreadsService(connection.access_token, connection.threads_user_id)
    result = await service.create_and_publish_thread(
        user_id=connection.threads_user_id,
        text=post_data.text,
        image_url=post_data.image_url,
        video_url=post_data.video_url
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to create post")

    # 로컬 DB에 포스트 저장
    media_type = "TEXT"
    if post_data.video_url:
        media_type = "VIDEO"
    elif post_data.image_url:
        media_type = "IMAGE"

    new_post = ThreadsPost(
        connection_id=connection.id,
        user_id=current_user.id,
        threads_post_id=result.get("id", ""),
        text=post_data.text,
        media_type=media_type,
        media_url=post_data.image_url or post_data.video_url,
        timestamp=datetime.utcnow()
    )
    db.add(new_post)
    db.commit()

    logger.info(f"Threads post created for user {current_user.id}: {result.get('id')}")
    return {"post_id": result.get("id"), "message": "Post created successfully"}


# ===== 분석 API =====

@router.get("/analytics")
async def get_threads_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Threads 분석 데이터 (기본 통계)"""
    connection = db.query(ThreadsConnection).filter(
        ThreadsConnection.user_id == current_user.id,
        ThreadsConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Threads connection not found")

    # 최근 포스트 통계 집계
    from sqlalchemy import func

    stats = db.query(
        func.count(ThreadsPost.id).label("total_posts"),
        func.sum(ThreadsPost.like_count).label("total_likes"),
        func.sum(ThreadsPost.reply_count).label("total_replies"),
        func.sum(ThreadsPost.repost_count).label("total_reposts"),
        func.sum(ThreadsPost.views_count).label("total_views"),
        func.avg(ThreadsPost.like_count).label("avg_likes"),
        func.avg(ThreadsPost.views_count).label("avg_views")
    ).filter(ThreadsPost.connection_id == connection.id).first()

    return {
        "account": {
            "username": connection.username,
            "name": connection.name,
            "followers_count": connection.followers_count,
            "profile_picture_url": connection.threads_profile_picture_url
        },
        "stats": {
            "total_posts_synced": stats.total_posts or 0,
            "total_likes": stats.total_likes or 0,
            "total_replies": stats.total_replies or 0,
            "total_reposts": stats.total_reposts or 0,
            "total_views": stats.total_views or 0,
            "avg_likes_per_post": round(stats.avg_likes or 0, 1),
            "avg_views_per_post": round(stats.avg_views or 0, 1)
        },
        "last_synced_at": connection.last_synced_at
    }
