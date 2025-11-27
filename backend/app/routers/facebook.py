"""
Facebook API Router
- Facebook 페이지 연동/해제
- 게시물 목록 조회/생성
- 인사이트 조회
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os

from .. import models, auth
from ..database import get_db
from ..oauth import oauth
from ..services.facebook_service import FacebookService, sync_facebook_posts
from ..logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/facebook",
    tags=["facebook"]
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
FACEBOOK_APP_ID = os.getenv("FACEBOOK_CLIENT_ID", "")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET", "")


# ===== Pydantic Schemas =====

class FacebookConnectionResponse(BaseModel):
    id: int
    facebook_user_id: str
    facebook_user_name: Optional[str]
    page_id: Optional[str]
    page_name: Optional[str]
    page_category: Optional[str]
    page_picture_url: Optional[str]
    page_fan_count: Optional[int]
    page_followers_count: Optional[int]
    is_active: bool
    last_synced_at: Optional[datetime]

    class Config:
        from_attributes = True


class FacebookPostResponse(BaseModel):
    id: int
    post_id: str
    message: Optional[str]
    story: Optional[str]
    full_picture: Optional[str]
    permalink_url: Optional[str]
    post_type: Optional[str]
    created_time: Optional[datetime]
    is_published: bool
    likes_count: int
    comments_count: int
    shares_count: int

    class Config:
        from_attributes = True


class CreatePostRequest(BaseModel):
    message: str
    link: Optional[str] = None
    published: Optional[bool] = True


class CreatePhotoPostRequest(BaseModel):
    photo_url: str
    caption: Optional[str] = None
    published: Optional[bool] = True


class FacebookPageInfo(BaseModel):
    id: str
    name: str
    category: Optional[str]
    picture_url: Optional[str]
    fan_count: Optional[int]
    followers_count: Optional[int]
    access_token: str


# ===== OAuth 연동 엔드포인트 =====

@router.get('/connect')
async def facebook_connect(
    request: Request,
    user_id: int = None
):
    """Facebook 페이지 연동 시작 (OAuth)"""
    # 명시적으로 redirect_uri 설정 (authlib이 올바른 URI를 사용하도록)
    redirect_uri = os.getenv('FACEBOOK_PAGES_REDIRECT_URI', 'http://localhost:8000/api/facebook/callback')
    logger.info(f"Facebook connect - redirect_uri: {redirect_uri}")
    # user_id를 세션에 저장
    if user_id:
        request.session['facebook_connect_user_id'] = user_id
        logger.info(f"Storing user_id in session: {user_id}")
    return await oauth.facebook_pages.authorize_redirect(request, redirect_uri)


@router.get('/callback')
async def facebook_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """Facebook OAuth 콜백 처리"""
    logger.info(f"Facebook callback received: {request.url}")
    try:
        logger.info("Attempting to authorize access token...")
        token = await oauth.facebook_pages.authorize_access_token(request)
        logger.info(f"Token received: {list(token.keys())}")

        access_token = token['access_token']

        # 세션에서 user_id 가져오기
        user_id = request.session.get('facebook_connect_user_id')
        logger.info(f"User ID from session: {user_id}")

        if not user_id:
            logger.error("User ID not found in session")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/settings?error=user_not_found"
            )

        # 세션에서 제거
        request.session.pop('facebook_connect_user_id', None)

        # 사용자 찾기
        user = db.query(models.User).filter(
            models.User.id == user_id
        ).first()

        if not user:
            logger.error(f"User not found for id: {user_id}")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/settings?error=user_not_found"
            )

        logger.info(f"Found user: {user.id}")

        # Facebook 서비스 초기화
        fb_service = FacebookService(access_token)

        # 사용자 정보 가져오기
        me = await fb_service.get_me()
        if not me:
            logger.error("Failed to get Facebook user info")
            await fb_service.close()
            return RedirectResponse(
                url=f"{FRONTEND_URL}/settings?error=facebook_api_error"
            )

        logger.info(f"Facebook user: {me}")

        # 관리하는 페이지 목록 가져오기
        pages = await fb_service.get_my_pages()
        logger.info(f"User pages: {pages}")

        await fb_service.close()

        # 기존 연동 확인
        existing = db.query(models.FacebookConnection).filter(
            models.FacebookConnection.user_id == user.id
        ).first()

        # 페이지 정보 (첫 번째 페이지 사용, 또는 페이지 선택 UI 필요)
        page_data = pages[0] if pages else None

        # 페이지 목록을 캐싱용으로 변환
        cached_pages = None
        if pages:
            cached_pages = [
                {
                    'id': p['id'],
                    'name': p.get('name', ''),
                    'category': p.get('category'),
                    'picture_url': p.get('picture', {}).get('data', {}).get('url'),
                    'fan_count': p.get('fan_count'),
                    'followers_count': p.get('followers_count'),
                    'access_token': p.get('access_token', '')
                }
                for p in pages
            ]

        if existing:
            # 업데이트
            existing.facebook_user_id = me['id']
            existing.facebook_user_name = me.get('name')
            existing.user_access_token = access_token
            existing.is_active = True
            existing.available_pages = cached_pages  # 페이지 목록 캐싱

            if page_data:
                existing.page_id = page_data['id']
                existing.page_name = page_data.get('name')
                existing.page_category = page_data.get('category')
                existing.page_picture_url = page_data.get('picture', {}).get('data', {}).get('url')
                existing.page_fan_count = page_data.get('fan_count')
                existing.page_followers_count = page_data.get('followers_count')
                existing.page_access_token = page_data.get('access_token')
        else:
            # 새로 생성
            connection = models.FacebookConnection(
                user_id=user.id,
                facebook_user_id=me['id'],
                facebook_user_name=me.get('name'),
                user_access_token=access_token,
                is_active=True,
                available_pages=cached_pages  # 페이지 목록 캐싱
            )

            if page_data:
                connection.page_id = page_data['id']
                connection.page_name = page_data.get('name')
                connection.page_category = page_data.get('category')
                connection.page_picture_url = page_data.get('picture', {}).get('data', {}).get('url')
                connection.page_fan_count = page_data.get('fan_count')
                connection.page_followers_count = page_data.get('followers_count')
                connection.page_access_token = page_data.get('access_token')

            db.add(connection)

        db.commit()

        return RedirectResponse(
            url=f"{FRONTEND_URL}/facebook?connected=true"
        )

    except Exception as e:
        import traceback
        logger.error(f"Facebook OAuth error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/settings?error=facebook_oauth_failed"
        )


@router.delete('/disconnect')
async def facebook_disconnect(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Facebook 연동 해제"""
    connection = db.query(models.FacebookConnection).filter(
        models.FacebookConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Facebook connection not found")

    db.delete(connection)
    db.commit()

    return {"message": "Facebook disconnected successfully"}


# ===== 연동 상태 확인 =====

@router.get('/status', response_model=Optional[FacebookConnectionResponse])
async def get_facebook_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Facebook 연동 상태 확인"""
    connection = db.query(models.FacebookConnection).filter(
        models.FacebookConnection.user_id == current_user.id
    ).first()

    return connection


@router.get('/pages', response_model=List[FacebookPageInfo])
async def get_my_pages(
    refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """사용자가 관리하는 Facebook 페이지 목록 (캐시 우선)"""
    logger.info(f"Getting pages for user: {current_user.id}, refresh: {refresh}")

    connection = db.query(models.FacebookConnection).filter(
        models.FacebookConnection.user_id == current_user.id
    ).first()

    if not connection:
        logger.error(f"No Facebook connection found for user: {current_user.id}")
        raise HTTPException(status_code=404, detail="Facebook not connected")

    # 캐시된 페이지가 있고 refresh가 아니면 바로 반환
    if not refresh and connection.available_pages:
        logger.info(f"Returning cached pages: {len(connection.available_pages)} pages")
        return [
            FacebookPageInfo(
                id=p['id'],
                name=p.get('name', ''),
                category=p.get('category'),
                picture_url=p.get('picture_url'),
                fan_count=p.get('fan_count'),
                followers_count=p.get('followers_count'),
                access_token=p.get('access_token', '')
            )
            for p in connection.available_pages
        ]

    # 캐시가 없거나 refresh 요청이면 API 호출
    logger.info(f"Fetching pages from Facebook API")
    fb_service = FacebookService(connection.user_access_token)
    pages = await fb_service.get_my_pages()
    await fb_service.close()

    logger.info(f"Pages from Facebook API: {pages}")

    if not pages:
        logger.warning("No pages returned from Facebook API")
        return []

    # 캐시 업데이트
    connection.available_pages = [
        {
            'id': p['id'],
            'name': p.get('name', ''),
            'category': p.get('category'),
            'picture_url': p.get('picture', {}).get('data', {}).get('url'),
            'fan_count': p.get('fan_count'),
            'followers_count': p.get('followers_count'),
            'access_token': p.get('access_token', '')
        }
        for p in pages
    ]
    db.commit()

    return [
        FacebookPageInfo(
            id=p['id'],
            name=p.get('name', ''),
            category=p.get('category'),
            picture_url=p.get('picture', {}).get('data', {}).get('url'),
            fan_count=p.get('fan_count'),
            followers_count=p.get('followers_count'),
            access_token=p.get('access_token', '')
        )
        for p in pages
    ]


@router.post('/select-page/{page_id}')
async def select_page(
    page_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """연동할 페이지 선택"""
    connection = db.query(models.FacebookConnection).filter(
        models.FacebookConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Facebook not connected")

    fb_service = FacebookService(connection.user_access_token)
    pages = await fb_service.get_my_pages()
    await fb_service.close()

    if not pages:
        raise HTTPException(status_code=404, detail="No pages found")

    # 선택한 페이지 찾기
    selected_page = next((p for p in pages if p['id'] == page_id), None)

    if not selected_page:
        raise HTTPException(status_code=404, detail="Page not found")

    # 페이지 정보 업데이트
    connection.page_id = selected_page['id']
    connection.page_name = selected_page.get('name')
    connection.page_category = selected_page.get('category')
    connection.page_picture_url = selected_page.get('picture', {}).get('data', {}).get('url')
    connection.page_fan_count = selected_page.get('fan_count')
    connection.page_followers_count = selected_page.get('followers_count')
    connection.page_access_token = selected_page.get('access_token')

    db.commit()
    db.refresh(connection)

    return {"message": "Page selected successfully", "page_name": connection.page_name}


# ===== 게시물 관리 =====

@router.get('/posts', response_model=List[FacebookPostResponse])
async def get_posts(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """페이지 게시물 목록 조회"""
    connection = db.query(models.FacebookConnection).filter(
        models.FacebookConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Facebook not connected")

    posts = db.query(models.FacebookPost).filter(
        models.FacebookPost.connection_id == connection.id
    ).order_by(
        models.FacebookPost.created_time.desc()
    ).offset(skip).limit(limit).all()

    return posts


@router.post('/posts/sync')
async def sync_posts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Facebook에서 게시물 동기화"""
    connection = db.query(models.FacebookConnection).filter(
        models.FacebookConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Facebook not connected")

    if not connection.page_id:
        raise HTTPException(status_code=400, detail="No page selected")

    fb_service = FacebookService(
        connection.user_access_token,
        connection.page_access_token
    )

    synced_count = await sync_facebook_posts(
        fb_service,
        connection.page_id,
        connection.id,
        current_user.id,
        db
    )

    # 마지막 동기화 시간 업데이트
    connection.last_synced_at = datetime.utcnow()
    db.commit()

    await fb_service.close()

    return {"message": "Posts synced successfully", "synced_count": synced_count}


@router.post('/posts/create')
async def create_post(
    request: CreatePostRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """페이지에 게시물 작성"""
    connection = db.query(models.FacebookConnection).filter(
        models.FacebookConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Facebook not connected")

    if not connection.page_id:
        raise HTTPException(status_code=400, detail="No page selected")

    fb_service = FacebookService(
        connection.user_access_token,
        connection.page_access_token
    )

    result = await fb_service.create_post(
        connection.page_id,
        request.message,
        request.link,
        request.published
    )

    await fb_service.close()

    if not result:
        raise HTTPException(status_code=500, detail="Failed to create post")

    return {"message": "Post created successfully", "post_id": result.get('id')}


@router.post('/posts/create-photo')
async def create_photo_post(
    request: CreatePhotoPostRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """페이지에 사진 게시물 작성"""
    connection = db.query(models.FacebookConnection).filter(
        models.FacebookConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Facebook not connected")

    if not connection.page_id:
        raise HTTPException(status_code=400, detail="No page selected")

    fb_service = FacebookService(
        connection.user_access_token,
        connection.page_access_token
    )

    result = await fb_service.create_photo_post(
        connection.page_id,
        request.photo_url,
        request.caption,
        request.published
    )

    await fb_service.close()

    if not result:
        raise HTTPException(status_code=500, detail="Failed to create photo post")

    return {"message": "Photo post created successfully", "post_id": result.get('id')}


@router.delete('/posts/{post_id}')
async def delete_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """게시물 삭제"""
    connection = db.query(models.FacebookConnection).filter(
        models.FacebookConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Facebook not connected")

    fb_service = FacebookService(
        connection.user_access_token,
        connection.page_access_token
    )

    success = await fb_service.delete_post(post_id)
    await fb_service.close()

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete post")

    # DB에서도 삭제
    db.query(models.FacebookPost).filter(
        models.FacebookPost.post_id == post_id
    ).delete()
    db.commit()

    return {"message": "Post deleted successfully"}


# ===== 인사이트 =====

@router.get('/insights')
async def get_page_insights(
    period: str = 'day',
    date_preset: str = 'last_30d',
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """페이지 인사이트 조회"""
    connection = db.query(models.FacebookConnection).filter(
        models.FacebookConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Facebook not connected")

    if not connection.page_id:
        raise HTTPException(status_code=400, detail="No page selected")

    fb_service = FacebookService(
        connection.user_access_token,
        connection.page_access_token
    )

    insights = await fb_service.get_page_insights(
        connection.page_id,
        period=period,
        date_preset=date_preset
    )

    await fb_service.close()

    return insights or {"data": []}


@router.post('/refresh-page')
async def refresh_page_info(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """페이지 정보 새로고침"""
    connection = db.query(models.FacebookConnection).filter(
        models.FacebookConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Facebook not connected")

    if not connection.page_id:
        raise HTTPException(status_code=400, detail="No page selected")

    fb_service = FacebookService(
        connection.user_access_token,
        connection.page_access_token
    )

    page_info = await fb_service.get_page_info(connection.page_id)
    await fb_service.close()

    if page_info:
        connection.page_name = page_info.get('name')
        connection.page_category = page_info.get('category')
        connection.page_fan_count = page_info.get('fan_count')
        connection.page_followers_count = page_info.get('followers_count')
        connection.page_picture_url = page_info.get('picture', {}).get('data', {}).get('url')
        connection.last_synced_at = datetime.utcnow()
        db.commit()

    return {"message": "Page info refreshed successfully"}
