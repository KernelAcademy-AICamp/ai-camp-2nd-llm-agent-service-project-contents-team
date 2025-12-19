# Contents Creator Backend API

FastAPI 기반 AI 콘텐츠 제작 및 멀티 플랫폼 관리 백엔드 서비스입니다.

## 주요 기능

### AI 콘텐츠 생성
- **AI 텍스트 생성**: Claude, Gemini API를 활용한 블로그/SNS 콘텐츠 자동 생성
- **AI 이미지 생성**: Gemini 2.0 Flash, Stable Diffusion 기반 이미지 생성
- **AI 동영상 생성**: Replicate API (LTX-Video, Stable Video Diffusion) 기반 동영상 제작
- **카드뉴스 생성**: 자동 레이아웃 및 디자인 적용 카드뉴스 제작
- **AI 채팅 어시스턴트**: 대화형 콘텐츠 생성 인터페이스

### 브랜드 분석 (Multi-Agent Pipeline)
- 네이버 블로그 분석: 글쓰기 스타일, 구조, 톤 분석
- Instagram 분석: 이미지 스타일, 색상 팔레트, 해시태그 패턴
- YouTube 분석: 콘텐츠 스타일, 제목 패턴, 썸네일 특성

### 멀티 플랫폼 연동
- YouTube, Facebook, Instagram, X(Twitter), Threads, TikTok, WordPress OAuth 연동
- 통합 SNS 발행 및 발행 이력 추적

### 인증 및 사용자 관리
- OAuth 2.0 소셜 로그인 (Google, Kakao, Facebook, Apple)
- JWT 기반 토큰 인증
- 크레딧 시스템

---

## 기술 스택

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

### AI / ML API
| 기술 | 용도 |
| :--- | :--- |
| Google Gemini API | 이미지 생성, 텍스트 생성, 프롬프트 최적화 |
| Anthropic Claude API | 콘텐츠 생성, 브랜드 분석, 품질 검증 |
| Google Vertex AI | Google Cloud 기반 AI 서비스 |
| Hugging Face | Stable Diffusion 2.1 이미지 생성 |
| Replicate API | AI 동영상 생성 (LTX-Video, Stable Video Diffusion) |

---

## 프로젝트 구조

```
backend/
├── app/
│   ├── main.py                    # FastAPI 앱 설정 및 라우터 등록
│   ├── models.py                  # SQLAlchemy 모델 (40개)
│   ├── schemas.py                 # Pydantic 스키마
│   ├── database.py                # DB 연결 설정
│   ├── auth.py                    # JWT 인증
│   ├── oauth.py                   # OAuth 설정
│   ├── agents.py                  # Agentic AI 워크플로우
│   ├── routers/                   # API 라우터 (22개)
│   │   ├── auth.py                # 인증 API
│   │   ├── oauth.py               # OAuth 콜백
│   │   ├── user.py                # 사용자 프로필
│   │   ├── chat.py                # AI 채팅
│   │   ├── ai_content.py          # AI 콘텐츠 생성
│   │   ├── image.py               # 이미지 생성
│   │   ├── ai_video_generation.py # AI 동영상 생성
│   │   ├── brand_analysis.py      # 브랜드 분석
│   │   ├── cardnews.py            # 카드뉴스 생성
│   │   ├── sns_publish.py         # 멀티 플랫폼 발행
│   │   ├── onboarding.py          # 온보딩
│   │   ├── dashboard.py           # 대시보드
│   │   ├── credits.py             # 크레딧 시스템
│   │   ├── templates.py           # 템플릿 관리
│   │   ├── published_content.py   # 발행 콘텐츠 추적
│   │   ├── generated_videos.py    # 생성 동영상 관리
│   │   ├── ai_recommendations.py  # AI 추천
│   │   └── sns/                   # SNS 플랫폼별 라우터
│   │       ├── youtube.py         # YouTube 연동
│   │       ├── facebook.py        # Facebook 연동
│   │       ├── instagram.py       # Instagram 연동
│   │       ├── x.py               # X(Twitter) 연동
│   │       ├── threads.py         # Threads 연동
│   │       ├── tiktok.py          # TikTok 연동
│   │       ├── wordpress.py       # WordPress 연동
│   │       └── blog.py            # 네이버 블로그 분석
│   ├── services/                  # 비즈니스 로직 서비스
│   │   ├── ai_video_service.py    # AI 동영상 생성 서비스
│   │   ├── brand_analyzer_service.py  # 브랜드 분석 로직
│   │   ├── instagram_service.py   # Instagram API
│   │   ├── facebook_service.py    # Facebook API
│   │   ├── youtube_service.py     # YouTube API
│   │   ├── x_service.py           # X API
│   │   ├── threads_service.py     # Threads API
│   │   ├── naver_blog_service.py  # 네이버 블로그 스크래핑
│   │   └── supabase_storage.py    # Supabase 스토리지
│   ├── brand_agents/              # 브랜드 분석 Multi-Agent Pipeline
│   │   ├── pipeline.py            # 분석 파이프라인 오케스트레이션
│   │   ├── collectors.py          # 데이터 수집 에이전트
│   │   ├── analyzers.py           # 분석 에이전트
│   │   ├── synthesizer.py         # 결과 통합 에이전트
│   │   └── normalizer.py          # 데이터 정규화
│   ├── utils/                     # 유틸리티
│   │   ├── cardnews_renderer.py   # 카드뉴스 렌더링
│   │   └── vertex_ai_client.py    # Vertex AI 클라이언트
│   ├── prompts/                   # AI 프롬프트
│   └── system_prompts/            # 시스템 프롬프트
├── fonts/                         # 카드뉴스용 폰트
├── uploads/                       # 업로드된 파일 저장소
├── logs/                          # 애플리케이션 로그
├── requirements.txt               # Python 의존성
└── README.md
```

