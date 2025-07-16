#!/bin/bash
# File: scripts/quick-start.sh
# Quick start script for CryptoPredict MVP development
# Runs backend in Docker, frontend locally

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

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Check if Node.js is installed
check_node() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js and try again."
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm and try again."
        exit 1
    fi
}

# Start backend services only
start_backend() {
    print_status "Starting backend services (PostgreSQL, Redis, FastAPI)..."
    check_docker
    
    # Create directories
    mkdir -p logs backend/logs
    
    # Start services
    docker-compose -f docker-compose-backend.yml up -d --build
    
    print_status "Waiting for services to be ready..."
    sleep 15
    
    # Check if services are ready
    if docker-compose -f docker-compose-backend.yml exec postgres pg_isready -U postgres -d cryptopredict > /dev/null 2>&1; then
        print_success "PostgreSQL is ready"
    else
        print_error "PostgreSQL is not ready"
        return 1
    fi
    
    if docker-compose -f docker-compose-backend.yml exec redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is ready"
    else
        print_error "Redis is not ready"
        return 1
    fi
    
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend API is ready"
    else
        print_warning "Backend API is not ready yet, but starting..."
    fi
    
    print_success "Backend services started successfully!"
}

# Start frontend locally
start_frontend() {
    print_status "Starting frontend locally..."
    check_node
    
    if [ ! -d "frontend" ]; then
        print_error "Frontend directory not found. Please run from project root."
        return 1
    fi
    
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_status "Installing frontend dependencies..."
        npm install
    fi
    
    # Start development server
    print_status "Starting Next.js development server..."
    print_status "Frontend will be available at: http://localhost:3000"
    print_status "Press Ctrl+C to stop"
    
    # Set environment variables
    export NEXT_PUBLIC_API_URL=http://localhost:8000
    
    npm run dev
}

# Stop backend services
stop_backend() {
    print_status "Stopping backend services..."
    docker-compose -f docker-compose-backend.yml down
    print_success "Backend services stopped."
}

# Show logs
show_logs() {
    docker-compose -f docker-compose-backend.yml logs -f
}

# Check status
check_status() {
    print_status "Checking service status..."
    
    # Check PostgreSQL
    if docker-compose -f docker-compose-backend.yml exec postgres pg_isready -U postgres -d cryptopredict > /dev/null 2>&1; then
        print_success "PostgreSQL is ready"
    else
        print_error "PostgreSQL is not ready"
    fi
    
    # Check Redis
    if docker-compose -f docker-compose-backend.yml exec redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is ready"
    else
        print_error "Redis is not ready"
    fi
    
    # Check Backend
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend API is ready at http://localhost:8000"
    else
        print_warning "Backend API is not ready"
    fi
    
    # Check Frontend (if running)
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend is running at http://localhost:3000"
    else
        print_warning "Frontend is not running"
    fi
}

# Show help
show_help() {
    echo "CryptoPredict MVP Quick Start"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start-backend   Start backend services (PostgreSQL, Redis, FastAPI)"
    echo "  start-frontend  Start frontend locally (requires Node.js)"
    echo "  stop-backend    Stop backend services"
    echo "  status          Check service status"
    echo "  logs            Show backend logs"
    echo "  full-start      Start backend then frontend"
    echo "  help            Show this help message"
    echo ""
    echo "Quick Start Guide:"
    echo "  1. ./scripts/quick-start.sh start-backend"
    echo "  2. ./scripts/quick-start.sh start-frontend  (in another terminal)"
    echo ""
    echo "Or use: ./scripts/quick-start.sh full-start"
}

# Full start (backend + frontend)
full_start() {
    start_backend
    if [ $? -eq 0 ]; then
        print_status "Backend started successfully. Now starting frontend..."
        sleep 2
        start_frontend
    else
        print_error "Failed to start backend. Frontend not started."
    fi
}

# Main script logic
case "${1:-help}" in
    start-backend)
        start_backend
        ;;
    start-frontend)
        start_frontend
        ;;
    stop-backend)
        stop_backend
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs
        ;;
    full-start)
        full_start
        ;;
    help|*)
        show_help
        ;;
esac