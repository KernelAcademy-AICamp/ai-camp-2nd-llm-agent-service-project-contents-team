from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"]
)

# 참고: 일반 로그인/회원가입은 제거되었습니다.
# 모든 인증은 OAuth2.0 소셜 로그인을 통해 이루어집니다.
# OAuth 엔드포인트는 routers/oauth.py에 있습니다.


@router.post("/logout")
async def logout(current_user: models.User = Depends(auth.get_current_active_user)):
    """
    사용자 로그아웃을 처리합니다.

    참고: JWT는 stateless하므로 서버 측에서 토큰을 무효화할 수 없습니다.
    클라이언트 측에서 토큰을 삭제하여 로그아웃을 구현합니다.
    """
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    """
    현재 인증된 사용자 정보를 반환합니다.
    """
    return current_user


@router.put("/me", response_model=schemas.User)
async def update_user_me(
    user_update: schemas.UserBase,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    현재 사용자의 정보를 업데이트합니다.
    """
    # 이메일이 변경되었고 이미 사용 중인 경우 체크
    if user_update.email != current_user.email:
        existing_user = db.query(models.User).filter(
            models.User.email == user_update.email
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # 사용자명이 변경되었고 이미 사용 중인 경우 체크
    if user_update.username != current_user.username:
        existing_user = db.query(models.User).filter(
            models.User.username == user_update.username
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    current_user.email = user_update.email
    current_user.username = user_update.username
    current_user.full_name = user_update.full_name

    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/refresh-token")
async def refresh_token(current_user: models.User = Depends(auth.get_current_active_user)):
    """
    현재 토큰이 유효한 경우 새로운 액세스 토큰을 발급합니다.
    사용자 활동 감지 시 세션 연장에 사용됩니다.
    """
    new_token = auth.refresh_access_token(current_user)
    return {
        "access_token": new_token,
        "token_type": "bearer"
    }