---

## 설치 및 실행

### 1. Python 가상환경 생성

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

프로젝트 루트의 `.env` 파일에서 백엔드 설정:

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
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/oauth/google/callback

KAKAO_CLIENT_ID=your-kakao-rest-api-key
KAKAO_REDIRECT_URI=http://localhost:8000/api/oauth/kakao/callback

FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret
FACEBOOK_REDIRECT_URI=http://localhost:8000/api/oauth/facebook/callback

X_CLIENT_ID=your-x-client-id
X_CLIENT_SECRET=your-x-client-secret

# ===== AI API Keys =====
GOOGLE_API_KEY=your-google-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
HUGGINGFACE_API_KEY=your-huggingface-api-key
REPLICATE_API_TOKEN=your-replicate-api-token

# ===== Google Cloud (Optional) =====
GOOGLE_APPLICATION_CREDENTIALS=secrets/google-cloud-key.json
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=asia-northeast1

# ===== Supabase Storage (Optional) =====
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

안전한 시크릿 키 생성:
```bash
openssl rand -hex 32
```

### 4. 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

서버가 `http://localhost:8000`에서 실행됩니다.

---

## API 문서

서버 실행 후 자동 생성된 API 문서 확인:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## API 엔드포인트

### 인증
| 메서드 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| GET | `/api/auth/me` | 현재 사용자 정보 |
| PUT | `/api/auth/me` | 사용자 정보 수정 |
| POST | `/api/auth/logout` | 로그아웃 |
| POST | `/api/auth/refresh-token` | 토큰 갱신 |
| GET | `/api/oauth/{provider}/login` | OAuth 로그인 시작 |
| GET | `/api/oauth/{provider}/callback` | OAuth 콜백 |

### AI 콘텐츠
| 메서드 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| POST | `/api/ai-content/save` | AI 생성 콘텐츠 저장 |
| GET | `/api/ai-content/history` | 생성 이력 조회 |
| POST | `/api/chat` | AI 채팅 |
| GET | `/api/chat/{session_id}/messages` | 채팅 메시지 조회 |

### 이미지 생성
| 메서드 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| POST | `/api/image/generate` | 이미지 생성 |
| POST | `/api/image/optimize-prompt` | 프롬프트 최적화 |

### 동영상 생성
| 메서드 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| POST | `/api/ai-video/generate` | 동영상 생성 시작 |
| GET | `/api/ai-video/status/{job_id}` | 생성 상태 조회 |
| GET | `/api/videos/history` | 동영상 이력 |

### 카드뉴스
| 메서드 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| POST | `/api/cardnews/generate` | 카드뉴스 생성 |
| GET | `/api/cardnews/{id}` | 카드뉴스 조회 |

### 브랜드 분석
| 메서드 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| POST | `/api/brand-analysis/analyze` | 브랜드 분석 실행 |
| GET | `/api/brand-analysis/{user_id}` | 분석 결과 조회 |

### SNS 연동
| 메서드 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| GET | `/api/youtube/connect` | YouTube 연동 |
| GET | `/api/facebook/connect` | Facebook 연동 |
| GET | `/api/instagram/connect` | Instagram 연동 |
| GET | `/api/x/connect` | X(Twitter) 연동 |
| GET | `/api/threads/connect` | Threads 연동 |
| GET | `/api/tiktok/connect` | TikTok 연동 |
| GET | `/api/wordpress/connect` | WordPress 연동 |
| POST | `/api/sns/publish` | 통합 SNS 발행 |

