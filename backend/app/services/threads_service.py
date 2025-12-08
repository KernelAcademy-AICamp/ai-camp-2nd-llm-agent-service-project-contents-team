"""
Threads API Service
- Meta의 Threads API를 사용한 포스트 관리 및 계정 정보 조회
- OAuth 2.0 인증 방식
"""
import os
import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from ..models import ThreadsConnection, ThreadsPost
from ..logger import get_logger

logger = get_logger(__name__)


# Threads API 기본 URL
THREADS_API_URL = "https://graph.threads.net/v1.0"
THREADS_AUTH_URL = "https://threads.net/oauth/authorize"
THREADS_TOKEN_URL = "https://graph.threads.net/oauth/access_token"


class ThreadsService:
    """Threads API 서비스 클래스"""

    def __init__(self, access_token: str, user_id: Optional[str] = None):
        self.access_token = access_token
        self.user_id = user_id

    async def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """API 요청 수행"""
        if params is None:
            params = {}
        params["access_token"] = self.access_token

        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(url, params=params)
                elif method == "POST":
                    if json_data:
                        response = await client.post(url, params=params, json=json_data)
                    else:
                        response = await client.post(url, params=params, data=data)
                elif method == "DELETE":
                    response = await client.delete(url, params=params)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                if response.status_code >= 400:
                    logger.error(f"Threads API error: {response.status_code} - {response.text}")
                    return None

                return response.json()
            except Exception as e:
                logger.error(f"Threads API request failed: {str(e)}")
                return None

    # ===== 사용자 정보 API =====

    async def get_me(self) -> Optional[Dict]:
        """현재 인증된 사용자 정보 조회"""
        url = f"{THREADS_API_URL}/me"
        params = {
            "fields": "id,username,name,threads_profile_picture_url,threads_biography"
        }

        return await self._make_request("GET", url, params=params)

    async def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """사용자 프로필 정보 조회"""
        url = f"{THREADS_API_URL}/{user_id}"
        params = {
            "fields": "id,username,name,threads_profile_picture_url,threads_biography"
        }

        return await self._make_request("GET", url, params=params)

    # ===== 포스트 조회 API =====

    async def get_user_threads(
        self,
        user_id: str,
        limit: int = 25,
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> Optional[Dict]:
        """사용자의 Threads 포스트 목록 조회"""
        url = f"{THREADS_API_URL}/{user_id}/threads"
        params = {
            "fields": "id,media_type,media_url,permalink,text,timestamp,thumbnail_url,is_quote_post",
            "limit": min(limit, 100)
        }

        if since:
            params["since"] = since
        if until:
            params["until"] = until

        return await self._make_request("GET", url, params=params)

    async def get_thread_by_id(self, thread_id: str) -> Optional[Dict]:
        """Threads 포스트 상세 정보 조회"""
        url = f"{THREADS_API_URL}/{thread_id}"
        params = {
            "fields": "id,media_type,media_url,permalink,text,timestamp,thumbnail_url,is_quote_post,owner"
        }

        return await self._make_request("GET", url, params=params)

    async def get_thread_insights(self, thread_id: str) -> Optional[Dict]:
        """Threads 포스트 인사이트 조회"""
        url = f"{THREADS_API_URL}/{thread_id}/insights"
        params = {
            "metric": "views,likes,replies,reposts,quotes"
        }

        return await self._make_request("GET", url, params=params)

    # ===== 포스트 작성 API =====

    async def create_thread_container(
        self,
        user_id: str,
        text: Optional[str] = None,
        image_url: Optional[str] = None,
        video_url: Optional[str] = None,
        media_type: str = "TEXT"
    ) -> Optional[Dict]:
        """Threads 미디어 컨테이너 생성

        Args:
            user_id: Threads 사용자 ID
            text: 포스트 텍스트
            image_url: 이미지 URL (IMAGE 타입용)
            video_url: 비디오 URL (VIDEO 타입용)
            media_type: TEXT, IMAGE, VIDEO
        """
        url = f"{THREADS_API_URL}/{user_id}/threads"
        params = {
            "media_type": media_type
        }

        if text:
            params["text"] = text
        if image_url and media_type == "IMAGE":
            params["image_url"] = image_url
        if video_url and media_type == "VIDEO":
            params["video_url"] = video_url

        return await self._make_request("POST", url, params=params)

    async def publish_thread(self, user_id: str, creation_id: str) -> Optional[Dict]:
        """Threads 포스트 발행

        Args:
            user_id: Threads 사용자 ID
            creation_id: create_thread_container에서 반환된 ID
        """
        url = f"{THREADS_API_URL}/{user_id}/threads_publish"
        params = {
            "creation_id": creation_id
        }

        return await self._make_request("POST", url, params=params)

    async def create_and_publish_thread(
        self,
        user_id: str,
        text: Optional[str] = None,
        image_url: Optional[str] = None,
        video_url: Optional[str] = None
    ) -> Optional[Dict]:
        """Threads 포스트 생성 및 발행 (통합 함수)"""
        # 미디어 타입 결정
        if video_url:
            media_type = "VIDEO"
        elif image_url:
            media_type = "IMAGE"
        else:
            media_type = "TEXT"

        # 1. 컨테이너 생성
        container = await self.create_thread_container(
            user_id=user_id,
            text=text,
            image_url=image_url,
            video_url=video_url,
            media_type=media_type
        )

        if not container or "id" not in container:
            logger.error("Failed to create thread container")
            return None

        creation_id = container["id"]

        # 2. 발행
        result = await self.publish_thread(user_id, creation_id)
        if result:
            logger.info(f"Thread published successfully: {result.get('id')}")
        return result

    # ===== 토큰 관리 =====

    @staticmethod
    async def exchange_code_for_token(code: str, redirect_uri: str) -> Optional[Dict]:
        """인증 코드를 액세스 토큰으로 교환"""
        client_id = os.getenv("THREADS_APP_ID")
        client_secret = os.getenv("THREADS_APP_SECRET")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                THREADS_TOKEN_URL,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                    "code": code
                }
            )

            if response.status_code == 200:
                return response.json()

            logger.error(f"Threads token exchange failed: {response.text}")
            return None

    @staticmethod
    async def get_long_lived_token(short_lived_token: str) -> Optional[Dict]:
        """단기 토큰을 장기 토큰으로 교환 (60일)"""
        client_secret = os.getenv("THREADS_APP_SECRET")

        url = f"{THREADS_API_URL}/access_token"
        params = {
            "grant_type": "th_exchange_token",
            "client_secret": client_secret,
            "access_token": short_lived_token
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)

            if response.status_code == 200:
                return response.json()

            logger.error(f"Threads long-lived token exchange failed: {response.text}")
            return None

    @staticmethod
    async def refresh_long_lived_token(long_lived_token: str) -> Optional[Dict]:
        """장기 토큰 갱신 (만료 전 갱신 필요)"""
        url = f"{THREADS_API_URL}/refresh_access_token"
        params = {
            "grant_type": "th_refresh_token",
            "access_token": long_lived_token
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)

            if response.status_code == 200:
                return response.json()

            logger.error(f"Threads token refresh failed: {response.text}")
            return None


