"""
예약 발행 스케줄러
- APScheduler를 사용하여 예약된 콘텐츠를 자동 발행
- 매분 예약된 콘텐츠를 확인하고 발행 시간이 된 콘텐츠를 발행
"""

import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

from .database import SessionLocal
from .models import PublishedContent, GeneratedImage, XConnection, ThreadsConnection, InstagramConnection, FacebookConnection
from .services.x_service import XService, XTokenExpiredError, XAPIError
from .services.threads_service import ThreadsService
from .services.instagram_service import InstagramService
from .services.facebook_service import FacebookService

logger = logging.getLogger(__name__)

# 스케줄러 인스턴스
scheduler = AsyncIOScheduler()


async def publish_scheduled_content(content_id: int, db):
    """
    예약된 콘텐츠를 실제로 발행
    """
    content = db.query(PublishedContent).filter(PublishedContent.id == content_id).first()
    if not content:
        logger.warning(f"예약 발행 실패: 콘텐츠를 찾을 수 없음 (id={content_id})")
        return False

    if content.status != "scheduled":
        logger.warning(f"예약 발행 스킵: 콘텐츠 상태가 scheduled가 아님 (id={content_id}, status={content.status})")
        return False

    logger.info(f"예약 발행 시작: id={content_id}, platform={content.platform}")

    try:
        publish_url = None
        platform_post_id = None

        # X(Twitter) 발행
        if content.platform == "x":
            publish_url, platform_post_id = await _publish_to_x(
                db, content.user_id, content.content, content.tags
            )

        # Threads 발행
        elif content.platform == "threads":
            publish_url, platform_post_id = await _publish_to_threads(
                db, content.user_id, content.content, content.tags
            )

        # Instagram 발행
        elif content.platform in ["sns", "instagram"]:
            image_url = content.uploaded_image_url
            if not image_url and content.image_ids and len(content.image_ids) > 0:
                image = db.query(GeneratedImage).filter(
                    GeneratedImage.id == content.image_ids[0]
                ).first()
                if image:
                    image_url = image.image_url

            publish_url, platform_post_id = await _publish_to_instagram(
                db, content.user_id, content.content, content.tags, image_url
            )

        # Facebook 발행
        elif content.platform == "facebook":
            image_url = content.uploaded_image_url
            if not image_url and content.image_ids and len(content.image_ids) > 0:
                image = db.query(GeneratedImage).filter(
                    GeneratedImage.id == content.image_ids[0]
                ).first()
                if image:
                    image_url = image.image_url

            publish_url, platform_post_id = await _publish_to_facebook(
                db, content.user_id, content.content, content.tags, image_url
            )

        else:
            logger.warning(f"예약 발행 실패: 지원하지 않는 플랫폼 (platform={content.platform})")
            content.status = "failed"
            content.publish_error = f"지원하지 않는 플랫폼입니다: {content.platform}"
            db.commit()
            return False

        # 발행 성공
        content.status = "published"
        content.published_at = datetime.utcnow()
        if publish_url:
            content.publish_url = publish_url
        if platform_post_id:
            content.platform_post_id = platform_post_id

        db.commit()
        logger.info(f"예약 발행 완료: id={content_id}, platform={content.platform}, url={publish_url}")
        return True

    except Exception as e:
        logger.error(f"예약 발행 실패: id={content_id}, error={str(e)}")
        content.status = "failed"
        content.publish_error = str(e)
        db.commit()
        return False


async def _publish_to_x(db, user_id: int, content: str, tags: list = None) -> tuple:
    """X(Twitter)에 콘텐츠 발행"""
    connection = db.query(XConnection).filter(
        XConnection.user_id == user_id,
        XConnection.is_active == True
    ).first()

    if not connection:
        raise Exception("X 계정이 연동되어 있지 않습니다.")

    tweet_text = content
    if tags and len(tags) > 0:
        hashtags = " ".join([f"#{tag}" if not tag.startswith("#") else tag for tag in tags])
        if len(tweet_text) + len(hashtags) + 1 <= 280:
            tweet_text = f"{tweet_text}\n{hashtags}"

    if len(tweet_text) > 280:
        tweet_text = tweet_text[:277] + "..."

    service = XService(connection.access_token, connection.refresh_token)
    result = await service.create_tweet(tweet_text)

    if not result:
        raise Exception("X 발행에 실패했습니다.")

    post_id = result.get("id")
    username = connection.username
    publish_url = f"https://x.com/{username}/status/{post_id}" if username and post_id else None

    return publish_url, post_id


async def _publish_to_threads(db, user_id: int, content: str, tags: list = None) -> tuple:
    """Threads에 콘텐츠 발행"""
    connection = db.query(ThreadsConnection).filter(
        ThreadsConnection.user_id == user_id,
        ThreadsConnection.is_active == True
    ).first()

    if not connection:
        raise Exception("Threads 계정이 연동되어 있지 않습니다.")

    post_text = content
    if tags and len(tags) > 0:
        hashtags = " ".join([f"#{tag}" if not tag.startswith("#") else tag for tag in tags])
        if len(post_text) + len(hashtags) + 1 <= 500:
            post_text = f"{post_text}\n\n{hashtags}"

    if len(post_text) > 500:
        post_text = post_text[:497] + "..."

    service = ThreadsService(connection.access_token, connection.threads_user_id)
    result = await service.create_and_publish_thread(
        user_id=connection.threads_user_id,
        text=post_text
    )

    if not result:
        raise Exception("Threads 발행에 실패했습니다.")

    post_id = result.get("id")
    username = connection.username
    publish_url = f"https://www.threads.net/@{username}/post/{post_id}" if username and post_id else None

    return publish_url, post_id


