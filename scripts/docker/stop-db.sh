#!/bin/bash
# File: scripts/stop-db.sh
# Stop databases script

echo "🛑 Stopping databases..."
echo "========================"

# Check if docker-compose file exists
if [ ! -f "docker-compose-backend.yml" ]; then
    echo "❌ docker-compose-backend.yml not found!"
    echo "Please run from project root directory."
    exit 1
fi

# Stop and remove containers
docker-compose -f docker-compose-backend.yml down

echo ""
echo "✅ Databases stopped!"
echo ""
echo "To start again: ./scripts/quick-setup.sh"
echo "To clean everything: docker-compose -f docker-compose-backend.yml down -v"