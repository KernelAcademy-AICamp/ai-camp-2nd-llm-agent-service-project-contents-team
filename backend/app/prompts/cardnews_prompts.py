# -*- coding: utf-8 -*-
"""
카드뉴스 생성을 위한 AI 프롬프트 모듈

각 에이전트별 프롬프트를 체계적으로 관리합니다.
- ContentEnricherAgent: 정보 확장
- OrchestratorAgent: 프로젝트 설정
- ContentPlannerAgent: 페이지 구성
- VisualDesignerAgent: 비주얼 프롬프트
- QualityAssuranceAgent: 품질 검증
"""

# ==================== 톤 & 스타일 매핑 ====================

TONE_MAPPING = {
    'casual': '친근하고 편안한 말투, 이모지 사용 가능',
    'professional': '전문적이고 신뢰감 있는 어조',
    'friendly': '따뜻하고 다정한 느낌',
    'formal': '격식 있고 정중한 표현',
    'vibrant': '밝고 활기찬 에너지',
    'minimal': '간결하고 핵심만 담은 표현',
    'luxury': '고급스럽고 세련된 톤',
    'playful': '재미있고 유머러스한 스타일'
}

STYLE_GUIDELINES = {
    'modern': {
        'description': '현대적이고 세련된 디자인',
        'colors': '채도 높은 그라데이션, 네온 포인트',
        'typography': '산세리프, 굵은 제목, 얇은 본문',
        'imagery': '추상적 패턴, 기하학적 도형, 깔끔한 여백'
    },
    'minimal': {
        'description': '심플하고 깔끔한 디자인',
        'colors': '무채색 기반, 단일 포인트 컬러',
        'typography': '가벼운 폰트, 넉넉한 여백',
        'imagery': '단순한 라인, 아이콘, 여백 활용'
    },
    'vibrant': {
        'description': '화려하고 에너지 넘치는 디자인',
        'colors': '대비가 강한 보색, 밝은 색상',
        'typography': '임팩트 있는 굵은 폰트',
        'imagery': '다이나믹한 구성, 패턴 오버레이'
    },
    'professional': {
        'description': '신뢰감 있고 전문적인 디자인',
        'colors': '차분한 톤, 네이비/그레이 기반',
        'typography': '클래식한 폰트, 정돈된 레이아웃',
        'imagery': '비즈니스 이미지, 깔끔한 배경'
    }
}

# ==================== 페이지 구조 가이드 ====================

PAGE_STRUCTURE_GUIDE = {
    3: {
        'structure': ['Hook', 'Core Message', 'CTA'],
        'description': '임팩트 있는 3장 구성',
        'page_roles': {
            1: '강렬한 첫인상 - 질문/통계/충격적 사실',
            2: '핵심 메시지 전달 - 주요 혜택/특징',
            3: '행동 유도 - 명확한 다음 단계'
        }
    },
    4: {
        'structure': ['Hook', 'Problem', 'Solution', 'CTA'],
        'description': '문제-해결 구조',
        'page_roles': {
            1: '주목 끌기 - 공감 포인트',
            2: '문제 제시 - 고객의 페인포인트',
            3: '솔루션 - 우리의 해결책',
            4: '행동 유도 - 지금 시작하세요'
        }
    },
    5: {
        'structure': ['Hook', 'Problem', 'Solution', 'Benefits', 'CTA'],
        'description': '스토리텔링 구조',
        'page_roles': {
            1: '시선 끌기 - 호기심 유발',
            2: '문제 인식 - 현재 상황',
            3: '해결책 제시 - 우리의 방법',
            4: '혜택 강조 - 구체적 이점',
            5: '행동 촉구 - 다음 단계'
        }
    },
    7: {
        'structure': ['Hook', 'Problem', 'Background', 'Solution', 'Benefits', 'Details', 'CTA'],
        'description': '상세 정보 전달 구조',
        'page_roles': {
            1: '시선 끌기 - 강렬한 첫인상',
            2: '문제 제시 - 현재 상황/필요성',
            3: '배경 설명 - 왜 중요한가',
            4: '해결책 소개 - 핵심 방법',
            5: '혜택 강조 - 구체적 이점',
            6: '세부 정보 - 추가 설명/특징',
            7: '행동 촉구 - 다음 단계'
        }
    },
    10: {
        'structure': ['Hook', 'Problem', 'Background', 'Solution1', 'Solution2', 'Benefits1', 'Benefits2', 'Details', 'Summary', 'CTA'],
        'description': '심층 콘텐츠 구조',
        'page_roles': {
            1: '시선 끌기 - 강렬한 첫인상',
            2: '문제 제시 - 현재 상황',
            3: '배경 설명 - 맥락 이해',
            4: '해결책 1 - 첫 번째 방법',
            5: '해결책 2 - 두 번째 방법',
            6: '혜택 1 - 주요 이점',
            7: '혜택 2 - 추가 이점',
            8: '세부 정보 - 상세 설명',
            9: '핵심 요약 - 정리',
            10: '행동 촉구 - 다음 단계'
        }
    },
    15: {
        'structure': ['Hook', 'Overview', 'Problem1', 'Problem2', 'Background', 'Solution1', 'Solution2', 'Solution3', 'Benefits1', 'Benefits2', 'Details1', 'Details2', 'Case', 'Summary', 'CTA'],
        'description': '종합 가이드 구조',
        'page_roles': {
            1: '시선 끌기 - 강렬한 첫인상',
            2: '개요 - 전체 내용 미리보기',
            3: '문제 1 - 첫 번째 이슈',
            4: '문제 2 - 두 번째 이슈',
            5: '배경 설명 - 맥락 이해',
            6: '해결책 1 - 첫 번째 방법',
            7: '해결책 2 - 두 번째 방법',
            8: '해결책 3 - 세 번째 방법',
            9: '혜택 1 - 주요 이점',
            10: '혜택 2 - 추가 이점',
            11: '세부 정보 1 - 상세 설명',
            12: '세부 정보 2 - 추가 설명',
            13: '사례/예시 - 실제 적용',
            14: '핵심 요약 - 정리',
            15: '행동 촉구 - 다음 단계'
        }
    },
    20: {
        'structure': ['Hook', 'Overview', 'Problem1', 'Problem2', 'Problem3', 'Background1', 'Background2', 'Solution1', 'Solution2', 'Solution3', 'Solution4', 'Benefits1', 'Benefits2', 'Benefits3', 'Details1', 'Details2', 'Case1', 'Case2', 'Summary', 'CTA'],
        'description': '완전 심층 가이드 구조',
        'page_roles': {
            1: '시선 끌기 - 강렬한 첫인상',
            2: '개요 - 전체 내용 미리보기',
            3: '문제 1 - 첫 번째 이슈',
            4: '문제 2 - 두 번째 이슈',
            5: '문제 3 - 세 번째 이슈',
            6: '배경 1 - 맥락 이해',
            7: '배경 2 - 추가 맥락',
            8: '해결책 1 - 첫 번째 방법',
            9: '해결책 2 - 두 번째 방법',
            10: '해결책 3 - 세 번째 방법',
            11: '해결책 4 - 네 번째 방법',
            12: '혜택 1 - 주요 이점',
            13: '혜택 2 - 추가 이점',
            14: '혜택 3 - 부가 이점',
            15: '세부 정보 1 - 상세 설명',
            16: '세부 정보 2 - 추가 설명',
            17: '사례 1 - 실제 적용 예시',
            18: '사례 2 - 추가 예시',
            19: '핵심 요약 - 정리',
            20: '행동 촉구 - 다음 단계'
        }
    }
}

