# Contents Creator - AI 기반 콘텐츠 제작 플랫폼

1인 기업 및 소상공인을 위한 AI 기반 콘텐츠 제작 및 멀티 플랫폼 관리 서비스

## 프로젝트 개요

Contents Creator는 LLM Agent를 활용하여 블로그, SNS, 동영상 콘텐츠를 자동으로 생성하고 Instagram, Facebook, YouTube, X(Twitter) 등 다양한 플랫폼에 통합 관리할 수 있는 서비스입니다.

### 핵심 기능

- **AI 콘텐츠 생성**: Claude, Gemini를 활용한 블로그/SNS 콘텐츠 자동 생성
- **AI 이미지 생성**: Gemini 2.0 Flash, Stable Diffusion 기반 이미지 생성
- **AI 동영상 생성**: Replicate API (Stable Video Diffusion, LTX-Video) 기반 동영상 제작
- **브랜드 분석**: 기존 블로그/Instagram/YouTube 콘텐츠 분석 및 스타일 추출
- **멀티 플랫폼 연동**: YouTube, Facebook, Instagram, X(Twitter) OAuth 연동
- **AI 채팅 어시스턴트**: 대화형 콘텐츠 생성 인터페이스

---

## 기술 스택

### Frontend

| 기술 | 버전 | 용도 |
| :--- | :--- | :--- |
| React | 19.2.0 | UI 프레임워크 |
| React Router DOM | 7.9.5 | 클라이언트 라우팅 |
| Axios | 1.13.2 | API 통신 |
| React Markdown | 10.1.0 | 마크다운 렌더링 |
| CSS3 | - | 스타일링 |

### Backend

| 기술 | 버전 | 용도 |
| :--- | :--- | :--- |
| FastAPI | 0.115.0 | RESTful API 서버 |
| Uvicorn | 0.32.0 | ASGI 서버 |
| SQLAlchemy | 2.0.36 | ORM |
| SQLite / PostgreSQL | - | 데이터베이스 |
| Python-JOSE | 3.3.0 | JWT 인증 |
| Authlib | 1.3.2 | OAuth 2.0 |
| Pydantic | 2.10.0 | 데이터 검증 |
| HTTPX | 0.28.1 | 비동기 HTTP 클라이언트 |

### AI / ML

| 기술 | 용도 |
| :--- | :--- |
| Google Gemini API | 이미지 생성 (Gemini 2.0 Flash), 프롬프트 최적화 |
| Anthropic Claude API | 콘텐츠 생성, 프롬프트 최적화, 브랜드 분석 |
| Hugging Face | Stable Diffusion 2.1 이미지 생성 |
| Replicate API | AI 동영상 생성 (Stable Video Diffusion, LTX-Video) |

### OAuth 2.0 연동

| 플랫폼 | 기능 |
| :--- | :--- |
| Google | 소셜 로그인 |
| Kakao | 소셜 로그인 |
| Facebook | 소셜 로그인, 페이지 연동, 콘텐츠 발행 |
| Instagram | 비즈니스 계정 연동, 콘텐츠 발행 |
| YouTube | 채널 연동, 동영상 분석 |
| X (Twitter) | 계정 연동, 콘텐츠 발행 |

---

## 프로젝트 구조

