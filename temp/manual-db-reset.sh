#!/bin/bash
# File: scripts/manual-db-reset.sh
# Manual database reset using direct Docker commands

set -e

echo "🔧 Manual Database Reset"
echo "======================="

echo "Step 1: Drop database via Docker..."
docker-compose -f docker-compose-backend.yml exec postgres dropdb -U postgres --if-exists cryptopredict || echo "Database may not exist, continuing..."

echo "Step 2: Create database via Docker..."
docker-compose -f docker-compose-backend.yml exec postgres createdb -U postgres cryptopredict || echo "Database might already exist, continuing..."

echo "Step 3: Test connection..."
if docker-compose -f docker-compose-backend.yml exec postgres psql -U postgres -d cryptopredict -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database connection successful!"
else
    echo "❌ Database connection failed!"
    exit 1
fi

echo ""
echo "🎉 Manual database reset complete!"
echo "================================="
echo ""
echo "Now run: ./scripts/setup-db.sh"