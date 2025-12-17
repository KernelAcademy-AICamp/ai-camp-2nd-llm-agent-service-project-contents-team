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

        if platform == 'naver_blog':
            return self._normalize_blog(raw_data)
        elif platform == 'instagram':
            return self._normalize_instagram(raw_data)
        elif platform == 'youtube':
            return self._normalize_youtube(raw_data)
        else:
            logger.warning(f"⚠️ 알 수 없는 플랫폼: {platform}")
            return self._normalize_generic(raw_data)

    def _normalize_blog(self, data: Dict[str, Any]) -> UnifiedContent:
        """네이버 블로그 데이터 정규화"""
        try:
            # 날짜 파싱
            date_str = data.get('date')
            created_at = None
            if date_str and date_str != 'N/A':
                try:
                    created_at = datetime.fromisoformat(date_str)
                except:
                    created_at = None

            return UnifiedContent(
                platform='naver_blog',
                title=data.get('title'),
                body_text=data.get('content', ''),
                media=None,  # 블로그는 텍스트 중심
                tags=[],  # TODO: 블로그에서 태그 추출
                engagement=None,  # 블로그는 참여 지표 없음
                created_at=created_at,
                platform_specific={
                    'link': data.get('link'),
                    'category': data.get('category')
                }
            )
        except Exception as e:
            logger.error(f"❌ 블로그 데이터 정규화 실패: {e}")
            return self._normalize_generic(data)

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
