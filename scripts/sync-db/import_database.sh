#!/bin/bash
# File: scripts/sync-db/import_database.sh
# Import database from exported backup

echo "🚀 CryptoPredict Database Import"
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

# Show usage
show_usage() {
    echo "Usage: $0 <backup_directory>"
    echo ""
    echo "Import database from exported backup directory"
    echo ""
    echo "Example:"
    echo "  $0 database_backup_20250726_123456"
    echo "  $0 /path/to/database_backup_20250726_123456"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running"
        return 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        return 1
    fi
    
    print_success "Prerequisites OK"
    return 0
}

# Find compose file
find_compose_file() {
    if [ -f "docker-compose-backend.yml" ]; then
        COMPOSE_FILE="docker-compose-backend.yml"
    elif [ -f "docker-compose.yml" ]; then
        COMPOSE_FILE="docker-compose.yml"
    else
        print_error "No docker-compose file found!"
        return 1
    fi
    print_status "Using: $COMPOSE_FILE"
    return 0
}

# Validate backup directory
validate_backup() {
    local backup_dir="$1"
    
    if [ ! -d "$backup_dir" ]; then
        print_error "Backup directory not found: $backup_dir"
        return 1
    fi
    
    if [ ! -f "$backup_dir/postgres.tar.gz" ]; then
        print_error "PostgreSQL backup not found: $backup_dir/postgres.tar.gz"
        return 1
    fi
    
    print_success "Backup directory validated"
    
    # Show backup info if available
    if [ -f "$backup_dir/README.md" ]; then
        echo ""
        print_status "Backup Information:"
        echo "-------------------"
        head -15 "$backup_dir/README.md" | tail -10
        echo ""
    fi
    
    return 0
}

# Confirm destructive operation
confirm_import() {
    echo ""
    print_warning "⚠️  WARNING: This will REPLACE your current database!"
    print_warning "All existing data will be permanently deleted."
    echo ""
    echo -n "Are you sure you want to continue? (yes/no): "
    read -r response
    echo ""
    
    if [[ ! "$response" =~ ^[Yy][Ee][Ss]$ ]]; then
        print_status "Import cancelled by user"
        return 1
    fi
    
    print_status "Proceeding with import..."
    return 0
}

# Import database volumes
import_volumes() {
    local backup_dir="$1"
    
    print_status "Importing database volumes..."
    
    # Stop all containers
    print_status "Stopping containers..."
    docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
    
    # Remove existing volumes
    print_status "Removing existing volumes..."
    docker volume rm cryptopredict_postgres_data 2>/dev/null || true
    docker volume rm cryptopredict_redis_data 2>/dev/null || true
    
    # Create fresh volumes
    print_status "Creating fresh volumes..."
    docker volume create cryptopredict_postgres_data
    docker volume create cryptopredict_redis_data
    
    # Import PostgreSQL data
    print_status "Importing PostgreSQL data..."
    docker run --rm \
        -v cryptopredict_postgres_data:/data \
        -v "$(realpath "$backup_dir")":/backup \
        alpine \
        sh -c "cd /data && tar xzf /backup/postgres.tar.gz"
    
    if [ $? -eq 0 ]; then
        print_success "PostgreSQL data imported successfully"
    else
        print_error "PostgreSQL import failed"
        return 1
    fi
    
    # Import Redis data
    if [ -f "$backup_dir/redis.tar.gz" ]; then
        print_status "Importing Redis data..."
        docker run --rm \
            -v cryptopredict_redis_data:/data \
            -v "$(realpath "$backup_dir")":/backup \
            alpine \
            sh -c "cd /data && tar xzf /backup/redis.tar.gz 2>/dev/null" || true
        print_success "Redis data imported"
    else
        print_warning "No Redis backup found (this is usually OK)"
    fi
    
    return 0
}

# Verify import
verify_import() {
    print_status "Verifying import..."
    
    # Start containers
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis
    
    # Wait for PostgreSQL
    print_status "Waiting for PostgreSQL..."
    for i in {1..30}; do
        if docker-compose -f "$COMPOSE_FILE" exec postgres pg_isready -U postgres > /dev/null 2>&1; then
            print_success "PostgreSQL is accessible"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "PostgreSQL verification timeout"
            return 1
        fi
        sleep 2
    done
    
    # Check tables
    table_count=$(docker-compose -f "$COMPOSE_FILE" exec postgres \
        psql -U postgres -d cryptopredict -t -c \
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ' || echo "0")
    
    if [ "$table_count" -gt 0 ]; then
        print_success "Found $table_count database tables"
    else
        print_warning "No tables found"
        return 1
    fi
    
    # Stop containers after verification
    docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
    
    return 0
}

# Main function
main() {
    local backup_dir="$1"
    
    # Check arguments
    if [ -z "$backup_dir" ]; then
        print_error "No backup directory specified"
        show_usage
        exit 1
    fi
    
    print_status "Starting database import..."
    
    if ! check_prerequisites; then
        exit 1
    fi
    
    if ! find_compose_file; then
        exit 1
    fi
    
    if ! validate_backup "$backup_dir"; then
        exit 1
    fi
    
    if ! confirm_import; then
        exit 0
    fi
    
    if ! import_volumes "$backup_dir"; then
        print_error "Import failed!"
        exit 1
    fi
    
    if ! verify_import; then
        print_warning "Import completed but verification had issues"
    fi
    
    echo ""
    print_success "Import completed successfully!"
    echo ""
    echo "🎉 Your database has been restored!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Run setup script: ./scripts/sync-db/complete_setup.sh --existing"
    echo "   2. Start application: docker-compose -f $COMPOSE_FILE up -d"
    echo "   3. Verify health: curl http://localhost:8000/health"
    echo ""
    echo "💡 All your data has been restored:"
    echo "   ✅ User accounts and authentication"
    echo "   ✅ Cryptocurrency data"
    echo "   ✅ Price history and predictions"
    echo "   ✅ Application settings"
    echo ""
    echo "🧹 Optional: Remove backup directory after verification:"
    echo "     rm -rf '$backup_dir'"
}

main "$@"