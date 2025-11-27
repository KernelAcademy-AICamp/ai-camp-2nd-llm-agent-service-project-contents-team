"""
Instagram Graph API Service
- Instagram 비즈니스/크리에이터 계정 관리
- 게시물 조회/생성
- 인사이트 조회
"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..logger import get_logger

logger = get_logger(__name__)

GRAPH_API_VERSION = "v18.0"
GRAPH_API_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class InstagramService:
    """Instagram Graph API 서비스 클래스"""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """HTTP 클라이언트 종료"""
        await self.client.aclose()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None
    ) -> Optional[Dict]:
        """Instagram Graph API 요청"""
        url = f"{GRAPH_API_BASE_URL}/{endpoint}"

        if params is None:
            params = {}
        params['access_token'] = self.access_token

        try:
            if method.upper() == 'GET':
                response = await self.client.get(url, params=params)
            elif method.upper() == 'POST':
                response = await self.client.post(url, params=params, data=data)
            elif method.upper() == 'DELETE':
                response = await self.client.delete(url, params=params)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Instagram API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Instagram API request failed: {e}")
            return None

    # ===== Instagram 비즈니스 계정 조회 =====

    async def get_instagram_accounts_from_pages(self, pages: List[Dict]) -> List[Dict]:
        """
        Facebook 페이지들에 연결된 Instagram 비즈니스 계정 조회
        """
        instagram_accounts = []

        for page in pages:
            page_id = page.get('id')
            page_access_token = page.get('access_token')

            if not page_id or not page_access_token:
                continue

            # 페이지에 연결된 Instagram 계정 조회
            result = await self._make_request(
                'GET',
                f'{page_id}',
                params={
                    'fields': 'instagram_business_account{id,username,name,profile_picture_url,biography,website,followers_count,follows_count,media_count}',
                    'access_token': page_access_token
                }
            )

            if result and 'instagram_business_account' in result:
                ig_account = result['instagram_business_account']
                ig_account['facebook_page_id'] = page_id
                ig_account['facebook_page_name'] = page.get('name')
                ig_account['page_access_token'] = page_access_token
                instagram_accounts.append(ig_account)
                logger.info(f"Found Instagram account: {ig_account.get('username')} for page {page.get('name')}")

        return instagram_accounts

    async def get_account_info(self, instagram_user_id: str) -> Optional[Dict]:
        """Instagram 비즈니스 계정 정보 조회"""
        return await self._make_request(
            'GET',
            instagram_user_id,
            params={
                'fields': 'id,username,name,profile_picture_url,biography,website,followers_count,follows_count,media_count'
            }
        )

    # ===== 미디어(게시물) 관리 =====

    async def get_media_list(
        self,
        instagram_user_id: str,
        limit: int = 25
    ) -> Optional[List[Dict]]:
        """Instagram 게시물 목록 조회"""
        result = await self._make_request(
            'GET',
            f'{instagram_user_id}/media',
            params={
                'fields': 'id,media_type,media_url,thumbnail_url,permalink,caption,timestamp,like_count,comments_count',
                'limit': limit
            }
        )
        if result and 'data' in result:
            return result['data']
        return None

    async def get_media_details(self, media_id: str) -> Optional[Dict]:
        """게시물 상세 정보 조회"""
        return await self._make_request(
            'GET',
            media_id,
            params={
                'fields': 'id,media_type,media_url,thumbnail_url,permalink,caption,timestamp,like_count,comments_count,children{id,media_type,media_url}'
            }
        )

    async def get_media_insights(self, media_id: str) -> Optional[Dict]:
        """게시물 인사이트 조회 (비즈니스 계정만)"""
        # 이미지/캐러셀용 메트릭
        result = await self._make_request(
            'GET',
            f'{media_id}/insights',
            params={
                'metric': 'engagement,impressions,reach,saved'
            }
        )
        return result

    # ===== 계정 인사이트 =====

    async def get_account_insights(
        self,
        instagram_user_id: str,
        period: str = 'day',
        metrics: List[str] = None
    ) -> Optional[Dict]:
        """계정 인사이트 조회"""
        if metrics is None:
            metrics = [
                'impressions',
                'reach',
                'profile_views',
                'follower_count'
            ]

        return await self._make_request(
            'GET',
            f'{instagram_user_id}/insights',
            params={
                'metric': ','.join(metrics),
                'period': period
            }
        )

    async def get_account_insights_by_time(
        self,
        instagram_user_id: str,
        since: int,
        until: int
    ) -> Optional[Dict]:
        """기간별 계정 인사이트 조회"""
        return await self._make_request(
            'GET',
            f'{instagram_user_id}/insights',
            params={
                'metric': 'impressions,reach,profile_views',
                'period': 'day',
                'since': since,
                'until': until
            }
        )

    # ===== 미디어 게시 =====

    async def create_media_container(
        self,
        instagram_user_id: str,
        image_url: str = None,
        video_url: str = None,
        caption: str = None,
        is_carousel_item: bool = False
    ) -> Optional[Dict]:
        """미디어 컨테이너 생성 (게시 1단계)"""
        params = {}

        if image_url:
            params['image_url'] = image_url
        elif video_url:
            params['video_url'] = video_url
            params['media_type'] = 'VIDEO'

        if caption:
            params['caption'] = caption

        if is_carousel_item:
            params['is_carousel_item'] = 'true'

        return await self._make_request(
            'POST',
            f'{instagram_user_id}/media',
            params=params
        )

    async def publish_media(
        self,
        instagram_user_id: str,
        creation_id: str
    ) -> Optional[Dict]:
        """미디어 게시 (게시 2단계)"""
        return await self._make_request(
            'POST',
            f'{instagram_user_id}/media_publish',
            params={'creation_id': creation_id}
        )

    async def create_carousel_container(
        self,
        instagram_user_id: str,
        children_ids: List[str],
        caption: str = None
    ) -> Optional[Dict]:
        """캐러셀 컨테이너 생성"""
        params = {
            'media_type': 'CAROUSEL',
            'children': ','.join(children_ids)
        }

        if caption:
            params['caption'] = caption

        return await self._make_request(
            'POST',
            f'{instagram_user_id}/media',
            params=params
        )


async def sync_instagram_posts(
    service: InstagramService,
    instagram_user_id: str,
    connection_id: int,
    user_id: int,
    db
) -> int:
    """Instagram 게시물 동기화"""
    from .. import models

    posts = await service.get_media_list(instagram_user_id, limit=50)
    if not posts:
        return 0

    synced_count = 0

    for post_data in posts:
        media_id = post_data.get('id')

        # 기존 게시물 확인
        existing = db.query(models.InstagramPost).filter(
            models.InstagramPost.media_id == media_id
        ).first()

        # 게시 시간 파싱
        timestamp = None
        if post_data.get('timestamp'):
            try:
                timestamp = datetime.fromisoformat(
                    post_data['timestamp'].replace('Z', '+00:00')
                )
            except Exception:
                pass

        if existing:
            # 업데이트
            existing.media_type = post_data.get('media_type')
            existing.media_url = post_data.get('media_url')
            existing.thumbnail_url = post_data.get('thumbnail_url')
            existing.permalink = post_data.get('permalink')
            existing.caption = post_data.get('caption')
            existing.like_count = post_data.get('like_count', 0)
            existing.comments_count = post_data.get('comments_count', 0)
            existing.last_stats_updated_at = datetime.utcnow()
        else:
            # 새로 생성
            new_post = models.InstagramPost(
                connection_id=connection_id,
                user_id=user_id,
                media_id=media_id,
                media_type=post_data.get('media_type'),
                media_url=post_data.get('media_url'),
                thumbnail_url=post_data.get('thumbnail_url'),
                permalink=post_data.get('permalink'),
                caption=post_data.get('caption'),
                timestamp=timestamp,
                like_count=post_data.get('like_count', 0),
                comments_count=post_data.get('comments_count', 0),
                last_stats_updated_at=datetime.utcnow()
            )
            db.add(new_post)
            synced_count += 1

    db.commit()
    return synced_count
