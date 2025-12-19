"""
YouTube API Service
- YouTube Data API v3를 사용한 채널/동영상 관리
- YouTube Analytics API를 사용한 분석 데이터 조회
"""
import os
import re
import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from ..models import YouTubeConnection, YouTubeVideo, YouTubeAnalytics
from ..logger import get_logger

logger = get_logger(__name__)


# YouTube API 기본 URL
YOUTUBE_DATA_API_URL = "https://www.googleapis.com/youtube/v3"
YOUTUBE_ANALYTICS_API_URL = "https://youtubeanalytics.googleapis.com/v2"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


class YouTubeService:
    """YouTube API 서비스 클래스"""

    def __init__(self, access_token: str, refresh_token: Optional[str] = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

    async def _refresh_access_token(self) -> Optional[str]:
        """액세스 토큰 갱신"""
        if not self.refresh_token:
            return None

        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token"
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.headers["Authorization"] = f"Bearer {self.access_token}"
                return self.access_token

            logger.error(f"Token refresh failed: {response.text}")
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
                response = await client.post(url, headers=self.headers, params=params, json=json_data)
            elif method == "PUT":
                response = await client.put(url, headers=self.headers, params=params, json=json_data)
            elif method == "DELETE":
                response = await client.delete(url, headers=self.headers, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")

            if response.status_code == 401 and retry_on_401:
                # 토큰 갱신 시도
                new_token = await self._refresh_access_token()
                if new_token:
                    return await self._make_request(method, url, params, json_data, retry_on_401=False)
                return None

            if response.status_code >= 400:
                logger.error(f"YouTube API error: {response.status_code} - {response.text}")
                return None

            return response.json()

    # ===== 채널 관련 API =====

    async def get_my_channel(self) -> Optional[Dict]:
        """내 채널 정보 조회"""
        url = f"{YOUTUBE_DATA_API_URL}/channels"
        params = {
            "part": "snippet,contentDetails,statistics,brandingSettings",
            "mine": "true"
        }

        result = await self._make_request("GET", url, params)
        if result and result.get("items"):
            return result["items"][0]
        return None

    async def get_channel_by_id(self, channel_id: str) -> Optional[Dict]:
        """채널 ID로 채널 정보 조회"""
        url = f"{YOUTUBE_DATA_API_URL}/channels"
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": channel_id
        }

        result = await self._make_request("GET", url, params)
        if result and result.get("items"):
            return result["items"][0]
        return None

    # ===== 동영상 관련 API =====

    async def get_my_videos(
        self,
        max_results: int = 50,
        page_token: Optional[str] = None
    ) -> Optional[Dict]:
        """내 채널의 동영상 목록 조회"""
        # 먼저 채널의 uploads playlist ID 가져오기
        channel = await self.get_my_channel()
        if not channel:
            return None

        uploads_playlist_id = channel.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
        if not uploads_playlist_id:
            return None

        # 업로드 플레이리스트에서 동영상 가져오기
        url = f"{YOUTUBE_DATA_API_URL}/playlistItems"
        params = {
            "part": "snippet,contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": min(max_results, 50)
        }
        if page_token:
            params["pageToken"] = page_token

        return await self._make_request("GET", url, params)

    async def get_video_details(self, video_ids: List[str]) -> Optional[List[Dict]]:
        """동영상 상세 정보 조회 (최대 50개)"""
        url = f"{YOUTUBE_DATA_API_URL}/videos"
        params = {
            "part": "snippet,contentDetails,statistics,status",
            "id": ",".join(video_ids[:50])
        }

        result = await self._make_request("GET", url, params)
        if result:
            return result.get("items", [])
        return None

    async def get_video_by_id(self, video_id: str) -> Optional[Dict]:
        """단일 동영상 정보 조회"""
        videos = await self.get_video_details([video_id])
        if videos:
            return videos[0]
        return None

    # ===== 동영상 업로드/수정 API =====

    async def upload_video(
        self,
        video_file_path: str,
        title: str,
        description: str = "",
        tags: List[str] = None,
        category_id: str = "22",  # 기본: People & Blogs
        privacy_status: str = "private"  # private, public, unlisted
    ) -> Optional[Dict]:
        """
        동영상 업로드 (Resumable Upload)
        참고: 실제 파일 업로드는 multipart/form-data 사용
        """
        # 메타데이터 준비
        metadata = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        # Resumable Upload 초기화
        init_url = f"{YOUTUBE_DATA_API_URL}/videos"
        params = {
            "uploadType": "resumable",
            "part": "snippet,status"
        }

        async with httpx.AsyncClient() as client:
            # 1. 업로드 세션 시작
            init_response = await client.post(
                init_url,
                headers={
                    **self.headers,
                    "Content-Type": "application/json",
                    "X-Upload-Content-Type": "video/*"
                },
                params=params,
                json=metadata
            )

            if init_response.status_code != 200:
                logger.error(f"Upload init failed: {init_response.text}")
                return None

            upload_url = init_response.headers.get("Location")
            if not upload_url:
                logger.error("No upload URL received")
                return None

            # 2. 실제 파일 업로드
            with open(video_file_path, "rb") as video_file:
                video_data = video_file.read()

            upload_response = await client.put(
                upload_url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "video/*"
                },
                content=video_data,
                timeout=600.0  # 10분 타임아웃
            )

            if upload_response.status_code in [200, 201]:
                return upload_response.json()

            logger.error(f"Upload failed: {upload_response.text}")
            return None

    async def update_video(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category_id: Optional[str] = None,
        privacy_status: Optional[str] = None
    ) -> Optional[Dict]:
        """동영상 정보 수정"""
        # 기존 동영상 정보 가져오기
        video = await self.get_video_by_id(video_id)
        if not video:
            return None

        # 업데이트할 데이터 준비
        update_data = {
            "id": video_id,
            "snippet": {
                "title": title or video["snippet"]["title"],
                "description": description if description is not None else video["snippet"].get("description", ""),
                "tags": tags if tags is not None else video["snippet"].get("tags", []),
                "categoryId": category_id or video["snippet"]["categoryId"]
            }
        }

        parts = ["snippet"]

        if privacy_status:
            update_data["status"] = {"privacyStatus": privacy_status}
            parts.append("status")

        url = f"{YOUTUBE_DATA_API_URL}/videos"
        params = {"part": ",".join(parts)}

        return await self._make_request("PUT", url, params, update_data)

    async def delete_video(self, video_id: str) -> bool:
        """동영상 삭제"""
        url = f"{YOUTUBE_DATA_API_URL}/videos"
        params = {"id": video_id}

        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=self.headers, params=params)
            return response.status_code == 204

    # ===== 분석 API (YouTube Analytics) =====

    async def get_channel_analytics(
        self,
        start_date: str,  # YYYY-MM-DD
        end_date: str,    # YYYY-MM-DD
        metrics: List[str] = None,
        dimensions: List[str] = None
    ) -> Optional[Dict]:
        """채널 전체 분석 데이터 조회"""
        url = f"{YOUTUBE_ANALYTICS_API_URL}/reports"

        default_metrics = [
            "views", "estimatedMinutesWatched", "averageViewDuration",
            "likes", "dislikes", "comments", "shares",
            "subscribersGained", "subscribersLost"
        ]

        params = {
            "ids": "channel==MINE",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": ",".join(metrics or default_metrics)
        }

        if dimensions:
            params["dimensions"] = ",".join(dimensions)

        return await self._make_request("GET", url, params)

    async def get_video_analytics(
        self,
        video_id: str,
        start_date: str,
        end_date: str,
        metrics: List[str] = None
    ) -> Optional[Dict]:
        """특정 동영상 분석 데이터 조회"""
        url = f"{YOUTUBE_ANALYTICS_API_URL}/reports"

        default_metrics = [
            "views", "estimatedMinutesWatched", "averageViewDuration",
            "averageViewPercentage", "likes", "dislikes", "comments", "shares"
        ]

        params = {
            "ids": "channel==MINE",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": ",".join(metrics or default_metrics),
            "filters": f"video=={video_id}"
        }

        return await self._make_request("GET", url, params)

    async def get_traffic_sources(
        self,
        start_date: str,
        end_date: str,
        video_id: Optional[str] = None
    ) -> Optional[Dict]:
        """트래픽 소스 분석"""
        url = f"{YOUTUBE_ANALYTICS_API_URL}/reports"

        params = {
            "ids": "channel==MINE",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views,estimatedMinutesWatched",
            "dimensions": "insightTrafficSourceType"
        }

        if video_id:
            params["filters"] = f"video=={video_id}"

        return await self._make_request("GET", url, params)

    async def get_demographics(
        self,
        start_date: str,
        end_date: str
    ) -> Optional[Dict]:
        """시청자 인구통계 데이터"""
        url = f"{YOUTUBE_ANALYTICS_API_URL}/reports"

        params = {
            "ids": "channel==MINE",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "viewerPercentage",
            "dimensions": "ageGroup,gender"
        }

        return await self._make_request("GET", url, params)

    async def get_top_videos(
        self,
        start_date: str,
        end_date: str,
        max_results: int = 10
    ) -> Optional[Dict]:
        """인기 동영상 순위"""
        url = f"{YOUTUBE_ANALYTICS_API_URL}/reports"

        params = {
            "ids": "channel==MINE",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": "views,estimatedMinutesWatched,averageViewDuration,likes,comments",
            "dimensions": "video",
            "sort": "-views",
            "maxResults": max_results
        }

        return await self._make_request("GET", url, params)


