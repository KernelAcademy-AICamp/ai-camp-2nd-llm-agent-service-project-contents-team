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
from ..models import User, BrandAnalysis
from ..auth import get_current_user
from ..services.naver_blog_service import NaverBlogService
from ..services.brand_analyzer_service import BrandAnalyzerService

router = APIRouter(prefix="/api/brand-analysis", tags=["brand-analysis"])
logger = logging.getLogger(__name__)


class MultiPlatformAnalysisRequest(BaseModel):
    """멀티 플랫폼 분석 요청"""
    blog_url: Optional[str] = None
    instagram_url: Optional[str] = None
    youtube_url: Optional[str] = None
    max_posts: int = 10  # 각 플랫폼당 최대 포스트 수


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
    백그라운드에서 멀티 플랫폼 분석 수행
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

        # 분석할 플랫폼 확인
        platforms_to_analyze = []
        if blog_url:
            platforms_to_analyze.append(("blog", blog_url))
        if instagram_url:
            platforms_to_analyze.append(("instagram", instagram_url))
        if youtube_url:
            platforms_to_analyze.append(("youtube", youtube_url))

        if not platforms_to_analyze:
            logger.error("분석할 플랫폼이 없습니다")
            return

        # 상태 업데이트
        for platform, _ in platforms_to_analyze:
            if platform == "blog":
                brand_analysis.blog_analysis_status = "analyzing"
                brand_analysis.blog_url = blog_url
            elif platform == "instagram":
                brand_analysis.instagram_analysis_status = "analyzing"
                brand_analysis.instagram_url = instagram_url
            elif platform == "youtube":
                brand_analysis.youtube_analysis_status = "analyzing"
                brand_analysis.youtube_url = youtube_url
        db.commit()

        # 병렬로 플랫폼 분석 실행
        tasks = []
        if blog_url:
            tasks.append(analyze_blog_platform(blog_url, max_posts))
        if instagram_url:
            tasks.append(analyze_instagram_platform(instagram_url, max_posts))
        if youtube_url:
            tasks.append(analyze_youtube_platform(youtube_url, max_posts))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 처리
        overall_data = {
            "brand_name": None,
            "business_type": None,
            "brand_tone": None,
            "brand_values": None,
            "target_audience": None,
            "brand_personality": None,
            "key_themes": None,
            "emotional_tone": None
        }

        for i, (platform, url) in enumerate(platforms_to_analyze):
            result = results[i]

            if isinstance(result, Exception) or result is None:
                # 분석 실패
                if platform == "blog":
                    brand_analysis.blog_analysis_status = "failed"
                elif platform == "instagram":
                    brand_analysis.instagram_analysis_status = "failed"
                elif platform == "youtube":
                    brand_analysis.youtube_analysis_status = "failed"
                continue

            # 플랫폼별 데이터 저장
            if platform == "blog" and result.get("analysis"):
                analysis = result["analysis"]
                overall = analysis.get("overall", {})
                blog = analysis.get("blog", {})

                # Overall 데이터 (첫 번째 플랫폼 데이터 사용)
                if not overall_data["brand_tone"]:
                    overall_data["brand_name"] = overall.get("brand_name")
                    overall_data["business_type"] = overall.get("business_type")
                    overall_data["brand_tone"] = overall.get("brand_tone")
                    overall_data["brand_values"] = overall.get("brand_values")
                    overall_data["target_audience"] = overall.get("target_audience")
                    overall_data["brand_personality"] = overall.get("brand_personality")
                    overall_data["key_themes"] = overall.get("key_themes")
                    overall_data["emotional_tone"] = overall.get("emotional_tone")

                # Blog 데이터
                brand_analysis.blog_writing_style = blog.get("writing_style")
                brand_analysis.blog_content_structure = blog.get("content_structure")
                brand_analysis.blog_call_to_action = blog.get("call_to_action")
                brand_analysis.blog_keyword_usage = blog.get("keyword_usage")
                brand_analysis.blog_analyzed_posts = result.get("analyzed_posts", 0)
                brand_analysis.blog_analyzed_at = datetime.utcnow()
                brand_analysis.blog_analysis_status = "completed"

            elif platform == "instagram" and result.get("analysis"):
                instagram = result["analysis"].get("instagram", {})
                brand_analysis.instagram_caption_style = instagram.get("caption_style")
                brand_analysis.instagram_image_style = instagram.get("image_style")
                brand_analysis.instagram_hashtag_pattern = instagram.get("hashtag_pattern")
                brand_analysis.instagram_color_palette = instagram.get("color_palette")
                brand_analysis.instagram_analyzed_posts = result.get("analyzed_posts", 0)
                brand_analysis.instagram_analyzed_at = datetime.utcnow()
                brand_analysis.instagram_analysis_status = "completed"

            elif platform == "youtube" and result.get("analysis"):
                youtube = result["analysis"].get("youtube", {})
                brand_analysis.youtube_content_style = youtube.get("content_style")
                brand_analysis.youtube_title_pattern = youtube.get("title_pattern")
                brand_analysis.youtube_description_style = youtube.get("description_style")
                brand_analysis.youtube_thumbnail_style = youtube.get("thumbnail_style")
                brand_analysis.youtube_analyzed_videos = result.get("analyzed_videos", 0)
                brand_analysis.youtube_analyzed_at = datetime.utcnow()
                brand_analysis.youtube_analysis_status = "completed"

        # Overall 데이터 저장
        if overall_data["brand_tone"]:
            brand_analysis.brand_name = overall_data["brand_name"]
            brand_analysis.business_type = overall_data["business_type"]
            brand_analysis.brand_tone = overall_data["brand_tone"]
            brand_analysis.brand_values = overall_data["brand_values"]
            brand_analysis.target_audience = overall_data["target_audience"]
            brand_analysis.brand_personality = overall_data["brand_personality"]
            brand_analysis.key_themes = overall_data["key_themes"]
            brand_analysis.emotional_tone = overall_data["emotional_tone"]

        db.commit()
        logger.info(f"사용자 {user_id}의 멀티 플랫폼 분석 완료")

    except Exception as e:
        logger.error(f"멀티 플랫폼 분석 중 오류: {e}")
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
    백그라운드에서 수동 콘텐츠 분석 수행
    """
    try:
        logger.info(f"사용자 {user_id}의 수동 콘텐츠 분석 시작")

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

        # Gemini를 사용하여 샘플 분석
        analyzer = BrandAnalyzerService()

        # 텍스트 샘플 분석
        if text_samples and len(text_samples) >= 2:
            # 텍스트를 포스트 형태로 변환
            posts = [{"title": f"샘플 {i+1}", "content": sample, "date": "N/A"}
                     for i, sample in enumerate(text_samples)]

            business_info = {
                'brand_name': user.brand_name,
                'business_type': user.business_type,
                'business_description': user.business_description
            }

            text_analysis = await analyzer.analyze_brand(posts, business_info)

            # Overall 데이터 저장
            overall = text_analysis.get('overall', {})
            brand_analysis.brand_tone = overall.get('brand_tone')
            brand_analysis.brand_values = overall.get('brand_values')
            brand_analysis.target_audience = overall.get('target_audience')
            brand_analysis.brand_personality = overall.get('brand_personality')
            brand_analysis.key_themes = overall.get('key_themes')
            brand_analysis.emotional_tone = overall.get('emotional_tone')

            # Blog 데이터 저장 (수동 입력의 경우 blog 필드 활용)
            blog = text_analysis.get('blog', {})
            brand_analysis.blog_writing_style = blog.get('writing_style')
            brand_analysis.blog_content_structure = blog.get('content_structure')
            brand_analysis.blog_call_to_action = blog.get('call_to_action')
            brand_analysis.blog_keyword_usage = blog.get('keyword_usage')
            brand_analysis.blog_analyzed_posts = len(text_samples)
            brand_analysis.blog_analyzed_at = datetime.utcnow()
            brand_analysis.blog_analysis_status = "completed"

        # 이미지 샘플 분석 (AI 보완 분석)
        if image_samples and len(image_samples) >= 2:
            # TODO: 이미지 스타일 분석 구현
            # 현재는 기본값 설정
            brand_analysis.instagram_caption_style = "수동 입력 기반"
            brand_analysis.instagram_image_style = f"{len(image_samples)}개 샘플 기반 분석"
            brand_analysis.instagram_hashtag_pattern = "일반적인 패턴"
            brand_analysis.instagram_color_palette = ["#000000", "#FFFFFF"]
            brand_analysis.instagram_analyzed_posts = len(image_samples)
            brand_analysis.instagram_analyzed_at = datetime.utcnow()
            brand_analysis.instagram_analysis_status = "completed"

        # 영상 샘플 분석 (AI 보완 분석)
        if video_samples and len(video_samples) >= 2:
            # TODO: 영상 스타일 분석 구현
            # 현재는 기본값 설정
            brand_analysis.youtube_content_style = "수동 입력 기반"
            brand_analysis.youtube_title_pattern = f"{len(video_samples)}개 샘플 기반 분석"
            brand_analysis.youtube_description_style = "일반적인 스타일"
            brand_analysis.youtube_thumbnail_style = "기본 스타일"
            brand_analysis.youtube_analyzed_videos = len(video_samples)
            brand_analysis.youtube_analyzed_at = datetime.utcnow()
            brand_analysis.youtube_analysis_status = "completed"

        # AI 보완 분석: 데이터가 부족한 경우 Gemini로 보완
        if not brand_analysis.brand_tone:
            # Overall 데이터가 없는 경우 AI로 생성
            logger.info("Overall 데이터 부족 - AI 보완 분석 수행")

            # 비즈니스 정보 기반으로 AI 보완
            supplemental_prompt = f"""
