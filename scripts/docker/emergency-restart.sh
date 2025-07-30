#!/bin/bash
# File: scripts/emergency-restart.sh
# Emergency restart of everything

echo "🚨 Emergency Restart"
echo "=================="

echo "🛑 Stopping all containers..."
docker-compose -f docker-compose-backend.yml down -v

echo "🧹 Cleaning up Docker..."
docker system prune -f

echo "🔄 Restarting containers..."
docker-compose -f docker-compose-backend.yml up -d postgres redis

echo "⏳ Waiting for containers to be ready..."
sleep 15

echo "🔍 Checking container status..."
docker-compose -f docker-compose-backend.yml ps

echo "🏗️ Creating database..."
docker-compose -f docker-compose-backend.yml exec postgres psql -U postgres -c "CREATE DATABASE cryptopredict;" 2>/dev/null || echo "Database might already exist"

echo "✅ Emergency restart complete!"
echo ""
echo "Now run: ./scripts/use-integer-models.sh"