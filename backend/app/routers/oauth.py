from datetime import timedelta
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx

from .. import models, auth
from ..database import get_db
from ..oauth import oauth
from .credits import grant_signup_bonus

router = APIRouter(
    prefix="/api/oauth",
    tags=["oauth"]
)

# 프론트엔드 URL (프로덕션 배포 시 환경 변수로 설정 권장)
FRONTEND_URL = "http://localhost:3000"


async def get_or_create_user(
    db: Session,
    email: str,
    username: str,
    full_name: str,
    oauth_provider: str,
    oauth_id: str,
    profile_image: str = None
) -> models.User:
    """
    OAuth 사용자 정보로 사용자를 찾거나 생성합니다.
    """
    # OAuth ID로 찾기
    user = db.query(models.User).filter(
        models.User.oauth_provider == oauth_provider,
        models.User.oauth_id == oauth_id
    ).first()

    if user:
        # 기존 사용자 정보 업데이트
        user.email = email
        user.full_name = full_name
        if profile_image:
            user.profile_image = profile_image
        db.commit()
        db.refresh(user)
        return user

    # 새 사용자 생성
    # username이 중복될 수 있으므로 고유한 username 생성
    base_username = username
    counter = 1
    while db.query(models.User).filter(models.User.username == username).first():
        username = f"{base_username}_{counter}"
        counter += 1

    user = models.User(
        email=email,
        username=username,
        full_name=full_name,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        profile_image=profile_image
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 신규 사용자에게 회원가입 보너스 크레딧 지급
    grant_signup_bonus(db, user.id)

    return user


# Google OAuth
@router.get('/google/login')
async def google_login(request: Request):
    """Google OAuth 로그인 시작"""
    redirect_uri = request.url_for('google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get('/google/callback')
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Google OAuth 콜백"""
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')

        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")

        user = await get_or_create_user(
            db=db,
            email=user_info['email'],
            username=user_info.get('name', user_info['email'].split('@')[0]),
            full_name=user_info.get('name', ''),
            oauth_provider='google',
            oauth_id=user_info['sub'],
            profile_image=user_info.get('picture')
        )

        # JWT 토큰 생성
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        # 프론트엔드로 리다이렉트 (토큰 포함)
        return RedirectResponse(
            url=f"{FRONTEND_URL}/oauth/callback?token={access_token}&provider=google"
        )

    except Exception as e:
        import traceback
        print(f"Google OAuth error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=oauth_failed")


# Kakao OAuth
@router.get('/kakao/login')
async def kakao_login(request: Request):
    """Kakao OAuth 로그인 시작"""
    redirect_uri = request.url_for('kakao_callback')
    return await oauth.kakao.authorize_redirect(request, redirect_uri)


@router.get('/kakao/callback')
async def kakao_callback(request: Request, db: Session = Depends(get_db)):
    """Kakao OAuth 콜백"""
    try:
        token = await oauth.kakao.authorize_access_token(request)

        # Kakao 사용자 정보 가져오기
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://kapi.kakao.com/v2/user/me',
                headers={'Authorization': f"Bearer {token['access_token']}"}
            )
            user_info = response.json()

        kakao_account = user_info.get('kakao_account', {})
        profile = kakao_account.get('profile', {})

        email = kakao_account.get('email')
        if not email:
            # 이메일이 없는 경우 임시 이메일 생성
            email = f"kakao_{user_info['id']}@kakao.local"

        user = await get_or_create_user(
            db=db,
            email=email,
            username=profile.get('nickname', f"kakao_user_{user_info['id']}"),
            full_name=profile.get('nickname', ''),
            oauth_provider='kakao',
            oauth_id=str(user_info['id']),
            profile_image=profile.get('profile_image_url')
        )

        # JWT 토큰 생성
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        return RedirectResponse(
            url=f"{FRONTEND_URL}/oauth/callback?token={access_token}&provider=kakao"
        )

    except Exception as e:
        import traceback
        print(f"Kakao OAuth error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=oauth_failed")


# Facebook OAuth
@router.get('/facebook/login')
async def facebook_login(request: Request):
    """Facebook OAuth 로그인 시작"""
    redirect_uri = request.url_for('facebook_callback')
    return await oauth.facebook.authorize_redirect(request, redirect_uri)


@router.get('/facebook/callback')
async def facebook_callback(request: Request, db: Session = Depends(get_db)):
    """Facebook OAuth 콜백"""
    try:
        token = await oauth.facebook.authorize_access_token(request)

        # Facebook 사용자 정보 가져오기
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://graph.facebook.com/me',
                params={
                    'fields': 'id,name,email,picture',
                    'access_token': token['access_token']
                }
            )
            user_info = response.json()

        email = user_info.get('email')
        if not email:
            # 이메일이 없는 경우 임시 이메일 생성
            email = f"facebook_{user_info['id']}@facebook.local"

        user = await get_or_create_user(
            db=db,
            email=email,
            username=user_info.get('name', f"fb_user_{user_info['id']}"),
            full_name=user_info.get('name', ''),
            oauth_provider='facebook',
            oauth_id=user_info['id'],
            profile_image=user_info.get('picture', {}).get('data', {}).get('url')
        )

        # JWT 토큰 생성
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        return RedirectResponse(
            url=f"{FRONTEND_URL}/oauth/callback?token={access_token}&provider=facebook"
        )

    except Exception as e:
        import traceback
        print(f"Facebook OAuth error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=oauth_failed")
