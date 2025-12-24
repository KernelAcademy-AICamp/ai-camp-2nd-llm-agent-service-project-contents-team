"""
멀티 플랫폼 브랜드 분석 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import asyncio

from ..database import get_db, SessionLocal
from ..models import User, BrandAnalysis, YouTubeConnection, InstagramConnection, ThreadsConnection
from ..auth import get_current_user
from ..services.brand_analyzer_service import BrandAnalyzerService
from ..services.supabase_storage import get_storage_service
from ..brand_agents import BrandAnalysisPipeline
import uuid

router = APIRouter(prefix="/api/brand-analysis", tags=["brand-analysis"])
logger = logging.getLogger(__name__)


def update_analysis_progress(db: Session, user_id: int, progress: int, step: str):
    """분석 진행률 업데이트 헬퍼 함수"""
    try:
        brand_analysis = db.query(BrandAnalysis).filter(BrandAnalysis.user_id == user_id).first()
        if brand_analysis:
            brand_analysis.analysis_progress = progress
            brand_analysis.analysis_step = step
            db.commit()
            logger.info(f"📊 Progress 업데이트: {progress}% ({step})")
    except Exception as e:
        logger.error(f"Progress 업데이트 실패: {e}")


class MultiPlatformAnalysisRequest(BaseModel):
    """멀티 플랫폼 분석 요청"""
    instagram_url: Optional[str] = None
    youtube_url: Optional[str] = None
    threads_url: Optional[str] = None
    max_posts: int = 10  # 각 플랫폼당 최대 포스트 수


class BasicProfileRequest(BaseModel):
    """기본 프로필 생성 요청"""
    brand_name: str
    business_type: str
    business_description: str
    target_audience: str
    selected_styles: Optional[List[str]] = None
    brand_values: Optional[List[str]] = None


class ManualAnalysisRequest(BaseModel):
    """수동 콘텐츠 분석 요청"""
    text_samples: Optional[List[str]] = None
    # image_samples와 video_samples는 FormData로 받음


class AnalysisResponse(BaseModel):
    """분석 응답"""
    status: str
    message: str
    analysis: Optional[Dict[str, Any]] = None


async def analyze_instagram_platform(instagram_url: str, max_posts: int) -> Dict[str, Any]:
    """인스타그램 플랫폼 분석 (TODO: 실제 구현 필요)"""
    try:
        logger.info(f"인스타그램 분석 시작: {instagram_url}")
        # TODO: 인스타그램 크롤링 및 분석 구현
        # 현재는 더미 데이터 반환
        return {
            "url": instagram_url,
            "analyzed_posts": 0,
            "analysis": {
                "instagram": {
                    "caption_style": "짧고 임팩트 있는",
                    "image_style": "밝고 화사한",
                    "hashtag_pattern": "5-10개, 브랜드명 포함",
                    "color_palette": ["#FF6B6B", "#4ECDC4", "#45B7D1"]
                }
            }
        }
    except Exception as e:
        logger.error(f"인스타그램 분석 실패: {e}")
        return None


async def analyze_youtube_platform(youtube_url: str, max_videos: int) -> Dict[str, Any]:
    """유튜브 플랫폼 분석 (TODO: 실제 구현 필요)"""
    try:
        logger.info(f"유튜브 분석 시작: {youtube_url}")
        # TODO: 유튜브 API 연동 및 분석 구현
        # 현재는 더미 데이터 반환
        return {
            "url": youtube_url,
            "analyzed_videos": 0,
            "analysis": {
                "youtube": {
                    "content_style": "튜토리얼 중심",
                    "title_pattern": "숫자 활용, 질문형",
                    "description_style": "상세하고 구조적",
                    "thumbnail_style": "텍스트 오버레이, 밝은 배경"
                }
            }
        }
    except Exception as e:
        logger.error(f"유튜브 분석 실패: {e}")
        return None


async def multi_platform_analysis_background(
    user_id: int,
    instagram_url: Optional[str],
    youtube_url: Optional[str],
    threads_url: Optional[str],
    max_posts: int
):
    """
    백그라운드에서 멀티 플랫폼 분석 수행 (Multi-Agent Pipeline 사용)
    """
    logger.info(f"🚀 백그라운드 태스크 시작 - 사용자 ID: {user_id}")

    # 백그라운드 태스크용 새 DB 세션 생성
    try:
        db = SessionLocal()
        logger.info("✅ DB 세션 생성 성공")
    except Exception as e:
        logger.error(f"❌ DB 세션 생성 실패: {e}")
        return

    try:
        logger.info(f"사용자 {user_id}의 멀티 플랫폼 분석 시작")

        # 사용자 조회
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"사용자를 찾을 수 없습니다: {user_id}")
            return

        # BrandAnalysis 레코드 가져오기 또는 생성
        brand_analysis = db.query(BrandAnalysis).filter(BrandAnalysis.user_id == user_id).first()
        if not brand_analysis:
            brand_analysis = BrandAnalysis(user_id=user_id)
            db.add(brand_analysis)

        # 분석 시작 상태 설정
        brand_analysis.analysis_status = "analyzing"
        brand_analysis.analysis_error = None
        brand_analysis.analysis_progress = 5
        brand_analysis.analysis_step = "collecting"

        # 플랫폼 URL 구성
        platform_urls = {}
        if instagram_url:
            platform_urls['instagram'] = instagram_url
            brand_analysis.instagram_analysis_status = "analyzing"
            brand_analysis.instagram_url = instagram_url
        if youtube_url:
            platform_urls['youtube'] = youtube_url
            brand_analysis.youtube_analysis_status = "analyzing"
            brand_analysis.youtube_url = youtube_url
        if threads_url:
            platform_urls['threads'] = threads_url
            # Note: BrandAnalysis 모델에 threads_* 필드가 추가되면 여기에 매핑 추가 필요

        # Instagram Connection 자동 감지 (OAuth 연동 기반)
        instagram_connection = db.query(InstagramConnection).filter(
            InstagramConnection.user_id == user_id,
            InstagramConnection.is_active == True
        ).first()

        if instagram_connection:
            logger.info(f"✅ Instagram 계정 연동 확인됨: @{instagram_connection.instagram_username}")
            platform_urls['instagram'] = 'connected'  # OAuth 연동 표시
            brand_analysis.instagram_analysis_status = "analyzing"
            brand_analysis.instagram_url = f"https://instagram.com/{instagram_connection.instagram_username}"

        # YouTube Connection 자동 감지 (OAuth 연동 기반)
        youtube_connection = db.query(YouTubeConnection).filter(
            YouTubeConnection.user_id == user_id,
            YouTubeConnection.is_active == True
        ).first()

        if youtube_connection:
            logger.info(f"✅ YouTube 계정 연동 확인됨: {youtube_connection.channel_title}")
            platform_urls['youtube'] = 'connected'  # OAuth 연동 표시
            brand_analysis.youtube_analysis_status = "analyzing"
            brand_analysis.youtube_url = f"https://youtube.com/@{youtube_connection.channel_custom_url or youtube_connection.channel_id}"

        # Threads Connection 자동 감지 (OAuth 연동 기반)
        threads_connection = db.query(ThreadsConnection).filter(
            ThreadsConnection.user_id == user_id,
            ThreadsConnection.is_active == True
        ).first()

        if threads_connection:
            logger.info(f"✅ Threads 계정 연동 확인됨: @{threads_connection.username}")
            platform_urls['threads'] = 'connected'  # OAuth 연동 표시
            # Note: BrandAnalysis 모델에 threads_* 필드가 추가되면 여기에 매핑 추가 필요

        if not platform_urls:
            logger.error("분석할 플랫폼이 없습니다")
            return

        db.commit()

        # Progress: 플랫폼 연동 확인 완료 (20%)
        update_analysis_progress(db, user_id, 20, "collecting")

        # ===== Multi-Agent Pipeline 실행 =====
        pipeline = BrandAnalysisPipeline(db=db)

        # Progress: 분석 시작 (30%)
        update_analysis_progress(db, user_id, 30, "analyzing")

        brand_profile = await pipeline.run(
            user_id=user_id,  # int 타입으로 전달
            platform_urls=platform_urls,
            max_items=max_posts
        )

        # Progress: 분석 완료, 프로필 저장 중 (80%)
        update_analysis_progress(db, user_id, 80, "synthesizing")

        # ===== BrandProfile → BrandAnalysis 변환 =====
        # Overall 데이터
        brand_analysis.brand_name = brand_profile.identity.brand_name
        brand_analysis.business_type = brand_profile.identity.business_type
        brand_analysis.brand_tone = brand_profile.tone_of_voice.sentence_style
        brand_analysis.brand_values = brand_profile.identity.brand_values
        brand_analysis.target_audience = brand_profile.identity.target_audience
        brand_analysis.brand_personality = brand_profile.identity.brand_personality
        brand_analysis.key_themes = brand_profile.content_strategy.primary_topics
        brand_analysis.emotional_tone = brand_profile.identity.emotional_tone

        # Instagram 데이터
        if 'instagram' in brand_profile.analyzed_platforms:
            brand_analysis.instagram_caption_style = brand_profile.tone_of_voice.sentence_style
            brand_analysis.instagram_image_style = brand_profile.visual_style.image_style
            brand_analysis.instagram_hashtag_pattern = "분석됨"
            brand_analysis.instagram_color_palette = brand_profile.visual_style.color_palette
            brand_analysis.instagram_analyzed_posts = brand_profile.total_contents_analyzed
            brand_analysis.instagram_analyzed_at = datetime.utcnow()
            brand_analysis.instagram_analysis_status = "completed"

        # YouTube 데이터
        if 'youtube' in brand_profile.analyzed_platforms:
            brand_analysis.youtube_content_style = brand_profile.content_strategy.content_structure
            brand_analysis.youtube_title_pattern = "분석됨"
            brand_analysis.youtube_description_style = brand_profile.content_strategy.content_structure
            brand_analysis.youtube_thumbnail_style = brand_profile.visual_style.composition_style
            brand_analysis.youtube_analyzed_videos = brand_profile.total_contents_analyzed
            brand_analysis.youtube_analyzed_at = datetime.utcnow()
            brand_analysis.youtube_analysis_status = "completed"

        # ===== 통합 브랜드 프로필 저장 =====
        # mode="json"으로 datetime을 문자열로 변환하여 JSON 직렬화 가능하게 함
        brand_analysis.brand_profile_json = brand_profile.model_dump(mode="json")
        brand_analysis.profile_source = brand_profile.source
        brand_analysis.profile_confidence = brand_profile.confidence_level
        brand_analysis.profile_updated_at = datetime.utcnow()

        # 분석 완료 상태 설정
        brand_analysis.analysis_status = "completed"
        brand_analysis.analysis_error = None
        brand_analysis.analysis_progress = 100
        brand_analysis.analysis_step = "completed"

        db.commit()
        logger.info(f"사용자 {user_id}의 멀티 플랫폼 분석 완료")

    except Exception as e:
        logger.error(f"멀티 플랫폼 분석 중 오류: {e}")
        import traceback
        traceback.print_exc()
        try:
            brand_analysis = db.query(BrandAnalysis).filter(BrandAnalysis.user_id == user_id).first()
            if brand_analysis:
                # 전체 분석 상태를 실패로 설정
                brand_analysis.analysis_status = "failed"
                brand_analysis.analysis_error = str(e)[:500]  # 에러 메시지 저장 (최대 500자)

                if instagram_url:
                    brand_analysis.instagram_analysis_status = "failed"
                if youtube_url:
                    brand_analysis.youtube_analysis_status = "failed"
                if threads_url:
                    pass  # Note: BrandAnalysis 모델에 threads_* 필드가 추가되면 여기에 상태 업데이트 추가
                db.commit()
        except Exception as commit_error:
            logger.error(f"실패 상태 저장 중 오류: {commit_error}")
    finally:
        # DB 세션 닫기
        db.close()


@router.post("/multi-platform", response_model=AnalysisResponse)
async def analyze_multi_platform(
    request: MultiPlatformAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    멀티 플랫폼 브랜드 분석 시작 (비동기)

    - 인스타그램, 유튜브, Threads 중 제공된 플랫폼만 분석 (OAuth 연동 기반)
    - 백그라운드에서 처리되며, 완료 후 DB에 저장
    """
    try:
        # 최소 1개 플랫폼 URL 필요 (실제로는 OAuth 연동 확인)
        if not any([request.instagram_url, request.youtube_url, request.threads_url]):
            # OAuth 연동된 플랫폼이 있는지 확인
            pass  # OAuth 연동은 백그라운드 함수에서 자동 감지

        # BrandAnalysis 레코드 확인
        brand_analysis = db.query(BrandAnalysis).filter(BrandAnalysis.user_id == current_user.id).first()

        # 이미 분석 중인지 확인
        if brand_analysis:
            analyzing = (
                (request.instagram_url and brand_analysis.instagram_analysis_status == "analyzing") or
                (request.youtube_url and brand_analysis.youtube_analysis_status == "analyzing")
            )
            if analyzing:
                raise HTTPException(
                    status_code=400,
                    detail="이미 분석이 진행 중입니다. 잠시 후 다시 시도해주세요."
                )

        # 백그라운드 태스크로 분석 시작
        background_tasks.add_task(
            multi_platform_analysis_background,
            current_user.id,
            request.instagram_url,
            request.youtube_url,
            request.threads_url,
            request.max_posts
        )

        platforms = []
        if request.instagram_url:
            platforms.append("인스타그램")
        if request.youtube_url:
            platforms.append("유튜브")
        if request.threads_url:
            platforms.append("Threads")

        return AnalysisResponse(
            status="started",
            message=f"{', '.join(platforms)} 분석이 시작되었습니다. 잠시 후 결과를 확인해주세요."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"멀티 플랫폼 분석 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=f"분석을 시작할 수 없습니다: {str(e)}")


@router.get("/status", response_model=Dict[str, Any])
async def get_analysis_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    브랜드 분석 상태 조회

    Returns:
        각 플랫폼별 분석 상태 및 결과
    """
    brand_analysis = db.query(BrandAnalysis).filter(BrandAnalysis.user_id == current_user.id).first()

    if not brand_analysis:
        return {
            "analysis_status": "pending",
            "analysis_error": None,
            "overall": None,
            "blog": {"status": "pending", "url": None, "analyzed_at": None},
            "instagram": {"status": "pending", "url": None, "analyzed_at": None},
            "youtube": {"status": "pending", "url": None, "analyzed_at": None}
        }

    # Overall 데이터
    overall = None
    if brand_analysis.brand_tone:
        overall = {
            "brand_name": brand_analysis.brand_name,
            "business_type": brand_analysis.business_type,
            "brand_tone": brand_analysis.brand_tone,
            "brand_values": brand_analysis.brand_values,
            "target_audience": brand_analysis.target_audience,
            "brand_personality": brand_analysis.brand_personality,
            "key_themes": brand_analysis.key_themes,
            "emotional_tone": brand_analysis.emotional_tone
        }

    # 플랫폼별 상태
    blog_data = {
        "status": brand_analysis.blog_analysis_status,
        "url": brand_analysis.blog_url,
        "analyzed_at": brand_analysis.blog_analyzed_at.isoformat() if brand_analysis.blog_analyzed_at else None
    }
    if brand_analysis.blog_analysis_status == "completed":
        blog_data["analysis"] = {
            "writing_style": brand_analysis.blog_writing_style,
            "content_structure": brand_analysis.blog_content_structure,
            "call_to_action": brand_analysis.blog_call_to_action,
            "keyword_usage": brand_analysis.blog_keyword_usage
        }

    instagram_data = {
        "status": brand_analysis.instagram_analysis_status,
        "url": brand_analysis.instagram_url,
        "analyzed_at": brand_analysis.instagram_analyzed_at.isoformat() if brand_analysis.instagram_analyzed_at else None
    }
    if brand_analysis.instagram_analysis_status == "completed":
        instagram_data["analysis"] = {
            "caption_style": brand_analysis.instagram_caption_style,
            "image_style": brand_analysis.instagram_image_style,
            "hashtag_pattern": brand_analysis.instagram_hashtag_pattern,
            "color_palette": brand_analysis.instagram_color_palette
        }

    youtube_data = {
        "status": brand_analysis.youtube_analysis_status,
        "url": brand_analysis.youtube_url,
        "analyzed_at": brand_analysis.youtube_analyzed_at.isoformat() if brand_analysis.youtube_analyzed_at else None
    }
    if brand_analysis.youtube_analysis_status == "completed":
        youtube_data["analysis"] = {
            "content_style": brand_analysis.youtube_content_style,
            "title_pattern": brand_analysis.youtube_title_pattern,
            "description_style": brand_analysis.youtube_description_style,
            "thumbnail_style": brand_analysis.youtube_thumbnail_style
        }

    return {
        "analysis_status": brand_analysis.analysis_status or "pending",
        "analysis_progress": brand_analysis.analysis_progress or 0,
        "analysis_step": brand_analysis.analysis_step,
        "analysis_error": brand_analysis.analysis_error,
        "overall": overall,
        "blog": blog_data,
        "instagram": instagram_data,
        "youtube": youtube_data
    }


async def manual_content_analysis_background(
    user_id: int,
    text_samples: Optional[List[str]],
    image_urls: Optional[List[str]],  # Supabase Storage URL
    video_urls: Optional[List[str]],  # Supabase Storage URL
):
    """
    백그라운드에서 수동 콘텐츠 분석 수행 (Multi-Agent Pipeline 사용)

    주의: 백그라운드 태스크용 새 DB 세션 생성
    """
    logger.info(f"🚀 백그라운드 태스크 시작 - 사용자 ID: {user_id}")

    # 백그라운드 태스크용 새 DB 세션 생성
    try:
        db = SessionLocal()
        logger.info("✅ DB 세션 생성 성공")
    except Exception as e:
        logger.error(f"❌ DB 세션 생성 실패: {e}")
        return

    try:
        logger.info(f"사용자 {user_id}의 수동 콘텐츠 분석 시작 (Multi-Agent Pipeline)")

        # 사용자 조회
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"사용자를 찾을 수 없습니다: {user_id}")
            return

        # BrandAnalysis 레코드 가져오기 또는 생성
        brand_analysis = db.query(BrandAnalysis).filter(BrandAnalysis.user_id == user_id).first()
        if not brand_analysis:
            brand_analysis = BrandAnalysis(user_id=user_id)
            db.add(brand_analysis)

        # 분석 시작 상태 및 진행률 설정
        brand_analysis.analysis_status = "analyzing"
        brand_analysis.analysis_error = None
        brand_analysis.analysis_progress = 5
        brand_analysis.analysis_step = "collecting"
        db.commit()

        # Progress: 샘플 수집 완료 (20%)
        update_analysis_progress(db, user_id, 20, "collecting")

        # ===== Multi-Agent Pipeline 실행 =====
        pipeline = BrandAnalysisPipeline(db=db)

        # Progress: 분석 시작 (30%)
        update_analysis_progress(db, user_id, 30, "analyzing")
        brand_profile = await pipeline.run_from_manual_samples(
            user_id=str(user_id),  # str 타입으로 변환
            text_samples=text_samples,
            image_samples=image_urls,
            video_samples=video_urls
        )

        # Progress: 분석 완료, 프로필 저장 중 (80%)
        update_analysis_progress(db, user_id, 80, "synthesizing")

        # ===== BrandProfile → BrandAnalysis 매핑 (기존 컬럼 호환성) =====
        logger.info("BrandProfile → BrandAnalysis 매핑 중...")

        # Overall 필드
        brand_analysis.brand_name = brand_profile.identity.brand_name
        brand_analysis.business_type = brand_profile.identity.business_type
        brand_analysis.brand_personality = brand_profile.identity.brand_personality
        brand_analysis.brand_values = brand_profile.identity.brand_values
        brand_analysis.target_audience = brand_profile.identity.target_audience
        brand_analysis.emotional_tone = brand_profile.identity.emotional_tone
        brand_analysis.brand_tone = brand_profile.tone_of_voice.sentence_style
        brand_analysis.key_themes = brand_profile.content_strategy.primary_topics

        # Instagram 필드 (이미지 샘플 분석 결과)
        if image_urls:
            brand_analysis.instagram_caption_style = brand_profile.tone_of_voice.sentence_style
            brand_analysis.instagram_image_style = brand_profile.visual_style.image_style or "기본 스타일"
            brand_analysis.instagram_hashtag_pattern = "분석 기반 패턴"
            brand_analysis.instagram_color_palette = brand_profile.visual_style.color_palette
            brand_analysis.instagram_analyzed_posts = len(image_urls)
            brand_analysis.instagram_analyzed_at = datetime.utcnow()
            brand_analysis.instagram_analysis_status = "completed"

        # YouTube 필드 (영상 샘플 분석 결과)
        if video_urls:
            brand_analysis.youtube_content_style = brand_profile.content_strategy.content_structure
            brand_analysis.youtube_title_pattern = brand_profile.tone_of_voice.sentence_style
            brand_analysis.youtube_description_style = brand_profile.tone_of_voice.sentence_style
            brand_analysis.youtube_thumbnail_style = brand_profile.visual_style.image_style or "기본 스타일"
            brand_analysis.youtube_analyzed_videos = len(video_urls)
            brand_analysis.youtube_analyzed_at = datetime.utcnow()
            brand_analysis.youtube_analysis_status = "completed"

        # ===== 통합 브랜드 프로필 저장 =====
        # mode="json"으로 datetime을 문자열로 변환하여 JSON 직렬화 가능하게 함
        brand_analysis.brand_profile_json = brand_profile.model_dump(mode="json")
        brand_analysis.profile_source = brand_profile.source
        brand_analysis.profile_confidence = brand_profile.confidence_level
        brand_analysis.profile_updated_at = datetime.utcnow()

        # 분석 완료 상태 설정
        brand_analysis.analysis_status = "completed"
        brand_analysis.analysis_error = None
        brand_analysis.analysis_progress = 100
        brand_analysis.analysis_step = "completed"

        db.commit()
        logger.info(f"사용자 {user_id}의 수동 콘텐츠 분석 완료 (신뢰도: {brand_profile.confidence_level})")

        # BrandProfile JSON 로그 (디버깅용)
        logger.info(f"생성된 BrandProfile: {brand_profile.model_dump(mode='json')}")

    except Exception as e:
        logger.error(f"❌ 수동 콘텐츠 분석 중 오류: {e}")
        import traceback
        traceback.print_exc()

        # 에러 발생 시 분석 상태를 failed로 설정
        try:
            brand_analysis = db.query(BrandAnalysis).filter(BrandAnalysis.user_id == user_id).first()
            if brand_analysis:
                brand_analysis.analysis_status = "failed"
                brand_analysis.analysis_error = str(e)[:500]  # 에러 메시지 저장 (최대 500자)
                brand_analysis.analysis_step = "failed"
                db.commit()
                logger.info(f"❌ 분석 실패 상태 저장 완료: {user_id}")
        except Exception as commit_error:
            logger.error(f"❌ 실패 상태 저장 중 오류: {commit_error}")
    finally:
        # DB 세션 닫기
        db.close()
        logger.info("✅ DB 세션 닫기 완료")


@router.post("/manual", response_model=AnalysisResponse)
async def analyze_manual_content(
    background_tasks: BackgroundTasks,
    text_samples: Optional[str] = Form(None),  # JSON 문자열로 받음
    image_files: Optional[List[UploadFile]] = File(None),
    video_files: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    수동 콘텐츠 업로드 분석 시작 (비동기)

    - 텍스트, 이미지, 영상 샘플 중 최소 1개 타입에서 2개 이상 제공 필요
    - 파일을 Supabase Storage에 업로드 후 URL을 백그라운드 태스크에 전달
    - 백그라운드에서 처리되며, 완료 후 DB에 저장
    """
    try:
        import json

        # 텍스트 샘플 파싱
        text_list = None
        if text_samples:
            try:
                text_list = json.loads(text_samples)
            except:
                text_list = [text_samples]

        # 유효성 검사
        has_valid_text = text_list and len(text_list) >= 2
        has_valid_images = image_files and len(image_files) >= 2
        has_valid_videos = video_files and len(video_files) >= 2

        if not (has_valid_text or has_valid_images or has_valid_videos):
            raise HTTPException(
                status_code=400,
                detail="최소 1개 콘텐츠 타입에서 2개 이상의 샘플이 필요합니다."
            )

        # ===== Supabase Storage에 파일 업로드 =====
        image_urls = []
        video_urls = []

        try:
            storage = get_storage_service()
            bucket_name = "brand-samples"  # Supabase에 미리 생성 필요
            user_folder = f"user_{current_user.id}"
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

            # 이미지 파일 업로드
            if image_files:
                for idx, img in enumerate(image_files):
                    # 파일 확장자 추출
                    ext = img.filename.split('.')[-1] if '.' in img.filename else 'jpg'
                    file_path = f"{user_folder}/images/{timestamp}_{idx}.{ext}"

                    # 파일 데이터 읽기
                    file_data = await img.read()

                    # Content-Type 결정
                    content_type = img.content_type or f"image/{ext}"

                    # Supabase에 업로드
                    url = storage.upload_file(
                        bucket=bucket_name,
                        file_path=file_path,
                        file_data=file_data,
                        content_type=content_type
                    )
                    image_urls.append(url)
                    logger.info(f"✅ 이미지 업로드 완료: {url}")

            # 영상 파일 업로드
            if video_files:
                for idx, vid in enumerate(video_files):
                    # 파일 확장자 추출
                    ext = vid.filename.split('.')[-1] if '.' in vid.filename else 'mp4'
                    file_path = f"{user_folder}/videos/{timestamp}_{idx}.{ext}"

                    # 파일 데이터 읽기
                    file_data = await vid.read()

                    # Content-Type 결정
                    content_type = vid.content_type or f"video/{ext}"

                    # Supabase에 업로드
                    url = storage.upload_file(
                        bucket=bucket_name,
                        file_path=file_path,
                        file_data=file_data,
                        content_type=content_type
                    )
                    video_urls.append(url)
                    logger.info(f"✅ 영상 업로드 완료: {url}")

        except Exception as upload_error:
            logger.error(f"❌ 파일 업로드 실패: {upload_error}")
            raise HTTPException(
                status_code=500,
                detail=f"파일 업로드에 실패했습니다: {str(upload_error)}"
            )

        # 백그라운드 태스크로 분석 시작 (DB 세션 전달 안 함 - 백그라운드에서 새로 생성)
        background_tasks.add_task(
            manual_content_analysis_background,
            current_user.id,
            text_list,
            image_urls if image_urls else None,
            video_urls if video_urls else None,
        )

        content_types = []
        if has_valid_text:
            content_types.append("텍스트")
        if has_valid_images:
            content_types.append("이미지")
        if has_valid_videos:
            content_types.append("영상")

        return AnalysisResponse(
            status="started",
            message=f"{', '.join(content_types)} 샘플 분석이 시작되었습니다. 잠시 후 결과를 확인해주세요."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"수동 콘텐츠 분석 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=f"분석을 시작할 수 없습니다: {str(e)}")


@router.post("/create-basic-profile", response_model=AnalysisResponse)
async def create_basic_profile(
    request: BasicProfileRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    비즈니스 정보만으로 기본 BrandProfile 생성 (샘플 없음)

    - 사용자가 스타일/가치를 입력한 경우 샘플 없이도 브랜드 프로필 생성 가능
    - AI가 업종 특성 기반으로 브랜드 특성 추론
    - 신뢰도: LOW (추론 기반)
    """
    try:
        logger.info(f"사용자 {current_user.id}의 기본 브랜드 프로필 생성 시작")

        # BrandAnalysis 레코드 확인
        brand_analysis = db.query(BrandAnalysis).filter(BrandAnalysis.user_id == current_user.id).first()
        if not brand_analysis:
            brand_analysis = BrandAnalysis(user_id=current_user.id)
            db.add(brand_analysis)
            db.commit()

        # 백그라운드 태스크로 BrandProfile 생성
        background_tasks.add_task(
            create_basic_profile_background,
            current_user.id,
            request.brand_name,
            request.business_type,
            request.business_description,
            request.target_audience,
            request.selected_styles,
            request.brand_values,
            db
        )

        return AnalysisResponse(
            status="started",
            message="기본 브랜드 프로필 생성이 시작되었습니다. 잠시 후 결과를 확인해주세요."
        )

    except Exception as e:
        logger.error(f"기본 프로필 생성 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=f"기본 프로필 생성을 시작할 수 없습니다: {str(e)}")


async def create_basic_profile_background(
    user_id: int,
    brand_name: str,
    business_type: str,
    business_description: str,
    target_audience: str,
    selected_styles: Optional[List[str]],
    brand_values: Optional[List[str]],
    db: Session
):
    """
    백그라운드에서 기본 BrandProfile 생성
    """
    try:
        logger.info(f"사용자 {user_id}의 기본 BrandProfile 생성 중...")

        # BrandProfileSynthesizer 사용
        from ..brand_agents.synthesizer import BrandProfileSynthesizer

        synthesizer = BrandProfileSynthesizer()
        brand_profile = await synthesizer.synthesize_from_business_info(
            user_id=str(user_id),
            brand_name=brand_name,
            business_type=business_type,
            business_description=business_description,
            target_audience=target_audience,
            selected_styles=selected_styles,
            brand_values=brand_values
        )

        # BrandAnalysis 레코드 업데이트
        brand_analysis = db.query(BrandAnalysis).filter(BrandAnalysis.user_id == user_id).first()
        if brand_analysis:
            # BrandProfile → BrandAnalysis 매핑
            brand_analysis.brand_name = brand_profile.identity.brand_name
            brand_analysis.business_type = brand_profile.identity.business_type
            brand_analysis.brand_personality = brand_profile.identity.brand_personality
            brand_analysis.brand_values = brand_profile.identity.brand_values
            brand_analysis.target_audience = brand_profile.identity.target_audience
            brand_analysis.emotional_tone = brand_profile.identity.emotional_tone
            brand_analysis.brand_tone = brand_profile.tone_of_voice.sentence_style
            brand_analysis.key_themes = brand_profile.content_strategy.primary_topics

            # ===== 통합 브랜드 프로필 저장 =====
            # mode="json"으로 datetime을 문자열로 변환하여 JSON 직렬화 가능하게 함
            brand_analysis.brand_profile_json = brand_profile.model_dump(mode="json")
            brand_analysis.profile_source = brand_profile.source
            brand_analysis.profile_confidence = brand_profile.confidence_level
            brand_analysis.profile_updated_at = datetime.utcnow()

            db.commit()
            logger.info(f"사용자 {user_id}의 기본 BrandProfile 생성 완료 (신뢰도: {brand_profile.confidence_level})")

            # BrandProfile JSON 로그 (디버깅용)
            logger.info(f"생성된 BrandProfile: {brand_profile.model_dump(mode='json')}")

    except Exception as e:
        logger.error(f"기본 BrandProfile 생성 중 오류: {e}")
        import traceback
        traceback.print_exc()
