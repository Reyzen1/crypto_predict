#!/bin/bash
# File: scripts/sync-db/export_database.sh
# Export database for transfer to another system

echo "🚀 CryptoPredict Database Export"
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

# Export database volumes
export_volumes() {
    print_status "Exporting database volumes..."
    
    # Create backup directory
    BACKUP_DIR="database_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Ensure containers are running
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis
    sleep 10
    
    # Export PostgreSQL volume
    print_status "Exporting PostgreSQL data..."
    docker run --rm \
        -v cryptopredict_postgres_data:/data:ro \
        -v "$(pwd)/$BACKUP_DIR":/backup \
        alpine \
        sh -c "cd /data && tar czf /backup/postgres.tar.gz ."
    
    if [ $? -eq 0 ]; then
        local size=$(du -h "$BACKUP_DIR/postgres.tar.gz" | cut -f1)
        print_success "PostgreSQL exported (Size: $size)"
    else
        print_error "PostgreSQL export failed"
        return 1
    fi
    
    # Export Redis volume
    print_status "Exporting Redis data..."
    docker run --rm \
        -v cryptopredict_redis_data:/data:ro \
        -v "$(pwd)/$BACKUP_DIR":/backup \
        alpine \
        sh -c "cd /data && tar czf /backup/redis.tar.gz . 2>/dev/null" || true
    
    if [ -f "$BACKUP_DIR/redis.tar.gz" ]; then
        local size=$(du -h "$BACKUP_DIR/redis.tar.gz" | cut -f1)
        print_success "Redis exported (Size: $size)"
    else
        print_warning "Redis export failed (this is usually OK)"
    fi
    
    # Create transfer info
    cat > "$BACKUP_DIR/README.md" << EOF
# CryptoPredict Database Export

**Export Date:** $(date)
**Source Computer:** $(hostname)
**Export Method:** Docker Volume Transfer

## Contents

- \`postgres.tar.gz\` - PostgreSQL database with ALL data
- \`redis.tar.gz\` - Redis cache data (optional)
- \`README.md\` - This file

## What's Included

✅ All database tables and data  
✅ User accounts and passwords  
✅ Cryptocurrency data  
✅ Price history data  
✅ Predictions and models  
✅ Application settings  
✅ Database schema and indexes  

## Import Instructions

### On Target System:

1. **Copy this folder** to the target system
2. **Clone the project** from GitHub:
   \`\`\`bash
   git clone [your-repo-url]
   cd crypto_predict
   \`\`\`

3. **Run the import script**:
   \`\`\`bash
   ./scripts/sync-db/import_database.sh /path/to/$BACKUP_DIR
   \`\`\`

4. **Start the application**:
   \`\`\`bash
   docker-compose -f docker-compose-backend.yml up -d
   \`\`\`

## File Sizes

EOF
    
    # Add file sizes
    if [ -f "$BACKUP_DIR/postgres.tar.gz" ]; then
        echo "- PostgreSQL: $(du -h "$BACKUP_DIR/postgres.tar.gz" | cut -f1)" >> "$BACKUP_DIR/README.md"
    fi
    
    if [ -f "$BACKUP_DIR/redis.tar.gz" ]; then
        echo "- Redis: $(du -h "$BACKUP_DIR/redis.tar.gz" | cut -f1)" >> "$BACKUP_DIR/README.md"
    fi
    
    echo "" >> "$BACKUP_DIR/README.md"
    echo "**Total backup size:** $(du -sh "$BACKUP_DIR" | cut -f1)" >> "$BACKUP_DIR/README.md"
    
    echo "$BACKUP_DIR"
}

# Main function
main() {
    print_status "Starting database export..."
    
    if ! check_prerequisites; then
        exit 1
    fi
    
    if ! find_compose_file; then
        exit 1
    fi
    
    backup_dir=$(export_volumes)
    if [ $? -eq 0 ]; then
        echo ""
        print_success "Export completed successfully!"
        echo ""
        echo "📁 Backup location: $(pwd)/$backup_dir"
        echo "📊 Backup size: $(du -sh "$backup_dir" | cut -f1)"
        echo ""
        echo "📋 Next steps:"
        echo "   1. Copy '$backup_dir' to target system"
        echo "   2. On target: git clone [repo]"
        echo "   3. On target: ./scripts/sync-db/import_database.sh $backup_dir"
        echo ""
        echo "💡 The backup includes ALL your data (users, prices, predictions, etc.)"
    else
        print_error "Export failed!"
        exit 1
    fi
}

main "$@"