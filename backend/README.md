# Contents Creator Backend API

FastAPI 기반 콘텐츠 크리에이터 백엔드 서비스입니다.

## 기능

- ✅ JWT 기반 사용자 인증
- ✅ 회원가입/로그인/로그아웃
- ✅ 사용자 프로필 관리
- ✅ SQLite 데이터베이스 (PostgreSQL로 변경 가능)
- ✅ CORS 설정 (React 프론트엔드와 연동)

## 설치 및 실행

### 1. Python 가상환경 생성 (권장)

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

`.env.example` 파일을 `.env`로 복사하고 필요한 값을 설정합니다:

```bash
cp .env.example .env
```

`.env` 파일에서 `SECRET_KEY`를 변경하세요. 안전한 시크릿 키를 생성하려면:

```bash
openssl rand -hex 32
```

### 4. 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

서버가 `http://localhost:8000`에서 실행됩니다.

## API 문서

서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API 엔드포인트

### 인증 (Authentication)

#### 회원가입
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "full_name": "User Name"
}
```

#### 로그인
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=username&password=password123
```

응답:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 로그아웃
```http
POST /api/auth/logout
Authorization: Bearer {access_token}
```

#### 현재 사용자 정보 조회
```http
GET /api/auth/me
Authorization: Bearer {access_token}
```

#### 사용자 정보 수정
```http
PUT /api/auth/me
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "email": "newemail@example.com",
  "username": "newusername",
  "full_name": "New Name"
}
```

## 데이터베이스

기본적으로 SQLite를 사용하며, `app.db` 파일에 저장됩니다.

PostgreSQL로 변경하려면 `.env` 파일에서 `DATABASE_URL`을 수정하세요:

```
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## 프로젝트 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI 애플리케이션
│   ├── models.py         # SQLAlchemy 모델
│   ├── schemas.py        # Pydantic 스키마
│   ├── database.py       # 데이터베이스 설정
│   ├── auth.py           # 인증 유틸리티
│   └── routers/
│       ├── __init__.py
│       └── auth.py       # 인증 라우터
├── .env                  # 환경 변수
├── .env.example          # 환경 변수 예시
├── .gitignore
├── requirements.txt      # Python 의존성
└── README.md
```

## 보안

- 비밀번호는 bcrypt로 해시되어 저장됩니다
- JWT 토큰을 사용한 인증
- CORS 설정으로 허용된 오리진만 접근 가능
- `.env` 파일은 절대 Git에 커밋하지 마세요

## 개발 팁

### API 테스트

Swagger UI (`/docs`)에서 직접 API를 테스트할 수 있습니다.

또는 curl을 사용:

```bash
# 회원가입
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"password123","full_name":"Test User"}'

# 로그인
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

### 데이터베이스 초기화

데이터베이스를 초기화하려면 `app.db` 파일을 삭제하고 서버를 다시 실행하세요:

```bash
rm app.db
uvicorn app.main:app --reload
```
