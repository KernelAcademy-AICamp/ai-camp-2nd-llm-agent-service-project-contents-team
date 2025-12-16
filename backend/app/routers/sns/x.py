"""
X Router
- X(구 Twitter) 계정 연동 및 포스트 관리 API
"""
import os
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...database import get_db
from ...auth import get_current_user
from ...models import User, XConnection, XPost
from ...services.x_service import XService, sync_x_user_info, sync_x_posts, XTokenExpiredError
from ...logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/x", tags=["x"])


def auto_disconnect_x(db: Session, connection: XConnection, user_id: int):
    """토큰 만료 시 자동 연동 해제"""
    logger.info(f"Auto-disconnecting X for user {user_id} due to token expiration")
    db.query(XPost).filter(XPost.connection_id == connection.id).delete()
    db.delete(connection)
    db.commit()

# X API 설정
X_CLIENT_ID = os.getenv("X_CLIENT_ID")
X_CLIENT_SECRET = os.getenv("X_CLIENT_SECRET")
X_REDIRECT_URI = os.getenv("X_REDIRECT_URI", "http://localhost:8000/api/x/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# X OAuth 2.0 URLs
X_AUTH_URL = "https://twitter.com/i/oauth2/authorize"
X_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

# PKCE 코드 저장 (실제 프로덕션에서는 Redis 등 사용)
oauth_state_store = {}


# ===== Pydantic 스키마 =====

class XPostCreate(BaseModel):
    text: str
    reply_to: Optional[str] = None


class XConnectionResponse(BaseModel):
    id: int
    x_user_id: str
    username: Optional[str]
    name: Optional[str]
    description: Optional[str]
    profile_image_url: Optional[str]
    verified: bool
    followers_count: int
    following_count: int
    post_count: int
    is_active: bool
    last_synced_at: Optional[datetime]

    class Config:
        from_attributes = True


class XPostResponse(BaseModel):
    id: int
    post_id: str
    text: Optional[str]
    created_at: Optional[datetime]
    media_type: Optional[str]
    media_url: Optional[str]
    repost_count: int
    reply_count: int
    like_count: int
    quote_count: int
    impression_count: int

    class Config:
        from_attributes = True


# ===== PKCE 헬퍼 함수 =====

def generate_code_verifier() -> str:
    """PKCE code_verifier 생성"""
    return secrets.token_urlsafe(32)


def generate_code_challenge(verifier: str) -> str:
    """PKCE code_challenge 생성 (S256)"""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode()


# ===== OAuth 연동 엔드포인트 =====

@router.get("/connect")
async def connect_twitter(user_id: int):
    """X OAuth 2.0 연동 시작"""
    if not X_CLIENT_ID:
        raise HTTPException(status_code=500, detail="X API credentials not configured")

    # PKCE 생성
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    state = secrets.token_urlsafe(16)

    # 상태 저장 (프로덕션에서는 Redis 등 사용)
    oauth_state_store[state] = {
        "user_id": user_id,
        "code_verifier": code_verifier,
        "created_at": datetime.utcnow()
    }

    # X OAuth 2.0 인증 URL 생성
    scopes = "tweet.read tweet.write users.read offline.access"
    auth_url = (
        f"{X_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={X_CLIENT_ID}"
        f"&redirect_uri={X_REDIRECT_URI}"
        f"&scope={scopes}"
        f"&state={state}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )

    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def twitter_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """X OAuth 콜백 처리"""
    import httpx

    # 상태 검증
    if state not in oauth_state_store:
        return RedirectResponse(url=f"{FRONTEND_URL}/x?error=invalid_state")

    state_data = oauth_state_store.pop(state)
    user_id = state_data["user_id"]
    code_verifier = state_data["code_verifier"]

    # 사용자 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url=f"{FRONTEND_URL}/x?error=user_not_found")

    # 액세스 토큰 요청
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                X_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": X_REDIRECT_URI,
                    "code_verifier": code_verifier,
                    "client_id": X_CLIENT_ID,
                },
                auth=(X_CLIENT_ID, X_CLIENT_SECRET) if X_CLIENT_SECRET else None,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if token_response.status_code != 200:
                logger.error(f"X token error: {token_response.text}")
                return RedirectResponse(url=f"{FRONTEND_URL}/x?error=token_error")

            token_data = token_response.json()

    except Exception as e:
        logger.error(f"X OAuth error: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/x?error=oauth_error")

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 7200)  # 기본 2시간

    # X 사용자 정보 조회
    service = XService(access_token, refresh_token)
    user_info = await service.get_me()

    if not user_info:
        return RedirectResponse(url=f"{FRONTEND_URL}/x?error=user_info_error")

    # 기존 연동 확인 및 업데이트/생성
    connection = db.query(XConnection).filter(
        XConnection.user_id == user_id
    ).first()

    if connection:
        # 기존 연동 업데이트
        connection.x_user_id = user_info["id"]
        connection.username = user_info.get("username")
        connection.name = user_info.get("name")
        connection.description = user_info.get("description")
        connection.profile_image_url = user_info.get("profile_image_url")
        connection.verified = user_info.get("verified", False)
        connection.access_token = access_token
        connection.refresh_token = refresh_token
        connection.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        connection.is_active = True

        public_metrics = user_info.get("public_metrics", {})
        connection.followers_count = public_metrics.get("followers_count", 0)
        connection.following_count = public_metrics.get("following_count", 0)
        connection.post_count = public_metrics.get("tweet_count", 0)
        connection.listed_count = public_metrics.get("listed_count", 0)
    else:
        # 새 연동 생성
        public_metrics = user_info.get("public_metrics", {})
        connection = XConnection(
            user_id=user_id,
            x_user_id=user_info["id"],
            username=user_info.get("username"),
            name=user_info.get("name"),
            description=user_info.get("description"),
            profile_image_url=user_info.get("profile_image_url"),
            verified=user_info.get("verified", False),
            followers_count=public_metrics.get("followers_count", 0),
            following_count=public_metrics.get("following_count", 0),
            post_count=public_metrics.get("tweet_count", 0),
            listed_count=public_metrics.get("listed_count", 0),
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
            is_active=True
        )
        db.add(connection)

    connection.last_synced_at = datetime.utcnow()
    db.commit()

    logger.info(f"X connected for user {user_id}: @{connection.username}")
    return RedirectResponse(url=f"{FRONTEND_URL}/x?connected=true")


