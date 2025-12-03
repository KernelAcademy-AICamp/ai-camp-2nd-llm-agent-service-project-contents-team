"""
Twitter(X) Router
- Twitter 계정 연동 및 트윗 관리 API
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

from ..database import get_db
from ..auth import get_current_user
from ..models import User, TwitterConnection, Tweet
from ..services.twitter_service import TwitterService, sync_twitter_user_info, sync_twitter_tweets
from ..logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/twitter", tags=["twitter"])

# Twitter API 설정
TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")
TWITTER_REDIRECT_URI = os.getenv("TWITTER_REDIRECT_URI", "http://localhost:8000/api/twitter/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Twitter OAuth 2.0 URLs
TWITTER_AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TWITTER_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

# PKCE 코드 저장 (실제 프로덕션에서는 Redis 등 사용)
oauth_state_store = {}


# ===== Pydantic 스키마 =====

class TweetCreate(BaseModel):
    text: str
    reply_to: Optional[str] = None


class TwitterConnectionResponse(BaseModel):
    id: int
    twitter_user_id: str
    username: Optional[str]
    name: Optional[str]
    description: Optional[str]
    profile_image_url: Optional[str]
    verified: bool
    followers_count: int
    following_count: int
    tweet_count: int
    is_active: bool
    last_synced_at: Optional[datetime]

    class Config:
        from_attributes = True


class TweetResponse(BaseModel):
    id: int
    tweet_id: str
    text: Optional[str]
    created_at: Optional[datetime]
    media_type: Optional[str]
    media_url: Optional[str]
    retweet_count: int
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
    """Twitter OAuth 2.0 연동 시작"""
    if not TWITTER_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Twitter API credentials not configured")

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

    # Twitter OAuth 2.0 인증 URL 생성
    scopes = "tweet.read tweet.write users.read offline.access"
    auth_url = (
        f"{TWITTER_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={TWITTER_CLIENT_ID}"
        f"&redirect_uri={TWITTER_REDIRECT_URI}"
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
    """Twitter OAuth 콜백 처리"""
    import httpx

    # 상태 검증
    if state not in oauth_state_store:
        return RedirectResponse(url=f"{FRONTEND_URL}/twitter?error=invalid_state")

    state_data = oauth_state_store.pop(state)
    user_id = state_data["user_id"]
    code_verifier = state_data["code_verifier"]

    # 사용자 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url=f"{FRONTEND_URL}/twitter?error=user_not_found")

    # 액세스 토큰 요청
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                TWITTER_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": TWITTER_REDIRECT_URI,
                    "code_verifier": code_verifier,
                    "client_id": TWITTER_CLIENT_ID,
                },
                auth=(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET) if TWITTER_CLIENT_SECRET else None,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if token_response.status_code != 200:
                logger.error(f"Twitter token error: {token_response.text}")
                return RedirectResponse(url=f"{FRONTEND_URL}/twitter?error=token_error")

            token_data = token_response.json()

    except Exception as e:
        logger.error(f"Twitter OAuth error: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/twitter?error=oauth_error")

    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 7200)  # 기본 2시간

    # Twitter 사용자 정보 조회
    service = TwitterService(access_token, refresh_token)
    user_info = await service.get_me()

    if not user_info:
        return RedirectResponse(url=f"{FRONTEND_URL}/twitter?error=user_info_error")

    # 기존 연동 확인 및 업데이트/생성
    connection = db.query(TwitterConnection).filter(
        TwitterConnection.user_id == user_id
    ).first()

    if connection:
        # 기존 연동 업데이트
        connection.twitter_user_id = user_info["id"]
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
        connection.tweet_count = public_metrics.get("tweet_count", 0)
        connection.listed_count = public_metrics.get("listed_count", 0)
    else:
        # 새 연동 생성
        public_metrics = user_info.get("public_metrics", {})
        connection = TwitterConnection(
            user_id=user_id,
            twitter_user_id=user_info["id"],
            username=user_info.get("username"),
            name=user_info.get("name"),
            description=user_info.get("description"),
            profile_image_url=user_info.get("profile_image_url"),
            verified=user_info.get("verified", False),
            followers_count=public_metrics.get("followers_count", 0),
            following_count=public_metrics.get("following_count", 0),
            tweet_count=public_metrics.get("tweet_count", 0),
            listed_count=public_metrics.get("listed_count", 0),
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
            is_active=True
        )
        db.add(connection)

    connection.last_synced_at = datetime.utcnow()
    db.commit()

    logger.info(f"Twitter connected for user {user_id}: @{connection.username}")
    return RedirectResponse(url=f"{FRONTEND_URL}/twitter?connected=true")


# ===== 연동 상태 API =====

@router.get("/status", response_model=Optional[TwitterConnectionResponse])
async def get_twitter_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Twitter 연동 상태 확인"""
    connection = db.query(TwitterConnection).filter(
        TwitterConnection.user_id == current_user.id,
        TwitterConnection.is_active == True
    ).first()

    return connection


