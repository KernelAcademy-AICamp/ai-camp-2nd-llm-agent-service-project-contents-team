#!/bin/bash

echo "🚀 Setting up FastAPI Backend..."

# Python 버전 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"

# 가상환경 생성 (이미 있으면 스킵)
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# 가상환경 활성화
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# 의존성 설치
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Backend setup complete!"
echo ""
echo "To manually activate the virtual environment, run:"
echo "  source backend/venv/bin/activate"
