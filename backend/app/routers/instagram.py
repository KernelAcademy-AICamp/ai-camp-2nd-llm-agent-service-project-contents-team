from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import httpx
from datetime import datetime, timezone

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/api/instagram",
    tags=["instagram"]
)

# Meta Graph API 베이스 URL
GRAPH_API_URL = "https://graph.facebook.com/v18.0"


@router.post("/connect", response_model=schemas.InstagramAccount)
async def connect_instagram_account(
    access_token: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Instagram Business Account 연동

    1. Facebook 페이지 목록 가져오기
    2. 페이지에 연결된 Instagram Business Account 가져오기
    3. DB에 저장
    """
    try:
        async with httpx.AsyncClient() as client:
            # 1. 사용자의 Facebook 페이지 목록 가져오기
            pages_response = await client.get(
                f"{GRAPH_API_URL}/me/accounts",
                params={
                    "access_token": access_token,
                    "fields": "id,name,access_token"
                }
            )

            if pages_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Facebook 페이지를 가져올 수 없습니다."
                )

            pages_data = pages_response.json()

            if not pages_data.get("data"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="연결된 Facebook 페이지가 없습니다."
                )

            # 첫 번째 페이지 사용 (나중에 사용자가 선택하도록 개선 가능)
            page = pages_data["data"][0]
            page_id = page["id"]
            page_name = page["name"]
            page_access_token = page["access_token"]

            # 2. 페이지에 연결된 Instagram Business Account 가져오기
            instagram_response = await client.get(
                f"{GRAPH_API_URL}/{page_id}",
                params={
                    "access_token": page_access_token,
                    "fields": "instagram_business_account"
                }
            )

            if instagram_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Instagram Business Account를 가져올 수 없습니다."
                )

            instagram_data = instagram_response.json()

            if "instagram_business_account" not in instagram_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="이 Facebook 페이지에 연결된 Instagram Business Account가 없습니다."
                )

            ig_account_id = instagram_data["instagram_business_account"]["id"]

            # 3. Instagram 계정 정보 가져오기
            ig_info_response = await client.get(
                f"{GRAPH_API_URL}/{ig_account_id}",
                params={
                    "access_token": page_access_token,
                    "fields": "username,profile_picture_url"
                }
            )

            if ig_info_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Instagram 계정 정보를 가져올 수 없습니다."
                )

            ig_info = ig_info_response.json()

            # 4. DB에 저장 (기존 계정이 있으면 업데이트)
            existing_account = db.query(models.InstagramAccount).filter(
                models.InstagramAccount.instagram_business_account_id == ig_account_id
            ).first()

            if existing_account:
                # 업데이트
                existing_account.username = ig_info.get("username", "")
                existing_account.profile_picture_url = ig_info.get("profile_picture_url")
                existing_account.facebook_page_id = page_id
                existing_account.facebook_page_name = page_name
                existing_account.access_token = page_access_token
                existing_account.is_active = True
                existing_account.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(existing_account)
                return existing_account
            else:
                # 새로 생성
                new_account = models.InstagramAccount(
                    user_id=current_user.id,
                    instagram_business_account_id=ig_account_id,
                    username=ig_info.get("username", ""),
                    profile_picture_url=ig_info.get("profile_picture_url"),
                    facebook_page_id=page_id,
                    facebook_page_name=page_name,
                    access_token=page_access_token,
                    is_active=True
                )
                db.add(new_account)
                db.commit()
                db.refresh(new_account)
                return new_account

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API 요청 실패: {str(e)}"
        )


@router.get("/accounts", response_model=List[schemas.InstagramAccount])
async def get_instagram_accounts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    현재 사용자의 연동된 Instagram 계정 목록 가져오기
    """
    accounts = db.query(models.InstagramAccount).filter(
        models.InstagramAccount.user_id == current_user.id,
        models.InstagramAccount.is_active == True
    ).all()

    return accounts


@router.post("/publish", response_model=schemas.Post)
async def publish_to_instagram(
    request: schemas.InstagramPublishRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Instagram에 이미지 게시물 발행

    Instagram Graph API는 두 단계로 이루어집니다:
    1. 미디어 컨테이너 생성 (이미지 업로드)
    2. 컨테이너를 게시물로 발행
    """
    # 1. 연동된 Instagram 계정 가져오기
    ig_account = db.query(models.InstagramAccount).filter(
        models.InstagramAccount.user_id == current_user.id,
        models.InstagramAccount.is_active == True
    ).first()

    if not ig_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="연동된 Instagram 계정이 없습니다."
        )

    # 예약 발행인 경우
    if request.scheduled_time:
        scheduled_post = models.ScheduledPost(
            user_id=current_user.id,
            platform="instagram",
            content_type="image",
            caption=request.caption,
            media_url=request.image_url,
            scheduled_time=request.scheduled_time,
            status="pending"
        )
        db.add(scheduled_post)
        db.commit()
        db.refresh(scheduled_post)

        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="예약 발행이 등록되었습니다."
        )

    # 즉시 발행
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: 미디어 컨테이너 생성
            container_response = await client.post(
                f"{GRAPH_API_URL}/{ig_account.instagram_business_account_id}/media",
                data={
                    "image_url": request.image_url,
                    "caption": request.caption,
                    "access_token": ig_account.access_token
                }
            )

            if container_response.status_code != 200:
                error_data = container_response.json()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"미디어 컨테이너 생성 실패: {error_data.get('error', {}).get('message', 'Unknown error')}"
                )

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

                # 실패한 게시물 기록
                failed_post = models.Post(
                    user_id=current_user.id,
                    platform="instagram",
                    content_type="image",
                    caption=request.caption,
                    media_url=request.image_url,
                    status="failed",
                    error_message=error_data.get('error', {}).get('message', 'Unknown error')
                )
                db.add(failed_post)
                db.commit()

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"게시물 발행 실패: {error_data.get('error', {}).get('message', 'Unknown error')}"
                )

            publish_data = publish_response.json()
            post_id = publish_data.get("id")

            # 성공한 게시물 기록
            new_post = models.Post(
                user_id=current_user.id,
                platform="instagram",
                platform_post_id=post_id,
                content_type="image",
                caption=request.caption,
                media_url=request.image_url,
                status="published"
            )
            db.add(new_post)
            db.commit()
            db.refresh(new_post)

            return new_post

    except httpx.HTTPError as e:
        # 실패한 게시물 기록
        failed_post = models.Post(
            user_id=current_user.id,
            platform="instagram",
            content_type="image",
            caption=request.caption,
            media_url=request.image_url,
            status="failed",
            error_message=str(e)
        )
        db.add(failed_post)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API 요청 실패: {str(e)}"
        )


@router.get("/posts", response_model=List[schemas.Post])
async def get_posts(
    platform: str = "instagram",
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    발행된 게시물 이력 조회
    """
    posts = db.query(models.Post).filter(
        models.Post.user_id == current_user.id,
        models.Post.platform == platform
    ).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()

    return posts


@router.get("/scheduled", response_model=List[schemas.ScheduledPost])
async def get_scheduled_posts(
    platform: str = "instagram",
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    예약된 게시물 목록 조회
    """
    scheduled_posts = db.query(models.ScheduledPost).filter(
        models.ScheduledPost.user_id == current_user.id,
        models.ScheduledPost.platform == platform,
        models.ScheduledPost.status.in_(["pending", "processing"])
    ).order_by(models.ScheduledPost.scheduled_time).offset(skip).limit(limit).all()

    return scheduled_posts


@router.delete("/accounts/{account_id}")
async def disconnect_instagram_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Instagram 계정 연동 해제
    """
    account = db.query(models.InstagramAccount).filter(
        models.InstagramAccount.id == account_id,
        models.InstagramAccount.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="계정을 찾을 수 없습니다."
        )

    account.is_active = False
    db.commit()

    return {"message": "Instagram 계정 연동이 해제되었습니다."}
