# 이미지 생성 기능 설정 가이드

## 문제 해결

이미지 생성 시 "이미지 생성에 실패했습니다" 오류가 발생하는 경우, 아래 단계를 따라 설정해주세요.

## 1. API 키 발급

### Hugging Face API 키 생성 (권장)

1. [Hugging Face](https://huggingface.co/) 회원가입
2. [Settings → Access Tokens](https://huggingface.co/settings/tokens) 페이지로 이동
3. "New token" 클릭
4. Token 이름 입력 (예: `image-generation`)
5. Role을 "read"로 선택
6. "Generate a token" 클릭
7. 생성된 토큰을 복사

## 2. 환경 변수 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 아래 내용을 추가하세요:

```bash
# .env 파일
HUGGINGFACE_API_KEY=여기에_발급받은_API_키를_붙여넣기
PORT=5000
NODE_ENV=development
```

**중요:** `.env` 파일은 절대 Git에 커밋하지 마세요! (이미 `.gitignore`에 추가되어 있습니다)

## 3. 서버 실행

### 방법 1: 개발 모드 (프론트엔드 + 백엔드 동시 실행)

```bash
npm run dev
```

이 명령어는 다음을 동시에 실행합니다:
- 백엔드 서버 (포트 5000)
- React 개발 서버 (포트 3000)

### 방법 2: 서버 개별 실행

터미널 1 - 백엔드 서버:
```bash
npm run server
```

터미널 2 - 프론트엔드:
```bash
npm start
```

## 4. 이미지 생성 테스트

1. 브라우저에서 http://localhost:3000 접속
2. 콘텐츠 유형에서 "이미지 생성" 선택
3. AI 모델 선택 (나노바나 또는 제미나이)
4. 프롬프트 입력 (예: "A beautiful sunset over the ocean with vibrant colors")
5. "이미지 생성하기" 버튼 클릭
6. 첫 번째 요청 시 모델 로딩으로 20-30초 정도 걸릴 수 있습니다

## 사용 가능한 AI 모델

### 1. Stable Diffusion XL (현재 구현)
- **모델:** stabilityai/stable-diffusion-xl-base-1.0
- **장점:** 고품질 이미지 생성, 무료 사용 가능
- **단점:** 첫 요청 시 모델 로딩 시간 필요
- **API 제공자:** Hugging Face Inference API

## 주의사항

1. **모델 로딩 시간**: 첫 번째 요청 시 모델이 로드되므로 20-30초 정도 소요될 수 있습니다. 이후 요청은 더 빠릅니다.

2. **무료 사용 한도**: Hugging Face의 무료 Inference API는 사용량 제한이 있습니다. 프로덕션 환경에서는 유료 플랜 고려가 필요합니다.

3. **프롬프트 작성 팁**:
   - 영어로 작성하면 더 좋은 결과를 얻을 수 있습니다
   - 구체적이고 상세한 설명을 포함하세요
   - 원하는 스타일, 색상, 분위기를 명시하세요

## 트러블슈팅

### 오류: "모델이 로딩 중입니다"
- **원인:** 모델이 아직 로드되지 않았습니다
- **해결:** 20-30초 후 다시 시도하세요

### 오류: "API 키 인증에 실패했습니다"
- **원인:** .env 파일의 API 키가 올바르지 않습니다
- **해결:**
  1. .env 파일이 프로젝트 루트에 있는지 확인
  2. API 키가 정확한지 확인
  3. 서버를 재시작

### 오류: "요청 시간이 초과되었습니다"
- **원인:** 네트워크 지연 또는 서버 과부하
- **해결:** 잠시 후 다시 시도하세요

### 서버 연결 오류
- **원인:** 백엔드 서버가 실행되지 않았습니다
- **해결:** `npm run server` 또는 `npm run dev` 실행

## 대안 API 옵션

### OpenAI DALL-E (유료)
더 높은 품질이 필요한 경우 OpenAI DALL-E를 사용할 수 있습니다.

### Stability AI (유료)
안정적인 프로덕션 환경이 필요한 경우 공식 Stability AI API를 사용할 수 있습니다.

## 추가 도움이 필요하신가요?

문제가 계속되면 다음을 확인해주세요:
1. Node.js 버전 (v14 이상 권장)
2. npm 패키지 설치 상태 (`npm install`)
3. 방화벽/프록시 설정
4. 서버 로그 확인 (터미널에서 에러 메시지 확인)
