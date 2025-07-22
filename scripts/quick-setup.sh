#!/bin/bash
# File: scripts/quick-setup.sh
# Super simple setup script for Git Bash/MINGW64

set -e

echo "🚀 CryptoPredict MVP Quick Setup"
echo "================================"

# Check if we're in the right directory
if [ ! -f "docker-compose-backend.yml" ]; then
    echo "❌ docker-compose-backend.yml not found!"
    echo "Please run from project root directory."
    exit 1
fi

# Step 1: Start databases
echo "📦 Starting databases..."
docker-compose -f docker-compose-backend.yml up -d postgres redis

# Step 2: Wait for databases
echo "⏳ Waiting for databases (30 seconds)..."
sleep 30

# Step 3: Check if databases are ready
echo "✅ Checking PostgreSQL..."
max_attempts=10
for i in $(seq 1 $max_attempts); do
    if docker-compose -f docker-compose-backend.yml exec postgres pg_isready -U postgres -d cryptopredict > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready!"
        break
    else
        if [ $i -eq $max_attempts ]; then
            echo "❌ PostgreSQL not ready after $max_attempts attempts, but continuing..."
        else
            echo "⏳ PostgreSQL not ready, waiting... (attempt $i/$max_attempts)"
            sleep 3
        fi
    fi
done

echo "✅ Checking Redis..."
for i in $(seq 1 $max_attempts); do
    if docker-compose -f docker-compose-backend.yml exec redis redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis is ready!"
        break
    else
        if [ $i -eq $max_attempts ]; then
            echo "❌ Redis not ready after $max_attempts attempts, but continuing..."
        else
            echo "⏳ Redis not ready, waiting... (attempt $i/$max_attempts)"
            sleep 3
        fi
    fi
done

# Step 4: Setup Python backend
echo "🐍 Setting up Python backend..."
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found!"
    exit 1
fi

cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    if command -v python3.12 &> /dev/null; then
        python3.12 -m venv venv
    elif command -v python3 &> /dev/null; then
        python3 -m venv venv
    elif command -v py &> /dev/null; then
        py -3.12 -m venv venv || py -3 -m venv venv
    else
        python -m venv venv
    fi
fi

# Activate and install packages
echo "Installing Python packages..."
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt

cd ..

# Step 5: Setup frontend
echo "⚛️ Setting up frontend..."
if [ ! -d "frontend" ]; then
    echo "❌ Frontend directory not found!"
    exit 1
fi

cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js packages..."
    npm install
fi

cd ..

# Step 6: Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x scripts/*.sh

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Now you can start the services:"
echo ""
echo "Terminal 1 (Backend):"
echo "  ./scripts/start-backend.sh"
echo ""
echo "Terminal 2 (Frontend):"
echo "  ./scripts/start-frontend.sh"
echo ""
echo "🌐 URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "🛑 To stop databases:"
echo "  ./scripts/stop-db.sh"