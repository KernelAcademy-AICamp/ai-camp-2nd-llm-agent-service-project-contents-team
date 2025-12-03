"""
Twitter(X) API Service
- Twitter API v2를 사용한 트윗 관리 및 계정 정보 조회
- OAuth 2.0 with PKCE 인증 방식
"""
import os
import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from ..models import TwitterConnection, Tweet
from ..logger import get_logger

logger = get_logger(__name__)


# Twitter API v2 기본 URL
TWITTER_API_URL = "https://api.twitter.com/2"
TWITTER_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"


class TwitterService:
    """Twitter API v2 서비스 클래스"""

    def __init__(self, access_token: str, refresh_token: Optional[str] = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    async def _refresh_access_token(self) -> Optional[str]:
        """액세스 토큰 갱신 (OAuth 2.0)"""
        if not self.refresh_token:
            return None

        client_id = os.getenv("TWITTER_CLIENT_ID")
        client_secret = os.getenv("TWITTER_CLIENT_SECRET")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                TWITTER_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                    "client_id": client_id,
                },
                auth=(client_id, client_secret) if client_secret else None,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data.get("refresh_token", self.refresh_token)
                self.headers["Authorization"] = f"Bearer {self.access_token}"
                logger.info("Twitter access token refreshed successfully")
                return self.access_token

            logger.error(f"Twitter token refresh failed: {response.text}")
            return None

    async def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        retry_on_401: bool = True
    ) -> Optional[Dict]:
        """API 요청 수행 (토큰 갱신 자동 처리)"""
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=self.headers, params=params)
            elif method == "POST":
                response = await client.post(url, headers=self.headers, json=json_data)
            elif method == "DELETE":
                response = await client.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            if response.status_code == 401 and retry_on_401:
                # 토큰 갱신 시도
                new_token = await self._refresh_access_token()
                if new_token:
                    return await self._make_request(method, url, params, json_data, retry_on_401=False)
                return None

            if response.status_code >= 400:
                logger.error(f"Twitter API error: {response.status_code} - {response.text}")
                return None

            # DELETE 요청은 빈 응답일 수 있음
            if response.status_code == 204:
                return {"success": True}

            return response.json()

    # ===== 사용자 정보 API =====

    async def get_me(self) -> Optional[Dict]:
        """현재 인증된 사용자 정보 조회"""
        url = f"{TWITTER_API_URL}/users/me"
        params = {
            "user.fields": "id,name,username,description,profile_image_url,verified,public_metrics,created_at"
        }

        result = await self._make_request("GET", url, params=params)
        if result and "data" in result:
            return result["data"]
        return None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """사용자 ID로 정보 조회"""
        url = f"{TWITTER_API_URL}/users/{user_id}"
        params = {
            "user.fields": "id,name,username,description,profile_image_url,verified,public_metrics,created_at"
        }

        result = await self._make_request("GET", url, params=params)
        if result and "data" in result:
            return result["data"]
        return None

    # ===== 트윗 조회 API =====

    async def get_user_tweets(
        self,
        user_id: str,
        max_results: int = 50,
        pagination_token: Optional[str] = None
    ) -> Optional[Dict]:
        """사용자의 트윗 목록 조회"""
        url = f"{TWITTER_API_URL}/users/{user_id}/tweets"
        params = {
            "max_results": min(max_results, 100),  # 최대 100개
            "tweet.fields": "id,text,created_at,public_metrics,attachments,conversation_id,in_reply_to_user_id,referenced_tweets",
            "expansions": "attachments.media_keys",
            "media.fields": "type,url,preview_image_url"
        }

        if pagination_token:
            params["pagination_token"] = pagination_token

        return await self._make_request("GET", url, params=params)

    async def get_tweet_by_id(self, tweet_id: str) -> Optional[Dict]:
        """트윗 ID로 상세 정보 조회"""
        url = f"{TWITTER_API_URL}/tweets/{tweet_id}"
        params = {
            "tweet.fields": "id,text,created_at,public_metrics,attachments,conversation_id,in_reply_to_user_id,referenced_tweets",
            "expansions": "attachments.media_keys",
            "media.fields": "type,url,preview_image_url"
        }

        result = await self._make_request("GET", url, params=params)
        if result and "data" in result:
            return result
        return None

    # ===== 트윗 작성 API =====

    async def create_tweet(self, text: str, reply_to: Optional[str] = None) -> Optional[Dict]:
        """새 트윗 작성"""
        url = f"{TWITTER_API_URL}/tweets"
        data = {"text": text}

        if reply_to:
            data["reply"] = {"in_reply_to_tweet_id": reply_to}

        result = await self._make_request("POST", url, json_data=data)
        if result and "data" in result:
            return result["data"]
        return None

    async def delete_tweet(self, tweet_id: str) -> bool:
        """트윗 삭제"""
        url = f"{TWITTER_API_URL}/tweets/{tweet_id}"
        result = await self._make_request("DELETE", url)
        return result is not None and result.get("data", {}).get("deleted", False)

    # ===== 미디어 업로드 API (v1.1 사용 필요) =====
    # 참고: 미디어 업로드는 Twitter API v1.1을 사용해야 함

    async def upload_media(self, media_data: bytes, media_type: str) -> Optional[str]:
        """미디어 업로드 (v1.1 API 사용)

        참고: Twitter API v2는 미디어 업로드를 지원하지 않음
        v1.1의 media/upload 엔드포인트를 사용해야 함
        """
        # Twitter API v1.1 미디어 업로드 엔드포인트
        url = "https://upload.twitter.com/1.1/media/upload.json"

        # OAuth 1.0a 인증이 필요하므로 별도 구현 필요
        # 현재는 텍스트 트윗만 지원
        logger.warning("Media upload requires OAuth 1.0a authentication (not implemented)")
        return None


