# 콘텐츠 팀 🤖 LLM Agent 기반 콘텐츠 크리에이터 서비스 개발

_본 프로젝트는 1인 기업 및 소상공인을 위한 AI 기반 콘텐츠 제작 및 자동화 서비스입니다._

## 1. 👥 팀원 및 역할

| 이름 | GitHub |
| :--- |  :--- |
| [이름] |  [GitHub ID] |
| [이름] |  [GitHub ID] |
| [이름] |  [GitHub ID] |
| [이름] |  [GitHub ID] |

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

본 프로젝트는 다음 기술 스택을 기반으로 합니다. (팀별 상황에 맞게 수정 가능)

| 구분 | 기술 |
| :--- | :--- |
| **Frontend** | React.js, React Router, CSS3 |
| **Backend** | FastAPI, Python, SQLAlchemy, JWT Authentication |
| **Database** | SQLite (PostgreSQL로 변경 가능) |
| **AI / ML** | (추후 구현) OpenAI API, Gemini API, LangChain |
| **External APIs** | (추후 구현) Instagram API, Facebook API, YouTube API |
| **Infra / Tools** | Git, npm, Node.js, Python, uvicorn |

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

5. **OAuth2.0 소셜 로그인 설정 (필수)**

   로그인 기능을 사용하려면 OAuth 앱을 등록해야 합니다.

   **상세한 설정 가이드**: `backend/OAUTH_SETUP.md` 참조

   **지원 플랫폼**:
   - ✅ **Google**: [Google Cloud Console](https://console.cloud.google.com/)에서 OAuth 2.0 클라이언트 ID 생성
   - ✅ **Kakao**: [Kakao Developers](https://developers.kakao.com/)에서 REST API 키 발급
   - ✅ **Facebook**: [Facebook Developers](https://developers.facebook.com/)에서 앱 ID 발급

   발급받은 클라이언트 ID와 시크릿을 `backend/.env` 파일에 추가:
   ```env
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/oauth/google/callback

   KAKAO_CLIENT_ID=your-kakao-rest-api-key
   KAKAO_REDIRECT_URI=http://localhost:8000/api/oauth/kakao/callback

   FACEBOOK_CLIENT_ID=your-facebook-app-id
   FACEBOOK_CLIENT_SECRET=your-facebook-app-secret
   FACEBOOK_REDIRECT_URI=http://localhost:8000/api/oauth/facebook/callback
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
├── public/             # 정적 파일 (index.html, favicon 등)
├── src/
│   ├── components/     # 재사용 가능한 UI 컴포넌트
│   │   ├── Header.js   # 헤더 컴포넌트
│   │   ├── Sidebar.js  # 사이드바 네비게이션
│   │   └── Layout.js   # 레이아웃 래퍼
│   ├── pages/          # 페이지 컴포넌트
│   │   ├── Dashboard.js        # 대시보드
│   │   ├── ContentCreator.js   # 콘텐츠 생성
│   │   ├── ContentList.js      # 콘텐츠 관리
│   │   ├── Templates.js        # 템플릿
│   │   ├── Schedule.js         # 스케줄 관리
│   │   ├── Analytics.js        # 분석
│   │   └── Settings.js         # 설정
│   ├── App.js          # 메인 앱 컴포넌트
│   └── index.js        # 엔트리 포인트
├── package.json        # 프로젝트 의존성
└── README.md           # 프로젝트 문서
```

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

### 7.2. 추후 구현 예정
- 🔄 **AI 콘텐츠 생성**: OpenAI/Gemini API 연동
- 🔄 **플랫폼 API 연동**: Instagram, Facebook, YouTube 자동 발행
- 🔄 **스케줄링**: 예약 발행 시스템
- 🔄 **분석 대시보드**: 실시간 성과 분석 및 인사이트
- 🔄 **이미지 편집**: 이미지 업로드 및 편집 기능

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
2. **AI 콘텐츠 생성 모듈**: LLM Agent 기반 자동 생성 (예정)
3. **멀티 플랫폼 연동**: 소셜 미디어 API 통합 (예정)
4. **스케줄링 시스템**: 예약 발행 자동화 (예정)
5. **분석 대시보드**: 성과 추적 및 인사이트 (예정)
6. **최종 발표 자료 및 데모 영상**

---

## 11. 📜 License

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).
