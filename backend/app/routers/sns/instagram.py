"""
Instagram API Router
- Instagram 비즈니스 계정 연동/해제
- 게시물 목록 조회/생성
- 인사이트 조회
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os

from ... import models, auth
from ...database import get_db
from ...oauth import oauth
from ...services.instagram_service import InstagramService, sync_instagram_posts
from ...services.facebook_service import FacebookService
from ...logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/instagram",
    tags=["instagram"]
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


# ===== Pydantic Schemas =====

class InstagramConnectionResponse(BaseModel):
    id: int
    instagram_account_id: Optional[str]
    instagram_username: Optional[str]
    instagram_name: Optional[str]
    instagram_profile_picture_url: Optional[str]
    instagram_biography: Optional[str]
    followers_count: Optional[int] = 0
    follows_count: Optional[int] = 0
    media_count: Optional[int] = 0
    page_id: Optional[str]
    page_name: Optional[str]
    is_active: bool
    last_synced_at: Optional[datetime]

    class Config:
        from_attributes = True


class InstagramPostResponse(BaseModel):
    id: int
    media_id: str
    media_type: Optional[str]
    media_url: Optional[str]
    thumbnail_url: Optional[str]
    permalink: Optional[str]
    caption: Optional[str]
    timestamp: Optional[datetime]
    like_count: int
    comments_count: int

    class Config:
        from_attributes = True


class InstagramAccountInfo(BaseModel):
    id: str
    username: Optional[str]
    name: Optional[str]
    profile_picture_url: Optional[str]
    followers_count: Optional[int]
    follows_count: Optional[int]
    media_count: Optional[int]
    facebook_page_id: str
    facebook_page_name: Optional[str]


# ===== OAuth 연동 엔드포인트 =====

@router.get('/connect')
async def instagram_connect(
    request: Request,
    user_id: int = None
):
    """Instagram 비즈니스 계정 연동 시작 (Facebook OAuth 사용)"""
    redirect_uri = os.getenv('INSTAGRAM_REDIRECT_URI', 'http://localhost:8000/api/instagram/callback')
    logger.info(f"Instagram connect - redirect_uri: {redirect_uri}")

    if user_id:
        request.session['instagram_connect_user_id'] = user_id
        logger.info(f"Storing user_id in session: {user_id}")

    return await oauth.instagram.authorize_redirect(request, redirect_uri)


@router.get('/callback')
async def instagram_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """Instagram OAuth 콜백 처리"""
    logger.info(f"Instagram callback received: {request.url}")
    try:
        token = await oauth.instagram.authorize_access_token(request)
        logger.info(f"Token received: {list(token.keys())}")

        access_token = token['access_token']

        # 세션에서 user_id 가져오기
        user_id = request.session.get('instagram_connect_user_id')
        logger.info(f"User ID from session: {user_id}")

        if not user_id:
            logger.error("User ID not found in session")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/settings?error=user_not_found"
            )

        request.session.pop('instagram_connect_user_id', None)

        # 사용자 찾기
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            logger.error(f"User not found for id: {user_id}")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/settings?error=user_not_found"
            )

        # Facebook 서비스로 페이지 목록 가져오기
        fb_service = FacebookService(access_token)
        pages = await fb_service.get_my_pages()
        logger.info(f"User pages: {pages}")

        if not pages:
            await fb_service.close()
            return RedirectResponse(
                url=f"{FRONTEND_URL}/instagram?error=no_pages"
            )

        # Instagram 서비스로 연결된 Instagram 계정 조회
        ig_service = InstagramService(access_token)
        instagram_accounts = await ig_service.get_instagram_accounts_from_pages(pages)
        logger.info(f"Instagram accounts: {instagram_accounts}")

        await fb_service.close()
        await ig_service.close()

        if not instagram_accounts:
            return RedirectResponse(
                url=f"{FRONTEND_URL}/instagram?error=no_instagram_account"
            )

        # 기존 연동 확인
        existing = db.query(models.InstagramConnection).filter(
            models.InstagramConnection.user_id == user.id
        ).first()

        # 첫 번째 Instagram 계정 사용 (또는 선택 UI 필요)
        ig_data = instagram_accounts[0]

        # 캐싱용 계정 목록 변환
        cached_accounts = [
            {
                'id': acc.get('id'),
                'username': acc.get('username'),
                'name': acc.get('name'),
                'profile_picture_url': acc.get('profile_picture_url'),
                'followers_count': acc.get('followers_count'),
                'follows_count': acc.get('follows_count'),
                'media_count': acc.get('media_count'),
                'facebook_page_id': acc.get('facebook_page_id'),
                'facebook_page_name': acc.get('facebook_page_name'),
                'page_access_token': acc.get('page_access_token')
            }
            for acc in instagram_accounts
        ]

        if existing:
            # 업데이트
            existing.instagram_account_id = ig_data['id']
            existing.instagram_username = ig_data.get('username')
            existing.instagram_name = ig_data.get('name')
            existing.instagram_profile_picture_url = ig_data.get('profile_picture_url')
            existing.instagram_biography = ig_data.get('biography')
            existing.instagram_website = ig_data.get('website')
            existing.followers_count = ig_data.get('followers_count', 0)
            existing.follows_count = ig_data.get('follows_count', 0)
            existing.media_count = ig_data.get('media_count', 0)
            existing.page_id = ig_data.get('facebook_page_id')
            existing.page_name = ig_data.get('facebook_page_name')
            existing.user_access_token = access_token
            existing.page_access_token = ig_data.get('page_access_token')
            existing.is_active = True
        else:
            # 새로 생성
            connection = models.InstagramConnection(
                user_id=user.id,
                instagram_account_id=ig_data['id'],
                instagram_username=ig_data.get('username'),
                instagram_name=ig_data.get('name'),
                instagram_profile_picture_url=ig_data.get('profile_picture_url'),
                instagram_biography=ig_data.get('biography'),
                instagram_website=ig_data.get('website'),
                followers_count=ig_data.get('followers_count', 0),
                follows_count=ig_data.get('follows_count', 0),
                media_count=ig_data.get('media_count', 0),
                page_id=ig_data.get('facebook_page_id'),
                page_name=ig_data.get('facebook_page_name'),
                user_access_token=access_token,
                page_access_token=ig_data.get('page_access_token'),
                is_active=True
            )
            db.add(connection)

        db.commit()

        return RedirectResponse(
            url=f"{FRONTEND_URL}/instagram?connected=true"
        )

    except Exception as e:
        import traceback
        logger.error(f"Instagram OAuth error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/settings?error=instagram_oauth_failed"
        )


@router.delete('/disconnect')
async def instagram_disconnect(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Instagram 연동 해제"""
    connection = db.query(models.InstagramConnection).filter(
        models.InstagramConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Instagram connection not found")

    db.delete(connection)
    db.commit()

    return {"message": "Instagram disconnected successfully"}


# ===== 연동 상태 확인 =====

@router.get('/status', response_model=Optional[InstagramConnectionResponse])
async def get_instagram_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Instagram 연동 상태 확인"""
    connection = db.query(models.InstagramConnection).filter(
        models.InstagramConnection.user_id == current_user.id
    ).first()

    return connection


@router.get('/accounts', response_model=List[InstagramAccountInfo])
async def get_instagram_accounts(
    refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """연결 가능한 Instagram 계정 목록 (캐시 우선)"""
    connection = db.query(models.InstagramConnection).filter(
        models.InstagramConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Instagram not connected")

    # 새로 조회
    fb_service = FacebookService(connection.user_access_token or connection.page_access_token)
    pages = await fb_service.get_my_pages()

    if not pages:
        await fb_service.close()
        return []

    ig_service = InstagramService(connection.user_access_token or connection.page_access_token)
    instagram_accounts = await ig_service.get_instagram_accounts_from_pages(pages)

    await fb_service.close()
    await ig_service.close()

    return [
        InstagramAccountInfo(
            id=acc['id'],
            username=acc.get('username'),
            name=acc.get('name'),
            profile_picture_url=acc.get('profile_picture_url'),
            followers_count=acc.get('followers_count'),
            follows_count=acc.get('follows_count'),
            media_count=acc.get('media_count'),
            facebook_page_id=acc.get('facebook_page_id', ''),
            facebook_page_name=acc.get('facebook_page_name')
        )
        for acc in instagram_accounts
    ]


@router.post('/select-account/{instagram_user_id}')
async def select_account(
    instagram_user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """연동할 Instagram 계정 선택"""
    connection = db.query(models.InstagramConnection).filter(
        models.InstagramConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Instagram not connected")

    # 새로 조회해서 선택한 계정 찾기
    fb_service = FacebookService(connection.user_access_token or connection.page_access_token)
    pages = await fb_service.get_my_pages()

    if not pages:
        await fb_service.close()
        raise HTTPException(status_code=404, detail="No pages available")

    ig_service = InstagramService(connection.user_access_token or connection.page_access_token)
    instagram_accounts = await ig_service.get_instagram_accounts_from_pages(pages)

    await fb_service.close()
    await ig_service.close()

    # 선택한 계정 찾기
    selected = next(
        (acc for acc in instagram_accounts if acc['id'] == instagram_user_id),
        None
    )

    if not selected:
        raise HTTPException(status_code=404, detail="Account not found")

    # 계정 정보 업데이트
    connection.instagram_account_id = selected['id']
    connection.instagram_username = selected.get('username')
    connection.instagram_name = selected.get('name')
    connection.instagram_profile_picture_url = selected.get('profile_picture_url')
    connection.followers_count = selected.get('followers_count', 0)
    connection.follows_count = selected.get('follows_count', 0)
    connection.media_count = selected.get('media_count', 0)
    connection.page_id = selected.get('facebook_page_id')
    connection.page_name = selected.get('facebook_page_name')
    connection.page_access_token = selected.get('page_access_token')

    db.commit()
    db.refresh(connection)

    return {"message": "Account selected successfully", "username": connection.instagram_username}


# ===== 게시물 관리 =====

@router.get('/posts', response_model=List[InstagramPostResponse])
async def get_posts(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Instagram 게시물 목록 조회"""
    connection = db.query(models.InstagramConnection).filter(
        models.InstagramConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Instagram not connected")

    posts = db.query(models.InstagramPost).filter(
        models.InstagramPost.connection_id == connection.id
    ).order_by(
        models.InstagramPost.timestamp.desc()
    ).offset(skip).limit(limit).all()

    return posts


@router.post('/posts/sync')
async def sync_posts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Instagram에서 게시물 동기화"""
    connection = db.query(models.InstagramConnection).filter(
        models.InstagramConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Instagram not connected")

    if not connection.instagram_account_id:
        raise HTTPException(status_code=400, detail="Instagram account not selected")

    ig_service = InstagramService(connection.page_access_token)

    synced_count = await sync_instagram_posts(
        ig_service,
        connection.instagram_account_id,
        connection.id,
        current_user.id,
        db
    )

    # 계정 정보도 함께 업데이트 (media_count 등)
    account_info = await ig_service.get_account_info(connection.instagram_account_id)
    if account_info:
        connection.followers_count = account_info.get('followers_count', 0)
        connection.follows_count = account_info.get('follows_count', 0)
        connection.media_count = account_info.get('media_count', 0)

    connection.last_synced_at = datetime.utcnow()
    db.commit()

    await ig_service.close()

    return {"message": "Posts synced successfully", "synced_count": synced_count}


# ===== 인사이트 =====

@router.get('/insights')
async def get_account_insights(
    period: str = 'day',
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Instagram 계정 인사이트 조회"""
    connection = db.query(models.InstagramConnection).filter(
        models.InstagramConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Instagram not connected")

    if not connection.instagram_account_id:
        raise HTTPException(status_code=400, detail="Instagram account not selected")

    ig_service = InstagramService(connection.page_access_token)
    insights = await ig_service.get_account_insights(
        connection.instagram_account_id,
        period=period
    )
    await ig_service.close()

    return insights or {"data": []}


@router.post('/refresh')
async def refresh_account_info(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Instagram 계정 정보 새로고침"""
    connection = db.query(models.InstagramConnection).filter(
        models.InstagramConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Instagram not connected")

    if not connection.instagram_account_id:
        raise HTTPException(status_code=400, detail="Instagram account not selected")

    ig_service = InstagramService(connection.page_access_token)
    account_info = await ig_service.get_account_info(connection.instagram_account_id)
    await ig_service.close()

    if account_info:
        connection.instagram_username = account_info.get('username')
        connection.instagram_name = account_info.get('name')
        connection.instagram_profile_picture_url = account_info.get('profile_picture_url')
        connection.instagram_biography = account_info.get('biography')
        connection.instagram_website = account_info.get('website')
        connection.followers_count = account_info.get('followers_count', 0)
        connection.follows_count = account_info.get('follows_count', 0)
        connection.media_count = account_info.get('media_count', 0)
        connection.last_synced_at = datetime.utcnow()
        db.commit()

    return {"message": "Account info refreshed successfully"}
