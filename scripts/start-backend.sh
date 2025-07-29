# File: temp/start-backend-from-root.sh
# Script to start backend from root directory
# This fixes the ModuleNotFoundError: No module named 'app' issue

#!/bin/bash

echo "🚀 CryptoPredict Backend Startup (From Root)"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in project root
if [ ! -d "backend" ]; then
    print_error "Backend directory not found! Please run from project root."
    exit 1
fi

# Check if backend/app directory exists
if [ ! -d "backend/app" ]; then
    print_error "backend/app directory not found!"
    print_warning "Creating missing backend/app structure..."
    
    # Create basic app structure
    mkdir -p backend/app
    touch backend/app/__init__.py
    
    if [ ! -f "backend/app/main.py" ]; then
        print_error "backend/app/main.py not found!"
        print_warning "Please ensure all backend files are present."
        exit 1
    fi
fi

# Change to backend directory
print_status "Changing to backend directory..."
cd backend

# Check for virtual environment
if [ -f "venv/Scripts/activate" ]; then
    print_status "Activating virtual environment (Windows)..."
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    print_status "Activating virtual environment (Linux/Mac)..."
    source venv/bin/activate
else
    print_warning "Virtual environment not found!"
    print_status "Attempting to run with system Python..."
fi

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    print_error "uvicorn not found! Installing..."
    pip install uvicorn fastapi
fi

# Set environment variables
print_status "Setting environment variables..."
export DATABASE_URL="postgresql://postgres:postgres123@localhost:5432/cryptopredict"
export REDIS_URL="redis://localhost:6379/0"
export ENVIRONMENT="development"
export DEBUG="true"
export SECRET_KEY="dev-secret-key-change-in-production"
export JWT_SECRET_KEY="dev-jwt-secret-key-change-in-production"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES="30"
export BACKEND_CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

# Start database containers if not running
print_status "Checking database containers..."
if ! docker ps | grep -q cryptopredict_postgres; then
    print_warning "Database containers not running. Starting them..."
    cd ..
    docker-compose -f docker-compose-backend.yml up -d postgres redis
    cd backend
    print_status "Waiting for databases to be ready..."
    sleep 10
fi

print_success "Environment setup complete!"
print_status "Backend will start at: http://localhost:8000"
print_status "API Docs available at: http://localhost:8000/docs"
print_status "Press Ctrl+C to stop"
echo ""

# Start FastAPI from backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000