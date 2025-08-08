#!/bin/bash
# File: scripts/export-database.sh
# Export PostgreSQL database for transfer to another system

echo "📤 CryptoPredict Database Export Tool"
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

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    print_success "Environment variables loaded from .env"
else
    print_warning ".env file not found, using defaults"
fi

# Database configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5433}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-admin123}
DB_NAME=${DB_NAME:-cryptopredict}

# Export configuration
EXPORT_DIR="database_export_$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${EXPORT_DIR}/cryptopredict_backup.sql"
ENV_FILE="${EXPORT_DIR}/database_config.env"
README_FILE="${EXPORT_DIR}/README.md"

print_info "Export Configuration:"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   User: $DB_USER"
echo "   Database: $DB_NAME"
echo "   Export Directory: $EXPORT_DIR"
echo ""

# Create export directory
print_info "Creating export directory..."
mkdir -p "$EXPORT_DIR"
print_success "Export directory created: $EXPORT_DIR"

# Test database connection
print_info "Testing database connection..."
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q; then
    print_error "Cannot connect to PostgreSQL!"
    print_error "Please ensure PostgreSQL is running on $DB_HOST:$DB_PORT"
    exit 1
fi
print_success "Database connection OK"

# Export database schema and data
print_info "Exporting database..."
export PGPASSWORD="$DB_PASSWORD"

# Create full backup with schema and data (without database creation commands)
pg_dump -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --clean \
        --if-exists \
        --no-owner \
        --no-privileges \
        --verbose \
        --file="$BACKUP_FILE"

if [ $? -eq 0 ]; then
    print_success "Database backup created: $BACKUP_FILE"
else
    print_error "Database backup failed!"
    exit 1
fi

# Create separate schema-only backup (for import flexibility)
SCHEMA_FILE="${EXPORT_DIR}/schema_only.sql"
pg_dump -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --schema-only \
        --clean \
        --if-exists \
        --no-owner \
        --no-privileges \
        --file="$SCHEMA_FILE"

if [ $? -eq 0 ]; then
    print_success "Schema backup created: $SCHEMA_FILE"
fi

# Create data-only backup
DATA_FILE="${EXPORT_DIR}/data_only.sql"
pg_dump -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --data-only \
        --column-inserts \
        --no-owner \
        --no-privileges \
        --file="$DATA_FILE"

if [ $? -eq 0 ]; then
    print_success "Data backup created: $DATA_FILE"
fi

# Export environment configuration
print_info "Creating environment configuration..."
cat > "$ENV_FILE" << EOF
# Database Configuration for CryptoPredict
# Generated on $(date)
# Original source: $DB_HOST:$DB_PORT

# Database Settings
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5433/$DB_NAME
DB_HOST=localhost
DB_PORT=5433
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME

# Application Settings (copy from your original .env)
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production-12345678
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production-87654321
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis Settings
REDIS_URL=redis://127.0.0.1:6379/0

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:3000,http://localhost:8000,http://testserver

# External API Keys (update with your own)
COINGECKO_API_KEY=your_coingecko_api_key_here
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# ML Model Settings
MODEL_PATH=./models
MODEL_UPDATE_INTERVAL=3600
DATA_COLLECTION_INTERVAL=300

# Logging Settings
LOG_LEVEL=INFO
LOG_FILE_PATH=./logs/app.log
EOF

print_success "Environment configuration created: $ENV_FILE"

# Create README with import instructions
print_info "Creating import instructions..."
cat > "$README_FILE" << 'EOF'
# CryptoPredict Database Export

This package contains a complete export of the CryptoPredict database.

## 📦 Contents

- `cryptopredict_backup.sql` - Complete database backup (schema + data)
- `schema_only.sql` - Database schema only
- `data_only.sql` - Data only (with INSERT statements)
- `database_config.env` - Environment configuration
- `README.md` - This file

## 🚀 Import Instructions

### 1. Prerequisites on Target System

```bash
# Install PostgreSQL (any version compatible)
# Install Redis (if using Redis features)
# Install Python 3.8+ with virtual environment
# Install Node.js 16+ (for frontend)
```

### 2. Setup PostgreSQL

```bash
# Create database user (if needed)
sudo -u postgres createuser --interactive postgres

# Set password for postgres user
sudo -u postgres psql
ALTER USER postgres PASSWORD 'admin123';
\q

# Create database
createdb -h localhost -p 5433 -U postgres cryptopredict
# Note: Adjust port if your PostgreSQL runs on different port
```

### 3. Import Database

