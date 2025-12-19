"""
X 및 Threads 콘텐츠 컬럼 추가 마이그레이션 스크립트
ai_generated_contents 테이블에 x_content, x_hashtags, threads_content, threads_hashtags 컬럼을 추가합니다.
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# .env 파일 로드
load_dotenv(Path(__file__).parent.parent.parent / ".env")
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL 환경 변수가 설정되지 않았습니다.")
    sys.exit(1)

print(f"Connecting to database...")

engine = create_engine(DATABASE_URL)

migration_statements = [
    # X 콘텐츠 컬럼 추가
    "ALTER TABLE ai_generated_contents ADD COLUMN IF NOT EXISTS x_content TEXT;",
    "ALTER TABLE ai_generated_contents ADD COLUMN IF NOT EXISTS x_hashtags JSONB;",

    # Threads 콘텐츠 컬럼 추가
    "ALTER TABLE ai_generated_contents ADD COLUMN IF NOT EXISTS threads_content TEXT;",
    "ALTER TABLE ai_generated_contents ADD COLUMN IF NOT EXISTS threads_hashtags JSONB;",
]

def run_migration():
    with engine.connect() as conn:
        for stmt in migration_statements:
            try:
                print(f"Executing: {stmt[:60]}...")
                conn.execute(text(stmt))
                conn.commit()
                print("  ✓ Success")
            except Exception as e:
                error_msg = str(e)
                # 이미 추가된 경우 무시
                if "already exists" in error_msg:
                    print(f"  ⊘ Skipped (already exists)")
                else:
                    print(f"  ✗ Error: {error_msg}")

    # 확인
    print("\n컬럼 확인 중...")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'ai_generated_contents'
            AND column_name IN ('x_content', 'x_hashtags', 'threads_content', 'threads_hashtags')
        """))
        columns = result.fetchall()
        print(f"추가된 컬럼: {[col[0] for col in columns]}")

    print("\n마이그레이션 완료!")

if __name__ == "__main__":
    run_migration()