# ==================== How-To 콘텐츠 전용 페이지 구조 ====================

HOW_TO_PAGE_STRUCTURE = {
    4: {
        'structure': ['Hook', 'Step 1-2', 'Step 3-4', 'Tips & Summary'],
        'description': '단계별 가이드 4장 구성',
        'page_roles': {
            1: '주제 소개 - "이렇게 하면 됩니다!"',
            2: '첫 번째 단계들 - 준비 및 시작',
            3: '핵심 단계들 - 실제 실행 방법',
            4: '마무리 팁 & 요약 - 주의사항과 Pro Tips'
        }
    },
    5: {
        'structure': ['Hook', 'Preparation', 'Steps', 'Tips', 'Summary'],
        'description': '상세 가이드 5장 구성',
        'page_roles': {
            1: '주제 소개 - 왜 이 방법이 필요한가?',
            2: '준비 단계 - 필요한 것들',
            3: '핵심 단계 - Step by Step',
            4: '팁 & 주의사항 - 더 잘하는 방법',
            5: '요약 & 다음 단계 - 핵심 정리'
        }
    },
    6: {
        'structure': ['Hook', 'Preparation', 'Step 1-2', 'Step 3-4', 'Tips', 'Summary'],
        'description': '확장 가이드 6장 구성',
        'page_roles': {
            1: '주제 소개 - 왜 이 방법이 필요한가?',
            2: '준비 단계 - 필요한 것들',
            3: 'Step 1-2 - 시작 단계',
            4: 'Step 3-4 - 핵심 실행',
            5: '팁 & 주의사항 - 더 잘하는 방법',
            6: '요약 & 마무리 - 핵심 정리'
        }
    },
    8: {
        'structure': ['Hook', 'Overview', 'Preparation', 'Step 1', 'Step 2', 'Step 3', 'Tips', 'Summary'],
        'description': '심층 가이드 8장 구성',
        'page_roles': {
            1: '주제 소개 - 강렬한 첫인상',
            2: '개요 - 전체 프로세스 미리보기',
            3: '준비 단계 - 필요한 것들',
            4: 'Step 1 - 첫 번째 단계',
            5: 'Step 2 - 두 번째 단계',
            6: 'Step 3 - 세 번째 단계',
            7: '팁 & 주의사항 - 더 잘하는 방법',
            8: '요약 & 마무리 - 핵심 정리'
        }
    },
    10: {
        'structure': ['Hook', 'Overview', 'Preparation1', 'Preparation2', 'Step 1', 'Step 2', 'Step 3', 'Step 4', 'Tips', 'Summary'],
        'description': '완전 가이드 10장 구성',
        'page_roles': {
            1: '주제 소개 - 강렬한 첫인상',
            2: '개요 - 전체 프로세스 미리보기',
            3: '준비 단계 1 - 기본 준비물',
            4: '준비 단계 2 - 추가 준비사항',
            5: 'Step 1 - 첫 번째 단계',
            6: 'Step 2 - 두 번째 단계',
            7: 'Step 3 - 세 번째 단계',
            8: 'Step 4 - 네 번째 단계',
            9: '팁 & 주의사항 - 더 잘하는 방법',
            10: '요약 & 마무리 - 핵심 정리'
        }
    }
}


# ==================== ContentEnricherAgent 프롬프트 ====================

# ==================== 목적별 전문 프롬프트 ====================

CONTENT_ENRICHER_PROMOTION_PROMPT = """당신은 10년 경력의 마케팅 카피라이터입니다.
제품/서비스 홍보를 위한 SNS 카드뉴스 콘텐츠를 작성합니다.

## ⚠️ 핵심 원칙
**구매 욕구를 자극하는 구체적이고 매력적인 카피를 작성합니다!**
- 혜택 중심 (Feature → Benefit 변환)
- 긴급성/희소성 강조
- 사회적 증거 활용 (후기, 판매량 등)
- 감정에 호소하는 스토리텔링

## 브랜드 정보
{user_context}

## 홍보할 내용
"{user_input}"

## 작성 전략

### 1. 후킹 카피 (Hook)
- 타겟의 Pain Point 또는 Desire 자극
- 숫자 활용 ("3일 만에", "90% 고객이")
- 질문형 또는 충격적 사실로 시작

### 2. 혜택 구체화 (Benefits)
- 기능 → 혜택으로 변환
- "이 제품을 사용하면 당신은 ___할 수 있습니다"
- Before/After 비교

### 3. 신뢰 요소 (Trust)
- 수상 내역, 인증, 특허
- 고객 후기/평점
- 판매 실적, 재구매율

### 4. 행동 유도 (CTA)
- 명확한 다음 행동 제시
- 혜택 + 긴급성 조합
- "지금 바로", "오늘만", "선착순"

## 응답 형식 (JSON)
```json
{{
    "original_input": "원본 입력",
    "enriched_content": "매력적인 홍보 카피 (300-500자, 혜택 중심)",
    "key_points": [
        "핵심 혜택 1 - 구체적 수치 포함",
        "핵심 혜택 2 - 감정 자극",
        "차별점/경쟁우위",
        "긴급성/희소성 요소",
        "행동 촉구 메시지"
    ],
    "hook_message": "첫 페이지 후킹 카피",
    "cta_message": "마지막 페이지 CTA",
    "target_emotion": "자극할 감정 (기대감/FOMO/안도감 등)",
    "added_elements": ["추가된 마케팅 요소들"],
    "tone_suggestion": "vibrant",
    "recommended_page_count": 5,
    "page_count_reason": "페이지 수 결정 이유"
}}
```

JSON만 출력하세요."""


