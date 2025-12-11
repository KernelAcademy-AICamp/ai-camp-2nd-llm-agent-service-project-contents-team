"""
발행 콘텐츠 API 라우터
- 임시저장, 예약발행, 즉시발행, 콘텐츠 관리
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from datetime import datetime
import logging
import os
import uuid
from google.cloud import storage

from ..database import get_db
from ..models import User, PublishedContent, ContentGenerationSession, GeneratedImage, XConnection, ThreadsConnection, InstagramConnection
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


@router.post("/draft", response_model=PublishedContentResponse)
async def save_draft(
    request: PublishedContentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    콘텐츠 임시저장 (작성 중)
    - 생성된 콘텐츠를 편집하여 임시저장
    """
    try:
        published = PublishedContent(
            user_id=current_user.id,
            session_id=request.session_id,
            platform=request.platform,
            title=request.title,
            content=request.content,
            tags=request.tags,
            image_ids=request.image_ids,
            uploaded_image_url=request.uploaded_image_url,
            status="draft"
        )
        db.add(published)
        db.commit()
        db.refresh(published)

        logger.info(f"임시저장 완료: user_id={current_user.id}, id={published.id}")
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
    - scheduled_at 시간에 자동 발행 예약
    """
    try:
        # 예약 시간 검증
        if request.scheduled_at <= datetime.now(request.scheduled_at.tzinfo):
            raise HTTPException(status_code=400, detail="예약 시간은 현재 시간 이후여야 합니다.")

        published = PublishedContent(
            user_id=current_user.id,
            session_id=request.session_id,
            platform=request.platform,
            title=request.title,
            content=request.content,
            tags=request.tags,
            image_ids=request.image_ids,
            uploaded_image_url=request.uploaded_image_url,
            status="scheduled",
            scheduled_at=request.scheduled_at
        )
        db.add(published)
        db.commit()
        db.refresh(published)

        logger.info(f"예약발행 설정: user_id={current_user.id}, id={published.id}, scheduled_at={request.scheduled_at}")
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

        # TODO: 다른 플랫폼 발행 로직 추가
        # - blog: 네이버 블로그 API

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
    """
    query = db.query(PublishedContent).filter(
        PublishedContent.user_id == current_user.id
    )

    if status:
        query = query.filter(PublishedContent.status == status)

    if platform:
        query = query.filter(PublishedContent.platform == platform)

    contents = query.order_by(
        PublishedContent.created_at.desc()
    ).offset(skip).limit(limit).all()

    return contents


@router.get("/stats")
async def get_content_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    콘텐츠 상태별 통계 (콘텐츠 관리 페이지 탭 카운트용)
    """
    total = db.query(PublishedContent).filter(
        PublishedContent.user_id == current_user.id
    ).count()

    draft = db.query(PublishedContent).filter(
        PublishedContent.user_id == current_user.id,
        PublishedContent.status == "draft"
    ).count()

    scheduled = db.query(PublishedContent).filter(
        PublishedContent.user_id == current_user.id,
        PublishedContent.status == "scheduled"
    ).count()

    published = db.query(PublishedContent).filter(
        PublishedContent.user_id == current_user.id,
        PublishedContent.status == "published"
    ).count()

    return {
        "total": total,
        "draft": draft,
        "scheduled": scheduled,
        "published": published
    }


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


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    이미지 업로드 (Cloudinary)
    - Instagram/SNS 발행용 이미지 업로드
    - 반환: image_url (Cloudinary URL - 공개 접근 가능)
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
        # GCS 클라이언트 초기화 (lazy initialization)
        init_gcs()

        if not gcs_bucket:
            raise Exception("Google Cloud Storage가 초기화되지 않았습니다. 환경변수를 확인해주세요.")

        # 파일명 생성: publish/{user_id}/{uuid}.{ext}
        ext = file.filename.split('.')[-1].lower() if file.filename and '.' in file.filename else 'jpg'
        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            ext = 'jpg'
        blob_name = f"publish/{current_user.id}/{uuid.uuid4().hex}.{ext}"

        # GCS에 업로드
        blob = gcs_bucket.blob(blob_name)
        blob.upload_from_string(content, content_type=file.content_type)

        # 공개 URL 생성 (버킷이 공개 설정된 경우)
        blob.make_public()
        image_url = blob.public_url

        logger.info(f"이미지 업로드 완료 (GCS): user_id={current_user.id}, url={image_url}")

        return {
            "image_url": image_url,
            "public_id": blob_name,
            "width": None,
            "height": None,
            "format": ext,
            "size": len(content)
        }

    except Exception as e:
        logger.error(f"이미지 업로드 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이미지 업로드에 실패했습니다: {str(e)}")
