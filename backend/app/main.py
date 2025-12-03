from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from pathlib import Path
from dotenv import load_dotenv
from .routers import auth, oauth, image, video, cardnews, onboarding, ai_recommendations, user, blog, chat, brand_analysis, youtube, facebook, instagram, x, ai_video_generation, sns_publish, ai_content, sns_content
from .database import engine, Base


# 루트 .env 파일 먼저 로드 (프로젝트 루트) - 라우터 import 전에 로드 필수!
root_env = Path(__file__).parent.parent.parent / ".env"
load_dotenv(root_env)

# backend/.env 파일 로드 (있으면 덮어쓰기)
load_dotenv()

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Contents Creator API",
    description="AI 기반 콘텐츠 제작 서비스 API (OAuth2.0 소셜 로그인)",
    version="1.0.0"
)

# Session Middleware (OAuth에 필요)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key-here")
)

# CORS 설정 - 개발 환경에서는 모든 출처 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서 모든 출처 허용
    allow_credentials=False,  # credentials를 사용하지 않으므로 False
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(user.router)
app.include_router(image.router)
app.include_router(video.router)
app.include_router(cardnews.router)
app.include_router(onboarding.router)
app.include_router(ai_recommendations.router)
app.include_router(blog.router)
app.include_router(chat.router)
app.include_router(brand_analysis.router)
app.include_router(youtube.router)
app.include_router(facebook.router)
app.include_router(instagram.router)
app.include_router(x.router)
app.include_router(ai_video_generation.router)
app.include_router(sns_publish.router)
app.include_router(ai_content.router)
app.include_router(sns_content.router)


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
