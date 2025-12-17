"""
Brand Analysis Pipeline

Multi-Agent Pipeline의 메인 조율자
"""

import logging
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
from .collectors import BlogCollectorAgent, InstagramCollectorAgent, YouTubeCollectorAgent
from .normalizer import DataNormalizer
from .analyzers import TextAnalyzerAgent, VisualAnalyzerAgent, EngagementAnalyzerAgent
from .synthesizer import BrandProfileSynthesizer
from .schemas import BrandProfile, UnifiedContent, MediaInfo, BrandProfileSource, ConfidenceLevel

logger = logging.getLogger(__name__)


class BrandAnalysisPipeline:
    """
    브랜드 분석 Multi-Agent Pipeline

    4 Layer Architecture:
    - Layer 1: Platform Collectors (데이터 수집)
    - Layer 2: Data Normalizer (데이터 정규화)
    - Layer 3: Analysis Agents (분석)
    - Layer 4: Brand Profile Synthesizer (통합)
    """

    def __init__(self, db=None):
        """
        Args:
            db: Database session (YouTube Collector에 필요)
        """
        self.db = db

        # Layer 1: Collectors (YouTube는 런타임에 생성)
        self.collectors = {
            'blog': BlogCollectorAgent(),
            'instagram': InstagramCollectorAgent()
        }

        # Layer 2: Normalizer
        self.normalizer = DataNormalizer()

        # Layer 3: Analyzers
        self.analyzers = {
            'text': TextAnalyzerAgent(),
            'visual': VisualAnalyzerAgent(),
            'engagement': EngagementAnalyzerAgent()
        }

        # Layer 4: Synthesizer
        self.synthesizer = BrandProfileSynthesizer()

    async def run(
        self,
        user_id: int,
        platform_urls: Dict[str, str],
        max_items: int = 10
    ) -> BrandProfile:
        """
        브랜드 분석 Pipeline 실행

        Args:
            user_id: 사용자 ID (int)
            platform_urls: 플랫폼별 URL
                {
                    'blog': 'https://blog.naver.com/example',
                    'instagram': 'https://instagram.com/example',
                    'youtube': 'connected'  # YouTube는 OAuth 연동 기반
                }
            max_items: 각 플랫폼당 최대 수집 아이템 수

        Returns:
            BrandProfile 객체
        """
        try:
            logger.info("=" * 80)
            logger.info("🚀 Brand Analysis Multi-Agent Pipeline 시작")
            logger.info("=" * 80)

            # ===== Layer 1: 데이터 수집 =====
            logger.info("\n📦 Layer 1: Platform Data Collection")
            logger.info("-" * 80)

            collection_tasks = []
            platforms_to_analyze = []

            # 입력된 플랫폼에 대해서만 collector 실행
            if 'blog' in platform_urls and platform_urls['blog']:
                logger.info(f"  ✓ 블로그 수집 예정: {platform_urls['blog']}")
                collection_tasks.append(
                    self.collectors['blog'].collect(platform_urls['blog'], max_items)
                )
                platforms_to_analyze.append('naver_blog')

            if 'instagram' in platform_urls and platform_urls['instagram']:
                logger.info(f"  ✓ 인스타그램 수집 예정: {platform_urls['instagram']}")
                collection_tasks.append(
                    self.collectors['instagram'].collect(platform_urls['instagram'], max_items)
                )
                platforms_to_analyze.append('instagram')

            # YouTube는 OAuth 연동 기반으로 수집
            if 'youtube' in platform_urls and platform_urls['youtube']:
                logger.info(f"  ✓ YouTube 수집 예정 (OAuth 연동 기반)")
                youtube_collector = YouTubeCollectorAgent(db=self.db, user_id=user_id)
                collection_tasks.append(
                    youtube_collector.collect(max_items=max_items)
                )
                platforms_to_analyze.append('youtube')

            if not collection_tasks:
                raise ValueError("분석할 플랫폼이 없습니다")

            # 병렬 수집 실행
            logger.info(f"\n  ⏳ {len(collection_tasks)}개 플랫폼 병렬 수집 중...")
            raw_contents_lists = await asyncio.gather(*collection_tasks, return_exceptions=False)

            # 결과 병합
            raw_contents = []
            for raw_list in raw_contents_lists:
                if raw_list:
                    raw_contents.extend(raw_list)

            logger.info(f"  ✅ 총 {len(raw_contents)}개 콘텐츠 수집 완료")

            if not raw_contents:
                raise ValueError("수집된 콘텐츠가 없습니다")

            # ===== Layer 2: 데이터 정규화 =====
            logger.info("\n🔄 Layer 2: Data Normalization")
            logger.info("-" * 80)

            unified_contents = [
                self.normalizer.normalize(raw) for raw in raw_contents
            ]
            logger.info(f"  ✅ {len(unified_contents)}개 콘텐츠 정규화 완료")

            # ===== Layer 3: 분석 =====
            logger.info("\n🔍 Layer 3: Multi-Agent Analysis")
            logger.info("-" * 80)

            logger.info("  📝 텍스트 분석 시작...")
            logger.info("  🎨 비주얼 분석 시작...")
            logger.info("  📊 참여 지표 분석 시작...")

            # 병렬 분석 실행
            text_analysis, visual_analysis, engagement_analysis = await asyncio.gather(
                self.analyzers['text'].analyze(unified_contents),
                self.analyzers['visual'].analyze(unified_contents),
                self.analyzers['engagement'].analyze(unified_contents)
            )

            logger.info("  ✅ 모든 분석 완료")

            # ===== Layer 4: 브랜드 프로필 통합 =====
            logger.info("\n🔮 Layer 4: Brand Profile Synthesis")
            logger.info("-" * 80)

            brand_profile = await self.synthesizer.synthesize(
                user_id=user_id,
                text_analysis=text_analysis,
                visual_analysis=visual_analysis,
                engagement_analysis=engagement_analysis,
                unified_contents=unified_contents,
                analyzed_platforms=platforms_to_analyze
            )

            # ✅ 메타데이터 업데이트: SNS 분석임을 명시
            brand_profile.source = BrandProfileSource.SNS_ANALYSIS
            brand_profile.confidence_level = ConfidenceLevel.HIGH
            brand_profile.updated_at = datetime.utcnow()

            logger.info("=" * 80)
            logger.info("✅ Brand Analysis Pipeline 완료!")
            logger.info(f"   브랜드명: {brand_profile.brand_name or '(미확인)'}")
            logger.info(f"   분석된 플랫폼: {', '.join(platforms_to_analyze)}")
            logger.info(f"   총 콘텐츠 수: {len(unified_contents)}")
            logger.info(f"   신뢰도: {brand_profile.confidence_level}")
            logger.info("=" * 80 + "\n")

            return brand_profile

        except Exception as e:
            logger.error(f"\n❌ Pipeline 실행 실패: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"브랜드 분석 실패: {str(e)}")

    async def run_from_manual_samples(
        self,
        user_id: str,
        text_samples: Optional[List[str]] = None,
        image_samples: Optional[List[str]] = None,
        video_samples: Optional[List[str]] = None
    ) -> BrandProfile:
        """
        수동 샘플로부터 브랜드 분석 (Multi-Agent Pipeline 활용)

        Args:
            user_id: 사용자 ID
            text_samples: 텍스트 샘플 리스트
            image_samples: 이미지 파일 경로 리스트
            video_samples: 영상 파일 경로 리스트

        Returns:
            BrandProfile 객체 (source=MANUAL_SAMPLES, confidence_level=MEDIUM)
        """
        try:
            logger.info("=" * 80)
            logger.info("🚀 Manual Samples Brand Analysis Pipeline 시작")
            logger.info("=" * 80)

            # ===== Layer 1 건너뛰기: 수동 샘플을 UnifiedContent로 변환 =====
            logger.info("\n📦 Manual Samples → UnifiedContent 변환")
            logger.info("-" * 80)

            unified_contents = []

            # 텍스트 샘플 변환
            if text_samples:
                for idx, text in enumerate(text_samples):
                    if text and text.strip():
                        unified_contents.append(UnifiedContent(
                            platform='manual_text',
                            title=None,
                            body_text=text,
                            media=None,
                            tags=[],
                            engagement=None,
                            created_at=datetime.utcnow(),
                            platform_specific={'sample_index': idx}
                        ))
                logger.info(f"  ✓ {len(text_samples)}개 텍스트 샘플 변환 완료")

            # 이미지 샘플 변환
            if image_samples:
                for idx, img_path in enumerate(image_samples):
                    unified_contents.append(UnifiedContent(
                        platform='manual_image',
                        title=None,
                        body_text='',
                        media=MediaInfo(
                            type='image',
                            urls=[img_path],
                            count=1
                        ),
                        tags=[],
                        engagement=None,
                        created_at=datetime.utcnow(),
                        platform_specific={'sample_index': idx, 'file_path': img_path}
                    ))
                logger.info(f"  ✓ {len(image_samples)}개 이미지 샘플 변환 완료")

            # 영상 샘플 변환
            if video_samples:
                for idx, vid_path in enumerate(video_samples):
                    unified_contents.append(UnifiedContent(
                        platform='manual_video',
                        title=None,
                        body_text='',
                        media=MediaInfo(
                            type='video',
                            urls=[vid_path],
                            count=1
                        ),
                        tags=[],
                        engagement=None,
                        created_at=datetime.utcnow(),
                        platform_specific={'sample_index': idx, 'file_path': vid_path}
                    ))
                logger.info(f"  ✓ {len(video_samples)}개 영상 샘플 변환 완료")

            if not unified_contents:
                raise ValueError("변환된 샘플이 없습니다")

            logger.info(f"  ✅ 총 {len(unified_contents)}개 샘플 UnifiedContent로 변환 완료")

            # ===== Layer 2: 정규화 건너뛰기 (이미 UnifiedContent 형식) =====

            # ===== Layer 3: 분석 =====
            logger.info("\n🔍 Layer 3: Multi-Agent Analysis")
            logger.info("-" * 80)

            logger.info("  📝 텍스트 분석 시작...")
            logger.info("  🎨 비주얼 분석 시작...")
            logger.info("  📊 참여 지표 분석 시작...")

            # 병렬 분석 실행
            text_analysis, visual_analysis, engagement_analysis = await asyncio.gather(
                self.analyzers['text'].analyze(unified_contents),
                self.analyzers['visual'].analyze(unified_contents),
                self.analyzers['engagement'].analyze(unified_contents)
            )

            logger.info("  ✅ 모든 분석 완료")

            # ===== Layer 4: 브랜드 프로필 통합 =====
            logger.info("\n🔮 Layer 4: Brand Profile Synthesis")
            logger.info("-" * 80)

            brand_profile = await self.synthesizer.synthesize(
                user_id=user_id,
                text_analysis=text_analysis,
                visual_analysis=visual_analysis,
                engagement_analysis=engagement_analysis,
                unified_contents=unified_contents,
                analyzed_platforms=['manual_samples']
            )

            # ✅ 메타데이터 업데이트: 수동 샘플 분석임을 명시
            brand_profile.source = BrandProfileSource.MANUAL_SAMPLES
            brand_profile.confidence_level = ConfidenceLevel.MEDIUM
            brand_profile.updated_at = datetime.utcnow()

            logger.info("=" * 80)
            logger.info("✅ Manual Samples Brand Analysis Pipeline 완료!")
            logger.info(f"   브랜드명: {brand_profile.brand_name or '(미확인)'}")
            logger.info(f"   분석된 샘플: {len(unified_contents)}개")
            logger.info(f"   신뢰도: {brand_profile.confidence_level}")
            logger.info("=" * 80 + "\n")

            return brand_profile

        except Exception as e:
            logger.error(f"\n❌ Manual Samples Pipeline 실행 실패: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"수동 샘플 브랜드 분석 실패: {str(e)}")
