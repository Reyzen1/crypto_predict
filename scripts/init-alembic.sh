#!/bin/bash
# File: scripts/init-alembic.sh
# Initialize Alembic for database migrations

set -e

echo "🗄️ Initializing Alembic for Database Migrations"
echo "==============================================="

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

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres123@localhost:5432/cryptopredict"
export REDIS_URL="redis://localhost:6379/0"

# Check if Alembic is already initialized
if [ -d "alembic" ]; then
    echo "⚠️ Alembic already initialized. Skipping initialization."
else
    echo "🚀 Initializing Alembic..."
    alembic init alembic
    echo "✅ Alembic initialized!"
fi

echo ""
echo "🎉 Alembic setup complete!"
echo "========================="
echo ""
echo "Next steps:"
echo "1. Review alembic.ini configuration"
echo "2. Create database models"
echo "3. Generate first migration: alembic revision --autogenerate -m 'Initial migration'"
echo "4. Apply migration: alembic upgrade head"

cd ..