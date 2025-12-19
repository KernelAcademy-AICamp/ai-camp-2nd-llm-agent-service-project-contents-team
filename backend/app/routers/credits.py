"""
크레딧 시스템 API 라우터
- 크레딧 잔액 조회
- 크레딧 충전 (테스트용)
- 크레딧 사용 내역 조회
- 크레딧 패키지 조회
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from ..database import get_db
from ..auth import get_current_user
from .. import models

router = APIRouter(prefix="/api/credits", tags=["credits"])


# ========== Pydantic 스키마 ==========

class CreditBalanceResponse(BaseModel):
    balance: int
    user_id: int

    class Config:
        from_attributes = True


class CreditPackageResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    credits: int
    bonus_credits: int
    price: int
    badge: Optional[str]
    is_popular: bool
    total_credits: int  # credits + bonus_credits

    class Config:
        from_attributes = True


class CreditTransactionResponse(BaseModel):
    id: int
    amount: int
    type: str  # charge, use, bonus, refund
    description: Optional[str]
    balance_before: int
    balance_after: int
    reference_type: Optional[str]
    reference_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ChargeCreditsRequest(BaseModel):
    package_id: int


class UseCreditsRequest(BaseModel):
    amount: int
    description: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None


class CreditCheckResponse(BaseModel):
    has_enough: bool
    current_balance: int
    required_amount: int
    shortage: int  # 부족한 크레딧 수 (0이면 충분)


# ========== 크레딧 비용 상수 ==========

CREDIT_COSTS = {
    "video_15s": 10,    # 숏폼 영상 (15초)
    "video_30s": 20,    # 숏폼 영상 (30초)
    "video_60s": 35,    # 숏폼 영상 (60초)
    "ai_image": 2,      # AI 이미지 생성
    "cardnews": 5,      # 카드뉴스 생성
}

SIGNUP_BONUS_CREDITS = 100  # 회원가입 보너스


# ========== 헬퍼 함수 ==========

def get_or_create_user_credit(db: Session, user_id: int) -> models.UserCredit:
    """사용자 크레딧 조회 또는 생성"""
    user_credit = db.query(models.UserCredit).filter(
        models.UserCredit.user_id == user_id
    ).first()

    if not user_credit:
        user_credit = models.UserCredit(user_id=user_id, balance=0)
        db.add(user_credit)
        db.commit()
        db.refresh(user_credit)

    return user_credit


def add_credit_transaction(
    db: Session,
    user_credit: models.UserCredit,
    amount: int,
    transaction_type: str,
    description: str,
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
    package_id: Optional[int] = None
) -> models.CreditTransaction:
    """크레딧 거래 내역 추가 및 잔액 업데이트"""
    balance_before = user_credit.balance
    balance_after = balance_before + amount

    # 잔액 업데이트
    user_credit.balance = balance_after

    # 거래 내역 생성
    transaction = models.CreditTransaction(
        user_credit_id=user_credit.id,
        user_id=user_credit.user_id,
        amount=amount,
        type=transaction_type,
        description=description,
        balance_before=balance_before,
        balance_after=balance_after,
        reference_type=reference_type,
        reference_id=reference_id,
        package_id=package_id
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    db.refresh(user_credit)

    return transaction


def grant_signup_bonus(db: Session, user_id: int) -> Optional[models.CreditTransaction]:
    """회원가입 보너스 크레딧 지급"""
    user_credit = get_or_create_user_credit(db, user_id)

    # 이미 보너스를 받았는지 확인
    existing_bonus = db.query(models.CreditTransaction).filter(
        models.CreditTransaction.user_id == user_id,
        models.CreditTransaction.type == "bonus",
        models.CreditTransaction.description == "회원가입 보너스"
    ).first()

    if existing_bonus:
        return None  # 이미 보너스를 받음

    # 보너스 지급
    return add_credit_transaction(
        db=db,
        user_credit=user_credit,
        amount=SIGNUP_BONUS_CREDITS,
        transaction_type="bonus",
        description="회원가입 보너스",
        reference_type="signup_bonus"
    )


# ========== API 엔드포인트 ==========

@router.get("/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """현재 사용자의 크레딧 잔액 조회"""
    user_credit = get_or_create_user_credit(db, current_user.id)
    return CreditBalanceResponse(balance=user_credit.balance, user_id=current_user.id)


@router.get("/check/{amount}", response_model=CreditCheckResponse)
async def check_credit_balance(
    amount: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """크레딧 잔액이 충분한지 확인"""
    user_credit = get_or_create_user_credit(db, current_user.id)
    shortage = max(0, amount - user_credit.balance)

    return CreditCheckResponse(
        has_enough=user_credit.balance >= amount,
        current_balance=user_credit.balance,
        required_amount=amount,
        shortage=shortage
    )


@router.get("/packages", response_model=List[CreditPackageResponse])
async def get_credit_packages(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """활성화된 크레딧 패키지 목록 조회"""
    packages = db.query(models.CreditPackage).filter(
        models.CreditPackage.is_active == True
    ).order_by(models.CreditPackage.sort_order).all()

    return [
        CreditPackageResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            credits=p.credits,
            bonus_credits=p.bonus_credits,
            price=p.price,
            badge=p.badge,
            is_popular=p.is_popular,
            total_credits=p.credits + p.bonus_credits
        )
        for p in packages
    ]


@router.get("/transactions", response_model=List[CreditTransactionResponse])
async def get_credit_transactions(
    limit: int = 50,
    offset: int = 0,
    transaction_type: Optional[str] = None,  # charge, use, bonus, refund
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """크레딧 거래 내역 조회"""
    query = db.query(models.CreditTransaction).filter(
        models.CreditTransaction.user_id == current_user.id
    )

    if transaction_type:
        query = query.filter(models.CreditTransaction.type == transaction_type)

    transactions = query.order_by(
        desc(models.CreditTransaction.created_at)
    ).offset(offset).limit(limit).all()

    return transactions


@router.post("/charge", response_model=CreditTransactionResponse)
async def charge_credits(
    request: ChargeCreditsRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    크레딧 충전 (테스트용 - 실제 결제 없이 충전)
    실제 서비스에서는 PG 결제 연동 후 충전 처리
    """
    # 패키지 조회
    package = db.query(models.CreditPackage).filter(
        models.CreditPackage.id == request.package_id,
        models.CreditPackage.is_active == True
    ).first()

    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="패키지를 찾을 수 없습니다."
        )

    user_credit = get_or_create_user_credit(db, current_user.id)
    total_credits = package.credits + package.bonus_credits

    # 충전 처리
    transaction = add_credit_transaction(
        db=db,
        user_credit=user_credit,
        amount=total_credits,
        transaction_type="charge",
        description=f"{package.name} 패키지 충전 ({package.credits:,} + 보너스 {package.bonus_credits:,})",
        reference_type="package_charge",
        reference_id=str(package.id),
        package_id=package.id
    )

    return transaction


