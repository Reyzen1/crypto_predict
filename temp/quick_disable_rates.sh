#!/bin/bash
# temp/quick_disable_rates.sh  
# Quick fix: disable rate limits entirely

echo "⚡ Quick Rate Limit Disable"
echo "=========================="

cd backend

echo "📋 Backing up config..."
cp app/core/celery_config.py app/core/celery_config.py.backup
echo "✅ Backup created"

echo ""
echo "📋 Disabling rate limits..."

# Simple sed replacement to disable rate limits
sed -i 's/worker_disable_rate_limits: bool = False/worker_disable_rate_limits: bool = True  # DISABLED/g' app/core/celery_config.py

echo "✅ Rate limits disabled"

echo ""
echo "📋 Testing worker..."

timeout 5s python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --queues=price_data \
    --pool=threads

exit_code=$?

echo ""
if [ $exit_code -eq 124 ] || [ $exit_code -eq 0 ]; then
    echo "🎉 SUCCESS! Worker can run without rate limits"
    echo "✅ Rate limit disable worked"
    echo ""
    echo "🚀 Now run: ./temp/run_workers_fixed.sh"
else
    echo "❌ Still has issues (exit code: $exit_code)"
    echo "🔧 Restoring backup..."
    cp app/core/celery_config.py.backup app/core/celery_config.py
fi