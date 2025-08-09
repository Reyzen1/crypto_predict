#!/bin/bash
# File: scripts/run-workers-simple-kill-all.sh  
# Simple, no-frills restart of Beat and Flower

echo "🚀 Simple Beat & Flower Restart"
echo "==============================="
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

# Check environment
if [ ! -d "backend" ]; then
    print_error "Please run from project root directory"
    exit 1
fi

# Setup
mkdir -p scripts/logs/pids
LOG_DIR="scripts/logs"
PID_DIR="$LOG_DIR/pids"

# Step 1: Complete cleanup
print_info "1️⃣ Complete cleanup..."

# Kill everything
pkill -f "celery" 2>/dev/null || true

# Clean PID files
rm -f "$PID_DIR"/*.pid 2>/dev/null || true

# Clean logs
> "$LOG_DIR/celery_beat.log"
> "$LOG_DIR/celery_flower.log"

sleep 5
print_success "Cleanup completed"

# Step 2: Start workers first (simple method)
print_info "2️⃣ Starting workers..."

cd backend

# Start workers one by one with simple commands
echo "Starting data worker..."
nohup python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --queues=price_data,market_data,data_sync \
    --hostname=data_worker@%h \
    --pool=solo \
    --concurrency=1 \
    > "../$LOG_DIR/data_worker_simple.log" 2>&1 &
echo $! > "../$PID_DIR/data_worker_solo.pid"

sleep 3

echo "Starting ml worker..."
nohup python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --queues=ml_prediction,model_training,ml_tasks \
    --hostname=ml_worker@%h \
    --pool=solo \
    --concurrency=1 \
    > "../$LOG_DIR/ml_worker_simple.log" 2>&1 &
echo $! > "../$PID_DIR/ml_worker_solo.pid"

sleep 3

echo "Starting notification worker..."
nohup python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --queues=notifications,alerts,email_tasks \
    --hostname=notification_worker@%h \
    --pool=solo \
    --concurrency=1 \
    > "../$LOG_DIR/notification_worker_simple.log" 2>&1 &
echo $! > "../$PID_DIR/notification_worker_solo.pid"

sleep 3

echo "Starting general worker..."
nohup python -m celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --queues=general,cleanup,maintenance,default \
    --hostname=general_worker@%h \
    --pool=solo \
    --concurrency=1 \
    > "../$LOG_DIR/general_worker_simple.log" 2>&1 &
echo $! > "../$PID_DIR/general_worker_solo.pid"

cd ..

print_success "Workers started"

# Step 3: Start Beat (super simple)
print_info "3️⃣ Starting Beat Scheduler..."

cd backend

# Remove any existing beat files
rm -f celerybeat-schedule* 2>/dev/null || true
rm -f ../scripts/logs/celerybeat-schedule* 2>/dev/null || true

echo "Starting Beat..."
nohup python -m celery -A app.tasks.celery_app beat \
    --loglevel=info \
    > "../$LOG_DIR/celery_beat.log" 2>&1 &

BEAT_PID=$!
echo "$BEAT_PID" > "../$PID_DIR/celery_beat.pid"

cd ..

print_info "Beat started with PID: $BEAT_PID"

# Check Beat after 10 seconds
sleep 10
if ps -p "$BEAT_PID" > /dev/null 2>&1; then
    print_success "Beat is running successfully"
else
    print_warning "Beat may have stopped - check logs"
    echo "Beat log:"
    tail -5 "$LOG_DIR/celery_beat.log" | sed 's/^/  /'
fi

# Step 4: Start Flower (super simple)
print_info "4️⃣ Starting Flower Monitor..."

cd backend

echo "Starting Flower..."
nohup python -m celery -A app.tasks.celery_app flower \
    --port=5555 \
    --basic_auth=admin:cryptopredict123 \
    > "../$LOG_DIR/celery_flower.log" 2>&1 &

FLOWER_PID=$!
echo "$FLOWER_PID" > "../$PID_DIR/celery_flower.pid"

cd ..

print_info "Flower started with PID: $FLOWER_PID"

# Check Flower after 10 seconds
sleep 10
if ps -p "$FLOWER_PID" > /dev/null 2>&1; then
    print_success "Flower is running successfully"
    print_info "🌐 Access at: http://localhost:5555"
    print_info "🔐 Login: admin / cryptopredict123"
else
    print_warning "Flower may have stopped - check logs"
    echo "Flower log:"
    tail -5 "$LOG_DIR/celery_flower.log" | sed 's/^/  /'
fi

# Step 5: Final status check
echo
print_info "5️⃣ Final Status Check..."

echo "Process Summary:"
workers_running=0
for worker in data_worker ml_worker notification_worker general_worker; do
    pid_file="$PID_DIR/${worker}_solo.pid"
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "  ✅ $worker: Running (PID: $pid)"
            ((workers_running++))
        else
            echo "  ❌ $worker: Stopped"
        fi
    else
        echo "  ⚠️  $worker: No PID file"
    fi
done

# Check Beat
if ps -p "$BEAT_PID" > /dev/null 2>&1; then
    echo "  ✅ Beat Scheduler: Running (PID: $BEAT_PID)"
    beat_running=1
else
    echo "  ❌ Beat Scheduler: Stopped"
    beat_running=0
fi

# Check Flower
if ps -p "$FLOWER_PID" > /dev/null 2>&1; then
    echo "  ✅ Flower Monitor: Running (PID: $FLOWER_PID)"
    flower_running=1
else
    echo "  ❌ Flower Monitor: Stopped"
    flower_running=0
fi

echo
echo "Summary:"
echo "  Workers: $workers_running/4 running"
echo "  Beat: $([ $beat_running -eq 1 ] && echo "✅" || echo "❌")"
echo "  Flower: $([ $flower_running -eq 1 ] && echo "✅" || echo "❌")"

if [ $workers_running -eq 4 ] && [ $beat_running -eq 1 ] && [ $flower_running -eq 1 ]; then
    print_success "🎉 All services are running!"
    echo
    print_info "Test with: ./scripts/run-workers.sh status"
    print_info "Access Flower: http://localhost:5555"
else
    print_warning "Some services may need attention"
    echo
    print_info "Check individual log files in scripts/logs/"
fi