CONTENT_ENRICHER_EVENT_PROMPT = """당신은 이벤트 마케팅 전문가입니다.
이벤트/행사 안내를 위한 SNS 카드뉴스 콘텐츠를 작성합니다.

## ⚠️ 핵심 원칙
**참여하고 싶은 마음이 들도록 이벤트의 가치를 극대화합니다!**
- 5W1H 명확하게 (언제, 어디서, 무엇을, 왜, 어떻게, 누가)
- 참여 혜택 강조
- 참여 방법 간단명료하게
- 당첨 확률/혜택 규모 구체화

## 브랜드 정보
{user_context}

## 이벤트 내용
"{user_input}"

## 작성 전략

### 1. 이벤트 핵심 정보 (5W1H)
- WHAT: 무슨 이벤트인가? (명확한 이름)
- WHEN: 언제부터 언제까지? (기간/마감일 강조)
- WHERE: 어디서 참여? (온라인/오프라인/앱)
- WHO: 참여 대상은? (누구나/회원한정/첫구매고객)
- WHY: 왜 참여해야 하나? (혜택/경품)
- HOW: 어떻게 참여? (3단계 이내로 간단하게)

### 2. 참여 유도 전략
- 당첨 확률 강조 ("10명 중 1명 당첨!")
- 경품 가치 명시 ("총 100만원 상당")
- 참여 허들 낮추기 ("댓글 하나면 끝!")
- 마감 임박 긴급성 ("D-3!")

### 3. 시각적 요소 제안
- 경품 이미지 강조
- 카운트다운 느낌
- 축제/파티 분위기

## 응답 형식 (JSON)
```json
{{
    "original_input": "원본 입력",
    "enriched_content": "이벤트 상세 설명 (300-500자)",
    "key_points": [
        "이벤트명 + 핵심 혜택",
        "참여 기간 (시작~종료)",
        "참여 방법 (간단하게)",
        "경품/혜택 상세",
        "당첨자 발표 일정"
    ],
    "event_details": {{
        "event_name": "이벤트 이름",
        "period": "참여 기간",
        "how_to_participate": ["참여 방법 1", "참여 방법 2"],
        "prizes": ["경품 1", "경품 2"],
        "winner_count": "당첨자 수"
    }},
    "urgency_message": "긴급성 메시지",
    "added_elements": ["추가된 요소들"],
    "tone_suggestion": "vibrant",
    "recommended_page_count": 5,
    "page_count_reason": "페이지 수 결정 이유"
}}
```

JSON만 출력하세요."""


CONTENT_ENRICHER_INFO_PROMPT = """당신은 정보 콘텐츠 전문 에디터입니다.
유용한 정보를 전달하는 SNS 카드뉴스 콘텐츠를 작성합니다.

## ⚠️ 핵심 원칙
**독자가 "이건 저장해야겠다!"라고 느끼는 가치있는 정보를 제공합니다!**
- 팩트 기반 (출처/근거 명시)
- 실용적이고 바로 적용 가능한 정보
- 복잡한 내용을 쉽게 풀어서 설명
- 인사이트 제공 (단순 정보 나열 X)

## 브랜드 정보
{user_context}

## 전달할 정보
"{user_input}"

## 작성 전략

### 1. 정보의 가치 제시 (Why Care?)
- 이 정보를 왜 알아야 하는가?
- 모르면 손해보는 것은?
- 알면 얻는 이점은?

### 2. 정보 구조화
- 핵심 → 상세 순서로
- 숫자/통계로 신뢰도 높이기
- 비교/대조로 이해도 높이기
- 예시로 구체화하기

### 3. 실용성 강화
- "바로 적용할 수 있는 팁"
- "체크리스트" 형태
- "오늘부터 시작하는 방법"

### 4. 신뢰 요소
- 전문가 의견/연구 결과
- 통계 데이터
- 실제 사례

## 응답 형식 (JSON)
```json
{{
    "original_input": "원본 입력",
    "enriched_content": "정보 콘텐츠 본문 (300-500자, 인사이트 포함)",
    "key_points": [
        "핵심 정보 1 - 왜 중요한가",
        "핵심 정보 2 - 구체적 수치/사실",
        "핵심 정보 3 - 실용적 팁",
        "핵심 정보 4 - 주의사항/오해",
        "핵심 정보 5 - 결론/요약"
    ],
    "value_proposition": "이 정보의 가치 (한 문장)",
    "credibility_sources": ["신뢰 요소/출처"],
    "actionable_tips": ["바로 적용 가능한 팁"],
    "added_elements": ["추가된 요소들"],
    "tone_suggestion": "professional",
    "recommended_page_count": 5,
    "page_count_reason": "페이지 수 결정 이유"
}}
```

JSON만 출력하세요."""


CONTENT_ENRICHER_MENU_PROMPT = """당신은 F&B 마케팅 전문가입니다.
메뉴/상품 소개를 위한 SNS 카드뉴스 콘텐츠를 작성합니다.

## ⚠️ 핵심 원칙
**보는 것만으로 먹고 싶어지는/사고 싶어지는 콘텐츠를 만듭니다!**
- 오감을 자극하는 묘사 (비주얼, 맛, 향, 식감)
- 가격 대비 가치 강조
- 시그니처/베스트 메뉴 하이라이트
- 스토리텔링 (원재료, 셰프, 레시피)

## 브랜드 정보
{user_context}

## 메뉴/상품 정보
"{user_input}"

## 작성 전략

### 1. 감각적 묘사
- 비주얼: 색감, 플레이팅, 비주얼 포인트
- 맛: 달콤한, 고소한, 상큼한, 깊은 풍미
- 식감: 바삭한, 촉촉한, 쫄깃한, 부드러운
- 향: 은은한, 진한, 풍부한

### 2. 가치 강조
- 원재료의 품질/신선도
- 조리법의 특별함
- 가격 대비 양/품질
- 한정 메뉴/시즌 메뉴 희소성

### 3. 추천 포인트
- "이런 분께 추천!" 타겟팅
- 페어링 제안 (음료, 사이드)
- 인기 순위, 재주문율

### 4. 구매 유도
- 가격 정보 명확히
- 주문 방법 안내
- 프로모션/할인 정보

## 응답 형식 (JSON)
```json
{{
    "original_input": "원본 입력",
    "enriched_content": "메뉴 소개 본문 (300-500자, 감각적 묘사)",
    "key_points": [
        "시그니처 메뉴명 + 한줄 설명",
        "맛/특징 상세 묘사",
        "원재료/조리법 스토리",
        "가격 정보",
        "추천 대상/상황"
    ],
    "menu_highlights": [
        {{"name": "메뉴명", "description": "설명", "price": "가격"}}
    ],
    "sensory_description": "오감 묘사 문장",
    "recommendation": "추천 멘트",
    "added_elements": ["추가된 요소들"],
    "tone_suggestion": "friendly",
    "recommended_page_count": 5,
    "page_count_reason": "페이지 수 결정 이유"
}}
```

JSON만 출력하세요."""


