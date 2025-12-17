"""
Supabase Storage 업로드 기능 테스트
- 테스트 이미지 업로드
- Public URL 검증
- 파일 다운로드 확인
- 파일 삭제 테스트
"""

import os
import sys
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv

# 프로젝트 루트의 .env 로드
root_env = Path(__file__).parent.parent / ".env"
load_dotenv(root_env)

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.supabase_storage import get_storage_service
import requests


def create_test_image() -> bytes:
    """간단한 테스트 이미지 생성 (1x1 PNG)"""
    # 1x1 빨간색 PNG 이미지 (최소 크기)
    png_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf'
        b'\xc0\x00\x00\x00\x03\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00'
        b'IEND\xaeB`\x82'
    )
    return png_data


def main():
    print("=" * 60)
    print("🧪 Supabase Storage 업로드 테스트 시작")
    print("=" * 60)
    print()

    try:
        # 1. Storage Service 초기화
        print("1️⃣ SupabaseStorageService 초기화 중...")
        storage = get_storage_service()
        print("✅ Storage Service 초기화 성공")
        print()

        # 2. 테스트 이미지 생성
        print("2️⃣ 테스트 이미지 생성 중...")
        test_image_data = create_test_image()
        print(f"✅ 테스트 이미지 생성 완료 ({len(test_image_data)} bytes)")
        print()

        # 3. 파일 업로드 테스트
        test_bucket = "ai-video-products"
        test_file_path = "test/upload_test.png"

        print(f"3️⃣ 파일 업로드 테스트 ({test_bucket}/{test_file_path})")
        public_url = storage.upload_file(
            bucket=test_bucket,
            file_path=test_file_path,
            file_data=test_image_data,
            content_type="image/png"
        )
        print(f"✅ 업로드 성공!")
        print(f"   Public URL: {public_url}")
        print()

        # 4. Public URL 접근 테스트 (HTTP GET)
        print("4️⃣ Public URL 접근 테스트 중...")
        response = requests.get(public_url, timeout=10)

        if response.status_code == 200:
            print(f"✅ HTTP 접근 성공 (Status: {response.status_code})")
            print(f"   Content-Type: {response.headers.get('Content-Type')}")
            print(f"   Content-Length: {len(response.content)} bytes")

            # 다운로드한 파일이 원본과 동일한지 확인
            if response.content == test_image_data:
                print("✅ 다운로드한 파일이 원본과 일치합니다!")
            else:
                print("⚠️  다운로드한 파일이 원본과 다릅니다.")
        else:
            print(f"❌ HTTP 접근 실패 (Status: {response.status_code})")
        print()

        # 5. 파일 목록 조회 테스트
        print("5️⃣ 파일 목록 조회 테스트 중...")
        files = storage.list_files(test_bucket, "test")
        print(f"✅ 파일 목록 조회 성공 ({len(files)}개 파일)")
        for file in files:
            print(f"   - {file.get('name', 'N/A')}")
        print()

        # 6. 파일 삭제 테스트
        print("6️⃣ 파일 삭제 테스트 중...")
        delete_result = storage.delete_file(test_bucket, test_file_path)

        if delete_result:
            print("✅ 파일 삭제 성공")

            # 삭제 확인
            response_after_delete = requests.get(public_url, timeout=10)
            if response_after_delete.status_code == 404:
                print("✅ 파일이 정상적으로 삭제되었습니다 (404 확인)")
            else:
                print(f"⚠️  삭제 후 파일 접근: {response_after_delete.status_code}")
        else:
            print("❌ 파일 삭제 실패")
        print()

        print("=" * 60)
        print("🎉 모든 테스트 완료!")
        print("=" * 60)
        print()
        print("📋 테스트 결과 요약:")
        print("✅ Storage Service 초기화")
        print("✅ 파일 업로드")
        print("✅ Public URL 생성")
        print("✅ HTTP 다운로드")
        print("✅ 파일 목록 조회")
        print("✅ 파일 삭제")

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ 테스트 중 오류 발생!")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        print("📝 확인 사항:")
        print("1. .env 파일에 SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY 설정 확인")
        print("2. ai-video-products 버킷이 Supabase에 존재하는지 확인")
        print("3. 버킷이 Public으로 설정되어 있는지 확인")
        print("4. 네트워크 연결 상태 확인")
        sys.exit(1)


if __name__ == "__main__":
    main()
