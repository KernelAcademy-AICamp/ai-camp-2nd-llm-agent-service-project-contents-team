"""
Gemini AI 브랜드 분석 서비스

수집된 블로그 포스트를 분석하여 브랜드 특성 추출
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)


class BrandAnalyzerService:
    """Gemini를 사용한 브랜드 분석 서비스"""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    async def analyze_brand(self, posts: List[Dict[str, str]], business_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        블로그 포스트들을 분석하여 브랜드 특성 추출

        Args:
            posts: 수집된 블로그 포스트 목록
            business_info: 기존 비즈니스 정보 (있다면)

        Returns:
            브랜드 분석 결과 JSON
        """
        if not posts:
            raise ValueError("분석할 포스트가 없습니다")

        try:
            # 포스트들을 하나의 텍스트로 결합
            combined_text = self._prepare_analysis_text(posts)

            # 기존 비즈니스 정보를 컨텍스트로 추가
            context = ""
            if business_info:
                context = f"""
기존 비즈니스 정보:
- 브랜드명: {business_info.get('brand_name', '알 수 없음')}
- 업종: {business_info.get('business_type', '알 수 없음')}
- 비즈니스 설명: {business_info.get('business_description', '없음')}
"""

            # Gemini로 분석 요청
            prompt = f"""
당신은 브랜드 마케팅 전문가입니다. 아래 블로그 포스트들을 분석하여 이 브랜드의 특성을 파악해주세요.

{context}

===== 블로그 포스트 내용 =====
{combined_text}
================================

위 블로그 포스트들을 분석하여 다음 정보를 JSON 형식으로 추출해주세요:

{{
  "brand_tone": "브랜드 톤앤매너 (예: 친근하고 전문적인, 캐주얼한, 격식있는 등)",
  "writing_style": "글쓰기 스타일 특징 (예: ~해요체 사용, 이모티콘 활용, 스토리텔링 중심 등)",
  "key_themes": ["주요 주제1", "주요 주제2", "주요 주제3"],
  "target_audience": "추정되는 타겟 고객층 (예: 20-30대 여성, 자영업자, 부모님 등)",
  "brand_values": ["브랜드 가치1", "브랜드 가치2"],
  "content_structure": "콘텐츠 구조 패턴 (예: 도입-본론-결론, Q&A 형식, 리스트 형식 등)",
  "unique_features": ["이 브랜드만의 독특한 특징1", "특징2"],
  "keyword_frequency": {{
    "핵심키워드1": 빈도수,
    "핵심키워드2": 빈도수,
    "핵심키워드3": 빈도수
  }},
  "emotional_tone": "감정적 톤 (예: 따뜻한, 유머러스한, 진지한, 열정적인 등)",
  "call_to_action_style": "행동 유도 방식 (예: 직접적, 간접적, 질문형 등)",
  "image_usage_pattern": "이미지 사용 패턴 (추정)",
  "posting_topics": ["주로 다루는 주제 유형들"],
  "brand_personality": "브랜드 성격 종합 설명 (2-3문장)"
}}

**중요**: 반드시 위 JSON 형식으로만 응답해주세요. 다른 텍스트는 포함하지 마세요.
"""

            logger.info("Gemini로 브랜드 분석 요청 중...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # JSON 추출 (```json 태그 제거)
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()

            # JSON 파싱
            analysis = json.loads(response_text)

            logger.info("브랜드 분석 완료")
            return {
                "analysis": analysis,
                "analyzed_posts_count": len(posts),
                "total_content_length": len(combined_text)
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}")
            logger.error(f"응답 텍스트: {response_text if 'response_text' in locals() else 'N/A'}")
            raise Exception("브랜드 분석 결과를 파싱할 수 없습니다")
        except Exception as e:
            logger.error(f"브랜드 분석 중 오류: {e}")
            raise Exception(f"브랜드 분석 실패: {str(e)}")

    def _prepare_analysis_text(self, posts: List[Dict[str, str]], max_chars: int = 30000) -> str:
        """
        포스트들을 분석용 텍스트로 결합 (토큰 제한 고려)

        Args:
            posts: 포스트 목록
            max_chars: 최대 문자 수 (Gemini 토큰 제한 고려)

        Returns:
            결합된 텍스트
        """
        combined = []
        current_length = 0

        for i, post in enumerate(posts, 1):
            post_text = f"""
[포스트 {i}]
제목: {post['title']}
작성일: {post.get('date', '알 수 없음')}
내용:
{post['content'][:3000]}  # 각 포스트는 최대 3000자까지만
---
"""
            if current_length + len(post_text) > max_chars:
                logger.warning(f"텍스트 길이 제한 도달. {i-1}개 포스트만 분석에 사용")
                break

            combined.append(post_text)
            current_length += len(post_text)

        return '\n'.join(combined)

    async def generate_content_guidelines(self, brand_analysis: Dict[str, Any]) -> str:
        """
        브랜드 분석 결과를 바탕으로 콘텐츠 생성 가이드라인 생성

        Args:
            brand_analysis: 브랜드 분석 결과

        Returns:
            콘텐츠 생성 가이드라인 텍스트
        """
        analysis = brand_analysis.get('analysis', {})

        guidelines = f"""
# 콘텐츠 생성 가이드라인

## 톤앤매너
{analysis.get('brand_tone', '정보 없음')}

## 글쓰기 스타일
{analysis.get('writing_style', '정보 없음')}

## 타겟 고객
{analysis.get('target_audience', '정보 없음')}

## 주요 주제
{', '.join(analysis.get('key_themes', []))}

## 브랜드 가치
{', '.join(analysis.get('brand_values', []))}

## 감정적 톤
{analysis.get('emotional_tone', '정보 없음')}

## 행동 유도 스타일
{analysis.get('call_to_action_style', '정보 없음')}

## 브랜드 성격
{analysis.get('brand_personality', '정보 없음')}
"""
        return guidelines
