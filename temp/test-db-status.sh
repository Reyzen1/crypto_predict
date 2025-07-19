#!/bin/bash
# File: scripts/test-db-status.sh
# Test current database status

echo "🔍 Testing Database Status"
echo "========================="

echo "📋 Checking if database exists..."
if docker-compose -f docker-compose-backend.yml exec postgres psql -U postgres -lqt | cut -d \| -f 1 | grep -qw cryptopredict; then
    echo "✅ Database 'cryptopredict' exists"
    
    echo "📊 Checking tables..."
    docker-compose -f docker-compose-backend.yml exec postgres psql -U postgres -d cryptopredict -c "
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    "
    
    echo "👤 Checking users table schema..."
    docker-compose -f docker-compose-backend.yml exec postgres psql -U postgres -d cryptopredict -c "
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        ORDER BY ordinal_position;
    " 2>/dev/null || echo "⚠️ Users table doesn't exist"
    
else
    echo "❌ Database 'cryptopredict' does not exist"
    echo ""
    echo "💡 Solutions:"
    echo "   1. Run: ./scripts/drop-tables.sh"
    echo "   2. Run: ./scripts/manual-db-reset.sh"
    echo "   3. Run: ./scripts/setup-db.sh"
fi

echo ""
echo "🌐 PostgreSQL container status:"
docker-compose -f docker-compose-backend.yml ps postgres