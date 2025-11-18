from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv

from .routers import auth, oauth, image
from .database import engine, Base

load_dotenv()

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Contents Creator API",
    description="AI 기반 콘텐츠 제작 및 자동화 서비스 API (OAuth2.0 소셜 로그인 전용)",
    version="1.0.0"
)

# Session Middleware (OAuth에 필요)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key-here")
)

# CORS 설정
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(image.router)


@app.get("/")
def read_root():
    """
    API 루트 엔드포인트
    """
    return {
        "message": "Welcome to Contents Creator API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """
    헬스 체크 엔드포인트
    """
    return {"status": "healthy"}
