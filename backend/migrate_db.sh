#!/bin/bash

echo "⚠️  데이터베이스 마이그레이션을 시작합니다."
echo "⚠️  주의: 기존 데이터가 모두 삭제됩니다!"
echo ""

# 현재 디렉토리 확인
if [ ! -f "app/main.py" ]; then
    echo "❌ backend 디렉토리에서 실행해주세요."
    echo "   cd backend && bash migrate_db.sh"
    exit 1
fi

# .env 파일 로드
if [ -f "../.env" ]; then
    export $(grep -v '^#' ../.env | xargs)
elif [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# DATABASE_URL 확인
DATABASE_URL=${DATABASE_URL:-"sqlite:///./app.db"}

echo "📊 데이터베이스 URL: $DATABASE_URL"
echo ""

# 확인 메시지
read -p "계속하시겠습니까? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "마이그레이션을 취소했습니다."
    exit 0
fi

echo ""

# SQLite인 경우
if [[ $DATABASE_URL == sqlite* ]]; then
    echo "🗑️  SQLite 데이터베이스 삭제 중..."

    # 기존 데이터베이스 파일 삭제
    if [ -f "app.db" ]; then
        rm app.db
        echo "✅ app.db 삭제 완료"
    fi

    if [ -f "app.db-shm" ]; then
        rm app.db-shm
        echo "✅ app.db-shm 삭제 완료"
    fi

    if [ -f "app.db-wal" ]; then
        rm app.db-wal
        echo "✅ app.db-wal 삭제 완료"
    fi

    echo ""
    echo "✅ SQLite 마이그레이션 완료!"
    echo ""
    echo "다음 단계:"
    echo "1. 백엔드 서버를 시작하면 새 데이터베이스가 자동으로 생성됩니다."
    echo "   uvicorn app.main:app --reload"
    echo ""
    echo "2. 또는 npm start로 프론트엔드와 함께 시작:"
    echo "   cd .. && npm start"

# PostgreSQL인 경우
elif [[ $DATABASE_URL == postgresql* ]]; then
    echo "🐘 PostgreSQL 데이터베이스 마이그레이션..."
    echo ""
    echo "⚠️  PostgreSQL 마이그레이션은 수동으로 진행해야 합니다:"
    echo ""
    echo "1. PostgreSQL에 연결:"
    echo "   psql -U username -d dbname"
    echo ""
    echo "2. 모든 테이블 삭제 (주의!):"
    echo "   DROP TABLE IF EXISTS users CASCADE;"
    echo "   DROP TABLE IF EXISTS instagram_accounts CASCADE;"
    echo "   DROP TABLE IF EXISTS posts CASCADE;"
    echo "   DROP TABLE IF EXISTS scheduled_posts CASCADE;"
    echo ""
    echo "3. 백엔드 서버를 시작하면 테이블이 자동으로 생성됩니다:"
    echo "   uvicorn app.main:app --reload"
    echo ""
    echo "또는 Python을 사용하여 테이블 생성:"
    echo "   python3 -c \"from app.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine)\""
    echo ""
else
    echo "❌ 지원되지 않는 데이터베이스 URL입니다."
    exit 1
fi
