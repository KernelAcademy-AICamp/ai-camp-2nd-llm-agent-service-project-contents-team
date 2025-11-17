# 나노바나나(Claude) 이미지 생성 기능 가이드

## 개요

나노바나나(Claude) 모델을 선택하면 다음과 같이 동작합니다:

1. **사용자 프롬프트 입력** - 간단한 설명 입력 (한글/영어 가능)
2. **Claude가 프롬프트 최적화** - 전문적인 이미지 생성 프롬프트로 변환
3. **Stable Diffusion이 이미지 생성** - 최적화된 프롬프트로 고품질 이미지 생성

### 나노바나나의 역할

Claude(나노바나나)는 직접 이미지를 생성하지 않고, **프롬프트 엔지니어 역할**을 합니다:

- 사용자의 간단한 설명을 전문적인 이미지 생성 프롬프트로 변환
- 스타일, 조명, 구도, 품질 등의 디테일 추가
- Stable Diffusion에 최적화된 프롬프트 생성

## 설정 방법

### 1. Anthropic API 키 발급

1. [Anthropic Console](https://console.anthropic.com/) 접속 및 회원가입
2. [API Keys](https://console.anthropic.com/settings/keys) 페이지로 이동
3. "Create Key" 클릭
4. 키 이름 입력 (예: `image-generation`)
5. 생성된 API 키를 **즉시 복사** (다시 볼 수 없습니다!)

### 2. .env 파일에 API 키 추가

[.env](.env) 파일을 열고 다음 줄을 수정하세요:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-여기에_실제_키를_붙여넣기
```

**전체 .env 파일 예시:**
```bash
# Hugging Face API Key (이미지 생성용)
HUGGINGFACE_API_KEY=hf_XxXxXxXxXxXxXxXxXxXx

# Anthropic API Key (나노바나나 - Claude로 프롬프트 최적화)
ANTHROPIC_API_KEY=sk-ant-api03-XxXxXxXxXxXxXxXxXxXx

PORT=5000
NODE_ENV=development
```

### 3. 서버 실행

```bash
# 개발 모드 (프론트엔드 + 백엔드 동시 실행)
npm run dev
```

또는 개별 실행:

```bash
# 터미널 1 - 백엔드
npm run server

# 터미널 2 - 프론트엔드
npm start
```

## 사용 방법

1. 브라우저에서 http://localhost:3000 접속
2. "이미지 생성" 탭 선택
3. AI 모델에서 **"나노바나나 (Nanovana)"** 선택
4. 프롬프트 입력 (한글로도 가능!)
   - 예: "바다 위의 석양"
   - 예: "A cute cat playing with yarn"
5. "이미지 생성하기" 클릭
6. Claude가 프롬프트를 최적화한 후 이미지 생성

## 프롬프트 최적화 예시

### 입력 (사용자):
```
바다 위의 석양
```

### 출력 (Claude 최적화):
```
A breathtaking sunset over the ocean, golden hour lighting, vibrant orange and pink sky reflecting on calm water, photorealistic, highly detailed, 8k resolution, professional photography, cinematic composition
```

### 입력 (사용자):
```
귀여운 고양이
```

### 출력 (Claude 최적화):
```
Adorable fluffy kitten with big eyes, soft fur texture, playful pose, studio lighting, highly detailed, kawaii style, pastel colors, professional pet photography, 8k, masterpiece quality
```

## 나노바나나 vs 제미나이

| 특징 | 나노바나나 (Claude) | 제미나이 (Gemini) |
|------|-------------------|------------------|
| 프롬프트 최적화 | ✅ Claude가 자동 최적화 | ❌ 프롬프트 그대로 사용 |
| 한글 프롬프트 | ✅ 한글 입력 가능 (자동 영어 변환) | ⚠️ 영어 권장 |
| 이미지 품질 | ⭐⭐⭐⭐⭐ (프롬프트 최적화로 향상) | ⭐⭐⭐ (사용자 프롬프트 의존) |
| API 비용 | Anthropic API 사용 (유료) | HuggingFace만 사용 (무료) |

## 비용 안내

### Anthropic API
- **무료 크레딧**: 신규 가입 시 $5 무료 제공
- **프롬프트 최적화 비용**: 약 $0.001-0.003 per 요청
- **100회 이미지 생성 시**: 약 $0.10-0.30

### Hugging Face API
- **무료 티어**: 월 1,000회 요청 무료
- **프로덕션**: 유료 플랜 필요

## Anthropic API 없이 사용하기

Anthropic API 키를 설정하지 않아도 이미지 생성은 가능합니다:

1. `.env`에서 `ANTHROPIC_API_KEY`를 설정하지 않거나 주석 처리
2. 나노바나나 모델 선택 시 프롬프트 최적화 없이 바로 Stable Diffusion 사용
3. 서버 로그에 "⚠️ Anthropic API 키가 없어 프롬프트 최적화를 건너뜁니다" 메시지 표시

**권장사항**: 더 나은 이미지 품질을 위해 Anthropic API 키 설정을 권장합니다.

## 트러블슈팅

### "Anthropic API 인증 실패"
- `.env` 파일에 올바른 API 키가 입력되었는지 확인
- API 키가 `sk-ant-api03-`로 시작하는지 확인
- [Anthropic Console](https://console.anthropic.com/settings/keys)에서 키가 활성화되어 있는지 확인
- 서버 재시작 (`Ctrl+C` 후 `npm run dev`)

### "이미지 생성에 실패했습니다"
- Hugging Face API 키도 필요합니다 ([IMAGE_GENERATION_SETUP.md](IMAGE_GENERATION_SETUP.md) 참고)
- 백엔드 서버가 실행 중인지 확인
- 브라우저 콘솔과 서버 터미널 로그 확인

### 프롬프트 최적화가 작동하지 않음
- `.env` 파일에 `ANTHROPIC_API_KEY`가 설정되어 있는지 확인
- 서버 로그에서 "🤖 Claude로 프롬프트 최적화 중..." 메시지 확인
- API 크레딧 잔액 확인

## 개발자 정보

### 서버 로그 확인

나노바나나 모드에서 이미지 생성 시 다음 로그를 확인할 수 있습니다:

```
🤖 Claude로 프롬프트 최적화 중...
✨ 최적화된 프롬프트: A breathtaking sunset over the ocean...
```

### API 엔드포인트

**POST** `/api/generate-image`

**Request:**
```json
{
  "prompt": "바다 위의 석양",
  "model": "nanovana"
}
```

**Response:**
```json
{
  "success": true,
  "imageUrl": "data:image/png;base64,...",
  "message": "이미지가 성공적으로 생성되었습니다.",
  "optimizedPrompt": "A breathtaking sunset over the ocean...",
  "usedClaudeOptimization": true
}
```

## 추가 리소스

- [Anthropic API 문서](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [Stable Diffusion 프롬프트 가이드](https://stable-diffusion-art.com/prompt-guide/)
- [Hugging Face Inference API](https://huggingface.co/docs/api-inference/index)
