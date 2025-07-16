#!/bin/bash
# File: scripts/start-frontend.sh
# Start frontend script for Git Bash

set -e

echo "⚛️ Starting Next.js Frontend..."
echo "==============================="

# Check if we're in the right directory
if [ ! -d "frontend" ]; then
    echo "❌ Frontend directory not found! Please run from project root."
    exit 1
fi

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ node_modules not found!"
    echo "Installing dependencies..."
    npm install
fi

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found!"
    echo "Please run: ./scripts/quick-setup.sh first"
    exit 1
fi

# Set environment variables
echo "🔧 Setting environment variables..."
export NEXT_PUBLIC_API_URL="http://localhost:8000"
export NEXT_PUBLIC_WS_URL="ws://localhost:8000"
export NODE_ENV="development"

echo ""
echo "🚀 Frontend starting at: http://localhost:3000"
echo "🔗 API endpoint: http://localhost:8000"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Start Next.js
npm run dev