"""
brand_analysis 테이블에 analysis_progress, analysis_step 컬럼 추가
- 분석 진행률(0-100%)을 표시하기 위한 컬럼
- 현재 분석 단계를 표시하기 위한 컬럼
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """analysis_progress, analysis_step 컬럼 추가"""

    with engine.connect() as conn:
        # analysis_progress 컬럼 추가 (0-100 정수)
        conn.execute(text("""
            ALTER TABLE brand_analysis
            ADD COLUMN IF NOT EXISTS analysis_progress INTEGER DEFAULT 0
        """))
        print("analysis_progress 컬럼 추가 완료")

        # analysis_step 컬럼 추가 (현재 단계)
        conn.execute(text("""
            ALTER TABLE brand_analysis
            ADD COLUMN IF NOT EXISTS analysis_step VARCHAR
        """))
        print("analysis_step 컬럼 추가 완료")

        # 기존 완료된 분석은 progress를 100으로 설정
        conn.execute(text("""
            UPDATE brand_analysis
            SET analysis_progress = 100
            WHERE analysis_status = 'completed'
        """))
        print("기존 완료된 분석 데이터 progress 업데이트 완료")

        conn.commit()

    print("\n마이그레이션 완료!")


if __name__ == "__main__":
    run_migration()
