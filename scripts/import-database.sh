#!/bin/bash
# File: scripts/import-database.sh
# Import CryptoPredict database from export package

echo "📥 CryptoPredict Database Import Tool"
echo "====================================="

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

# Script parameters
IMPORT_SOURCE=${1:-""}
FORCE_RECREATE=${2:-"false"}
AUTO_CLEANUP=${3:-"true"}  # Default: auto cleanup extracted directories

show_usage() {
    echo "Usage: $0 [import_source] [force_recreate] [auto_cleanup]"
    echo ""
    echo "Parameters:"
    echo "  import_source     - Archive file (.tar.gz) or directory (auto-detect if not specified)"
    echo "  force_recreate    - true/false - Whether to drop existing database (default: false)"
    echo "  auto_cleanup      - true/false - Auto remove extracted directory (default: true)"
    echo ""
    echo "Examples:"
    echo "  $0                                          # Auto-detect, safe mode, auto cleanup"
    echo "  $0 backup.tar.gz                           # Import from archive with auto cleanup"
    echo "  $0 backup.tar.gz true                      # Force recreate database"
    echo "  $0 backup.tar.gz false false               # Keep extracted directory"
    echo "  $0 database_export_20241230_140000         # Import from directory"
    echo ""
    exit 1
}

# Auto-detect and handle import source
IMPORT_DIR=""

