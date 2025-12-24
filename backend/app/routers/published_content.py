"""
발행 콘텐츠 API 라우터
- 임시저장, 예약발행, 즉시발행, 콘텐츠 관리
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, case, text
from typing import Optional, List
from datetime import datetime
import time
import logging
from pydantic import BaseModel
import os
import uuid
import base64
from google.cloud import storage
from supabase import create_client, Client

from ..database import get_db
from ..models import User, PublishedContent, ContentGenerationSession, GeneratedImage, XConnection, ThreadsConnection, InstagramConnection, FacebookConnection, YouTubeConnection, TikTokConnection, WordPressConnection
from ..auth import get_current_user
from ..schemas import (
    PublishedContentCreate,
    PublishedContentSchedule,
    PublishedContentUpdate,
    PublishedContentResponse,
    PublishedContentListResponse
)
from ..services.x_service import XService, XTokenExpiredError, XAPIError
from ..services.threads_service import ThreadsService
from ..services.instagram_service import InstagramService
from ..services.facebook_service import FacebookService
from ..services.youtube_service import YouTubeService

router = APIRouter(prefix="/api/published-contents", tags=["published-contents"])
logger = logging.getLogger(__name__)

# Google Cloud Storage 설정
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "contents-creator-uploads")
gcs_client = None
gcs_bucket = None

def init_gcs():
    """GCS 클라이언트 초기화 (GOOGLE_CREDENTIALS_BASE64 사용)"""
    global gcs_client, gcs_bucket
    if gcs_client is not None:
        return

    try:
        import base64
        import json
        from google.oauth2 import service_account

        creds_base64 = os.getenv("GOOGLE_CREDENTIALS_BASE64")
        if creds_base64:
            creds_json = base64.b64decode(creds_base64).decode('utf-8')
            creds_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            gcs_client = storage.Client(credentials=credentials, project=creds_dict.get('project_id'))
        else:
            # 기본 인증 (GOOGLE_APPLICATION_CREDENTIALS 환경변수 사용)
            gcs_client = storage.Client()

        gcs_bucket = gcs_client.bucket(GCS_BUCKET_NAME)
        logger.info(f"GCS initialized: bucket={GCS_BUCKET_NAME}")
    except Exception as e:
        logger.warning(f"Failed to initialize GCS: {e}")
        gcs_client = None
        gcs_bucket = None


# Supabase 설정 (카드뉴스 이미지 업로드용)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
_supabase_client: Client = None


def _get_supabase_client() -> Client:
    """Supabase 클라이언트 반환 (lazy initialization)"""
    global _supabase_client
    if _supabase_client is None:
        if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
            logger.info("Supabase client initialized for published_content")
        else:
            logger.warning("Supabase credentials not found")
    return _supabase_client


async def upload_cardnews_image_to_supabase(
    base64_data_url: str,
    user_id: int,
    session_id: int,
    page_number: int
) -> str:
    """
    Base64 이미지를 Supabase Storage에 업로드하고 공개 URL 반환
    """
    client = _get_supabase_client()
    if not client:
        raise Exception("Supabase client not initialized")

    # base64 데이터 추출
    if ',' in base64_data_url:
        header, data = base64_data_url.split(',', 1)
        # 이미지 타입 추출
        if 'png' in header:
            ext = 'png'
            content_type = 'image/png'
        elif 'gif' in header:
            ext = 'gif'
            content_type = 'image/gif'
        elif 'webp' in header:
            ext = 'webp'
            content_type = 'image/webp'
        else:
            ext = 'jpg'
            content_type = 'image/jpeg'
    else:
        data = base64_data_url
        ext = 'png'
        content_type = 'image/png'

    # base64 디코딩
    image_bytes = base64.b64decode(data)

    # 파일 경로 생성
    file_path = f"cardnews/{user_id}/{session_id}/page_{page_number}.{ext}"

    # Supabase Storage에 업로드
    bucket_name = "cardnews"

    try:
        # 기존 파일 삭제 시도 (있으면)
        try:
            client.storage.from_(bucket_name).remove([file_path])
        except Exception:
            pass  # 파일이 없으면 무시

        # 업로드
        client.storage.from_(bucket_name).upload(
            file_path,
            image_bytes,
            {"content-type": content_type}
        )

        # 공개 URL 생성
        public_url = client.storage.from_(bucket_name).get_public_url(file_path)

        logger.info(f"Image uploaded to Supabase: {public_url[:80]}...")
        return public_url

    except Exception as e:
        logger.error(f"Supabase upload failed: {e}")
        raise Exception(f"이미지 업로드 실패: {str(e)}")


@router.post("/draft", response_model=PublishedContentResponse)
async def save_draft(
    request: PublishedContentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    콘텐츠 임시저장 (작성 중)
    - id가 있으면 기존 콘텐츠 업데이트
    - id가 없으면 새로 생성
    """
    try:
        # 기존 콘텐츠가 있는지 확인 (id로 조회)
        existing = None
        if request.id:
            existing = db.query(PublishedContent).filter(
                PublishedContent.id == request.id,
                PublishedContent.user_id == current_user.id
            ).first()

        if existing:
            # 기존 콘텐츠 업데이트
            existing.title = request.title
            existing.content = request.content
            existing.tags = request.tags
            existing.image_ids = request.image_ids
            existing.uploaded_image_url = request.uploaded_image_url
            existing.card_image_urls = request.card_image_urls
            # session_id와 platform은 변경하지 않음

            db.commit()
            db.refresh(existing)

            logger.info(f"임시저장 업데이트: user_id={current_user.id}, id={existing.id}")
            return existing
        else:
            # 새로 생성
            published = PublishedContent(
                user_id=current_user.id,
                session_id=request.session_id,
                platform=request.platform,
                title=request.title,
                content=request.content,
                tags=request.tags,
                image_ids=request.image_ids,
                uploaded_image_url=request.uploaded_image_url,
                card_image_urls=request.card_image_urls,
                status="draft"
            )
            db.add(published)
            db.commit()
            db.refresh(published)

            logger.info(f"임시저장 생성: user_id={current_user.id}, id={published.id}")
            return published

    except Exception as e:
        db.rollback()
        logger.error(f"임시저장 실패: {e}")
        raise HTTPException(status_code=500, detail=f"임시저장에 실패했습니다: {str(e)}")


