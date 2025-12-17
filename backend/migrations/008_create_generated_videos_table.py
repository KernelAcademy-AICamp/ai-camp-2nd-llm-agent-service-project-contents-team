"""
generated_videos 테이블 생성
- 완료된 비디오 결과물만 저장
- VideoGenerationJob과 session_id로 1:1 연결
- Supabase Storage URL 저장
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """generated_videos 테이블 생성"""

    with engine.connect() as conn:
        # generated_videos 테이블 생성
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS generated_videos (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                final_video_url VARCHAR NOT NULL,
                product_name VARCHAR NOT NULL,
                tier VARCHAR NOT NULL,
                duration_seconds INTEGER NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT fk_generated_videos_session_id
                    FOREIGN KEY (session_id)
                    REFERENCES video_generation_jobs(session_id)
                    ON DELETE CASCADE,

                CONSTRAINT fk_generated_videos_user_id
                    FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """))
        print("✅ generated_videos 테이블 생성 완료")

        # 인덱스 생성
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_generated_videos_session_id
            ON generated_videos(session_id)
        """))
        print("✅ session_id 인덱스 생성 완료")

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_generated_videos_user_id
            ON generated_videos(user_id)
        """))
        print("✅ user_id 인덱스 생성 완료")

        conn.commit()

    print("\n🎉 마이그레이션 완료!")
    print("생성된 테이블: generated_videos")
    print("컬럼: id, session_id, user_id, final_video_url, product_name, tier, duration_seconds, created_at")
    print("외래키: session_id → video_generation_jobs.session_id")
    print("       user_id → users.id")


if __name__ == "__main__":
    run_migration()
