#!/bin/bash
# File: temp/manual-start.sh
# Manual worker starter with real-time monitoring

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
print_header() { echo -e "${PURPLE}$1${NC}"; }

echo -e "${PURPLE}🚀 Manual Worker Starter & Monitor${NC}"
echo "===================================="
echo

# Cleanup first
print_info "🧹 Cleaning up any existing processes..."
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true
pkill -f "celery.*flower" 2>/dev/null || true
sleep 2
print_success "Cleanup completed"
echo

# Ensure directories exist
mkdir -p scripts/logs/pids
mkdir -p scripts/logs

# Function to start a worker and monitor it
start_and_monitor_worker() {
    local worker_name=$1
    local queues=$2
    local log_file="scripts/logs/${worker_name}_solo.log"
    local pid_file="scripts/logs/pids/${worker_name}_solo.pid"
    
    print_header "🔧 Starting $worker_name"
    print_info "   Queues: $queues"
    print_info "   Log: $log_file"
    print_info "   PID: $pid_file"
    
    # Clear old log
    > "$log_file"
    
    # Change to backend directory
    cd backend
    
    # Start worker in background
    echo "⏳ Launching worker..."
    python -m celery -A app.tasks.celery_app worker \
        --loglevel=info \
        --queues="$queues" \
        --hostname="${worker_name}@%h" \
        --pool=solo \
        --concurrency=1 \
        --prefetch-multiplier=1 \
        --max-tasks-per-child=50 \
        --time-limit=300 \
        --soft-time-limit=240 \
        > "../$log_file" 2>&1 &
    
    local pid=$!
    echo "$pid" > "../$pid_file"
    
    cd ..
    
    print_info "   ⏳ PID: $pid - Waiting for startup..."
    
    # Monitor startup for 10 seconds
    local timeout=10
    local success=false
    
    while [ $timeout -gt 0 ]; do
        if ps -p $pid > /dev/null 2>&1; then
            # Check if worker is ready
            if [ -f "$log_file" ] && grep -q "ready" "$log_file" 2>/dev/null; then
                print_success "   🎉 $worker_name is READY (PID: $pid)"
                success=true
                break
            elif [ -f "$log_file" ] && grep -q "ERROR\|CRITICAL\|Traceback" "$log_file" 2>/dev/null; then
                print_error "   💥 $worker_name failed with errors:"
                tail -3 "$log_file" | sed 's/^/      /'
                break
            else
                echo "   ⏳ Still starting... ($timeout seconds left)"
            fi
        else
            print_error "   💀 Process $pid died"
            break
        fi
        
        sleep 1
        ((timeout--))
    done
    
    if [ "$success" = false ] && ps -p $pid > /dev/null 2>&1; then
        print_warning "   ⚠️  $worker_name started but not ready yet"
        print_info "   📋 Recent log output:"
        if [ -f "$log_file" ]; then
            tail -5 "$log_file" | sed 's/^/      /'
        fi
    fi
    
    echo ""
    return 0
}

# Function to start system service
start_service() {
    local service_name=$1
    local cmd=$2
    local log_file="scripts/logs/${service_name}.log"
    local pid_file="scripts/logs/pids/${service_name}.pid"
    
    print_header "🔧 Starting $service_name"
    print_info "   Command: $cmd"
    print_info "   Log: $log_file"
    
    # Clear old log
    > "$log_file"
    
    cd backend
    
    # Start service
    echo "⏳ Launching $service_name..."
    eval "$cmd > '../$log_file' 2>&1 &"
    local pid=$!
    echo "$pid" > "../$pid_file"
    
    cd ..
    
    print_info "   ⏳ PID: $pid - Waiting for startup..."
    
    sleep 3
    
    if ps -p $pid > /dev/null 2>&1; then
        print_success "   🎉 $service_name started (PID: $pid)"
    else
        print_error "   💀 $service_name failed to start"
        if [ -f "$log_file" ]; then
            print_error "   📋 Error log:"
            tail -3 "$log_file" | sed 's/^/      /'
        fi
    fi
    
    echo ""
    return 0
}

# Check environment first
print_info "🔍 Pre-flight checks..."

# Check Redis
cd backend
if python -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping(); print('Redis OK')" 2>/dev/null; then
    print_success "Redis connection verified"
else
    print_error "Redis connection failed!"
    print_info "Please start Redis: docker-compose up redis -d"
    exit 1
fi
cd ..

# Check celery app
cd backend
if python -c "from app.tasks.celery_app import app; print('Celery app OK')" 2>/dev/null; then
    print_success "Celery app configuration verified"
else
    print_error "Celery app configuration failed!"
    exit 1
fi
cd ..

echo ""
print_header "🚀 Starting Workers One by One"
echo "==============================="
echo

# Start workers with monitoring
start_and_monitor_worker "data_worker" "price_data,market_data,data_sync"
start_and_monitor_worker "ml_worker" "ml_prediction,model_training,ml_tasks"
start_and_monitor_worker "notification_worker" "notifications,alerts,email_tasks"
start_and_monitor_worker "general_worker" "general,cleanup,maintenance,default"

# Start system services
start_service "celery_beat" "python -m celery -A app.tasks.celery_app beat --loglevel=info --schedule=../scripts/logs/celerybeat-schedule"

start_service "celery_flower" "python -m celery -A app.tasks.celery_app flower --port=5555 --basic_auth=admin:cryptopredict123"

# Final status check
print_header "📊 Final Status Check"
echo "====================="
echo

print_info "🔍 Running processes:"
ps aux 2>/dev/null | grep -E "(celery|worker)" | grep -v grep | while read line; do
    echo "   $line"
done

echo ""
print_info "📁 PID files created:"
for pid_file in scripts/logs/pids/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file" 2>/dev/null)
        name=$(basename "$pid_file" .pid)
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "   ✅ $name: $pid (running)"
        else
            echo "   ❌ $name: $pid (dead)"
        fi
    fi
done

echo ""
print_success "🎉 Manual startup completed!"
print_info "💡 Now try: ./scripts/run-workers-win.sh status"