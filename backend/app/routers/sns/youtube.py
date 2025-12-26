"""
YouTube API Router
- YouTube 채널 연동/해제
- 동영상 목록 조회/업로드
- 분석 데이터 조회
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
import tempfile

from ... import models, auth
from ...database import get_db
from ...oauth import oauth
from ...services.youtube_service import YouTubeService, sync_youtube_videos, parse_duration
from ...logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/youtube",
    tags=["youtube"]
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


# ===== Pydantic Schemas =====

class YouTubeConnectionResponse(BaseModel):
    id: int
    channel_id: str
    channel_title: Optional[str]
    channel_thumbnail_url: Optional[str]
    channel_custom_url: Optional[str]
    subscriber_count: Optional[int]
    video_count: Optional[int]
    view_count: Optional[int]
    is_active: bool
    last_synced_at: Optional[datetime]

    class Config:
        from_attributes = True


class YouTubeVideoResponse(BaseModel):
    id: int
    video_id: str
    title: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    published_at: Optional[datetime]
    duration: Optional[str]
    duration_seconds: Optional[int]
    privacy_status: Optional[str]
    view_count: int
    like_count: int
    comment_count: int
    tags: Optional[List[str]]

    class Config:
        from_attributes = True


class VideoUploadRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    tags: Optional[List[str]] = []
    category_id: Optional[str] = "22"  # People & Blogs
    privacy_status: Optional[str] = "private"


class VideoUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    privacy_status: Optional[str] = None


class AnalyticsRequest(BaseModel):
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    video_id: Optional[str] = None


# ===== OAuth 연동 엔드포인트 =====

@router.get('/connect')
async def youtube_connect(
    request: Request,
    user_id: int = None
):
    """YouTube 채널 연동 시작 (OAuth)"""
    redirect_uri = request.url_for('youtube_callback')
    # user_id를 state에 저장하여 콜백에서 사용
    if user_id:
        request.session['youtube_connect_user_id'] = user_id
        logger.info(f"Storing user_id in session: {user_id}")
    return await oauth.youtube.authorize_redirect(request, redirect_uri)


@router.get('/callback')
async def youtube_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """YouTube OAuth 콜백 처리"""
    logger.info(f"YouTube callback received: {request.url}")
    try:
        logger.info("Attempting to authorize access token...")
        token = await oauth.youtube.authorize_access_token(request)
        logger.info(f"Token received: {list(token.keys())}")

        # 세션에서 user_id 가져오기 (연동 시작 시 저장됨)
        user_id = request.session.get('youtube_connect_user_id')
        logger.info(f"User ID from session: {user_id}")

        if user_id:
            # 세션에 저장된 user_id로 사용자 찾기
            user = db.query(models.User).filter(
                models.User.id == user_id
            ).first()
            # 세션에서 제거
            request.session.pop('youtube_connect_user_id', None)
        else:
            # 세션에 user_id가 없으면 토큰의 이메일로 찾기 (fallback)
            user_info = token.get('userinfo')
            logger.info(f"User info from token: {user_info}")
            if user_info:
                user = db.query(models.User).filter(
                    models.User.email == user_info['email']
                ).first()
            else:
                user = None

        if not user:
            logger.error(f"User not found")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/settings?error=user_not_found"
            )

        logger.info(f"Found user: {user.id}")

        access_token = token['access_token']
        refresh_token = token.get('refresh_token')
        expires_in = token.get('expires_in', 3600)
        logger.info(f"Access token: {access_token[:20]}..., Refresh token: {refresh_token}")

        # YouTube 채널 정보 가져오기
        logger.info("Getting YouTube channel info...")
        youtube_service = YouTubeService(access_token, refresh_token)
        channel_info = await youtube_service.get_my_channel()
        logger.info(f"Channel info: {channel_info}")

        if not channel_info:
            logger.error("No YouTube channel found")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/settings?error=no_youtube_channel"
            )

        snippet = channel_info.get('snippet', {})
        statistics = channel_info.get('statistics', {})

        # 기존 연동 확인
        existing = db.query(models.YouTubeConnection).filter(
            models.YouTubeConnection.user_id == user.id
        ).first()

        if existing:
            # 업데이트
            existing.channel_id = channel_info['id']
            existing.channel_title = snippet.get('title')
            existing.channel_description = snippet.get('description')
            existing.channel_thumbnail_url = snippet.get('thumbnails', {}).get('high', {}).get('url')
            existing.channel_custom_url = snippet.get('customUrl')
            existing.subscriber_count = int(statistics.get('subscriberCount', 0))
            existing.video_count = int(statistics.get('videoCount', 0))
            existing.view_count = int(statistics.get('viewCount', 0))
            existing.access_token = access_token
            existing.refresh_token = refresh_token or existing.refresh_token
            existing.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            existing.is_active = True
        else:
            # 새로 생성
            connection = models.YouTubeConnection(
                user_id=user.id,
                channel_id=channel_info['id'],
                channel_title=snippet.get('title'),
                channel_description=snippet.get('description'),
                channel_thumbnail_url=snippet.get('thumbnails', {}).get('high', {}).get('url'),
                channel_custom_url=snippet.get('customUrl'),
                subscriber_count=int(statistics.get('subscriberCount', 0)),
                video_count=int(statistics.get('videoCount', 0)),
                view_count=int(statistics.get('viewCount', 0)),
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
                is_active=True
            )
            db.add(connection)

        db.commit()

        return RedirectResponse(
            url=f"{FRONTEND_URL}/youtube?connected=true"
        )

    except Exception as e:
        import traceback
        logger.error(f"YouTube OAuth error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/settings?error=youtube_oauth_failed"
        )


@router.delete('/disconnect')
async def youtube_disconnect(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """YouTube 채널 연동 해제"""
    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="YouTube connection not found")

    db.delete(connection)
    db.commit()

    return {"message": "YouTube channel disconnected successfully"}


# ===== 연동 상태 확인 =====

@router.get('/status', response_model=Optional[YouTubeConnectionResponse])
async def get_youtube_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """YouTube 연동 상태 확인"""
    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    return connection


@router.post('/refresh-channel')
async def refresh_channel_info(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """채널 정보 새로고침"""
    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="YouTube connection not found")

    service = YouTubeService(connection.access_token, connection.refresh_token)
    channel_info = await service.get_my_channel()

    if not channel_info:
        raise HTTPException(status_code=500, detail="Failed to fetch channel info")

    snippet = channel_info.get('snippet', {})
    statistics = channel_info.get('statistics', {})

    connection.channel_title = snippet.get('title')
    connection.channel_description = snippet.get('description')
    connection.channel_thumbnail_url = snippet.get('thumbnails', {}).get('high', {}).get('url')
    connection.channel_custom_url = snippet.get('customUrl')
    connection.subscriber_count = int(statistics.get('subscriberCount', 0))
    connection.video_count = int(statistics.get('videoCount', 0))
    connection.view_count = int(statistics.get('viewCount', 0))

    db.commit()
    db.refresh(connection)

    return connection


# ===== 동영상 관리 =====

@router.get('/videos', response_model=List[YouTubeVideoResponse])
async def get_youtube_videos(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """동영상 목록 조회 (DB에서)"""
    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="YouTube connection not found")

    videos = db.query(models.YouTubeVideo).filter(
        models.YouTubeVideo.connection_id == connection.id
    ).order_by(
        models.YouTubeVideo.published_at.desc()
    ).offset(skip).limit(limit).all()

    return videos


@router.post('/videos/sync')
async def sync_videos(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """YouTube 동영상 동기화"""
    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="YouTube connection not found")

    service = YouTubeService(connection.access_token, connection.refresh_token)

    # 동기화 실행
    synced_count = await sync_youtube_videos(db, connection, service)

    return {
        "message": "Videos synced successfully",
        "synced_count": synced_count
    }


@router.get('/videos/{video_id}')
async def get_video_detail(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """동영상 상세 정보 (DB + YouTube API)"""
    # DB에서 조회
    video = db.query(models.YouTubeVideo).filter(
        models.YouTubeVideo.video_id == video_id,
        models.YouTubeVideo.user_id == current_user.id
    ).first()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # YouTube API에서 최신 정보 가져오기
    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    if connection:
        service = YouTubeService(connection.access_token, connection.refresh_token)
        youtube_data = await service.get_video_by_id(video_id)

        if youtube_data:
            statistics = youtube_data.get('statistics', {})
            video.view_count = int(statistics.get('viewCount', 0))
            video.like_count = int(statistics.get('likeCount', 0))
            video.comment_count = int(statistics.get('commentCount', 0))
            video.last_stats_updated_at = datetime.utcnow()
            db.commit()
            db.refresh(video)

    return video


@router.post('/videos/upload')
async def upload_video(
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),  # 쉼표로 구분된 태그
    category_id: str = Form("22"),
    privacy_status: str = Form("private"),
    video_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """동영상 업로드"""
    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="YouTube connection not found")

    # 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        content = await video_file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        service = YouTubeService(connection.access_token, connection.refresh_token)

        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        result = await service.upload_video(
            video_file_path=tmp_path,
            title=title,
            description=description,
            tags=tag_list,
            category_id=category_id,
            privacy_status=privacy_status
        )

        if not result:
            raise HTTPException(status_code=500, detail="Video upload failed")

        # DB에 저장
        video_id = result["id"]
        snippet = result.get("snippet", {})

        new_video = models.YouTubeVideo(
            connection_id=connection.id,
            user_id=current_user.id,
            video_id=video_id,
            title=snippet.get("title", title),
            description=snippet.get("description", description),
            thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url"),
            privacy_status=privacy_status,
            tags=tag_list,
            category_id=category_id,
            published_at=datetime.utcnow()
        )
        db.add(new_video)
        db.commit()

        return {
            "message": "Video uploaded successfully",
            "video_id": video_id,
            "title": title
        }

    finally:
        # 임시 파일 삭제
        os.unlink(tmp_path)


class VideoUploadFromUrlRequest(BaseModel):
    video_url: str
    title: str
    description: str = ""
    tags: List[str] = []
    category_id: str = "22"  # People & Blogs
    privacy_status: str = "private"


@router.post('/videos/upload-from-url')
async def upload_video_from_url(
    request: VideoUploadFromUrlRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """URL에서 동영상 다운로드 후 YouTube에 업로드"""
    import httpx

    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="YouTube connection not found. Please connect your YouTube channel first.")

    # URL에서 동영상 다운로드
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.get(request.video_url)
            response.raise_for_status()
            video_content = response.content
    except Exception as e:
        logger.error(f"Failed to download video from URL: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to download video: {str(e)}")

    # 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_content)
        tmp_path = tmp.name

    try:
        service = YouTubeService(connection.access_token, connection.refresh_token)

        result = await service.upload_video(
            video_file_path=tmp_path,
            title=request.title,
            description=request.description,
            tags=request.tags,
            category_id=request.category_id,
            privacy_status=request.privacy_status
        )

        if not result:
            raise HTTPException(status_code=500, detail="Video upload to YouTube failed")

        # DB에 저장
        video_id = result["id"]
        snippet = result.get("snippet", {})

        new_video = models.YouTubeVideo(
            connection_id=connection.id,
            user_id=current_user.id,
            video_id=video_id,
            title=snippet.get("title", request.title),
            description=snippet.get("description", request.description),
            thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url"),
            privacy_status=request.privacy_status,
            tags=request.tags,
            category_id=request.category_id,
            published_at=datetime.utcnow()
        )
        db.add(new_video)
        db.commit()

        return {
            "message": "Video uploaded successfully",
            "video_id": video_id,
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "title": request.title
        }

    finally:
        # 임시 파일 삭제
        os.unlink(tmp_path)


@router.put('/videos/{video_id}')
async def update_video(
    video_id: str,
    request: VideoUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """동영상 정보 수정"""
    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="YouTube connection not found")

    service = YouTubeService(connection.access_token, connection.refresh_token)

    result = await service.update_video(
        video_id=video_id,
        title=request.title,
        description=request.description,
        tags=request.tags,
        privacy_status=request.privacy_status
    )

    if not result:
        raise HTTPException(status_code=500, detail="Video update failed")

    # DB 업데이트
    video = db.query(models.YouTubeVideo).filter(
        models.YouTubeVideo.video_id == video_id,
        models.YouTubeVideo.user_id == current_user.id
    ).first()

    if video:
        if request.title:
            video.title = request.title
        if request.description is not None:
            video.description = request.description
        if request.tags is not None:
            video.tags = request.tags
        if request.privacy_status:
            video.privacy_status = request.privacy_status
        db.commit()

    return {"message": "Video updated successfully"}


@router.delete('/videos/{video_id}')
async def delete_video(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """동영상 삭제"""
    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="YouTube connection not found")

    service = YouTubeService(connection.access_token, connection.refresh_token)

    success = await service.delete_video(video_id)

    if not success:
        raise HTTPException(status_code=500, detail="Video deletion failed")

    # DB에서도 삭제
    video = db.query(models.YouTubeVideo).filter(
        models.YouTubeVideo.video_id == video_id,
        models.YouTubeVideo.user_id == current_user.id
    ).first()

    if video:
        db.delete(video)
        db.commit()

    return {"message": "Video deleted successfully"}


# ===== 분석 데이터 =====

@router.get('/analytics/channel')
async def get_channel_analytics(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """채널 전체 분석 데이터"""
    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="YouTube connection not found")

    service = YouTubeService(connection.access_token, connection.refresh_token)

    analytics = await service.get_channel_analytics(start_date, end_date)

    if not analytics:
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")

    return analytics


@router.get('/analytics/video/{video_id}')
async def get_video_analytics(
    video_id: str,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """동영상별 분석 데이터"""
    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="YouTube connection not found")

    service = YouTubeService(connection.access_token, connection.refresh_token)

    analytics = await service.get_video_analytics(video_id, start_date, end_date)

    if not analytics:
        raise HTTPException(status_code=500, detail="Failed to fetch video analytics")

    return analytics


@router.get('/analytics/traffic')
async def get_traffic_sources(
    start_date: str,
    end_date: str,
    video_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """트래픽 소스 분석"""
    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="YouTube connection not found")

    service = YouTubeService(connection.access_token, connection.refresh_token)

    traffic = await service.get_traffic_sources(start_date, end_date, video_id)

    if not traffic:
        raise HTTPException(status_code=500, detail="Failed to fetch traffic data")

    return traffic


@router.get('/analytics/demographics')
async def get_demographics(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """시청자 인구통계"""
    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="YouTube connection not found")

    service = YouTubeService(connection.access_token, connection.refresh_token)

    demographics = await service.get_demographics(start_date, end_date)

    if not demographics:
        raise HTTPException(status_code=500, detail="Failed to fetch demographics")

    return demographics


@router.get('/analytics/top-videos')
async def get_top_videos(
    start_date: str,
    end_date: str,
    max_results: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """인기 동영상 순위"""
    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="YouTube connection not found")

    service = YouTubeService(connection.access_token, connection.refresh_token)

    top_videos = await service.get_top_videos(start_date, end_date, max_results)

    if not top_videos:
        raise HTTPException(status_code=500, detail="Failed to fetch top videos")

    return top_videos


@router.get('/analytics/summary')
async def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """분석 요약 (최근 30일)"""
    connection = db.query(models.YouTubeConnection).filter(
        models.YouTubeConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="YouTube connection not found")

    # 최근 30일
    end_date = datetime.utcnow().strftime("%Y-%m-%d")
    start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    service = YouTubeService(connection.access_token, connection.refresh_token)

    # 채널 분석
    channel_analytics = await service.get_channel_analytics(start_date, end_date)

    # 인기 동영상
    top_videos = await service.get_top_videos(start_date, end_date, 5)

    # 트래픽 소스
    traffic = await service.get_traffic_sources(start_date, end_date)

    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "channel": {
            "title": connection.channel_title,
            "thumbnail": connection.channel_thumbnail_url,
            "subscribers": connection.subscriber_count,
            "total_videos": connection.video_count,
            "total_views": connection.view_count
        },
        "analytics": channel_analytics,
        "top_videos": top_videos,
        "traffic_sources": traffic
    }
