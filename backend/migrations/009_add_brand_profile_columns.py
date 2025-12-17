"""
brand_analysis 테이블에 통합 브랜드 프로필 컬럼 추가
- brand_profile_json: 전체 BrandProfile 객체 저장 (JSON)
- profile_source: 데이터 출처 추적
- profile_confidence: 신뢰도 수준 (low/medium/high)
- profile_updated_at: 프로필 마지막 업데이트 시간
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """brand_analysis 테이블에 브랜드 프로필 컬럼 추가"""

    with engine.connect() as conn:
        # brand_profile_json 컬럼 추가
        try:
            conn.execute(text("""
                ALTER TABLE brand_analysis
                ADD COLUMN IF NOT EXISTS brand_profile_json JSON
            """))
            print("✅ brand_profile_json 컬럼 추가 완료")
        except Exception as e:
            print(f"⚠️ brand_profile_json: {e}")

        # profile_source 컬럼 추가
        try:
            conn.execute(text("""
                ALTER TABLE brand_analysis
                ADD COLUMN IF NOT EXISTS profile_source VARCHAR
            """))
            print("✅ profile_source 컬럼 추가 완료")
        except Exception as e:
            print(f"⚠️ profile_source: {e}")

        # profile_confidence 컬럼 추가
        try:
            conn.execute(text("""
                ALTER TABLE brand_analysis
                ADD COLUMN IF NOT EXISTS profile_confidence VARCHAR
            """))
            print("✅ profile_confidence 컬럼 추가 완료")
        except Exception as e:
            print(f"⚠️ profile_confidence: {e}")

        # profile_updated_at 컬럼 추가
        try:
            conn.execute(text("""
                ALTER TABLE brand_analysis
                ADD COLUMN IF NOT EXISTS profile_updated_at TIMESTAMP WITH TIME ZONE
            """))
            print("✅ profile_updated_at 컬럼 추가 완료")
        except Exception as e:
            print(f"⚠️ profile_updated_at: {e}")

        conn.commit()

    print("\n🎉 마이그레이션 완료!")
    print("테이블: brand_analysis")
    print("추가된 컬럼:")
    print("  - brand_profile_json (JSON)")
    print("  - profile_source (VARCHAR)")
    print("  - profile_confidence (VARCHAR)")
    print("  - profile_updated_at (TIMESTAMP WITH TIME ZONE)")


if __name__ == "__main__":
    run_migration()