async def _publish_to_instagram(db, user_id: int, content: str, tags: list = None, image_url: str = None) -> tuple:
    """Instagram에 콘텐츠 발행"""
    connection = db.query(InstagramConnection).filter(
        InstagramConnection.user_id == user_id,
        InstagramConnection.is_active == True
    ).first()

    if not connection:
        raise Exception("Instagram 계정이 연동되어 있지 않습니다.")

    if not image_url:
        raise Exception("Instagram 발행에는 이미지가 필요합니다.")

    caption = content
    if tags and len(tags) > 0:
        hashtags = " ".join([f"#{tag}" if not tag.startswith("#") else tag for tag in tags])
        if len(caption) + len(hashtags) + 2 <= 2200:
            caption = f"{caption}\n\n{hashtags}"

    if len(caption) > 2200:
        caption = caption[:2197] + "..."

    service = InstagramService(connection.page_access_token)

    container = await service.create_media_container(
        instagram_user_id=connection.instagram_account_id,
        image_url=image_url,
        caption=caption
    )

    if not container or "id" not in container:
        raise Exception("Instagram 미디어 컨테이너 생성에 실패했습니다.")

    result = await service.publish_media(
        instagram_user_id=connection.instagram_account_id,
        creation_id=container["id"]
    )

    await service.close()

    if not result or "id" not in result:
        raise Exception("Instagram 발행에 실패했습니다.")

    post_id = result.get("id")
    publish_url = f"https://www.instagram.com/p/{post_id}/" if post_id else None

    return publish_url, post_id


async def _publish_to_facebook(db, user_id: int, content: str, tags: list = None, image_url: str = None) -> tuple:
    """Facebook 페이지에 콘텐츠 발행"""
    connection = db.query(FacebookConnection).filter(
        FacebookConnection.user_id == user_id,
        FacebookConnection.is_active == True
    ).first()

    if not connection:
        raise Exception("Facebook 페이지가 연동되어 있지 않습니다.")

    if not connection.page_id or not connection.page_access_token:
        raise Exception("Facebook 페이지가 선택되어 있지 않습니다.")

    message = content
    if tags and len(tags) > 0:
        hashtags = " ".join([f"#{tag}" if not tag.startswith("#") else tag for tag in tags])
        message = f"{message}\n\n{hashtags}"

    service = FacebookService(connection.user_access_token, connection.page_access_token)

    if image_url:
        result = await service.create_photo_post(
            page_id=connection.page_id,
            photo_url=image_url,
            caption=message
        )
    else:
        result = await service.create_post(
            page_id=connection.page_id,
            message=message
        )

    await service.close()

    if not result or "id" not in result:
        raise Exception("Facebook 발행에 실패했습니다.")

    post_id = result.get("id")
    actual_post_id = post_id.split("_")[-1] if "_" in post_id else post_id
    publish_url = f"https://www.facebook.com/{connection.page_id}/posts/{actual_post_id}"

    return publish_url, post_id


async def check_and_publish_scheduled_contents():
    """
    예약된 콘텐츠를 확인하고 발행 시간이 된 콘텐츠를 발행
    """
    db = SessionLocal()
    try:
        # 현재 시간 이전에 예약된 콘텐츠 조회
        now = datetime.utcnow()
        scheduled_contents = db.query(PublishedContent).filter(
            PublishedContent.status == "scheduled",
            PublishedContent.scheduled_at <= now
        ).all()

        if scheduled_contents:
            logger.info(f"예약 발행 대상: {len(scheduled_contents)}개")

        for content in scheduled_contents:
            try:
                await publish_scheduled_content(content.id, db)
            except Exception as e:
                logger.error(f"예약 발행 처리 중 오류: content_id={content.id}, error={str(e)}")

    except Exception as e:
        logger.error(f"예약 발행 확인 중 오류: {str(e)}")
    finally:
        db.close()


def start_scheduler():
    """
    스케줄러 시작
    - 매분 예약된 콘텐츠 확인
    """
    if scheduler.running:
        print("⚠️  스케줄러가 이미 실행 중입니다.")
        logger.info("스케줄러가 이미 실행 중입니다.")
        return

    # 매분 실행되는 작업 추가
    scheduler.add_job(
        check_and_publish_scheduled_contents,
        trigger=IntervalTrigger(minutes=1),
        id='check_scheduled_contents',
        name='예약 발행 확인',
        replace_existing=True
    )

    scheduler.start()
    print("✅ 예약 발행 스케줄러 시작됨 (매분 확인)")
    logger.info("예약 발행 스케줄러 시작됨 (매분 확인)")


def stop_scheduler():
    """
    스케줄러 정지
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("예약 발행 스케줄러 정지됨")
