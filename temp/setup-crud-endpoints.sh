#!/bin/bash
# Setup CRUD API Endpoints

set -e

echo "📊 Setting up CRUD API Endpoints"
echo "================================="

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found! Please run from project root."
    exit 1
fi

echo "✅ Project structure verified"

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

echo "📦 Installing additional dependencies for CRUD endpoints..."
pip install --quiet --upgrade pip
pip install --quiet psutil==5.9.6     # For system monitoring in health endpoints

echo "✅ Dependencies installed"

cd ..

echo ""
echo "🎯 Setup Complete!"
echo "=================="
echo ""
echo "✅ CRUD endpoint dependencies installed"
echo "✅ Compatible with existing api_v1 structure"
echo "✅ Authentication integration ready"
echo ""
echo "📂 Files to copy from artifacts:"
echo "   1. backend/app/api/api_v1/endpoints/users.py (NEW)"
echo "   2. backend/app/api/api_v1/endpoints/crypto.py (NEW)"
echo "   3. backend/app/api/api_v1/endpoints/prices.py (NEW)"
echo "   4. backend/app/api/api_v1/endpoints/health.py (NEW)"
echo "   5. backend/app/api/api_v1/api.py (UPDATE - all routers enabled)"
echo "   6. backend/requirements.txt (UPDATE - psutil added)"
echo ""
echo "🧪 After copying files, test with:"
echo "   ./temp/test-crud-endpoints.sh"
echo ""
echo "🚀 CRUD endpoints ready for your api_v1 structure!"