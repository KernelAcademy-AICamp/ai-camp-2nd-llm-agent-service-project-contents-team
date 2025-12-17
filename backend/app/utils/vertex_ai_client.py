"""
Vertex AI Gemini 2.5 Flash 클라이언트 유틸리티

브랜드 분석을 위한 Vertex AI API 헬퍼 함수 제공
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

logger = logging.getLogger(__name__)


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
            self.model = GenerativeModel("gemini-2.0-flash-exp")
            logger.info(f"✅ Vertex AI 초기화 완료 (프로젝트: {self.project_id}, 위치: {self.location})")
        except Exception as e:
            logger.error(f"❌ Vertex AI 초기화 실패: {e}")
            raise

    async def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 8192,
        top_p: float = 0.95,
        top_k: int = 40
    ) -> str:
        """
        Gemini 2.5 Flash로 텍스트 생성

        Args:
            prompt: 프롬프트
            temperature: 창의성 조절 (0.0~1.0)
            max_output_tokens: 최대 출력 토큰 수
            top_p: 누적 확률 임계값
            top_k: Top-K 샘플링

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

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )

            return response.text

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
