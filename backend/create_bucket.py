"""
Supabase Storage 버킷 생성 스크립트
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# .env 파일 로드
load_dotenv(Path(__file__).parent.parent / ".env")

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# 새 버킷 생성
bucket_name = "ai-generated-content"
try:
    result = supabase.storage.create_bucket(
        bucket_name,
        options={
            "public": True,
            "file_size_limit": 10485760,  # 10MB
            "allowed_mime_types": ["image/png", "image/jpeg", "image/webp", "image/gif"]
        }
    )
    print(f"✅ 버킷 '{bucket_name}' 생성 성공!")
except Exception as e:
    if "already exists" in str(e).lower():
        print(f"ℹ️  버킷 '{bucket_name}'가 이미 존재합니다.")
    else:
        print(f"❌ 버킷 생성 실패: {e}")

# 버킷 목록 확인
buckets = supabase.storage.list_buckets()
print("\n📦 현재 버킷 목록:")
for b in buckets:
    print(f"  - {b.name} (Public: {b.public})")
