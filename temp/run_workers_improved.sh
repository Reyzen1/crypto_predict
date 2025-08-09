#!/bin/bash
# temp/run_workers_fixed.sh
# Fixed worker script with correct Celery parameters

echo "🚀 Fixed Celery Workers Start"
echo "============================="

# Kill any existing workers first
echo "🛑 Stopping existing workers..."
pkill -f "celery.*worker" 2>/dev/null || true
sleep 2

# Change to backend directory
cd backend

echo ""
echo "📋 Starting workers with correct parameters..."

# Start workers with FIXED parameters
echo "🔧 Worker 1: Price Data (threads pool for async compatibility)"
python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=price_data \
    --pool=threads \
    --hostname=price_worker@%h \
    --max-tasks-per-child=1000 \
    --time-limit=300 \
    --soft-time-limit=240 &

price_worker_pid=$!
echo "✅ Price worker started with PID: $price_worker_pid"

sleep 3

echo ""
echo "🔧 Worker 2: ML Processing (solo pool)"
python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --queues=ml_processing \
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
    --queues=scheduling \
    --pool=threads \
    --hostname=scheduling_worker@%h \
    --max-tasks-per-child=1000 &

scheduling_worker_pid=$!
echo "✅ Scheduling worker started with PID: $scheduling_worker_pid"

sleep 3

echo ""
echo "🔧 Worker 4: General (threads pool)"
python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --queues=default \
    --pool=threads \
    --hostname=general_worker@%h \
    --max-tasks-per-child=1000 &

general_worker_pid=$!
echo "✅ General worker started with PID: $general_worker_pid"

# Wait for all workers to start
echo ""
echo "⏱️ Waiting 10 seconds for workers to fully initialize..."
sleep 10

echo ""
echo "📊 Checking worker status..."

workers_running=0

# Check each worker
if kill -0 $price_worker_pid 2>/dev/null; then
    echo "✅ Price worker (PID: $price_worker_pid): Running"
    workers_running=$((workers_running + 1))
else
    echo "❌ Price worker: Stopped"
fi

if kill -0 $ml_worker_pid 2>/dev/null; then
    echo "✅ ML worker (PID: $ml_worker_pid): Running"
    workers_running=$((workers_running + 1))
else
    echo "❌ ML worker: Stopped"
fi

if kill -0 $scheduling_worker_pid 2>/dev/null; then
    echo "✅ Scheduling worker (PID: $scheduling_worker_pid): Running"
    workers_running=$((workers_running + 1))
else
    echo "❌ Scheduling worker: Stopped"
fi

if kill -0 $general_worker_pid 2>/dev/null; then
    echo "✅ General worker (PID: $general_worker_pid): Running"
    workers_running=$((workers_running + 1))
else
    echo "❌ General worker: Stopped"
fi

echo ""
echo "📈 Workers running: $workers_running/4"

if [ $workers_running -eq 4 ]; then
    echo "🎉 ALL WORKERS RUNNING SUCCESSFULLY!"
    
    echo ""
    echo "🧪 Testing with a simple task..."
    
    # Test with debug task
    python -c "
try:
    from app.tasks.celery_app import debug_task
    result = debug_task.delay()
    print(f'✅ Test task queued: {result.id}')
    print('⏱️ Waiting 5 seconds for result...')
    
    import time
    time.sleep(5)
    
    try:
        task_result = result.get(timeout=10)
        print(f'✅ Task completed: {task_result}')
    except Exception as e:
        print(f'⚠️ Task timeout or error: {e}')
        
except Exception as e:
    print(f'❌ Test task failed: {e}')
"
    
    echo ""
    echo "🧪 Testing price collection task..."
    python -c "
try:
    from app.tasks.price_collector import sync_all_prices
    result = sync_all_prices.delay()
    print(f'✅ Price sync task queued: {result.id}')
    print('⏱️ This task will run in background...')
except Exception as e:
    print(f'❌ Price task failed: {e}')
"

elif [ $workers_running -gt 0 ]; then
    echo "⚠️ Some workers running, some stopped"
    echo "🔧 Partial success - check logs for stopped workers"
else
    echo "❌ All workers stopped"
    echo "🔍 Check error messages above"
fi

echo ""
echo "📋 Current worker processes:"
ps aux | grep -E "(celery.*worker)" | grep -v grep | head -10

echo ""
echo "💾 Worker PIDs saved for management:"
echo "Price: $price_worker_pid, ML: $ml_worker_pid, Scheduling: $scheduling_worker_pid, General: $general_worker_pid"

# Save PIDs to file for easy cleanup
echo "$price_worker_pid $ml_worker_pid $scheduling_worker_pid $general_worker_pid" > /tmp/celery_worker_pids.txt

echo ""
echo "🔧 To stop all workers manually:"
echo "   kill $price_worker_pid $ml_worker_pid $scheduling_worker_pid $general_worker_pid"
echo "   # or run: pkill -f 'celery.*worker'"

echo ""
echo "✅ Fixed worker startup completed!"
echo "🌐 Flower should be accessible at: http://localhost:5555"

# Final status
if [ $workers_running -eq 4 ]; then
    echo ""
    echo "🎉 SUCCESS: All 4 workers are running!"
    echo "🚀 Your CryptoPredict system is now fully operational!"
    echo ""
    echo "📋 What's running:"
    echo "   ✅ 4 Celery Workers (Price, ML, Scheduling, General)"
    echo "   ✅ Beat Scheduler (if started separately)"  
    echo "   ✅ Flower Monitor (if started separately)"
    echo ""
    echo "📈 Tasks will now be processed automatically every 5 minutes"
fi