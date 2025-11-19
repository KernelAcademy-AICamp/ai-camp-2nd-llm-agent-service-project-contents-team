# 콘텐츠 팀 🤖 LLM Agent 기반 콘텐츠 크리에이터 서비스 개발

_본 프로젝트는 1인 기업 및 소상공인을 위한 AI 기반 콘텐츠 제작 및 자동화 서비스입니다._

## 1. 👥 팀원 및 역할

| 이름 | GitHub |
| :--- |  :--- |
| 기유진 |  [GitHub ID] |
| 김종주 |  jonjour99 |
| 오화영 |  [GitHub ID] |

---

## 2. 🎯 프로젝트 개요

### 2.1. 프로젝트 주제
- **콘텐츠 크리에이터: 1인 기업 및 소상공인을 위한 AI 기반 콘텐츠 제작 및 자동 배포 플랫폼**

### 2.2. 제작 배경 (해결하고자 하는 문제)
- 1인 기업과 소상공인은 제한된 시간과 리소스로 인해 효과적인 마케팅 콘텐츠를 지속적으로 생산하기 어렵습니다.
- 다양한 플랫폼(Instagram, Facebook, YouTube, 블로그 등)에 맞는 콘텐츠를 각각 제작하고 관리하는 것은 많은 시간과 노력이 필요합니다.

### 2.3. 핵심 목표 (제공하는 가치)
1. **AI 기반 콘텐츠 생성**: LLM Agent를 활용하여 비즈니스에 맞는 마케팅 콘텐츠를 자동으로 생성
2. **멀티 플랫폼 관리**: 소셜 미디어, 블로그, 이메일 등 다양한 플랫폼의 콘텐츠를 한 곳에서 관리
3. **자동 예약 발행**: 콘텐츠를 미리 작성하고 원하는 시간에 자동으로 발행
4. **템플릿 시스템**: 검증된 마케팅 템플릿을 활용하여 빠르게 콘텐츠 제작
5. **성과 분석**: 콘텐츠 성과를 분석하고 인사이트 제공

---

## 3. 🛠️ 기술 스택 (Tech Stack)

### 3.1. Frontend
| 구분 | 기술 | 버전 | 용도 |
| :--- | :--- | :--- | :--- |
| **Core** | React | ^19.2.0 | UI 프레임워크 |
| **Routing** | React Router DOM | ^7.9.5 | 클라이언트 라우팅 |
| **HTTP Client** | Axios | ^1.13.2 | API 통신 |
| **Markdown** | React Markdown | ^10.1.0 | 마크다운 렌더링 |
| **Styling** | CSS3 | - | 스타일링 |
| **Build Tool** | React Scripts (CRA) | 5.0.1 | 빌드 및 개발 서버 |

### 3.2. Backend
| 구분 | 기술 | 버전 | 용도 |
| :--- | :--- | :--- | :--- |
| **Framework** | FastAPI | 0.115.0 | RESTful API 서버 |
| **Server** | Uvicorn | 0.32.0 | ASGI 서버 |
| **ORM** | SQLAlchemy | 2.0.36 | 데이터베이스 ORM |
| **Database** | SQLite / PostgreSQL | - | SQLite (개발), PostgreSQL (프로덕션) |
| **DB Driver** | psycopg2-binary | 2.9.9 | PostgreSQL 드라이버 |
| **Authentication** | Python-JOSE | 3.3.0 | JWT 토큰 생성/검증 |
| **OAuth** | Authlib | 1.3.2 | OAuth 2.0 클라이언트 |
| **Validation** | Pydantic | 2.10.0 | 데이터 검증 및 직렬화 |
| **HTTP Client** | HTTPX | 0.28.1 | 비동기 HTTP 클라이언트 |
| **Session** | itsdangerous | 2.2.0 | 세션 관리 |

