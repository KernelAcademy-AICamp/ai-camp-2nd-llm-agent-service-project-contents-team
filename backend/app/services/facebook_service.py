"""
Facebook Graph API Service
- Facebook 페이지 관리
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


class FacebookService:
    """Facebook Graph API 서비스 클래스"""

    def __init__(self, access_token: str, page_access_token: str = None):
        self.access_token = access_token
        self.page_access_token = page_access_token or access_token
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """HTTP 클라이언트 종료"""
        await self.client.aclose()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None,
        use_page_token: bool = False
    ) -> Optional[Dict]:
        """Facebook Graph API 요청"""
        url = f"{GRAPH_API_BASE_URL}/{endpoint}"
        token = self.page_access_token if use_page_token else self.access_token

        if params is None:
            params = {}
        params['access_token'] = token

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
                error_data = response.json() if response.text else {}
                error_message = error_data.get('error', {}).get('message', response.text)
                error_code = error_data.get('error', {}).get('code', 'unknown')
                logger.error(f"Facebook API error: {response.status_code} - Code: {error_code} - {error_message}")
                logger.error(f"Full error response: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Facebook API request failed: {e}")
            return None

    # ===== 사용자 정보 =====

    async def get_me(self) -> Optional[Dict]:
        """현재 사용자 정보 조회"""
        return await self._make_request(
            'GET',
            'me',
            params={'fields': 'id,name,email,picture'}
        )

    async def get_my_pages(self) -> Optional[List[Dict]]:
        """사용자가 관리하는 페이지 목록 조회"""
        logger.info("Fetching user's pages from Facebook API")

        # 먼저 me/accounts 시도
        result = await self._make_request(
            'GET',
            'me/accounts',
            params={'fields': 'id,name,category,picture,access_token,fan_count,followers_count'}
        )
        logger.info(f"get_my_pages (me/accounts) result: {result}")

        if result and 'data' in result and len(result['data']) > 0:
            return result['data']

        # me/accounts가 비어있으면 비즈니스를 통해 페이지 조회
        logger.info("No pages from me/accounts, trying me/businesses")
        businesses = await self._make_request(
            'GET',
            'me/businesses',
            params={'fields': 'id,name'}
        )
        logger.info(f"get_my_businesses result: {businesses}")

        if not businesses or 'data' not in businesses:
            return None

        all_pages = []
        for business in businesses['data']:
            business_id = business['id']
            logger.info(f"Fetching pages for business: {business_id}")

            # 비즈니스의 소유 페이지 조회
            pages_result = await self._make_request(
                'GET',
                f'{business_id}/owned_pages',
                params={'fields': 'id,name,category,picture,access_token,fan_count,followers_count'}
            )
            logger.info(f"Business {business_id} owned_pages: {pages_result}")

            if pages_result and 'data' in pages_result:
                all_pages.extend(pages_result['data'])

        return all_pages if all_pages else None

    # ===== 페이지 정보 =====

    async def get_page_info(self, page_id: str) -> Optional[Dict]:
        """페이지 상세 정보 조회"""
        return await self._make_request(
            'GET',
            page_id,
            params={
                'fields': 'id,name,category,picture,fan_count,followers_count,'
                         'about,description,website,phone,emails,location'
            },
            use_page_token=True
        )

    async def get_page_insights(
        self,
        page_id: str,
        metrics: List[str] = None,
        period: str = 'day',
        date_preset: str = 'last_30d'
    ) -> Optional[Dict]:
        """페이지 인사이트 조회"""
        if metrics is None:
            metrics = [
                'page_impressions',
                'page_impressions_unique',
                'page_engaged_users',
                'page_post_engagements',
                'page_fan_adds',
                'page_fan_removes',
                'page_views_total'
            ]

        return await self._make_request(
            'GET',
            f'{page_id}/insights',
            params={
                'metric': ','.join(metrics),
                'period': period,
                'date_preset': date_preset
            },
            use_page_token=True
        )

    # ===== 게시물 관리 =====

    async def get_page_posts(
        self,
        page_id: str,
        limit: int = 25
    ) -> dict:
        """페이지 게시물 목록 조회

        Returns:
            dict: {"data": [...], "error": None} 또는 {"data": None, "error": "에러메시지"}
        """
        # posts 엔드포인트 사용 (페이지가 직접 작성한 게시물만)
        logger.info(f"Fetching posts for page {page_id} with page_token: {self.page_access_token[:20] if self.page_access_token else 'None'}...")

        url = f"{GRAPH_API_BASE_URL}/{page_id}/posts"
        params = {
            'fields': 'id,message,full_picture,permalink_url,created_time,shares,reactions.summary(total_count),comments.summary(total_count)',
            'limit': limit,
            'access_token': self.page_access_token
        }

        try:
            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Facebook get_page_posts result: {len(result.get('data', [])) if result else 0} posts")
                return {"data": result.get('data', []), "error": None}
            else:
                error_data = response.json() if response.text else {}
                error_message = error_data.get('error', {}).get('message', response.text)
                error_code = error_data.get('error', {}).get('code', 'unknown')
                error_type = error_data.get('error', {}).get('type', 'unknown')

                logger.error(f"Facebook API error: {response.status_code} - Code: {error_code} - Type: {error_type} - {error_message}")

                # 사용자 친화적 에러 메시지
                if error_code == 190:  # 토큰 만료
                    return {"data": None, "error": "액세스 토큰이 만료되었습니다. Facebook을 다시 연동해주세요."}
                elif error_code == 200:  # 권한 없음
                    return {"data": None, "error": f"페이지 게시물 읽기 권한이 없습니다. ({error_message})"}
                elif error_code == 10 or error_type == 'OAuthException':
                    return {"data": None, "error": f"Facebook 앱 권한 문제: {error_message}"}
                else:
                    return {"data": None, "error": f"Facebook API 오류: {error_message}"}

        except Exception as e:
            logger.error(f"Facebook API request failed: {e}")
            return {"data": None, "error": f"요청 실패: {str(e)}"}

    async def get_post_details(self, post_id: str) -> Optional[Dict]:
        """게시물 상세 정보 조회"""
        return await self._make_request(
            'GET',
            post_id,
            params={
                'fields': 'id,message,story,full_picture,permalink_url,created_time,'
                         'type,is_published,is_hidden,'
                         'likes.summary(true),comments.summary(true),shares,'
                         'reactions.summary(true)'
            },
            use_page_token=True
        )

    async def create_post(
        self,
        page_id: str,
        message: str,
        link: str = None,
        published: bool = True,
        scheduled_publish_time: int = None
    ) -> Optional[Dict]:
        """페이지에 게시물 작성"""
        data = {'message': message}

        if link:
            data['link'] = link

        if not published:
            data['published'] = 'false'
            if scheduled_publish_time:
                data['scheduled_publish_time'] = scheduled_publish_time

        return await self._make_request(
            'POST',
            f'{page_id}/feed',
            data=data,
            use_page_token=True
        )

    async def create_photo_post(
        self,
        page_id: str,
        photo_url: str,
        caption: str = None,
        published: bool = True
    ) -> Optional[Dict]:
        """페이지에 사진 게시물 작성"""
        data = {'url': photo_url}

        if caption:
            data['caption'] = caption

        if not published:
            data['published'] = 'false'

        return await self._make_request(
            'POST',
            f'{page_id}/photos',
            data=data,
            use_page_token=True
        )

    async def update_post(
        self,
        post_id: str,
        message: str
    ) -> Optional[Dict]:
        """게시물 수정"""
        return await self._make_request(
            'POST',
            post_id,
            data={'message': message},
            use_page_token=True
        )

    async def delete_post(self, post_id: str) -> bool:
        """게시물 삭제"""
        result = await self._make_request(
            'DELETE',
            post_id,
            use_page_token=True
        )
        return result is not None and result.get('success', False)

    async def create_multi_photo_post(
        self,
        page_id: str,
        photo_urls: List[str],
        message: str = None
    ) -> Optional[Dict]:
        """
        페이지에 여러 사진이 포함된 게시물 작성
        1. 각 사진을 published=false로 업로드하여 photo_id 획득
        2. 모든 photo_id를 attached_media로 묶어서 feed에 게시
        """
        if not photo_urls:
            return None

        # 1. 각 사진을 unpublished로 업로드
        photo_ids = []
        for idx, photo_url in enumerate(photo_urls):
            logger.info(f"Uploading photo {idx + 1}/{len(photo_urls)}: {photo_url[:80]}...")
            result = await self._make_request(
                'POST',
                f'{page_id}/photos',
                data={
                    'url': photo_url,
                    'published': 'false'  # 게시하지 않고 ID만 획득
                },
                use_page_token=True
            )
            if result and 'id' in result:
                photo_ids.append(result['id'])
                logger.info(f"Photo {idx + 1} uploaded: {result['id']}")
            else:
                logger.error(f"Failed to upload photo {idx + 1}")
                # 실패 시 계속 진행 (일부만 성공해도 게시)

        if not photo_ids:
            logger.error("No photos were uploaded successfully")
            return None

        # 2. 모든 사진을 하나의 게시물로 묶어서 발행
        data = {}
        if message:
            data['message'] = message

        # attached_media 파라미터로 사진들 연결
        for idx, photo_id in enumerate(photo_ids):
            data[f'attached_media[{idx}]'] = f'{{"media_fbid":"{photo_id}"}}'

        logger.info(f"Creating multi-photo post with {len(photo_ids)} photos")
        return await self._make_request(
            'POST',
            f'{page_id}/feed',
            data=data,
            use_page_token=True
        )

    # ===== 토큰 관리 =====

    async def exchange_token_for_long_lived(
        self,
        app_id: str,
        app_secret: str,
        short_lived_token: str
    ) -> Optional[Dict]:
        """단기 토큰을 장기 토큰으로 교환"""
        try:
            response = await self.client.get(
                f"{GRAPH_API_BASE_URL}/oauth/access_token",
                params={
                    'grant_type': 'fb_exchange_token',
                    'client_id': app_id,
                    'client_secret': app_secret,
                    'fb_exchange_token': short_lived_token
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Token exchange failed: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return None

    async def debug_token(self, token: str, app_token: str) -> Optional[Dict]:
        """토큰 정보 확인"""
        try:
            response = await self.client.get(
                f"{GRAPH_API_BASE_URL}/debug_token",
                params={
                    'input_token': token,
                    'access_token': app_token
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Token debug failed: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Token debug error: {e}")
            return None


async def sync_facebook_posts(
    service: FacebookService,
    page_id: str,
    connection_id: int,
    user_id: int,
    db
) -> dict:
    """Facebook 페이지 게시물 동기화"""
    from .. import models

    result = await service.get_page_posts(page_id, limit=50)

    # 에러가 있으면 에러 정보 반환
    if result.get("error"):
        logger.warning(f"Facebook API error for page {page_id}: {result['error']}")
        return {"new": 0, "updated": 0, "total_fetched": 0, "error": result["error"]}

    posts = result.get("data", [])

    if not posts:
        logger.warning(f"No posts returned from Facebook API for page {page_id}")
        return {"new": 0, "updated": 0, "total_fetched": 0, "error": None}

    logger.info(f"Facebook API returned {len(posts)} posts for page {page_id}")

    new_count = 0
    updated_count = 0

    for post_data in posts:
        post_id = post_data.get('id')
        if not post_id:
            continue

        # 기존 게시물 확인
        existing = db.query(models.FacebookPost).filter(
            models.FacebookPost.post_id == post_id
        ).first()

        # 통계 추출 (reactions로 변경됨)
        likes_count = post_data.get('reactions', {}).get('summary', {}).get('total_count', 0)
        comments_count = post_data.get('comments', {}).get('summary', {}).get('total_count', 0)
        shares_count = post_data.get('shares', {}).get('count', 0) if post_data.get('shares') else 0

        # 게시 시간 파싱
        created_time = None
        if post_data.get('created_time'):
            try:
                created_time = datetime.fromisoformat(
                    post_data['created_time'].replace('Z', '+00:00')
                )
            except Exception:
                pass

        if existing:
            # 업데이트
            existing.message = post_data.get('message')
            existing.story = post_data.get('story')
            existing.full_picture = post_data.get('full_picture')
            existing.permalink_url = post_data.get('permalink_url')
            existing.likes_count = likes_count
            existing.comments_count = comments_count
            existing.shares_count = shares_count
            existing.is_published = post_data.get('is_published', True)
            existing.is_hidden = post_data.get('is_hidden', False)
            existing.last_stats_updated_at = datetime.utcnow()
            updated_count += 1
        else:
            # 새로 생성
            new_post = models.FacebookPost(
                connection_id=connection_id,
                user_id=user_id,
                post_id=post_id,
                message=post_data.get('message'),
                story=post_data.get('story'),
                full_picture=post_data.get('full_picture'),
                permalink_url=post_data.get('permalink_url'),
                post_type=post_data.get('type'),
                created_time=created_time,
                is_published=post_data.get('is_published', True),
                is_hidden=post_data.get('is_hidden', False),
                likes_count=likes_count,
                comments_count=comments_count,
                shares_count=shares_count,
                last_stats_updated_at=datetime.utcnow()
            )
            db.add(new_post)
            new_count += 1

    db.commit()
    logger.info(f"Facebook sync complete: {new_count} new, {updated_count} updated")
    return {"new": new_count, "updated": updated_count, "total_fetched": len(posts), "error": None}
