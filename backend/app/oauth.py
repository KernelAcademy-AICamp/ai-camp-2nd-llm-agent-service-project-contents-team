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

# Facebook OAuth
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
