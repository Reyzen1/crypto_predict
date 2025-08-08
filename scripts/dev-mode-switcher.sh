#!/bin/bash
# File: dev-mode-switcher.sh
# Simple development environment switcher (Local ↔ Docker)
# Usage: ./dev-mode-switcher.sh [local|docker|status]

ACTION=${1:-status}

echo "🔄 CryptoPredict Development Mode Switcher"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
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

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

show_status() {
    echo ""
    echo "📊 Current Environment Status"
    echo "============================="
    
    if [ -f ".env" ]; then
        print_success ".env file exists"
        
        # Check database URL
        DB_URL=$(grep "DATABASE_URL" .env | cut -d'=' -f2)
        if [[ "$DB_URL" == *"localhost:5433"* ]]; then
            echo "🔹 Mode: LOCAL (PostgreSQL localhost:5433)"
        elif [[ "$DB_URL" == *"postgres:5432"* ]]; then
            echo "🔹 Mode: DOCKER (PostgreSQL postgres:5432)"
        else
            echo "🔹 Mode: UNKNOWN"
        fi
        
        # Check Redis
        REDIS_URL=$(grep "REDIS_URL" .env | cut -d'=' -f2)
        if [[ "$REDIS_URL" == *"127.0.0.1:6379"* ]]; then
            echo "🔹 Cache: Local Redis"
        elif [[ "$REDIS_URL" == *"redis:6379"* ]]; then
            echo "🔹 Cache: Docker Redis"
        fi
        
        # Check environment
        ENV_VAR=$(grep "ENVIRONMENT" .env | cut -d'=' -f2)
        echo "🔹 Environment: $ENV_VAR"
        
    else
        print_warning ".env file not found"
    fi
    
    # Check backups
    if [ -f ".env.local.backup" ]; then
        echo "💾 Local backup: Available"
    fi
    if [ -f ".env.docker.backup" ]; then
        echo "💾 Docker backup: Available"
    fi
    
    # Check services
    if command_exists pg_isready && pg_isready -h localhost -p 5433 -q; then
        echo "🗄️ Local PostgreSQL: Running (port 5433)"
    else
        echo "🗄️ Local PostgreSQL: Not accessible"
    fi
    
    if command_exists redis-cli && redis-cli ping >/dev/null 2>&1; then
        echo "📦 Local Redis: Running"
    else
        echo "📦 Local Redis: Not accessible"
    fi
    
    if command_exists docker-compose; then
        if docker-compose ps 2>/dev/null | grep -q "Up"; then
            echo "🐳 Docker containers: Running"
        else
            echo "🐳 Docker containers: Stopped"
        fi
    fi
    
    echo ""
}

switch_to_local() {
    echo "🏠 Switching to LOCAL development mode..."
    
    # Step 1: Stop Docker containers
    print_info "Stopping Docker containers..."
    if command_exists docker-compose; then
        docker-compose -f docker-compose-backend.yml down 2>/dev/null || true
        docker-compose down 2>/dev/null || true
        print_success "Docker containers stopped"
    fi
    
    # Step 2: Backup current .env if it's Docker config
    if [ -f ".env" ]; then
        DB_URL=$(grep "DATABASE_URL" .env | cut -d'=' -f2)
        if [[ "$DB_URL" == *"postgres:5432"* ]] && [ ! -f ".env.docker.backup" ]; then
            cp .env .env.docker.backup
            print_info "Docker config backed up: .env.docker.backup"
        fi
    fi
    
    # Step 3: Apply local configuration
    print_info "Configuring for local development..."
    
    if [ -f ".env.local.backup" ]; then
        # Restore from local backup
        cp .env.local.backup .env
        print_success "Restored local configuration from backup"
    else
        # Update current .env for local
        temp_env=$(mktemp)
        
        while IFS= read -r line; do
            if [[ $line =~ ^DATABASE_URL= ]]; then
                echo "DATABASE_URL=postgresql://postgres:admin123@localhost:5433/cryptopredict" >> "$temp_env"
            elif [[ $line =~ ^REDIS_URL= ]]; then
                echo "REDIS_URL=redis://127.0.0.1:6379/0" >> "$temp_env"
            elif [[ $line =~ ^CORS_ORIGINS= ]]; then
                echo "CORS_ORIGINS=http://localhost:3000,http://localhost:3000,http://localhost:8000,http://testserver" >> "$temp_env"
            elif [[ $line =~ ^API_URL= ]]; then
                echo "API_URL=http://localhost:8000" >> "$temp_env"
            elif [[ $line =~ ^WS_URL= ]]; then
                echo "WS_URL=ws://localhost:8000" >> "$temp_env"
            elif [[ $line =~ ^ENVIRONMENT= ]]; then
                echo "ENVIRONMENT=development" >> "$temp_env"
            elif [[ $line =~ ^DEBUG= ]]; then
                echo "DEBUG=true" >> "$temp_env"
            else
                echo "$line" >> "$temp_env"
            fi
        done < .env
        
        mv "$temp_env" .env
        print_success "Updated .env for local development"
    fi
    
    # Step 4: Create database if needed
    print_info "Setting up database..."
    PGPASSWORD=admin123 createdb -h localhost -p 5433 -U postgres cryptopredict 2>/dev/null && {
        print_success "Database 'cryptopredict' created"
    } || {
        print_info "Database already exists"
    }
    
    # Step 5: Create/update tables from models (no Alembic)
    print_info "Creating tables from models..."
    cd backend
    python -c "
from app.core.database import engine, Base
from app.models import User, Cryptocurrency, PriceData, Prediction
try:
    Base.metadata.create_all(bind=engine)
    print('✅ Tables created/updated from models')
except Exception as e:
    print(f'❌ Table creation failed: {e}')
" 2>/dev/null || print_warning "Could not create tables (run backend first)"
    cd ..
    
    print_success "Switched to LOCAL mode"
}

