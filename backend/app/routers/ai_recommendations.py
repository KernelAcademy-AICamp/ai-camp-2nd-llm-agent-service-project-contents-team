from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from .. import models, auth
from ..database import get_db
import google.generativeai as genai
import os
import json

router = APIRouter(
    prefix="/api/ai",
    tags=["ai-recommendations"]
)

# Gemini 설정
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class InterestRecommendationRequest(BaseModel):
    brand_name: str
    business_type: str
    business_description: str
    age_range: str
    gender: str

class InterestRecommendationResponse(BaseModel):
    interests: List[str]
    reasoning: str

@router.post("/recommend-interests", response_model=InterestRecommendationResponse)
async def recommend_interests(
    request: InterestRecommendationRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI가 비즈니스 정보를 기반으로 타겟 고객의 관심사를 추천
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        prompt = f"""
당신은 마케팅 전문가입니다. 다음 비즈니스 정보를 분석하고 타겟 고객이 가질 만한 관심사 5개를 추천해주세요.

비즈니스 정보:
- 브랜드명: {request.brand_name}
- 업종: {request.business_type}
- 설명: {request.business_description}
- 타겟 연령: {request.age_range}
- 타겟 성별: {request.gender}

응답 형식 (JSON):
{{
    "interests": ["관심사1", "관심사2", "관심사3", "관심사4", "관심사5"],
    "reasoning": "추천 이유를 1-2문장으로 설명"
}}

한국어로 답변하세요. JSON 형식만 반환하세요.
"""

        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # JSON 파싱
        if result_text.startswith('```json'):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith('```'):
            result_text = result_text[3:-3].strip()

        result = json.loads(result_text)

        return InterestRecommendationResponse(
            interests=result['interests'][:5],
            reasoning=result.get('reasoning', '')
        )

    except Exception as e:
        print(f"Interest recommendation error: {e}")
        # 폴백: 기본 추천
        fallback_interests = {
            'food': ['음식', '카페', '건강', '라이프스타일', '여행'],
            'fashion': ['패션', '뷰티', '스타일', '쇼핑', '트렌드'],
            'health': ['운동', '건강', '웰빙', '다이어트', '영양'],
            'education': ['교육', '학습', '자기계발', '커리어', '독서'],
            'tech': ['기술', 'IT', '혁신', '스타트업', '개발'],
            'retail': ['쇼핑', '소비', '트렌드', '라이프스타일', '브랜드'],
            'service': ['서비스', '편의', '생활', '경험', '품질'],
        }

        interests = fallback_interests.get(request.business_type, ['일상', '트렌드', '문화', '여가', '소통'])

        return InterestRecommendationResponse(
            interests=interests,
            reasoning="비즈니스 유형을 기반으로 추천되었습니다."
        )


class BusinessQuestionRequest(BaseModel):
    business_type: str

class BusinessQuestion(BaseModel):
    question: str
    placeholder: str
    field_name: str

class BusinessQuestionsResponse(BaseModel):
    questions: List[BusinessQuestion]

# 업종별 맞춤 질문 데이터
BUSINESS_QUESTIONS = {
    'food': [
        {
            'question': '주요 메뉴나 제품은 무엇인가요?',
            'placeholder': '예: 수제 케이크, 건강식 도시락',
            'field_name': 'main_products'
        },
        {
            'question': '특별히 강조하고 싶은 특징이 있나요?',
            'placeholder': '예: 유기농 재료, 저칼로리',
            'field_name': 'special_features'
        },
    ],
    'fashion': [
        {
            'question': '주요 취급 브랜드나 스타일은?',
            'placeholder': '예: 캐주얼, 포멀, 스트릿',
            'field_name': 'style_category'
        },
        {
            'question': '어떤 시즌이나 상황에 어울리나요?',
            'placeholder': '예: 데일리룩, 오피스룩',
            'field_name': 'occasion'
        },
    ],
    'health': [
        {
            'question': '제공하는 주요 프로그램은?',
            'placeholder': '예: PT, 요가, 필라테스',
            'field_name': 'programs'
        },
        {
            'question': '트레이너나 시설의 특징은?',
            'placeholder': '예: 전문 자격증 보유, 최신 장비',
            'field_name': 'facilities'
        },
    ],
    'education': [
        {
            'question': '주요 강의 분야는?',
            'placeholder': '예: 영어, 코딩, 입시',
            'field_name': 'subjects'
        },
        {
            'question': '수강 대상은 누구인가요?',
            'placeholder': '예: 초등학생, 직장인, 취준생',
            'field_name': 'target_students'
        },
    ],
    'tech': [
        {
            'question': '제공하는 기술이나 서비스는?',
            'placeholder': '예: 웹 개발, 앱 개발, AI 솔루션',
            'field_name': 'tech_services'
        },
        {
            'question': '주요 고객층은?',
            'placeholder': '예: 스타트업, 중소기업, 개인',
            'field_name': 'client_type'
        },
    ],
    'retail': [
        {
            'question': '판매하는 주요 상품 카테고리는?',
            'placeholder': '예: 생활용품, 전자제품, 식품',
            'field_name': 'product_categories'
        },
        {
            'question': '온라인/오프라인 중 주력은?',
            'placeholder': '예: 온라인 쇼핑몰, 오프라인 매장',
            'field_name': 'sales_channel'
        },
    ],
    'service': [
        {
            'question': '제공하는 서비스 유형은?',
            'placeholder': '예: 청소, 배달, 수리',
            'field_name': 'service_type'
        },
        {
            'question': '서비스 지역이나 범위는?',
            'placeholder': '예: 서울 전지역, 전국',
            'field_name': 'service_area'
        },
    ],
}

@router.post("/business-questions", response_model=BusinessQuestionsResponse)
async def get_business_questions(
    request: BusinessQuestionRequest,
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    업종에 맞는 맞춤 질문 반환
    """
    questions = BUSINESS_QUESTIONS.get(request.business_type, [])

    if not questions:
        # 기본 질문
        questions = [
            {
                'question': '주요 제품이나 서비스는 무엇인가요?',
                'placeholder': '예: 제품명, 서비스명',
                'field_name': 'main_offering'
            },
            {
                'question': '특별히 강조하고 싶은 점은?',
                'placeholder': '예: 품질, 가격, 서비스',
                'field_name': 'unique_selling_point'
            },
        ]

    return BusinessQuestionsResponse(questions=questions)
