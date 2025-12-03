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


@router.put("/profile", response_model=schemas.UserProfile)
async def update_user_profile(
    update_data: schemas.ProfileUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자 프로필 정보 수정
    - 비즈니스 정보 (brand_name, business_type, business_description)
    - 타겟 고객 (target_audience)
    - 스타일 선호도 (preferences)
    """
    # 비즈니스 정보 업데이트
    if update_data.brand_name is not None:
        current_user.brand_name = update_data.brand_name
    if update_data.business_type is not None:
        current_user.business_type = update_data.business_type
    if update_data.business_description is not None:
        current_user.business_description = update_data.business_description

    # 타겟 고객 업데이트
    if update_data.target_audience is not None:
        current_user.target_audience = update_data.target_audience

    # 스타일 선호도 업데이트
    if update_data.preferences is not None:
        user_preference = db.query(models.UserPreference).filter(
            models.UserPreference.user_id == current_user.id
        ).first()

        if user_preference:
            # 기존 선호도 업데이트
            pref_data = update_data.preferences.model_dump(exclude_unset=True)
            for key, value in pref_data.items():
                if value is not None:
                    setattr(user_preference, key, value)
        else:
            # 새 선호도 생성
            pref_data = update_data.preferences.model_dump(exclude_unset=True)
            user_preference = models.UserPreference(
                user_id=current_user.id,
                **pref_data
            )
            db.add(user_preference)

    db.commit()
    db.refresh(current_user)

    # 업데이트된 프로필 반환
    user_preference = db.query(models.UserPreference).filter(
        models.UserPreference.user_id == current_user.id
    ).first()

    return schemas.UserProfile(
        user=current_user,
        preferences=user_preference
    )