@router.post("/schedule", response_model=PublishedContentResponse)
async def schedule_publish(
    request: PublishedContentSchedule,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    콘텐츠 예약발행
    - id가 있으면 기존 콘텐츠 업데이트 후 예약
    - id가 없으면 새로 생성 후 예약
    """
    try:
        # 예약 시간 검증
        if request.scheduled_at <= datetime.now(request.scheduled_at.tzinfo):
            raise HTTPException(status_code=400, detail="예약 시간은 현재 시간 이후여야 합니다.")

        # 기존 콘텐츠가 있는지 확인
        existing = None
        if request.id:
            existing = db.query(PublishedContent).filter(
                PublishedContent.id == request.id,
                PublishedContent.user_id == current_user.id
            ).first()

        if existing:
            # 기존 콘텐츠 업데이트
            existing.title = request.title
            existing.content = request.content
            existing.tags = request.tags
            existing.image_ids = request.image_ids
            existing.uploaded_image_url = request.uploaded_image_url
            existing.card_image_urls = request.card_image_urls
            existing.status = "scheduled"
            existing.scheduled_at = request.scheduled_at

            db.commit()
            db.refresh(existing)

            logger.info(f"예약발행 업데이트: user_id={current_user.id}, id={existing.id}, scheduled_at={request.scheduled_at}")
            return existing
        else:
            # 새로 생성
            published = PublishedContent(
                user_id=current_user.id,
                session_id=request.session_id,
                platform=request.platform,
                title=request.title,
                content=request.content,
                tags=request.tags,
                image_ids=request.image_ids,
                uploaded_image_url=request.uploaded_image_url,
                card_image_urls=request.card_image_urls,
                status="scheduled",
                scheduled_at=request.scheduled_at
            )
            db.add(published)
            db.commit()
            db.refresh(published)

            logger.info(f"예약발행 생성: user_id={current_user.id}, id={published.id}, scheduled_at={request.scheduled_at}")
            return published

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"예약발행 실패: {e}")
        raise HTTPException(status_code=500, detail=f"예약발행 설정에 실패했습니다: {str(e)}")


@router.post("/publish/{content_id}", response_model=PublishedContentResponse)
async def publish_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    콘텐츠 즉시 발행
    - 실제 SNS API 연동하여 발행
    """
    published = db.query(PublishedContent).filter(
        PublishedContent.id == content_id,
        PublishedContent.user_id == current_user.id
    ).first()

    if not published:
        raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없습니다.")

    if published.status == "published":
        raise HTTPException(status_code=400, detail="이미 발행된 콘텐츠입니다.")

    try:
        publish_url = None
        platform_post_id = None

        # X(Twitter) 발행
        if published.platform == "x":
            publish_url, platform_post_id = await _publish_to_x(
                db, current_user, published.content, published.tags
            )

        # Threads 발행
        elif published.platform == "threads":
            publish_url, platform_post_id = await _publish_to_threads(
                db, current_user, published.content, published.tags
            )

        # Instagram 발행
        elif published.platform in ["sns", "instagram"]:
            # Instagram은 이미지가 필수
            # 우선순위: 1) 직접 업로드한 이미지, 2) 생성된 이미지
            image_url = published.uploaded_image_url
            if not image_url and published.image_ids and len(published.image_ids) > 0:
                image = db.query(GeneratedImage).filter(
                    GeneratedImage.id == published.image_ids[0]
                ).first()
                if image:
                    image_url = image.image_url

            publish_url, platform_post_id = await _publish_to_instagram(
                db, current_user, published.content, published.tags, image_url
            )

        # Facebook 발행
        elif published.platform == "facebook":
            # 이미지가 있으면 사진 게시물, 없으면 텍스트 게시물
            image_url = published.uploaded_image_url
            if not image_url and published.image_ids and len(published.image_ids) > 0:
                image = db.query(GeneratedImage).filter(
                    GeneratedImage.id == published.image_ids[0]
                ).first()
                if image:
                    image_url = image.image_url

            publish_url, platform_post_id = await _publish_to_facebook(
                db, current_user, published.content, published.tags, image_url
            )

        # YouTube 발행
        elif published.platform == "youtube":
            # YouTube는 동영상 파일이 필수 - 현재는 video_file_path 지원 안 함
            # TODO: GeneratedVideo 테이블에서 동영상 경로 가져오기
            raise HTTPException(
                status_code=400,
                detail="YouTube 발행은 동영상 파일이 필요합니다. 현재 이 기능은 개발 중입니다."
            )

        # TikTok 발행
        elif published.platform == "tiktok":
            # TikTok은 동영상 URL이 필수
            # TODO: GeneratedVideo 테이블에서 동영상 URL 가져오기
            raise HTTPException(
                status_code=400,
                detail="TikTok 발행은 동영상 URL이 필요합니다. 현재 이 기능은 개발 중입니다."
            )

        # WordPress 발행
        elif published.platform == "wordpress":
            publish_url, platform_post_id = await _publish_to_wordpress(
                db, current_user, published.title, published.content, published.tags
            )

        # 지원하지 않는 플랫폼
        else:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 플랫폼입니다: {published.platform}"
            )

        # 발행 성공 - 상태 업데이트
        published.status = "published"
        published.published_at = datetime.utcnow()
        if publish_url:
            published.publish_url = publish_url
        if platform_post_id:
            published.platform_post_id = platform_post_id

        db.commit()
        db.refresh(published)

        logger.info(f"콘텐츠 발행 완료: user_id={current_user.id}, id={content_id}, platform={published.platform}")
        return published

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        published.status = "failed"
        published.publish_error = str(e)
        db.commit()
        logger.error(f"콘텐츠 발행 실패: {e}")
        raise HTTPException(status_code=500, detail=f"발행에 실패했습니다: {str(e)}")