switch_to_docker() {
    echo "🐳 Switching to DOCKER development mode..."
    
    # Step 1: Backup current .env if it's local config
    if [ -f ".env" ]; then
        DB_URL=$(grep "DATABASE_URL" .env | cut -d'=' -f2)
        if [[ "$DB_URL" == *"localhost"* ]] && [ ! -f ".env.local.backup" ]; then
            cp .env .env.local.backup
            print_info "Local config backed up: .env.local.backup"
        fi
    fi
    
    # Step 2: Apply Docker configuration
    print_info "Configuring for Docker development..."
    
    if [ -f ".env.docker.backup" ]; then
        # Restore from Docker backup
        cp .env.docker.backup .env
        print_success "Restored Docker configuration from backup"
    else
        # Update current .env for Docker
        temp_env=$(mktemp)
        
        while IFS= read -r line; do
            if [[ $line =~ ^DATABASE_URL= ]]; then
                echo "DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/cryptopredict" >> "$temp_env"
            elif [[ $line =~ ^REDIS_URL= ]]; then
                echo "REDIS_URL=redis://redis:6379/0" >> "$temp_env"
            elif [[ $line =~ ^API_URL= ]]; then
                echo "API_URL=http://localhost:8000" >> "$temp_env"
            elif [[ $line =~ ^WS_URL= ]]; then
                echo "WS_URL=ws://localhost:8000" >> "$temp_env"
            else
                echo "$line" >> "$temp_env"
            fi
        done < .env
        
        mv "$temp_env" .env
        print_success "Updated .env for Docker"
    fi
    
    # Step 3: Start Docker containers
    print_info "Starting Docker containers..."
    if command_exists docker-compose; then
        docker-compose -f docker-compose-backend.yml up -d postgres redis
        
        print_info "Waiting for containers to start..."
        sleep 8
        
        if docker-compose -f docker-compose-backend.yml ps | grep -q "Up"; then
            print_success "Docker containers started"
        else
            print_error "Failed to start containers"
        fi
    else
        print_error "Docker Compose not found"
    fi
    
    print_success "Switched to DOCKER mode"
}

create_startup_scripts() {
    print_info "Creating startup scripts..."
    
    # Backend startup script
    cat > start-backend-local.sh << 'EOF'
#!/bin/bash
# File: start-backend-local.sh
# Start backend development server

echo "🚀 Starting Backend Development Server"
echo "======================================"

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

cd backend

# Activate virtual environment if not active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    if [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
        echo "✅ Virtual environment activated"
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "⚠️  Virtual environment not found"
    fi
fi

echo "Environment: $ENVIRONMENT"
echo "Database: $DATABASE_URL"
echo "Redis: $REDIS_URL"
echo ""
echo "📍 Backend URL: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
EOF

    # Frontend startup script
    cat > start-frontend-local.sh << 'EOF'
#!/bin/bash
# File: start-frontend-local.sh
# Start frontend development server

echo "⚛️ Starting Frontend Development Server"
echo "======================================="

cd frontend

echo "📍 Frontend URL: http://localhost:3000"
echo "🔄 Hot reload enabled"
echo ""

# Start Next.js development server
npm run dev
EOF

    chmod +x start-backend-local.sh
    chmod +x start-frontend-local.sh
    
    print_success "Startup scripts created"
}

# Main logic
case $ACTION in
    "local")
        switch_to_local
        create_startup_scripts
        ;;
    "docker")
        switch_to_docker
        create_startup_scripts
        ;;
    "status")
        show_status
        ;;
    *)
        echo "Usage: $0 [local|docker|status]"
        echo ""
        echo "Commands:"
        echo "  local   - Switch to local development (PostgreSQL 5433, Redis local)"
        echo "  docker  - Switch to Docker development (containers)"
        echo "  status  - Show current development mode"
        echo ""
        exit 1
        ;;
esac

# Show final status
show_status

echo "🎉 Development Environment Ready!"
echo "================================"
echo ""
echo "🚀 Start development servers:"
echo "  Terminal 1: ./start-backend-local.sh"
echo "  Terminal 2: ./start-frontend-local.sh"
echo ""
echo "🌐 URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "💡 Switch modes anytime:"
echo "  ./dev-mode-switcher.sh local   # Local development"
echo "  ./dev-mode-switcher.sh docker  # Docker development"
echo "  ./dev-mode-switcher.sh status  # Check current mode"