# 🤖 AI Agentic 카드뉴스 생성 API

## 📌 개요

사용자가 **간단한 텍스트 프롬프트만 입력**하면, 여러 AI 에이전트들이 협업하여 **자동으로 카드뉴스를 기획·생성**하는 시스템입니다.

## 🎯 AI Agentic 워크플로우

```
사용자 프롬프트 입력
         ↓
┌────────────────────────────────────────────┐
│   [Orchestrator Agent]                     │
│   - 프롬프트 분석                           │
│   - 페이지 수 결정                          │
│   - 타겟/톤/스타일 파악                      │
└────────────┬───────────────────────────────┘
             ↓
┌────────────────────────────────────────────┐
│   [Content Planner Agent]                  │
│   - 페이지별 제목/내용 기획                  │
│   - 스토리텔링 구조 설계                     │
│   - 비주얼 컨셉 제안                         │
└────────────┬───────────────────────────────┘
             ↓
┌────────────────────────────────────────────┐
│   [Visual Designer Agent]                  │
│   - 이미지 생성 프롬프트 최적화              │
│   - 레이아웃에 맞는 비주얼 설계              │
└────────────┬───────────────────────────────┘
             ↓
┌────────────────────────────────────────────┐
│   [Quality Assurance Agent]                │
│   - 콘텐츠 품질 검증                         │
│   - 일관성 체크                              │
│   - 개선사항 제안                            │
└────────────┬───────────────────────────────┘
             ↓
┌────────────────────────────────────────────┐
│   [Image Generation + Card Assembly]       │
│   - Gemini로 배경 이미지 생성               │
│   - 텍스트 오버레이                          │
│   - 최종 카드뉴스 완성                       │
└────────────────────────────────────────────┘
```

---

## 🔌 API 엔드포인트

### POST `/api/generate-agentic-cardnews`

AI Agentic 방식으로 카드뉴스 자동 생성

#### Request (Form Data)

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `prompt` | string | ✅ | - | 사용자 입력 프롬프트 (예: "새로운 카페 오픈 홍보") |
| `purpose` | string | ❌ | `info` | 목적: `promotion`, `menu`, `info`, `event` |
| `fontStyle` | string | ❌ | `rounded` | 폰트: `rounded`, `sharp` |
| `colorTheme` | string | ❌ | `warm` | 색상: `warm`, `cool`, `vibrant`, `minimal` |
| `generateImages` | boolean | ❌ | `true` | 배경 이미지 자동 생성 여부 |

#### Response (JSON)

```json
{
  "success": true,
  "cards": [
    "data:image/png;base64,...",
    "data:image/png;base64,...",
    "data:image/png;base64,..."
  ],
  "count": 3,
  "analysis": {
    "page_count": 3,
    "target_audience": "20-30대 직장인",
    "tone": "친근하고 전문적인",
    "style": "modern"
  },
  "quality_score": 8.5,
  "pages_info": [
    {
      "page": 1,
      "title": "새로운 시작",
      "content": "여러분을 위한 특별한 공간이 열립니다"
    },
    {
      "page": 2,
      "title": "프리미엄 커피",
      "content": "바리스타가 직접 내려드리는 스페셜티 커피"
    },
    {
      "page": 3,
      "title": "오픈 이벤트",
      "content": "첫 방문 시 아메리카노 1+1 무료"
    }
  ]
}
```

---

## 🧪 테스트 방법

### 1. cURL로 테스트

```bash
curl -X POST "http://localhost:8000/api/generate-agentic-cardnews" \
  -F "prompt=새로운 베이커리 카페 오픈 홍보" \
  -F "purpose=promotion" \
  -F "fontStyle=rounded" \
  -F "colorTheme=warm" \
  -F "generateImages=true"
```

### 2. Python으로 테스트