@router.delete("/disconnect")
async def disconnect_twitter(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Twitter 연동 해제"""
    connection = db.query(TwitterConnection).filter(
        TwitterConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Twitter connection not found")

    # 연관된 트윗도 삭제
    db.query(Tweet).filter(Tweet.connection_id == connection.id).delete()
    db.delete(connection)
    db.commit()

    logger.info(f"Twitter disconnected for user {current_user.id}")
    return {"message": "Twitter disconnected successfully"}


@router.post("/refresh")
async def refresh_twitter_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Twitter 계정 정보 새로고침"""
    connection = db.query(TwitterConnection).filter(
        TwitterConnection.user_id == current_user.id,
        TwitterConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Twitter connection not found")

    service = TwitterService(connection.access_token, connection.refresh_token)
    success = await sync_twitter_user_info(db, connection, service)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to refresh Twitter info")

    db.refresh(connection)
    return connection


# ===== 트윗 API =====

@router.get("/tweets")
async def get_tweets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """트윗 목록 조회"""
    connection = db.query(TwitterConnection).filter(
        TwitterConnection.user_id == current_user.id,
        TwitterConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Twitter connection not found")

    tweets = db.query(Tweet).filter(
        Tweet.connection_id == connection.id
    ).order_by(Tweet.created_at_twitter.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": t.id,
            "tweet_id": t.tweet_id,
            "text": t.text,
            "created_at": t.created_at_twitter,
            "media_type": t.media_type,
            "media_url": t.media_url,
            "retweet_count": t.retweet_count,
            "reply_count": t.reply_count,
            "like_count": t.like_count,
            "quote_count": t.quote_count,
            "impression_count": t.impression_count
        }
        for t in tweets
    ]


@router.post("/tweets/sync")
async def sync_tweets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """트윗 동기화"""
    connection = db.query(TwitterConnection).filter(
        TwitterConnection.user_id == current_user.id,
        TwitterConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Twitter connection not found")

    service = TwitterService(connection.access_token, connection.refresh_token)
    synced_count = await sync_twitter_tweets(db, connection, service)

    return {"synced_count": synced_count, "message": f"Synced {synced_count} tweets"}


@router.post("/tweets/create")
async def create_tweet(
    tweet_data: TweetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """새 트윗 작성"""
    connection = db.query(TwitterConnection).filter(
        TwitterConnection.user_id == current_user.id,
        TwitterConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Twitter connection not found")

    # 텍스트 길이 검증
    if len(tweet_data.text) > 280:
        raise HTTPException(status_code=400, detail="Tweet exceeds 280 characters")

    service = TwitterService(connection.access_token, connection.refresh_token)
    result = await service.create_tweet(tweet_data.text, tweet_data.reply_to)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to create tweet")

    # 로컬 DB에 트윗 저장
    new_tweet = Tweet(
        connection_id=connection.id,
        user_id=current_user.id,
        tweet_id=result["id"],
        text=tweet_data.text,
        created_at_twitter=datetime.utcnow()
    )
    db.add(new_tweet)
    db.commit()

    logger.info(f"Tweet created for user {current_user.id}: {result['id']}")
    return {"tweet_id": result["id"], "message": "Tweet created successfully"}


@router.delete("/tweets/{tweet_id}")
async def delete_tweet(
    tweet_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """트윗 삭제"""
    connection = db.query(TwitterConnection).filter(
        TwitterConnection.user_id == current_user.id,
        TwitterConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Twitter connection not found")

    # 로컬 트윗 확인
    tweet = db.query(Tweet).filter(
        Tweet.tweet_id == tweet_id,
        Tweet.connection_id == connection.id
    ).first()

    service = TwitterService(connection.access_token, connection.refresh_token)
    success = await service.delete_tweet(tweet_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete tweet")

    # 로컬 DB에서 삭제
    if tweet:
        db.delete(tweet)
        db.commit()

    logger.info(f"Tweet deleted for user {current_user.id}: {tweet_id}")
    return {"message": "Tweet deleted successfully"}


# ===== 분석 API =====

@router.get("/analytics")
async def get_twitter_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Twitter 분석 데이터 (기본 통계)"""
    connection = db.query(TwitterConnection).filter(
        TwitterConnection.user_id == current_user.id,
        TwitterConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Twitter connection not found")

    # 최근 트윗 통계 집계
    from sqlalchemy import func

    stats = db.query(
        func.count(Tweet.id).label("total_tweets"),
        func.sum(Tweet.like_count).label("total_likes"),
        func.sum(Tweet.retweet_count).label("total_retweets"),
        func.sum(Tweet.reply_count).label("total_replies"),
        func.sum(Tweet.impression_count).label("total_impressions"),
        func.avg(Tweet.like_count).label("avg_likes"),
        func.avg(Tweet.retweet_count).label("avg_retweets")
    ).filter(Tweet.connection_id == connection.id).first()

    return {
        "account": {
            "username": connection.username,
            "name": connection.name,
            "followers_count": connection.followers_count,
            "following_count": connection.following_count,
            "tweet_count": connection.tweet_count
        },
        "stats": {
            "total_tweets_synced": stats.total_tweets or 0,
            "total_likes": stats.total_likes or 0,
            "total_retweets": stats.total_retweets or 0,
            "total_replies": stats.total_replies or 0,
            "total_impressions": stats.total_impressions or 0,
            "avg_likes_per_tweet": round(stats.avg_likes or 0, 1),
            "avg_retweets_per_tweet": round(stats.avg_retweets or 0, 1)
        },
        "last_synced_at": connection.last_synced_at
    }
