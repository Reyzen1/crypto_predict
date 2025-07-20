#!/bin/bash
# Setup Authentication System using existing api_v1 structure

set -e

echo "🔐 Setting up Authentication System (api_v1 compatible)"
echo "====================================================="

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found! Please run from project root."
    exit 1
fi

echo "✅ Project structure verified"

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p backend/app/services
mkdir -p backend/app/api/api_v1/endpoints

echo "✅ Directories created"

# Install dependencies
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

echo "📦 Installing authentication dependencies..."
pip install --quiet --upgrade pip
pip install --quiet PyJWT==2.8.0
pip install --quiet "passlib[bcrypt]==1.7.4"
pip install --quiet "python-jose[cryptography]==3.3.0"
pip install --quiet pydantic-settings==2.1.0

echo "✅ Dependencies installed"

cd ..

echo ""
echo "🎯 Setup Complete!"
echo "=================="
echo ""
echo "✅ Directories ready"
echo "✅ Dependencies installed" 
echo "✅ Compatible with your existing api_v1 structure"
echo ""
echo "📂 Files to copy from artifacts:"
echo "   1. backend/app/core/security.py (NEW)"
echo "   2. backend/app/core/config.py (NEW)" 
echo "   3. backend/app/core/deps.py (NEW)"
echo "   4. backend/app/services/auth.py (NEW)"
echo "   5. backend/app/api/api_v1/endpoints/auth.py (NEW)"
echo "   6. backend/app/api/api_v1/api.py (UPDATE - auth router enabled)"
echo "   7. backend/app/main.py (UPDATE - merged with your code)"
echo "   8. backend/requirements.txt (UPDATE - merged with your ML deps)"
echo "   9. backend/app/services/__init__.py (NEW)"
echo "   10. backend/app/api/api_v1/endpoints/__init__.py (NEW)"
echo ""
echo "🧪 After copying files, test with:"
echo "   ./temp/test-auth-api-v1.sh"
echo ""
echo "🚀 Authentication system ready for your api_v1 structure!"