@router.post("/use", response_model=CreditTransactionResponse)
async def use_credits(
    request: UseCreditsRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """크레딧 사용"""
    if request.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="사용할 크레딧은 0보다 커야 합니다."
        )

    user_credit = get_or_create_user_credit(db, current_user.id)

    # 잔액 확인
    if user_credit.balance < request.amount:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": "크레딧이 부족합니다.",
                "current_balance": user_credit.balance,
                "required_amount": request.amount,
                "shortage": request.amount - user_credit.balance
            }
        )

    # 사용 처리
    transaction = add_credit_transaction(
        db=db,
        user_credit=user_credit,
        amount=-request.amount,  # 음수로 저장
        transaction_type="use",
        description=request.description,
        reference_type=request.reference_type,
        reference_id=request.reference_id
    )

    return transaction


@router.post("/bonus/signup", response_model=Optional[CreditTransactionResponse])
async def grant_signup_bonus_endpoint(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """회원가입 보너스 크레딧 지급 (최초 1회)"""
    transaction = grant_signup_bonus(db, current_user.id)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 회원가입 보너스를 받으셨습니다."
        )

    return transaction


@router.get("/costs")
async def get_credit_costs(
    current_user: models.User = Depends(get_current_user)
):
    """각 기능별 크레딧 비용 조회"""
    return {
        "costs": CREDIT_COSTS,
        "descriptions": {
            "video_15s": "숏폼 영상 (15초)",
            "video_30s": "숏폼 영상 (30초)",
            "video_60s": "숏폼 영상 (60초)",
            "ai_image": "AI 이미지 생성 (1장)",
            "cardnews": "카드뉴스 생성",
        }
    }
