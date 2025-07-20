# File: ./temp/install-psutil.sh
# Install psutil for system monitoring

#!/bin/bash

set -e

echo "📦 Installing PSUtil"
echo "==================="

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

echo "📦 Installing psutil for system monitoring..."
pip install --no-cache-dir psutil==5.9.6

echo "📄 Updating requirements.txt..."
pip freeze > requirements.txt

echo ""
echo "✅ PSUtil installed successfully!"
echo "================================="
echo ""
echo "📦 psutil is used for:"
echo "  - System monitoring in health endpoints"
echo "  - CPU and memory usage tracking"
echo "  - Process monitoring"
echo ""
echo "🧪 Now test again with:"
echo "   ./temp/final-external-test.sh"

cd ..