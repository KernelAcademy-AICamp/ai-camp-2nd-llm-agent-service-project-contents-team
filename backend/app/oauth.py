from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
import os
from dotenv import load_dotenv

load_dotenv()

config = Config(environ=os.environ)

oauth = OAuth(config)

# Google OAuth
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID', ''),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET', ''),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    redirect_uri=os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/oauth/google/callback'),
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Kakao OAuth
oauth.register(
    name='kakao',
    client_id=os.getenv('KAKAO_CLIENT_ID', ''),
    client_secret=os.getenv('KAKAO_CLIENT_SECRET', ''),
    authorize_url='https://kauth.kakao.com/oauth/authorize',
    authorize_params=None,
    access_token_url='https://kauth.kakao.com/oauth/token',
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri=os.getenv('KAKAO_REDIRECT_URI', 'http://localhost:8000/api/oauth/kakao/callback'),
    client_kwargs={'scope': 'profile_nickname profile_image'},
)

# Facebook OAuth (로그인용)
oauth.register(
    name='facebook',
    client_id=os.getenv('FACEBOOK_CLIENT_ID', ''),
    client_secret=os.getenv('FACEBOOK_CLIENT_SECRET', ''),
    authorize_url='https://www.facebook.com/v18.0/dialog/oauth',
    authorize_params=None,
    access_token_url='https://graph.facebook.com/v18.0/oauth/access_token',
    access_token_params=None,
    redirect_uri=os.getenv('FACEBOOK_REDIRECT_URI', 'http://localhost:8000/api/oauth/facebook/callback'),
    client_kwargs={'scope': 'email public_profile'},
)

# Facebook Pages OAuth (페이지 관리용)
# 개발 모드에서는 기본 권한만 사용 (앱 검토 후 고급 권한 추가 가능)
# 고급 권한 (앱 검토 필요): pages_manage_posts, pages_manage_metadata, pages_read_user_content
oauth.register(
    name='facebook_pages',
    client_id=os.getenv('FACEBOOK_CLIENT_ID', ''),
    client_secret=os.getenv('FACEBOOK_CLIENT_SECRET', ''),
    authorize_url='https://www.facebook.com/v18.0/dialog/oauth',
    authorize_params=None,
    access_token_url='https://graph.facebook.com/v18.0/oauth/access_token',
    access_token_params=None,
    redirect_uri=os.getenv('FACEBOOK_PAGES_REDIRECT_URI', 'http://localhost:8000/api/facebook/callback'),
    client_kwargs={
        'scope': ' '.join([
            'public_profile',
            'pages_show_list',              # 페이지 목록 조회 (기본 권한)
            'pages_read_engagement',        # 페이지 인사이트 읽기 (기본 권한)
        ]),
    }
)

# YouTube OAuth (Google OAuth with YouTube scopes)
oauth.register(
    name='youtube',
    client_id=os.getenv('GOOGLE_CLIENT_ID', ''),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET', ''),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    redirect_uri=os.getenv('YOUTUBE_REDIRECT_URI', 'http://localhost:8000/api/youtube/callback'),
    client_kwargs={
        'scope': ' '.join([
            'openid',
            'email',
            'profile',
            'https://www.googleapis.com/auth/youtube.readonly',           # 채널 및 동영상 정보 읽기
            'https://www.googleapis.com/auth/youtube.upload',             # 동영상 업로드
            'https://www.googleapis.com/auth/youtube.force-ssl',          # 댓글, 좋아요 등 관리
            'https://www.googleapis.com/auth/yt-analytics.readonly',      # 분석 데이터 읽기
        ]),
        'access_type': 'offline',  # refresh token 받기 위해 필요
        'prompt': 'consent',       # 항상 동의 화면 표시 (refresh token 보장)
    }
)
