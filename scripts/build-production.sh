#!/bin/bash

# ==============================================
# Production Build Script
# ==============================================
# 사용법: ./scripts/build-production.sh
#
# 이 스크립트는 프로덕션용 프론트엔드 빌드를 생성합니다.
# .env.production 파일의 환경변수가 자동으로 적용됩니다.

set -e  # 에러 발생 시 스크립트 중단

echo "========================================"
echo "  Production Build Script"
echo "========================================"

# 프로젝트 루트 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo ""
echo "[1/4] Checking .env.production file..."
if [ ! -f ".env.production" ]; then
    echo "ERROR: .env.production file not found!"
    echo "Please create .env.production with the following content:"
    echo ""
    echo "REACT_APP_API_URL=https://ddukddak.p-e.kr"
    echo "REACT_APP_GEMINI_API_KEY=your_key_here"
    echo "REACT_APP_INSTAGRAM_APP_ID=your_app_id_here"
    exit 1
fi

echo ".env.production found!"
echo ""
echo "Environment variables to be included in build:"
grep "^REACT_APP_" .env.production | sed 's/=.*/=***/'
echo ""

echo "[2/4] Installing dependencies..."
npm install --silent

echo ""
echo "[3/4] Building production bundle..."
npm run build

echo ""
echo "[4/4] Verifying build..."
if [ -d "build" ]; then
    # localhost 참조 확인
    if grep -r "localhost:8000" build/static/js/*.js 2>/dev/null; then
        echo ""
        echo "WARNING: Build still contains localhost:8000 references!"
        echo "Please check your .env.production file."
    else
        echo "Build verified - no localhost:8000 references found."
    fi

    echo ""
    echo "========================================"
    echo "  Build Complete!"
    echo "========================================"
    echo ""
    echo "Build output: $PROJECT_ROOT/build/"
    echo ""
    echo "Next steps:"
    echo "1. Upload the 'build' folder to your server"
    echo "2. Make sure server .env has production URLs"
    echo ""
else
    echo "ERROR: Build folder not created!"
    exit 1
fi
