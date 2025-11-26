"""
브랜드 분석 테이블에 brand_name, business_type 컬럼 추가
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# .env 파일 로드
root_env = Path(__file__).parent.parent.parent / ".env"
load_dotenv(root_env)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL 환경 변수가 설정되지 않았습니다")
    sys.exit(1)

print(f"데이터베이스 연결 중: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # brand_name 컬럼 추가
        print("brand_name 컬럼 추가 중...")
        conn.execute(text("ALTER TABLE brand_analysis ADD COLUMN IF NOT EXISTS brand_name VARCHAR"))

        # business_type 컬럼 추가
        print("business_type 컬럼 추가 중...")
        conn.execute(text("ALTER TABLE brand_analysis ADD COLUMN IF NOT EXISTS business_type VARCHAR"))

        conn.commit()
        print("✅ 마이그레이션 완료!")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    sys.exit(1)
