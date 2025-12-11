"""
발행 콘텐츠 테이블 마이그레이션
- PublishedContent: 임시저장, 예약발행, 발행완료 콘텐츠 관리
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """published_contents 테이블 생성"""

    with engine.connect() as conn:
        # published_contents 테이블 생성
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS published_contents (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                session_id INTEGER REFERENCES content_generation_sessions(id) ON DELETE SET NULL,

                -- 플랫폼 정보
                platform VARCHAR(20) NOT NULL,

                -- 편집된 콘텐츠
                title VARCHAR(500),
                content TEXT NOT NULL,
                tags JSON,

                -- 이미지 참조
                image_ids JSON,

                -- 상태 관리
                status VARCHAR(20) NOT NULL DEFAULT 'draft',

                -- 예약/발행 정보
                scheduled_at TIMESTAMP WITH TIME ZONE,
                published_at TIMESTAMP WITH TIME ZONE,
                publish_url VARCHAR(500),
                publish_error TEXT,

                -- 통계
                views INTEGER DEFAULT 0,

                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))

        print("✅ published_contents 테이블 생성 완료")

        # 인덱스 생성
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_published_contents_user_id
            ON published_contents(user_id)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_published_contents_session_id
            ON published_contents(session_id)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_published_contents_status
            ON published_contents(status)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_published_contents_platform
            ON published_contents(platform)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_published_contents_scheduled_at
            ON published_contents(scheduled_at)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_published_contents_created_at
            ON published_contents(created_at DESC)
        """))

        print("✅ 인덱스 생성 완료")

        conn.commit()

    print("\n🎉 published_contents 테이블 마이그레이션 완료!")


if __name__ == "__main__":
    run_migration()
