"""
Vertex AI Gemini 2.5 Flash 클라이언트 유틸리티

브랜드 분석을 위한 Vertex AI API 헬퍼 함수 제공
"""

import os
import json
import logging
import asyncio
import httpx
from typing import Dict, Any, Optional, List
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part

logger = logging.getLogger(__name__)

# 기본 타임아웃 설정 (초)
DEFAULT_TIMEOUT = 120


class VertexAIClient:
    """Vertex AI Gemini 2.5 Flash 클라이언트"""

    def __init__(self):
        """
        Vertex AI 초기화

        환경 변수 필요:
        - GOOGLE_CLOUD_PROJECT: GCP 프로젝트 ID
        - GOOGLE_CLOUD_LOCATION: GCP 리전 (예: us-central1)
        - GOOGLE_APPLICATION_CREDENTIALS: 서비스 계정 JSON 파일 경로
        """
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT 환경 변수가 설정되지 않았습니다")

        try:
            vertexai.init(project=self.project_id, location=self.location)
            self.model = GenerativeModel("gemini-2.5-flash")
            logger.info(f"✅ Vertex AI 초기화 완료 (프로젝트: {self.project_id}, 위치: {self.location})")
        except Exception as e:
            logger.error(f"❌ Vertex AI 초기화 실패: {e}")
            raise

    def _sync_generate_content(
        self,
        prompt: str,
        generation_config: GenerationConfig
    ) -> str:
        """
        동기 방식으로 Gemini API 호출 (to_thread에서 사용)
        """
        response = self.model.generate_content(
            prompt,
            generation_config=generation_config
        )
        return response.text

    async def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 8192,
        top_p: float = 0.95,
        top_k: int = 40,
        timeout: int = DEFAULT_TIMEOUT
    ) -> str:
        """
        Gemini 2.5 Flash로 텍스트 생성 (비동기 + 타임아웃)

        Args:
            prompt: 프롬프트
            temperature: 창의성 조절 (0.0~1.0)
            max_output_tokens: 최대 출력 토큰 수
            top_p: 누적 확률 임계값
            top_k: Top-K 샘플링
            timeout: 타임아웃 (초, 기본 120초)

        Returns:
            생성된 텍스트
        """
        try:
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                top_p=top_p,
                top_k=top_k
            )

            # 동기 호출을 별도 스레드에서 실행 + 타임아웃 적용
            response_text = await asyncio.wait_for(
                asyncio.to_thread(
                    self._sync_generate_content,
                    prompt,
                    generation_config
                ),
                timeout=timeout
            )

            return response_text

        except asyncio.TimeoutError:
            logger.error(f"❌ Vertex AI 응답 타임아웃 ({timeout}초)")
            raise Exception(f"Vertex AI 응답 타임아웃 ({timeout}초)")
        except Exception as e:
            logger.error(f"❌ Vertex AI 콘텐츠 생성 실패: {e}")
            raise Exception(f"Vertex AI 생성 실패: {str(e)}")

    async def generate_json(
        self,
        prompt: str,
        temperature: float = 0.5,
        max_output_tokens: int = 8192
    ) -> Dict[str, Any]:
        """
        JSON 형식 응답 생성

        Args:
            prompt: 프롬프트 (JSON 형식 요청 포함 필요)
            temperature: 창의성 조절
            max_output_tokens: 최대 출력 토큰 수

        Returns:
            파싱된 JSON 딕셔너리
        """
        try:
            response_text = await self.generate_content(
                prompt=prompt,
                temperature=temperature,
                max_output_tokens=max_output_tokens
            )

            # JSON 추출 (```json 태그 제거)
            cleaned_text = response_text.strip()

            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text.replace('```json', '').replace('```', '').strip()
            elif cleaned_text.startswith('```'):
                cleaned_text = cleaned_text.replace('```', '').strip()

            # JSON 파싱
            parsed_json = json.loads(cleaned_text)
            return parsed_json

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 파싱 실패: {e}")
            logger.error(f"응답 텍스트: {response_text if 'response_text' in locals() else 'N/A'}")
            raise Exception("JSON 파싱 실패")
        except Exception as e:
            logger.error(f"❌ JSON 생성 실패: {e}")
            raise

    async def _download_image(self, url: str, timeout: int = 30) -> bytes:
        """
        URL에서 이미지 다운로드

        Args:
            url: 이미지 URL
            timeout: 다운로드 타임아웃 (초)

        Returns:
            이미지 바이트 데이터
        """
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    def _get_mime_type(self, url: str) -> str:
        """URL에서 MIME 타입 추론"""
        lower_url = url.lower()
        if '.png' in lower_url:
            return "image/png"
        elif '.gif' in lower_url:
            return "image/gif"
        elif '.webp' in lower_url:
            return "image/webp"
        else:
            return "image/jpeg"

    def _sync_generate_with_images(
        self,
        prompt: str,
        image_parts: List[Part],
        generation_config: GenerationConfig
    ) -> str:
        """
        이미지와 함께 동기 방식으로 Gemini API 호출
        """
        # 프롬프트와 이미지를 결합
        contents = image_parts + [prompt]
        response = self.model.generate_content(
            contents,
            generation_config=generation_config
        )
        return response.text

    async def analyze_images_with_prompt(
        self,
        image_urls: List[str],
        prompt: str,
        temperature: float = 0.3,
        max_output_tokens: int = 8192,
        timeout: int = DEFAULT_TIMEOUT
    ) -> Dict[str, Any]:
        """
        여러 이미지를 Gemini 멀티모달로 분석

        Args:
            image_urls: 이미지 URL 리스트 (최대 10개)
            prompt: 분석 프롬프트 (JSON 응답 요청 포함)
            temperature: 창의성 조절
            max_output_tokens: 최대 출력 토큰
            timeout: 타임아웃 (초)

        Returns:
            파싱된 JSON 딕셔너리
        """
        try:
            # 최대 10개 이미지로 제한
            urls_to_process = image_urls[:10]
            logger.info(f"🖼️ {len(urls_to_process)}개 이미지 다운로드 시작")

            # 이미지 다운로드 (병렬)
            image_parts = []
            for url in urls_to_process:
                try:
                    image_data = await self._download_image(url)
                    mime_type = self._get_mime_type(url)
                    image_parts.append(Part.from_data(image_data, mime_type=mime_type))
                    logger.info(f"✅ 이미지 다운로드 성공: {url[:50]}...")
                except Exception as e:
                    logger.warning(f"⚠️ 이미지 다운로드 실패 (건너뜀): {url[:50]}... - {e}")
                    continue

            if not image_parts:
                logger.error("❌ 다운로드된 이미지가 없습니다")
                raise Exception("분석할 이미지가 없습니다")

            logger.info(f"🎨 {len(image_parts)}개 이미지 Gemini 분석 시작")

            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                top_p=0.95,
                top_k=40
            )

            # 멀티모달 분석 실행
            response_text = await asyncio.wait_for(
                asyncio.to_thread(
                    self._sync_generate_with_images,
                    prompt,
                    image_parts,
                    generation_config
                ),
                timeout=timeout
            )

            # JSON 파싱
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text.replace('```json', '').replace('```', '').strip()
            elif cleaned_text.startswith('```'):
                cleaned_text = cleaned_text.replace('```', '').strip()

            parsed_json = json.loads(cleaned_text)
            logger.info("✅ 이미지 분석 완료")
            return parsed_json

        except asyncio.TimeoutError:
            logger.error(f"❌ 이미지 분석 타임아웃 ({timeout}초)")
            raise Exception(f"이미지 분석 타임아웃 ({timeout}초)")
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 파싱 실패: {e}")
            raise Exception("이미지 분석 JSON 파싱 실패")
        except Exception as e:
            logger.error(f"❌ 이미지 분석 실패: {e}")
            raise


# 싱글톤 인스턴스
_vertex_client: Optional[VertexAIClient] = None


def get_vertex_client() -> VertexAIClient:
    """
    Vertex AI 클라이언트 싱글톤 인스턴스 반환

    Returns:
        VertexAIClient 인스턴스
    """
    global _vertex_client

    if _vertex_client is None:
        _vertex_client = VertexAIClient()

    return _vertex_client
