"""
TikTok API 라우터
- TikTok for Business API를 사용한 OAuth 2.0 연동
- 동영상 업로드, 목록 조회, 통계 확인
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
import httpx
import os

from ..database import get_db
from ..models import User, TikTokConnection, TikTokVideo
from .. import auth

router = APIRouter(prefix="/api/tiktok", tags=["TikTok"])

# TikTok API 설정
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
TIKTOK_REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:8000/api/tiktok/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# TikTok API 엔드포인트
TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_USER_INFO_URL = "https://open.tiktokapis.com/v2/user/info/"
TIKTOK_VIDEO_LIST_URL = "https://open.tiktokapis.com/v2/video/list/"
TIKTOK_VIDEO_UPLOAD_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"


def get_current_user(user_id: int, db: Session) -> User:
    """사용자 조회"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/connect")
async def connect_tiktok(user_id: int = Query(...)):
    """
    TikTok OAuth 연동 시작
    - TikTok 로그인 페이지로 리다이렉트
    """
    if not TIKTOK_CLIENT_KEY:
        raise HTTPException(status_code=500, detail="TikTok API credentials not configured")

    # OAuth 2.0 인증 URL 생성
    # 필요한 스코프: user.info.basic, video.list, video.upload
    scope = "user.info.basic,video.list,video.publish"

    auth_url = (
        f"{TIKTOK_AUTH_URL}"
        f"?client_key={TIKTOK_CLIENT_KEY}"
        f"&response_type=code"
        f"&scope={scope}"
        f"&redirect_uri={TIKTOK_REDIRECT_URI}"
        f"&state={user_id}"
    )

    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def tiktok_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    TikTok OAuth 콜백 처리
    """
    if error:
        return RedirectResponse(url=f"{FRONTEND_URL}/tiktok?error={error}")

    if not code or not state:
        return RedirectResponse(url=f"{FRONTEND_URL}/tiktok?error=missing_params")

    try:
        user_id = int(state)
        user = get_current_user(user_id, db)

        # 액세스 토큰 요청
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                TIKTOK_TOKEN_URL,
                data={
                    "client_key": TIKTOK_CLIENT_KEY,
                    "client_secret": TIKTOK_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": TIKTOK_REDIRECT_URI
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

        if token_response.status_code != 200:
            return RedirectResponse(url=f"{FRONTEND_URL}/tiktok?error=token_failed")

        token_data = token_response.json()

        if "error" in token_data:
            return RedirectResponse(url=f"{FRONTEND_URL}/tiktok?error={token_data.get('error')}")

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 86400)
        open_id = token_data.get("open_id")

        # 사용자 정보 조회
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                TIKTOK_USER_INFO_URL,
                params={"fields": "open_id,union_id,avatar_url,display_name,bio_description,profile_deep_link,follower_count,following_count,likes_count,video_count"},
                headers={"Authorization": f"Bearer {access_token}"}
            )

        user_info = {}
        if user_response.status_code == 200:
            response_data = user_response.json()
            user_info = response_data.get("data", {}).get("user", {})

        # 기존 연동 확인
        existing_connection = db.query(TikTokConnection).filter(
            TikTokConnection.user_id == user_id
        ).first()

        token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        if existing_connection:
            # 업데이트
            existing_connection.tiktok_user_id = open_id
            existing_connection.union_id = user_info.get("union_id")
            existing_connection.username = user_info.get("display_name")
            existing_connection.avatar_url = user_info.get("avatar_url")
            existing_connection.bio_description = user_info.get("bio_description")
            existing_connection.profile_deep_link = user_info.get("profile_deep_link")
            existing_connection.follower_count = user_info.get("follower_count", 0)
            existing_connection.following_count = user_info.get("following_count", 0)
            existing_connection.likes_count = user_info.get("likes_count", 0)
            existing_connection.video_count = user_info.get("video_count", 0)
            existing_connection.access_token = access_token
            existing_connection.refresh_token = refresh_token
            existing_connection.token_expires_at = token_expires_at
            existing_connection.is_active = True
            existing_connection.last_synced_at = datetime.utcnow()
        else:
            # 새로 생성
            new_connection = TikTokConnection(
                user_id=user_id,
                tiktok_user_id=open_id,
                union_id=user_info.get("union_id"),
                username=user_info.get("display_name"),
                avatar_url=user_info.get("avatar_url"),
                bio_description=user_info.get("bio_description"),
                profile_deep_link=user_info.get("profile_deep_link"),
                follower_count=user_info.get("follower_count", 0),
                following_count=user_info.get("following_count", 0),
                likes_count=user_info.get("likes_count", 0),
                video_count=user_info.get("video_count", 0),
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=token_expires_at,
                is_active=True,
                last_synced_at=datetime.utcnow()
            )
            db.add(new_connection)

        db.commit()
        return RedirectResponse(url=f"{FRONTEND_URL}/tiktok?connected=true")

    except Exception as e:
        print(f"TikTok callback error: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/tiktok?error=callback_failed")


@router.get("/status")
async def get_tiktok_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    TikTok 연동 상태 확인
    """
    connection = db.query(TikTokConnection).filter(
        TikTokConnection.user_id == current_user.id,
        TikTokConnection.is_active == True
    ).first()

    if not connection:
        return None

    return {
        "tiktok_user_id": connection.tiktok_user_id,
        "username": connection.username,
        "avatar_url": connection.avatar_url,
        "bio_description": connection.bio_description,
        "profile_deep_link": connection.profile_deep_link,
        "follower_count": connection.follower_count,
        "following_count": connection.following_count,
        "likes_count": connection.likes_count,
        "video_count": connection.video_count,
        "last_synced_at": connection.last_synced_at.isoformat() if connection.last_synced_at else None
    }


