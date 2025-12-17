"""
Supabase Storage 헬퍼 서비스
- 파일 업로드
- Public URL 생성
- 파일 삭제
"""

import os
from typing import Optional
from supabase import create_client, Client
from ..logger import get_logger

logger = get_logger(__name__)


class SupabaseStorageService:
    """
    Supabase Storage 작업을 위한 헬퍼 클래스

    사용 예:
    ```python
    storage = SupabaseStorageService()
    url = storage.upload_file(
        bucket="ai-video-products",
        file_path="1/product.jpg",
        file_data=image_bytes
    )
    ```
    """

    def __init__(self):
        """
        Supabase 클라이언트 초기화
        환경 변수에서 SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY 로드
        """
        supabase_url = os.getenv("SUPABASE_URL")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not service_role_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables"
            )

        self.client: Client = create_client(supabase_url, service_role_key)
        logger.info(f"SupabaseStorageService initialized with URL: {supabase_url}")

    def upload_file(
        self,
        bucket: str,
        file_path: str,
        file_data: bytes,
        content_type: Optional[str] = None
    ) -> str:
        """
        파일을 Supabase Storage에 업로드하고 Public URL 반환

        Args:
            bucket: 버킷 이름 (예: "ai-video-products")
            file_path: 버킷 내 파일 경로 (예: "1/product.jpg")
            file_data: 업로드할 파일 데이터 (bytes)
            content_type: MIME 타입 (예: "image/jpeg", "video/mp4")

        Returns:
            str: Public URL (예: "https://xxx.supabase.co/storage/v1/object/public/ai-video-products/1/product.jpg")

        Raises:
            Exception: 업로드 실패 시
        """
        try:
            logger.info(f"Uploading file to Supabase: {bucket}/{file_path}")

            # 파일 업로드
            options = {}
            if content_type:
                options["content-type"] = content_type

            # upsert=True: 같은 경로에 파일이 있으면 덮어쓰기
            response = self.client.storage.from_(bucket).upload(
                path=file_path,
                file=file_data,
                file_options={
                    "content-type": content_type or "application/octet-stream",
                    "upsert": "true"  # 덮어쓰기 허용
                }
            )

            # Public URL 생성
            public_url = self.get_public_url(bucket, file_path)

            logger.info(f"✅ File uploaded successfully: {public_url}")
            return public_url

        except Exception as e:
            logger.error(f"❌ Failed to upload file to {bucket}/{file_path}: {str(e)}")
            raise Exception(f"Supabase upload failed: {str(e)}")

    def get_public_url(self, bucket: str, file_path: str) -> str:
        """
        파일의 Public URL 생성

        Args:
            bucket: 버킷 이름
            file_path: 버킷 내 파일 경로

        Returns:
            str: Public URL
        """
        try:
            response = self.client.storage.from_(bucket).get_public_url(file_path)
            return response
        except Exception as e:
            logger.error(f"Failed to get public URL for {bucket}/{file_path}: {str(e)}")
            raise

    def delete_file(self, bucket: str, file_path: str) -> bool:
        """
        파일 삭제

        Args:
            bucket: 버킷 이름
            file_path: 버킷 내 파일 경로

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            logger.info(f"Deleting file from Supabase: {bucket}/{file_path}")

            response = self.client.storage.from_(bucket).remove([file_path])

            logger.info(f"✅ File deleted successfully: {bucket}/{file_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to delete file {bucket}/{file_path}: {str(e)}")
            return False

    def list_files(self, bucket: str, path: str = "") -> list:
        """
        버킷 내 파일 목록 조회

        Args:
            bucket: 버킷 이름
            path: 조회할 경로 (기본값: 루트)

        Returns:
            list: 파일 목록
        """
        try:
            response = self.client.storage.from_(bucket).list(path)
            return response
        except Exception as e:
            logger.error(f"Failed to list files in {bucket}/{path}: {str(e)}")
            return []

    def delete_folder(self, bucket: str, folder_path: str) -> bool:
        """
        폴더 내 모든 파일 삭제

        Args:
            bucket: 버킷 이름
            folder_path: 폴더 경로 (예: "1/18/")

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            logger.info(f"Deleting folder from Supabase: {bucket}/{folder_path}")

            # 폴더 내 파일 목록 조회
            files = self.list_files(bucket, folder_path)

            if not files:
                logger.info(f"No files found in {bucket}/{folder_path}")
                return True

            # 파일 경로 목록 생성
            file_paths = [f"{folder_path}/{f['name']}" for f in files if f.get('name')]

            # 일괄 삭제
            if file_paths:
                response = self.client.storage.from_(bucket).remove(file_paths)
                logger.info(f"✅ Deleted {len(file_paths)} files from {bucket}/{folder_path}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to delete folder {bucket}/{folder_path}: {str(e)}")
            return False


# 싱글톤 인스턴스 (필요 시 사용)
_storage_service_instance: Optional[SupabaseStorageService] = None


def get_storage_service() -> SupabaseStorageService:
    """
    SupabaseStorageService 싱글톤 인스턴스 반환
    """
    global _storage_service_instance
    if _storage_service_instance is None:
        _storage_service_instance = SupabaseStorageService()
    return _storage_service_instance
