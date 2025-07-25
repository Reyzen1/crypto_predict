#!/bin/bash
# File: temp/export_database.sh
# Export CryptoPredict database volumes for transfer
# Usage: ./temp/export_database.sh

set -e

echo "🚀 CryptoPredict Database Export"
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

# Create backup directory
setup_backup_dir() {
    print_status "Setting up backup directory..."
    
    if [ -d "database_backup" ]; then
        print_warning "Backup directory already exists. Removing old backup..."
        rm -rf database_backup
    fi
    
    mkdir -p database_backup
    print_success "Backup directory created: database_backup/"
}

# Stop containers for clean backup
stop_containers() {
    print_status "Stopping containers for clean backup..."
    
    docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
    
    print_success "Containers stopped"
}

# Start only database containers
start_database_containers() {
    print_status "Starting database containers..."
    
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis
    
    # Wait for containers to be ready
    print_status "Waiting for containers to be ready..."
    sleep 10
    
    # Check if containers are running
    if ! docker-compose -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
        print_error "PostgreSQL container failed to start"
        exit 1
    fi
    
    if ! docker-compose -f "$COMPOSE_FILE" ps redis | grep -q "Up"; then
        print_warning "Redis container failed to start (continuing anyway)"
    fi
    
    print_success "Database containers are ready"
}

# Export PostgreSQL volume
export_postgres() {
    print_status "Exporting PostgreSQL data..."
    
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
        -v cryptopredict_postgres_data:/data:ro \
        -v "${backup_path}:/backup" \
        alpine \
        sh -c "cd /data && tar czf /backup/postgres.tar.gz ."
    
    if [ $? -eq 0 ]; then
        local size=$(du -h database_backup/postgres.tar.gz | cut -f1)
        print_success "PostgreSQL data exported (Size: $size)"
    else
        print_error "PostgreSQL export failed"
        exit 1
    fi
}

# Export Redis volume
export_redis() {
    print_status "Exporting Redis data..."
    
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
        -v cryptopredict_redis_data:/data:ro \
        -v "${backup_path}:/backup" \
        alpine \
        sh -c "cd /data && tar czf /backup/redis.tar.gz . 2>/dev/null" || true
    
    if [ -f "database_backup/redis.tar.gz" ]; then
        local size=$(du -h database_backup/redis.tar.gz | cut -f1)
        print_success "Redis data exported (Size: $size)"
    else
        print_warning "Redis export failed or no data found (this is usually OK)"
    fi
}

# Create transfer info file
create_info_file() {
    print_status "Creating transfer info file..."
    
    cat > database_backup/README.txt << EOF
CryptoPredict Database Export
============================
Export Date: $(date)
Source Computer: $(hostname)
Export Script: temp/export_database.sh

Contents:
---------
- postgres.tar.gz (PostgreSQL database with ALL data)
- redis.tar.gz (Redis cache data - optional)

What's Included:
---------------
✅ All database tables and data
✅ User accounts and passwords
✅ Cryptocurrency data
✅ Price history data
✅ Predictions and models
✅ Application settings
✅ Database schema and indexes

Import Instructions:
-------------------
1. Copy this entire 'database_backup' folder to target system
2. Place it in the project root directory
3. Run: ./temp/import_database.sh
4. Start application: docker-compose -f docker-compose-backend.yml up -d

File Sizes:
----------
EOF
    
    # Add file sizes to info
    if [ -f "database_backup/postgres.tar.gz" ]; then
        echo "- PostgreSQL: $(du -h database_backup/postgres.tar.gz | cut -f1)" >> database_backup/README.txt
    fi
    
    if [ -f "database_backup/redis.tar.gz" ]; then
        echo "- Redis: $(du -h database_backup/redis.tar.gz | cut -f1)" >> database_backup/README.txt
    fi
    
    echo "" >> database_backup/README.txt
    echo "Total backup size: $(du -sh database_backup | cut -f1)" >> database_backup/README.txt
    
    print_success "Transfer info created: database_backup/README.txt"
}

# Cleanup - stop containers
cleanup() {
    print_status "Cleaning up..."
    docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
    print_success "Cleanup completed"
}

# Main export process
main() {
    echo ""
    print_status "Starting database export process..."
    echo ""
    
    # Run all steps
    check_docker
    find_compose_file  
    setup_backup_dir
    stop_containers
    start_database_containers
    export_postgres
    export_redis
    create_info_file
    cleanup
    
    echo ""
    echo "================================================="
    print_success "DATABASE EXPORT COMPLETED!"
    echo "================================================="
    echo ""
    echo "📁 Backup Location: $(pwd)/database_backup/"
    echo "📊 Backup Size: $(du -sh database_backup | cut -f1)"
    echo ""
    echo "📋 Next Steps:"
    echo "  1. Copy 'database_backup' folder to target system"
    echo "  2. On target system, run: ./temp/import_database.sh"
    echo "  3. Start application: docker-compose -f docker-compose-backend.yml up -d"
    echo ""
    echo "💡 The backup includes ALL your data (users, prices, predictions, etc.)"
    echo ""
}

# Run main function
main