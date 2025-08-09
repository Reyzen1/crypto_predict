#!/bin/bash
# temp/quick_worker_test.sh
# Quick test to see why workers stop

echo "⚡ Quick Worker Test"
echo "==================="

cd backend

echo "📋 Test 1: Start one worker and monitor for 10 seconds..."
echo ""

# Start worker in background
python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --queue=price_data \
    --pool=threads \
    --without-heartbeat \
    --without-mingle \
    --without-gossip &

worker_pid=$!
echo "🚀 Worker started with PID: $worker_pid"

# Monitor for 10 seconds
for i in {1..10}; do
    sleep 1
    if kill -0 $worker_pid 2>/dev/null; then
        echo "⏱️ Second $i: Worker running"
    else
        echo "❌ Second $i: Worker stopped!"
        break
    fi
done

# Clean up if still running
if kill -0 $worker_pid 2>/dev/null; then
    echo "✅ Worker survived 10 seconds - killing gracefully"
    kill $worker_pid
    wait $worker_pid 2>/dev/null
else
    echo "❌ Worker stopped on its own"
fi

echo ""
echo "📋 Test 2: Queue a simple task and see if worker processes it..."
echo ""

# Start worker in background again
python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --queue=price_data \
    --pool=threads &

worker_pid=$!
echo "🚀 Worker started with PID: $worker_pid"

# Wait a moment for worker to start
sleep 3

# Queue a test task
echo "📤 Queuing test task..."
python -c "
from app.tasks.celery_app import debug_task
result = debug_task.delay()
print(f'Task ID: {result.id}')

import time
time.sleep(5)

try:
    task_result = result.get(timeout=10)
    print(f'✅ Task result: {task_result}')
except Exception as e:
    print(f'❌ Task failed: {e}')
"

# Check worker status
if kill -0 $worker_pid 2>/dev/null; then
    echo "✅ Worker still running after task"
    kill $worker_pid
    wait $worker_pid 2>/dev/null
else
    echo "❌ Worker stopped after task"
fi

echo ""
echo "📋 Test 3: Check what happens with empty queue..."
echo ""

echo "🧪 Starting worker with empty queue..."
timeout 5s python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --queue=price_data \
    --pool=threads

exit_code=$?

echo ""
echo "Exit code: $exit_code"

case $exit_code in
    0)
        echo "✅ Worker exited normally"
        ;;
    124)
        echo "✅ Worker was running (killed by timeout)"
        ;;
    *)
        echo "❌ Worker had issues (exit code: $exit_code)"
        ;;
esac

echo ""
echo "📊 Summary:"
echo "==========="

if [ $exit_code -eq 124 ] || [ $exit_code -eq 0 ]; then
    echo "✅ Workers can start and run properly"
    echo "🔧 Issue is likely in the startup script"
    echo ""
    echo "🚀 Solutions:"
    echo "   1. Use improved worker script"
    echo "   2. Add background startup"
    echo "   3. Modify original script timeout"
    echo ""
    echo "📝 Try the improved script:"
    echo "   chmod +x temp/run_workers_improved.sh"
    echo "   ./temp/run_workers_improved.sh"
else
    echo "❌ Workers have startup issues"
    echo "🔍 Need to investigate error messages above"
fi