### 크레딧
| 메서드 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| GET | `/api/credits/packages` | 크레딧 패키지 목록 |
| GET | `/api/credits/balance` | 현재 크레딧 잔액 |
| POST | `/api/credits/purchase` | 크레딧 구매 |
| GET | `/api/credits/transactions` | 거래 이력 |

### 템플릿
| 메서드 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| GET | `/api/templates` | 템플릿 목록 |
| POST | `/api/templates` | 템플릿 생성 |
| PUT | `/api/templates/{id}` | 템플릿 수정 |
| DELETE | `/api/templates/{id}` | 템플릿 삭제 |

### 발행 콘텐츠
| 메서드 | 엔드포인트 | 설명 |
| :--- | :--- | :--- |
| GET | `/api/published` | 발행 콘텐츠 목록 |
| GET | `/api/published/{id}` | 발행 콘텐츠 상세 |

---

## 데이터베이스 모델 (40개)

### 사용자 관리 (2개)
- `User`: OAuth 정보, 비즈니스 정보
- `UserPreference`: 텍스트/이미지/동영상 스타일 선호도

### 콘텐츠 (6개)
- `Content`: 통합 콘텐츠
- `ContentGenerationSession`: 생성 세션 추적
- `GeneratedBlogContent`: 블로그 포스트
- `GeneratedSNSContent`: SNS 콘텐츠
- `GeneratedXContent`: X(Twitter) 콘텐츠
- `GeneratedThreadsContent`: Threads 콘텐츠

### 이미지 & 동영상 (4개)
- `GeneratedImage`: 생성된 이미지
- `GeneratedCardnewsContent`: 카드뉴스
- `VideoGenerationJob`: 동영상 생성 작업
- `GeneratedVideo`: 생성된 동영상

### 브랜드 분석 (1개)
- `BrandAnalysis`: 멀티 플랫폼 브랜드 프로필

### 채팅 (2개)
- `ChatSession`: AI 채팅 세션
- `ChatMessage`: 채팅 메시지

### SNS 연동 (14개)
- YouTube: `YouTubeConnection`, `YouTubeVideo`, `YouTubeAnalytics`
- Facebook: `FacebookConnection`, `FacebookPost`
- Instagram: `InstagramConnection`, `InstagramPost`
- X(Twitter): `XConnection`, `XPost`
- Threads: `ThreadsConnection`, `ThreadsPost`
- TikTok: `TikTokConnection`, `TikTokVideo`
- WordPress: `WordPressConnection`, `WordPressPost`

### 발행 추적 (1개)
- `PublishedContent`: 통합 발행 추적

### 크레딧 시스템 (3개)
- `UserCredit`: 크레딧 잔액
- `CreditTransaction`: 거래 이력
- `CreditPackage`: 구매 패키지

### 템플릿 (2개)
- `TemplateTab`: 템플릿 카테고리
- `Template`: 콘텐츠 템플릿

---

## Agentic AI 아키텍처

### 콘텐츠 생성 워크플로우
| 에이전트 | 역할 |
| :--- | :--- |
| ContentPlannerAgent | 콘텐츠 계획 수립 |
| ContentEnricherAgent | 콘텐츠 작성 |
| QualityAssuranceAgent | 품질 검증 |
| VisualDesignerAgent | 비주얼 최적화 |
| OrchestratorAgent | 전체 워크플로우 조정 |

### 브랜드 분석 파이프라인
| 에이전트 | 역할 |
| :--- | :--- |
| DataCollectorAgent | 플랫폼 데이터 수집 |
| StyleAnalyzerAgent | 스타일 분석 |
| BrandSynthesizerAgent | 브랜드 프로필 통합 |

---

## 보안

- JWT 토큰 기반 인증
- OAuth 2.0 소셜 로그인
- CORS 설정으로 허용된 오리진만 접근 가능
- 환경 변수로 민감 정보 관리
- `.env` 파일은 절대 Git에 커밋하지 마세요

---

## 개발 팁

### API 테스트

Swagger UI (`/docs`)에서 직접 API를 테스트하거나 curl 사용:

```bash
# OAuth 로그인 URL 확인
curl http://localhost:8000/api/oauth/google/login

# AI 채팅 (인증 필요)
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{"message": "블로그 콘텐츠 아이디어 추천해줘"}'
```

### 로그 확인

```bash
tail -f logs/app.log
```
