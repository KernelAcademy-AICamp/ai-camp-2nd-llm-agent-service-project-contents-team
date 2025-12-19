"""
새로운 콘텐츠 생성 테이블 구조 (v2) 마이그레이션
- ContentGenerationSession: 사용자 입력값 저장
- GeneratedBlogContent: 블로그 결과
- GeneratedSNSContent: SNS 결과
- GeneratedXContent: X 결과
- GeneratedThreadsContent: Threads 결과
- GeneratedImage: 생성된 이미지
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine

def run_migration():
    """새로운 콘텐츠 테이블 생성"""

    with engine.connect() as conn:
        # 1. content_generation_sessions 테이블 생성
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS content_generation_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                topic TEXT NOT NULL,
                content_type VARCHAR NOT NULL,
                style VARCHAR NOT NULL,
                selected_platforms JSON NOT NULL,
                analysis_data JSON,
                critique_data JSON,
                generation_attempts INTEGER DEFAULT 1,
                status VARCHAR DEFAULT 'generated',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_content_generation_sessions_user_id
            ON content_generation_sessions(user_id)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_content_generation_sessions_created_at
            ON content_generation_sessions(created_at DESC)
        """))

        print("✅ content_generation_sessions 테이블 생성 완료")

        # 2. generated_blog_contents 테이블 생성
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS generated_blog_contents (
                id SERIAL PRIMARY KEY,
                session_id INTEGER NOT NULL REFERENCES content_generation_sessions(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR NOT NULL,
                content TEXT NOT NULL,
                tags JSON,
                score INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_generated_blog_contents_session_id
            ON generated_blog_contents(session_id)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_generated_blog_contents_user_id
            ON generated_blog_contents(user_id)
        """))

        print("✅ generated_blog_contents 테이블 생성 완료")

        # 3. generated_sns_contents 테이블 생성
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS generated_sns_contents (
                id SERIAL PRIMARY KEY,
                session_id INTEGER NOT NULL REFERENCES content_generation_sessions(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                hashtags JSON,
                score INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_generated_sns_contents_session_id
            ON generated_sns_contents(session_id)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_generated_sns_contents_user_id
            ON generated_sns_contents(user_id)
        """))

        print("✅ generated_sns_contents 테이블 생성 완료")

        # 4. generated_x_contents 테이블 생성
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS generated_x_contents (
                id SERIAL PRIMARY KEY,
                session_id INTEGER NOT NULL REFERENCES content_generation_sessions(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                hashtags JSON,
                score INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_generated_x_contents_session_id
            ON generated_x_contents(session_id)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_generated_x_contents_user_id
            ON generated_x_contents(user_id)
        """))

        print("✅ generated_x_contents 테이블 생성 완료")

        # 5. generated_threads_contents 테이블 생성
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS generated_threads_contents (
                id SERIAL PRIMARY KEY,
                session_id INTEGER NOT NULL REFERENCES content_generation_sessions(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                hashtags JSON,
                score INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_generated_threads_contents_session_id
            ON generated_threads_contents(session_id)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_generated_threads_contents_user_id
            ON generated_threads_contents(user_id)
        """))

        print("✅ generated_threads_contents 테이블 생성 완료")

        # 6. generated_images 테이블 생성
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS generated_images (
                id SERIAL PRIMARY KEY,
                session_id INTEGER NOT NULL REFERENCES content_generation_sessions(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                image_url VARCHAR NOT NULL,
                prompt TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_generated_images_session_id
            ON generated_images(session_id)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_generated_images_user_id
            ON generated_images(user_id)
        """))

        print("✅ generated_images 테이블 생성 완료")

        conn.commit()

    print("\n🎉 모든 테이블 마이그레이션 완료!")


if __name__ == "__main__":
    run_migration()
