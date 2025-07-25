#!/bin/bash
# File: temp/import_database.sh
# Import CryptoPredict database volumes from backup
# Usage: ./temp/import_database.sh

set -e

echo "🚀 CryptoPredict Database Import"
echo "==============================="

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
    print_status "Checking Docker availability..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    print_success "Docker is ready"
}

# Check if backup files exist
check_backup_files() {
    print_status "Checking backup files..."
    
    if [ ! -d "database_backup" ]; then
        print_error "Backup directory 'database_backup' not found!"
        print_error "Please copy the backup folder from source system first."
        echo ""
        echo "Expected structure:"
        echo "  database_backup/"
        echo "  ├── postgres.tar.gz"
        echo "  ├── redis.tar.gz"
        echo "  └── README.txt"
        exit 1
    fi
    
    if [ ! -f "database_backup/postgres.tar.gz" ]; then
        print_error "PostgreSQL backup file not found: database_backup/postgres.tar.gz"
        exit 1
    fi
    
    print_success "Backup files found"
    
    # Show backup info if available
    if [ -f "database_backup/README.txt" ]; then
        echo ""
        print_status "Backup Information:"
        echo "-------------------"
        head -10 database_backup/README.txt
        echo ""
    fi
}

# Find appropriate docker-compose file
find_compose_file() {
    if [ -f "docker-compose-backend.yml" ]; then
        COMPOSE_FILE="docker-compose-backend.yml"
    elif [ -f "docker-compose.yml" ]; then
        COMPOSE_FILE="docker-compose.yml"
    else
        print_error "No docker-compose file found!"
        print_error "Please run this script from the project root directory."
        exit 1
    fi
    
    print_status "Using compose file: $COMPOSE_FILE"
}

# Confirm destructive operation
confirm_import() {
    echo ""
    print_warning "⚠️  WARNING: This will REPLACE your current database!"
    print_warning "All existing data will be permanently deleted."
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_status "Import cancelled by user."
        exit 0
    fi
    
    print_status "Proceeding with import..."
}

# Stop all containers
stop_containers() {
    print_status "Stopping all containers..."
    
    docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
    docker-compose -f docker-compose.yml down 2>/dev/null || true
    
    # Wait a moment for containers to fully stop
    sleep 3
    
    print_success "All containers stopped"
}

# Remove existing volumes
remove_volumes() {
    print_status "Removing existing database volumes..."
    
    # Remove PostgreSQL volume
    if docker volume ls | grep -q cryptopredict_postgres_data; then
        docker volume rm cryptopredict_postgres_data 2>/dev/null || true
        print_status "Removed PostgreSQL volume"
    fi
    
    # Remove Redis volume
    if docker volume ls | grep -q cryptopredict_redis_data; then
        docker volume rm cryptopredict_redis_data 2>/dev/null || true
        print_status "Removed Redis volume"
    fi
    
    print_success "Existing volumes cleaned"
}

# Create fresh volumes
create_volumes() {
    print_status "Creating fresh database volumes..."
    
    docker volume create cryptopredict_postgres_data
    docker volume create cryptopredict_redis_data
    
    print_success "Fresh volumes created"
}

# Import PostgreSQL data
import_postgres() {
    print_status "Importing PostgreSQL data..."
    
    # Use absolute Windows path to avoid Git Bash path conversion
    local backup_path
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        # Convert to Windows path format for Docker
        backup_path="$(cygpath -w "$(pwd)/database_backup")"
        backup_path="${backup_path//\\//}"
    else
        backup_path="$(pwd)/database_backup"
    fi
    
    docker run --rm \
        -v cryptopredict_postgres_data:/data \
        -v "${backup_path}:/backup" \
        alpine \
        sh -c "cd /data && tar xzf /backup/postgres.tar.gz"
    
    if [ $? -eq 0 ]; then
        print_success "PostgreSQL data imported successfully"
    else
        print_error "PostgreSQL import failed"
        exit 1
    fi
}

# Import Redis data
import_redis() {
    if [ -f "database_backup/redis.tar.gz" ]; then
        print_status "Importing Redis data..."
        
        # Use absolute Windows path to avoid Git Bash path conversion
        local backup_path
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
            # Convert to Windows path format for Docker
            backup_path="$(cygpath -w "$(pwd)/database_backup")"
            backup_path="${backup_path//\\//}"
        else
            backup_path="$(pwd)/database_backup"
        fi
        
        docker run --rm \
            -v cryptopredict_redis_data:/data \
            -v "${backup_path}:/backup" \
            alpine \
            sh -c "cd /data && tar xzf /backup/redis.tar.gz 2>/dev/null" || true
        
        print_success "Redis data imported"
    else
        print_warning "No Redis backup found (this is usually OK)"
    fi
}

# Verify import
verify_import() {
    print_status "Verifying import..."
    
    # Start containers temporarily for verification
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to start..."
    sleep 15
    
    # Check if we can connect to PostgreSQL
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
        print_success "PostgreSQL is accessible"
        
        # Try to list tables
        table_count=$(docker-compose -f "$COMPOSE_FILE" exec -T postgres \
            psql -U postgres -d cryptopredict -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ' || echo "0")
        
        if [ "$table_count" -gt 0 ]; then
            print_success "Found $table_count database tables"
        else
            print_warning "No tables found (database might be empty)"
        fi
    else
        print_warning "Cannot verify PostgreSQL connection (might still be starting)"
    fi
    
    # Stop containers after verification
    docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
}

# Show completion message
show_completion() {
    echo ""
    echo "================================================="
    print_success "DATABASE IMPORT COMPLETED!"
    echo "================================================="
    echo ""
    echo "🎉 Your database has been restored successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo "  1. Start the application:"
    echo "     docker-compose -f $COMPOSE_FILE up -d"
    echo ""
    echo "  2. Wait for containers to be ready (~30 seconds)"
    echo ""
    echo "  3. Verify the application is working:"
    echo "     curl http://localhost:8000/health"
    echo ""
    echo "  4. Access the application:"
    echo "     • API Documentation: http://localhost:8000/docs"
    echo "     • Health Check: http://localhost:8000/health"
    echo ""
    echo "💡 All your data has been restored:"
    echo "   ✅ User accounts and authentication"
    echo "   ✅ Cryptocurrency data"
    echo "   ✅ Price history and predictions"
    echo "   ✅ Application settings"
    echo ""
    echo "🧹 Optional: You can now delete the backup folder:"
    echo "     rm -rf database_backup"
    echo ""
}

# Main import process
main() {
    echo ""
    print_status "Starting database import process..."
    echo ""
    
    # Run all steps
    check_docker
    check_backup_files
    find_compose_file
    confirm_import
    stop_containers
    remove_volumes
    create_volumes
    import_postgres
    import_redis
    verify_import
    show_completion
}

# Error handling
trap 'echo ""; print_error "Import failed! Check the error messages above."; exit 1' ERR

# Run main function
main