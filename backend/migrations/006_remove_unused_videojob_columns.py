"""
video_generation_jobs 테이블에서 사용하지 않는 컬럼 삭제
- cost: 비용 정보 (프론트엔드 미사용)
- planning_model, image_model, video_model: AI 모델 추적 (미사용)
- updated_at: 업데이트 시각 (created_at, completed_at으로 충분)
- thumbnail_url: 썸네일 URL (작동하지 않음, 프론트엔드 미사용)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """사용하지 않는 컬럼 삭제"""

    with engine.connect() as conn:
        # cost 컬럼 삭제
        conn.execute(text("""
            ALTER TABLE video_generation_jobs
            DROP COLUMN IF EXISTS cost
        """))
        print("✅ cost 컬럼 삭제 완료")

        # AI 모델 컬럼 삭제
        conn.execute(text("""
            ALTER TABLE video_generation_jobs
            DROP COLUMN IF EXISTS planning_model,
            DROP COLUMN IF EXISTS image_model,
            DROP COLUMN IF EXISTS video_model
        """))
        print("✅ AI 모델 컬럼 (planning_model, image_model, video_model) 삭제 완료")

        # updated_at 컬럼 삭제
        conn.execute(text("""
            ALTER TABLE video_generation_jobs
            DROP COLUMN IF EXISTS updated_at
        """))
        print("✅ updated_at 컬럼 삭제 완료")

        # thumbnail_url 컬럼 삭제
        conn.execute(text("""
            ALTER TABLE video_generation_jobs
            DROP COLUMN IF EXISTS thumbnail_url
        """))
        print("✅ thumbnail_url 컬럼 삭제 완료")

        conn.commit()

    print("\n🎉 마이그레이션 완료!")
    print("삭제된 컬럼: cost, planning_model, image_model, video_model, updated_at, thumbnail_url")
    print("유지된 컬럼: completed_at")


if __name__ == "__main__":
    run_migration()
