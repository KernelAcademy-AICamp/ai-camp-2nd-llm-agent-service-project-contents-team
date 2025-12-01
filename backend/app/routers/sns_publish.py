"""
SNS 통합 발행 API Router
- Instagram과 Facebook에 동시 발행
- 이미지 업로드 지원
"""
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
import os

from .. import models, auth
from ..database import get_db
from ..services.instagram_service import InstagramService
from ..services.facebook_service import FacebookService
from ..logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/sns",
    tags=["sns-publish"]
)

# 임시 이미지 호스팅을 위한 IMGBB API
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "")


# ===== Pydantic Schemas =====

class PlatformSelection(BaseModel):
    instagram: bool = False
    facebook: bool = False


class PublishContent(BaseModel):
    type: str = "text"  # "text" or "image"
    instagramCaption: Optional[str] = None
    facebookPost: Optional[str] = None
    hashtags: Optional[List[str]] = []
    images: Optional[List[str]] = []  # base64 또는 URL


class PublishRequest(BaseModel):
    platforms: PlatformSelection
    content: PublishContent


class PlatformStatus(BaseModel):
    connected: bool
    username: Optional[str] = None
    name: Optional[str] = None
    profile_picture_url: Optional[str] = None


class SNSStatusResponse(BaseModel):
    instagram: PlatformStatus
    facebook: PlatformStatus


# ===== Helper Functions =====

async def upload_image_to_hosting(image_data: str) -> Optional[str]:
    """
    이미지를 임시 호스팅 서비스에 업로드하고 URL 반환
    Instagram API는 공개 URL이 필요함
    """
    # 이미 URL인 경우 그대로 반환
    if image_data.startswith('http://') or image_data.startswith('https://'):
        return image_data

    # base64 데이터인 경우 IMGBB에 업로드
    if not IMGBB_API_KEY:
        logger.warning("IMGBB_API_KEY not configured, cannot upload base64 images")
        return None

    try:
        # base64 prefix 제거
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.imgbb.com/1/upload",
                data={
                    "key": IMGBB_API_KEY,
                    "image": image_data,
                    "expiration": 86400  # 24시간 후 만료
                }
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result['data']['url']

            logger.error(f"IMGBB upload failed: {response.text}")
            return None

    except Exception as e:
        logger.error(f"Image upload error: {e}")
        return None


async def publish_to_instagram(
    connection: models.InstagramConnection,
    caption: str,
    hashtags: List[str],
    image_urls: List[str]
) -> Dict:
    """Instagram에 게시물 발행"""
    try:
        ig_service = InstagramService(connection.page_access_token)

        # 해시태그를 캡션에 추가
        full_caption = caption
        if hashtags:
            hashtag_text = ' '.join([f'#{tag}' if not tag.startswith('#') else tag for tag in hashtags])
            full_caption = f"{caption}\n\n{hashtag_text}"

        if not image_urls:
            await ig_service.close()
            return {"success": False, "error": "Instagram requires at least one image"}

        if len(image_urls) == 1:
            # 단일 이미지 게시
            container = await ig_service.create_media_container(
                connection.instagram_account_id,
                image_url=image_urls[0],
                caption=full_caption
            )

            if not container or 'id' not in container:
                await ig_service.close()
                return {"success": False, "error": "Failed to create media container"}

            # 게시
            result = await ig_service.publish_media(
                connection.instagram_account_id,
                container['id']
            )

            await ig_service.close()

            if result and 'id' in result:
                return {"success": True, "post_id": result['id']}
            else:
                return {"success": False, "error": "Failed to publish media"}

        else:
            # 캐러셀 (여러 이미지) 게시
            children_ids = []

            for img_url in image_urls[:10]:  # Instagram 최대 10개
                container = await ig_service.create_media_container(
                    connection.instagram_account_id,
                    image_url=img_url,
                    is_carousel_item=True
                )
                if container and 'id' in container:
                    children_ids.append(container['id'])

            if not children_ids:
                await ig_service.close()
                return {"success": False, "error": "Failed to create carousel items"}

            # 캐러셀 컨테이너 생성
            carousel = await ig_service.create_carousel_container(
                connection.instagram_account_id,
                children_ids,
                caption=full_caption
            )

            if not carousel or 'id' not in carousel:
                await ig_service.close()
                return {"success": False, "error": "Failed to create carousel container"}

            # 게시
            result = await ig_service.publish_media(
                connection.instagram_account_id,
                carousel['id']
            )

            await ig_service.close()

            if result and 'id' in result:
                return {"success": True, "post_id": result['id']}
            else:
                return {"success": False, "error": "Failed to publish carousel"}

    except Exception as e:
        logger.error(f"Instagram publish error: {e}")
        return {"success": False, "error": str(e)}


