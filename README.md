# Contents Creator - AI 기반 콘텐츠 제작 플랫폼

1인 기업 및 소상공인을 위한 AI 기반 콘텐츠 제작 및 멀티 플랫폼 관리 서비스

## 프로젝트 개요

Contents Creator는 LLM Agent를 활용하여 블로그, SNS, 동영상 콘텐츠를 자동으로 생성하고 Instagram, Facebook, YouTube, X(Twitter), Threads, TikTok, WordPress 등 다양한 플랫폼에 통합 발행할 수 있는 서비스입니다.

### 핵심 기능

- **AI 콘텐츠 생성**: Claude, Gemini를 활용한 블로그/SNS 콘텐츠 자동 생성
- **AI 이미지 생성**: Gemini 2.0 Flash, Stable Diffusion 기반 이미지 생성
- **AI 동영상 생성**: Replicate API (Stable Video Diffusion, LTX-Video) 기반 동영상 제작
- **카드뉴스 생성**: 자동 레이아웃 및 디자인 적용 카드뉴스 제작
- **브랜드 분석**: Multi-Agent Pipeline으로 블로그/Instagram/YouTube 콘텐츠 분석 및 스타일 추출
- **멀티 플랫폼 연동**: YouTube, Facebook, Instagram, X(Twitter), Threads, TikTok, WordPress OAuth 연동
- **AI 채팅 어시스턴트**: 대화형 콘텐츠 생성 인터페이스
- **크레딧 시스템**: 사용량 기반 크레딧 관리

---

## 기술 스택

### Frontend

| 기술 | 버전 | 용도 |
| :--- | :--- | :--- |
| React | 19.2.0 | UI 프레임워크 |
| React Router DOM | 7.9.5 | 클라이언트 라우팅 |
| Axios | 1.13.2 | API 통신 |
| React Markdown | 10.1.0 | 마크다운 렌더링 |
| React Icons | 5.5.0 | 아이콘 라이브러리 |
| CSS3 | - | 스타일링 |

### Backend

| 기술 | 버전 | 용도 |
| :--- | :--- | :--- |
| FastAPI | 0.115.0 | RESTful API 서버 |
| Uvicorn | 0.32.0 | ASGI 서버 |
| SQLAlchemy | 2.0.36 | ORM |
| Supabase (PostgreSQL) | - | 데이터베이스 |
| Python-JOSE | 3.3.0 | JWT 인증 |
| Authlib | 1.3.2 | OAuth 2.0 |
| Pydantic | 2.10.0 | 데이터 검증 |
| HTTPX | 0.28.1 | 비동기 HTTP 클라이언트 |
| Pillow | 11.0.0 | 이미지 처리 |
| MoviePy | 2.2.1 | 동영상 편집 |

### AI / ML

| 기술 | 용도 |
| :--- | :--- |
| Google Gemini API | 이미지 생성 (Gemini 2.0 Flash), 텍스트 생성, 프롬프트 최적화 |
| Anthropic Claude API | 콘텐츠 생성, 브랜드 분석, 품질 검증 |
| Google Vertex AI | Google Cloud 기반 AI 서비스 |
| Hugging Face | Stable Diffusion 2.1 이미지 생성 |
| Replicate API | AI 동영상 생성 (Stable Video Diffusion, LTX-Video) |
| FAL API | 이미지/동영상 생성 (대체 제공자) |

### SNS/플랫폼 연동

| 플랫폼 | 기능 |
| :--- | :--- |
| Google | 소셜 로그인 |
| Kakao | 소셜 로그인 |
| Facebook | 소셜 로그인, 페이지 연동, 콘텐츠 발행 |
| Instagram | 비즈니스 계정 연동, 콘텐츠 발행 |
| YouTube | 채널 연동, 동영상 분석, 업로드 |
| X (Twitter) | 계정 연동, 트윗 발행 |
| Threads | 계정 연동, 포스트 발행 |
| TikTok | 계정 연동, 동영상 업로드 |
| WordPress | 블로그 연동, 포스트 발행 |

---

## 프로젝트 구조