async def _publish_to_x(db: Session, user: User, content: str, tags: list = None) -> tuple:
    """
    X(Twitter)에 콘텐츠 발행
    Returns: (publish_url, post_id)
    """
    # X 연동 확인
    connection = db.query(XConnection).filter(
        XConnection.user_id == user.id,
        XConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(
            status_code=400,
            detail="X 계정이 연동되어 있지 않습니다. 설정에서 X 계정을 연동해주세요."
        )

    logger.info(f"X 발행 시작: user_id={user.id}, username=@{connection.username}")

    # 텍스트 준비 (태그 포함)
    tweet_text = content
    if tags and len(tags) > 0:
        hashtags = " ".join([f"#{tag}" if not tag.startswith("#") else tag for tag in tags])
        # 280자 제한 확인
        if len(tweet_text) + len(hashtags) + 1 <= 280:
            tweet_text = f"{tweet_text}\n{hashtags}"
        elif len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."

    # 텍스트 길이 검증
    if len(tweet_text) > 280:
        tweet_text = tweet_text[:277] + "..."

    logger.info(f"트윗 텍스트 준비 완료: {len(tweet_text)}자")

    try:
        service = XService(connection.access_token, connection.refresh_token)
        result = await service.create_tweet(tweet_text)

        if not result:
            logger.error(f"X 발행 실패: create_tweet returned None")
            raise HTTPException(status_code=500, detail="X 발행에 실패했습니다. X API 응답이 없습니다.")

        post_id = result.get("id")
        username = connection.username
        publish_url = f"https://x.com/{username}/status/{post_id}" if username and post_id else None

        logger.info(f"X 발행 성공: user_id={user.id}, post_id={post_id}, url={publish_url}")
        return publish_url, post_id

    except XTokenExpiredError:
        # 토큰 만료 - 연동 해제
        logger.warning(f"X 토큰 만료: user_id={user.id}")
        connection.is_active = False
        db.commit()
        raise HTTPException(
            status_code=401,
            detail="X 토큰이 만료되었습니다. 설정에서 X 계정을 다시 연동해주세요."
        )
    except XAPIError as e:
        logger.error(f"X API 에러: {e.status_code} - {e.response_text}")
        # 403: 권한 없음 (Free tier 제한 등)
        if e.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail="X 발행 권한이 없습니다. X API 접근 권한을 확인해주세요. (Free tier는 쓰기 권한이 제한될 수 있습니다)"
            )
        raise HTTPException(status_code=500, detail=f"X 발행 실패: {e.message}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"X 발행 중 예외 발생: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"X 발행 중 오류가 발생했습니다: {str(e)}")


