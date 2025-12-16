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
    }
}


# ==================== ContentEnricherAgent 프롬프트 ====================

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
- 3장: 간단한 홍보/알림
- 4장: 문제-해결 구조
- 5장: 스토리텔링 필요 시
- 원칙: 적을수록 좋음. 불필요하게 늘리지 않기

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


def get_content_enricher_prompt(user_input: str, purpose: str, user_context: str = "") -> str:
    """ContentEnricherAgent용 프롬프트 생성"""
    context_text = user_context if user_context else "브랜드 정보 없음"
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
- 최대 5장 (절대 초과 금지)
- 적을수록 임팩트 있음

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


def get_content_planner_prompt(
    page_count: int,
    enriched_content: str,
    key_points: list,
    tone: str,
    audience: str,
    style: str
) -> str:
    """ContentPlannerAgent용 프롬프트 생성"""
    # 톤 설명 가져오기
    tone_description = TONE_MAPPING.get(tone, '친근하고 편안한 말투')

    # 페이지 구조 가이드 가져오기
    structure = PAGE_STRUCTURE_GUIDE.get(page_count, PAGE_STRUCTURE_GUIDE[3])
    page_structure = f"구조: {' → '.join(structure['structure'])}\n"
    for page_num, role in structure['page_roles'].items():
        page_structure += f"  - {page_num}페이지: {role}\n"

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
