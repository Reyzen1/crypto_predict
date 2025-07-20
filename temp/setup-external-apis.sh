# File: ./temp/setup-external-apis.sh
# Setup External API Integration dependencies and structure

#!/bin/bash

set -e

echo "🌐 Setting up External API Integration"
echo "======================================"

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found! Please run from project root."
    exit 1
fi

echo "✅ Project structure verified"

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p backend/app/external
mkdir -p backend/app/services
echo "✅ Directories created"

# Move to backend directory
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

echo "📦 Installing External API dependencies..."
pip install --quiet --upgrade pip

# HTTP client for API calls
pip install --quiet httpx==0.25.2

# Retry and resilience library
pip install --quiet tenacity==8.2.3

# Redis async client
pip install --quiet aioredis==2.0.1

# Rate limiting library
pip install --quiet slowapi==0.1.9

# Data validation for external APIs
pip install --quiet pydantic==2.5.0

# Date/time handling
pip install --quiet python-dateutil==2.8.2

echo "✅ Dependencies installed"

# Update requirements.txt
echo ""
echo "📄 Updating requirements.txt..."
pip freeze > requirements.txt
echo "✅ Requirements.txt updated"

cd ..

echo ""
echo "🎯 Setup Complete!"
echo "=================="
echo ""
echo "✅ Directories created"
echo "✅ Dependencies installed:"
echo "   - httpx: Modern HTTP client"
echo "   - tenacity: Retry mechanisms"
echo "   - aioredis: Redis async client"
echo "   - slowapi: Rate limiting"
echo "   - python-dateutil: Date handling"
echo "✅ Requirements.txt updated"
echo ""
echo "📂 Files to copy from artifacts:"
echo "   1. backend/app/external/__init__.py (NEW)"
echo "   2. backend/app/core/rate_limiter.py (NEW)"
echo "   3. backend/app/external/coingecko.py (NEW)"
echo "   4. backend/app/services/external_api.py (NEW)"
echo "   5. backend/app/services/data_sync.py (NEW)"
echo "   6. backend/app/api/api_v1/endpoints/external.py (NEW)"
echo "   7. backend/app/api/api_v1/api.py (UPDATE)"
echo ""
echo "🧪 After copying files, test with:"
echo "   ./temp/test-external-apis.sh"
echo ""
echo "🚀 External API Integration ready!"