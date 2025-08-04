#!/bin/bash
# File: start-frontend-local.sh
# Start frontend development server

echo "⚛️ Starting Frontend Development Server"
echo "======================================="

cd frontend

echo "📍 Frontend URL: http://localhost:3000"
echo "🔄 Hot reload enabled"
echo ""

# Start Next.js development server
npm run dev
