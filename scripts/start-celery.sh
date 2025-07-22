#!/bin/bash
# scripts/start-celery.sh
# Celery worker and beat startup script

echo "🚀 Starting Celery Workers and Beat Scheduler"
echo "============================================="

cd backend

echo ""
echo "📋 Step 1: Environment Check"
echo "----------------------------"
echo "Current directory: $(pwd)"
echo "Python path: $(which python)"

# Check if Redis is running
echo ""
echo "📋 Step 2: Redis Connection Check"
echo "---------------------------------"
python -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print('✅ Redis is running and accessible')
except Exception as e:
    print('❌ Redis connection failed: ' + str(e))
    print('Please start Redis: docker-compose up redis')
    exit(1)
"

# Test Celery configuration
echo ""
echo "📋 Step 3: Celery Configuration Test"
echo "------------------------------------"
python -c "
try:
    from app.tasks.celery_app import celery_app
    print('✅ Celery app imported successfully')
    print('   Broker: ' + celery_app.conf.broker_url)
    print('   Backend: ' + celery_app.conf.result_backend)
    
    # Test basic task
    from app.tasks.celery_app import health_check
    print('✅ Health check task available')
    
except Exception as e:
    print('❌ Celery configuration failed: ' + str(e))
    import traceback
    traceback.print_exc()
    exit(1)
"

echo ""
echo "📋 Step 4: Starting Celery Services"
echo "-----------------------------------"

# Function to start Celery worker in background
start_worker() {
    echo "Starting Celery Worker..."
    celery -A app.tasks.celery_app worker --loglevel=info --pool=solo &
    WORKER_PID=$!
    echo "✅ Celery Worker started (PID: $WORKER_PID)"
}

# Function to start Celery beat scheduler in background  
start_beat() {
    echo "Starting Celery Beat Scheduler..."
    celery -A app.tasks.celery_app beat --loglevel=info &
    BEAT_PID=$!
    echo "✅ Celery Beat started (PID: $BEAT_PID)"
}

# Function to start Celery flower monitoring (optional)
start_flower() {
    echo "Starting Celery Flower Monitoring..."
    celery -A app.tasks.celery_app flower --port=5555 &
    FLOWER_PID=$!
    echo "✅ Celery Flower started (PID: $FLOWER_PID)"
    echo "   Monitor at: http://localhost:5555"
}

# Start services
start_worker
sleep 2
start_beat
sleep 2

# Ask if user wants Flower monitoring
read -p "Start Celery Flower monitoring? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    start_flower
fi

echo ""
echo "🎉 CELERY SERVICES STARTED!"
echo "=========================="
echo ""
echo "📊 Running Services:"
echo "  ✅ Celery Worker (PID: $WORKER_PID)"
echo "  ✅ Celery Beat Scheduler (PID: $BEAT_PID)"
if [[ $FLOWER_PID ]]; then
    echo "  ✅ Celery Flower Monitor (PID: $FLOWER_PID)"
fi

echo ""
echo "📋 Scheduled Tasks:"
echo "  🔄 sync_all_prices - Every 5 minutes"
echo "  🔄 sync_historical_data - Every hour"  
echo "  🔄 discover_new_cryptocurrencies - Daily at 2 AM"
echo "  🔄 cleanup_old_data - Weekly on Sunday at 3 AM"

echo ""
echo "🔧 Management Commands:"
echo "  Test task: python -c \"from app.tasks.celery_app import health_check; print(health_check.delay().get())\""
echo "  Stop worker: kill $WORKER_PID"
echo "  Stop beat: kill $BEAT_PID"
if [[ $FLOWER_PID ]]; then
    echo "  Stop flower: kill $FLOWER_PID"
fi

echo ""
echo "💡 Tips:"
echo "  - Monitor logs for task execution"
echo "  - Use Flower UI for task monitoring"
echo "  - Check Redis for task queues"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep script running to monitor processes
trap 'echo "Stopping Celery services..."; kill $WORKER_PID $BEAT_PID $FLOWER_PID 2>/dev/null; exit' INT

# Wait for processes
wait