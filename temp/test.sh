#!/bin/bash

# Fix Celery Rate Limit Issues
# Celery only supports: s (second), m (minute), h (hour)

echo "🔧 Fixing Celery Rate Limit Configuration..."
echo "=================================="

# Navigate to backend directory
cd backend

# Backup current config
cp app/core/celery_config.py app/core/celery_config.py.backup
echo "💾 Backup created: celery_config.py.backup"

# Fix rate limits using sed
echo "🔍 Converting unsupported rate limit formats..."

# Convert 1/d to 1/24h (once per day = once per 24 hours)
sed -i 's/"rate_limit": *"1\/d"/"rate_limit": "1\/24h"/g' app/core/celery_config.py

# Convert any other /d patterns to /24h
sed -i 's/"rate_limit": *"\([0-9]*\)\/d"/"rate_limit": "\1\/24h"/g' app/core/celery_config.py

# Convert weekly patterns if they exist
sed -i 's/"rate_limit": *"1\/w"/"rate_limit": "1\/168h"/g' app/core/celery_config.py

echo "✅ Rate limit conversions completed:"
echo "   • 1/d → 1/24h (once per day)"
echo "   • 1/w → 1/168h (once per week)"

# Show the current rate limits in the config
echo ""
echo "📋 Current rate limits in config:"
grep -n "rate_limit" app/core/celery_config.py | head -10

echo ""
echo "🚀 Testing worker startup..."
echo "Starting price worker to test configuration..."

# Test with a quick worker startup
timeout 10s python -m celery -A app.tasks.celery_app worker --queues=price_data --pool=threads --loglevel=info &
WORKER_PID=$!

sleep 5

if kill -0 $WORKER_PID 2>/dev/null; then
    echo "✅ Worker started successfully!"
    kill $WORKER_PID
    wait $WORKER_PID 2>/dev/null
else
    echo "❌ Worker failed to start"
fi

echo ""
echo "🎯 Manual commands to run workers:"
echo "Price worker:"
echo "  python -m celery -A app.tasks.celery_app worker --queues=price_data --pool=threads"
echo ""
echo "General worker:"
echo "  python -m celery -A app.tasks.celery_app worker --queues=general --pool=threads"