```
contents_creator/
├── backend/                        # FastAPI 백엔드
│   └── app/
│       ├── main.py                 # FastAPI 앱 설정
│       ├── models.py               # SQLAlchemy 모델 (16개)
│       ├── schemas.py              # Pydantic 스키마
│       ├── database.py             # DB 연결 설정
│       ├── auth.py                 # JWT 인증
│       ├── oauth.py                # OAuth 설정
│       ├── routers/                # API 라우터 (18개)
│       │   ├── auth.py             # 인증 API
│       │   ├── oauth.py            # OAuth 콜백
│       │   ├── user.py             # 사용자 프로필
│       │   ├── chat.py             # AI 채팅
│       │   ├── ai_content.py       # AI 콘텐츠 생성
│       │   ├── image.py            # 이미지 생성
│       │   ├── video.py            # 동영상 관리
│       │   ├── ai_video_generation.py  # AI 동영상 생성
│       │   ├── brand_analysis.py   # 브랜드 분석
│       │   ├── blog.py             # 블로그 분석
│       │   ├── youtube.py          # YouTube 연동
│       │   ├── facebook.py         # Facebook 연동
│       │   ├── instagram.py        # Instagram 연동
│       │   ├── x.py                # X(Twitter) 연동
│       │   ├── sns.py              # SNS 통합 발행
│       │   └── onboarding.py       # 온보딩
│       ├── services/               # 비즈니스 로직
│       │   ├── brand_analyzer.py   # 브랜드 분석 서비스
│       │   ├── naver_blog.py       # 네이버 블로그 스크래핑
│       │   ├── instagram.py        # Instagram API
│       │   ├── facebook.py         # Facebook API
│       │   └── youtube.py          # YouTube API
│       └── system_prompts/         # AI 시스템 프롬프트
│
├── src/                            # React 프론트엔드
│   ├── pages/
│   │   ├── Home.js                 # 메인 AI 채팅 인터페이스
│   │   ├── auth/
│   │   │   ├── Login.js            # 로그인
│   │   │   └── OAuthCallback.js    # OAuth 콜백
│   │   ├── onboarding/
│   │   │   └── DynamicOnboarding.js  # 온보딩 (브랜드 분석)
│   │   ├── content/
│   │   │   ├── AIContentGenerator.js   # AI 콘텐츠 생성
│   │   │   ├── AIVideoGenerator.js     # AI 동영상 생성
│   │   │   ├── ImageGenerator.js       # 이미지 생성
│   │   │   ├── ImageStudio.js          # 이미지 스튜디오
│   │   │   ├── CardNews.js             # 카드뉴스
│   │   │   ├── VideoCreator.js         # 동영상 제작
│   │   │   ├── ContentList.js          # 콘텐츠 목록
│   │   │   └── Templates.js            # 템플릿
│   │   ├── connection_SNS/
│   │   │   ├── youtube/YouTube.js      # YouTube 연동
│   │   │   ├── facebook/Facebook.js    # Facebook 연동
│   │   │   ├── instagram/Instagram.js  # Instagram 연동
│   │   │   └── x/X.js                  # X(Twitter) 연동
│   │   ├── dashboard/Dashboard.js      # 대시보드
│   │   ├── profile/MyPage.js           # 마이페이지
│   │   ├── settings/Settings.js        # 설정
│   │   └── legal/                      # 법적 고지
│   ├── components/
│   │   ├── Layout.js               # 레이아웃
│   │   ├── Sidebar.js              # 사이드바
│   │   ├── ProtectedRoute.js       # 인증 라우트
│   │   ├── AgenticContentForm.js   # AI 콘텐츠 폼
│   │   ├── AgenticContentResult.js # AI 콘텐츠 결과
│   │   └── SNSPublishModal.js      # SNS 발행 모달
│   ├── contexts/
│   │   ├── AuthContext.js          # 인증 상태
│   │   └── ContentContext.js       # 콘텐츠 상태
│   └── services/
│       ├── api.js                  # API 클라이언트
│       ├── agenticService.js       # AI 콘텐츠 서비스
│       └── geminiService.js        # Gemini API
│
├── .env.example                    # 환경 변수 템플릿
├── package.json                    # npm 설정
└── README.md                       # 프로젝트 문서
```

---

## 데이터베이스 모델

### 사용자 관리
- **User**: OAuth 정보, 비즈니스 정보, 타겟 고객 정보
- **UserPreference**: 텍스트/이미지/동영상 스타일 선호도

### 콘텐츠
- **Content**: 블로그, 이미지, 동영상 통합 콘텐츠
- **AIGeneratedContent**: AI 생성 블로그/SNS 콘텐츠
- **Video**: 동영상 메타데이터
- **VideoGenerationJob**: 동영상 생성 작업 추적

### 브랜드 분석
- **BrandAnalysis**: 플랫폼별 브랜드 스타일 분석 결과

### SNS 연동
- **YouTubeConnection / YouTubeVideo / YouTubeAnalytics**
- **FacebookConnection / FacebookPost**
- **InstagramConnection / InstagramPost**
- **XConnection / XPost**
- **SNSPublishedContent**: 발행된 콘텐츠 추적

### 채팅
- **ChatSession / ChatMessage**: AI 채팅 세션 및 메시지

---

## 시작하기

### 요구사항

