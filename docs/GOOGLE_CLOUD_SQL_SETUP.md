# Google Cloud SQL 설정 가이드

이 가이드는 Google Cloud SQL에 PostgreSQL 데이터베이스를 설정하고 연결하는 방법을 설명합니다.

## 1. Google Cloud SQL 인스턴스 생성

### 1.1 Google Cloud Console에서 작업

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 프로젝트 선택 또는 새 프로젝트 생성
3. 좌측 메뉴에서 **SQL** 선택
4. **인스턴스 만들기** 클릭
5. **PostgreSQL** 선택

### 1.2 인스턴스 구성

**기본 설정:**
- **인스턴스 ID**: `contents-creator-db` (원하는 이름)
- **비밀번호**: 강력한 비밀번호 설정 (저장 필수!)
- **데이터베이스 버전**: PostgreSQL 15 (또는 최신 버전)
- **리전**: `asia-northeast3` (서울) 추천
- **영역**: 단일 영역

**머신 구성:**
- **머신 유형**:
  - 개발/테스트: `db-f1-micro` (무료 티어, 메모리 0.6GB)
  - 프로덕션: `db-n1-standard-1` (메모리 3.75GB)

**스토리지:**
- **스토리지 유형**: SSD
- **스토리지 용량**: 10GB (시작용, 자동 증가 활성화)

**연결:**
- **공개 IP**: 활성화
- **승인된 네트워크**:
  - 개발 환경: `0.0.0.0/0` (모든 IP 허용, 보안 주의!)
  - 프로덕션: 특정 IP만 허용

6. **인스턴스 만들기** 클릭 (생성에 5-10분 소요)

## 2. 데이터베이스 생성

인스턴스가 생성되면:

1. 생성된 인스턴스 클릭
2. **데이터베이스** 탭 선택
3. **데이터베이스 만들기** 클릭
4. **데이터베이스 이름**: `contents_creator`
5. **만들기** 클릭

## 3. 연결 정보 확인

1. 인스턴스 개요 페이지에서 다음 정보 확인:
   - **공개 IP 주소**: 예) `34.64.123.456`
   - **연결 이름**: 예) `프로젝트ID:리전:인스턴스ID`

## 4. 로컬 환경 설정

### 4.1 필요한 패키지 설치

```bash
# PostgreSQL 어댑터 설치
pip install psycopg2-binary

# 또는 컴파일 버전 (더 빠름, 시스템에 PostgreSQL 필요)
pip install psycopg2
```

### 4.2 환경 변수 설정

프로젝트 루트의 `.env` 파일에 추가:

```env
# Google Cloud SQL 설정
ENV=production
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@YOUR_PUBLIC_IP:5432/contents_creator

# 예시:
# DATABASE_URL=postgresql://postgres:MySecurePass123!@34.64.123.456:5432/contents_creator
```

**주의사항:**
- `YOUR_PASSWORD`: Cloud SQL 생성 시 설정한 비밀번호
- `YOUR_PUBLIC_IP`: Cloud SQL 인스턴스의 공개 IP
- `contents_creator`: 생성한 데이터베이스 이름

## 5. 데이터베이스 마이그레이션

### 5.1 기존 SQLite 데이터 백업 (옵션)

```bash
# SQLite 데이터를 JSON으로 내보내기 (필요한 경우)
cd backend
python -c "
from app.database import SessionLocal, engine
from app.models import User
import json

db = SessionLocal()
users = db.query(User).all()
data = [{'id': u.id, 'email': u.email, 'username': u.username} for u in users]
with open('backup.json', 'w') as f:
    json.dump(data, f, indent=2)
db.close()
print('Backup completed!')
"
```

### 5.2 새 데이터베이스에 테이블 생성

```bash
cd backend
python -c "
from app.database import engine, Base
from app.models import *  # 모든 모델 import

print('Creating tables...')
Base.metadata.create_all(bind=engine)
print('Tables created successfully!')
"
```

## 6. 연결 테스트

