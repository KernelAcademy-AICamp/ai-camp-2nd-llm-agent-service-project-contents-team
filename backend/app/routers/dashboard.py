"""
Dashboard API - 통합 플랫폼 상태 조회
모든 플랫폼의 연동 상태를 한 번에 조회하여 프론트엔드 로딩 시간 단축
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ..database import get_db
from ..models import (
    User, YouTubeConnection, FacebookConnection, InstagramConnection,
    XConnection, ThreadsConnection, TikTokConnection, WordPressConnection
)
from .. import auth

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/status")
async def get_all_platform_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth.get_current_active_user)
):
    """
    모든 SNS 플랫폼의 연동 상태를 한 번에 조회
    기존: 7번의 API 호출 → 개선: 1번의 API 호출
    """
    user_id = current_user.id

    # 모든 연결 정보를 병렬로 조회 (SQLAlchemy는 자동으로 최적화)
    youtube = db.query(YouTubeConnection).filter(
        YouTubeConnection.user_id == user_id
    ).first()

    facebook = db.query(FacebookConnection).filter(
        FacebookConnection.user_id == user_id
    ).first()

    instagram = db.query(InstagramConnection).filter(
        InstagramConnection.user_id == user_id
    ).first()

    x_conn = db.query(XConnection).filter(
        XConnection.user_id == user_id
    ).first()

    threads = db.query(ThreadsConnection).filter(
        ThreadsConnection.user_id == user_id
    ).first()

    tiktok = db.query(TikTokConnection).filter(
        TikTokConnection.user_id == user_id
    ).first()

    wordpress = db.query(WordPressConnection).filter(
        WordPressConnection.user_id == user_id
    ).first()

    return {
        "youtube": _format_youtube(youtube) if youtube else None,
        "facebook": _format_facebook(facebook) if facebook else None,
        "instagram": _format_instagram(instagram) if instagram else None,
        "x": _format_x(x_conn) if x_conn else None,
        "threads": _format_threads(threads) if threads else None,
        "tiktok": _format_tiktok(tiktok) if tiktok else None,
        "wordpress": _format_wordpress(wordpress) if wordpress else None,
    }


def _format_youtube(conn: YouTubeConnection) -> dict:
    """YouTube 연결 정보 포맷"""
    return {
        "channel_id": conn.channel_id,
        "channel_title": conn.channel_title,
        "subscriber_count": conn.subscriber_count or 0,
        "view_count": conn.view_count or 0,
        "video_count": conn.video_count or 0,
        "profile_picture_url": conn.channel_thumbnail_url,
        "connected_at": conn.created_at.isoformat() if conn.created_at else None,
    }


def _format_facebook(conn: FacebookConnection) -> dict:
    """Facebook 연결 정보 포맷"""
    return {
        "page_id": conn.page_id,
        "page_name": conn.page_name,
        "page_category": conn.page_category,
        "page_followers_count": conn.page_followers_count or 0,
        "page_likes_count": conn.page_fan_count or 0,
        "page_picture_url": conn.page_picture_url,
        "connected_at": conn.created_at.isoformat() if conn.created_at else None,
    }


def _format_instagram(conn: InstagramConnection) -> dict:
    """Instagram 연결 정보 포맷"""
    return {
        "instagram_account_id": conn.instagram_account_id,
        "instagram_username": conn.instagram_username,
        "followers_count": conn.followers_count or 0,
        "follows_count": conn.follows_count or 0,
        "media_count": conn.media_count or 0,
        "profile_picture_url": conn.instagram_profile_picture_url,
        "connected_at": conn.created_at.isoformat() if conn.created_at else None,
    }


def _format_x(conn: XConnection) -> dict:
    """X(Twitter) 연결 정보 포맷"""
    return {
        "x_user_id": conn.x_user_id,
        "x_username": conn.username,
        "x_name": conn.name,
        "followers_count": conn.followers_count or 0,
        "following_count": conn.following_count or 0,
        "tweet_count": conn.post_count or 0,
        "profile_image_url": conn.profile_image_url,
        "connected_at": conn.created_at.isoformat() if conn.created_at else None,
    }


def _format_threads(conn: ThreadsConnection) -> dict:
    """Threads 연결 정보 포맷"""
    return {
        "threads_user_id": conn.threads_user_id,
        "username": conn.username,
        "name": conn.name,
        "followers_count": conn.followers_count or 0,
        "profile_picture_url": conn.threads_profile_picture_url,
        "connected_at": conn.created_at.isoformat() if conn.created_at else None,
    }


def _format_tiktok(conn: TikTokConnection) -> dict:
    """TikTok 연결 정보 포맷"""
    return {
        "tiktok_user_id": conn.tiktok_user_id,
        "tiktok_username": conn.username,
        "display_name": conn.username,
        "follower_count": conn.follower_count or 0,
        "following_count": conn.following_count or 0,
        "likes_count": conn.likes_count or 0,
        "video_count": conn.video_count or 0,
        "profile_picture_url": conn.avatar_url,
        "connected_at": conn.created_at.isoformat() if conn.created_at else None,
    }


def _format_wordpress(conn: WordPressConnection) -> dict:
    """WordPress 연결 정보 포맷"""
    return {
        "site_url": conn.site_url,
        "site_name": conn.site_name,
        "username": conn.wp_username,
        "total_posts": conn.post_count or 0,
        "total_pages": conn.page_count or 0,
        "total_media": 0,
        "connected_at": conn.created_at.isoformat() if conn.created_at else None,
    }