# ===== 연동 상태 API =====

@router.get("/status", response_model=Optional[XConnectionResponse])
async def get_x_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """X 연동 상태 확인"""
    connection = db.query(XConnection).filter(
        XConnection.user_id == current_user.id,
        XConnection.is_active == True
    ).first()

    return connection


@router.delete("/disconnect")
async def disconnect_x(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """X 연동 해제"""
    connection = db.query(XConnection).filter(
        XConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="X connection not found")

    # 연관된 포스트도 삭제
    db.query(XPost).filter(XPost.connection_id == connection.id).delete()
    db.delete(connection)
    db.commit()

    logger.info(f"X disconnected for user {current_user.id}")
    return {"message": "X disconnected successfully"}


@router.post("/refresh")
async def refresh_x_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """X 계정 정보 새로고침"""
    connection = db.query(XConnection).filter(
        XConnection.user_id == current_user.id,
        XConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="X connection not found")

    try:
        service = XService(connection.access_token, connection.refresh_token)
        success = await sync_x_user_info(db, connection, service)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to refresh X info")

        db.refresh(connection)
        return connection
    except XTokenExpiredError:
        auto_disconnect_x(db, connection, current_user.id)
        raise HTTPException(
            status_code=401,
            detail="X 토큰이 만료되었습니다. 다시 연동해주세요."
        )


# ===== 포스트 API =====

@router.get("/posts")
async def get_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """포스트 목록 조회"""
    connection = db.query(XConnection).filter(
        XConnection.user_id == current_user.id,
        XConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="X connection not found")

    posts = db.query(XPost).filter(
        XPost.connection_id == connection.id
    ).order_by(XPost.created_at_x.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": p.id,
            "post_id": p.post_id,
            "text": p.text,
            "created_at": p.created_at_x,
            "media_type": p.media_type,
            "media_url": p.media_url,
            "repost_count": p.repost_count,
            "reply_count": p.reply_count,
            "like_count": p.like_count,
            "quote_count": p.quote_count,
            "impression_count": p.impression_count
        }
        for p in posts
    ]


