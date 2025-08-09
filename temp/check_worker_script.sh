#!/bin/bash
# temp/check_worker_script.sh
# Analyze the worker startup script to find why workers stop

echo "🔍 Worker Script Analysis"
echo "========================="

echo ""
echo "📋 Step 1: Checking run-workers-simple-kill-all.sh..."

if [ -f "scripts/run-workers-simple-kill-all.sh" ]; then
    echo "✅ Found worker script"
    echo ""
    
    echo "🔍 Looking for worker start commands..."
    grep -n -A5 -B5 "worker" scripts/run-workers-simple-kill-all.sh
    
    echo ""
    echo "🔍 Looking for timeout or kill commands..."
    grep -n -i -A3 -B3 "timeout\|kill\|stop" scripts/run-workers-simple-kill-all.sh
    
else
    echo "❌ Worker script not found"
fi

echo ""
echo "📋 Step 2: Checking for log files..."

# Look for any worker logs
echo "🔍 Searching for worker log files..."
find . -name "*worker*.log" -o -name "*celery*.log" -o -name "*.log" | grep -v ".git" | head -10

echo ""
echo "📋 Step 3: Checking running processes..."

echo "🔍 Current Python processes:"
ps aux | grep python | grep -v grep

echo ""
echo "🔍 Current Celery processes:"
ps aux | grep celery | grep -v grep

echo ""
echo "📋 Step 4: Analyzing worker configuration..."

echo "🔍 Checking celery configuration..."
cd backend
python -c "
from app.tasks.celery_app import celery_app
print('Worker Pool:', celery_app.conf.get('worker_pool', 'default'))
print('Worker Max Tasks Per Child:', celery_app.conf.get('worker_max_tasks_per_child', 'unlimited'))
print('Worker Prefetch Multiplier:', celery_app.conf.get('worker_prefetch_multiplier', 4))
print('Task Time Limit:', celery_app.conf.get('task_time_limit', 'unlimited'))
print('Task Soft Time Limit:', celery_app.conf.get('task_soft_time_limit', 'unlimited'))
"

echo ""
echo "📋 Step 5: Quick worker start/stop test..."

echo "🧪 Starting worker for 5 seconds to see behavior..."
cd backend

# Start worker in background and capture PID
python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --queue=price_data \
    --pool=solo &

worker_pid=$!
echo "🚀 Worker started with PID: $worker_pid"

# Wait 5 seconds
sleep 5

# Check if still running
if kill -0 $worker_pid 2>/dev/null; then
    echo "✅ Worker is still running after 5 seconds"
    # Kill it gracefully
    kill $worker_pid
    wait $worker_pid 2>/dev/null
    echo "🛑 Worker stopped gracefully"
else
    echo "❌ Worker stopped on its own within 5 seconds"
    echo "🔍 This indicates the worker is crashing or exiting early"
fi

echo ""
echo "📋 Analysis Summary:"
echo "==================="

echo ""
echo "If workers are stopping immediately, possible causes:"
echo "1. 🔧 Script kills workers too quickly"
echo "2. 🔧 Workers exit when no tasks are available"
echo "3. 🔧 Configuration issues in celery_config"
echo "4. 🔧 Memory or resource limits"
echo "5. 🔧 Pool configuration problems"
echo ""
echo "🚀 Solutions to try:"
echo "   • Modify script to keep workers alive longer"
echo "   • Add a simple keepalive task"
echo "   • Change worker pool from 'solo' to 'threads'"
echo "   • Increase worker startup delay"