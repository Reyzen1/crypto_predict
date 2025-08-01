#!/bin/bash
# File: scripts/sync-db/export_database_working.sh
# Working database export script using temp volume method

echo "🚀 CryptoPredict Database Export (Working Version)"
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

# Change to project root
cd "$PROJECT_ROOT"

# Main export function
main() {
    print_status "Starting database export using temp volume method..."
    
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
    
    # Create backup directory structure
    BACKUP_BASE_DIR="scripts/sync-db/database_backup"
    BACKUP_DIR="$BACKUP_BASE_DIR/backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    print_success "Created backup directory: $BACKUP_DIR"
    
    # Ensure containers are running
    print_status "Ensuring containers are running..."
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis
    sleep 5
    
    # Create temp volume
    print_status "Creating temporary export volume..."
    docker volume create temp_export
    
    # Export PostgreSQL
    print_status "Exporting PostgreSQL data..."
    docker run --rm \
        -v cryptopredict_postgres_data:/data:ro \
        -v temp_export:/backup \
        alpine sh -c "cd /data && tar czf /backup/postgres.tar.gz ."
    
    if [ $? -eq 0 ]; then
        print_success "PostgreSQL data exported to temp volume"
    else
        print_error "PostgreSQL export failed"
        docker volume rm temp_export
        exit 1
    fi
    
    # Copy PostgreSQL from temp volume to host
    print_status "Copying PostgreSQL backup to host..."
    docker create --name temp_postgres_container -v temp_export:/data alpine
    docker cp temp_postgres_container:/data/postgres.tar.gz "./$BACKUP_DIR/"
    docker rm temp_postgres_container
    
    if [ -f "$BACKUP_DIR/postgres.tar.gz" ]; then
        local pg_size=$(du -h "$BACKUP_DIR/postgres.tar.gz" | cut -f1)
        print_success "PostgreSQL backup copied (Size: $pg_size)"
    else
        print_error "Failed to copy PostgreSQL backup"
        docker volume rm temp_export
        exit 1
    fi
    
    # Export Redis
    print_status "Exporting Redis data..."
    docker run --rm \
        -v cryptopredict_redis_data:/data:ro \
        -v temp_export:/backup \
        alpine sh -c "cd /data && tar czf /backup/redis.tar.gz . 2>/dev/null" || true
    
    # Copy Redis from temp volume to host
    print_status "Copying Redis backup to host..."
    docker create --name temp_redis_container -v temp_export:/data alpine
    docker cp temp_redis_container:/data/redis.tar.gz "./$BACKUP_DIR/" 2>/dev/null || true
    docker rm temp_redis_container
    
    if [ -f "$BACKUP_DIR/redis.tar.gz" ]; then
        local redis_size=$(du -h "$BACKUP_DIR/redis.tar.gz" | cut -f1)
        print_success "Redis backup copied (Size: $redis_size)"
    else
        print_warning "Redis backup not found (this is usually OK)"
    fi
    
    # Clean up temp volume
    print_status "Cleaning up temporary volume..."
    docker volume rm temp_export
    
    # Create README file
    print_status "Creating transfer documentation..."
    cat > "$BACKUP_DIR/README.md" << EOF
# CryptoPredict Database Export

**Export Date:** $(date)
**Source Computer:** $(hostname)
**Export Method:** Docker Volume Transfer (Temp Volume)

## Contents

- \`postgres.tar.gz\` - PostgreSQL database with ALL data
- \`redis.tar.gz\` - Redis cache data (optional)
- \`README.md\` - This documentation

## What's Included

✅ All database tables and data  
✅ User accounts and passwords  
✅ Cryptocurrency data  
✅ Price history and predictions  
✅ ML model training data  
✅ Application settings  
✅ Database schema and indexes  

## Import Instructions

### On Target System:

1. **Clone the project:**
   \`\`\`bash
   git clone [your-repo-url]
   cd crypto_predict
   \`\`\`

2. **Copy this backup folder to project root**

3. **Run import:**
   \`\`\`bash
   # Using working import script (recommended)
   ./scripts/sync-db/import_database_working.sh $BACKUP_DIR
   
   # Or using standard import script
   ./scripts/sync-db/import_database.sh $BACKUP_DIR
   \`\`\`

4. **Start application:**
   \`\`\`bash
   docker-compose -f docker-compose-backend.yml up -d
   \`\`\`

## File Information

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
    echo "" >> "$BACKUP_DIR/README.md"
    echo "## Manual Import Steps (if script fails)" >> "$BACKUP_DIR/README.md"
    echo "" >> "$BACKUP_DIR/README.md"
    echo "\`\`\`bash" >> "$BACKUP_DIR/README.md"
    echo "# Stop containers" >> "$BACKUP_DIR/README.md"
    echo "docker-compose -f docker-compose-backend.yml down" >> "$BACKUP_DIR/README.md"
    echo "" >> "$BACKUP_DIR/README.md"
    echo "# Remove old volumes" >> "$BACKUP_DIR/README.md"
    echo "docker volume rm cryptopredict_postgres_data cryptopredict_redis_data" >> "$BACKUP_DIR/README.md"
    echo "" >> "$BACKUP_DIR/README.md"
    echo "# Create fresh volumes" >> "$BACKUP_DIR/README.md"
    echo "docker volume create cryptopredict_postgres_data" >> "$BACKUP_DIR/README.md"
    echo "docker volume create cryptopredict_redis_data" >> "$BACKUP_DIR/README.md"
    echo "" >> "$BACKUP_DIR/README.md"
    echo "# Create temp volume and copy files" >> "$BACKUP_DIR/README.md"
    echo "docker volume create temp_restore" >> "$BACKUP_DIR/README.md"
    echo "docker create --name restore_temp -v temp_restore:/data alpine" >> "$BACKUP_DIR/README.md"
    echo "docker cp ./$BACKUP_DIR/postgres.tar.gz restore_temp:/data/" >> "$BACKUP_DIR/README.md"
    echo "docker cp ./$BACKUP_DIR/redis.tar.gz restore_temp:/data/" >> "$BACKUP_DIR/README.md"
    echo "docker rm restore_temp" >> "$BACKUP_DIR/README.md"
    echo "" >> "$BACKUP_DIR/README.md"
    echo "# Extract to final volumes" >> "$BACKUP_DIR/README.md"
    echo "docker run --rm -v temp_restore:/source -v cryptopredict_postgres_data:/dest alpine sh -c 'cd /dest && tar xzf /source/postgres.tar.gz'" >> "$BACKUP_DIR/README.md"
    echo "docker run --rm -v temp_restore:/source -v cryptopredict_redis_data:/dest alpine sh -c 'cd /dest && tar xzf /source/redis.tar.gz'" >> "$BACKUP_DIR/README.md"
    echo "" >> "$BACKUP_DIR/README.md"
    echo "# Clean up and start" >> "$BACKUP_DIR/README.md"
    echo "docker volume rm temp_restore" >> "$BACKUP_DIR/README.md"
    echo "docker-compose -f docker-compose-backend.yml up -d" >> "$BACKUP_DIR/README.md"
    echo "\`\`\`" >> "$BACKUP_DIR/README.md"
    
    # Final summary
    echo ""
    echo "=================================================="
    print_success "EXPORT COMPLETED SUCCESSFULLY!"
    echo "=================================================="
    echo ""
    echo "📁 Backup Location: $(pwd)/$BACKUP_DIR"
    echo "📊 Backup Contents:"
    ls -la "$BACKUP_DIR"
    echo ""
    echo "📋 File Sizes:"
    du -h "$BACKUP_DIR"/*
    echo ""
    echo "📦 Total Size: $(du -sh "$BACKUP_DIR" | cut -f1)"
    echo ""
    echo "🚀 Next Steps:"
    echo "   1. Copy '$BACKUP_DIR' to target system"
    echo "   2. Place backup folder in target system's project root"
    echo "   3. On target: git clone [repo] && cd crypto_predict"
    echo "   4. On target: ./scripts/sync-db/import_database_working.sh $BACKUP_DIR"
    echo "   5. On target: docker-compose -f docker-compose-backend.yml up -d"
    echo ""
    echo "💡 Or copy just the backup folder contents and use relative path:"
    echo "   ./scripts/sync-db/import_database_working.sh scripts/sync-db/database_backup/backup_YYYYMMDD_HHMMSS"
    echo ""
    echo "📁 Backup Structure:"
    echo "   scripts/sync-db/database_backup/"
    echo "   └── backup_$(date +%Y%m%d_%H%M%S)/"
    echo "       ├── postgres.tar.gz"
    echo "       ├── redis.tar.gz"
    echo "       └── README.md"
    echo ""
    echo "💡 The backup includes ALL your data and is ready for transfer!"
}

# Run main function
main "$@"