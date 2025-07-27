#!/bin/bash
# File: scripts/sync-db/complete_setup.sh
# Complete setup script for future database migrations

echo "🚀 CryptoPredict Complete Setup"
echo "==============================="

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
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

# Change to project root
cd "$PROJECT_ROOT"

# Find compose file
find_compose_file() {
    if [ -f "docker-compose-backend.yml" ]; then
        COMPOSE_FILE="docker-compose-backend.yml"
    elif [ -f "docker-compose.yml" ]; then
        COMPOSE_FILE="docker-compose.yml"
    else
        print_error "No docker-compose file found!"
        exit 1
    fi
    print_status "Using: $COMPOSE_FILE"
}

# Check if this is a fresh setup or existing

# Check for development mode
check_dev_mode() {
    if [ -f "backend/.dev_mode_no_alembic" ]; then
        echo "development"
    else
        echo "production"
    fi
}

check_setup_type() {
    if docker-compose -f "$COMPOSE_FILE" exec postgres psql -U postgres -d cryptopredict -c "SELECT 1 FROM alembic_version LIMIT 1;" 2>/dev/null | grep -q "1"; then
        echo "existing"
    else
        echo "fresh"
    fi
}

# Fresh setup
fresh_setup() {
    print_status "Fresh setup detected"
    
    # Start containers
    print_status "Starting containers..."
    docker-compose -f "$COMPOSE_FILE" up -d
    sleep 15
    
    # Wait for PostgreSQL
    print_status "Waiting for PostgreSQL..."
    for i in {1..30}; do
        if docker-compose -f "$COMPOSE_FILE" exec postgres pg_isready -U postgres > /dev/null 2>&1; then
            print_success "PostgreSQL is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "PostgreSQL failed to start"
            exit 1
        fi
        sleep 2
    done
    
    # Run migrations
    print_status "Running migrations..."
    cd backend
    if alembic upgrade head; then
        print_success "Migrations applied"
    else
        print_error "Migration failed"
        exit 1
    fi
    cd ..
    
    # Create seed data
    print_status "Creating seed data..."
    if python scripts/sync-db/seed_data.py; then
        print_success "Seed data created"
    else
        print_warning "Seed data creation had issues"
    fi
    
    print_success "Fresh setup completed!"
}

# Existing setup migration
existing_setup() {
    print_status "Existing setup detected"
    
    # Ensure containers are running
    print_status "Ensuring containers are running..."
    docker-compose -f "$COMPOSE_FILE" up -d
    sleep 5
    
    # Check for migration updates
    print_status "Checking for migration updates..."
    cd backend
    
    
    # Check for development mode
    dev_mode=$(check_dev_mode)
    if [ "$dev_mode" = "development" ]; then
        print_status "Development mode detected - skipping Alembic"
        print_success "Development mode uses direct model creation"
    else
        # Original Alembic logic here
        # Check current vs head
    current=$(alembic current 2>/dev/null | tail -1 | awk '{print $1}')
    heads=$(alembic heads --resolve-dependencies 2>/dev/null | wc -l)
    
    if [ -z "$current" ] || [ "$heads" -gt 1 ]; then
        print_warning "Database needs migration updates"
        
        # Handle multiple heads if present
        if [ "$heads" -gt 1 ]; then
            print_status "Merging multiple heads..."
            alembic merge heads -m "merge conflicting heads" || true
        fi
        
        # Apply migrations
        if alembic upgrade head; then
            print_success "Migrations applied"
        else
            print_warning "Migration had issues, continuing..."
        fi
    else
        print_success "Database is up to date"
    fi
    
    cd ..
    
    # Check for missing seed data
    print_status "Checking seed data..."
    python scripts/sync-db/seed_data.py
}

# Verify setup
verify_setup() {
    print_status "Verifying setup..."
    
    # Test database connection
    if docker-compose -f "$COMPOSE_FILE" exec postgres pg_isready -U postgres > /dev/null 2>&1; then
        print_success "Database connection OK"
    else
        print_error "Database connection failed"
        return 1
    fi
    
    # Test required tables
    tables=("users" "cryptocurrencies" "price_data" "predictions" "alembic_version")
    for table in "${tables[@]}"; do
        if docker-compose -f "$COMPOSE_FILE" exec postgres psql -U postgres -d cryptopredict -c "SELECT 1 FROM information_schema.tables WHERE table_name='$table';" 2>/dev/null | grep -q "1"; then
            print_success "Table $table exists"
        else
            print_warning "Table $table not found"
        fi
    done
    
    # Test Alembic status
    cd backend
    if alembic current > /dev/null 2>&1; then
        print_success "Alembic is properly configured"
    else
        print_warning "Alembic needs attention"
    fi
    cd ..
    
    print_success "Verification completed"
}

# Show usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --fresh     Force fresh setup (WARNING: destroys existing data)"
    echo "  --existing  Force existing setup migration"
    echo "  --verify    Only run verification"
    echo "  --help      Show this help message"
    echo ""
    echo "Default: Auto-detect setup type"
}

# Main function
main() {
    local force_type=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --fresh)
                force_type="fresh"
                shift
                ;;
            --existing)
                force_type="existing"
                shift
                ;;
            --verify)
                find_compose_file
                verify_setup
                exit 0
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Check if running from correct directory
    if [ ! -f "docker-compose-backend.yml" ] && [ ! -f "docker-compose.yml" ]; then
        print_error "Please run from project root directory"
        print_error "Current directory: $(pwd)"
        exit 1
    fi
    
    find_compose_file
    
    # Determine setup type
    if [ -n "$force_type" ]; then
        setup_type="$force_type"
    else
        setup_type=$(check_setup_type)
    fi
    
    print_status "Setup type: $setup_type"
    
    case $setup_type in
        "fresh")
            if [ "$force_type" = "fresh" ]; then
                print_warning "⚠️  DESTRUCTIVE OPERATION: This will destroy existing data!"
                echo -n "Continue? (yes/no): "
                read -r response
                if [[ ! "$response" =~ ^[Yy][Ee][Ss]$ ]]; then
                    print_status "Cancelled by user"
                    exit 0
                fi
                # Clean slate
                docker-compose -f "$COMPOSE_FILE" down -v 2>/dev/null || true
            fi
            fresh_setup
            ;;
        "existing")
            existing_setup
            ;;
        *)
            print_error "Cannot determine setup type"
            exit 1
            ;;
    esac
    
    # Verify everything
    verify_setup
    
    echo ""
    print_success "Setup completed successfully!"
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Start development: docker-compose -f $COMPOSE_FILE up -d"
    echo "   2. Test API: curl http://localhost:8000/health"
    echo "   3. Run ML tests: python temp/test_complete_ml_pipeline.py"
    echo ""
    echo "📋 For future use:"
    echo "   • Regular migration: ./scripts/sync-db/complete_setup.sh"
    echo "   • Fresh start: ./scripts/sync-db/complete_setup.sh --fresh"
    echo "   • Verify only: ./scripts/sync-db/complete_setup.sh --verify"
}

main "$@"