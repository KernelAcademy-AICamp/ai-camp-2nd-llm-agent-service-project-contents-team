from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/api/user",
    tags=["user"]
)


def build_user_context(
    user: models.User,
    preference: Optional[models.UserPreference],
    brand_analysis: Optional[models.BrandAnalysis]
) -> schemas.UserContext:
    """사용자 정보를 콘텐츠 생성용 컨텍스트로 통합"""
    return schemas.UserContext(
        # 기본 정보 (User 테이블)
        brand_name=user.brand_name,
        business_type=user.business_type,
        business_description=user.business_description,
        target_audience=user.target_audience,

        # 스타일 선호도 (UserPreference 테이블)
        text_tone=preference.text_tone if preference else None,
        text_style_sample=preference.text_style_sample if preference else None,
        image_style_description=preference.image_style_description if preference else None,
        image_color_palette=preference.image_color_palette if preference else None,

        # 브랜드 분석 결과 (BrandAnalysis 테이블)
        brand_tone=brand_analysis.brand_tone if brand_analysis else None,
        brand_personality=brand_analysis.brand_personality if brand_analysis else None,
        key_themes=brand_analysis.key_themes if brand_analysis else None,
        emotional_tone=brand_analysis.emotional_tone if brand_analysis else None,
        blog_writing_style=brand_analysis.blog_writing_style if brand_analysis else None,
        instagram_caption_style=brand_analysis.instagram_caption_style if brand_analysis else None,
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


@router.get("/context", response_model=schemas.UserProfileWithBrand)
async def get_user_context_for_content(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    콘텐츠 생성용 사용자 컨텍스트 조회
    - 사용자 기본 정보
    - 스타일 선호도
    - 브랜드 분석 결과
    - 통합된 컨텍스트 (AI 프롬프트용)
    """
    # 사용자 선호도 조회
    user_preference = db.query(models.UserPreference).filter(
        models.UserPreference.user_id == current_user.id
    ).first()

    # 브랜드 분석 결과 조회
    brand_analysis = db.query(models.BrandAnalysis).filter(
        models.BrandAnalysis.user_id == current_user.id
    ).first()

    # 콘텐츠 생성용 컨텍스트 빌드
    context = build_user_context(current_user, user_preference, brand_analysis)

    return schemas.UserProfileWithBrand(
        user=current_user,
        preferences=user_preference,
        brand_analysis=brand_analysis,
        context=context
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