# ===== 데이터베이스 헬퍼 함수 =====

async def sync_threads_user_info(
    db: Session,
    connection: ThreadsConnection,
    service: ThreadsService
) -> bool:
    """Threads 사용자 정보 동기화"""
    user_info = await service.get_me()
    if not user_info:
        return False

    # 연결 정보 업데이트
    connection.threads_user_id = user_info.get("id")
    connection.username = user_info.get("username")
    connection.name = user_info.get("name")
    connection.threads_profile_picture_url = user_info.get("threads_profile_picture_url")
    connection.threads_biography = user_info.get("threads_biography")

    connection.last_synced_at = datetime.utcnow()
    db.commit()

    logger.info(f"Threads user info synced: @{connection.username}")
    return True


async def sync_threads_posts(
    db: Session,
    connection: ThreadsConnection,
    service: ThreadsService,
    max_posts: int = 25
) -> int:
    """Threads 포스트 동기화"""
    synced_count = 0

    result = await service.get_user_threads(connection.threads_user_id, limit=max_posts)
    if not result or "data" not in result:
        return 0

    posts_data = result["data"]

    for post_data in posts_data:
        post_id = post_data["id"]

        # 기존 포스트 확인
        existing_post = db.query(ThreadsPost).filter(ThreadsPost.threads_post_id == post_id).first()

        # 인사이트 조회 (통계)
        insights = await service.get_thread_insights(post_id)
        stats = {}
        if insights and "data" in insights:
            for metric in insights["data"]:
                stats[metric["name"]] = metric["values"][0]["value"] if metric["values"] else 0

        if existing_post:
            # 기존 포스트 업데이트
            existing_post.text = post_data.get("text")
            existing_post.media_type = post_data.get("media_type")
            existing_post.media_url = post_data.get("media_url")
            existing_post.thumbnail_url = post_data.get("thumbnail_url")
            existing_post.permalink = post_data.get("permalink")
            existing_post.is_quote_post = post_data.get("is_quote_post", False)
            existing_post.views_count = stats.get("views", 0)
            existing_post.like_count = stats.get("likes", 0)
            existing_post.reply_count = stats.get("replies", 0)
            existing_post.repost_count = stats.get("reposts", 0)
            existing_post.quote_count = stats.get("quotes", 0)
            existing_post.last_stats_updated_at = datetime.utcnow()
        else:
            # 새 포스트 생성
            new_post = ThreadsPost(
                connection_id=connection.id,
                user_id=connection.user_id,
                threads_post_id=post_id,
                text=post_data.get("text"),
                media_type=post_data.get("media_type"),
                media_url=post_data.get("media_url"),
                thumbnail_url=post_data.get("thumbnail_url"),
                permalink=post_data.get("permalink"),
                timestamp=datetime.fromisoformat(
                    post_data["timestamp"].replace("Z", "+00:00")
                ) if "timestamp" in post_data else None,
                is_quote_post=post_data.get("is_quote_post", False),
                views_count=stats.get("views", 0),
                like_count=stats.get("likes", 0),
                reply_count=stats.get("replies", 0),
                repost_count=stats.get("reposts", 0),
                quote_count=stats.get("quotes", 0),
                last_stats_updated_at=datetime.utcnow()
            )
            db.add(new_post)
            synced_count += 1

    db.commit()
    logger.info(f"Synced {synced_count} new threads for @{connection.username}")
    return synced_count
