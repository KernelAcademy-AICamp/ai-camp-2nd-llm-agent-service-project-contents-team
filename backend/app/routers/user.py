from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/api/user",
    tags=["user"]
)


@router.get("/profile", response_model=schemas.UserProfile)
async def get_user_profile(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 사용자의 프로필 정보 조회
    - 사용자 기본 정보 (이메일, 이름, 브랜드명, 비즈니스 정보 등)
    - 사용자 선호도 정보 (텍스트/이미지/비디오 스타일 샘플)
    """
    # 사용자 선호도 조회
    user_preference = db.query(models.UserPreference).filter(
        models.UserPreference.user_id == current_user.id
    ).first()

    return schemas.UserProfile(
        user=current_user,
        preferences=user_preference
    )


@router.get("/me", response_model=schemas.User)
async def get_current_user_info(
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    현재 로그인한 사용자의 기본 정보만 조회
    """
    return current_user
