# 🗄️ Database Sync Scripts

This directory contains all scripts for database synchronization, migration, and transfer for the CryptoPredict project.

## 📋 Scripts Overview

### 🔄 `complete_setup.sh`
**Main setup script for database initialization and migration**

```bash
# Auto-detect and setup
./scripts/sync-db/complete_setup.sh

# Force fresh setup (destroys existing data)
./scripts/sync-db/complete_setup.sh --fresh

# Force existing setup migration  
./scripts/sync-db/complete_setup.sh --existing

# Verify setup only
./scripts/sync-db/complete_setup.sh --verify
```

**Use cases:**
- ✅ First-time project setup
- ✅ After pulling code updates
- ✅ Migrating to new system
- ✅ Fixing database issues

---

### 📤 `export_database.sh`
**Export database for transfer to another system**

```bash
./scripts/sync-db/export_database.sh
```

**Output:**
- Creates `database_backup_YYYYMMDD_HHMMSS/` folder
- Contains PostgreSQL and Redis data
- Includes transfer instructions

---

### 📥 `import_database.sh`
**Import database from exported backup**

```bash
./scripts/sync-db/import_database.sh database_backup_20250726_123456
```

**⚠️ Warning:** This destroys existing database data!

---

### 🔧 `create_sync_migration.py`
**Create Alembic migration to sync database with models**

```bash
python scripts/sync-db/create_sync_migration.py
```

**Use when:**
- Models and database are out of sync
- After major schema changes
- Database missing columns/tables

---

### 🌱 `seed_data.py`
**Add essential seed data to database**

```bash
python scripts/sync-db/seed_data.py
```

**Creates:**
- Test user (`test@cryptopredict.com`)
- Bitcoin and Ethereum cryptocurrencies
- Essential reference data

---

## 🚀 Quick Start Scenarios

### 📱 **New Developer Setup**
```bash
git clone [repo-url]
cd crypto_predict
./scripts/sync-db/complete_setup.sh
```

### 🔄 **After Code Updates**
```bash
git pull
./scripts/sync-db/complete_setup.sh --existing
```

### 🗂️ **Transfer to New System**
```bash
# On source system:
./scripts/sync-db/export_database.sh

# Transfer database_backup_* folder to target system

# On target system:
git clone [repo-url]
cd crypto_predict  
./scripts/sync-db/import_database.sh database_backup_20250726_123456
./scripts/sync-db/complete_setup.sh --existing
```

### 🔧 **Fix Database Issues**
```bash
# If database is corrupted or out of sync:
./scripts/sync-db/complete_setup.sh --fresh

# If just need to sync schema:
python scripts/sync-db/create_sync_migration.py
```

---

## 📋 Prerequisites

### Required Tools:
- ✅ **Docker** - For containers
- ✅ **Docker Compose** - For service orchestration
- ✅ **Python 3.8+** - For Python scripts
- ✅ **Git** - For code management

### Required on PATH:
- `docker`
- `docker-compose`
- `python`
- `git`

---

## 🏗️ Directory Structure

```
scripts/sync-db/
├── complete_setup.sh           # 🔄 Main setup script
├── export_database.sh          # 📤 Database export
├── import_database.sh          # 📥 Database import  
├── create_sync_migration.py    # 🔧 Create sync migration
├── seed_data.py                # 🌱 Add seed data
└── README.md                   # 📚 This file
```

---

## 🛠️ Technical Details

### Database Connection:
- **Host:** localhost (via Docker)
- **Port:** 5432 (PostgreSQL), 6379 (Redis)
- **Database:** cryptopredict
- **User:** postgres

### Migration System:
- **Tool:** Alembic
- **Location:** `backend/alembic/`
- **Auto-detection:** ✅ Models vs Database sync

### Backup Format:
- **PostgreSQL:** tar.gz of data directory
- **Redis:** tar.gz of data directory  
- **Transfer:** Cross-platform compatible

---

## 🔍 Troubleshooting

### Common Issues:

#### 🚫 "Docker not running"
```bash
# Start Docker Desktop
# Or on Linux: sudo systemctl start docker
```

#### 🚫 "No docker-compose file found"
```bash
# Make sure you're in project root
cd /path/to/crypto_predict
```

#### 🚫 "PostgreSQL connection failed"
```bash
# Wait longer for container startup
sleep 30
./scripts/sync-db/complete_setup.sh --verify
```

#### 🚫 "Migration failed"
```bash
# Check for multiple heads
cd backend
alembic heads

# Merge if needed
alembic merge heads -m "merge"
alembic upgrade head
```

#### 🚫 "Missing columns/tables"
```bash
# Force sync migration
python scripts/sync-db/create_sync_migration.py
```

---

## 📞 Getting Help

1. **Check logs:**
   ```bash
   docker-compose -f docker-compose-backend.yml logs
   ```

2. **Verify setup:**
   ```bash
   ./scripts/sync-db/complete_setup.sh --verify
   ```

3. **Database status:**
   ```bash
   docker-compose -f docker-compose-backend.yml exec postgres psql -U postgres -d cryptopredict -c "\dt"
   ```

4. **Start fresh (destructive):**
   ```bash
   ./scripts/sync-db/complete_setup.sh --fresh
   ```

---

## 🎯 Best Practices

### ✅ **Do:**
- Run `complete_setup.sh` after code updates
- Export database before major changes
- Use version control for migration files
- Test imports on development environment first

### ❌ **Don't:**
- Run `--fresh` on production data
- Skip verification steps
- Manually edit migration files
- Transfer database files without proper export/import

---

**📚 For more details, see individual script documentation and project README.**