if [ -z "$IMPORT_SOURCE" ]; then
    print_info "Auto-detecting import source..."
    
    # Look for .tar.gz archives first
    ARCHIVE_FILES=(cryptopredict_db_export_*.tar.gz)
    if [ ${#ARCHIVE_FILES[@]} -eq 1 ] && [ -f "${ARCHIVE_FILES[0]}" ]; then
        IMPORT_SOURCE="${ARCHIVE_FILES[0]}"
        print_success "Found export archive: $IMPORT_SOURCE"
    elif [ ${#ARCHIVE_FILES[@]} -gt 1 ]; then
        print_warning "Multiple archive files found:"
        for file in "${ARCHIVE_FILES[@]}"; do
            if [ -f "$file" ]; then
                echo "   • $file"
            fi
        done
        print_error "Please specify which archive to import"
        show_usage
    else
        # Look for directories
        EXPORT_DIRS=(database_export_*)
        if [ ${#EXPORT_DIRS[@]} -eq 1 ] && [ -d "${EXPORT_DIRS[0]}" ]; then
            IMPORT_SOURCE="${EXPORT_DIRS[0]}"
            print_success "Found export directory: $IMPORT_SOURCE"
        elif [ ${#EXPORT_DIRS[@]} -gt 1 ]; then
            print_warning "Multiple export directories found:"
            for dir in "${EXPORT_DIRS[@]}"; do
                if [ -d "$dir" ]; then
                    echo "   • $dir"
                fi
            done
            print_error "Please specify which directory to import"
            show_usage
        else
            print_error "No export archive or directory found!"
            print_info "Looking for: cryptopredict_db_export_*.tar.gz or database_export_*"
            show_usage
        fi
    fi
fi

# Handle archive extraction
EXTRACTED_BY_SCRIPT="false"

if [[ "$IMPORT_SOURCE" == *.tar.gz ]]; then
    print_info "Archive detected: $IMPORT_SOURCE"
    
    if [ ! -f "$IMPORT_SOURCE" ]; then
        print_error "Archive file not found: $IMPORT_SOURCE"
        exit 1
    fi
    
    print_info "Extracting archive..."
    
    # Extract archive
    tar -xzf "$IMPORT_SOURCE"
    
    if [ $? -eq 0 ]; then
        print_success "Archive extracted successfully"
        EXTRACTED_BY_SCRIPT="true"
        
        # Find extracted directory - be more specific about the search
        print_info "Looking for extracted directory..."
        
        # Method 1: Look for newly created directories
        EXTRACTED_DIRS=(database_export_*)
        VALID_DIRS=()
        
        for dir in "${EXTRACTED_DIRS[@]}"; do
            if [ -d "$dir" ] && [ -f "$dir/cryptopredict_backup.sql" ]; then
                VALID_DIRS+=("$dir")
                print_info "Found valid directory: $dir"
            fi
        done
        
        if [ ${#VALID_DIRS[@]} -eq 1 ]; then
            IMPORT_DIR="${VALID_DIRS[0]}"
            print_success "Using extracted directory: $IMPORT_DIR"
        elif [ ${#VALID_DIRS[@]} -gt 1 ]; then
            # Multiple valid directories, use the most recent one
            IMPORT_DIR=$(ls -1t "${VALID_DIRS[@]}" | head -n 1)
            print_success "Multiple directories found, using most recent: $IMPORT_DIR"
        else
            # Method 2: Check archive contents and find the directory name
            print_info "Checking archive contents..."
            ARCHIVE_DIR=$(tar -tzf "$IMPORT_SOURCE" | head -1 | cut -d'/' -f1)
            
            if [ -n "$ARCHIVE_DIR" ] && [ -d "$ARCHIVE_DIR" ]; then
                IMPORT_DIR="$ARCHIVE_DIR"
                print_success "Found directory from archive: $IMPORT_DIR"
            else
                print_error "Could not find extracted directory"
                print_info "Available directories:"
                ls -la | grep "^d" | grep "database_export"
                print_info "Archive contents:"
                tar -tzf "$IMPORT_SOURCE" | head -5
                exit 1
            fi
        fi
    else
        print_error "Failed to extract archive: $IMPORT_SOURCE"
        exit 1
    fi
    
elif [ -d "$IMPORT_SOURCE" ]; then
    print_info "Directory detected: $IMPORT_SOURCE"
    IMPORT_DIR="$IMPORT_SOURCE"
else
    print_error "Import source not found or invalid: $IMPORT_SOURCE"
    print_error "Expected: .tar.gz archive or directory"
    exit 1
fi

# Validate import directory
if [ ! -d "$IMPORT_DIR" ]; then
    print_error "Import directory not found: $IMPORT_DIR"
    exit 1
fi

# Check for required files
BACKUP_FILE="$IMPORT_DIR/cryptopredict_backup.sql"
BACKUP_FIXED="$IMPORT_DIR/cryptopredict_backup_fixed.sql"
SCHEMA_FILE="$IMPORT_DIR/schema_only.sql"
SCHEMA_FIXED="$IMPORT_DIR/schema_only_fixed.sql"
DATA_FILE="$IMPORT_DIR/data_only.sql"
ENV_FILE="$IMPORT_DIR/database_config.env"

print_info "Checking export files..."

# Use fixed files if available, otherwise use original
if [ -f "$BACKUP_FIXED" ]; then
    BACKUP_FILE="$BACKUP_FIXED"
    print_success "Using fixed backup file: cryptopredict_backup_fixed.sql"
elif [ -f "$BACKUP_FILE" ]; then
    print_success "Using original backup file: cryptopredict_backup.sql"
else
    print_error "Main backup file not found!"
    exit 1
fi

if [ -f "$SCHEMA_FIXED" ]; then
    SCHEMA_FILE="$SCHEMA_FIXED"
    print_success "Schema file found: schema_only_fixed.sql"
elif [ -f "$SCHEMA_FILE" ]; then
    print_success "Schema file found: schema_only.sql"
fi

if [ -f "$DATA_FILE" ]; then
    print_success "Data file found: data_only.sql"
fi

if [ -f "$ENV_FILE" ]; then
    print_success "Environment config found: database_config.env"
else
    print_warning "Environment config not found: database_config.env"
fi

# Load database configuration
print_info "Loading database configuration..."

# Try to load from environment config file
if [ -f "$ENV_FILE" ]; then
    export $(cat "$ENV_FILE" | grep -v '^#' | xargs)
    print_success "Configuration loaded from $ENV_FILE"
elif [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    print_success "Configuration loaded from .env"
else
    print_warning "No configuration file found, using defaults"
fi

# Database configuration with defaults
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5433}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-admin123}
DB_NAME=${DB_NAME:-cryptopredict}

print_info "Import Configuration:"
echo "   Source: $IMPORT_SOURCE"
echo "   Directory: $IMPORT_DIR"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   User: $DB_USER"
echo "   Database: $DB_NAME"
echo "   Force recreate: $FORCE_RECREATE"
echo "   Auto cleanup: $AUTO_CLEANUP"
echo ""

# Test PostgreSQL connection
print_info "Testing PostgreSQL connection..."
if ! command -v psql >/dev/null 2>&1; then
    print_error "PostgreSQL client (psql) not found!"
    print_error "Please install PostgreSQL client tools"
    exit 1
fi

if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q; then
    print_error "Cannot connect to PostgreSQL!"
    print_error "Please ensure PostgreSQL is running on $DB_HOST:$DB_PORT"
    print_info "Try: pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER"
    exit 1
fi
print_success "PostgreSQL connection OK"

# Set password for psql commands
export PGPASSWORD="$DB_PASSWORD"

# Check if database exists
print_info "Checking if database exists..."
DB_EXISTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -w "$DB_NAME" | wc -l)

if [ "$DB_EXISTS" -eq 1 ]; then
    print_warning "Database '$DB_NAME' already exists"
    
    if [ "$FORCE_RECREATE" = "true" ]; then
        print_warning "Force recreate enabled - dropping existing database"
        RECREATE_DB="yes"
    else
        echo ""
        echo "⚠️  Database '$DB_NAME' already exists!"
        echo ""
        echo "Options:"
        echo "   1. Overwrite existing database (all data will be lost)"
        echo "   2. Use different database name"
        echo "   3. Cancel import"
        echo ""
        read -p "Do you want to OVERWRITE the existing database? [y/N]: " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            RECREATE_DB="yes"
            print_warning "User confirmed database overwrite"
        else
            print_info "Import cancelled by user"
            echo ""
            echo "💡 Alternative options:"
            echo "   • Use different database name in .env"
            echo "   • Run with force flag: $0 $IMPORT_SOURCE true"
            echo "   • Manually handle: dropdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME"
            echo ""
            exit 0
        fi
    fi
    
    if [ "$RECREATE_DB" = "yes" ]; then
        print_warning "Dropping existing database..."
        
        # Show database info before dropping
        print_info "Current database info:"
        CURRENT_TABLES=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "\dt" | wc -l 2>/dev/null || echo "0")
        CURRENT_USERS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "unknown")
        echo "   • Tables: $CURRENT_TABLES"
        echo "   • Users: $CURRENT_USERS"
        
        echo ""
        echo "⚠️  FINAL WARNING: This will permanently delete all data!"
        read -p "Type 'DELETE' to confirm: " CONFIRM
        
        if [ "$CONFIRM" = "DELETE" ]; then
            print_warning "Confirmed - proceeding with database deletion"
            
            # Terminate connections to database
            print_info "Terminating active connections..."
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '$DB_NAME'
                  AND pid <> pg_backend_pid();" >/dev/null 2>&1
            
            # Drop database
            print_info "Dropping database..."
            dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
            
            if [ $? -eq 0 ]; then
                print_success "Existing database dropped"
            else
                print_error "Failed to drop existing database"
                print_info "You may need to manually drop it:"
                print_info "   dropdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME"
                exit 1
            fi
        else
            print_info "Confirmation failed - import cancelled"
            echo "Expected 'DELETE' but got: '$CONFIRM'"
            exit 0
        fi
    fi
    
    # Create new database
    print_info "Creating new database..."
    createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
    
    if [ $? -eq 0 ]; then
        print_success "New database created: $DB_NAME"
    else
        print_error "Failed to create database"
        exit 1
    fi
    
else
    print_info "Database does not exist, creating..."
    createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
    
    if [ $? -eq 0 ]; then
        print_success "Database created: $DB_NAME"
    else
        print_error "Failed to create database"
        exit 1
    fi
fi

# Import database
print_info "Importing database from backup..."

# Import to the existing database (not using the DROP/CREATE commands from backup)
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$BACKUP_FILE" -v ON_ERROR_STOP=0 --quiet

# Check if import was successful by counting tables
IMPORTED_TABLES=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "\dt" | wc -l 2>/dev/null || echo "0")

if [ "$IMPORTED_TABLES" -gt 0 ]; then
    print_success "Database import completed successfully"
else
    print_warning "Standard import had issues, trying alternative method..."
    
    # Alternative method: Use custom import without DROP DATABASE commands
    if [ -f "$SCHEMA_FILE" ] && [ -f "$DATA_FILE" ]; then
        print_info "Using schema + data import method..."
        
        # Create a filtered schema file without DROP/CREATE DATABASE commands
        FILTERED_SCHEMA="/tmp/filtered_schema.sql"
        grep -v -E "^(DROP DATABASE|CREATE DATABASE|\\\\connect)" "$SCHEMA_FILE" > "$FILTERED_SCHEMA"
        
        print_info "Importing filtered schema..."
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$FILTERED_SCHEMA" --quiet
        
        if [ $? -eq 0 ]; then
            print_success "Schema imported successfully"
            
            print_info "Importing data..."
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$DATA_FILE" --quiet
            
            if [ $? -eq 0 ]; then
                print_success "Data imported successfully"
            else
                print_warning "Data import had some issues (this might be normal for existing data)"
            fi
        else
            print_error "Schema import failed"
        fi
        
        # Clean up temporary file
        rm -f "$FILTERED_SCHEMA"
    else
        print_error "Alternative import files not available"
        
        # Last resort: try importing without DROP/CREATE commands
        print_info "Trying filtered backup import..."
        
        FILTERED_BACKUP="/tmp/filtered_backup.sql"
        grep -v -E "^(DROP DATABASE|CREATE DATABASE|\\\\connect)" "$BACKUP_FILE" > "$FILTERED_BACKUP"
        
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$FILTERED_BACKUP" --quiet
        
        # Clean up
        rm -f "$FILTERED_BACKUP"
        
        # Check again
        FINAL_TABLES=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "\dt" | wc -l 2>/dev/null || echo "0")
        
        if [ "$FINAL_TABLES" -gt 0 ]; then
            print_success "Filtered import completed"
        else
            print_error "All import methods failed"
            exit 1
        fi
    fi
fi

# Verify import
print_info "Verifying database import..."

# Check tables
TABLES=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "\dt" | wc -l)
if [ "$TABLES" -gt 0 ]; then
    print_success "Found $TABLES tables in database"
    
    # List tables
    print_info "Tables:"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\dt" | grep -E "^ [a-z_]+" | while read -r line; do
        echo "   • $(echo $line | awk '{print $3}')"
    done
else
    print_warning "No tables found - this might indicate an import issue"
fi

# Check if we can query tables
USERS_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
CRYPTO_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM cryptocurrencies;" 2>/dev/null || echo "0")
PRICE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM price_data;" 2>/dev/null || echo "0")

print_info "Data verification:"
echo "   • Users: $USERS_COUNT records"
echo "   • Cryptocurrencies: $CRYPTO_COUNT records"
echo "   • Price Data: $PRICE_COUNT records"

# Setup environment file
print_info "Setting up environment configuration..."

if [ -f "$ENV_FILE" ] && [ ! -f ".env" ]; then
    cp "$ENV_FILE" .env
    print_success "Environment file created: .env"
    print_warning "Please review and update .env with your specific settings"
elif [ -f "$ENV_FILE" ] && [ -f ".env" ]; then
    cp "$ENV_FILE" .env.imported
    print_success "Environment template created: .env.imported"
    print_info "Review .env.imported and merge with your existing .env if needed"
fi

# Test application connection
if [ -f ".env" ]; then
    print_info "Testing application database connection..."
    
    if [ -d "backend" ] && [ -f "backend/app/core/config.py" ]; then
        cd backend 2>/dev/null || true
        
        # Test connection using app config
        python -c "
try:
    from app.core.config import settings
    from app.core.database import engine
    from sqlalchemy import text
    
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM users'))
        count = result.scalar()
        print('✅ Application database connection successful')
        print(f'   Users table accessible: {count} records')
except Exception as e:
    print(f'⚠️  Application connection test failed: {e}')
    print('   This is normal if the application is not yet configured')
" 2>/dev/null || print_info "Application test requires backend setup"
        
        cd .. 2>/dev/null || true
    fi
fi

# Display final summary
echo ""
echo "📊 Import Summary"
echo "================="
echo "✅ Database: $DB_NAME"
echo "✅ Host: $DB_HOST:$DB_PORT"
echo "✅ Tables: $TABLES found"
echo "✅ Data: Users($USERS_COUNT), Crypto($CRYPTO_COUNT), Prices($PRICE_COUNT)"

if [ -f ".env" ] || [ -f ".env.imported" ]; then
    echo "✅ Environment: Configured"
else
    echo "⚠️  Environment: Manual setup required"
fi

echo ""
echo "🎉 Import Complete!"
echo "=================="
echo ""
# Automatic cleanup of extracted directory
if [ "$EXTRACTED_BY_SCRIPT" = "true" ] && [ "$AUTO_CLEANUP" = "true" ] && [ -d "$IMPORT_DIR" ]; then
    print_info "Performing automatic cleanup..."
    rm -rf "$IMPORT_DIR"
    
    if [ $? -eq 0 ]; then
        print_success "Extracted directory removed: $IMPORT_DIR"
        print_success "Archive preserved: $IMPORT_SOURCE"
    else
        print_warning "Failed to remove extracted directory: $IMPORT_DIR"
    fi
fi

echo ""
echo "🎉 Import Complete!"
echo "=================="
echo ""
echo "🔧 Next steps:"
echo "   1. Review and update .env file"
echo "   2. Install application dependencies"
echo "   3. Run: ./dev-mode-switcher.sh local"
echo "   4. Start backend: ./start-backend-local.sh"
echo "   5. Verify: http://localhost:8000/docs"
echo ""
echo "🔍 Verify import:"
echo "   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
echo ""

if [ "$EXTRACTED_BY_SCRIPT" = "true" ] && [ "$AUTO_CLEANUP" = "false" ]; then
    echo "🗑️  Manual cleanup (if needed):"
    echo "   rm -rf $IMPORT_DIR    # Remove extracted directory"
    echo ""
fi
echo "🔒 Security:"
echo "   • Update passwords in .env"
echo "   • Add your API keys"
echo "   • Review database permissions"