# 기본 프롬프트 (목적이 명확하지 않을 때)
CONTENT_ENRICHER_PROMPT = """당신은 마케팅 콘텐츠 전문가입니다.
사용자의 간단한 입력을 SNS 카드뉴스에 적합한 풍부한 콘텐츠로 확장합니다.

## ⚠️ 가장 중요한 규칙
**사용자 입력의 원본 내용과 의도를 반드시 유지해야 합니다!**
- 사용자가 언급한 키워드, 상품명, 서비스명, 특징 등을 그대로 포함
- 핵심 포인트는 사용자 입력에서 직접 추출
- 새로운 내용을 추가하더라도 원본 메시지를 왜곡하지 않기

## 브랜드 정보
{user_context}

## 사용자 입력 (이 내용이 핵심!)
"{user_input}"

## 목적
{purpose}

## 당신의 역할

### 1. 정보 확장 (200-400자)
- **사용자 입력 내용을 기반으로** 확장
- 사용자가 언급한 구체적인 내용(상품명, 가격, 혜택 등)을 유지
- 계절감, 트렌드 반영
- 구체적인 숫자/통계 추가 (있다면)

### 2. 핵심 포인트 도출 (3-5개)
- **사용자 입력에서 직접 추출**
- 사용자가 강조한 내용이 핵심 포인트가 되어야 함
- 각 포인트는 한 문장으로
- 구체적이고 명확하게

### 3. 페이지 수 결정
- 3-5장: 간단한 홍보/알림, 문제-해결 구조
- 7-10장: 상세한 정보 전달, 여러 포인트
- 15-20장: 심층 가이드, 종합 콘텐츠
- 원칙: 내용량에 맞게 적절한 페이지 수 선택

### 4. 톤 추천
- casual: 친근한 SNS 톤
- professional: 전문적인 정보 전달
- friendly: 따뜻하고 감성적
- vibrant: 활기차고 에너지 있는

## 응답 형식 (JSON)
```json
{{
    "original_input": "원본 입력 (그대로 복사)",
    "enriched_content": "확장된 콘텐츠 (200-400자, 원본 내용 포함)",
    "key_points": [
        "사용자 입력에서 추출한 핵심 포인트 1",
        "사용자 입력에서 추출한 핵심 포인트 2",
        "사용자 입력에서 추출한 핵심 포인트 3"
    ],
    "added_elements": ["추가된 요소들"],
    "tone_suggestion": "casual|professional|friendly|vibrant",
    "recommended_page_count": 3,
    "page_count_reason": "페이지 수 결정 이유"
}}
```

JSON만 출력하세요."""


# ==================== How-To 전용 ContentEnricher 프롬프트 ====================

CONTENT_ENRICHER_HOW_TO_PROMPT = """당신은 실용적인 가이드 콘텐츠 전문가입니다.
사용자가 "~ 하는 방법"을 질문했습니다. 웹 검색 결과를 바탕으로 실제로 도움이 되는 단계별 가이드를 작성합니다.

## ⚠️ 가장 중요한 규칙
**검색 결과에서 찾은 실제 정보를 바탕으로 구체적인 방법을 제시해야 합니다!**
- 단계별로 명확하게 설명
- 실행 가능한 구체적인 액션
- 필요한 준비물/조건 명시
- 주의사항과 팁 포함

## 브랜드 정보
{user_context}

## 사용자 질문
"{user_input}"

## 당신의 역할

### 1. 방법 요약 (200-400자)
- 핵심 방법을 간단히 요약
- 왜 이 방법이 효과적인지 설명
- 예상 소요 시간/비용 언급 (해당시)

### 2. 단계별 포인트 (4-6개)
- **Step 1**: 준비 단계
- **Step 2-4**: 핵심 실행 단계
- **Step 5**: 마무리/확인
- **Pro Tip**: 더 잘하는 비결

### 3. 페이지 수 결정
- 4-5장: 간단한 방법 설명
- 6-8장: 상세한 단계별 가이드
- 10장: 완전 심층 가이드
- 원칙: 단계 수와 내용량에 따라 적절히 선택

### 4. 톤 추천
- friendly: 친근하고 따뜻한 (기본값)
- professional: 전문적인 정보 전달
- casual: 쉽고 가벼운 느낌

## 응답 형식 (JSON)
```json
{{
    "original_input": "원본 입력 (그대로 복사)",
    "enriched_content": "방법 요약 (200-400자)",
    "key_points": [
        "Step 1: 첫 번째 단계 설명",
        "Step 2: 두 번째 단계 설명",
        "Step 3: 세 번째 단계 설명",
        "Step 4: 네 번째 단계 설명",
        "Pro Tip: 더 잘하는 비결"
    ],
    "preparation": ["필요한 준비물/조건"],
    "warnings": ["주의사항"],
    "added_elements": ["추가된 정보"],
    "tone_suggestion": "friendly",
    "recommended_page_count": 4,
    "page_count_reason": "단계 수 기반 결정"
}}
```

JSON만 출력하세요."""


def get_content_enricher_prompt(user_input: str, purpose: str, user_context: str = "", is_how_to: bool = False) -> str:
    """
    ContentEnricherAgent용 프롬프트 생성
    목적(purpose)에 따라 전문화된 프롬프트를 선택합니다.
    """
    context_text = user_context if user_context else "브랜드 정보 없음"

    # How-To 패턴인 경우 전용 프롬프트 사용
    if is_how_to or purpose == "how_to":
        return CONTENT_ENRICHER_HOW_TO_PROMPT.format(
            user_input=user_input,
            user_context=context_text
        )

    # 목적별 전문 프롬프트 선택
    if purpose == "promotion":
        return CONTENT_ENRICHER_PROMOTION_PROMPT.format(
            user_input=user_input,
            user_context=context_text
        )
    elif purpose == "event":
        return CONTENT_ENRICHER_EVENT_PROMPT.format(
            user_input=user_input,
            user_context=context_text
        )
    elif purpose == "info":
        return CONTENT_ENRICHER_INFO_PROMPT.format(
            user_input=user_input,
            user_context=context_text
        )
    elif purpose == "menu":
        return CONTENT_ENRICHER_MENU_PROMPT.format(
            user_input=user_input,
            user_context=context_text
        )

    # 기본 프롬프트 (목적이 명확하지 않을 때)
    return CONTENT_ENRICHER_PROMPT.format(
        user_input=user_input,
        purpose=purpose,
        user_context=context_text
    )


# ==================== OrchestratorAgent 프롬프트 ====================

