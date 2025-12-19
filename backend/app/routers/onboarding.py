from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
import cloudinary
import cloudinary.uploader
from .. import models, schemas, auth
from ..database import get_db
import os
import json

router = APIRouter(
    prefix="/api/onboarding",
    tags=["onboarding"]
)

# Cloudinary 설정
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


@router.put("/business-info")
async def update_business_info(
    onboarding_data: schemas.UserOnboardingUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    비즈니스 정보 업데이트 (온보딩 1단계)
    """
    # User 정보 업데이트
    if onboarding_data.brand_name is not None:
        current_user.brand_name = onboarding_data.brand_name
    if onboarding_data.business_type is not None:
        current_user.business_type = onboarding_data.business_type
    if onboarding_data.business_description is not None:
        current_user.business_description = onboarding_data.business_description
    if onboarding_data.target_audience is not None:
        current_user.target_audience = onboarding_data.target_audience

    # ✅ BrandAnalysis 테이블도 함께 업데이트
    brand_analysis = db.query(models.BrandAnalysis).filter(
        models.BrandAnalysis.user_id == current_user.id
    ).first()

    if brand_analysis:
        # 기존 레코드 업데이트
        if onboarding_data.brand_name is not None:
            brand_analysis.brand_name = onboarding_data.brand_name
        if onboarding_data.business_type is not None:
            # business_type을 업종명으로 변환 (예: 'food' -> '베이커리 / 카페')
            business_type_map = {
                'food': '음식 / 카페',
                'tech': 'IT / 기술',
                'fashion': '패션 / 뷰티',
                'education': '교육',
                'health': '건강 / 의료'
            }
            brand_analysis.business_type = business_type_map.get(
                onboarding_data.business_type,
                onboarding_data.business_type
            )
    else:
        # 새 레코드 생성
        business_type_map = {
            'food': '음식 / 카페',
            'tech': 'IT / 기술',
            'fashion': '패션 / 뷰티',
            'education': '교육',
            'health': '건강 / 의료'
        }
        brand_analysis = models.BrandAnalysis(
            user_id=current_user.id,
            brand_name=onboarding_data.brand_name,
            business_type=business_type_map.get(
                onboarding_data.business_type,
                onboarding_data.business_type
            ) if onboarding_data.business_type else None
        )
        db.add(brand_analysis)

    db.commit()
    db.refresh(current_user)

    return {
        "message": "비즈니스 정보가 업데이트되었습니다.",
        "user": current_user
    }


@router.post("/preferences")
async def create_or_update_preferences(
    preference_data: schemas.UserPreferenceCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자 선호도 생성 또는 업데이트 (온보딩 2단계 - 텍스트 부분)
    """
    # 기존 선호도 확인
    preference = db.query(models.UserPreference).filter(
        models.UserPreference.user_id == current_user.id
    ).first()

    if preference:
        # 업데이트
        if preference_data.text_style_sample is not None:
            preference.text_style_sample = preference_data.text_style_sample
        if preference_data.text_tone is not None:
            preference.text_tone = preference_data.text_tone
        if preference_data.image_style_description is not None:
            preference.image_style_description = preference_data.image_style_description
        if preference_data.image_color_palette is not None:
            preference.image_color_palette = preference_data.image_color_palette
        if preference_data.video_style_description is not None:
            preference.video_style_description = preference_data.video_style_description
        if preference_data.video_duration_preference is not None:
            preference.video_duration_preference = preference_data.video_duration_preference
    else:
        # 생성
        preference = models.UserPreference(
            user_id=current_user.id,
            text_style_sample=preference_data.text_style_sample,
            text_tone=preference_data.text_tone,
            image_style_description=preference_data.image_style_description,
            image_color_palette=preference_data.image_color_palette,
            video_style_description=preference_data.video_style_description,
            video_duration_preference=preference_data.video_duration_preference
        )
        db.add(preference)

    db.commit()
    db.refresh(preference)

    return {
        "message": "선호도가 저장되었습니다.",
        "preference": preference
    }


@router.post("/upload-image-sample")
async def upload_image_sample(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    이미지 샘플 업로드 (Cloudinary)
    """
    try:
        # Cloudinary에 업로드
        result = cloudinary.uploader.upload(
            file.file,
            folder=f"user_samples/{current_user.id}/images",
            resource_type="image"
        )

        image_url = result.get("secure_url")

        # UserPreference 업데이트
        preference = db.query(models.UserPreference).filter(
            models.UserPreference.user_id == current_user.id
        ).first()

        if not preference:
            preference = models.UserPreference(user_id=current_user.id)
            db.add(preference)

        preference.image_style_sample_url = image_url
        if description:
            preference.image_style_description = description

        db.commit()
        db.refresh(preference)

        return {
            "message": "이미지 샘플이 업로드되었습니다.",
            "image_url": image_url,
            "preference": preference
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 업로드 실패: {str(e)}")


@router.post("/upload-video-sample")
async def upload_video_sample(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    duration_preference: Optional[str] = Form(None),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    영상 샘플 업로드 (Cloudinary)
    """
    try:
        # Cloudinary에 업로드
        result = cloudinary.uploader.upload(
            file.file,
            folder=f"user_samples/{current_user.id}/videos",
            resource_type="video"
        )

        video_url = result.get("secure_url")

        # UserPreference 업데이트
        preference = db.query(models.UserPreference).filter(
            models.UserPreference.user_id == current_user.id
        ).first()

        if not preference:
            preference = models.UserPreference(user_id=current_user.id)
            db.add(preference)

        preference.video_style_sample_url = video_url
        if description:
            preference.video_style_description = description
        if duration_preference:
            preference.video_duration_preference = duration_preference

        db.commit()
        db.refresh(preference)

        return {
            "message": "영상 샘플이 업로드되었습니다.",
            "video_url": video_url,
            "preference": preference
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"영상 업로드 실패: {str(e)}")


@router.post("/complete")
async def complete_onboarding(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    온보딩 완료 처리
    """
    current_user.onboarding_completed = True

    # ✅ BrandAnalysis 테이블 생성 또는 업데이트
    brand_analysis = db.query(models.BrandAnalysis).filter(
        models.BrandAnalysis.user_id == current_user.id
    ).first()

    if not brand_analysis:
        # BrandAnalysis 레코드가 없으면 생성하고 users 테이블 정보 복사
        business_type_map = {
            'food': '음식 / 카페',
            'tech': 'IT / 기술',
            'fashion': '패션 / 뷰티',
            'education': '교육',
            'health': '건강 / 의료'
        }
        brand_analysis = models.BrandAnalysis(
            user_id=current_user.id,
            brand_name=current_user.brand_name,
            business_type=business_type_map.get(
                current_user.business_type,
                current_user.business_type
            ) if current_user.business_type else None
        )
        db.add(brand_analysis)
    else:
        # 기존 레코드가 있지만 brand_name이나 business_type이 None이면 users 테이블에서 복사
        if not brand_analysis.brand_name and current_user.brand_name:
            brand_analysis.brand_name = current_user.brand_name
        if not brand_analysis.business_type and current_user.business_type:
            business_type_map = {
                'food': '음식 / 카페',
                'tech': 'IT / 기술',
                'fashion': '패션 / 뷰티',
                'education': '교육',
                'health': '건강 / 의료'
            }
            brand_analysis.business_type = business_type_map.get(
                current_user.business_type,
                current_user.business_type
            )

    db.commit()
    db.refresh(current_user)

    return {
        "message": "온보딩이 완료되었습니다!",
        "user": current_user
    }


@router.get("/status")
async def get_onboarding_status(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    온보딩 상태 확인
    """
    preference = db.query(models.UserPreference).filter(
        models.UserPreference.user_id == current_user.id
    ).first()

    return {
        "onboarding_completed": current_user.onboarding_completed,
        "has_business_info": bool(current_user.brand_name),
        "has_preferences": bool(preference),
        "has_text_sample": bool(preference and preference.text_style_sample),
        "has_image_sample": bool(preference and preference.image_style_sample_url),
        "has_video_sample": bool(preference and preference.video_style_sample_url),
        "user": current_user,
        "preferences": preference
    }