async def publish_to_facebook(
    connection: models.FacebookConnection,
    message: str,
    image_urls: List[str]
) -> Dict:
    """Facebook 페이지에 게시물 발행"""
    try:
        fb_service = FacebookService(
            connection.user_access_token,
            connection.page_access_token
        )

        if image_urls:
            # 사진 게시물
            result = await fb_service.create_photo_post(
                connection.page_id,
                image_urls[0],
                message
            )
        else:
            # 텍스트 게시물
            result = await fb_service.create_post(
                connection.page_id,
                message
            )

        await fb_service.close()

        if result and 'id' in result:
            return {"success": True, "post_id": result['id']}
        else:
            return {"success": False, "error": "Failed to create Facebook post"}

    except Exception as e:
        logger.error(f"Facebook publish error: {e}")
        return {"success": False, "error": str(e)}


# ===== API Endpoints =====

@router.get('/status', response_model=SNSStatusResponse)
async def get_sns_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Instagram과 Facebook 연동 상태 확인"""

    # Instagram 연동 상태
    ig_connection = db.query(models.InstagramConnection).filter(
        models.InstagramConnection.user_id == current_user.id,
        models.InstagramConnection.is_active == True
    ).first()

    instagram_status = PlatformStatus(
        connected=ig_connection is not None and ig_connection.instagram_account_id is not None,
        username=ig_connection.instagram_username if ig_connection else None,
        name=ig_connection.instagram_name if ig_connection else None,
        profile_picture_url=ig_connection.instagram_profile_picture_url if ig_connection else None
    )

    # Facebook 연동 상태
    fb_connection = db.query(models.FacebookConnection).filter(
        models.FacebookConnection.user_id == current_user.id,
        models.FacebookConnection.is_active == True
    ).first()

    facebook_status = PlatformStatus(
        connected=fb_connection is not None and fb_connection.page_id is not None,
        username=fb_connection.page_name if fb_connection else None,
        name=fb_connection.page_name if fb_connection else None,
        profile_picture_url=fb_connection.page_picture_url if fb_connection else None
    )

    return SNSStatusResponse(
        instagram=instagram_status,
        facebook=facebook_status
    )


@router.post('/publish')
async def publish_to_sns(
    request: PublishRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Instagram과 Facebook에 콘텐츠 발행"""

    results = {
        "success": False,
        "instagram": None,
        "facebook": None
    }

    # 이미지 URL 준비 (base64인 경우 호스팅 서비스에 업로드)
    image_urls = []
    for img in request.content.images or []:
        if img:
            hosted_url = await upload_image_to_hosting(img)
            if hosted_url:
                image_urls.append(hosted_url)
                logger.info(f"Image hosted at: {hosted_url}")

    # Instagram 발행
    if request.platforms.instagram:
        ig_connection = db.query(models.InstagramConnection).filter(
            models.InstagramConnection.user_id == current_user.id,
            models.InstagramConnection.is_active == True
        ).first()

        if not ig_connection or not ig_connection.instagram_account_id:
            results["instagram"] = {"success": False, "error": "Instagram not connected"}
        else:
            results["instagram"] = await publish_to_instagram(
                ig_connection,
                request.content.instagramCaption or "",
                request.content.hashtags or [],
                image_urls
            )

    # Facebook 발행
    if request.platforms.facebook:
        fb_connection = db.query(models.FacebookConnection).filter(
            models.FacebookConnection.user_id == current_user.id,
            models.FacebookConnection.is_active == True
        ).first()

        if not fb_connection or not fb_connection.page_id:
            results["facebook"] = {"success": False, "error": "Facebook page not connected"}
        else:
            # Facebook 메시지에 해시태그 포함
            fb_message = request.content.facebookPost or ""
            if request.content.hashtags:
                hashtag_text = ' '.join([f'#{tag}' if not tag.startswith('#') else tag for tag in request.content.hashtags])
                fb_message = f"{fb_message}\n\n{hashtag_text}"

            results["facebook"] = await publish_to_facebook(
                fb_connection,
                fb_message,
                image_urls
            )

    # 전체 성공 여부 판단
    instagram_success = results.get("instagram", {}).get("success", True) if results.get("instagram") else True
    facebook_success = results.get("facebook", {}).get("success", True) if results.get("facebook") else True
    results["success"] = instagram_success or facebook_success

    return results
