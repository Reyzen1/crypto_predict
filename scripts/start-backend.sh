#!/bin/bash
# File: scripts/start-backend.sh
# Start backend script for Git Bash

set -e

echo "🐍 Starting FastAPI Backend..."
echo "==============================="

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found! Please run from project root."
    exit 1
fi

cd backend

# Activate virtual environment
if [ -f "venv/Scripts/activate" ]; then
    echo "🔧 Activating virtual environment (Windows)..."
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    echo "🔧 Activating virtual environment (Linux/Mac)..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "Please run: ./scripts/quick-setup.sh first"
    exit 1
fi

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "❌ uvicorn not found! Installing..."
    pip install uvicorn fastapi
fi

# Set environment variables
echo "🔧 Setting environment variables..."
export DATABASE_URL="postgresql://postgres:postgres123@localhost:5432/cryptopredict"
export REDIS_URL="redis://localhost:6379/0"
export ENVIRONMENT="development"
export DEBUG="true"
export SECRET_KEY="dev-secret-key-change-in-production"
export JWT_SECRET_KEY="dev-jwt-secret-key-change-in-production"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES="30"
export BACKEND_CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

echo ""
echo "🚀 Backend starting at: http://localhost:8000"
echo "📚 API Docs available at: http://localhost:8000/docs"
echo "📖 Alternative Docs at: http://localhost:8000/redoc"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Start FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload