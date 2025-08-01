# CryptoPredict Database Export

**Export Date:** Tue Jul 29 18:51:55 IST 2025
**Source Computer:** DESKTOP-52VKHGP
**Export Method:** Docker Volume Transfer (Temp Volume)

## Contents

- `postgres.tar.gz` - PostgreSQL database with ALL data
- `redis.tar.gz` - Redis cache data (optional)
- `README.md` - This documentation

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
   ```bash
   git clone [your-repo-url]
   cd crypto_predict
   ```

2. **Copy this backup folder to project root**

3. **Run import:**
   ```bash
   # Using working import script (recommended)
   ./scripts/sync-db/import_database_working.sh scripts/sync-db/database_backup/backup_20250729_185145
   
   # Or using standard import script
   ./scripts/sync-db/import_database.sh scripts/sync-db/database_backup/backup_20250729_185145
   ```

4. **Start application:**
   ```bash
   docker-compose -f docker-compose-backend.yml up -d
   ```

## File Information

- PostgreSQL: 1.0K
- Redis: 1.0K

**Total backup size:** 6.0K

## Manual Import Steps (if script fails)

```bash
# Stop containers
docker-compose -f docker-compose-backend.yml down

# Remove old volumes
docker volume rm cryptopredict_postgres_data cryptopredict_redis_data

# Create fresh volumes
docker volume create cryptopredict_postgres_data
docker volume create cryptopredict_redis_data

# Create temp volume and copy files
docker volume create temp_restore
docker create --name restore_temp -v temp_restore:/data alpine
docker cp ./scripts/sync-db/database_backup/backup_20250729_185145/postgres.tar.gz restore_temp:/data/
docker cp ./scripts/sync-db/database_backup/backup_20250729_185145/redis.tar.gz restore_temp:/data/
docker rm restore_temp

# Extract to final volumes
docker run --rm -v temp_restore:/source -v cryptopredict_postgres_data:/dest alpine sh -c 'cd /dest && tar xzf /source/postgres.tar.gz'
docker run --rm -v temp_restore:/source -v cryptopredict_redis_data:/dest alpine sh -c 'cd /dest && tar xzf /source/redis.tar.gz'

# Clean up and start
docker volume rm temp_restore
docker-compose -f docker-compose-backend.yml up -d
```
