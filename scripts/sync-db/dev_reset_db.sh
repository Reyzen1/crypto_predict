#!/bin/bash
# File: scripts/sync-db/dev_reset_db.sh
# Quick database reset for development

echo "🔄 Development Database Reset"
echo "============================"

# Stop containers
docker-compose -f docker-compose-backend.yml down

# Remove database volume
docker volume rm cryptopredict_postgres_data 2>/dev/null || true

# Create fresh volume
docker volume create cryptopredict_postgres_data

# Start containers
docker-compose -f docker-compose-backend.yml up -d postgres redis

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
sleep 10

# Reset database from models
python scripts/sync-db/disable_alembic_dev.py

# Add seed data
python scripts/sync-db/seed_data.py

echo "✅ Development database reset complete!"
echo "🚀 Start backend: cd backend && uvicorn app.main:app --reload"
