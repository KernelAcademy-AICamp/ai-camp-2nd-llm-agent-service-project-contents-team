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

# 확인 메시지
read -p "계속하시겠습니까? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "마이그레이션을 취소했습니다."
    exit 0
fi

echo ""
echo "🗑️  기존 데이터베이스 삭제 중..."

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
echo "✅ 마이그레이션 완료!"
echo ""
echo "다음 단계:"
echo "1. 백엔드 서버를 시작하면 새 데이터베이스가 자동으로 생성됩니다."
echo "   uvicorn app.main:app --reload"
echo ""
echo "2. 또는 npm start로 프론트엔드와 함께 시작:"
echo "   cd .. && npm start"