@router.delete("/disconnect")
async def disconnect_tiktok(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    TikTok 연동 해제
    """
    connection = db.query(TikTokConnection).filter(
        TikTokConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="TikTok connection not found")

    db.delete(connection)
    db.commit()

    return {"message": "TikTok disconnected successfully"}


@router.post("/refresh")
async def refresh_tiktok_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    TikTok 계정 정보 새로고침
    """
    connection = db.query(TikTokConnection).filter(
        TikTokConnection.user_id == current_user.id,
        TikTokConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="TikTok connection not found")

    # 토큰 갱신 필요 여부 확인
    if connection.token_expires_at and connection.token_expires_at < datetime.utcnow():
        # 토큰 갱신
        if connection.refresh_token:
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    TIKTOK_TOKEN_URL,
                    data={
                        "client_key": TIKTOK_CLIENT_KEY,
                        "client_secret": TIKTOK_CLIENT_SECRET,
                        "grant_type": "refresh_token",
                        "refresh_token": connection.refresh_token
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )

            if token_response.status_code == 200:
                token_data = token_response.json()
                connection.access_token = token_data.get("access_token", connection.access_token)
                connection.refresh_token = token_data.get("refresh_token", connection.refresh_token)
                expires_in = token_data.get("expires_in", 86400)
                connection.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    # 사용자 정보 조회
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            TIKTOK_USER_INFO_URL,
            params={"fields": "open_id,union_id,avatar_url,display_name,bio_description,profile_deep_link,follower_count,following_count,likes_count,video_count"},
            headers={"Authorization": f"Bearer {connection.access_token}"}
        )

    if user_response.status_code == 200:
        response_data = user_response.json()
        user_info = response_data.get("data", {}).get("user", {})

        connection.username = user_info.get("display_name", connection.username)
        connection.avatar_url = user_info.get("avatar_url", connection.avatar_url)
        connection.bio_description = user_info.get("bio_description", connection.bio_description)
        connection.profile_deep_link = user_info.get("profile_deep_link", connection.profile_deep_link)
        connection.follower_count = user_info.get("follower_count", connection.follower_count)
        connection.following_count = user_info.get("following_count", connection.following_count)
        connection.likes_count = user_info.get("likes_count", connection.likes_count)
        connection.video_count = user_info.get("video_count", connection.video_count)
        connection.last_synced_at = datetime.utcnow()

    db.commit()
    db.refresh(connection)

    return {
        "message": "TikTok info refreshed",
        "username": connection.username,
        "follower_count": connection.follower_count,
        "video_count": connection.video_count
    }


