"""
video_generation_jobs 테이블에 session_id 컬럼 추가
- session_id: 작업 추적용 고유 세션 ID (UUID)
- VideoGenerationJob과 GeneratedVideo를 연결하는 공통 키
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine
import uuid


def run_migration():
    """session_id 컬럼 추가 및 기존 레코드에 UUID 생성"""

    with engine.connect() as conn:
        # session_id 컬럼 추가 (nullable=True로 먼저 추가)
        conn.execute(text("""
            ALTER TABLE video_generation_jobs
            ADD COLUMN IF NOT EXISTS session_id VARCHAR
        """))
        print("✅ session_id 컬럼 추가 완료")

        # 기존 레코드에 UUID 생성
        result = conn.execute(text("""
            SELECT id FROM video_generation_jobs WHERE session_id IS NULL
        """))
        null_session_ids = result.fetchall()

        for row in null_session_ids:
            job_id = row[0]
            new_session_id = str(uuid.uuid4())
            conn.execute(text("""
                UPDATE video_generation_jobs
                SET session_id = :session_id
                WHERE id = :job_id
            """), {"session_id": new_session_id, "job_id": job_id})

        print(f"✅ 기존 {len(null_session_ids)}개 레코드에 session_id 생성 완료")

        # session_id를 NOT NULL과 UNIQUE로 변경
        conn.execute(text("""
            ALTER TABLE video_generation_jobs
            ALTER COLUMN session_id SET NOT NULL
        """))
        print("✅ session_id를 NOT NULL로 변경 완료")

        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_video_generation_jobs_session_id
            ON video_generation_jobs(session_id)
        """))
        print("✅ session_id UNIQUE 인덱스 생성 완료")

        conn.commit()

    print("\n🎉 마이그레이션 완료!")
    print("추가된 컬럼: session_id (VARCHAR, UNIQUE, NOT NULL, INDEXED)")


if __name__ == "__main__":
    run_migration()