# ===== 헬퍼 함수들 =====

def parse_duration(duration: str) -> int:
    """ISO 8601 duration을 초 단위로 변환 (PT4M13S -> 253)"""
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration)

    if not match:
        return 0

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds


async def sync_youtube_videos(
    db: Session,
    connection: YouTubeConnection,
    service: YouTubeService
) -> int:
    """YouTube 동영상 목록 동기화"""
    synced_count = 0
    page_token = None

    while True:
        result = await service.get_my_videos(max_results=50, page_token=page_token)
        if not result or not result.get("items"):
            break

        video_ids = [
            item["contentDetails"]["videoId"]
            for item in result["items"]
        ]

        # 상세 정보 가져오기
        video_details = await service.get_video_details(video_ids)
        if not video_details:
            break

        for video in video_details:
            video_id = video["id"]
            snippet = video["snippet"]
            statistics = video.get("statistics", {})
            content_details = video.get("contentDetails", {})
            status = video.get("status", {})

            # 기존 데이터 확인
            existing = db.query(YouTubeVideo).filter(
                YouTubeVideo.video_id == video_id
            ).first()

            duration = content_details.get("duration", "")

            if existing:
                # 업데이트
                existing.title = snippet["title"]
                existing.description = snippet.get("description", "")
                existing.thumbnail_url = snippet.get("thumbnails", {}).get("high", {}).get("url")
                existing.view_count = int(statistics.get("viewCount", 0))
                existing.like_count = int(statistics.get("likeCount", 0))
                existing.comment_count = int(statistics.get("commentCount", 0))
                existing.privacy_status = status.get("privacyStatus")
                existing.tags = snippet.get("tags", [])
                existing.last_stats_updated_at = datetime.utcnow()
            else:
                # 새로 추가
                new_video = YouTubeVideo(
                    connection_id=connection.id,
                    user_id=connection.user_id,
                    video_id=video_id,
                    title=snippet["title"],
                    description=snippet.get("description", ""),
                    thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url"),
                    published_at=datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")),
                    duration=duration,
                    duration_seconds=parse_duration(duration),
                    privacy_status=status.get("privacyStatus"),
                    upload_status=status.get("uploadStatus"),
                    view_count=int(statistics.get("viewCount", 0)),
                    like_count=int(statistics.get("likeCount", 0)),
                    comment_count=int(statistics.get("commentCount", 0)),
                    tags=snippet.get("tags", []),
                    category_id=snippet.get("categoryId"),
                    last_stats_updated_at=datetime.utcnow()
                )
                db.add(new_video)
                synced_count += 1

        db.commit()

        # 다음 페이지
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    # 연동 정보 업데이트
    connection.last_synced_at = datetime.utcnow()
    db.commit()

    return synced_count
