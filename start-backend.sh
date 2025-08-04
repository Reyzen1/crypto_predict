#!/bin/bash
# File: start-backend-local.sh
# Start backend development server

echo "🚀 Starting Backend Development Server"
echo "======================================"

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

cd backend

# Activate virtual environment if not active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    if [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
        echo "✅ Virtual environment activated"
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "⚠️  Virtual environment not found"
    fi
fi

echo "Environment: $ENVIRONMENT"
echo "Database: $DATABASE_URL"
echo "Redis: $REDIS_URL"
echo ""
echo "📍 Backend URL: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
