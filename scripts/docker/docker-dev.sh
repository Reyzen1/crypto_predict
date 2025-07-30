#!/bin/bash
# File: scripts/docker-dev.sh
# Docker management scripts for CryptoPredict MVP development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success ".env file created. Please update it with your configuration."
        else
            print_error ".env.example file not found. Please create .env file manually."
            exit 1
        fi
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p logs backend/logs redis frontend/.next
    print_success "Directories created."
}

# Build and start all services
start_all() {
    print_status "Starting CryptoPredict MVP development environment..."
    check_docker
    check_env
    create_directories
    
    print_status "Building and starting services..."
    docker-compose up -d --build
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    check_services
}

# Start specific services
start_db() {
    print_status "Starting database services..."
    check_docker
    docker-compose up -d postgres redis
    print_success "Database services started."
}

start_backend() {
    print_status "Starting backend service..."
    check_docker
    docker-compose up -d backend
    print_success "Backend service started."
}

start_frontend() {
    print_status "Starting frontend service..."
    check_docker
    docker-compose up -d frontend
    print_success "Frontend service started."
}

# Stop services
stop_all() {
    print_status "Stopping all services..."
    docker-compose down
    print_success "All services stopped."
}

# Stop and remove everything including volumes
reset_all() {
    print_warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Stopping and removing everything..."
        docker-compose down -v --remove-orphans
        docker system prune -f
        print_success "Environment reset complete."
    else
        print_status "Reset cancelled."
    fi
}

# View logs
logs_all() {
    docker-compose logs -f
}

logs_backend() {
    docker-compose logs -f backend
}

logs_frontend() {
    docker-compose logs -f frontend
}

logs_db() {
    docker-compose logs -f postgres redis
}

# Check service status
check_services() {
    print_status "Checking service status..."
    
    # Check PostgreSQL
    if docker-compose exec postgres pg_isready -U postgres -d cryptopredict > /dev/null 2>&1; then
        print_success "PostgreSQL is ready"
    else
        print_error "PostgreSQL is not ready"
    fi
    
    # Check Redis
    if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is ready"
    else
        print_error "Redis is not ready"
    fi
    
    # Check Backend
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend API is ready"
    else
        print_warning "Backend API is not ready yet"
    fi
    
    # Check Frontend
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend is ready"
    else
        print_warning "Frontend is not ready yet"
    fi
}

# Database management
db_shell() {
    print_status "Opening PostgreSQL shell..."
    docker-compose exec postgres psql -U postgres -d cryptopredict
}

redis_shell() {
    print_status "Opening Redis shell..."
    docker-compose exec redis redis-cli
}

# Backup database
backup_db() {
    print_status "Creating database backup..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    docker-compose exec postgres pg_dump -U postgres cryptopredict > "backup_${timestamp}.sql"
    print_success "Database backup created: backup_${timestamp}.sql"
}

# Show help
show_help() {
    echo "CryptoPredict MVP Docker Management"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start          Start all services"
    echo "  start-db       Start database services only"
    echo "  start-backend  Start backend service only"
    echo "  start-frontend Start frontend service only"
    echo "  stop           Stop all services"
    echo "  reset          Stop and remove everything (including volumes)"
    echo "  status         Check service status"
    echo "  logs           View all logs"
    echo "  logs-backend   View backend logs"
    echo "  logs-frontend  View frontend logs"
    echo "  logs-db        View database logs"
    echo "  db-shell       Open PostgreSQL shell"
    echo "  redis-shell    Open Redis shell"
    echo "  backup         Create database backup"
    echo "  help           Show this help message"
    echo ""
    echo "URLs:"
    echo "  Frontend:      http://localhost:3000"
    echo "  Backend API:   http://localhost:8000"
    echo "  API Docs:      http://localhost:8000/docs"
    echo "  PgAdmin:       http://localhost:5050"
    echo "  Redis Commander: http://localhost:8081"
}

# Main script logic
case "${1:-help}" in
    start)
        start_all
        ;;
    start-db)
        start_db
        ;;
    start-backend)
        start_backend
        ;;
    start-frontend)
        start_frontend
        ;;
    stop)
        stop_all
        ;;
    reset)
        reset_all
        ;;
    status)
        check_services
        ;;
    logs)
        logs_all
        ;;
    logs-backend)
        logs_backend
        ;;
    logs-frontend)
        logs_frontend
        ;;
    logs-db)
        logs_db
        ;;
    db-shell)
        db_shell
        ;;
    redis-shell)
        redis_shell
        ;;
    backup)
        backup_db
        ;;
    help|*)
        show_help
        ;;
esac