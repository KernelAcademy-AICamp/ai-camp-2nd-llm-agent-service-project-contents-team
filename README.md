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
| **Database** | SQLite | - | 개발용 DB (PostgreSQL로 변경 가능) |
| **Authentication** | Python-JOSE | 3.3.0 | JWT 토큰 생성/검증 |
| **OAuth** | Authlib | 1.3.2 | OAuth 2.0 클라이언트 |
| **Validation** | Pydantic | 2.10.0 | 데이터 검증 및 직렬화 |
| **HTTP Client** | HTTPX | 0.28.1 | 비동기 HTTP 클라이언트 |
| **Session** | itsdangerous | 2.2.0 | 세션 관리 |

### 3.3. AI / ML (Image Generation)
| 구분 | 기술 | 버전 | 용도 |
| :--- | :--- | :--- | :--- |
| **Gemini API** | google-generativeai | 0.8.3 | 이미지 생성 (Gemini 2.0 Flash), 프롬프트 최적화 |
| **Anthropic API** | anthropic | 0.39.0 | 프롬프트 최적화 (Claude) |
| **Hugging Face** | - | - | Stable Diffusion 2.1 (이미지 생성) |
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

   로그인 및 AI 이미지 생성 기능을 사용하려면 API 키를 발급받아야 합니다.

   **상세한 설정 가이드**: `backend/OAUTH_SETUP.md` 참조

   **지원 플랫폼**:
   - ✅ **Google OAuth**: [Google Cloud Console](https://console.cloud.google.com/)에서 OAuth 2.0 클라이언트 ID 생성
   - ✅ **Kakao OAuth**: [Kakao Developers](https://developers.kakao.com/)에서 REST API 키 발급
   - ✅ **Facebook OAuth**: [Facebook Developers](https://developers.facebook.com/)에서 앱 ID 발급
   - ✅ **Google Gemini**: [Google AI Studio](https://makersuite.google.com/app/apikey)에서 API 키 생성
   - ✅ **Anthropic Claude**: [Anthropic Console](https://console.anthropic.com/settings/keys)에서 API 키 생성
   - ✅ **Hugging Face**: [Hugging Face](https://huggingface.co/settings/tokens)에서 토큰 생성

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

---

## 5. 🌳 레포지토리 구조

```
/
├── public/                     # 정적 파일
│   ├── index.html              # HTML 템플릿
│   ├── favicon.ico             # 파비콘
│   ├── logo192.png             # 앱 로고 (192x192)
│   ├── logo512.png             # 앱 로고 (512x512)
│   ├── manifest.json           # PWA 매니페스트
│   └── robots.txt              # SEO 로봇 설정
│
├── src/                        # 프론트엔드 소스
│   ├── components/             # 재사용 가능한 UI 컴포넌트
│   │   ├── Header.js           # 헤더 (네비게이션, 로그아웃)
│   │   ├── Sidebar.js          # 사이드바 메뉴
│   │   ├── Layout.js           # 페이지 레이아웃 래퍼
│   │   ├── BlogPostForm.js     # 블로그 작성 폼
│   │   ├── BlogPostResult.js   # 블로그 결과 표시
│   │   └── ProtectedRoute.js   # 인증 보호 라우트
│   │
│   ├── pages/                  # 페이지 컴포넌트
│   │   ├── Login.js            # 로그인 (OAuth)
│   │   ├── Register.js         # 회원가입
│   │   ├── OAuthCallback.js    # OAuth 콜백 처리
│   │   ├── Dashboard.js        # 대시보드
│   │   ├── ContentCreator.js   # 콘텐츠 생성 (블로그, 이미지)
│   │   ├── CardNews.js         # 카드뉴스 생성
│   │   ├── ContentList.js      # 콘텐츠 관리
│   │   ├── Templates.js        # 템플릿 라이브러리
│   │   ├── Schedule.js         # 스케줄 관리
│   │   ├── Analytics.js        # 성과 분석
│   │   └── Settings.js         # 설정
│   │
│   ├── contexts/               # React Context
│   │   └── AuthContext.js      # 인증 컨텍스트 (로그인 상태 관리)
│   │
│   ├── App.js                  # 메인 앱 컴포넌트
│   ├── App.css                 # 앱 스타일
│   ├── index.js                # 엔트리 포인트
│   ├── index.css               # 글로벌 스타일
│   ├── setupTests.js           # 테스트 설정
│   └── reportWebVitals.js      # 성능 측정
│
├── backend/                    # 백엔드 서버
│   ├── app/                    # FastAPI 애플리케이션
│   │   ├── routers/            # API 라우터
│   │   │   ├── auth.py         # 인증 엔드포인트
│   │   │   ├── oauth.py        # OAuth 엔드포인트
│   │   │   └── image.py        # 이미지 생성 엔드포인트
│   │   │
│   │   ├── main.py             # FastAPI 메인 앱
│   │   ├── models.py           # SQLAlchemy 모델 (User)
│   │   ├── schemas.py          # Pydantic 스키마
│   │   ├── database.py         # DB 연결 설정
│   │   ├── auth.py             # 인증 유틸리티 (JWT)
│   │   └── oauth.py            # OAuth 클라이언트 설정
│   │
│   ├── requirements.txt        # Python 의존성
│   ├── setup.sh                # 백엔드 초기 설정 스크립트
│   ├── migrate_db.sh           # DB 마이그레이션 스크립트
│   ├── app.db                  # SQLite 데이터베이스
│   ├── OAUTH_SETUP.md          # OAuth 설정 가이드
│   └── README.md               # 백엔드 문서
│
├── .env.example                # 환경 변수 템플릿
├── .gitignore                  # Git 무시 파일
├── package.json                # npm 의존성 및 스크립트
├── package-lock.json           # npm 의존성 잠금
└── README.md                   # 프로젝트 문서 (이 파일)
```

### 주요 디렉토리 설명

| 디렉토리 | 설명 |
| :--- | :--- |
| **`/src/components`** | 재사용 가능한 React 컴포넌트 (Header, Sidebar, Layout 등) |
| **`/src/pages`** | 각 라우트에 대응하는 페이지 컴포넌트 |
| **`/src/contexts`** | React Context API (전역 상태 관리) |
| **`/backend/app`** | FastAPI 백엔드 애플리케이션 |
| **`/backend/app/routers`** | API 엔드포인트 라우터 (인증, OAuth, 이미지 생성) |
| **`/public`** | 정적 파일 (HTML, 이미지, manifest) |

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
- ✅ **통합 이미지 생성 API**: `/api/generate-image` 엔드포인트
- ✅ **Base64 이미지 반환**: 프론트엔드에서 즉시 표시 가능

### 7.2. 추후 구현 예정
- 🔄 **AI 텍스트 생성**: OpenAI/Gemini API 연동 (블로그, SNS 콘텐츠)
- 🔄 **플랫폼 API 연동**: Instagram, Facebook, YouTube 자동 발행
- 🔄 **스케줄링**: 예약 발행 시스템
- 🔄 **분석 대시보드**: 실시간 성과 분석 및 인사이트
- 🔄 **이미지 편집**: 이미지 필터 및 크롭 기능

---

## 8. 🗓️ 프로젝트 로드맵 (7-Week Plan)

| 주차 | 핵심 목표 | 주요 산출물 |
| :--- | :--- | :--- |
| **1주차** | **기획 및 프론트엔드 개발** | UI/UX 디자인, React SPA 구현 ✅ |
| **2주차** | **백엔드 설계 및 API 개발** | FastAPI 서버, 데이터베이스 스키마 |
| **3주차** | **AI 기능 통합** | LLM Agent, 콘텐츠 생성 로직 |
| **4주차** | **플랫폼 API 연동** | 소셜 미디어 자동 발행 기능 |
| **5주차** | **스케줄링 및 자동화** | 예약 발행, 배치 처리 |
| **6주차** | **분석 및 최적화** | 성과 분석, 성능 개선 |
| **7주차** | **테스트 및 배포** | **동작하는 웹 서비스 (최종 산출물)** |

---

## 9. 📄 산출물 링크 (Documentation)

> 팀의 Notion, Fimga 등 관련 링크를 업데이트하세요.

-   **[➡️ 서비스 기획서 및 요구사항 명세서]([링크])`**
-   **[➡️ 시스템 아키텍처 다이어그램]([링크])`**
-   **[➡️ 데이터베이스 ERD]([링크])`**
-   **[➡️ 팀 WBS / Scrum 보드]([링크])`**

---

## 10. 🏁 최종 결과물 (Final Deliverables)

1. **웹 UI 기반 서비스**: React SPA ✅
2. **OAuth 2.0 소셜 로그인**: Google, Kakao, Facebook 통합 ✅
3. **AI 이미지 생성**: Gemini 2.0 Flash, Stable Diffusion 2.1 ✅
4. **프롬프트 최적화**: Gemini/Claude 기반 자동 최적화 ✅
5. **통합 백엔드 API**: FastAPI 기반 RESTful API ✅
6. **AI 콘텐츠 생성 모듈**: LLM Agent 기반 텍스트 생성 (예정)
7. **멀티 플랫폼 연동**: 소셜 미디어 자동 발행 (예정)
8. **스케줄링 시스템**: 예약 발행 자동화 (예정)
9. **분석 대시보드**: 성과 추적 및 인사이트 (예정)
10. **최종 발표 자료 및 데모 영상**

---

## 11. 📜 License

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).
