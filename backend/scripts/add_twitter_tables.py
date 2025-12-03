"""
Twitter 연동을 위한 테이블 추가 마이그레이션
- twitter_connections: Twitter 계정 연동 정보
- tweets: 트윗 정보
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# .env 파일 로드
root_env = Path(__file__).parent.parent.parent / ".env"
load_dotenv(root_env)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL 환경 변수가 설정되지 않았습니다")
    sys.exit(1)

print(f"데이터베이스 연결 중: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # twitter_connections 테이블 생성
        print("twitter_connections 테이블 생성 중...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS twitter_connections (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,

                -- Twitter 사용자 정보
                twitter_user_id VARCHAR NOT NULL,
                username VARCHAR,
                name VARCHAR,
                description TEXT,
                profile_image_url VARCHAR,
                verified BOOLEAN DEFAULT FALSE,

                -- 계정 통계
                followers_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0,
                tweet_count INTEGER DEFAULT 0,
                listed_count INTEGER DEFAULT 0,

                -- OAuth 2.0 토큰 정보
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                token_expires_at TIMESTAMP WITH TIME ZONE,

                -- 연동 상태
                is_active BOOLEAN DEFAULT TRUE,
                last_synced_at TIMESTAMP WITH TIME ZONE,

                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))

        # twitter_user_id 인덱스 생성
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_twitter_connections_twitter_user_id
            ON twitter_connections(twitter_user_id)
        """))

        print("tweets 테이블 생성 중...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tweets (
                id SERIAL PRIMARY KEY,
                connection_id INTEGER NOT NULL REFERENCES twitter_connections(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                -- 트윗 기본 정보
                tweet_id VARCHAR NOT NULL UNIQUE,
                text TEXT,
                created_at_twitter TIMESTAMP WITH TIME ZONE,

                -- 미디어 정보
                media_type VARCHAR,
                media_url VARCHAR,
                media_urls JSONB,

                -- 트윗 통계
                retweet_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                quote_count INTEGER DEFAULT 0,
                bookmark_count INTEGER DEFAULT 0,
                impression_count INTEGER DEFAULT 0,

                -- 트윗 메타데이터
                conversation_id VARCHAR,
                in_reply_to_user_id VARCHAR,
                referenced_tweets JSONB,

                -- 동기화 정보
                last_stats_updated_at TIMESTAMP WITH TIME ZONE,

                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))

        # tweet_id 인덱스 생성
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_tweets_tweet_id ON tweets(tweet_id)
        """))

        conn.commit()
        print("✅ Twitter 테이블 마이그레이션 완료!")
        print("")
        print("생성된 테이블:")
        print("  - twitter_connections: Twitter 계정 연동 정보")
        print("  - tweets: 트윗 정보")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    sys.exit(1)
