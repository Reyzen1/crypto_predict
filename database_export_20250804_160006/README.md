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

