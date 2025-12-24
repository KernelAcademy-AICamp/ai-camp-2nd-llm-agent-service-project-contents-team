"""
PostgreSQL 시퀀스 리셋 스크립트
UniqueViolation 오류 해결용
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# .env 파일 로드
load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL 환경 변수가 설정되지 않았습니다.")
    exit(1)

print(f"Connecting to database...")

engine = create_engine(DATABASE_URL)

# 시퀀스 리셋 쿼리
sequences_to_fix = [
    ("generated_blog_contents", "generated_blog_contents_id_seq"),
    ("generated_sns_contents", "generated_sns_contents_id_seq"),
    ("generated_x_contents", "generated_x_contents_id_seq"),
    ("generated_threads_contents", "generated_threads_contents_id_seq"),
    ("generated_images", "generated_images_id_seq"),
    ("content_generation_sessions", "content_generation_sessions_id_seq"),
]

with engine.connect() as conn:
    for table_name, seq_name in sequences_to_fix:
        try:
            # 현재 최대 ID 조회
            result = conn.execute(text(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}"))
            max_id = result.scalar()

            # 시퀀스 리셋
            conn.execute(text(f"SELECT setval('{seq_name}', {max_id + 1}, false)"))
            conn.commit()

            print(f"✅ {table_name}: 시퀀스를 {max_id + 1}로 리셋")
        except Exception as e:
            print(f"⚠️  {table_name}: {str(e)[:50]}")

print("\n✅ 시퀀스 리셋 완료!")
