"""
Data Normalizer

플랫폼별 원시 데이터를 UnifiedContent 형식으로 변환
"""

import logging
from typing import Dict, Any
from datetime import datetime
from .schemas import UnifiedContent, MediaInfo, EngagementMetrics

logger = logging.getLogger(__name__)


# ===== Layer 2: Data Normalizer =====

class DataNormalizer:
    """플랫폼별 데이터를 통합 형식으로 정규화"""

    def normalize(self, raw_data: Dict[str, Any]) -> UnifiedContent:
        """
        원시 데이터를 UnifiedContent로 변환

        Args:
            raw_data: 플랫폼별 원시 데이터

        Returns:
            UnifiedContent 객체
        """
        platform = raw_data.get('platform', 'unknown')

        if platform == 'instagram':
            return self._normalize_instagram(raw_data)
        elif platform == 'youtube':
            return self._normalize_youtube(raw_data)
        elif platform == 'threads':
            return self._normalize_threads(raw_data)
        else:
            logger.warning(f"⚠️ 알 수 없는 플랫폼: {platform}")
            return self._normalize_generic(raw_data)

    def _normalize_instagram(self, data: Dict[str, Any]) -> UnifiedContent:
        """인스타그램 데이터 정규화"""
        try:
            # 이미지 정보
            image_urls = data.get('image_urls', [])
            media = MediaInfo(
                type='image' if image_urls else 'none',
                urls=image_urls,
                count=len(image_urls)
            ) if image_urls else None

            # 참여 지표
            engagement = EngagementMetrics(
                likes=data.get('likes', 0),
                comments=data.get('comments', 0),
                shares=0,  # 인스타그램은 공유 지표 없음
                views=0
            )

            # 날짜 파싱
            date_str = data.get('date')
            created_at = None
            if date_str:
                try:
                    created_at = datetime.fromisoformat(date_str)
                except:
                    created_at = None

            return UnifiedContent(
                platform='instagram',
                title=None,  # 인스타그램은 제목 없음
                body_text=data.get('caption', ''),
                media=media,
                tags=data.get('hashtags', []),
                engagement=engagement,
                created_at=created_at,
                platform_specific={
                    'post_id': data.get('post_id'),
                    'location': data.get('location')
                }
            )
        except Exception as e:
            logger.error(f"❌ 인스타그램 데이터 정규화 실패: {e}")
            return self._normalize_generic(data)

    def _normalize_youtube(self, data: Dict[str, Any]) -> UnifiedContent:
        """유튜브 데이터 정규화"""
        try:
            # 비디오 정보
            thumbnail_url = data.get('thumbnail_url')
            media = MediaInfo(
                type='video',
                urls=[thumbnail_url] if thumbnail_url else [],
                count=1
            ) if thumbnail_url else None

            # 참여 지표
            engagement = EngagementMetrics(
                likes=data.get('likes', 0),
                comments=data.get('comments', 0),
                shares=0,  # YouTube Data API v3에서는 공유 수 제공 안 함
                views=data.get('views', 0)
            )

            # 날짜 파싱
            date_str = data.get('date')
            created_at = None
            if date_str:
                try:
                    created_at = datetime.fromisoformat(date_str)
                except:
                    created_at = None

            return UnifiedContent(
                platform='youtube',
                title=data.get('title'),
                body_text=data.get('description', ''),
                media=media,
                tags=[],  # TODO: 유튜브 태그 추출
                engagement=engagement,
                created_at=created_at,
                platform_specific={
                    'video_id': data.get('video_id'),
                    'duration': data.get('duration'),
                    'category': data.get('category')
                }
            )
        except Exception as e:
            logger.error(f"❌ 유튜브 데이터 정규화 실패: {e}")
            return self._normalize_generic(data)

    def _normalize_threads(self, data: Dict[str, Any]) -> UnifiedContent:
        """Threads 데이터 정규화"""
        try:
            # 미디어 정보
            media_type = data.get('media_type')
            media_url = data.get('media_url')
            thumbnail_url = data.get('thumbnail_url')

            media = None
            if media_type and media_url:
                # IMAGE, VIDEO, CAROUSEL_ALBUM 등
                urls = [media_url]
                if thumbnail_url and thumbnail_url != media_url:
                    urls.append(thumbnail_url)

                media = MediaInfo(
                    type='video' if media_type == 'VIDEO' else 'image',
                    urls=urls,
                    count=1
                )

            # 참여 지표 (Threads는 views, likes, replies, reposts, quotes 제공)
            engagement = EngagementMetrics(
                likes=data.get('likes', 0),
                comments=data.get('replies', 0),  # replies를 comments로 매핑
                shares=data.get('reposts', 0) + data.get('quotes', 0),  # reposts + quotes
                views=data.get('views', 0)
            )

            # 날짜 파싱
            date_str = data.get('date')
            created_at = None
            if date_str:
                try:
                    created_at = datetime.fromisoformat(date_str)
                except:
                    created_at = None

            return UnifiedContent(
                platform='threads',
                title=None,  # Threads는 제목 없음
                body_text=data.get('text', ''),
                media=media,
                tags=data.get('hashtags', []),
                engagement=engagement,
                created_at=created_at,
                platform_specific={
                    'username': data.get('username'),
                    'name': data.get('name'),
                    'biography': data.get('biography'),
                    'profile_picture_url': data.get('profile_picture_url'),
                    'reposts': data.get('reposts', 0),
                    'quotes': data.get('quotes', 0)
                }
            )
        except Exception as e:
            logger.error(f"❌ Threads 데이터 정규화 실패: {e}")
            return self._normalize_generic(data)

    def _normalize_generic(self, data: Dict[str, Any]) -> UnifiedContent:
        """범용 데이터 정규화 (폴백)"""
        return UnifiedContent(
            platform=data.get('platform', 'unknown'),
            title=data.get('title'),
            body_text=data.get('content', '') or data.get('caption', '') or data.get('description', ''),
            media=None,
            tags=[],
            engagement=None,
            created_at=None,
            platform_specific=data
        )