```bash
cd backend
python -c "
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    result = db.execute(text('SELECT version();'))
    version = result.fetchone()[0]
    print('✓ Connected to PostgreSQL!')
    print(f'Version: {version}')

    # 테이블 확인
    result = db.execute(text(\"\"\"
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    \"\"\"))
    tables = [row[0] for row in result.fetchall()]
    print(f'Tables: {tables}')
except Exception as e:
    print(f'✗ Connection failed: {e}')
finally:
    db.close()
"
```

## 7. Cloud SQL Auth Proxy 사용 (권장)

더 안전한 연결을 위해 Cloud SQL Auth Proxy 사용:

### 7.1 Cloud SQL Auth Proxy 다운로드

**macOS:**
```bash
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64
chmod +x cloud-sql-proxy
```

**Linux:**
```bash
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy
```

**Windows:**
```powershell
Invoke-WebRequest -Uri https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.x64.exe -OutFile cloud-sql-proxy.exe
```

### 7.2 서비스 계정 키 생성

1. Google Cloud Console에서 **IAM 및 관리자** > **서비스 계정**
2. **서비스 계정 만들기**
3. 역할: **Cloud SQL 클라이언트** 추가
4. **키 만들기** > **JSON** 선택
5. 다운로드한 JSON 파일을 프로젝트에 저장 (예: `gcloud-key.json`)

### 7.3 Proxy 실행

```bash
./cloud-sql-proxy --credentials-file=./gcloud-key.json 프로젝트ID:리전:인스턴스ID
```

### 7.4 환경 변수 수정 (Proxy 사용 시)

```env
# Cloud SQL Auth Proxy 사용 시
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@127.0.0.1:5432/contents_creator
```

## 8. 프로덕션 배포 시 고려사항

### 8.1 연결 풀 설정

현재 `database.py`에 이미 구현됨:
- `pool_size=10`: 기본 연결 풀
- `max_overflow=20`: 최대 초과 연결
- `pool_pre_ping=True`: 연결 유효성 검사
- `pool_recycle=3600`: 1시간마다 재활용

### 8.2 보안 설정

1. **승인된 네트워크 제한**: 특정 IP만 허용
2. **SSL 연결 강제**: Cloud SQL에서 설정 가능
3. **비밀번호 강화**: 복잡한 비밀번호 사용
4. **환경 변수 보안**: `.env` 파일을 git에 커밋하지 않음

### 8.3 백업 설정

1. Cloud SQL 인스턴스에서 **백업** 탭
2. **자동 백업 사용 설정**
3. 백업 시간대 설정 (사용량이 적은 시간)
4. 백업 보관 기간 설정 (7일 권장)

## 9. 비용 최적화

### 무료 티어 사용:
- **인스턴스 유형**: `db-f1-micro`
- **스토리지**: 10GB까지 무료
- **리전**: us-central1, us-west1, us-east1 (아시아는 유료)

### 비용 절감 팁:
1. 사용하지 않을 때 인스턴스 중지
2. 스토리지 자동 증가 비활성화 (수동 관리)
3. 백업 보관 기간 최소화
4. 불필요한 리플리카 제거

## 10. 문제 해결

### 연결 실패 시:

1. **방화벽 규칙 확인**:
   - Cloud SQL 인스턴스의 승인된 네트워크 확인
   - 로컬 방화벽 설정 확인

2. **비밀번호 확인**:
   - 특수문자가 URL에 올바르게 인코딩되었는지 확인
   - 필요시 urllib.parse.quote() 사용

3. **포트 확인**:
   - PostgreSQL 기본 포트: 5432
   - Cloud SQL Auth Proxy 사용 시: 127.0.0.1:5432

4. **로그 확인**:
   ```bash
   # FastAPI 서버 로그 확인
   # 연결 오류 메시지 확인
   ```

## 11. requirements.txt 업데이트

```txt
# PostgreSQL 지원
psycopg2-binary==2.9.9
# 또는
psycopg2==2.9.9
```

## 참고 자료

- [Cloud SQL 문서](https://cloud.google.com/sql/docs)
- [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)
- [PostgreSQL 문서](https://www.postgresql.org/docs/)
