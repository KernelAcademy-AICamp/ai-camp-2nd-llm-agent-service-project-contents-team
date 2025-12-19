from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os
from pathlib import Path
from dotenv import load_dotenv
from .routers import auth, oauth, image, generated_videos, cardnews, onboarding, ai_recommendations, user, chat, brand_analysis, ai_video_generation, ai_content, published_content, dashboard, credits, templates
from .routers.sns import blog, youtube, facebook, instagram, x, threads, tiktok, wordpress
from .database import engine, Base
from .scheduler import start_scheduler, stop_scheduler


# 루트 .env 파일 먼저 로드 (프로젝트 루트) - 라우터 import 전에 로드 필수!
root_env = Path(__file__).parent.parent.parent / ".env"
load_dotenv(root_env)

# backend/.env 파일 로드 (있으면 덮어쓰기)
load_dotenv()


# Google Cloud / Vertex AI 인증 설정
def setup_google_credentials():
    """
    Google Cloud 인증 설정
    - GOOGLE_APPLICATION_CREDENTIALS가 이미 설정되어 있으면 절대 경로로 변환
    - GOOGLE_CREDENTIALS_BASE64가 있으면 디코딩해서 임시 파일로 저장
    """
    # GOOGLE_APPLICATION_CREDENTIALS가 설정되어 있으면 절대 경로로 변환
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path:
        # 상대 경로인 경우 절대 경로로 변환
        if not os.path.isabs(credentials_path):
            # 프로젝트 루트 디렉토리 기준으로 절대 경로 생성
            # Path(__file__) = backend/app/main.py
            # .parent.parent.parent = 프로젝트 루트
            project_root = Path(__file__).parent.parent.parent
            credentials_path = str(project_root / credentials_path)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        # 파일 존재 여부 확인
        if os.path.exists(credentials_path):
            print(f"✅ Vertex AI credentials set: {credentials_path}")
            print(f"   Project: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
            print(f"   Location: {os.getenv('GOOGLE_CLOUD_LOCATION')}")
        else:
            print(f"⚠️  Credentials file not found: {credentials_path}")
        return

    # Base64 환경 변수가 있으면 디코딩해서 임시 파일로 저장
    credentials_base64 = os.getenv("GOOGLE_CREDENTIALS_BASE64")
    if credentials_base64:
        import base64
        import tempfile

        try:
            credentials_json = base64.b64decode(credentials_base64).decode('utf-8')

            # 임시 파일 생성 (서버가 실행되는 동안 유지)
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
            temp_file.write(credentials_json)
            temp_file.close()

            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file.name
            print(f"✅ Vertex AI credentials loaded from GOOGLE_CREDENTIALS_BASE64")
            print(f"   Project: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
            print(f"   Location: {os.getenv('GOOGLE_CLOUD_LOCATION')}")
        except Exception as e:
            print(f"⚠️  Failed to load Vertex AI credentials: {e}")
    else:
        print(f"ℹ️  No Vertex AI credentials found (GOOGLE_CREDENTIALS_BASE64 or GOOGLE_APPLICATION_CREDENTIALS)")


# 앱 시작 전 인증 설정
setup_google_credentials()

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# 초기 크레딧 패키지 시딩 (앱 시작 시 한 번만)
def seed_initial_credit_packages():
    from .database import SessionLocal
    from . import models

    db = SessionLocal()
    try:
        # 이미 패키지가 있으면 스킵
        if db.query(models.CreditPackage).first():
            return

        packages = [
            models.CreditPackage(name="스타터", description="처음 시작하는 분들을 위한 패키지", credits=50, bonus_credits=0, price=5000, sort_order=1),
            models.CreditPackage(name="베이직", description="가벼운 콘텐츠 제작에 적합", credits=120, bonus_credits=10, price=10000, sort_order=2),
            models.CreditPackage(name="스탠다드", description="가장 많이 선택하는 인기 패키지", credits=300, bonus_credits=50, price=25000, badge="인기", is_popular=True, sort_order=3),
            models.CreditPackage(name="프로", description="전문 크리에이터를 위한 패키지", credits=700, bonus_credits=150, price=50000, badge="추천", sort_order=4),
            models.CreditPackage(name="엔터프라이즈", description="대량 콘텐츠 제작에 최적화", credits=1500, bonus_credits=500, price=100000, badge="BEST", sort_order=5),
        ]
        for pkg in packages:
            db.add(pkg)
        db.commit()
        print("✅ 크레딧 패키지 초기 데이터 생성 완료")
    except Exception as e:
        print(f"⚠️ 크레딧 패키지 시딩 실패: {e}")
    finally:
        db.close()

seed_initial_credit_packages()


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
app.include_router(threads.router)
app.include_router(tiktok.router)
app.include_router(wordpress.router)
app.include_router(ai_video_generation.router)
app.include_router(generated_videos.router)
app.include_router(ai_content.router)
app.include_router(published_content.router)
app.include_router(dashboard.router)
app.include_router(credits.router)
app.include_router(templates.router)

# Static files 설정 (업로드된 파일 서빙)
uploads_dir = Path(__file__).parent.parent / "uploads"
uploads_dir.mkdir(exist_ok=True)  # uploads 디렉토리가 없으면 생성
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Static files 설정 (템플릿 미리보기 이미지 등)
static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


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


# 앱 시작/종료 이벤트
@app.on_event("startup")
async def startup_event():
    """앱 시작 시 스케줄러 시작"""
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 스케줄러 정지"""
    stop_scheduler()