### 3.3. AI / ML
| 구분 | 기술 | 버전 | 용도 |
| :--- | :--- | :--- | :--- |
| **Gemini API** | google-generativeai | 0.8.3 | 이미지 생성 (Gemini 2.0 Flash), 프롬프트 최적화 |
| **Anthropic API** | anthropic | 0.39.0 | 프롬프트 최적화 (Claude) |
| **Hugging Face** | - | - | Stable Diffusion 2.1 (이미지 생성) |
| **Replicate API** | replicate | 0.34.1 | AI 동영상 생성 (Stable Video Diffusion, LTX-Video) |
| **Image Processing** | Pillow | 11.0.0 | 이미지 처리 |

### 3.4. OAuth 2.0 Social Login
| 플랫폼 | 상태 | 기능 |
| :--- | :--- | :--- |
| **Google** | ✅ 구현 완료 | 소셜 로그인, 프로필 정보 연동 |
| **Kakao** | ✅ 구현 완료 | 소셜 로그인, 프로필 정보 연동 |
| **Facebook** | ✅ 구현 완료 | 소셜 로그인, 프로필 정보 연동 |

### 3.5. Development & Deployment
| 구분 | 기술 | 용도 |
| :--- | :--- | :--- |
| **Version Control** | Git, GitHub | 소스 코드 관리 |
| **Package Manager** | npm, pip | 의존성 관리 |
| **Process Manager** | concurrently | 다중 프로세스 실행 |
| **Environment** | python-dotenv | 환경 변수 관리 |
| **API Documentation** | Swagger UI (FastAPI 내장) | 자동 API 문서화 |

---

## 4. 🚀 시작하기 (Getting Started)

### 4.1. 개발 환경
- **Node.js 버전**: 16.x 이상
- **npm 버전**: 8.x 이상
- **Python 버전**: 3.8 이상
- **주요 라이브러리**: `package.json`, `backend/requirements.txt` 참조

### 4.2. 설치 및 실행

1. **레포지토리 복제**
   ```bash
   git clone https://github.com/KernelAcademy-AICamp/ai-camp-2nd-llm-agent-service-project-contents-team.git
   cd ai-camp-2nd-llm-agent-service-project-contents-team
   ```

2. **프론트엔드 의존성 설치**
   ```bash
   npm install
   ```

3. **백엔드 설정 (최초 1회)**
   ```bash
   npm run setup:backend
   ```