```
contents_creator/
├── backend/                           # FastAPI 백엔드
│   └── app/
│       ├── main.py                    # FastAPI 앱 설정 및 라우터 등록
│       ├── models.py                  # SQLAlchemy 모델 (40개)
│       ├── schemas.py                 # Pydantic 스키마
│       ├── database.py                # DB 연결 설정
│       ├── auth.py                    # JWT 인증
│       ├── oauth.py                   # OAuth 설정
│       ├── agents.py                  # Agentic AI 워크플로우
│       ├── routers/                   # API 라우터 (22개)
│       │   ├── auth.py                # 인증 API
│       │   ├── oauth.py               # OAuth 콜백
│       │   ├── user.py                # 사용자 프로필
│       │   ├── chat.py                # AI 채팅
│       │   ├── ai_content.py          # AI 콘텐츠 생성
│       │   ├── image.py               # 이미지 생성
│       │   ├── ai_video_generation.py # AI 동영상 생성
│       │   ├── brand_analysis.py      # 브랜드 분석
│       │   ├── cardnews.py            # 카드뉴스 생성
│       │   ├── sns_publish.py         # 멀티 플랫폼 발행
│       │   ├── onboarding.py          # 온보딩
│       │   ├── dashboard.py           # 대시보드
│       │   ├── credits.py             # 크레딧 시스템
│       │   ├── templates.py           # 템플릿 관리
│       │   ├── published_content.py   # 발행 콘텐츠 추적
│       │   ├── generated_videos.py    # 생성 동영상 관리
│       │   ├── ai_recommendations.py  # AI 추천
│       │   └── sns/                   # SNS 플랫폼별 라우터
│       │       ├── youtube.py         # YouTube 연동
│       │       ├── facebook.py        # Facebook 연동
│       │       ├── instagram.py       # Instagram 연동
│       │       ├── x.py               # X(Twitter) 연동
│       │       ├── threads.py         # Threads 연동
│       │       ├── tiktok.py          # TikTok 연동
│       │       ├── wordpress.py       # WordPress 연동
│       │       └── blog.py            # 네이버 블로그 분석
│       ├── services/                  # 비즈니스 로직 서비스
│       │   ├── ai_video_service.py    # AI 동영상 생성 서비스
│       │   ├── brand_analyzer_service.py  # 브랜드 분석 로직
│       │   ├── instagram_service.py   # Instagram API
│       │   ├── facebook_service.py    # Facebook API
│       │   ├── youtube_service.py     # YouTube API
│       │   ├── x_service.py           # X API
│       │   ├── threads_service.py     # Threads API
│       │   ├── naver_blog_service.py  # 네이버 블로그 스크래핑
│       │   └── supabase_storage.py    # Supabase 스토리지
│       ├── brand_agents/              # 브랜드 분석 Multi-Agent Pipeline
│       │   ├── pipeline.py            # 분석 파이프라인 오케스트레이션
│       │   ├── collectors.py          # 데이터 수집 에이전트
│       │   ├── analyzers.py           # 분석 에이전트
│       │   ├── synthesizer.py         # 결과 통합 에이전트
│       │   └── normalizer.py          # 데이터 정규화
│       ├── utils/                     # 유틸리티
│       │   ├── cardnews_renderer.py   # 카드뉴스 렌더링
│       │   └── vertex_ai_client.py    # Vertex AI 클라이언트
│       ├── prompts/                   # AI 프롬프트
│       └── system_prompts/            # 시스템 프롬프트
│
├── src/                               # React 프론트엔드
│   ├── pages/
│   │   ├── Home.js                    # 메인 AI 채팅 인터페이스
│   │   ├── auth/
│   │   │   ├── Login.js               # 로그인
│   │   │   └── OAuthCallback.js       # OAuth 콜백
│   │   ├── onboarding/
│   │   │   └── DynamicOnboarding.js   # 온보딩 (자동/수동 모드)
│   │   ├── content/
│   │   │   ├── ContentCreatorSimple.js  # 통합 콘텐츠 생성
│   │   │   ├── ContentEditor.js       # 콘텐츠 편집
│   │   │   ├── ContentHub.js          # 콘텐츠 허브
│   │   │   ├── ContentHistory.js      # 생성 이력
│   │   │   ├── ContentList.js         # 콘텐츠 목록
│   │   │   └── Templates.js           # 템플릿 관리
│   │   ├── connection_SNS/            # SNS 연동 페이지
│   │   │   ├── youtube/               # YouTube 채널 관리
│   │   │   ├── facebook/              # Facebook 페이지 관리
│   │   │   ├── instagram/             # Instagram 피드 관리
│   │   │   ├── x/                     # X(Twitter) 포스팅
│   │   │   ├── threads/               # Threads 연동
│   │   │   ├── tiktok/                # TikTok 연동
│   │   │   ├── wordpress/             # WordPress 블로그
│   │   │   └── common/                # 공통 컴포넌트
│   │   ├── dashboard/Dashboard.js     # 대시보드
│   │   ├── profile/MyPage.js          # 마이페이지
│   │   ├── settings/Settings.js       # 설정
│   │   ├── credits/                   # 크레딧 관리
│   │   └── legal/                     # 법적 고지
│   ├── components/
│   │   ├── Layout.js                  # 레이아웃
│   │   ├── Sidebar.js                 # 사이드바
│   │   ├── ProtectedRoute.js          # 인증 라우트
│   │   └── sns/                       # SNS 공통 컴포넌트
│   ├── contexts/
│   │   ├── AuthContext.js             # 인증 상태
│   │   └── ContentContext.js          # 콘텐츠 상태
│   └── services/
│       ├── api.js                     # API 클라이언트
│       ├── agenticService.js          # AI 콘텐츠 서비스
│       └── geminiService.js           # Gemini API
│
├── .env.example                       # 환경 변수 템플릿
├── package.json                       # npm 설정
└── README.md                          # 프로젝트 문서
```

