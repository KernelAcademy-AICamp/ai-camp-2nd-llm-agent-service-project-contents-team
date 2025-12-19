"""
AI Generated Contents 테이블에 generated_image_urls 컬럼 추가
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")
load_dotenv()

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL 환경 변수가 설정되지 않았습니다.")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

# 컬럼 추가 SQL
add_column_sql = """
ALTER TABLE ai_generated_contents
ADD COLUMN IF NOT EXISTS generated_image_urls JSONB;
"""

try:
    with engine.connect() as conn:
        conn.execute(text(add_column_sql))
        conn.commit()
        print("✅ generated_image_urls 컬럼이 추가되었습니다.")
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    sys.exit(1)
