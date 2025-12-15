from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드 (시스템 환경 변수 덮어쓰기)
root_env = Path(__file__).parent.parent.parent / ".env"
load_dotenv(root_env, override=True)
# 백엔드 .env 파일도 로드 (있으면 덮어쓰기)
load_dotenv(override=True)

# 환경 변수 설정
ENV = os.getenv("ENV", "development")  # development, production, test
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

# PostgreSQL 데이터베이스 연결 설정 (Supabase Pooler 최적화)
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,               # Supabase Free tier 제한 고려
        max_overflow=10,           # 최대 초과 연결 수
        pool_pre_ping=True,        # 연결 유효성 검사
        pool_recycle=300,          # 5분마다 연결 재활용 (Supabase 타임아웃 대응)
        pool_timeout=30,           # 연결 대기 타임아웃
        connect_args={
            "connect_timeout": 10,  # 연결 타임아웃 10초
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
        echo=False
    )
else:
    raise ValueError(f"지원하지 않는 데이터베이스입니다: {DATABASE_URL.split('://')[0]}. PostgreSQL만 지원합니다.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    데이터베이스 세션을 생성하고 반환합니다.
    요청이 끝나면 자동으로 세션을 닫습니다.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
