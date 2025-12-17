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
from ..models import User, BrandAnalysis, YouTubeConnection
from ..auth import get_current_user
from ..services.naver_blog_service import NaverBlogService
from ..services.brand_analyzer_service import BrandAnalyzerService
from ..brand_agents import BrandAnalysisPipeline

router = APIRouter(prefix="/api/brand-analysis", tags=["brand-analysis"])
logger = logging.getLogger(__name__)


class MultiPlatformAnalysisRequest(BaseModel):
    """멀티 플랫폼 분석 요청"""
    blog_url: Optional[str] = None
    instagram_url: Optional[str] = None
    youtube_url: Optional[str] = None
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


async def analyze_blog_platform(blog_url: str, max_posts: int) -> Dict[str, Any]:
    """블로그 플랫폼 분석"""
    try:
        logger.info(f"블로그 분석 시작: {blog_url}")
        blog_service = NaverBlogService()
        posts = await blog_service.collect_blog_posts(blog_url, max_posts)

        if not posts:
            return None

        # 블로그 분석 (BrandAnalyzerService 사용)
        analyzer = BrandAnalyzerService()
        result = await analyzer.analyze_brand(posts, {})

        return {
            "url": blog_url,
            "analyzed_posts": len(posts),
            "analysis": result
        }
    except Exception as e:
        logger.error(f"블로그 분석 실패: {e}")
        return None


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
    blog_url: Optional[str],
    instagram_url: Optional[str],
    youtube_url: Optional[str],
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

        # 플랫폼 URL 구성
        platform_urls = {}
        if blog_url:
            platform_urls['blog'] = blog_url
            brand_analysis.blog_analysis_status = "analyzing"
            brand_analysis.blog_url = blog_url
        if instagram_url:
            platform_urls['instagram'] = instagram_url
            brand_analysis.instagram_analysis_status = "analyzing"
            brand_analysis.instagram_url = instagram_url
        if youtube_url:
            platform_urls['youtube'] = youtube_url
            brand_analysis.youtube_analysis_status = "analyzing"
            brand_analysis.youtube_url = youtube_url

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

        if not platform_urls:
            logger.error("분석할 플랫폼이 없습니다")
            return

        db.commit()

        # ===== Multi-Agent Pipeline 실행 =====
        pipeline = BrandAnalysisPipeline(db=db)
        brand_profile = await pipeline.run(
            user_id=user_id,  # int 타입으로 전달
            platform_urls=platform_urls,
            max_items=max_posts
        )

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

        # Blog 데이터 (blog 플랫폼이 분석되었으면)
        if 'naver_blog' in brand_profile.analyzed_platforms:
            brand_analysis.blog_writing_style = brand_profile.content_strategy.content_structure
            brand_analysis.blog_content_structure = brand_profile.content_strategy.content_structure
            brand_analysis.blog_call_to_action = brand_profile.content_strategy.call_to_action_style
            brand_analysis.blog_keyword_usage = brand_profile.content_strategy.keyword_usage
            brand_analysis.blog_analyzed_posts = brand_profile.total_contents_analyzed
            brand_analysis.blog_analyzed_at = datetime.utcnow()
            brand_analysis.blog_analysis_status = "completed"

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
        brand_analysis.brand_profile_json = brand_profile.dict()
        brand_analysis.profile_source = brand_profile.source
        brand_analysis.profile_confidence = brand_profile.confidence_level
        brand_analysis.profile_updated_at = datetime.utcnow()

        db.commit()
        logger.info(f"사용자 {user_id}의 멀티 플랫폼 분석 완료")

    except Exception as e:
        logger.error(f"멀티 플랫폼 분석 중 오류: {e}")
        import traceback
        traceback.print_exc()
        try:
            brand_analysis = db.query(BrandAnalysis).filter(BrandAnalysis.user_id == user_id).first()
            if brand_analysis:
                if blog_url:
                    brand_analysis.blog_analysis_status = "failed"
                if instagram_url:
                    brand_analysis.instagram_analysis_status = "failed"
                if youtube_url:
                    brand_analysis.youtube_analysis_status = "failed"
                db.commit()
        except:
            pass
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

    - 블로그, 인스타그램, 유튜브 중 제공된 플랫폼만 분석
    - 백그라운드에서 처리되며, 완료 후 DB에 저장
    """
    try:
        # 최소 1개 플랫폼 URL 필요
        if not any([request.blog_url, request.instagram_url, request.youtube_url]):
            raise HTTPException(
                status_code=400,
                detail="최소 1개 이상의 플랫폼 URL이 필요합니다."
            )

        # BrandAnalysis 레코드 확인
        brand_analysis = db.query(BrandAnalysis).filter(BrandAnalysis.user_id == current_user.id).first()

        # 이미 분석 중인지 확인
        if brand_analysis:
            analyzing = (
                (request.blog_url and brand_analysis.blog_analysis_status == "analyzing") or
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
            request.blog_url,
            request.instagram_url,
            request.youtube_url,
            request.max_posts
        )

        platforms = []
        if request.blog_url:
            platforms.append("블로그")
        if request.instagram_url:
            platforms.append("인스타그램")
        if request.youtube_url:
            platforms.append("유튜브")

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
        "overall": overall,
        "blog": blog_data,
        "instagram": instagram_data,
        "youtube": youtube_data
    }


async def manual_content_analysis_background(
    user_id: int,
    text_samples: Optional[List[str]],
    image_samples: Optional[List[str]],  # 저장된 파일 경로
    video_samples: Optional[List[str]],  # 저장된 파일 경로
    db: Session
):
    """
    백그라운드에서 수동 콘텐츠 분석 수행 (Multi-Agent Pipeline 사용)
    """
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
            db.commit()

        # ===== Multi-Agent Pipeline 실행 =====
        pipeline = BrandAnalysisPipeline(db=db)
        brand_profile = await pipeline.run_from_manual_samples(
            user_id=user_id,  # int 타입으로 전달
            text_samples=text_samples,
            image_samples=image_samples,
            video_samples=video_samples
        )

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

        # Blog 필드 (텍스트 샘플 분석 결과)
        if text_samples:
            brand_analysis.blog_writing_style = brand_profile.content_strategy.content_structure
            brand_analysis.blog_content_structure = brand_profile.tone_of_voice.sentence_style
            brand_analysis.blog_call_to_action = brand_profile.content_strategy.call_to_action_style
            brand_analysis.blog_keyword_usage = brand_profile.content_strategy.keyword_usage
            brand_analysis.blog_analyzed_posts = len(text_samples)
            brand_analysis.blog_analyzed_at = datetime.utcnow()
            brand_analysis.blog_analysis_status = "completed"

        # Instagram 필드 (이미지 샘플 분석 결과)
        if image_samples:
            brand_analysis.instagram_caption_style = brand_profile.tone_of_voice.sentence_style
            brand_analysis.instagram_image_style = brand_profile.visual_style.image_style or "기본 스타일"
            brand_analysis.instagram_hashtag_pattern = "분석 기반 패턴"
            brand_analysis.instagram_color_palette = brand_profile.visual_style.color_palette
            brand_analysis.instagram_analyzed_posts = len(image_samples)
            brand_analysis.instagram_analyzed_at = datetime.utcnow()
            brand_analysis.instagram_analysis_status = "completed"

        # YouTube 필드 (영상 샘플 분석 결과)
        if video_samples:
            brand_analysis.youtube_content_style = brand_profile.content_strategy.content_structure
            brand_analysis.youtube_title_pattern = brand_profile.tone_of_voice.sentence_style
            brand_analysis.youtube_description_style = brand_profile.tone_of_voice.sentence_style
            brand_analysis.youtube_thumbnail_style = brand_profile.visual_style.image_style or "기본 스타일"
            brand_analysis.youtube_analyzed_videos = len(video_samples)
            brand_analysis.youtube_analyzed_at = datetime.utcnow()
            brand_analysis.youtube_analysis_status = "completed"

        # ===== 통합 브랜드 프로필 저장 =====
        brand_analysis.brand_profile_json = brand_profile.dict()
        brand_analysis.profile_source = brand_profile.source
        brand_analysis.profile_confidence = brand_profile.confidence_level
        brand_analysis.profile_updated_at = datetime.utcnow()

        db.commit()
        logger.info(f"사용자 {user_id}의 수동 콘텐츠 분석 완료 (신뢰도: {brand_profile.confidence_level})")

        # BrandProfile JSON 로그 (디버깅용)
        logger.info(f"생성된 BrandProfile: {brand_profile.dict()}")

    except Exception as e:
        logger.error(f"수동 콘텐츠 분석 중 오류: {e}")
        import traceback
        traceback.print_exc()


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
    - 백그라운드에서 처리되며, 완료 후 DB에 저장
    - 샘플이 부족한 경우 AI 보완 분석 수행
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

        # 파일 저장 (TODO: 실제 저장 로직 구현)
        image_paths = []
        video_paths = []

        if image_files:
            for img in image_files:
                # TODO: 실제 파일 저장 로직
                image_paths.append(f"/tmp/{img.filename}")

        if video_files:
            for vid in video_files:
                # TODO: 실제 파일 저장 로직
                video_paths.append(f"/tmp/{vid.filename}")

        # 백그라운드 태스크로 분석 시작
        background_tasks.add_task(
            manual_content_analysis_background,
            current_user.id,
            text_list,
            image_paths if image_paths else None,
            video_paths if video_paths else None,
            db
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
            brand_analysis.brand_profile_json = brand_profile.dict()
            brand_analysis.profile_source = brand_profile.source
            brand_analysis.profile_confidence = brand_profile.confidence_level
            brand_analysis.profile_updated_at = datetime.utcnow()

            db.commit()
            logger.info(f"사용자 {user_id}의 기본 BrandProfile 생성 완료 (신뢰도: {brand_profile.confidence_level})")

            # BrandProfile JSON 로그 (디버깅용)
            logger.info(f"생성된 BrandProfile: {brand_profile.dict()}")

    except Exception as e:
        logger.error(f"기본 BrandProfile 생성 중 오류: {e}")
        import traceback
        traceback.print_exc()
