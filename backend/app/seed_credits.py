"""
크레딧 패키지 초기 데이터 시딩 스크립트
실행: python -m app.seed_credits
"""
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from . import models


def seed_credit_packages(db: Session):
    """크레딧 패키지 초기 데이터 생성"""

    # 기존 패키지 확인
    existing = db.query(models.CreditPackage).first()
    if existing:
        print("크레딧 패키지가 이미 존재합니다. 시딩을 건너뜁니다.")
        return

    packages = [
        models.CreditPackage(
            name="스타터",
            description="처음 시작하는 분들을 위한 패키지",
            credits=50,
            bonus_credits=0,
            price=5000,
            badge=None,
            is_popular=False,
            sort_order=1
        ),
        models.CreditPackage(
            name="베이직",
            description="가벼운 콘텐츠 제작에 적합",
            credits=120,
            bonus_credits=10,
            price=10000,
            badge=None,
            is_popular=False,
            sort_order=2
        ),
        models.CreditPackage(
            name="스탠다드",
            description="가장 많이 선택하는 인기 패키지",
            credits=300,
            bonus_credits=50,
            price=25000,
            badge="인기",
            is_popular=True,
            sort_order=3
        ),
        models.CreditPackage(
            name="프로",
            description="전문 크리에이터를 위한 패키지",
            credits=700,
            bonus_credits=150,
            price=50000,
            badge="추천",
            is_popular=False,
            sort_order=4
        ),
        models.CreditPackage(
            name="엔터프라이즈",
            description="대량 콘텐츠 제작에 최적화",
            credits=1500,
            bonus_credits=500,
            price=100000,
            badge="BEST",
            is_popular=False,
            sort_order=5
        ),
    ]

    for package in packages:
        db.add(package)

    db.commit()
    print(f"✅ {len(packages)}개의 크레딧 패키지가 생성되었습니다.")


def main():
    # 테이블 생성
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_credit_packages(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
