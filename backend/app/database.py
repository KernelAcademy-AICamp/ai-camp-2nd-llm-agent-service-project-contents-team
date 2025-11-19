from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# 환경 변수 설정
ENV = os.getenv("ENV", "development")  # development, production, test
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# 데이터베이스 연결 설정
if DATABASE_URL.startswith("sqlite"):
    # SQLite 설정 (개발 환경)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
elif DATABASE_URL.startswith("postgresql"):
    # PostgreSQL 설정 (프로덕션 환경)
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,              # 연결 풀 크기
        max_overflow=20,           # 최대 초과 연결 수
        pool_pre_ping=True,        # 연결 유효성 검사
        pool_recycle=3600,         # 1시간마다 연결 재활용
        echo=ENV == "development"  # 개발 환경에서만 SQL 로그 출력
    )
else:
    # 기본 설정
    engine = create_engine(DATABASE_URL)

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
