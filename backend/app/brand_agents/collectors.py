"""
Platform Collector Agents

각 플랫폼별로 데이터를 수집하는 Collector Agent
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

from ..services.naver_blog_service import NaverBlogService
from ..services.youtube_service import YouTubeService
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
    """인스타그램 Collector Agent"""

    async def collect(self, url: str, max_items: int = 10) -> List[Dict[str, Any]]:
        """
        인스타그램 포스트 수집

        Args:
            url: 인스타그램 프로필 URL
            max_items: 최대 포스트 수

        Returns:
            인스타그램 포스트 리스트
            [
                {
                    'caption': str,
                    'image_urls': List[str],
                    'hashtags': List[str],
                    'likes': int,
                    'comments': int,
                    'date': str,
                    'platform': 'instagram'
                },
                ...
            ]
        """
        try:
            logger.info(f"📷 [Instagram Collector] 인스타그램 수집 시작: {url}")

            # TODO: 실제 Instagram API 또는 크롤링 구현
            # 현재는 더미 데이터 반환
            logger.warning("⚠️ [Instagram Collector] 실제 구현 필요 - 더미 데이터 반환")

            dummy_posts = [
                {
                    'caption': f"인스타그램 샘플 포스트 {i+1}\n\n우리 브랜드의 새로운 제품을 소개합니다! #브랜드 #신제품",
                    'image_urls': [f"https://example.com/image_{i+1}.jpg"],
                    'hashtags': ['브랜드', '신제품', '일상'],
                    'likes': 100 + i * 10,
                    'comments': 10 + i,
                    'date': datetime.now().isoformat(),
                    'platform': 'instagram'
                }
                for i in range(min(max_items, 3))  # 더미는 최대 3개
            ]

            logger.info(f"✅ [Instagram Collector] {len(dummy_posts)}개 포스트 수집 완료 (더미)")
            return dummy_posts

        except Exception as e:
            logger.error(f"❌ [Instagram Collector] 수집 실패: {e}")
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