---

## 데이터베이스 모델

### 사용자 관리 (2개)
- **User**: OAuth 정보, 비즈니스 정보, 타겟 고객 정보
- **UserPreference**: 텍스트/이미지/동영상 스타일 선호도

### 콘텐츠 (6개)
- **Content**: 블로그, 이미지, 동영상 통합 콘텐츠
- **ContentGenerationSession**: 콘텐츠 생성 세션 추적
- **GeneratedBlogContent**: 생성된 블로그 포스트
- **GeneratedSNSContent**: SNS 콘텐츠 (Instagram 등)
- **GeneratedXContent**: X(Twitter) 콘텐츠
- **GeneratedThreadsContent**: Threads 콘텐츠

### 이미지 & 동영상 (4개)
- **GeneratedImage**: 생성된 이미지
- **GeneratedCardnewsContent**: 카드뉴스 콘텐츠
- **VideoGenerationJob**: 동영상 생성 작업 추적
- **GeneratedVideo**: 생성된 동영상

### 브랜드 분석 (1개)
- **BrandAnalysis**: 멀티 플랫폼 브랜드 프로필

### 채팅 (2개)
- **ChatSession**: AI 채팅 세션
- **ChatMessage**: 채팅 메시지

### SNS 연동 (14개)
- **YouTubeConnection / YouTubeVideo / YouTubeAnalytics**: YouTube 연동
- **FacebookConnection / FacebookPost**: Facebook 연동
- **InstagramConnection / InstagramPost**: Instagram 연동
- **XConnection / XPost**: X(Twitter) 연동
- **ThreadsConnection / ThreadsPost**: Threads 연동
- **TikTokConnection / TikTokVideo**: TikTok 연동
- **WordPressConnection / WordPressPost**: WordPress 연동

### 발행 추적 (1개)
- **PublishedContent**: 모든 플랫폼 발행 콘텐츠 통합 추적

### 크레딧 시스템 (3개)
- **UserCredit**: 사용자 크레딧 잔액
- **CreditTransaction**: 크레딧 거래 이력
- **CreditPackage**: 크레딧 구매 패키지

### 템플릿 (2개)
- **TemplateTab**: 템플릿 카테고리
- **Template**: 콘텐츠 템플릿

---

## 시작하기

### 요구사항

- Node.js 18.x 이상
- Python 3.10 이상
- npm 9.x 이상
- Supabase 계정 (PostgreSQL 데이터베이스)

### 설치 및 실행

1. **레포지토리 복제**
   ```bash
   git clone https://github.com/KernelAcademy-AICamp/ai-camp-2nd-llm-agent-service-project-contents-team.git
   cd ai-camp-2nd-llm-agent-service-project-contents-team
   ```

2. **프론트엔드 의존성 설치**
   ```bash
   npm install
   ```

3. **백엔드 설정**
   ```bash
   npm run setup:backend
   ```

