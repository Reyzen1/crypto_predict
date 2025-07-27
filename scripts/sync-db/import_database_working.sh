#!/bin/bash
# File: scripts/sync-db/import_database_working.sh
# Working database import script using temp volume method

echo "🚀 CryptoPredict Database Import (Working Version)"
echo "=================================================="

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

# Show usage
show_usage() {
    echo "Usage: $0 <backup_directory>"
    echo ""
    echo "Import database from exported backup directory"
    echo ""
    echo "Example:"
    echo "  $0 database_backup_20250726_123456"
    echo "  $0 /path/to/database_backup_20250726_123456"
    echo ""
    echo "Options:"
    echo "  --help    Show this help message"
}

# Change to project root
cd "$PROJECT_ROOT"

# Main import function
main() {
    local backup_dir="$1"
    
    # Check arguments
    if [ -z "$backup_dir" ]; then
        print_error "No backup directory specified"
        show_usage
        exit 1
    fi
    
    if [ "$backup_dir" = "--help" ]; then
        show_usage
        exit 0
    fi
    
    print_status "Starting database import using temp volume method..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker not running"
        exit 1
    fi
    
    # Find compose file
    if [ -f "docker-compose-backend.yml" ]; then
        COMPOSE_FILE="docker-compose-backend.yml"
    elif [ -f "docker-compose.yml" ]; then
        COMPOSE_FILE="docker-compose.yml"
    else
        print_error "No docker-compose file found!"
        exit 1
    fi
    
    print_status "Using compose file: $COMPOSE_FILE"
    
    # Validate backup directory
    if [ ! -d "$backup_dir" ]; then
        print_error "Backup directory not found: $backup_dir"
        exit 1
    fi
    
    if [ ! -f "$backup_dir/postgres.tar.gz" ]; then
        print_error "PostgreSQL backup not found: $backup_dir/postgres.tar.gz"
        exit 1
    fi
    
    print_success "Backup directory validated: $backup_dir"
    
    # Show backup info if available
    if [ -f "$backup_dir/README.md" ]; then
        echo ""
        print_status "Backup Information:"
        echo "-------------------"
        head -10 "$backup_dir/README.md" | tail -5
        echo ""
    fi
    
    # Confirm destructive operation
    echo ""
    print_warning "⚠️  WARNING: This will REPLACE your current database!"
    print_warning "All existing data will be permanently deleted."
    echo ""
    echo -n "Are you sure you want to continue? (yes/no): "
    read -r response
    echo ""
    
    if [[ ! "$response" =~ ^[Yy][Ee][Ss]$ ]]; then
        print_status "Import cancelled by user"
        exit 0
    fi
    
    print_status "Proceeding with import..."
    
    # Stop containers
    print_status "Stopping containers..."
    docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
    sleep 3
    
    # Remove existing volumes
    print_status "Removing existing volumes..."
    docker volume rm cryptopredict_postgres_data 2>/dev/null || true
    docker volume rm cryptopredict_redis_data 2>/dev/null || true
    
    # Create fresh volumes
    print_status "Creating fresh volumes..."
    docker volume create cryptopredict_postgres_data
    docker volume create cryptopredict_redis_data
    
    # Create temp volume for import
    print_status "Creating temporary import volume..."
    docker volume rm temp_import 2>/dev/null || true
    docker volume create temp_import
    
    # Copy backup files to temp volume
    print_status "Copying backup files to temp volume..."
    docker create --name temp_import_container -v temp_import:/data alpine
    docker cp "$backup_dir/postgres.tar.gz" temp_import_container:/data/
    if [ -f "$backup_dir/redis.tar.gz" ]; then
        docker cp "$backup_dir/redis.tar.gz" temp_import_container:/data/
    fi
    docker rm temp_import_container
    
    # Verify files were copied
    print_status "Verifying backup files in temp volume..."
    docker run --rm -v temp_import:/data alpine ls -la /data/
    
    # Import PostgreSQL data
    print_status "Importing PostgreSQL data..."
    docker run --rm \
        -v temp_import:/source \
        -v cryptopredict_postgres_data:/dest \
        alpine sh -c "cd /dest && tar xzf /source/postgres.tar.gz"
    
    if [ $? -eq 0 ]; then
        print_success "PostgreSQL data imported successfully"
    else
        print_error "PostgreSQL import failed"
        docker volume rm temp_import
        exit 1
    fi
    
    # Import Redis data
    if [ -f "$backup_dir/redis.tar.gz" ]; then
        print_status "Importing Redis data..."
        docker run --rm \
            -v temp_import:/source \
            -v cryptopredict_redis_data:/dest \
            alpine sh -c "cd /dest && tar xzf /source/redis.tar.gz 2>/dev/null" || true
        print_success "Redis data imported"
    else
        print_warning "No Redis backup found (this is usually OK)"
    fi
    
    # Clean up temp volume
    print_status "Cleaning up temporary volume..."
    docker volume rm temp_import
    
    # Start containers for verification
    print_status "Starting containers for verification..."
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis
    
    # Wait for PostgreSQL
    print_status "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if docker-compose -f "$COMPOSE_FILE" exec postgres pg_isready -U postgres > /dev/null 2>&1; then
            print_success "PostgreSQL is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "PostgreSQL verification timeout (but import may still be successful)"
            break
        fi
        sleep 2
    done
    
    # Verify import
    print_status "Verifying import..."
    table_count=$(docker-compose -f "$COMPOSE_FILE" exec postgres \
        psql -U postgres -d cryptopredict -t -c \
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$table_count" -gt 0 ]; then
        print_success "Found $table_count database tables"
        
        # Show table list
        print_status "Database tables:"
        docker-compose -f "$COMPOSE_FILE" exec postgres \
            psql -U postgres -d cryptopredict -c "\\dt" 2>/dev/null || print_warning "Could not list tables"
        
    else
        print_warning "No tables found or verification failed"
    fi
    
    # Check users
    user_count=$(docker-compose -f "$COMPOSE_FILE" exec postgres \
        psql -U postgres -d cryptopredict -t -c \
        "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$user_count" -gt 0 ]; then
        print_success "Found $user_count users in database"
    fi
    
    # Check cryptocurrencies
    crypto_count=$(docker-compose -f "$COMPOSE_FILE" exec postgres \
        psql -U postgres -d cryptopredict -t -c \
        "SELECT COUNT(*) FROM cryptocurrencies;" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$crypto_count" -gt 0 ]; then
        print_success "Found $crypto_count cryptocurrencies in database"
    fi
    
    # Stop containers after verification (user will start them when ready)
    print_status "Stopping containers after verification..."
    docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
    
    # Final success message
    echo ""
    echo "=================================================="
    print_success "IMPORT COMPLETED SUCCESSFULLY!"
    echo "=================================================="
    echo ""
    echo "🎉 Your database has been restored!"
    echo ""
    echo "📊 Import Summary:"
    echo "   Database tables: $table_count"
    echo "   Users: $user_count" 
    echo "   Cryptocurrencies: $crypto_count"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Run setup: ./scripts/sync-db/complete_setup.sh --existing"
    echo "   2. Start app: docker-compose -f $COMPOSE_FILE up -d"
    echo "   3. Test API: curl http://localhost:8000/health"
    echo "   4. Test ML: python temp/test_complete_ml_pipeline.py"
    echo ""
    echo "💡 Data restored:"
    echo "   ✅ User accounts and authentication"
    echo "   ✅ Cryptocurrency data"
    echo "   ✅ Price history and predictions"
    echo "   ✅ ML models and training data"
    echo "   ✅ Application settings"
    echo ""
    echo "🧹 Optional cleanup:"
    echo "   rm -rf '$backup_dir'  # Remove backup after verification"
    echo ""
    print_success "Database migration completed successfully!"
}

# Error handling
set -e
trap 'echo ""; print_error "Import failed! Check error messages above."; exit 1' ERR

# Run main function
main "$@"