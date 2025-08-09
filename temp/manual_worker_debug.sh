#!/bin/bash
# temp/run_workers_improved.sh
# Improved worker script with better configuration for our async setup

echo "🚀 Improved Celery Workers Start"
echo "================================"

# Kill any existing workers first
echo "🛑 Stopping existing workers..."
pkill -f "celery.*worker" 2>/dev/null || true
sleep 2

# Change to backend directory
cd backend

echo ""
echo "📋 Starting improved workers configuration..."

# Start workers with improved settings
echo "🔧 Worker 1: Price Data (threads pool for async compatibility)"
python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queue=price_data \
    --pool=threads \
    --hostname=price_worker@%h \
    --max-tasks-per-child=1000 \
    --time-limit=300 \
    --soft-time-limit=240 &

price_worker_pid=$!
echo "✅ Price worker started with PID: $price_worker_pid"

sleep 3

echo ""
echo "🔧 Worker 2: ML Processing (solo pool for debugging)"
python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --queue=ml_processing \
    --pool=solo \
    --hostname=ml_worker@%h \
    --max-tasks-per-child=500 &

ml_worker_pid=$!
echo "✅ ML worker started with PID: $ml_worker_pid"

sleep 3

echo ""
echo "🔧 Worker 3: Scheduling (threads pool)"
python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --queue=scheduling \
    --pool=threads \
    --hostname=scheduling_worker@%h \
    --max-tasks-per-child=1000 &

scheduling_worker_pid=$!
echo "✅ Scheduling worker started with PID: $scheduling_worker_pid"

sleep 3

echo ""
echo "🔧 Worker 4: General (threads pool)"
python -m ce