@router.post("/posts/sync")
async def sync_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """포스트 동기화"""
    connection = db.query(XConnection).filter(
        XConnection.user_id == current_user.id,
        XConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="X connection not found")

    try:
        service = XService(connection.access_token, connection.refresh_token)
        synced_count = await sync_x_posts(db, connection, service)
        return {"synced_count": synced_count, "message": f"Synced {synced_count} posts"}
    except XTokenExpiredError:
        # 토큰 만료 - 자동 연동 해제
        auto_disconnect_x(db, connection, current_user.id)
        raise HTTPException(
            status_code=401,
            detail="X 토큰이 만료되었습니다. 다시 연동해주세요."
        )


@router.post("/posts/create")
async def create_post(
    post_data: XPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """새 포스트 작성"""
    connection = db.query(XConnection).filter(
        XConnection.user_id == current_user.id,
        XConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="X connection not found")

    # 텍스트 길이 검증
    if len(post_data.text) > 280:
        raise HTTPException(status_code=400, detail="Post exceeds 280 characters")

    try:
        service = XService(connection.access_token, connection.refresh_token)
        result = await service.create_tweet(post_data.text, post_data.reply_to)

        if not result:
            raise HTTPException(status_code=500, detail="Failed to create post")

        # 로컬 DB에 포스트 저장
        new_post = XPost(
            connection_id=connection.id,
            user_id=current_user.id,
            post_id=result["id"],
            text=post_data.text,
            created_at_x=datetime.utcnow()
        )
        db.add(new_post)
        db.commit()

        logger.info(f"Post created for user {current_user.id}: {result['id']}")
        return {"post_id": result["id"], "message": "Post created successfully"}
    except XTokenExpiredError:
        auto_disconnect_x(db, connection, current_user.id)
        raise HTTPException(
            status_code=401,
            detail="X 토큰이 만료되었습니다. 다시 연동해주세요."
        )


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """포스트 삭제"""
    connection = db.query(XConnection).filter(
        XConnection.user_id == current_user.id,
        XConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="X connection not found")

    # 로컬 포스트 확인
    post = db.query(XPost).filter(
        XPost.post_id == post_id,
        XPost.connection_id == connection.id
    ).first()

    try:
        service = XService(connection.access_token, connection.refresh_token)
        success = await service.delete_tweet(post_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete post")

        # 로컬 DB에서 삭제
        if post:
            db.delete(post)
            db.commit()

        logger.info(f"Post deleted for user {current_user.id}: {post_id}")
        return {"message": "Post deleted successfully"}
    except XTokenExpiredError:
        auto_disconnect_x(db, connection, current_user.id)
        raise HTTPException(
            status_code=401,
            detail="X 토큰이 만료되었습니다. 다시 연동해주세요."
        )


# ===== 분석 API =====

@router.get("/analytics")
async def get_x_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """X 분석 데이터 (기본 통계)"""
    connection = db.query(XConnection).filter(
        XConnection.user_id == current_user.id,
        XConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="X connection not found")

    # 최근 포스트 통계 집계
    from sqlalchemy import func

    stats = db.query(
        func.count(XPost.id).label("total_posts"),
        func.sum(XPost.like_count).label("total_likes"),
        func.sum(XPost.repost_count).label("total_reposts"),
        func.sum(XPost.reply_count).label("total_replies"),
        func.sum(XPost.impression_count).label("total_impressions"),
        func.avg(XPost.like_count).label("avg_likes"),
        func.avg(XPost.repost_count).label("avg_reposts")
    ).filter(XPost.connection_id == connection.id).first()

    return {
        "account": {
            "username": connection.username,
            "name": connection.name,
            "followers_count": connection.followers_count,
            "following_count": connection.following_count,
            "post_count": connection.post_count
        },
        "stats": {
            "total_posts_synced": stats.total_posts or 0,
            "total_likes": stats.total_likes or 0,
            "total_reposts": stats.total_reposts or 0,
            "total_replies": stats.total_replies or 0,
            "total_impressions": stats.total_impressions or 0,
            "avg_likes_per_post": round(stats.avg_likes or 0, 1),
            "avg_reposts_per_post": round(stats.avg_reposts or 0, 1)
        },
        "last_synced_at": connection.last_synced_at
    }
