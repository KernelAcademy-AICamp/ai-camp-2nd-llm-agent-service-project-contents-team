"""
Supabase Storage 연결 테스트 스크립트
- 환경 변수 로드
- Supabase 클라이언트 생성
- 버킷 목록 확인
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# .env 파일 로드
root_env = Path(__file__).parent.parent / ".env"
load_dotenv(root_env)

# 환경 변수 확인
print("=" * 50)
print("📋 환경 변수 확인")
print("=" * 50)
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
print(f"SUPABASE_ANON_KEY: {os.getenv('SUPABASE_ANON_KEY')[:20]}..." if os.getenv('SUPABASE_ANON_KEY') else "Not found")
print(f"SUPABASE_SERVICE_ROLE_KEY: {os.getenv('SUPABASE_SERVICE_ROLE_KEY')[:20]}..." if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else "Not found")
print()

try:
    # Supabase 클라이언트 생성 (service_role 키 사용)
    print("=" * 50)
    print("🔌 Supabase 클라이언트 연결 중...")
    print("=" * 50)

    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # 업로드/삭제에는 service_role 필요
    )

    print("✅ Supabase 클라이언트 생성 성공!")
    print()

    # 버킷 목록 조회
    print("=" * 50)
    print("📦 Storage 버킷 목록 조회")
    print("=" * 50)

    buckets = supabase.storage.list_buckets()

    if buckets:
        print(f"✅ 총 {len(buckets)}개의 버킷 발견:")
        for bucket in buckets:
            print(f"  - {bucket.name} (ID: {bucket.id}, Public: {bucket.public})")
    else:
        print("⚠️  버킷이 없습니다. Supabase Dashboard에서 버킷을 생성해주세요.")

    print()

    # 필요한 버킷 확인
    required_buckets = [
        "ai-video-products",
        "ai-video-cuts",
        "ai-video-transitions",
        "ai-video-finals"
    ]

    existing_bucket_names = [b.name for b in buckets] if buckets else []

    print("=" * 50)
    print("✅ 필수 버킷 확인")
    print("=" * 50)

    for bucket_name in required_buckets:
        if bucket_name in existing_bucket_names:
            print(f"✅ {bucket_name}")
        else:
            print(f"❌ {bucket_name} (없음)")

    print()
    print("=" * 50)
    print("🎉 Supabase Storage 연결 테스트 완료!")
    print("=" * 50)

except Exception as e:
    print()
    print("=" * 50)
    print("❌ 오류 발생!")
    print("=" * 50)
    print(f"Error: {str(e)}")
    print()
    print("📝 확인 사항:")
    print("1. .env 파일에 SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY 설정 확인")
    print("2. Supabase Dashboard에서 API 키 재확인")
    print("3. 네트워크 연결 상태 확인")
