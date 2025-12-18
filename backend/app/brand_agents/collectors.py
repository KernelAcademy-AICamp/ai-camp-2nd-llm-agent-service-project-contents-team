"""
Platform Collector Agents

각 플랫폼별로 데이터를 수집하는 Collector Agent
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

from ..services.naver_blog_service import NaverBlogService
from ..services.youtube_service import YouTubeService
from ..services.instagram_service import InstagramService
from ..services.threads_service import ThreadsService
from sqlalchemy.orm import Session
from .. import models

logger = logging.getLogger(__name__)


# ===== Layer 1: Platform Collector Agents =====

class PlatformCollectorAgent(ABC):
    """플랫폼 Collector Agent 추상 클래스"""

    @abstractmethod
    async def collect(self, url: str, max_items: int) -> List[Dict[str, Any]]:
        """
        플랫폼에서 콘텐츠 수집

        Args:
            url: 플랫폼 URL
            max_items: 최대 수집 아이템 수

        Returns:
            수집된 원시 데이터 리스트
        """
        pass


class BlogCollectorAgent(PlatformCollectorAgent):
    """네이버 블로그 Collector Agent"""

    def __init__(self):
        self.blog_service = NaverBlogService()

    async def collect(self, url: str, max_items: int = 10) -> List[Dict[str, Any]]:
        """
        네이버 블로그 포스트 수집

        Args:
            url: 블로그 URL
            max_items: 최대 포스트 수

        Returns:
            블로그 포스트 리스트
            [
                {
                    'title': str,
                    'content': str,
                    'date': str,
                    'link': str,
                    'platform': 'naver_blog'
                },
                ...
            ]
        """
        try:
            logger.info(f"📚 [Blog Collector] 블로그 수집 시작: {url}")
            posts = await self.blog_service.collect_blog_posts(url, max_items)

            if not posts:
                logger.warning(f"⚠️ [Blog Collector] 수집된 포스트가 없습니다")
                return []

            # platform 필드 추가
            for post in posts:
                post['platform'] = 'naver_blog'

            logger.info(f"✅ [Blog Collector] {len(posts)}개 포스트 수집 완료")
            return posts

        except Exception as e:
            logger.error(f"❌ [Blog Collector] 수집 실패: {e}")
            return []


class InstagramCollectorAgent(PlatformCollectorAgent):
    """인스타그램 Collector Agent (OAuth 연동 기반)"""

    def __init__(self, db: Session = None, user_id: int = None):
        """
        Args:
            db: Database session
            user_id: User ID (Instagram 연동 확인용)
        """
        self.db = db
        self.user_id = user_id

    async def collect(self, url: str = None, max_items: int = 25) -> List[Dict[str, Any]]:
        """
        인스타그램 포스트 수집 (OAuth 연동 기반)

        Args:
            url: 사용 안 함 (OAuth 연동으로 자동 수집)
            max_items: 최대 포스트 수

        Returns:
            인스타그램 포스트 리스트
            [
                {
                    'caption': str,
                    'image_urls': List[str],
                    'media_url': str,
                    'media_type': str,
                    'hashtags': List[str],
                    'likes': int,
                    'comments': int,
                    'date': str,
                    'platform': 'instagram',
                    'username': str,
                    'followers_count': int
                },
                ...
            ]
        """
        try:
            logger.info(f"📷 [Instagram Collector] Instagram 계정 연동 데이터 수집 시작 (user_id: {self.user_id})")

            if not self.db or not self.user_id:
                logger.warning("⚠️ [Instagram Collector] DB session 또는 user_id가 없습니다")
                return []

            # Instagram Connection 확인
            instagram_connection = self.db.query(models.InstagramConnection).filter(
                models.InstagramConnection.user_id == self.user_id,
                models.InstagramConnection.is_active == True
            ).first()

            if not instagram_connection:
                logger.warning(f"⚠️ [Instagram Collector] 연동된 Instagram 계정이 없습니다 (user_id: {self.user_id})")
                return []

            logger.info(f"✅ [Instagram Collector] 연동된 Instagram 계정 발견: @{instagram_connection.instagram_username}")

            # InstagramService 생성
            instagram_service = InstagramService(instagram_connection.page_access_token)

            # 계정 정보 가져오기
            account_info = await instagram_service.get_account_info(instagram_connection.instagram_account_id)

            if not account_info:
                logger.error("❌ [Instagram Collector] 계정 정보 가져오기 실패")
                await instagram_service.close()
                return []

            username = account_info.get('username', '')
            followers_count = account_info.get('followers_count', 0)

            # 게시물 목록 가져오기
            media_list = await instagram_service.get_media_list(
                instagram_connection.instagram_account_id,
                limit=max_items
            )

            await instagram_service.close()

            if not media_list:
                logger.warning("⚠️ [Instagram Collector] 수집된 게시물이 없습니다")
                return []

            # 데이터 정규화
            collected_posts = []
            for media in media_list:
                caption = media.get('caption', '')

                # 해시태그 추출
                hashtags = re.findall(r'#(\w+)', caption)

                # media_url 처리
                media_url = media.get('media_url', '')
                media_type = media.get('media_type', 'IMAGE')

                # thumbnail_url은 비디오일 때 사용
                if media_type == 'VIDEO':
                    media_url = media.get('thumbnail_url', media_url)

                collected_posts.append({
                    'caption': caption,
                    'image_urls': [media_url] if media_url else [],
                    'media_url': media_url,
                    'media_type': media_type,
                    'hashtags': hashtags,
                    'likes': media.get('like_count', 0),
                    'comments': media.get('comments_count', 0),
                    'date': media.get('timestamp', ''),
                    'platform': 'instagram',
                    'username': username,
                    'followers_count': followers_count
                })

            logger.info(f"✅ [Instagram Collector] {len(collected_posts)}개 게시물 수집 완료")
            logger.info(f"   계정: @{username} (팔로워: {followers_count:,}명)")

            return collected_posts

        except Exception as e:
            logger.error(f"❌ [Instagram Collector] 수집 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []


class YouTubeCollectorAgent(PlatformCollectorAgent):
    """유튜브 Collector Agent (OAuth 연동 기반)"""

    def __init__(self, db: Session = None, user_id: int = None):
        """
        Args:
            db: Database session
            user_id: User ID (YouTube 연동 확인용)
        """
        self.db = db
        self.user_id = user_id

    async def collect(self, url: str = None, max_items: int = 10) -> List[Dict[str, Any]]:
        """
        유튜브 비디오 수집 (OAuth 연동 기반)

        Args:
            url: 사용 안 함 (OAuth 연동으로 자동 수집)
            max_items: 최대 비디오 수

        Returns:
            유튜브 비디오 리스트
            [
                {
                    'title': str,
                    'description': str,
                    'thumbnail_url': str,
                    'tags': List[str],
                    'views': int,
                    'likes': int,
                    'comments': int,
                    'date': str,
                    'duration': str,
                    'platform': 'youtube',
                    'channel_name': str,
                    'channel_description': str,
                    'subscriber_count': int
                },
                ...
            ]
        """
        try:
            logger.info(f"🎥 [YouTube Collector] YouTube 계정 연동 데이터 수집 시작 (user_id: {self.user_id})")

            if not self.db or not self.user_id:
                logger.warning("⚠️ [YouTube Collector] DB session 또는 user_id가 없습니다")
                return []

            # YouTube Connection 확인
            youtube_connection = self.db.query(models.YouTubeConnection).filter(
                models.YouTubeConnection.user_id == self.user_id,
                models.YouTubeConnection.is_active == True
            ).first()

            if not youtube_connection:
                logger.warning(f"⚠️ [YouTube Collector] 연동된 YouTube 계정이 없습니다 (user_id: {self.user_id})")
                return []

            logger.info(f"✅ [YouTube Collector] 연동된 YouTube 채널 발견: {youtube_connection.channel_title}")

            # YouTubeService 생성
            youtube_service = YouTubeService(
                youtube_connection.access_token,
                youtube_connection.refresh_token
            )

            # 채널 정보 가져오기
            channel_info = await youtube_service.get_my_channel()

            if not channel_info:
                logger.error("❌ [YouTube Collector] 채널 정보 가져오기 실패")
                return []

            channel_snippet = channel_info.get('snippet', {})
            channel_title = channel_snippet.get('title', '')
            channel_description = channel_snippet.get('description', '')
            statistics = channel_info.get('statistics', {})
            subscriber_count = int(statistics.get('subscriberCount', 0))

            # 내 동영상 목록 가져오기
            videos = await youtube_service.get_my_videos(max_results=max_items)

            if not videos:
                logger.warning("⚠️ [YouTube Collector] 수집된 동영상이 없습니다")
                return []

            # 데이터 정규화
            collected_videos = []
            for video in videos:
                snippet = video.get('snippet', {})
                statistics = video.get('statistics', {})
                content_details = video.get('contentDetails', {})

                collected_videos.append({
                    'title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                    'tags': snippet.get('tags', []),
                    'views': int(statistics.get('viewCount', 0)),
                    'likes': int(statistics.get('likeCount', 0)),
                    'comments': int(statistics.get('commentCount', 0)),
                    'date': snippet.get('publishedAt', ''),
                    'duration': content_details.get('duration', ''),
                    'platform': 'youtube',
                    'channel_name': channel_title,
                    'channel_description': channel_description,
                    'subscriber_count': subscriber_count
                })

            logger.info(f"✅ [YouTube Collector] {len(collected_videos)}개 동영상 수집 완료")
            logger.info(f"   채널: {channel_title} (구독자: {subscriber_count:,}명)")

            return collected_videos

        except Exception as e:
            logger.error(f"❌ [YouTube Collector] 수집 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []


class ThreadsCollectorAgent(PlatformCollectorAgent):
    """Threads Collector Agent (OAuth 연동 기반)"""

    def __init__(self, db: Session = None, user_id: int = None):
        """
        Args:
            db: Database session
            user_id: User ID (Threads 연동 확인용)
        """
        self.db = db
        self.user_id = user_id

    async def collect(self, url: str = None, max_items: int = 25) -> List[Dict[str, Any]]:
        """
        Threads 포스트 수집 (OAuth 연동 기반)

        Args:
            url: 사용 안 함 (OAuth 연동으로 자동 수집)
            max_items: 최대 포스트 수

        Returns:
            Threads 포스트 리스트
            [
                {
                    'text': str,
                    'media_type': str,
                    'media_url': str,
                    'thumbnail_url': str,
                    'hashtags': List[str],
                    'views': int,
                    'likes': int,
                    'replies': int,
                    'reposts': int,
                    'quotes': int,
                    'date': str,
                    'platform': 'threads',
                    'username': str,
                    'name': str,
                    'biography': str,
                    'profile_picture_url': str
                },
                ...
            ]
        """
        try:
            logger.info(f"🧵 [Threads Collector] Threads 계정 연동 데이터 수집 시작 (user_id: {self.user_id})")

            if not self.db or not self.user_id:
                logger.warning("⚠️ [Threads Collector] DB session 또는 user_id가 없습니다")
                return []

            # Threads Connection 확인
            threads_connection = self.db.query(models.ThreadsConnection).filter(
                models.ThreadsConnection.user_id == self.user_id,
                models.ThreadsConnection.is_active == True
            ).first()

            if not threads_connection:
                logger.warning(f"⚠️ [Threads Collector] 연동된 Threads 계정이 없습니다 (user_id: {self.user_id})")
                return []

            logger.info(f"✅ [Threads Collector] 연동된 Threads 계정 발견: @{threads_connection.username}")

            # ThreadsService 생성
            threads_service = ThreadsService(threads_connection.access_token)

            # 사용자 정보 가져오기
            user_info = await threads_service.get_me()

            if not user_info:
                logger.error("❌ [Threads Collector] 사용자 정보 가져오기 실패")
                return []

            username = user_info.get('username', '')
            name = user_info.get('name', '')
            biography = user_info.get('threads_biography', '')
            profile_picture_url = user_info.get('threads_profile_picture_url', '')
            threads_user_id = user_info.get('id', threads_connection.threads_user_id)

            # 포스트 목록 가져오기
            posts_result = await threads_service.get_user_threads(
                threads_user_id,
                limit=max_items
            )

            if not posts_result or 'data' not in posts_result:
                logger.warning("⚠️ [Threads Collector] 수집된 포스트가 없습니다")
                return []

            posts_data = posts_result['data']

            # 데이터 정규화
            collected_posts = []
            for post in posts_data:
                post_id = post.get('id', '')
                text = post.get('text', '')

                # 해시태그 추출
                hashtags = re.findall(r'#(\w+)', text)

                # 인사이트 조회 (통계)
                insights = await threads_service.get_thread_insights(post_id)
                stats = {}
                if insights and 'data' in insights:
                    for metric in insights['data']:
                        metric_name = metric.get('name', '')
                        metric_values = metric.get('values', [])
                        if metric_values:
                            stats[metric_name] = metric_values[0].get('value', 0)

                collected_posts.append({
                    'text': text,
                    'media_type': post.get('media_type', 'TEXT'),
                    'media_url': post.get('media_url', ''),
                    'thumbnail_url': post.get('thumbnail_url', ''),
                    'hashtags': hashtags,
                    'views': stats.get('views', 0),
                    'likes': stats.get('likes', 0),
                    'replies': stats.get('replies', 0),
                    'reposts': stats.get('reposts', 0),
                    'quotes': stats.get('quotes', 0),
                    'date': post.get('timestamp', ''),
                    'platform': 'threads',
                    'username': username,
                    'name': name,
                    'biography': biography,
                    'profile_picture_url': profile_picture_url
                })

            logger.info(f"✅ [Threads Collector] {len(collected_posts)}개 포스트 수집 완료")
            logger.info(f"   계정: @{username} ({name})")

            return collected_posts

        except Exception as e:
            logger.error(f"❌ [Threads Collector] 수집 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
