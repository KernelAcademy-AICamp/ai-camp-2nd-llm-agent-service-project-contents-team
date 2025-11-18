"""
예약 발행 스케줄러

주기적으로 예약된 게시물을 확인하고 발행 시간이 되면 자동으로 발행합니다.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone
import httpx
import logging

from .database import SessionLocal
from . import models

logger = logging.getLogger(__name__)

# Meta Graph API 베이스 URL
GRAPH_API_URL = "https://graph.facebook.com/v18.0"

scheduler = AsyncIOScheduler()


async def publish_instagram_post(scheduled_post: models.ScheduledPost, ig_account: models.InstagramAccount, db):
    """
    Instagram에 게시물 발행
    """
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: 미디어 컨테이너 생성
            container_response = await client.post(
                f"{GRAPH_API_URL}/{ig_account.instagram_business_account_id}/media",
                data={
                    "image_url": scheduled_post.media_url,
                    "caption": scheduled_post.caption,
                    "access_token": ig_account.access_token
                }
            )

            if container_response.status_code != 200:
                error_data = container_response.json()
                raise Exception(f"미디어 컨테이너 생성 실패: {error_data.get('error', {}).get('message', 'Unknown error')}")

            container_data = container_response.json()
            creation_id = container_data.get("id")

            # Step 2: 컨테이너를 게시물로 발행
            publish_response = await client.post(
                f"{GRAPH_API_URL}/{ig_account.instagram_business_account_id}/media_publish",
                data={
                    "creation_id": creation_id,
                    "access_token": ig_account.access_token
                }
            )

            if publish_response.status_code != 200:
                error_data = publish_response.json()
                raise Exception(f"게시물 발행 실패: {error_data.get('error', {}).get('message', 'Unknown error')}")

            publish_data = publish_response.json()
            post_id = publish_data.get("id")

            # 성공한 게시물 기록
            new_post = models.Post(
                user_id=scheduled_post.user_id,
                platform=scheduled_post.platform,
                platform_post_id=post_id,
                content_type=scheduled_post.content_type,
                caption=scheduled_post.caption,
                media_url=scheduled_post.media_url,
                status="published"
            )
            db.add(new_post)
            db.flush()

            # 예약 게시물 상태 업데이트
            scheduled_post.status = "published"
            scheduled_post.post_id = new_post.id
            db.commit()

            logger.info(f"예약 게시물 발행 성공: {scheduled_post.id}")
            return True

    except Exception as e:
        logger.error(f"예약 게시물 발행 실패: {scheduled_post.id}, 오류: {str(e)}")

        # 실패한 게시물 기록
        failed_post = models.Post(
            user_id=scheduled_post.user_id,
            platform=scheduled_post.platform,
            content_type=scheduled_post.content_type,
            caption=scheduled_post.caption,
            media_url=scheduled_post.media_url,
            status="failed",
            error_message=str(e)
        )
        db.add(failed_post)

        # 예약 게시물 상태 업데이트
        scheduled_post.status = "failed"
        scheduled_post.error_message = str(e)
        scheduled_post.post_id = failed_post.id
        db.commit()

        return False


async def check_and_publish_scheduled_posts():
    """
    예약된 게시물을 확인하고 발행 시간이 되면 발행합니다.
    매분마다 실행됩니다.
    """
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # 발행 시간이 된 pending 상태의 예약 게시물 조회
        scheduled_posts = db.query(models.ScheduledPost).filter(
            models.ScheduledPost.status == "pending",
            models.ScheduledPost.scheduled_time <= now
        ).all()

        if not scheduled_posts:
            return

        logger.info(f"발행할 예약 게시물 {len(scheduled_posts)}개 발견")

        for scheduled_post in scheduled_posts:
            # 상태를 processing으로 변경 (중복 발행 방지)
            scheduled_post.status = "processing"
            db.commit()

            # 플랫폼에 따라 발행 처리
            if scheduled_post.platform == "instagram":
                # 연동된 Instagram 계정 가져오기
                ig_account = db.query(models.InstagramAccount).filter(
                    models.InstagramAccount.user_id == scheduled_post.user_id,
                    models.InstagramAccount.is_active == True
                ).first()

                if not ig_account:
                    scheduled_post.status = "failed"
                    scheduled_post.error_message = "연동된 Instagram 계정이 없습니다."
                    db.commit()
                    continue

                await publish_instagram_post(scheduled_post, ig_account, db)

            # 추후 다른 플랫폼 추가 가능
            # elif scheduled_post.platform == "facebook":
            #     await publish_facebook_post(scheduled_post, db)

    except Exception as e:
        logger.error(f"스케줄러 오류: {str(e)}")
    finally:
        db.close()


def start_scheduler():
    """
    스케줄러 시작
    매분마다 예약 게시물 확인
    """
    scheduler.add_job(
        check_and_publish_scheduled_posts,
        trigger=IntervalTrigger(minutes=1),
        id="check_scheduled_posts",
        name="예약 게시물 확인 및 발행",
        replace_existing=True
    )
    scheduler.start()
    logger.info("예약 발행 스케줄러 시작됨")


def shutdown_scheduler():
    """
    스케줄러 종료
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("예약 발행 스케줄러 종료됨")