4. **개발 서버 실행 (프론트엔드 + 백엔드 동시 실행)**
   ```bash
   npm start
   ```
   - 프론트엔드: [http://localhost:3000](http://localhost:3000)
   - 백엔드 API: [http://localhost:8000](http://localhost:8000)
   - API 문서: [http://localhost:8000/docs](http://localhost:8000/docs)

5. **개별 실행 (선택사항)**
   ```bash
   # 프론트엔드만 실행
   npm run start:frontend

   # 백엔드만 실행
   npm run start:backend
   ```

5. **OAuth2.0 소셜 로그인 및 AI API 설정 (필수)**

   로그인 및 AI 콘텐츠 생성 기능을 사용하려면 API 키를 발급받아야 합니다.

   **상세한 설정 가이드**: `backend/OAUTH_SETUP.md` 참조

   **지원 플랫폼**:
   - ✅ **Google OAuth**: [Google Cloud Console](https://console.cloud.google.com/)에서 OAuth 2.0 클라이언트 ID 생성
   - ✅ **Kakao OAuth**: [Kakao Developers](https://developers.kakao.com/)에서 REST API 키 발급
   - ✅ **Facebook OAuth**: [Facebook Developers](https://developers.facebook.com/)에서 앱 ID 발급
   - ✅ **Google Gemini**: [Google AI Studio](https://makersuite.google.com/app/apikey)에서 API 키 생성
   - ✅ **Anthropic Claude**: [Anthropic Console](https://console.anthropic.com/settings/keys)에서 API 키 생성
   - ✅ **Hugging Face**: [Hugging Face](https://huggingface.co/settings/tokens)에서 토큰 생성
   - ✅ **Replicate API**: [Replicate](https://replicate.com/account/api-tokens)에서 API 토큰 생성 (AI 동영상 생성)

   `.env.example` 파일을 복사하여 `.env` 파일을 생성하고 발급받은 키를 입력:
   ```bash
   cp .env.example .env
   ```

   `.env` 파일 예시:
   ```env
   # OAuth 2.0 설정
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   KAKAO_CLIENT_ID=your-kakao-rest-api-key
   FACEBOOK_CLIENT_ID=your-facebook-app-id
   FACEBOOK_CLIENT_SECRET=your-facebook-app-secret

   # AI API 키 설정
   GOOGLE_API_KEY=your_google_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   HUGGINGFACE_API_KEY=your_huggingface_api_key_here
   REPLICATE_API_TOKEN=your_replicate_api_token_here
   ```

6. **데이터베이스 초기화 (최초 1회)**

   User 모델이 OAuth를 지원하도록 변경되었으므로 DB를 재생성해야 합니다:
   ```bash
   cd backend
   bash migrate_db.sh
   ```

7. **프로덕션 빌드**
   ```bash
   npm run build
   ```

### 4.3. PostgreSQL 설정 (프로덕션 환경)

개발 환경에서는 SQLite를 사용하지만, 프로덕션 환경에서는 PostgreSQL 사용을 권장합니다.

#### PostgreSQL 설치 및 설정

1. **PostgreSQL 설치**

   **macOS (Homebrew)**:
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

   **Windows**:
   - [PostgreSQL 공식 사이트](https://www.postgresql.org/download/windows/)에서 설치

2. **데이터베이스 생성**
   ```bash
   # PostgreSQL 접속
   psql -U postgres

   # 데이터베이스 생성
   CREATE DATABASE contents_creator;

   # 사용자 생성 (선택사항)
   CREATE USER your_username WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE contents_creator TO your_username;

   # 종료
   \q
   ```

3. **환경 변수 설정**

   `.env` 파일에서 `DATABASE_URL`을 PostgreSQL로 변경:
   ```env
   # 개발 환경 (SQLite)
   ENV=development
   # DATABASE_URL=sqlite:///./app.db

   # 프로덕션 환경 (PostgreSQL)
   ENV=production
   DATABASE_URL=postgresql://your_username:your_password@localhost:5432/contents_creator
   ```

4. **PostgreSQL 드라이버 설치**
   ```bash
   cd backend
   pip install psycopg2-binary==2.9.9
   ```

5. **테이블 생성**

   백엔드 서버를 시작하면 자동으로 테이블이 생성됩니다:
   ```bash
   npm run start:backend
   ```

   또는 Python으로 직접 생성:
   ```bash
   cd backend
   python3 -c "from app.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine)"
   ```

6. **연결 확인**

   API 문서에서 헬스 체크:
   ```bash
   curl http://localhost:8000/health
   ```

#### 데이터베이스 전환 가이드

SQLite에서 PostgreSQL로 데이터를 마이그레이션하려면:

1. **데이터 백업** (SQLite):
   ```bash
   cd backend
   cp app.db app.db.backup
   ```

2. **PostgreSQL 설정** (위 단계 참조)

3. **마이그레이션 스크립트 실행**:
   ```bash
   bash migrate_db.sh
   ```

---

## 5. 🌳 레포지토리 구조

```
/
├── public/                         # 정적 파일
│   ├── index.html                  # HTML 템플릿
│   ├── favicon.ico                 # 파비콘
│   ├── logo192.png                 # 앱 로고 (192x192)
│   ├── logo512.png                 # 앱 로고 (512x512)
│   ├── manifest.json               # PWA 매니페스트
│   └── robots.txt                  # SEO 로봇 설정
│
├── src/                            # 프론트엔드 소스
│   ├── components/                 # 재사용 가능한 UI 컴포넌트
│   │   ├── Header.js / .css        # 헤더 (네비게이션, 로그아웃)
│   │   ├── Sidebar.js / .css       # 사이드바 메뉴 (대시보드, 콘텐츠 생성, AI 동영상 등)
│   │   ├── Layout.js / .css        # 페이지 레이아웃 래퍼
│   │   ├── BlogPostForm.js / .css  # 블로그 작성 폼
│   │   ├── BlogPostResult.js / .css # 블로그 결과 표시
│   │   └── ProtectedRoute.js       # 인증 보호 라우트
│   │
│   ├── pages/                      # 페이지 컴포넌트
│   │   ├── auth/                   # 인증 관련 페이지
│   │   │   ├── Login.js / .css     # 로그인 (OAuth 소셜 로그인)
│   │   │   ├── Register.js / .css  # 회원가입
│   │   │   └── OAuthCallback.js / .css # OAuth 콜백 처리
│   │   │
│   │   ├── dashboard/              # 대시보드
│   │   │   └── Dashboard.js / .css # 메인 대시보드 (통계, 최근 콘텐츠)
│   │   │
│   │   ├── content/                # 콘텐츠 생성 및 관리
│   │   │   ├── ContentCreator.js / .css # 콘텐츠 생성 (블로그, 이미지)
│   │   │   ├── CardNews.js / .css       # 카드뉴스 생성
│   │   │   ├── VideoCreator.js / .css   # AI 동영상 생성 (🆕)
│   │   │   ├── ContentList.js / .css    # 콘텐츠 관리
│   │   │   └── Templates.js / .css      # 템플릿 라이브러리
│   │   │
│   │   ├── analytics/              # 성과 분석
│   │   │   └── Analytics.js / .css # 성과 분석 대시보드 (플레이스홀더)
│   │   │
│   │   └── settings/               # 설정
│   │       └── Settings.js / .css  # 사용자 설정, 플랫폼 연동
│   │
│   ├── contexts/                   # React Context
│   │   └── AuthContext.js          # 인증 컨텍스트 (로그인 상태, JWT 토큰 관리)
│   │
│   ├── services/                   # API 서비스
│   │   ├── api.js                  # Axios 인스턴스, 인증 API
│   │   └── geminiService.js        # Gemini API 서비스
│   │
│   ├── App.js                      # 메인 앱 컴포넌트 (라우팅)
│   ├── App.css                     # 앱 스타일
│   ├── index.js                    # 엔트리 포인트
│   ├── index.css                   # 글로벌 스타일
│   ├── setupTests.js               # 테스트 설정
│   └── reportWebVitals.js          # 성능 측정
│
├── backend/                        # 백엔드 서버
│   ├── app/                        # FastAPI 애플리케이션
│   │   ├── routers/                # API 라우터
│   │   │   ├── __init__.py         # 라우터 패키지 초기화
│   │   │   ├── auth.py             # 인증 엔드포인트 (JWT 로그인)
│   │   │   ├── oauth.py            # OAuth 엔드포인트 (Google, Kakao, Facebook)
│   │   │   ├── image.py            # 이미지 생성 엔드포인트 (Gemini, SD)
│   │   │   └── video.py            # 동영상 생성 엔드포인트 (Replicate) 🆕
│   │   │
│   │   ├── __init__.py             # 앱 패키지 초기화
│   │   ├── main.py                 # FastAPI 메인 앱 (CORS, 미들웨어, 라우터 등록)
│   │   ├── models.py               # SQLAlchemy 모델 (User, Video)
│   │   ├── schemas.py              # Pydantic 스키마 (요청/응답 검증)
│   │   ├── database.py             # DB 연결 설정 (SQLite/PostgreSQL)
│   │   ├── auth.py                 # 인증 유틸리티 (JWT, 비밀번호 해싱)
│   │   └── oauth.py                # OAuth 클라이언트 설정
│   │
│   ├── requirements.txt            # Python 의존성
│   ├── setup.sh                    # 백엔드 초기 설정 스크립트
│   ├── migrate_db.sh               # DB 마이그레이션 스크립트
│   ├── app.db                      # SQLite 데이터베이스 (개발용)
│   ├── OAUTH_SETUP.md              # OAuth 설정 가이드
│   └── README.md                   # 백엔드 문서
│
├── .env.example                    # 환경 변수 템플릿
├── .env                            # 환경 변수 (Git 무시됨)
├── .gitignore                      # Git 무시 파일
├── package.json                    # npm 의존성 및 스크립트
├── package-lock.json               # npm 의존성 잠금
└── README.md                       # 프로젝트 문서 (이 파일)
```

### 주요 디렉토리 설명

| 디렉토리 | 설명 |
| :--- | :--- |
| **`/public`** | 정적 파일 (HTML, 이미지, manifest) |
| **`/src/components`** | 재사용 가능한 React 컴포넌트 (Header, Sidebar, Layout 등) |
| **`/src/pages`** | 각 라우트에 대응하는 페이지 컴포넌트 (auth, dashboard, content, analytics, settings) |
| **`/src/contexts`** | React Context API (전역 상태 관리 - 인증) |
| **`/src/services`** | API 서비스 레이어 (axios, gemini) |
| **`/backend/app`** | FastAPI 백엔드 애플리케이션 |
| **`/backend/app/routers`** | API 엔드포인트 라우터 (인증, OAuth, 이미지, 동영상) |
| **`/backend/app/models.py`** | 데이터베이스 모델 (User, Video) |

### 삭제된 파일/디렉토리 (정리 완료)
- ❌ `backend/app/routers/instagram.py` - Instagram 연동 기능 제거
- ❌ `backend/app/scheduler.py` - 스케줄러 기능 제거
- ❌ `src/pages/publishing/` - 발행 관련 페이지 제거 (Schedule, PublishHistory, AutoPublisher)
- ❌ Instagram 관련 데이터베이스 모델 (instagram_accounts, posts, scheduled_posts)

---

## 6. 룰 & 가이드라인 (Rules & Guidelines)

### 6.1. 핵심 수행 규칙
1.  **매일 오전 10시 KST** : 팀 스크럼 진행 (어제 한 일, 오늘 할 일, 장애물 공유)
2.  **문서화**: 아키텍처, ERD 등 주요 산출물은 **[Notion 링크]`** 에 문서화하고 팀원과 공유합니다.
3.  **환경 통일**: Python 및 주요 라이브러리 버전을 통일하여 개발 환경 차이로 인한 문제를 방지합니다. (`requirements.txt` 준수)
4.  **보안**: API Key, DB 접속 정보 등 민감 정보는 `.env` 파일을 사용하며, 절대로 Git에 커밋하지 않습니다. (`.gitignore` 확인)

### 6.2. Git 브랜치 전략
본 프로젝트는 **Git Flow**를 기반으로 한 브랜치 전략을 따릅니다.

-   **`master`**: 최종 릴리즈(배포) 브랜치. (7주차 발표회)
-   **`develop`**: 개발의 중심이 되는 브랜치.
-   **`feature/[기능명]`**: 신규 기능 개발 브랜치. (예: `feature/pdf-processing`)
    -   개발 완료 후 `develop` 브랜치로 Pull Request(PR)
-   **`hotfix/[버그명]`**: `master` 브랜치의 긴급 버그 수정.


```
[개발 플로우]

feature 브랜치 생성 (git checkout -b feature/my-feature develop)

기능 개발 및 커밋

develop 브랜치로 PR 요청 (코드 리뷰 진행)

develop 브랜치에 Merge
```

---

## 7. 📱 주요 기능

### 7.1. 현재 구현된 기능

#### 프론트엔드
- ✅ **대시보드**: 통계 카드, 최근 콘텐츠, 빠른 작업 버튼
- ✅ **콘텐츠 생성**: 다양한 콘텐츠 유형 및 플랫폼 선택, 에디터, 미리보기
- ✅ **콘텐츠 관리**: 검색, 필터링, 테이블 뷰, 페이지네이션
- ✅ **템플릿**: 템플릿 목록 및 사용
- ✅ **설정**: 플랫폼 연동, 프로필 정보, 알림 설정
- ✅ **반응형 디자인**: 모바일, 태블릿, 데스크톱 지원

#### 백엔드
- ✅ **OAuth2.0 소셜 로그인**: Google, Kakao, Facebook 지원
- ✅ **JWT 기반 인증**: 토큰 기반 사용자 인증 시스템
- ✅ **사용자 프로필**: 정보 조회 및 수정
- ✅ **자동 회원가입**: 소셜 로그인 시 자동 계정 생성
- ✅ **임시 이메일 생성**: 이메일 정보 없는 OAuth 제공자 지원
- ✅ **API 문서**: Swagger UI 자동 생성 (http://localhost:8000/docs)
- ✅ **CORS 설정**: 프론트엔드와 안전한 통신

#### AI 이미지 생성
- ✅ **Gemini 2.0 Flash Image**: Google Gemini API를 활용한 고품질 이미지 생성
- ✅ **Stable Diffusion 2.1**: Hugging Face API를 통한 이미지 생성
- ✅ **프롬프트 최적화**: Gemini/Claude를 활용한 프롬프트 자동 최적화
- ✅ **통합 이미지 생성 API**: `/api/image/generate` 엔드포인트
- ✅ **Base64 이미지 반환**: 프론트엔드에서 즉시 표시 가능

#### AI 동영상 생성 (🆕 7주차)
- ✅ **Stable Video Diffusion**: 이미지 → 동영상 변환 (고품질 모션 생성)
- ✅ **LTX-Video**: 텍스트 → 동영상 생성 (텍스트 프롬프트로 동영상 생성)
- ✅ **Replicate API 연동**: `/api/video/generate` 엔드포인트
- ✅ **동영상 관리**: 생성 이력 조회, 다운로드, 삭제 기능
- ✅ **실시간 상태 추적**: 처리 중, 완료, 실패 상태 표시
- ✅ **VideoCreator UI**: 모델 선택, 프롬프트 입력, 미리보기 기능

### 7.2. 추후 구현 예정
- 🔄 **AI 텍스트 생성**: OpenAI/Gemini API 연동 (블로그, SNS 콘텐츠)
- 🔄 **플랫폼 API 연동**: Instagram, Facebook, YouTube 자동 발행
- 🔄 **스케줄링**: 예약 발행 시스템
- 🔄 **분석 대시보드**: 실시간 성과 분석 및 인사이트
- 🔄 **이미지 편집**: 이미지 필터 및 크롭 기능
- 🔄 **동영상 편집**: 생성된 동영상 트리밍, 합성 기능

---

## 8. 🗓️ 프로젝트 로드맵 및 진행 상황 (7-Week Plan)

| 주차 | 핵심 목표 | 주요 작업 | 상태 |
| :---: | :--- | :--- | :---: |
| **1주차** | **프로젝트 기획** | - 벤치마킹 (Canva Magic Studio)<br>- 핵심 기능 도출<br>- 프로젝트 범위 정의<br>- 산출물: README.md | ✅ |
| **2주차** | **데이터 수집 및 고객 세분화** | - 웹/SNS 데이터 수집<br>- 고객 세분화 (나이, 성별, 관심사)<br>- JSON/CSV 데이터 저장 | ⏸️ |
| **3주차** | **맞춤형 콘텐츠 생성** | - LLM API 연동 (Gemini, Claude) ✅<br>- 텍스트 콘텐츠 생성 (블로그, SNS) ✅<br>- AI 이미지 생성 (Gemini 2.0, SD 2.1) ✅<br>- 카드뉴스 생성 ✅<br>- UI 구현 (React) ✅ | ✅ |
| **4주차** | **캠페인 성과 분석** | - CTR, Engagement 지표 분석<br>- 가상 사용자 반응 데이터 생성<br>- Streamlit 대시보드 시각화 | ⏸️ |
| **5주차** | **기능 통합 및 서비스화** | - OAuth 2.0 소셜 로그인 ✅<br>- React + FastAPI 통합 ✅<br>- MVP 웹 서비스 구조 ✅ | ✅ |
| **6주차** | **품질 개선** | - 프롬프트 최적화 🔄<br>- 옵션별 콘텐츠 생성 다양화<br>- 대시보드 개선 | 🔄 |
| **7주차** | **기능 고도화 및 배포** | - **AI 동영상 제작** ✅<br>  - Replicate API 연동 ✅<br>  - Stable Video Diffusion ✅<br>  - LTX-Video (Text-to-Video) ✅<br>- 클라우드 배포<br>- 최종 발표 준비 | 🔄 |

### 범례
- ✅ **완료**: 구현 완료 및 테스트 완료
- 🔄 **진행 중**: 현재 작업 중
- ⏸️ **보류**: 우선순위에 따라 보류

### 현재 진행 상황 (2025-11-19 기준)
- ✅ **완료된 작업**:
  - 1주차: 프로젝트 기획 및 요구사항 정의
  - 3주차: AI 이미지 생성, 텍스트 콘텐츠 생성, 카드뉴스
  - 5주차: OAuth 2.0 소셜 로그인, React + FastAPI 통합
  - 7주차: **AI 동영상 생성 기능 구현 완료** 🎬

- 🔄 **진행 중**:
  - 7주차: 클라우드 배포 준비
  - 최종 발표 자료 작성

- ⏸️ **보류 (차후 개선)**:
  - 2주차: 데이터 수집 및 고객 세분화
  - 4주차: 캠페인 성과 분석 대시보드
  - 플랫폼 API 연동 (Instagram, Facebook 등)

---

## 9. 📄 산출물 링크 (Documentation)

> 팀의 Notion, Fimga 등 관련 링크를 업데이트하세요.

-   **[➡️ 서비스 기획서 및 요구사항 명세서]([링크])`**
-   **[➡️ 시스템 아키텍처 다이어그램]([링크])`**
-   **[➡️ 데이터베이스 ERD]([링크])`**
-   **[➡️ 팀 WBS / Scrum 보드]([링크])`**

---

## 10. 🏁 최종 결과물 (Final Deliverables)

### 완료된 핵심 기능 ✅
1. **웹 UI 기반 서비스**: React SPA 구현 완료
2. **OAuth 2.0 소셜 로그인**: Google, Kakao, Facebook 3사 통합
3. **AI 이미지 생성**: Gemini 2.0 Flash, Stable Diffusion 2.1
4. **AI 동영상 생성** (🆕): Stable Video Diffusion, LTX-Video (Replicate API)
5. **프롬프트 최적화**: Gemini/Claude 기반 자동 최적화
6. **카드뉴스 생성**: 이미지 + 텍스트 기반 SNS 콘텐츠 제작
7. **통합 백엔드 API**: FastAPI 기반 RESTful API
8. **데이터베이스**: SQLite (개발), PostgreSQL (프로덕션) 지원

### 향후 개선 계획 🔄
9. **AI 텍스트 생성 고도화**: LLM Agent 기반 블로그/SNS 콘텐츠 자동 생성
10. **멀티 플랫폼 연동**: Instagram, Facebook, YouTube API 자동 발행
11. **스케줄링 시스템**: 예약 발행 자동화
12. **분석 대시보드**: 콘텐츠 성과 추적 및 AI 기반 인사이트 제공
13. **클라우드 배포**: Vercel (프론트엔드) + Railway/Render (백엔드)
14. **최종 발표 자료 및 데모 영상**

### 주요 성과 📊
- ✅ **7개 주요 페이지** 구현 (대시보드, 콘텐츠 생성, 카드뉴스, AI 동영상, 콘텐츠 관리, 템플릿, 설정)
- ✅ **3개 AI 모델** 통합 (Gemini 2.0, Stable Diffusion, Replicate Video)
- ✅ **4개 API 라우터** 구현 (인증, OAuth, 이미지, 동영상)
- ✅ **2개 데이터베이스** 지원 (SQLite, PostgreSQL)
- ✅ **완전한 인증 시스템** (JWT + OAuth 2.0)
- ✅ **반응형 UI/UX** (모바일, 태블릿, 데스크톱 대응)

---

## 11. 📜 License

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).
