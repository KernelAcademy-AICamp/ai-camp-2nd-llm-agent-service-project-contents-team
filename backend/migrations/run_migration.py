"""
Twitter to X 마이그레이션 스크립트
기존 테이블/컬럼명을 Twitter에서 X로 변경합니다.
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
    # Step 1: 테이블 이름 변경
    "ALTER TABLE IF EXISTS twitter_connections RENAME TO x_connections;",
    "ALTER TABLE IF EXISTS tweets RENAME TO x_posts;",

    # Step 2: x_connections 컬럼 이름 변경
    "ALTER TABLE x_connections RENAME COLUMN twitter_user_id TO x_user_id;",
    "ALTER TABLE x_connections RENAME COLUMN tweet_count TO post_count;",

    # Step 3: x_posts 컬럼 이름 변경
    "ALTER TABLE x_posts RENAME COLUMN tweet_id TO post_id;",
    "ALTER TABLE x_posts RENAME COLUMN created_at_twitter TO created_at_x;",
    "ALTER TABLE x_posts RENAME COLUMN retweet_count TO repost_count;",
    "ALTER TABLE x_posts RENAME COLUMN referenced_tweets TO referenced_posts;",
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
                # 이미 변경된 경우 무시
                if "does not exist" in error_msg or "already exists" in error_msg:
                    print(f"  ⊘ Skipped (already done or not needed)")
                else:
                    print(f"  ✗ Error: {error_msg}")

    print("\n마이그레이션 완료!")

if __name__ == "__main__":
    run_migration()