다음 비즈니스 정보를 바탕으로 브랜드 특성을 추론해주세요:

- 브랜드명: {user.brand_name}
- 업종: {user.business_type}
- 설명: {user.business_description}

다음 정보를 JSON 형식으로 제공해주세요:
{{
  "brand_tone": "브랜드 톤앤매너",
  "brand_values": ["가치1", "가치2"],
  "target_audience": "타겟 고객층",
  "brand_personality": "브랜드 성격 설명",
  "key_themes": ["주제1", "주제2"],
  "emotional_tone": "감정적 톤"
}}
"""
            try:
                import google.generativeai as genai
                import json
                import os

                api_key = os.getenv("GEMINI_API_KEY")
                if api_key:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    response = model.generate_content(supplemental_prompt)
                    response_text = response.text.strip()

                    # JSON 파싱
                    if response_text.startswith('```json'):
                        response_text = response_text.replace('```json', '').replace('```', '').strip()

                    supplemental_data = json.loads(response_text)

                    brand_analysis.brand_tone = supplemental_data.get('brand_tone')
                    brand_analysis.brand_values = supplemental_data.get('brand_values')
                    brand_analysis.target_audience = supplemental_data.get('target_audience')
                    brand_analysis.brand_personality = supplemental_data.get('brand_personality')
                    brand_analysis.key_themes = supplemental_data.get('key_themes')
                    brand_analysis.emotional_tone = supplemental_data.get('emotional_tone')

                    logger.info("AI 보완 분석 완료")
            except Exception as e:
                logger.error(f"AI 보완 분석 실패: {e}")

        db.commit()
        logger.info(f"사용자 {user_id}의 수동 콘텐츠 분석 완료")

    except Exception as e:
        logger.error(f"수동 콘텐츠 분석 중 오류: {e}")


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
