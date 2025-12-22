"""
video_generation_jobs 테이블에 4단계 Agent 파이프라인 결과 컬럼 추가

추가되는 컬럼:
- product_analysis (JSON): 1단계 제품 분석 결과
- story_plan (JSON): 2단계 스토리 기획 결과
- quality_evaluation (JSON): 4단계 품질 검증 결과
- generation_attempts (INTEGER): 품질 검증 재시도 횟수
- brand_confidence_used (VARCHAR): 적용된 브랜드 신뢰도
- processing_time_seconds (FLOAT): 총 처리 시간
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """4단계 Agent 파이프라인 결과 컬럼 추가"""

    with engine.connect() as conn:
        # 1단계: 제품 분석 결과
        conn.execute(text("""
            ALTER TABLE video_generation_jobs
            ADD COLUMN IF NOT EXISTS product_analysis JSON
        """))
        print("✅ product_analysis 컬럼 추가 완료")

        # 2단계: 스토리 기획 결과
        conn.execute(text("""
            ALTER TABLE video_generation_jobs
            ADD COLUMN IF NOT EXISTS story_plan JSON
        """))
        print("✅ story_plan 컬럼 추가 완료")

        # 4단계: 품질 검증 결과
        conn.execute(text("""
            ALTER TABLE video_generation_jobs
            ADD COLUMN IF NOT EXISTS quality_evaluation JSON
        """))
        print("✅ quality_evaluation 컬럼 추가 완료")

        # 메타데이터: 재시도 횟수
        conn.execute(text("""
            ALTER TABLE video_generation_jobs
            ADD COLUMN IF NOT EXISTS generation_attempts INTEGER DEFAULT 1
        """))
        print("✅ generation_attempts 컬럼 추가 완료")

        # 메타데이터: 브랜드 신뢰도
        conn.execute(text("""
            ALTER TABLE video_generation_jobs
            ADD COLUMN IF NOT EXISTS brand_confidence_used VARCHAR(20)
        """))
        print("✅ brand_confidence_used 컬럼 추가 완료")

        # 메타데이터: 처리 시간
        conn.execute(text("""
            ALTER TABLE video_generation_jobs
            ADD COLUMN IF NOT EXISTS processing_time_seconds FLOAT
        """))
        print("✅ processing_time_seconds 컬럼 추가 완료")

        conn.commit()

    print("\n🎉 마이그레이션 완료! video_generation_jobs 테이블에 6개 컬럼이 추가되었습니다.")


def rollback_migration():
    """마이그레이션 롤백 (컬럼 삭제)"""

    with engine.connect() as conn:
        columns_to_drop = [
            "product_analysis",
            "story_plan",
            "quality_evaluation",
            "generation_attempts",
            "brand_confidence_used",
            "processing_time_seconds"
        ]

        for column in columns_to_drop:
            try:
                conn.execute(text(f"""
                    ALTER TABLE video_generation_jobs
                    DROP COLUMN IF EXISTS {column}
                """))
                print(f"🗑️ {column} 컬럼 삭제 완료")
            except Exception as e:
                print(f"⚠️ {column} 컬럼 삭제 실패: {e}")

        conn.commit()

    print("\n롤백 완료!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--rollback", action="store_true", help="마이그레이션 롤백")
    args = parser.parse_args()

    if args.rollback:
        rollback_migration()
    else:
        run_migration()