async def _publish_to_threads(db: Session, user: User, content: str, tags: list = None) -> tuple:
    """
    Threads에 콘텐츠 발행
    Returns: (publish_url, post_id)
    """
    # Threads 연동 확인
    connection = db.query(ThreadsConnection).filter(
        ThreadsConnection.user_id == user.id,
        ThreadsConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(
            status_code=400,
            detail="Threads 계정이 연동되어 있지 않습니다. 설정에서 Threads 계정을 연동해주세요."
        )

    logger.info(f"Threads 발행 시작: user_id={user.id}, username=@{connection.username}")

    # 텍스트 준비 (태그 포함) - Threads는 500자 제한
    post_text = content
    if tags and len(tags) > 0:
        hashtags = " ".join([f"#{tag}" if not tag.startswith("#") else tag for tag in tags])
        if len(post_text) + len(hashtags) + 1 <= 500:
            post_text = f"{post_text}\n\n{hashtags}"

    if len(post_text) > 500:
        post_text = post_text[:497] + "..."

    logger.info(f"Threads 텍스트 준비 완료: {len(post_text)}자")

    try:
        service = ThreadsService(connection.access_token, connection.threads_user_id)
        result = await service.create_and_publish_thread(
            user_id=connection.threads_user_id,
            text=post_text
        )

        if not result:
            logger.error("Threads 발행 실패: create_and_publish_thread returned None")
            raise HTTPException(status_code=500, detail="Threads 발행에 실패했습니다.")

        post_id = result.get("id")
        username = connection.username
        publish_url = f"https://www.threads.net/@{username}/post/{post_id}" if username and post_id else None

        logger.info(f"Threads 발행 성공: user_id={user.id}, post_id={post_id}")
        return publish_url, post_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Threads 발행 중 예외 발생: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Threads 발행 중 오류가 발생했습니다: {str(e)}")


async def _publish_to_instagram(db: Session, user: User, content: str, tags: list = None, image_url: str = None) -> tuple:
    """
    Instagram에 콘텐츠 발행
    Returns: (publish_url, post_id)
    """
    # Instagram 연동 확인
    connection = db.query(InstagramConnection).filter(
        InstagramConnection.user_id == user.id,
        InstagramConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(
            status_code=400,
            detail="Instagram 계정이 연동되어 있지 않습니다. 설정에서 Instagram 계정을 연동해주세요."
        )

    # Instagram은 이미지가 필수
    if not image_url:
        raise HTTPException(
            status_code=400,
            detail="Instagram 발행에는 이미지가 필요합니다. 이미지를 추가해주세요."
        )

    logger.info(f"Instagram 발행 시작: user_id={user.id}, username=@{connection.instagram_username}")

    # 캡션 준비 (태그 포함) - Instagram은 2200자 제한
    caption = content
    if tags and len(tags) > 0:
        hashtags = " ".join([f"#{tag}" if not tag.startswith("#") else tag for tag in tags])
        if len(caption) + len(hashtags) + 2 <= 2200:
            caption = f"{caption}\n\n{hashtags}"

    if len(caption) > 2200:
        caption = caption[:2197] + "..."

    logger.info(f"Instagram 캡션 준비 완료: {len(caption)}자")

    try:
        service = InstagramService(connection.page_access_token)

        # 1. 미디어 컨테이너 생성
        container = await service.create_media_container(
            instagram_user_id=connection.instagram_account_id,
            image_url=image_url,
            caption=caption
        )

        if not container or "id" not in container:
            logger.error("Instagram 컨테이너 생성 실패")
            raise HTTPException(status_code=500, detail="Instagram 미디어 컨테이너 생성에 실패했습니다.")

        creation_id = container["id"]
        logger.info(f"Instagram 컨테이너 생성됨: {creation_id}")

        # 2. 미디어 발행
        result = await service.publish_media(
            instagram_user_id=connection.instagram_account_id,
            creation_id=creation_id
        )

        await service.close()

        if not result or "id" not in result:
            logger.error("Instagram 발행 실패")
            raise HTTPException(status_code=500, detail="Instagram 발행에 실패했습니다.")

        post_id = result.get("id")
        username = connection.instagram_username
        publish_url = f"https://www.instagram.com/p/{post_id}/" if post_id else None

        logger.info(f"Instagram 발행 성공: user_id={user.id}, post_id={post_id}")
        return publish_url, post_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Instagram 발행 중 예외 발생: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Instagram 발행 중 오류가 발생했습니다: {str(e)}")


async def _publish_to_facebook(db: Session, user: User, content: str, tags: list = None, image_url: str = None) -> tuple:
    """
    Facebook 페이지에 콘텐츠 발행
    Returns: (publish_url, post_id)
    """
    # Facebook 연동 확인
    connection = db.query(FacebookConnection).filter(
        FacebookConnection.user_id == user.id,
        FacebookConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(
            status_code=400,
            detail="Facebook 페이지가 연동되어 있지 않습니다. 설정에서 Facebook 페이지를 연동해주세요."
        )

    if not connection.page_id or not connection.page_access_token:
        raise HTTPException(
            status_code=400,
            detail="Facebook 페이지가 선택되어 있지 않습니다. 설정에서 페이지를 선택해주세요."
        )

    logger.info(f"Facebook 발행 시작: user_id={user.id}, page={connection.page_name}")

    # 메시지 준비 (태그 포함)
    message = content
    if tags and len(tags) > 0:
        hashtags = " ".join([f"#{tag}" if not tag.startswith("#") else tag for tag in tags])
        message = f"{message}\n\n{hashtags}"

    logger.info(f"Facebook 메시지 준비 완료: {len(message)}자")

    try:
        service = FacebookService(connection.user_access_token, connection.page_access_token)

        if image_url:
            # 사진 게시물
            result = await service.create_photo_post(
                page_id=connection.page_id,
                photo_url=image_url,
                caption=message
            )
        else:
            # 텍스트 게시물
            result = await service.create_post(
                page_id=connection.page_id,
                message=message
            )

        await service.close()

        if not result or "id" not in result:
            logger.error("Facebook 발행 실패: API 응답 없음")
            raise HTTPException(status_code=500, detail="Facebook 발행에 실패했습니다.")

        post_id = result.get("id")
        # Facebook 게시물 URL 형식: https://www.facebook.com/{page_id}/posts/{post_id}
        # post_id는 보통 "{page_id}_{actual_post_id}" 형식
        actual_post_id = post_id.split("_")[-1] if "_" in post_id else post_id
        publish_url = f"https://www.facebook.com/{connection.page_id}/posts/{actual_post_id}"

        logger.info(f"Facebook 발행 성공: user_id={user.id}, post_id={post_id}")
        return publish_url, post_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Facebook 발행 중 예외 발생: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Facebook 발행 중 오류가 발생했습니다: {str(e)}")


async def _publish_to_youtube(db: Session, user: User, title: str, content: str, tags: list = None, video_file_path: str = None) -> tuple:
    """
    YouTube에 동영상 업로드
    Returns: (publish_url, video_id)
    Note: YouTube는 동영상 파일이 필수입니다.
    """
    # YouTube 연동 확인
    connection = db.query(YouTubeConnection).filter(
        YouTubeConnection.user_id == user.id,
        YouTubeConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(
            status_code=400,
            detail="YouTube 계정이 연동되어 있지 않습니다. 설정에서 YouTube 계정을 연동해주세요."
        )

    if not video_file_path:
        raise HTTPException(
            status_code=400,
            detail="YouTube 발행에는 동영상 파일이 필요합니다."
        )

    logger.info(f"YouTube 발행 시작: user_id={user.id}, channel={connection.channel_title}")

    try:
        service = YouTubeService(connection.access_token, connection.refresh_token)

        result = await service.upload_video(
            video_file_path=video_file_path,
            title=title or "Untitled Video",
            description=content or "",
            tags=tags or [],
            privacy_status="public"
        )

        if not result or "id" not in result:
            logger.error("YouTube 업로드 실패: API 응답 없음")
            raise HTTPException(status_code=500, detail="YouTube 업로드에 실패했습니다.")

        video_id = result.get("id")
        publish_url = f"https://www.youtube.com/watch?v={video_id}"

        logger.info(f"YouTube 발행 성공: user_id={user.id}, video_id={video_id}")
        return publish_url, video_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"YouTube 발행 중 예외 발생: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"YouTube 발행 중 오류가 발생했습니다: {str(e)}")


async def _publish_to_tiktok(db: Session, user: User, title: str, content: str, video_url: str = None) -> tuple:
    """
    TikTok에 동영상 업로드
    Returns: (publish_url, publish_id)
    Note: TikTok은 동영상 URL이 필수입니다.
    """
    import httpx

    # TikTok 연동 확인
    connection = db.query(TikTokConnection).filter(
        TikTokConnection.user_id == user.id,
        TikTokConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(
            status_code=400,
            detail="TikTok 계정이 연동되어 있지 않습니다. 설정에서 TikTok 계정을 연동해주세요."
        )

    if not video_url:
        raise HTTPException(
            status_code=400,
            detail="TikTok 발행에는 동영상 URL이 필요합니다."
        )

    logger.info(f"TikTok 발행 시작: user_id={user.id}, username={connection.username}")

    try:
        TIKTOK_VIDEO_UPLOAD_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                TIKTOK_VIDEO_UPLOAD_URL,
                json={
                    "post_info": {
                        "title": title or "",
                        "privacy_level": "PUBLIC_TO_EVERYONE",
                        "disable_duet": False,
                        "disable_comment": False,
                        "disable_stitch": False
                    },
                    "source_info": {
                        "source": "PULL_FROM_URL",
                        "video_url": video_url
                    }
                },
                headers={
                    "Authorization": f"Bearer {connection.access_token}",
                    "Content-Type": "application/json"
                }
            )

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("error", {}).get("message", "Upload failed")
            logger.error(f"TikTok 발행 실패: {error_msg}")
            raise HTTPException(status_code=response.status_code, detail=f"TikTok 발행 실패: {error_msg}")

        result = response.json()
        publish_id = result.get("data", {}).get("publish_id")
        # TikTok은 업로드 후 처리 시간이 필요하여 즉시 URL을 알 수 없음
        publish_url = connection.profile_deep_link or f"https://www.tiktok.com/@{connection.username}"

        logger.info(f"TikTok 발행 성공: user_id={user.id}, publish_id={publish_id}")
        return publish_url, publish_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TikTok 발행 중 예외 발생: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"TikTok 발행 중 오류가 발생했습니다: {str(e)}")


async def _publish_to_wordpress(db: Session, user: User, title: str, content: str, tags: list = None, status: str = "publish") -> tuple:
    """
    WordPress에 게시물 발행
    Returns: (publish_url, post_id)
    """
    import httpx
    import base64

    # WordPress 연동 확인
    connection = db.query(WordPressConnection).filter(
        WordPressConnection.user_id == user.id,
        WordPressConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(
            status_code=400,
            detail="WordPress 사이트가 연동되어 있지 않습니다. 설정에서 WordPress 사이트를 연동해주세요."
        )

    if not connection.wp_app_password:
        raise HTTPException(
            status_code=400,
            detail="WordPress Application Password가 설정되어 있지 않습니다."
        )

    logger.info(f"WordPress 발행 시작: user_id={user.id}, site={connection.site_name}")

    # Basic Auth 헤더 생성
    credentials = f"{connection.wp_username}:{connection.wp_app_password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    auth_header = f"Basic {encoded}"

    # 게시물 데이터 준비
    post_payload = {
        "title": title or "Untitled Post",
        "content": content or "",
        "status": status  # publish, draft, pending, private
    }

    # 태그가 있으면 문자열로 변환해서 콘텐츠에 추가 (WordPress 태그는 ID 기반이므로)
    if tags and len(tags) > 0:
        hashtags = " ".join([f"#{tag}" if not tag.startswith("#") else tag for tag in tags])
        post_payload["content"] = f"{content}\n\n{hashtags}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{connection.site_url}/wp-json/wp/v2/posts",
                json=post_payload,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json"
                }
            )

        if response.status_code not in [200, 201]:
            error_detail = response.json() if response.content else "Unknown error"
            logger.error(f"WordPress 발행 실패: {error_detail}")
            raise HTTPException(status_code=response.status_code, detail=f"WordPress 발행 실패: {error_detail}")

        created_post = response.json()
        post_id = created_post.get("id")
        publish_url = created_post.get("link")

        logger.info(f"WordPress 발행 성공: user_id={user.id}, post_id={post_id}, url={publish_url}")
        return publish_url, str(post_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WordPress 발행 중 예외 발생: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"WordPress 발행 중 오류가 발생했습니다: {str(e)}")


@router.get("", response_model=List[PublishedContentListResponse])
async def list_published_contents(
    status: Optional[str] = Query(None, description="필터: draft, scheduled, published, failed"),
    platform: Optional[str] = Query(None, description="플랫폼 필터: blog, sns, x, threads"),
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    발행 콘텐츠 목록 조회 (콘텐츠 관리 페이지용)
    - 상태별, 플랫폼별 필터링 지원
    - 최적화: Raw SQL로 필요한 컬럼만 조회 (대용량 JSON/TEXT 제외)
    """
    start_time = time.perf_counter()

    # Raw SQL로 최적화된 쿼리 실행
    # card_image_urls는 제외하고, content는 SUBSTRING으로 300자만
    sql = """
        SELECT
            id, platform, title,
            SUBSTRING(content, 1, 300) as content,
            status, scheduled_at, published_at, views, created_at
        FROM published_contents
        WHERE user_id = :user_id
    """
    params = {"user_id": current_user.id, "skip": skip, "limit": limit}

    if status:
        sql += " AND status = :status"
        params["status"] = status

    if platform:
        sql += " AND platform = :platform"
        params["platform"] = platform

    sql += " ORDER BY created_at DESC OFFSET :skip LIMIT :limit"

    result = db.execute(text(sql), params)
    rows = result.fetchall()

    elapsed = time.perf_counter() - start_time
    logger.info(f"published_contents 목록 조회: {len(rows)}건, {elapsed:.3f}초")

    if not rows:
        return []

    # Row 객체를 dict로 변환 (card_image_urls는 목록에서 불필요하므로 null 처리)
    contents = [
        {
            "id": r.id,
            "platform": r.platform,
            "title": r.title,
            "content": r.content or "",
            "card_image_urls": None,  # 목록에서는 이미지 URL 불필요
            "status": r.status,
            "scheduled_at": r.scheduled_at,
            "published_at": r.published_at,
            "views": r.views,
            "created_at": r.created_at
        }
        for r in rows
    ]

    return contents


@router.get("/stats")
async def get_content_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    콘텐츠 상태별 통계 (콘텐츠 관리 페이지 탭 카운트용)
    - 최적화: 4개의 COUNT 쿼리를 1개의 조건부 COUNT로 통합
    """
    # 단일 쿼리로 모든 상태별 카운트 조회
    result = db.query(
        func.count(PublishedContent.id).label('total'),
        func.sum(case((PublishedContent.status == "draft", 1), else_=0)).label('draft'),
        func.sum(case((PublishedContent.status == "scheduled", 1), else_=0)).label('scheduled'),
        func.sum(case((PublishedContent.status == "published", 1), else_=0)).label('published')
    ).filter(
        PublishedContent.user_id == current_user.id
    ).first()

    return {
        "total": result.total or 0,
        "draft": int(result.draft or 0),
        "scheduled": int(result.scheduled or 0),
        "published": int(result.published or 0)
    }


@router.get("/by-session/{session_id}")
async def get_content_by_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    세션 ID로 기존 발행 콘텐츠 조회 (draft 상태만)
    - 생성내역에서 편집하기 클릭 시 중복 체크용
    - 이미 편집 중인 콘텐츠가 있으면 해당 콘텐츠 ID 반환
    """
    content = db.query(PublishedContent).filter(
        PublishedContent.session_id == session_id,
        PublishedContent.user_id == current_user.id,
        PublishedContent.status == "draft"
    ).first()

    if content:
        return {
            "exists": True,
            "content_id": content.id,
            "platform": content.platform,
            "title": content.title,
            "created_at": content.created_at.isoformat() if content.created_at else None
        }

    return {"exists": False}


@router.get("/{content_id}", response_model=PublishedContentResponse)
async def get_published_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    발행 콘텐츠 상세 조회
    """
    content = db.query(PublishedContent).filter(
        PublishedContent.id == content_id,
        PublishedContent.user_id == current_user.id
    ).first()

    if not content:
        raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없습니다.")

    return content


@router.put("/{content_id}", response_model=PublishedContentResponse)
async def update_published_content(
    content_id: int,
    request: PublishedContentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    발행 콘텐츠 수정
    - 발행 전(draft, scheduled) 상태에서만 수정 가능
    """
    content = db.query(PublishedContent).filter(
        PublishedContent.id == content_id,
        PublishedContent.user_id == current_user.id
    ).first()

    if not content:
        raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없습니다.")

    if content.status == "published":
        raise HTTPException(status_code=400, detail="발행된 콘텐츠는 수정할 수 없습니다.")

    try:
        if request.title is not None:
            content.title = request.title
        if request.content is not None:
            content.content = request.content
        if request.tags is not None:
            content.tags = request.tags
        if request.image_ids is not None:
            content.image_ids = request.image_ids
        if request.uploaded_image_url is not None:
            content.uploaded_image_url = request.uploaded_image_url
        if request.card_image_urls is not None:
            content.card_image_urls = request.card_image_urls
        if request.scheduled_at is not None:
            content.scheduled_at = request.scheduled_at
            content.status = "scheduled"

        db.commit()
        db.refresh(content)

        logger.info(f"콘텐츠 수정 완료: user_id={current_user.id}, id={content_id}")
        return content

    except Exception as e:
        db.rollback()
        logger.error(f"콘텐츠 수정 실패: {e}")
        raise HTTPException(status_code=500, detail=f"수정에 실패했습니다: {str(e)}")


@router.delete("/{content_id}")
async def delete_published_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    발행 콘텐츠 삭제
    """
    content = db.query(PublishedContent).filter(
        PublishedContent.id == content_id,
        PublishedContent.user_id == current_user.id
    ).first()

    if not content:
        raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없습니다.")

    db.delete(content)
    db.commit()

    logger.info(f"콘텐츠 삭제: user_id={current_user.id}, id={content_id}")
    return {"message": "콘텐츠가 삭제되었습니다."}


@router.post("/{content_id}/cancel-schedule", response_model=PublishedContentResponse)
async def cancel_schedule(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    예약 발행 취소
    - scheduled 상태를 draft로 변경
    """
    content = db.query(PublishedContent).filter(
        PublishedContent.id == content_id,
        PublishedContent.user_id == current_user.id
    ).first()

    if not content:
        raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없습니다.")

    if content.status != "scheduled":
        raise HTTPException(status_code=400, detail="예약된 콘텐츠만 취소할 수 있습니다.")

    content.status = "draft"
    content.scheduled_at = None
    db.commit()
    db.refresh(content)

    logger.info(f"예약 취소: user_id={current_user.id}, id={content_id}")
    return content


@router.post("/from-session/{session_id}", response_model=PublishedContentResponse)
async def create_from_session(
    session_id: int,
    platform: str = Query(..., description="플랫폼: blog, sns, x, threads"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    생성 세션에서 발행 콘텐츠 생성 (편집하기 기능)
    - ContentHistory에서 편집하기 클릭 시 호출
    - 원본 세션의 콘텐츠를 복사하여 draft 상태로 생성
    """
    session = db.query(ContentGenerationSession).filter(
        ContentGenerationSession.id == session_id,
        ContentGenerationSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    # 플랫폼별 콘텐츠 가져오기
    title = None
    content = None
    tags = None

    if platform == "blog" and session.blog_content:
        title = session.blog_content.title
        content = session.blog_content.content
        tags = session.blog_content.tags
    elif platform == "sns" and session.sns_content:
        content = session.sns_content.content
        tags = session.sns_content.hashtags
    elif platform == "x" and session.x_content:
        content = session.x_content.content
        tags = session.x_content.hashtags
    elif platform == "threads" and session.threads_content:
        content = session.threads_content.content
        tags = session.threads_content.hashtags
    else:
        raise HTTPException(status_code=400, detail=f"해당 플랫폼({platform})의 콘텐츠가 없습니다.")

    # 이미지 ID 목록
    image_ids = [img.id for img in session.images] if session.images else None

    # draft로 생성
    published = PublishedContent(
        user_id=current_user.id,
        session_id=session_id,
        platform=platform,
        title=title,
        content=content,
        tags=tags,
        image_ids=image_ids,
        status="draft"
    )
    db.add(published)
    db.commit()
    db.refresh(published)

    logger.info(f"세션에서 발행 콘텐츠 생성: user_id={current_user.id}, session_id={session_id}, platform={platform}")
    return published


class CardnewsPublishRequest(BaseModel):
    """카드뉴스 SNS 발행 요청"""
    platform: str  # instagram, facebook, threads
    image_urls: List[str]  # 카드뉴스 이미지 URL 배열
    caption: str  # 캡션/설명


@router.post("/publish-cardnews")
async def publish_cardnews(
    request: CardnewsPublishRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    카드뉴스 SNS 발행 (Instagram 캐러셀 / Facebook 앨범 / Threads)
    - Instagram: 캐러셀 포스트로 발행 (최대 10장)
    - Facebook: 사진 게시물로 발행 (첫 번째 이미지만)
    - Threads: 텍스트 포스트로 발행 (이미지 미지원 또는 첫 번째만)
    """
    platform = request.platform.lower()
    image_urls = request.image_urls
    caption = request.caption

    logger.info(f"카드뉴스 발행 요청: user_id={current_user.id}, platform={platform}, images={len(image_urls) if image_urls else 0}")

    if not image_urls or len(image_urls) == 0:
        raise HTTPException(status_code=400, detail="이미지가 필요합니다.")

    logger.info(f"카드뉴스 발행 시작: platform={platform}, images={len(image_urls)}")

    # base64 이미지를 Supabase Storage에 업로드하여 URL로 변환 (병렬 처리)
    import asyncio
    import time
    session_id = int(time.time())

    async def upload_single_image(idx: int, img_url: str) -> tuple:
        """개별 이미지 업로드 태스크"""
        if img_url.startswith('data:image'):
            public_url = await upload_cardnews_image_to_supabase(
                img_url,
                current_user.id,
                session_id,
                idx + 1
            )
            logger.info(f"이미지 {idx + 1} Supabase 업로드 완료")
            return (idx, public_url)
        else:
            return (idx, img_url)

    # base64 이미지가 있는지 확인
    has_base64 = any(url.startswith('data:image') for url in image_urls)

    if has_base64:
        logger.info(f"이미지 {len(image_urls)}개 병렬 업로드 시작...")
        tasks = [upload_single_image(idx, url) for idx, url in enumerate(image_urls)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 에러 확인
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"이미지 업로드 실패: {result}")
                raise HTTPException(status_code=500, detail=f"이미지 업로드 실패: {str(result)}")

        # 순서대로 정렬
        sorted_results = sorted([r for r in results if not isinstance(r, Exception)], key=lambda x: x[0])
        image_urls = [r[1] for r in sorted_results]
        logger.info(f"이미지 {len(image_urls)}개 업로드 완료")

    logger.info(f"최종 이미지 URL 수: {len(image_urls)}")

    try:
        publish_url = None
        platform_post_id = None

        # Instagram 캐러셀 발행
        if platform == "instagram":
            publish_url, platform_post_id = await _publish_cardnews_to_instagram(
                db, current_user, image_urls, caption
            )

        # Facebook 발행 (여러 이미지 지원)
        elif platform == "facebook":
            publish_url, platform_post_id = await _publish_cardnews_to_facebook(
                db, current_user, image_urls, caption
            )

        # Threads 발행 (텍스트만)
        elif platform == "threads":
            publish_url, platform_post_id = await _publish_to_threads(
                db, current_user, caption, None
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 플랫폼입니다: {platform}"
            )

        logger.info(f"카드뉴스 발행 완료: platform={platform}, url={publish_url}")

        return {
            "success": True,
            "platform": platform,
            "publish_url": publish_url,
            "platform_post_id": platform_post_id,
            "message": f"{platform}에 카드뉴스가 발행되었습니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"카드뉴스 발행 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"발행에 실패했습니다: {str(e)}")


async def _publish_cardnews_to_instagram(
    db: Session,
    user: User,
    image_urls: List[str],
    caption: str
) -> tuple:
    """
    Instagram에 캐러셀 포스트로 카드뉴스 발행
    Returns: (publish_url, post_id)
    """
    # Instagram 연동 확인
    connection = db.query(InstagramConnection).filter(
        InstagramConnection.user_id == user.id,
        InstagramConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(
            status_code=400,
            detail="Instagram 계정이 연동되어 있지 않습니다. 설정에서 Instagram 계정을 연동해주세요."
        )

    if len(image_urls) < 2:
        # 단일 이미지는 일반 발행으로 처리
        return await _publish_to_instagram(db, user, caption, None, image_urls[0])

    if len(image_urls) > 10:
        raise HTTPException(
            status_code=400,
            detail="Instagram 캐러셀은 최대 10장까지 가능합니다."
        )

    logger.info(f"Instagram 캐러셀 발행 시작: user_id={user.id}, images={len(image_urls)}")

    try:
        import asyncio
        service = InstagramService(connection.page_access_token)
        instagram_user_id = connection.instagram_account_id

        # 1. 각 이미지에 대해 캐러셀 아이템 컨테이너 생성 (병렬 처리)
        async def create_container(idx: int, img_url: str):
            """개별 컨테이너 생성 태스크"""
            container = await service.create_media_container(
                instagram_user_id=instagram_user_id,
                image_url=img_url,
                is_carousel_item=True
            )
            if not container or "id" not in container:
                raise Exception(f"이미지 {idx + 1} 컨테이너 생성 실패")
            logger.info(f"캐러셀 아이템 {idx + 1} 생성됨: {container['id']}")
            return (idx, container["id"])

        logger.info(f"캐러셀 아이템 {len(image_urls)}개 병렬 생성 시작...")
        tasks = [create_container(idx, url) for idx, url in enumerate(image_urls)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 확인 및 순서 정렬
        children_ids = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"캐러셀 아이템 생성 실패: {result}")
                raise HTTPException(status_code=500, detail=str(result))

        # 순서대로 정렬 (idx 기준)
        sorted_results = sorted([r for r in results if not isinstance(r, Exception)], key=lambda x: x[0])
        children_ids = [r[1] for r in sorted_results]
        logger.info(f"캐러셀 아이템 {len(children_ids)}개 생성 완료")

        # 2. 캐러셀 컨테이너 생성
        logger.info(f"캐러셀 컨테이너 생성 중: children={children_ids}")
        carousel_container = await service.create_carousel_container(
            instagram_user_id=instagram_user_id,
            children_ids=children_ids,
            caption=caption
        )

        if not carousel_container or "id" not in carousel_container:
            logger.error("캐러셀 컨테이너 생성 실패")
            raise HTTPException(status_code=500, detail="캐러셀 컨테이너 생성에 실패했습니다.")

        carousel_id = carousel_container["id"]
        logger.info(f"캐러셀 컨테이너 생성됨: {carousel_id}")

        # 3. 캐러셀 발행
        result = await service.publish_media(
            instagram_user_id=instagram_user_id,
            creation_id=carousel_id
        )

        await service.close()

        if not result or "id" not in result:
            logger.error("Instagram 캐러셀 발행 실패")
            raise HTTPException(status_code=500, detail="Instagram 캐러셀 발행에 실패했습니다.")

        post_id = result.get("id")
        username = connection.instagram_username
        publish_url = f"https://www.instagram.com/p/{post_id}/" if post_id else None

        logger.info(f"Instagram 캐러셀 발행 성공: user_id={user.id}, post_id={post_id}")
        return publish_url, post_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Instagram 캐러셀 발행 중 예외 발생: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Instagram 캐러셀 발행 중 오류가 발생했습니다: {str(e)}")


async def _publish_cardnews_to_facebook(
    db: Session,
    user: User,
    image_urls: List[str],
    caption: str
) -> tuple:
    """
    Facebook 페이지에 여러 이미지가 포함된 카드뉴스 발행
    Returns: (publish_url, post_id)
    """
    # Facebook 연동 확인
    connection = db.query(FacebookConnection).filter(
        FacebookConnection.user_id == user.id,
        FacebookConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(
            status_code=400,
            detail="Facebook 페이지가 연동되어 있지 않습니다. 설정에서 Facebook 페이지를 연동해주세요."
        )

    if not connection.page_id or not connection.page_access_token:
        raise HTTPException(
            status_code=400,
            detail="Facebook 페이지가 선택되어 있지 않습니다. 설정에서 페이지를 선택해주세요."
        )

    logger.info(f"Facebook 카드뉴스 발행 시작: user_id={user.id}, page={connection.page_name}, images={len(image_urls)}")

    try:
        service = FacebookService(connection.user_access_token, connection.page_access_token)

        # 여러 이미지 게시물 생성
        result = await service.create_multi_photo_post(
            page_id=connection.page_id,
            photo_urls=image_urls,
            message=caption
        )

        await service.close()

        if not result or "id" not in result:
            logger.error("Facebook 카드뉴스 발행 실패: API 응답 없음")
            raise HTTPException(status_code=500, detail="Facebook 카드뉴스 발행에 실패했습니다.")

        post_id = result.get("id")
        actual_post_id = post_id.split("_")[-1] if "_" in post_id else post_id
        publish_url = f"https://www.facebook.com/{connection.page_id}/posts/{actual_post_id}"

        logger.info(f"Facebook 카드뉴스 발행 성공: user_id={user.id}, post_id={post_id}")
        return publish_url, post_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Facebook 카드뉴스 발행 중 예외 발생: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Facebook 카드뉴스 발행 중 오류가 발생했습니다: {str(e)}")


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    이미지 업로드 (Supabase Storage)
    - Instagram/SNS 발행용 이미지 업로드
    - 반환: image_url (공개 접근 가능 URL)
    """
    # 파일 타입 검증
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="지원하지 않는 이미지 형식입니다. JPEG, PNG, GIF, WebP만 가능합니다."
        )

    # 파일 크기 제한 (10MB)
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail="이미지 크기는 10MB를 초과할 수 없습니다."
        )

    try:
        # Supabase 클라이언트 가져오기
        client = _get_supabase_client()
        if not client:
            raise Exception("Supabase 클라이언트가 초기화되지 않았습니다. 환경변수를 확인해주세요.")

        # 파일명 생성
        ext = file.filename.split('.')[-1].lower() if file.filename and '.' in file.filename else 'jpg'
        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            ext = 'jpg'

        # content-type 결정
        content_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        content_type = content_type_map.get(ext, 'image/jpeg')

        # 파일 경로: publish/{user_id}/{uuid}.{ext}
        file_path = f"publish/{current_user.id}/{uuid.uuid4().hex}.{ext}"
        bucket_name = "cardnews"  # 기존 cardnews 버킷 활용

        # 기존 파일 삭제 시도 (있으면)
        try:
            client.storage.from_(bucket_name).remove([file_path])
        except Exception:
            pass

        # Supabase Storage에 업로드
        client.storage.from_(bucket_name).upload(
            file_path,
            content,
            {"content-type": content_type}
        )

        # 공개 URL 생성
        image_url = client.storage.from_(bucket_name).get_public_url(file_path)

        logger.info(f"이미지 업로드 완료 (Supabase): user_id={current_user.id}, url={image_url[:80]}...")

        return {
            "image_url": image_url,
            "public_id": file_path,
            "width": None,
            "height": None,
            "format": ext,
            "size": len(content)
        }

    except Exception as e:
        logger.error(f"이미지 업로드 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이미지 업로드에 실패했습니다: {str(e)}")