# ===== 데이터베이스 헬퍼 함수 =====

async def sync_twitter_user_info(
    db: Session,
    connection: TwitterConnection,
    service: TwitterService
) -> bool:
    """Twitter 사용자 정보 동기화"""
    user_info = await service.get_me()
    if not user_info:
        return False

    # 연결 정보 업데이트
    connection.twitter_user_id = user_info["id"]
    connection.username = user_info.get("username")
    connection.name = user_info.get("name")
    connection.description = user_info.get("description")
    connection.profile_image_url = user_info.get("profile_image_url")
    connection.verified = user_info.get("verified", False)

    # 통계 업데이트
    public_metrics = user_info.get("public_metrics", {})
    connection.followers_count = public_metrics.get("followers_count", 0)
    connection.following_count = public_metrics.get("following_count", 0)
    connection.tweet_count = public_metrics.get("tweet_count", 0)
    connection.listed_count = public_metrics.get("listed_count", 0)

    connection.last_synced_at = datetime.utcnow()
    db.commit()

    logger.info(f"Twitter user info synced: @{connection.username}")
    return True


async def sync_twitter_tweets(
    db: Session,
    connection: TwitterConnection,
    service: TwitterService,
    max_tweets: int = 50
) -> int:
    """Twitter 트윗 동기화"""
    synced_count = 0

    result = await service.get_user_tweets(connection.twitter_user_id, max_results=max_tweets)
    if not result or "data" not in result:
        return 0

    tweets_data = result["data"]
    media_dict = {}

    # 미디어 정보 매핑
    if "includes" in result and "media" in result["includes"]:
        for media in result["includes"]["media"]:
            media_dict[media["media_key"]] = media

    for tweet_data in tweets_data:
        tweet_id = tweet_data["id"]

        # 기존 트윗 확인
        existing_tweet = db.query(Tweet).filter(Tweet.tweet_id == tweet_id).first()

        # 미디어 정보 추출
        media_url = None
        media_urls = []
        media_type = None

        if "attachments" in tweet_data and "media_keys" in tweet_data["attachments"]:
            for media_key in tweet_data["attachments"]["media_keys"]:
                if media_key in media_dict:
                    media = media_dict[media_key]
                    media_type = media.get("type")
                    url = media.get("url") or media.get("preview_image_url")
                    if url:
                        media_urls.append(url)
                        if not media_url:
                            media_url = url

        # 통계 정보
        public_metrics = tweet_data.get("public_metrics", {})

        if existing_tweet:
            # 기존 트윗 업데이트
            existing_tweet.text = tweet_data.get("text")
            existing_tweet.retweet_count = public_metrics.get("retweet_count", 0)
            existing_tweet.reply_count = public_metrics.get("reply_count", 0)
            existing_tweet.like_count = public_metrics.get("like_count", 0)
            existing_tweet.quote_count = public_metrics.get("quote_count", 0)
            existing_tweet.bookmark_count = public_metrics.get("bookmark_count", 0)
            existing_tweet.impression_count = public_metrics.get("impression_count", 0)
            existing_tweet.media_type = media_type
            existing_tweet.media_url = media_url
            existing_tweet.media_urls = media_urls if media_urls else None
            existing_tweet.last_stats_updated_at = datetime.utcnow()
        else:
            # 새 트윗 생성
            new_tweet = Tweet(
                connection_id=connection.id,
                user_id=connection.user_id,
                tweet_id=tweet_id,
                text=tweet_data.get("text"),
                created_at_twitter=datetime.fromisoformat(
                    tweet_data["created_at"].replace("Z", "+00:00")
                ) if "created_at" in tweet_data else None,
                media_type=media_type,
                media_url=media_url,
                media_urls=media_urls if media_urls else None,
                retweet_count=public_metrics.get("retweet_count", 0),
                reply_count=public_metrics.get("reply_count", 0),
                like_count=public_metrics.get("like_count", 0),
                quote_count=public_metrics.get("quote_count", 0),
                bookmark_count=public_metrics.get("bookmark_count", 0),
                impression_count=public_metrics.get("impression_count", 0),
                conversation_id=tweet_data.get("conversation_id"),
                in_reply_to_user_id=tweet_data.get("in_reply_to_user_id"),
                referenced_tweets=tweet_data.get("referenced_tweets"),
                last_stats_updated_at=datetime.utcnow()
            )
            db.add(new_tweet)
            synced_count += 1

    db.commit()
    logger.info(f"Synced {synced_count} new tweets for @{connection.username}")
    return synced_count