4. **환경 변수 설정**
   ```bash
   cp .env.example .env
   ```

   `.env` 파일 설정:
   ```env
   # ===== Backend Configuration =====
   SECRET_KEY=your-secret-key-here-change-this-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # Database (Supabase PostgreSQL)
   DATABASE_URL=postgresql://postgres.YOUR_PROJECT_REF:YOUR_PASSWORD@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres
   ENV=development
   CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

   # ===== OAuth 2.0 =====
   # Google
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/oauth/google/callback

   # Kakao
   KAKAO_CLIENT_ID=your-kakao-rest-api-key
   KAKAO_REDIRECT_URI=http://localhost:8000/api/oauth/kakao/callback

   # Facebook
   FACEBOOK_CLIENT_ID=your-facebook-app-id
   FACEBOOK_CLIENT_SECRET=your-facebook-app-secret
   FACEBOOK_REDIRECT_URI=http://localhost:8000/api/oauth/facebook/callback

   # X (Twitter)
   X_CLIENT_ID=your-x-client-id
   X_CLIENT_SECRET=your-x-client-secret

   # ===== AI API Keys =====
   GOOGLE_API_KEY=your-google-api-key
   ANTHROPIC_API_KEY=your-anthropic-api-key
   HUGGINGFACE_API_KEY=your-huggingface-api-key
   REPLICATE_API_TOKEN=your-replicate-api-token

   # Frontend
   REACT_APP_GEMINI_API_KEY=your-gemini-api-key

   # ===== Google Cloud (Optional) =====
   GOOGLE_APPLICATION_CREDENTIALS=secrets/google-cloud-key.json
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=asia-northeast1
   ```

5. **개발 서버 실행**
   ```bash
   npm start
   ```
   - 프론트엔드: http://localhost:3000
   - 백엔드 API: http://localhost:8000
   - API 문서: http://localhost:8000/docs

### 개별 실행

```bash
# 프론트엔드만
npm run start:frontend

# 백엔드만
npm run start:backend
```

### 프로덕션 빌드

```bash
npm run build
```

---

## Supabase 데이터베이스 설정

### 1. Supabase 프로젝트 생성