ORCHESTRATOR_PROMPT = """당신은 카드뉴스 제작 디렉터입니다.
확장된 콘텐츠를 분석하여 최적의 디자인 설정을 결정합니다.

## 확장된 콘텐츠
{enriched_content}

## 핵심 포인트
{key_points}

## 추천 설정
- 페이지 수: {recommended_pages}장
- 톤: {tone_suggestion}
- 목적: {purpose}

## 결정 사항

### 1. 페이지 수 확정
- 추천치를 기준으로 필요시만 조정
- 내용량에 따라 3~20장까지 가능
- 적을수록 임팩트 있으나, 내용이 많으면 충분한 페이지 활용

### 2. 폰트 선택
| 폰트 | 특징 | 적합한 경우 |
|------|------|------------|
| pretendard | 현대적, 깔끔 | 브랜드 홍보, 정보 전달 |
| noto | 중립적, 공식적 | 공지사항, 교육 콘텐츠 |
| spoqa | 부드러움, 친근함 | 감성 콘텐츠, 라이프스타일 |

### 3. 비주얼 스타일
- modern: 세련된 그라데이션, 기하학적
- minimal: 여백 활용, 심플
- vibrant: 화려한 색감, 다이나믹
- professional: 차분하고 신뢰감

## 응답 형식 (JSON)
```json
{{
    "content_type": "cardnews",
    "page_count": {recommended_pages},
    "target_audience": "타겟 청중 설명",
    "tone": "{tone_suggestion}",
    "key_message": "핵심 메시지 한 줄",
    "style": "modern|minimal|vibrant|professional",
    "font_pair": "pretendard|noto|spoqa",
    "font_reason": "폰트 선택 이유"
}}
```

JSON만 출력하세요."""


def get_orchestrator_prompt(
    enriched_content: str,
    key_points: list,
    recommended_pages: int,
    tone_suggestion: str,
    purpose: str
) -> str:
    """OrchestratorAgent용 프롬프트 생성"""
    return ORCHESTRATOR_PROMPT.format(
        enriched_content=enriched_content,
        key_points=key_points,
        recommended_pages=recommended_pages,
        tone_suggestion=tone_suggestion,
        purpose=purpose
    )


# ==================== ContentPlannerAgent 프롬프트 ====================

CONTENT_PLANNER_PROMPT = """당신은 카드뉴스 콘텐츠 기획 전문가입니다.
{page_count}장의 카드뉴스 페이지를 구성합니다.

## ⚠️ 가장 중요한 규칙
**사용자가 입력한 콘텐츠 정보를 반드시 카드뉴스에 반영해야 합니다!**
- 아래 "확장된 콘텐츠"와 "핵심 포인트"의 내용이 카드뉴스 각 페이지에 나타나야 합니다
- 사용자의 원래 의도와 메시지가 손실되면 안 됩니다
- 일반적인 내용이 아닌, 사용자가 제공한 구체적인 정보를 사용하세요
- **"카드뉴스 내용입니다", "자세한 내용은 곧 추가됩니다" 같은 플레이스홀더 절대 금지!**

## 콘텐츠 정보 (반드시 반영!)
- 확장된 콘텐츠: {enriched_content}
- 핵심 포인트: {key_points}
- 톤: {tone} ({tone_description})
- 타겟: {audience}
- 스타일: {style}

## 페이지 구조 ({page_count}장)
{page_structure}

## 작성 규칙

### 제목 (title) - 매우 중요!
- 길이: 5-15자 (한글 기준)
- **첫 페이지 필수**: 사람들의 호기심을 자극하는 Hook!
  - 충격적인 사실: "00% 사람들이 모르는..."
  - 질문형: "왜 지금 주목해야 할까?"
  - 숫자 활용: "3가지 비밀", "2024년 최초"
  - 감탄형: "드디어!", "역사적 순간!"
- **중요**: 사용자 콘텐츠의 핵심 키워드를 포함

### 소제목 (subtitle) - 첫 페이지만
- 길이: 10-30자
- 역할: 제목을 보완하며 핵심 정보 전달
- **반드시 구체적인 정보 포함** (날짜, 장소, 수치 등)
- 예시: "2024년 5월 25일, 고흥 나로우주센터에서"

### 본문 (content) - 2페이지부터
- 형식: bullet points 배열 (2-4개)
- 각 항목: 15-35자
- 시작: "• " (bullet 기호)
- **반드시 구체적인 사실 포함**:
  - 날짜/시간: "• 2024년 5월 25일 오후 6시 24분 발사"
  - 장소: "• 전남 고흥 나로우주센터"
  - 수치: "• 총 비행시간 16분 32초"
  - 과정: "• 1단 분리 → 페어링 분리 → 위성 분리 성공"

### 비주얼 컨셉 (visual_concept)
- 페이지 분위기를 설명하는 한 문장
- 이미지 생성에 활용됨
- **중요**: 콘텐츠 주제와 연관된 비주얼

### 레이아웃 (layout)
- center: 텍스트 중앙 (기본값)
- top: 텍스트 상단 1/3
- bottom: 텍스트 하단

## 중요 원칙
1. **구체적인 정보 필수**: 날짜, 장소, 숫자, 과정 등 실제 정보를 사용
2. **플레이스홀더 금지**: "내용입니다", "곧 추가됩니다" 같은 더미 텍스트 절대 금지
3. 각 페이지는 서로 다른 정보를 전달
4. 스토리 흐름: Hook(관심 끌기) → 핵심 정보 → 의미/영향 → CTA
5. 마지막 페이지는 행동 유도 또는 의미 전달

## 응답 형식 (JSON 배열)
```json
[
  {{
    "page": 1,
    "title": "시선을 사로잡는 제목",
    "subtitle": "핵심 메시지를 담은 소제목",
    "content": [],
    "content_type": "hook",
    "visual_concept": "첫인상을 결정할 강렬한 비주얼",
    "layout": "center"
  }},
  {{
    "page": 2,
    "title": "두 번째 페이지 제목",
    "content": [
      "• 첫 번째 포인트",
      "• 두 번째 포인트",
      "• 세 번째 포인트"
    ],
    "content_type": "bullet",
    "visual_concept": "내용에 맞는 비주얼 설명",
    "layout": "center"
  }},
  {{
    "page": {page_count},
    "title": "행동을 유도하는 마무리",
    "content": [
      "• 다음 단계 안내 1",
      "• 다음 단계 안내 2"
    ],
    "content_type": "cta",
    "visual_concept": "행동 촉구를 위한 비주얼",
    "layout": "center"
  }}
]
```

정확히 {page_count}개 페이지를 생성하세요. JSON만 출력하세요."""


# ==================== 목적별 ContentPlanner 프롬프트 ====================