```python
import requests

url = "http://localhost:8000/api/generate-agentic-cardnews"

data = {
    "prompt": "새로운 베이커리 카페 오픈 홍보",
    "purpose": "promotion",
    "fontStyle": "rounded",
    "colorTheme": "warm",
    "generateImages": True
}

response = requests.post(url, data=data)
result = response.json()

print(f"생성된 카드 수: {result['count']}")
print(f"품질 점수: {result['quality_score']}/10")
print(f"타겟: {result['analysis']['target_audience']}")

# 이미지 저장
for i, card_base64 in enumerate(result['cards']):
    # Base64 디코딩 후 파일로 저장
    import base64
    image_data = card_base64.split(',')[1]
    with open(f"card_{i+1}.png", "wb") as f:
        f.write(base64.b64decode(image_data))
```

### 3. JavaScript (Fetch)로 테스트

```javascript
const formData = new FormData();
formData.append('prompt', '새로운 베이커리 카페 오픈 홍보');
formData.append('purpose', 'promotion');
formData.append('fontStyle', 'rounded');
formData.append('colorTheme', 'warm');
formData.append('generateImages', 'true');

fetch('http://localhost:8000/api/generate-agentic-cardnews', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => {
    console.log(`생성된 카드: ${data.count}장`);
    console.log(`품질 점수: ${data.quality_score}/10`);

    // 이미지 표시
    data.cards.forEach((card, index) => {
      const img = document.createElement('img');
      img.src = card;
      document.body.appendChild(img);
    });
  });
```

---

## 📖 사용 예시

### 예시 1: 프로모션 카드뉴스

**입력:**
```
prompt: "겨울 세일 50% 할인 이벤트"
purpose: "promotion"
```

**AI가 자동 생성하는 내용:**
- 페이지 1: "겨울 대박 세일" - "최대 50% 특별 할인"
- 페이지 2: "전 품목 할인" - "의류, 신발, 가방 모두 반값"
- 페이지 3: "지금 바로 방문" - "12월 31일까지 한정"

### 예시 2: 신메뉴 소개

**입력:**
```
prompt: "딸기 시즌 신메뉴 출시"
purpose: "menu"
```

**AI가 자동 생성하는 내용:**
- 페이지 1: "딸기의 계절" - "달콤한 봄이 왔어요"
- 페이지 2: "딸기 라떼" - "진짜 딸기로 만든 프리미엄 라떼"
- 페이지 3: "딸기 케이크" - "수제 생크림과 신선한 딸기"
- 페이지 4: "기간 한정" - "딸기 시즌에만 만나요"

### 예시 3: 정보 전달

**입력:**
```
prompt: "카페 운영 시간 변경 안내"
purpose: "info"
```

**AI가 자동 생성하는 내용:**
- 페이지 1: "운영시간 안내" - "더 나은 서비스를 위해"
- 페이지 2: "새 운영시간" - "평일 08:00-22:00, 주말 10:00-20:00"
- 페이지 3: "감사합니다" - "변함없는 사랑 부탁드립니다"

---

## 🎨 스타일 옵션

### Color Themes

| 테마 | 설명 | 추천 용도 |
|------|------|-----------|
| `warm` | 따뜻한 오렌지/레드 계열 | 프로모션, 할인, 이벤트 |
| `cool` | 시원한 블루 계열 | 전문적, 신뢰성, 정보 전달 |
| `vibrant` | 화려한 핑크/퍼플 계열 | 신제품, 트렌디, 젊은층 |
| `minimal` | 미니멀 그레이 계열 | 고급스러운, 세련된, 모던 |

### Font Styles

| 스타일 | 설명 |
|--------|------|
| `rounded` | 둥글고 친근한 느낌 (Noto Sans KR) |
| `sharp` | 날카롭고 임팩트 있는 느낌 (Black Han Sans) |

### Purpose (목적)

| 목적 | 배지 텍스트 | 설명 |
|------|-------------|------|
| `promotion` | "프로모션" | 할인, 이벤트 홍보 |
| `menu` | "신메뉴" | 신제품, 신메뉴 소개 |
| `info` | "정보" | 공지사항, 정보 전달 |
| `event` | "이벤트" | 행사, 이벤트 안내 |

