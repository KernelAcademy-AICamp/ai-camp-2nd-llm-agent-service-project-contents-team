"""
블로그 분석 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from ..database import get_db
from ..models import User
from ..auth import get_current_user
from ..services.naver_blog_service import NaverBlogService
from ..services.brand_analyzer_service import BrandAnalyzerService

router = APIRouter(prefix="/api/blog", tags=["blog"])
logger = logging.getLogger(__name__)


class BlogAnalysisRequest(BaseModel):
    """블로그 분석 요청"""
    blog_url: str
    max_posts: int = 10  # 기본값: 최대 10개 포스트


class BlogAnalysisResponse(BaseModel):
    """블로그 분석 응답"""
    status: str
    message: str
    analysis: Optional[Dict[str, Any]] = None


async def analyze_blog_background(user_id: int, blog_url: str, max_posts: int, db: Session):
    """
    백그라운드에서 블로그 분석 수행
    """
    try:
        logger.info(f"사용자 {user_id}의 블로그 분석 시작: {blog_url}")

        # 사용자 조회
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"사용자를 찾을 수 없습니다: {user_id}")
            return

        # 분석 상태 업데이트
        user.blog_analysis_status = "analyzing"
        user.naver_blog_url = blog_url
        db.commit()

        # 1. 블로그 포스트 수집
        blog_service = NaverBlogService()
        posts = await blog_service.collect_blog_posts(blog_url, max_posts)

        if not posts:
            user.blog_analysis_status = "failed"
            db.commit()
            logger.error("수집된 포스트가 없습니다")
            return

        # 2. 브랜드 분석
        analyzer = BrandAnalyzerService()
        business_info = {
            'brand_name': user.brand_name,
            'business_type': user.business_type,
            'business_description': user.business_description
        }
        analysis_result = await analyzer.analyze_brand(posts, business_info)

        # 3. DB에 저장
        user.brand_analysis = analysis_result
        user.blog_analysis_status = "completed"
        user.blog_analyzed_at = datetime.utcnow()
        db.commit()

        logger.info(f"사용자 {user_id}의 블로그 분석 완료")

    except Exception as e:
        logger.error(f"블로그 분석 중 오류: {e}")
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.blog_analysis_status = "failed"
                db.commit()
        except:
            pass


@router.post("/analyze", response_model=BlogAnalysisResponse)
async def analyze_blog(
    request: BlogAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    네이버 블로그 분석 시작 (비동기)

    - 사용자의 블로그 URL을 입력받아 브랜드 분석 수행
    - 백그라운드에서 처리되며, 완료 후 DB에 저장
    """
    try:
        # 이미 분석 중인지 확인
        if current_user.blog_analysis_status == "analyzing":
            raise HTTPException(
                status_code=400,
                detail="이미 블로그 분석이 진행 중입니다. 잠시 후 다시 시도해주세요."
            )

        # 백그라운드 태스크로 분석 시작
        background_tasks.add_task(
            analyze_blog_background,
            current_user.id,
            request.blog_url,
            request.max_posts,
            db
        )

        return BlogAnalysisResponse(
            status="started",
            message="블로그 분석이 시작되었습니다. 잠시 후 결과를 확인해주세요."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"블로그 분석 시작 실패: {e}")
        raise HTTPException(status_code=500, detail=f"블로그 분석을 시작할 수 없습니다: {str(e)}")


@router.get("/analysis-status", response_model=Dict[str, Any])
async def get_analysis_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    블로그 분석 상태 조회

    Returns:
        - status: pending, analyzing, completed, failed
        - blog_url: 분석 중인 블로그 URL
        - analyzed_at: 마지막 분석 시간
        - analysis: 분석 결과 (completed 상태일 때만)
    """
    return {
        "status": current_user.blog_analysis_status,
        "blog_url": current_user.naver_blog_url,
        "analyzed_at": current_user.blog_analyzed_at.isoformat() if current_user.blog_analyzed_at else None,
        "analysis": current_user.brand_analysis if current_user.blog_analysis_status == "completed" else None
    }


@router.get("/brand-analysis", response_model=Dict[str, Any])
async def get_brand_analysis(
    current_user: User = Depends(get_current_user)
):
    """
    저장된 브랜드 분석 결과 조회

    Returns:
        브랜드 분석 결과 JSON
    """
    if not current_user.brand_analysis:
        raise HTTPException(
            status_code=404,
            detail="브랜드 분석 결과가 없습니다. 먼저 블로그 분석을 진행해주세요."
        )

    return current_user.brand_analysis


@router.delete("/brand-analysis")
async def delete_brand_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    브랜드 분석 결과 삭제 및 재분석 가능하도록 초기화
    """
    current_user.brand_analysis = None
    current_user.blog_analysis_status = "pending"
    current_user.blog_analyzed_at = None
    db.commit()

    return {"message": "브랜드 분석 결과가 삭제되었습니다."}