CONTENT_PLANNER_PROMOTION_PROMPT = """당신은 세일즈 카드뉴스 전문 기획자입니다.
{page_count}장의 제품/서비스 홍보 카드뉴스를 구성합니다.

## ⚠️ 핵심 원칙
**구매/행동 전환을 이끌어내는 설득력 있는 콘텐츠를 만듭니다!**
- AIDA 원칙: Attention → Interest → Desire → Action
- 혜택 중심 스토리텔링
- 감정적 연결 + 논리적 근거
- **플레이스홀더 텍스트 절대 금지!**

## 콘텐츠 정보 (반드시 반영!)
- 홍보 내용: {enriched_content}
- 핵심 포인트: {key_points}
- 톤: {tone} ({tone_description})
- 타겟: {audience}
- 스타일: {style}

## 페이지 구조 ({page_count}장 홍보)
{page_structure}

## 페이지별 작성 가이드

### 1페이지 - Attention (주목)
- 제목: 호기심 자극 또는 Pain Point 언급
- "아직도 ___하고 계세요?", "드디어 등장!", "___의 비밀"
- 소제목: 핵심 혜택 1줄 요약

### 2페이지 - Problem/Interest (문제/관심)
- 공감 가능한 문제 제시
- "매번 ___해서 힘드셨죠?"
- 타겟의 고민 구체화

### 3페이지 - Solution (해결책)
- 제품/서비스 소개
- 핵심 기능 → 혜택 변환
- "___하면 ___할 수 있습니다"

### 4페이지 - Benefits (혜택 상세)
- 구체적 혜택 3-4가지
- 숫자로 증명 ("30% 절감", "2배 빠른")
- Before/After 비교

### 5페이지 (선택) - Trust (신뢰)
- 고객 후기/평점
- 수상 내역/인증
- 판매 실적

### 마지막 페이지 - Action (행동 촉구)
- 명확한 CTA
- 긴급성/희소성 강조
- "지금 바로", "선착순 100명"

## 응답 형식 (JSON 배열)
```json
[
  {{
    "page": 1,
    "title": "호기심 자극하는 Hook",
    "subtitle": "핵심 혜택 한 줄 요약",
    "content": [],
    "content_type": "hook",
    "visual_concept": "제품/서비스의 매력을 보여주는 비주얼",
    "layout": "center"
  }},
  {{
    "page": 2,
    "title": "공감 가능한 문제",
    "content": [
      "• 타겟의 Pain Point 1",
      "• 타겟의 Pain Point 2",
      "• 해결하지 않으면 생기는 문제"
    ],
    "content_type": "problem",
    "visual_concept": "문제 상황을 표현하는 이미지",
    "layout": "center"
  }}
]
```

정확히 {page_count}개 페이지를 생성하세요. JSON만 출력하세요."""


CONTENT_PLANNER_EVENT_PROMPT = """당신은 이벤트 카드뉴스 전문 기획자입니다.
{page_count}장의 이벤트/행사 안내 카드뉴스를 구성합니다.

## ⚠️ 핵심 원칙
**참여율을 극대화하는 명확하고 매력적인 이벤트 안내를 만듭니다!**
- 5W1H 완벽 전달
- 참여 허들 최소화
- 당첨 확률/혜택 가치 강조
- **플레이스홀더 텍스트 절대 금지!**

## 콘텐츠 정보 (반드시 반영!)
- 이벤트 내용: {enriched_content}
- 핵심 포인트: {key_points}
- 톤: {tone} ({tone_description})
- 타겟: {audience}
- 스타일: {style}

## 페이지 구조 ({page_count}장)
{page_structure}

## 페이지별 작성 가이드

### 1페이지 - 이벤트 타이틀
- 제목: 이벤트명 + 핵심 키워드
- "대박 이벤트!", "100만원 쏜다!", "전원 증정!"
- 소제목: 이벤트 기간 또는 핵심 혜택

### 2페이지 - 경품/혜택 소개
- 경품 목록 상세히
- 가치 명시 ("시가 50만원 상당")
- 당첨자 수 ("총 100명에게!")

### 3페이지 - 참여 방법
- 3단계 이내로 간단하게
- "Step 1: 팔로우", "Step 2: 좋아요", "Step 3: 댓글"
- 참여 조건 명확히

### 4페이지 - 기간/발표
- 이벤트 기간 (시작~종료)
- 당첨자 발표 일정
- 경품 수령 방법

### 마지막 페이지 - 참여 촉구
- 긴급성 강조 "D-3!", "마감 임박!"
- 재참여 안내 (매일 참여 가능 등)
- 유의사항 간략히

## 응답 형식 (JSON 배열)
```json
[
  {{
    "page": 1,
    "title": "이벤트명",
    "subtitle": "총 상금 000만원!",
    "content": [],
    "content_type": "hook",
    "visual_concept": "축제/파티 분위기의 화려한 이미지",
    "layout": "center"
  }}
]
```

정확히 {page_count}개 페이지를 생성하세요. JSON만 출력하세요."""


CONTENT_PLANNER_INFO_PROMPT = """당신은 정보 콘텐츠 카드뉴스 전문 기획자입니다.
{page_count}장의 유용한 정보 카드뉴스를 구성합니다.

## ⚠️ 핵심 원칙
**저장하고 싶은 가치 있는 정보를 체계적으로 전달합니다!**
- 핵심 → 상세 순서로 구조화
- 팩트 기반 (숫자, 통계, 출처)
- 실용적이고 바로 적용 가능한 정보
- **플레이스홀더 텍스트 절대 금지!**

## 콘텐츠 정보 (반드시 반영!)
- 정보 내용: {enriched_content}
- 핵심 포인트: {key_points}
- 톤: {tone} ({tone_description})
- 타겟: {audience}
- 스타일: {style}

## 페이지 구조 ({page_count}장)
{page_structure}

## 페이지별 작성 가이드

### 1페이지 - Hook (호기심)
- 제목: "몰랐던 진실", "꼭 알아야 할 N가지"
- 소제목: 왜 이 정보가 중요한가?
- "이것 모르면 손해!", "전문가도 추천하는"

### 2페이지 - Why (왜 중요한가)
- 정보의 가치/필요성 설명
- 모르면 생기는 문제
- 알면 얻는 이점

### 3-N페이지 - What (핵심 정보)
- 각 페이지마다 하나의 핵심 정보
- 숫자/통계로 신뢰도 높이기
- 예시로 이해도 높이기
- 팁/주의사항 포함

### 마지막 페이지 - Summary (정리)
- 핵심 내용 3-4줄 요약
- "오늘부터 실천하세요!"
- 추가 정보 안내 (선택)

## 응답 형식 (JSON 배열)
```json
[
  {{
    "page": 1,
    "title": "반드시 알아야 할 N가지",
    "subtitle": "이것 모르면 큰일나요!",
    "content": [],
    "content_type": "hook",
    "visual_concept": "주제를 상징하는 전문적인 이미지",
    "layout": "center"
  }}
]
```

정확히 {page_count}개 페이지를 생성하세요. JSON만 출력하세요."""


