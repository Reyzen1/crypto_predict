#!/bin/bash
# File: scripts/local-dev.sh
# Local development script - runs everything locally without Docker
# Fastest way to get development environment running

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if Python 3.12 is available
check_python() {
    if command -v python3.12 &> /dev/null; then
        PYTHON_CMD="python3.12"
    elif command -v python3 &> /dev/null; then
        python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
        if [[ "$python_version" == "3.12" ]]; then
            PYTHON_CMD="python3"
        else
            print_warning "Python 3.12 not found, using python3 ($python_version)"
            PYTHON_CMD="python3"
        fi
    elif command -v python &> /dev/null; then
        python_version=$(python --version | cut -d' ' -f2 | cut -d'.' -f1-2)
        if [[ "$python_version" == "3.12" ]]; then
            PYTHON_CMD="python"
        else
            print_warning "Python 3.12 not found, using python ($python_version)"
            PYTHON_CMD="python"
        fi
    else
        print_error "Python not found. Please install Python 3.12"
        exit 1
    fi
    
    print_success "Using Python: $PYTHON_CMD"
}

# Check if Node.js is available
check_node() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js and try again."
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm and try again."
        exit 1
    fi
    
    node_version=$(node --version)
    print_success "Using Node.js: $node_version"
}

# Start databases with Docker (lightweight)
start_databases() {
    print_status "Starting PostgreSQL and Redis with Docker..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker for databases."
        exit 1
    fi
    
    # Start only databases
    docker-compose -f docker-compose-backend.yml up -d postgres redis
    
    print_status "Waiting for databases to be ready..."
    sleep 10
    
    # Check PostgreSQL
    if docker-compose -f docker-compose-backend.yml exec postgres pg_isready -U postgres -d cryptopredict > /dev/null 2>&1; then
        print_success "PostgreSQL is ready"
    else
        print_error "PostgreSQL is not ready"
        return 1
    fi
    
    # Check Redis
    if docker-compose -f docker-compose-backend.yml exec redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is ready"
    else
        print_error "Redis is not ready"
        return 1
    fi
}

# Setup Python backend environment
setup_backend() {
    print_status "Setting up Python backend environment..."
    check_python
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        $PYTHON_CMD -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies with simplified requirements
    print_status "Installing Python dependencies..."
    pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary redis pydantic python-decouple python-multipart httpx aiofiles slowapi
    
    print_success "Backend environment ready!"
    cd ..
}

# Setup frontend environment
setup_frontend() {
    print_status "Setting up frontend environment..."
    check_node
    
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_status "Installing frontend dependencies..."
        npm install
    fi
    
    print_success "Frontend environment ready!"
    cd ..
}

# Start backend locally
start_backend() {
    print_status "Starting FastAPI backend..."
    
    cd backend
    source venv/bin/activate
    
    # Set environment variables
    export DATABASE_URL="postgresql://postgres:postgres123@localhost:5432/cryptopredict"
    export REDIS_URL="redis://localhost:6379/0"
    export ENVIRONMENT="development"
    export DEBUG="true"
    export SECRET_KEY="dev-secret-key"
    export JWT_SECRET_KEY="dev-jwt-secret-key"
    
    # Start FastAPI
    print_status "Backend will be available at: http://localhost:8000"
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Start frontend locally
start_frontend() {
    print_status "Starting Next.js frontend..."
    
    cd frontend
    
    # Set environment variables
    export NEXT_PUBLIC_API_URL="http://localhost:8000"
    
    # Start Next.js
    print_status "Frontend will be available at: http://localhost:3000"
    npm run dev
}

# Stop databases
stop_databases() {
    print_status "Stopping databases..."
    docker-compose -f docker-compose-backend.yml down
    print_success "Databases stopped."
}

# Full setup and start
full_start() {
    start_databases
    setup_backend
    setup_frontend
    
    print_success "Environment setup complete!"
    print_status "To start services:"
    print_status "  Backend:  ./scripts/local-dev.sh start-backend"
    print_status "  Frontend: ./scripts/local-dev.sh start-frontend"
    print_status ""
    print_status "Or use 'tmux' or separate terminals for both"
}

# Show help
show_help() {
    echo "CryptoPredict MVP Local Development"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup           Setup both backend and frontend environments"
    echo "  start-db        Start databases (PostgreSQL, Redis) with Docker"
    echo "  setup-backend   Setup Python backend environment"
    echo "  setup-frontend  Setup Node.js frontend environment"
    echo "  start-backend   Start FastAPI backend locally"
    echo "  start-frontend  Start Next.js frontend locally"
    echo "  stop-db         Stop databases"
    echo "  full-start      Complete setup and instructions"
    echo "  help            Show this help message"
    echo ""
    echo "Quick Start:"
    echo "  1. $0 full-start"
    echo "  2. $0 start-backend   (in terminal 1)"
    echo "  3. $0 start-frontend  (in terminal 2)"
}

# Main script logic
case "${1:-help}" in
    setup)
        setup_backend
        setup_frontend
        ;;
    start-db)
        start_databases
        ;;
    setup-backend)
        setup_backend
        ;;
    setup-frontend)
        setup_frontend
        ;;
    start-backend)
        start_backend
        ;;
    start-frontend)
        start_frontend
        ;;
    stop-db)
        stop_databases
        ;;
    full-start)
        full_start
        ;;
    help|*)
        show_help
        ;;
esac