@router.get("/videos")
async def get_tiktok_videos(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    TikTok 동영상 목록 조회 (DB에서)
    """
    connection = db.query(TikTokConnection).filter(
        TikTokConnection.user_id == current_user.id,
        TikTokConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="TikTok connection not found")

    videos = db.query(TikTokVideo).filter(
        TikTokVideo.connection_id == connection.id
    ).order_by(TikTokVideo.create_time.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": video.id,
            "video_id": video.video_id,
            "title": video.title,
            "description": video.description,
            "cover_image_url": video.cover_image_url,
            "share_url": video.share_url,
            "duration": video.duration,
            "view_count": video.view_count,
            "like_count": video.like_count,
            "comment_count": video.comment_count,
            "share_count": video.share_count,
            "create_time": video.create_time.isoformat() if video.create_time else None
        }
        for video in videos
    ]


@router.post("/videos/sync")
async def sync_tiktok_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    TikTok에서 동영상 목록 동기화
    """
    connection = db.query(TikTokConnection).filter(
        TikTokConnection.user_id == current_user.id,
        TikTokConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="TikTok connection not found")

    synced_count = 0

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TIKTOK_VIDEO_LIST_URL,
                json={
                    "max_count": 20,
                    "fields": "id,title,video_description,duration,cover_image_url,share_url,embed_link,create_time,like_count,comment_count,share_count,view_count"
                },
                headers={
                    "Authorization": f"Bearer {connection.access_token}",
                    "Content-Type": "application/json"
                }
            )

        if response.status_code == 200:
            data = response.json()
            videos = data.get("data", {}).get("videos", [])

            for video_data in videos:
                video_id = video_data.get("id")

                existing_video = db.query(TikTokVideo).filter(
                    TikTokVideo.video_id == video_id
                ).first()

                create_time = None
                if video_data.get("create_time"):
                    create_time = datetime.fromtimestamp(video_data.get("create_time"))

                if existing_video:
                    existing_video.title = video_data.get("title", existing_video.title)
                    existing_video.description = video_data.get("video_description", existing_video.description)
                    existing_video.cover_image_url = video_data.get("cover_image_url", existing_video.cover_image_url)
                    existing_video.share_url = video_data.get("share_url", existing_video.share_url)
                    existing_video.embed_link = video_data.get("embed_link", existing_video.embed_link)
                    existing_video.duration = video_data.get("duration", existing_video.duration)
                    existing_video.view_count = video_data.get("view_count", existing_video.view_count)
                    existing_video.like_count = video_data.get("like_count", existing_video.like_count)
                    existing_video.comment_count = video_data.get("comment_count", existing_video.comment_count)
                    existing_video.share_count = video_data.get("share_count", existing_video.share_count)
                    existing_video.last_stats_updated_at = datetime.utcnow()
                else:
                    new_video = TikTokVideo(
                        connection_id=connection.id,
                        user_id=current_user.id,
                        video_id=video_id,
                        title=video_data.get("title"),
                        description=video_data.get("video_description"),
                        cover_image_url=video_data.get("cover_image_url"),
                        share_url=video_data.get("share_url"),
                        embed_link=video_data.get("embed_link"),
                        duration=video_data.get("duration"),
                        create_time=create_time,
                        view_count=video_data.get("view_count", 0),
                        like_count=video_data.get("like_count", 0),
                        comment_count=video_data.get("comment_count", 0),
                        share_count=video_data.get("share_count", 0),
                        last_stats_updated_at=datetime.utcnow()
                    )
                    db.add(new_video)
                    synced_count += 1

            connection.last_synced_at = datetime.utcnow()
            db.commit()

    except Exception as e:
        print(f"TikTok sync error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync videos: {str(e)}")

    return {"message": "Videos synced successfully", "synced_count": synced_count}


@router.post("/videos/upload")
async def upload_tiktok_video(
    video_url: str = Query(..., description="Video URL to upload"),
    title: str = Query(None, description="Video title"),
    privacy_level: str = Query("SELF_ONLY", description="Privacy: PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, SELF_ONLY"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    TikTok에 동영상 업로드 (URL 방식)
    - TikTok Content Posting API 사용
    """
    connection = db.query(TikTokConnection).filter(
        TikTokConnection.user_id == current_user.id,
        TikTokConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="TikTok connection not found")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TIKTOK_VIDEO_UPLOAD_URL,
                json={
                    "post_info": {
                        "title": title or "",
                        "privacy_level": privacy_level,
                        "disable_duet": False,
                        "disable_comment": False,
                        "disable_stitch": False
                    },
                    "source_info": {
                        "source": "PULL_FROM_URL",
                        "video_url": video_url
                    }
                },
                headers={
                    "Authorization": f"Bearer {connection.access_token}",
                    "Content-Type": "application/json"
                }
            )

        if response.status_code != 200:
            error_data = response.json()
            raise HTTPException(
                status_code=response.status_code,
                detail=error_data.get("error", {}).get("message", "Upload failed")
            )

        result = response.json()
        return {
            "message": "Video upload initiated",
            "publish_id": result.get("data", {}).get("publish_id")
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"TikTok upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload video: {str(e)}")


@router.get("/analytics")
async def get_tiktok_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    TikTok 기본 분석 데이터
    """
    connection = db.query(TikTokConnection).filter(
        TikTokConnection.user_id == current_user.id,
        TikTokConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="TikTok connection not found")

    # DB에서 통계 집계
    video_stats = db.query(
        func.count(TikTokVideo.id).label("video_count"),
        func.sum(TikTokVideo.view_count).label("total_views"),
        func.sum(TikTokVideo.like_count).label("total_likes"),
        func.sum(TikTokVideo.comment_count).label("total_comments"),
        func.sum(TikTokVideo.share_count).label("total_shares")
    ).filter(TikTokVideo.connection_id == connection.id).first()

    return {
        "account": {
            "username": connection.username,
            "follower_count": connection.follower_count,
            "following_count": connection.following_count,
            "likes_count": connection.likes_count,
            "video_count": connection.video_count
        },
        "videos": {
            "synced_count": video_stats.video_count or 0,
            "total_views": video_stats.total_views or 0,
            "total_likes": video_stats.total_likes or 0,
            "total_comments": video_stats.total_comments or 0,
            "total_shares": video_stats.total_shares or 0
        }
    }