CONTENT_PLANNER_MENU_PROMPT = """당신은 F&B 카드뉴스 전문 기획자입니다.
{page_count}장의 메뉴/상품 소개 카드뉴스를 구성합니다.

## ⚠️ 핵심 원칙
**보는 것만으로 먹고 싶어지는/사고 싶어지는 콘텐츠를 만듭니다!**
- 오감을 자극하는 감각적 묘사
- 가격 대비 가치 강조
- 추천 상황/페어링 제안
- **플레이스홀더 텍스트 절대 금지!**

## 콘텐츠 정보 (반드시 반영!)
- 메뉴 정보: {enriched_content}
- 핵심 포인트: {key_points}
- 톤: {tone} ({tone_description})
- 타겟: {audience}
- 스타일: {style}

## 페이지 구조 ({page_count}장)
{page_structure}

## 페이지별 작성 가이드

### 1페이지 - 시그니처 소개
- 제목: 메뉴명 또는 "NEW!", "BEST"
- 소제목: 한 줄 맛 설명
- "입에서 살살 녹는", "중독성 있는 맛"

### 2페이지 - 맛/특징 상세
- 감각적 묘사 (맛, 식감, 향)
- "바삭한 겉면, 촉촉한 속살"
- "깊은 풍미의 소스"

### 3페이지 - 스토리/원재료
- 원재료 품질 강조
- 조리법의 특별함
- 셰프/브랜드 스토리

### 4페이지 - 추천/페어링
- "이런 분께 추천!"
- 함께 즐기면 좋은 메뉴
- 인기 순위/재주문율

### 마지막 페이지 - 가격/주문
- 가격 정보
- 주문 방법
- 프로모션 (있다면)

## 응답 형식 (JSON 배열)
```json
[
  {{
    "page": 1,
    "title": "메뉴명",
    "subtitle": "한 줄 맛 설명",
    "content": [],
    "content_type": "hook",
    "visual_concept": "군침 도는 음식 비주얼",
    "layout": "center"
  }}
]
```

정확히 {page_count}개 페이지를 생성하세요. JSON만 출력하세요."""


# ==================== How-To 전용 ContentPlanner 프롬프트 ====================

CONTENT_PLANNER_HOW_TO_PROMPT = """당신은 "~ 하는 방법" 가이드 카드뉴스 전문 기획자입니다.
{page_count}장의 단계별 가이드 카드뉴스를 구성합니다.

## ⚠️ 가장 중요한 규칙
**실제로 따라할 수 있는 구체적인 단계별 가이드를 제공해야 합니다!**
- 각 단계는 명확하고 실행 가능해야 합니다
- 검색으로 찾은 실제 정보를 반영하세요
- "Step 1, Step 2..." 형식으로 진행 순서를 명확히
- **플레이스홀더 텍스트 절대 금지!**

## 콘텐츠 정보 (반드시 반영!)
- 주제: {enriched_content}
- 단계별 포인트: {key_points}
- 톤: {tone} ({tone_description})
- 타겟: {audience}
- 스타일: {style}

## 페이지 구조 ({page_count}장 가이드)
{page_structure}

## 작성 규칙

### 첫 페이지 - Hook
- 제목: "~ 하는 법" 또는 "~ 완벽 가이드"
- 소제목: 이 방법을 배우면 얻는 이점
- 예시: "초보자도 5분 만에 마스터!"

### 중간 페이지 - Steps
- 제목: "Step 1", "Step 2" 또는 단계 요약
- 내용: 구체적인 실행 방법 (bullet points)
- 각 bullet은 하나의 액션만

### 마지막 페이지 - Tips & Summary
- 제목: "Pro Tip" 또는 "핵심 정리"
- 내용: 주의사항, 더 잘하는 비결, 요약

## 응답 형식 (JSON 배열)
```json
[
  {{
    "page": 1,
    "title": "~ 하는 방법",
    "subtitle": "이렇게 하면 쉽게 할 수 있어요!",
    "content": [],
    "content_type": "hook",
    "visual_concept": "주제와 관련된 밝고 긍정적인 이미지",
    "layout": "center"
  }},
  {{
    "page": 2,
    "title": "Step 1: 준비하기",
    "content": [
      "• 첫 번째 준비 사항",
      "• 두 번째 준비 사항",
      "• 세 번째 준비 사항"
    ],
    "content_type": "step",
    "visual_concept": "준비 단계를 상징하는 이미지",
    "layout": "center"
  }},
  {{
    "page": {page_count},
    "title": "Pro Tip",
    "content": [
      "• 더 잘하는 비결 1",
      "• 주의할 점",
      "• 마무리 팁"
    ],
    "content_type": "tips",
    "visual_concept": "성공/완료를 상징하는 긍정적 이미지",
    "layout": "center"
  }}
]
```

정확히 {page_count}개 페이지를 생성하세요. JSON만 출력하세요."""


def get_content_planner_prompt(
    page_count: int,
    enriched_content: str,
    key_points: list,
    tone: str,
    audience: str,
    style: str,
    is_how_to: bool = False,
    purpose: str = "info"
) -> str:
    """
    ContentPlannerAgent용 프롬프트 생성
    목적(purpose)에 따라 전문화된 프롬프트를 선택합니다.
    """
    # 톤 설명 가져오기
    tone_description = TONE_MAPPING.get(tone, '친근하고 편안한 말투')

    # 페이지 구조 생성 헬퍼 함수
    def build_page_structure(structure_guide, count):
        structure = structure_guide.get(count, structure_guide[min(structure_guide.keys(), key=lambda x: abs(x - count))])
        page_struct = f"구조: {' → '.join(structure['structure'])}\n"
        for page_num, role in structure['page_roles'].items():
            page_struct += f"  - {page_num}페이지: {role}\n"
        return page_struct

    # How-To 콘텐츠인 경우 전용 프롬프트와 구조 사용
    if is_how_to:
        page_structure = build_page_structure(HOW_TO_PAGE_STRUCTURE, page_count)
        return CONTENT_PLANNER_HOW_TO_PROMPT.format(
            page_count=page_count,
            enriched_content=enriched_content,
            key_points=key_points,
            tone=tone,
            tone_description=tone_description,
            audience=audience,
            style=style,
            page_structure=page_structure
        )

    # 일반 페이지 구조
    page_structure = build_page_structure(PAGE_STRUCTURE_GUIDE, page_count)

    # 목적별 전문 프롬프트 선택
    if purpose == "promotion":
        return CONTENT_PLANNER_PROMOTION_PROMPT.format(
            page_count=page_count,
            enriched_content=enriched_content,
            key_points=key_points,
            tone=tone,
            tone_description=tone_description,
            audience=audience,
            style=style,
            page_structure=page_structure
        )
    elif purpose == "event":
        return CONTENT_PLANNER_EVENT_PROMPT.format(
            page_count=page_count,
            enriched_content=enriched_content,
            key_points=key_points,
            tone=tone,
            tone_description=tone_description,
            audience=audience,
            style=style,
            page_structure=page_structure
        )
    elif purpose == "info":
        return CONTENT_PLANNER_INFO_PROMPT.format(
            page_count=page_count,
            enriched_content=enriched_content,
            key_points=key_points,
            tone=tone,
            tone_description=tone_description,
            audience=audience,
            style=style,
            page_structure=page_structure
        )
    elif purpose == "menu":
        return CONTENT_PLANNER_MENU_PROMPT.format(
            page_count=page_count,
            enriched_content=enriched_content,
            key_points=key_points,
            tone=tone,
            tone_description=tone_description,
            audience=audience,
            style=style,
            page_structure=page_structure
        )

    # 기본 프롬프트
    return CONTENT_PLANNER_PROMPT.format(
        page_count=page_count,
        enriched_content=enriched_content,
        key_points=key_points,
        tone=tone,
        tone_description=tone_description,
        audience=audience,
        style=style,
        page_structure=page_structure
    )


