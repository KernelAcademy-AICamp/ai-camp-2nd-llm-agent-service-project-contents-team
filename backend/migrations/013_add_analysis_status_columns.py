"""
brand_analysis 테이블에 analysis_status, analysis_error 컬럼 추가
- 전체 분석 상태를 명시적으로 관리하기 위한 컬럼
- pending, analyzing, completed, failed 상태 지원
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """analysis_status, analysis_error 컬럼 추가"""

    with engine.connect() as conn:
        # analysis_status 컬럼 추가
        conn.execute(text("""
            ALTER TABLE brand_analysis
            ADD COLUMN IF NOT EXISTS analysis_status VARCHAR DEFAULT 'pending'
        """))
        print("analysis_status 컬럼 추가 완료")

        # analysis_error 컬럼 추가
        conn.execute(text("""
            ALTER TABLE brand_analysis
            ADD COLUMN IF NOT EXISTS analysis_error TEXT
        """))
        print("analysis_error 컬럼 추가 완료")

        # 기존 데이터 마이그레이션: brand_profile_json이 있으면 completed로 설정
        conn.execute(text("""
            UPDATE brand_analysis
            SET analysis_status = 'completed'
            WHERE brand_profile_json IS NOT NULL
              AND analysis_status = 'pending'
        """))
        print("기존 완료된 분석 데이터 상태 업데이트 완료")

        conn.commit()

    print("\n마이그레이션 완료!")


if __name__ == "__main__":
    run_migration()