- Node.js 16.x 이상
- Python 3.8 이상
- npm 8.x 이상

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
   # 인증
   SECRET_KEY=your-secret-key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # 데이터베이스
   DATABASE_URL=sqlite:///./app.db
   # DATABASE_URL=postgresql://user:password@localhost:5432/contents_creator

   # OAuth 2.0
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   KAKAO_CLIENT_ID=your-kakao-rest-api-key
   FACEBOOK_CLIENT_ID=your-facebook-app-id
   FACEBOOK_CLIENT_SECRET=your-facebook-app-secret
   X_CLIENT_ID=your-x-client-id
   X_CLIENT_SECRET=your-x-client-secret

   # AI API
   GOOGLE_API_KEY=your-google-api-key
   ANTHROPIC_API_KEY=your-anthropic-api-key
   HUGGINGFACE_API_KEY=your-huggingface-api-key
   REPLICATE_API_TOKEN=your-replicate-api-token

   # Frontend
   REACT_APP_GEMINI_API_KEY=your-gemini-api-key
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

## PostgreSQL 설정 (프로덕션)

### 설치

**macOS**:
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 데이터베이스 생성

```bash
psql -U postgres
CREATE DATABASE contents_creator;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE contents_creator TO your_username;
\q
```

### 환경 변수 설정

```env
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/contents_creator
```

---

## API 엔드포인트

### 인증
- `POST /api/auth/logout` - 로그아웃
- `GET /api/auth/me` - 현재 사용자 정보
- `GET /api/oauth/{provider}/login` - OAuth 로그인 시작
- `GET /api/oauth/{provider}/callback` - OAuth 콜백

### 사용자
- `GET /api/user/profile` - 프로필 조회
- `PUT /api/user/profile` - 프로필 수정

### AI 콘텐츠
- `POST /api/ai-content/save` - AI 생성 콘텐츠 저장
- `GET /api/ai-content/history` - 생성 이력 조회
- `POST /api/chat/` - AI 채팅

### 이미지 생성
- `POST /api/image/generate` - 이미지 생성
- `POST /api/image/optimize-prompt` - 프롬프트 최적화

### 동영상 생성
- `POST /api/ai-video/generate` - 동영상 생성 시작
- `GET /api/ai-video/status/{job_id}` - 생성 상태 조회
- `GET /api/video/history` - 동영상 이력

### 브랜드 분석
- `POST /api/brand-analysis/analyze` - 브랜드 분석 실행
- `GET /api/brand-analysis/{user_id}` - 분석 결과 조회

### SNS 연동
- `GET /api/youtube/connect` - YouTube 연동
- `GET /api/facebook/connect` - Facebook 연동
- `GET /api/instagram/connect` - Instagram 연동
- `GET /api/x/connect` - X(Twitter) 연동
- `POST /api/sns/publish` - 통합 SNS 발행

### 온보딩
- `POST /api/onboarding/` - 온보딩 정보 저장

---

## 주요 기능 상세

### 1. AI 채팅 어시스턴트 (Home)
- 대화형 인터페이스로 콘텐츠 아이디어 생성
- 사용자 비즈니스 컨텍스트 반영
- 채팅 세션 저장 및 불러오기

### 2. AI 콘텐츠 생성
- Agentic 워크플로우: 기획 → 생성 → 평가 → 최적화
- 블로그 포스트, SNS 캡션 자동 생성
- 브랜드 스타일 반영

### 3. AI 이미지 생성
- Gemini 2.0 Flash / Stable Diffusion 선택
- 브랜드 분석 기반 프롬프트 자동 강화
- 다양한 스타일 옵션

### 4. AI 동영상 생성
- 텍스트 → 동영상 (LTX-Video)
- 이미지 → 동영상 (Stable Video Diffusion)
- 생성 진행 상태 실시간 추적

### 5. 브랜드 분석
- 네이버 블로그 포스트 분석
- Instagram 피드 분석
- YouTube 채널 분석
- 글쓰기 스타일, 컬러 팔레트, 해시태그 패턴 추출

### 6. 멀티 플랫폼 발행
- Instagram + Facebook 동시 발행
- X(Twitter) 포스팅
- 발행 이력 추적

### 7. 온보딩
- 자동 모드: 블로그 URL로 브랜드 자동 분석
- 수동 모드: 비즈니스 정보 직접 입력
- 타겟 고객 설정

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