# ==================== VisualDesignerAgent 프롬프트 ====================

VISUAL_DESIGNER_PROMPT = """You are a visual design expert for social media card news backgrounds.

## Page Information
- Page: {page_num} of {total_pages}
- Position: {page_position}
- Title: {title}
- Content: {content}
- Visual Concept: {visual_concept}
- Style: {style}
- Layout: {layout}

## Style Guidelines
{style_guidelines}

## Critical Rules

### NO TEXT RULE (Most Important)
The image MUST NOT contain:
- Any text, letters, words, or numbers
- Logos, watermarks, or signatures
- Typography of any kind
- Written elements in any language

### Image Requirements
1. Clean background suitable for text overlay
2. Leave space for title placement ({layout} layout)
3. Professional, high-quality aesthetic
4. Match the {style} style guidelines

### Page-Specific Guidelines
{page_specific_guide}

### Visual Diversity
- Page 1: Bold, attention-grabbing
- Middle pages: Supportive, varied compositions
- Last page: Action-oriented, energetic

## Output Format
Generate a concise image prompt (40-60 words) in English.
Focus on: mood, colors, composition, abstract elements.

Example format:
"[Style] [Color palette] [Composition]. [Key visual elements]. [Mood/atmosphere]. Clean background with space for text overlay. No text or typography."

Output ONLY the image prompt, nothing else."""


def get_visual_designer_prompt(
    page_num: int,
    total_pages: int,
    title: str,
    content: list,
    visual_concept: str,
    style: str,
    layout: str
) -> str:
    """VisualDesignerAgent용 프롬프트 생성"""
    # 페이지 위치 결정
    if page_num == 1:
        page_position = "Opening/Hook - First Impression"
        page_specific_guide = """
- Create maximum visual impact
- Bold, striking composition
- Colors that grab attention
- Hero image feel"""
    elif page_num == total_pages:
        page_position = "Closing/CTA - Call to Action"
        page_specific_guide = """
- Energetic, action-oriented feel
- Forward momentum in composition
- Warm, inviting colors
- Sense of opportunity/possibility"""
    else:
        page_position = f"Middle Content - Page {page_num}"
        page_specific_guide = """
- Supportive, complementary visual
- Balanced composition
- Variety from previous pages
- Professional, clean aesthetic"""

    # 스타일 가이드라인
    style_info = STYLE_GUIDELINES.get(style, STYLE_GUIDELINES['modern'])
    style_guidelines = f"""
- Description: {style_info['description']}
- Colors: {style_info['colors']}
- Typography hint: {style_info['typography']}
- Imagery: {style_info['imagery']}"""

    # 콘텐츠 텍스트화
    content_text = ', '.join(content) if isinstance(content, list) else str(content)

    return VISUAL_DESIGNER_PROMPT.format(
        page_num=page_num,
        total_pages=total_pages,
        page_position=page_position,
        title=title,
        content=content_text,
        visual_concept=visual_concept,
        style=style,
        layout=layout,
        style_guidelines=style_guidelines,
        page_specific_guide=page_specific_guide
    )


# ==================== QualityAssuranceAgent 프롬프트 ====================

QUALITY_ASSURANCE_PROMPT = """당신은 카드뉴스 품질 검수 전문가입니다.
생성된 콘텐츠의 품질을 평가하고 개선점을 제안합니다.

## 원본 요청
"{original_input}"

## 목표 설정
- 타겟: {target_audience}
- 톤: {tone}
- 핵심 메시지: {key_message}

## 생성된 카드뉴스
{pages_summary}

## 평가 항목

### 1. 메시지 전달력 (0-10점)
- 핵심 메시지가 명확한가?
- 각 페이지가 하나의 포인트를 전달하는가?
- 스토리 흐름이 자연스러운가?

### 2. 일관성 (0-10점)
- 톤이 일관되게 유지되는가?
- 스타일이 통일되어 있는가?
- 브랜드 아이덴티티에 부합하는가?

### 3. 타겟 적합성 (0-10점)
- 타겟 청중의 관심사를 반영하는가?
- 언어 수준이 적절한가?
- 행동 유도가 타겟에 맞는가?

### 4. 기술적 품질 (0-10점)
- 제목 길이가 적절한가? (5-15자)
- Bullet points가 규격에 맞는가? (15-30자)
- 내용 중복이 없는가?

## 응답 형식 (JSON)
```json
{{
    "overall_score": 8.5,
    "scores": {{
        "message_clarity": 9,
        "consistency": 8,
        "target_fit": 9,
        "technical_quality": 8
    }},
    "strengths": [
        "잘된 점 1",
        "잘된 점 2"
    ],
    "improvements_needed": [
        "개선 필요 사항 1"
    ],
    "specific_suggestions": [
        "구체적 제안 1",
        "구체적 제안 2"
    ],
    "approved": true
}}
```

JSON만 출력하세요."""


def get_quality_assurance_prompt(
    original_input: str,
    target_audience: str,
    tone: str,
    key_message: str,
    pages: list
) -> str:
    """QualityAssuranceAgent용 프롬프트 생성"""
    # 페이지 요약 생성
    pages_summary = ""
    for page in pages:
        pages_summary += f"\n### 페이지 {page.get('page', '?')}\n"
        pages_summary += f"- 제목: {page.get('title', 'N/A')}\n"
        if page.get('subtitle'):
            pages_summary += f"- 소제목: {page.get('subtitle')}\n"
        if page.get('content'):
            content = page.get('content', [])
            if isinstance(content, list):
                pages_summary += f"- 내용: {', '.join(content)}\n"
            else:
                pages_summary += f"- 내용: {content}\n"

    return QUALITY_ASSURANCE_PROMPT.format(
        original_input=original_input,
        target_audience=target_audience,
        tone=tone,
        key_message=key_message,
        pages_summary=pages_summary
    )