1. [Supabase](https://supabase.com)에 접속하여 계정 생성
2. 새 프로젝트 생성 (Region: Northeast Asia - Seoul 권장)
3. 프로젝트 생성 완료 후 데이터베이스 비밀번호 저장

### 2. 데이터베이스 연결 정보 확인

Supabase 대시보드 → Settings → Database에서 Connection string 확인:

```env
DATABASE_URL=postgresql://postgres.YOUR_PROJECT_REF:YOUR_PASSWORD@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres
```

### 3. Connection Pooling (권장)

Supabase는 Connection Pooler를 제공합니다:
- **Transaction mode (포트 6543)**: 일반적인 사용에 권장
- **Session mode (포트 5432)**: 장기 연결이 필요한 경우

### 4. Supabase Storage (선택)

이미지/동영상 저장을 위해 Supabase Storage 사용 가능:

```env
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

---

## API 엔드포인트

### 인증
- `GET /api/auth/me` - 현재 사용자 정보
- `PUT /api/auth/me` - 사용자 정보 수정
- `POST /api/auth/logout` - 로그아웃
- `POST /api/auth/refresh-token` - 토큰 갱신
- `GET /api/oauth/{provider}/login` - OAuth 로그인 시작
- `GET /api/oauth/{provider}/callback` - OAuth 콜백

### AI 콘텐츠
- `POST /api/ai-content/save` - AI 생성 콘텐츠 저장
- `GET /api/ai-content/history` - 생성 이력 조회
- `POST /api/chat` - AI 채팅
- `GET /api/chat/{session_id}/messages` - 채팅 메시지 조회

### 이미지 생성
- `POST /api/image/generate` - 이미지 생성
- `POST /api/image/optimize-prompt` - 프롬프트 최적화

### 동영상 생성
- `POST /api/ai-video/generate` - 동영상 생성 시작
- `GET /api/ai-video/status/{job_id}` - 생성 상태 조회
- `GET /api/videos/history` - 동영상 이력

### 카드뉴스
- `POST /api/cardnews/generate` - 카드뉴스 생성
- `GET /api/cardnews/{id}` - 카드뉴스 조회

### 브랜드 분석
- `POST /api/brand-analysis/analyze` - 브랜드 분석 실행
- `GET /api/brand-analysis/{user_id}` - 분석 결과 조회

### SNS 연동
- `GET /api/youtube/connect` - YouTube 연동
- `GET /api/facebook/connect` - Facebook 연동
- `GET /api/instagram/connect` - Instagram 연동
- `GET /api/x/connect` - X(Twitter) 연동
- `GET /api/threads/connect` - Threads 연동
- `GET /api/tiktok/connect` - TikTok 연동
- `GET /api/wordpress/connect` - WordPress 연동
- `POST /api/sns/publish` - 통합 SNS 발행

### 크레딧
- `GET /api/credits/packages` - 크레딧 패키지 목록
- `GET /api/credits/balance` - 현재 크레딧 잔액
- `POST /api/credits/purchase` - 크레딧 구매
- `GET /api/credits/transactions` - 거래 이력

### 템플릿
- `GET /api/templates` - 템플릿 목록
- `POST /api/templates` - 템플릿 생성
- `PUT /api/templates/{id}` - 템플릿 수정
- `DELETE /api/templates/{id}` - 템플릿 삭제

### 발행 콘텐츠
- `GET /api/published` - 발행 콘텐츠 목록
- `GET /api/published/{id}` - 발행 콘텐츠 상세

---

## 주요 기능 상세

### 1. AI 채팅 어시스턴트
- Gemini API 기반 대화형 콘텐츠 생성
- 사용자 비즈니스 컨텍스트 자동 반영
- 채팅 세션 저장 및 불러오기
- 콘텐츠 아이디어 생성 및 제안

### 2. AI 콘텐츠 생성 (Agentic Workflow)

Multi-Agent 워크플로우를 통한 고품질 콘텐츠 생성:

| 에이전트 | 역할 |
| :--- | :--- |
| ContentPlannerAgent | 콘텐츠 계획 수립 |
| ContentEnricherAgent | 콘텐츠 작성 |
| QualityAssuranceAgent | 품질 검증 |
| VisualDesignerAgent | 비주얼 최적화 |
| OrchestratorAgent | 전체 워크플로우 조정 |

플랫폼별 자동 생성:
- 블로그 포스트 (Markdown)
- SNS 캡션 (Instagram, Facebook)
- 트윗 (X/Twitter)
- Threads 포스트
- YouTube 설명

### 3. AI 이미지 생성
- Google Gemini 2.0 Flash (기본)
- Hugging Face Stable Diffusion 2.1 (대체)
- 브랜드 분석 기반 프롬프트 자동 강화
- 스타일 선호도 적용

### 4. AI 동영상 생성
- **텍스트 → 동영상**: LTX-Video (Replicate)
- **이미지 → 동영상**: Stable Video Diffusion
- 생성 진행 상태 실시간 추적
- 동영상 메타데이터 저장

### 5. 카드뉴스 생성
- AI 기반 콘텐츠 구조화
- 자동 레이아웃 적용
- 다양한 템플릿 지원
- 이미지 렌더링 및 내보내기

### 6. 브랜드 분석 (Multi-Agent Pipeline)

플랫폼별 분석:
- **네이버 블로그**: 글쓰기 스타일, 구조, 톤 분석
- **Instagram**: 이미지 스타일, 색상 팔레트, 해시태그 패턴
- **YouTube**: 콘텐츠 스타일, 제목 패턴, 썸네일 특성

추출 요소:
- 브랜드 톤앤매너, 가치관, 성격
- 타겟 고객층, 핵심 주제
- 색상 팔레트, 이미지 스타일
- 키워드 패턴, 해시태그 사용법

### 7. 멀티 플랫폼 발행
- Instagram + Facebook 동시 발행
- X(Twitter) 트윗 포스팅
- YouTube 동영상 업로드
- Threads 포스트 발행
- TikTok 동영상 업로드
- WordPress 블로그 포스트 발행
- 발행 이력 통합 추적

### 8. 온보딩 프로세스

**자동 모드**:
- 블로그 URL 입력 → 자동 스크래핑 및 분석
- 비즈니스 정보 자동 추론

**수동 모드**:
- 비즈니스 정보 직접 입력
- 텍스트/이미지 샘플 업로드
- 스타일 선호도 수동 설정

### 9. 크레딧 시스템

| 패키지 | 크레딧 | 보너스 |
| :--- | :--- | :--- |
| 스타터 | 50 | - |
| 베이직 | 120 | +20 |
| 스탠다드 | 300 | +50 |
| 프로 | 700 | +100 |
| 엔터프라이즈 | 1500 | +300 |

---

## 아키텍처

### Frontend
- **라우팅**: React Router DOM
- **상태 관리**: React Context API (AuthContext, ContentContext)
- **API 통신**: Axios 인스턴스 + 인터셉터 (자동 토큰 관리)
- **스타일**: CSS3

### Backend
- **프레임워크**: FastAPI (ASGI 비동기)
- **데이터베이스**: SQLAlchemy ORM + Supabase PostgreSQL
- **스토리지**: Supabase Storage
- **API 스타일**: RESTful
- **인증**: JWT + OAuth 2.0
- **미들웨어**: CORS, SessionMiddleware

### Agentic AI
- **패턴**: Multi-Agent Workflow
- **Brand Analysis Pipeline**: DataCollector → StyleAnalyzer → BrandSynthesizer

---

## 팀 정보

| 이름 | GitHub |
| :--- | :--- |
| 기유진 | - |
| 김종주 | jonjour99 |
| 오화영 | - |

---

## License

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).