```bash
# Method 1: Complete restore (recommended)
psql -h localhost -p 5433 -U postgres -f cryptopredict_backup.sql

# Method 2: Schema then data (if complete restore fails)
psql -h localhost -p 5433 -U postgres -f schema_only.sql
psql -h localhost -p 5433 -U postgres -d cryptopredict -f data_only.sql
```

### 4. Setup Application

```bash
# Copy environment configuration
cp database_config.env .env

# Edit .env file with your specific settings:
# - Update passwords
# - Add your API keys
# - Adjust ports if needed

# Install and setup CryptoPredict application
# (Follow the main installation guide)
```

### 5. Verify Import

```bash
# Test database connection
psql -h localhost -p 5433 -U postgres -d cryptopredict -c "\dt"

# Should show tables:
# - users
# - cryptocurrencies  
# - price_data
# - predictions
# - alembic_version (if using migrations)
```

## 🔧 Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5433

# Check port availability
netstat -tulpn | grep 5433

# Connect to database manually
psql -h localhost -p 5433 -U postgres -d cryptopredict
```

### Import Errors

```bash
# If you get permission errors:
sudo -u postgres psql -f cryptopredict_backup.sql

# If database exists error:
dropdb -h localhost -p 5433 -U postgres cryptopredict
createdb -h localhost -p 5433 -U postgres cryptopredict
psql -h localhost -p 5433 -U postgres -f cryptopredict_backup.sql

# If encoding issues:
psql -h localhost -p 5433 -U postgres -f cryptopredict_backup.sql -v ON_ERROR_STOP=1
```

### Application Startup Issues

```bash
# Test configuration
python -c "from app.core.config import settings; print('Config OK:', settings.DATABASE_URL)"

# Test database connection
python -c "from app.core.database import engine; engine.connect()"

# Use development mode switcher
./dev-mode-switcher.sh local
```

## 📋 Export Information

- **Export Date**: Generated automatically
- **Source Database**: PostgreSQL on localhost:5433
- **Original Environment**: Development
- **Tables Exported**: All application tables with data
- **Compatibility**: PostgreSQL 12+ recommended

## 🔄 After Import

1. Update `.env` file with your specific configuration
2. Install application dependencies
3. Run `./dev-mode-switcher.sh local` to configure for local development
4. Start application with `./start-backend-local.sh`
5. Verify everything works at http://localhost:8000/docs

## 📞 Support

If you encounter issues during import, check:
1. PostgreSQL version compatibility
2. User permissions and passwords
3. Port availability and conflicts
4. Environment variable configuration

EOF

print_success "Import instructions created: $README_FILE"

# Create compressed archive
print_info "Creating compressed archive..."
ARCHIVE_NAME="cryptopredict_db_export_$(date +%Y%m%d_%H%M%S).tar.gz"

tar -czf "$ARCHIVE_NAME" "$EXPORT_DIR"

if [ $? -eq 0 ]; then
    print_success "Archive created: $ARCHIVE_NAME"
    
    # Show archive info
    ARCHIVE_SIZE=$(du -h "$ARCHIVE_NAME" | cut -f1)
    print_info "Archive size: $ARCHIVE_SIZE"
else
    print_error "Failed to create archive"
fi

# Display export summary
echo ""
echo "📊 Export Summary"
echo "================="
echo "✅ Database backup: $(du -h "$BACKUP_FILE" | cut -f1)"
echo "✅ Schema backup: $(du -h "$SCHEMA_FILE" | cut -f1)"
echo "✅ Data backup: $(du -h "$DATA_FILE" | cut -f1)"
echo "✅ Environment config: $ENV_FILE"
echo "✅ Instructions: $README_FILE"
if [ -f "$ARCHIVE_NAME" ]; then
    echo "✅ Compressed archive: $ARCHIVE_NAME ($ARCHIVE_SIZE)"
fi

echo ""
echo "🎉 Export Complete!"
echo "=================="
echo ""
echo "📤 Transfer files:"
echo "   • Archive: $ARCHIVE_NAME (recommended - auto-extracts)"
echo "   • Or directory: $EXPORT_DIR"
echo ""
echo "📝 On target system:"
echo "   1. Copy archive: scp $ARCHIVE_NAME user@target:/"
echo "   2. Run import: ./scripts/import-database.sh $ARCHIVE_NAME"
echo "   3. Setup app: ./dev-mode-switcher.sh local"
echo ""
echo "🔒 Security note:"
echo "   The export contains database passwords."
echo "   Keep it secure and delete after transfer."