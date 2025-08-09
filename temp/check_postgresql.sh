#!/bin/bash
# temp/check_postgresql.sh
# Check PostgreSQL status and fix connection issues

echo "🗄️ PostgreSQL Diagnostic & Fix"
echo "================================"

# Check if PostgreSQL is running
echo "📋 Step 1: Checking PostgreSQL processes..."
echo ""

# Check for PostgreSQL processes
postgresql_processes=$(ps aux | grep -i postgres | grep -v grep)
if [ -n "$postgresql_processes" ]; then
    echo "✅ PostgreSQL processes found:"
    echo "$postgresql_processes"
else
    echo "❌ No PostgreSQL processes found"
fi

echo ""
echo "📋 Step 2: Checking port 5433..."

# Check if port 5433 is in use
port_check=$(netstat -an | grep :5433)
if [ -n "$port_check" ]; then
    echo "✅ Port 5433 is in use:"
    echo "$port_check"
else
    echo "❌ Port 5433 is not in use"
fi

echo ""
echo "📋 Step 3: Checking default PostgreSQL port 5432..."

# Check default port
port_5432_check=$(netstat -an | grep :5432)
if [ -n "$port_5432_check" ]; then
    echo "✅ Port 5432 is in use:"
    echo "$port_5432_check"
else
    echo "❌ Port 5432 is not in use"
fi

echo ""
echo "📋 Step 4: Checking Docker containers..."

# Check if PostgreSQL is running in Docker
if command -v docker &> /dev/null; then
    docker_containers=$(docker ps | grep postgres)
    if [ -n "$docker_containers" ]; then
        echo "✅ PostgreSQL Docker containers found:"
        echo "$docker_containers"
    else
        echo "❌ No PostgreSQL Docker containers running"
        
        # Check if there are stopped containers
        stopped_containers=$(docker ps -a | grep postgres)
        if [ -n "$stopped_containers" ]; then
            echo "⚠️ Stopped PostgreSQL containers found:"
            echo "$stopped_containers"
        fi
    fi
else
    echo "⚠️ Docker not available"
fi

echo ""
echo "📋 Step 5: Suggested fixes..."
echo ""

# Suggest fixes based on findings
if [ -z "$postgresql_processes" ] && [ -z "$port_check" ]; then
    echo "🔧 PostgreSQL is not running. Try these fixes:"
    echo ""
    echo "Option 1: Start with Docker (Recommended)"
    echo "   docker-compose up -d postgres"
    echo ""
    echo "Option 2: Start local PostgreSQL service"
    echo "   # Windows:"
    echo "   net start postgresql-x64-13"
    echo "   # or check Windows Services"
    echo ""
    echo "Option 3: Use Docker run command"
    echo "   docker run --name postgres-crypto -e POSTGRES_PASSWORD=admin123 -p 5433:5432 -d postgres:13"
    echo ""
elif [ -n "$port_5432_check" ] && [ -z "$port_check" ]; then
    echo "🔧 PostgreSQL is running on default port 5432, but we need 5433"
    echo ""
    echo "Option 1: Change .env file to use port 5432"
    echo "   DATABASE_URL=postgresql://postgres:admin123@localhost:5432/cryptopredict"
    echo ""
    echo "Option 2: Start PostgreSQL on port 5433"
    echo "   docker run --name postgres-crypto -e POSTGRES_PASSWORD=admin123 -p 5433:5432 -d postgres:13"
    echo ""
elif [ -n "$docker_containers" ]; then
    echo "✅ PostgreSQL Docker container is running"
    echo "🔧 Check if it's on the correct port mapping"
else
    echo "🔧 Mixed situation - check specific containers and ports"
fi

echo ""
echo "📋 Step 6: Quick connection test..."

# Test both ports
echo "Testing connection to localhost:5433..."
if timeout 3 bash -c "</dev/tcp/localhost/5433" 2>/dev/null; then
    echo "✅ Port 5433 is accessible"
else
    echo "❌ Port 5433 is not accessible"
fi

echo "Testing connection to localhost:5432..."
if timeout 3 bash -c "</dev/tcp/localhost/5432" 2>/dev/null; then
    echo "✅ Port 5432 is accessible"
else
    echo "❌ Port 5432 is not accessible"
fi