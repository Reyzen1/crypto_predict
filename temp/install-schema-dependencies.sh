# File: ./scripts/install-schema-dependencies.sh
# Install additional dependencies needed for Pydantic schemas

#!/bin/bash

set -e

echo "📦 Installing Schema Dependencies"
echo "================================="

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
    exit 1
fi

echo ""
echo "📦 Installing Pydantic email validation..."
pip install "pydantic[email]"

echo ""
echo "📦 Installing additional validation libraries..."
pip install email-validator

echo ""
echo "📦 Installing JWT and authentication libraries..."
pip install python-jose[cryptography]
pip install passlib[bcrypt]

echo ""
echo "📦 Installing HTTP client for external APIs..."
pip install httpx

echo ""
echo "📦 Installing background task scheduler..."
pip install apscheduler

echo ""
echo "📦 Installing additional FastAPI utilities..."
pip install python-multipart

echo ""
echo "📋 Checking installed packages..."
python -c "
import pydantic
import email_validator
from pydantic import EmailStr
print('✅ Pydantic with email validation: ' + pydantic.VERSION)

try:
    from jose import jwt
    print('✅ Python-jose for JWT: Available')
except ImportError:
    print('❌ Python-jose: Not available')

try:
    from passlib.context import CryptContext
    print('✅ Passlib for password hashing: Available')
except ImportError:
    print('❌ Passlib: Not available')

try:
    import httpx
    print('✅ HTTPX for HTTP requests: Available')
except ImportError:
    print('❌ HTTPX: Not available')

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    print('✅ APScheduler for background jobs: Available')
except ImportError:
    print('❌ APScheduler: Not available')
"

cd ..

echo ""
echo "🎉 All Schema Dependencies Installed!"
echo "===================================="
echo ""
echo "✅ Pydantic with email validation"
echo "✅ Python-jose for JWT tokens"
echo "✅ Passlib for password hashing"
echo "✅ HTTPX for HTTP requests"
echo "✅ APScheduler for background tasks"
echo ""
echo "🧪 Now run schema tests:"
echo "   ./scripts/test-schemas.sh"