---

## 🔑 환경 변수 설정

AI Agentic 기능을 사용하려면 다음 API 키가 필요합니다:

```bash
# .env 파일
ANTHROPIC_API_KEY=sk-ant-xxxxx     # Claude (필수)
GOOGLE_API_KEY=AIzaSyxxxxx         # Gemini (선택, 이미지 생성용)
```

- **ANTHROPIC_API_KEY**: 콘텐츠 기획, 품질 검증에 사용
- **GOOGLE_API_KEY**: 프롬프트 최적화, 배경 이미지 생성에 사용

---

## ⚙️ 작동 원리 상세

### 1단계: Orchestrator Agent
```python
# 사용자 프롬프트 분석
분석 결과 = {
    "page_count": 5,           # AI가 자동으로 결정
    "target_audience": "20-30대",
    "tone": "친근하고 밝은",
    "key_message": "신제품 출시",
    "style": "modern"
}
```

### 2단계: Content Planner Agent
```python
# 페이지별 콘텐츠 기획
페이지들 = [
    {
        "page": 1,
        "title": "새로운 시작",
        "content": "여러분을 위한 특별한 공간",
        "visual_concept": "밝은 배경에 로고",
        "layout": "title_center"
    },
    # ... 나머지 페이지
]
```

### 3단계: Visual Designer Agent
```python
# 이미지 프롬프트 최적화
for 페이지 in 페이지들:
    페이지['image_prompt'] = """
    Clean gradient background with geometric shapes,
    modern design, soft lighting, professional,
    bright and welcoming atmosphere, high quality
    """
```

### 4단계: Quality Assurance Agent
```python
# 품질 검증
검증 결과 = {
    "overall_score": 8.5,
    "message_clarity_score": 9,
    "consistency_score": 8,
    "needs_improvement": [2],
    "suggestions": ["페이지 2: 내용이 너무 길어요"]
}
```

### 5단계: Image Generation + Assembly
```python
# Gemini로 배경 이미지 생성
for 페이지 in 페이지들:
    배경_이미지 = gemini_generate_image(페이지['image_prompt'])

    # 텍스트 오버레이
    최종_카드 = 카드_생성(
        배경=배경_이미지,
        제목=페이지['title'],
        내용=페이지['content']
    )
```

---

## 🚀 성능 최적화

- **병렬 처리**: 여러 페이지의 이미지를 동시에 생성 가능
- **캐싱**: 동일한 프롬프트에 대한 분석 결과 캐싱
- **폴백 메커니즘**: API 실패 시 기본 배경 사용
- **타임아웃**: 120초 타임아웃으로 응답 보장

---

## 🐛 오류 처리

| 오류 코드 | 설명 | 해결 방법 |
|----------|------|-----------|
| 500 | AI 워크플로우 실패 | API 키 확인, 로그 확인 |
| 400 | 프롬프트 누락 | prompt 필드 전달 확인 |
| 503 | Gemini API 로딩 중 | 잠시 후 재시도 |

---

## 📊 응답 시간

- **분석 단계**: 2-3초
- **콘텐츠 기획**: 3-5초
- **이미지 생성**: 페이지당 5-10초
- **조립**: 1-2초

**총 예상 시간**: 3페이지 기준 약 30-40초

---

## 💡 팁

1. **구체적인 프롬프트**: "새 카페 오픈"보다 "강남역 스페셜티 커피 카페 오픈"이 더 좋은 결과
2. **목적 명시**: purpose를 정확히 지정하면 더 적합한 톤으로 생성
3. **이미지 생성 옵션**: 빠른 테스트 시 `generateImages=false` 사용
4. **품질 점수 활용**: 7점 미만이면 프롬프트를 더 구체화해보세요

---

## 📝 라이선스

이 API는 다음 AI 서비스를 활용합니다:
- Anthropic Claude 3.5 Sonnet
- Google Gemini 2.0 Flash

각 서비스의 이용 약관을 준수해야 합니다.
