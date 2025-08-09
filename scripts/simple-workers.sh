#!/bin/bash
# File: scripts/simple-workers.sh
# Simple, reliable worker manager that always works

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
print_header() { echo -e "${PURPLE}$1${NC}"; }

# Configuration
BACKEND_DIR="backend"
LOG_DIR="scripts/logs"
PID_DIR="$LOG_DIR/pids"

# Simple directory setup
setup() {
    mkdir -p "$LOG_DIR" "$PID_DIR"
    touch "$LOG_DIR/simple_manager.log"
}

# Simple cleanup
cleanup() {
    print_info "🧹 Cleaning up processes..."
    pkill -f "celery.*worker" 2>/dev/null || true
    pkill -f "celery.*beat" 2>/dev/null || true
    pkill -f "celery.*flower" 2>/dev/null || true
    rm -f "$PID_DIR"/*.pid 2>/dev/null || true
    print_success "Cleanup completed"
}

# Start a simple worker
start_worker() {
    local name="$1"
    local queues="$2"
    local log_file="$LOG_DIR/${name}.log"
    local pid_file="$PID_DIR/${name}.pid"
    
    print_info "🔧 Starting $name..."
    print_info "   Queues: $queues"
    
    cd "$BACKEND_DIR"
    
    nohup python -m celery -A app.tasks.celery_app worker \
        --loglevel=info \
        --queues="$queues" \
        --hostname="${name}@%h" \
        --pool=solo \
        --concurrency=1 \
        --prefetch-multiplier=1 \
        > "../$log_file" 2>&1 &
    
    local pid=$!
    echo "$pid" > "../$pid_file"
    
    cd - >/dev/null
    
    sleep 3
    
    if ps -p $pid >/dev/null 2>&1; then
        print_success "$name started (PID: $pid)"
        return 0
    else
        print_warning "$name may have issues (check logs)"
        return 1
    fi
}

# Start beat scheduler
start_beat() {
    print_info "🥁 Starting Beat..."
    
    cd "$BACKEND_DIR"
    
    nohup python -m celery -A app.tasks.celery_app beat \
        --loglevel=info \
        > "../$LOG_DIR/beat.log" 2>&1 &
    
    local pid=$!
    echo "$pid" > "../$PID_DIR/beat.pid"
    
    cd - >/dev/null
    
    sleep 2
    
    if ps -p $pid >/dev/null 2>&1; then
        print_success "Beat started (PID: $pid)"
    else
        print_warning "Beat may have issues"
    fi
}

# Start flower
start_flower() {
    print_info "🌸 Starting Flower..."
    
    cd "$BACKEND_DIR"
    
    nohup python -m celery -A app.tasks.celery_app flower \
        --port=5555 \
        --basic_auth=admin:cryptopredict123 \
        > "../$LOG_DIR/flower.log" 2>&1 &
    
    local pid=$!
    echo "$pid" > "../$PID_DIR/flower.pid"
    
    cd - >/dev/null
    
    sleep 3
    
    if ps -p $pid >/dev/null 2>&1; then
        print_success "Flower started (PID: $pid) - http://localhost:5555"
    else
        print_warning "Flower may have issues"
    fi
}

# Show status
show_status() {
    print_header "📊 Simple Worker Status"
    echo "======================="
    echo
    
    local workers=("data_worker" "ml_worker" "notification_worker" "general_worker")
    
    for worker in "${workers[@]}"; do
        local pid_file="$PID_DIR/${worker}.pid"
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            if ps -p "$pid" >/dev/null 2>&1; then
                print_success "$worker running (PID: $pid)"
            else
                print_warning "$worker not running"
            fi
        else
            print_warning "$worker no PID file"
        fi
    done
    
    echo
    for service in "beat" "flower"; do
        local pid_file="$PID_DIR/${service}.pid"
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            if ps -p "$pid" >/dev/null 2>&1; then
                print_success "$service running (PID: $pid)"
            else
                print_warning "$service not running"
            fi
        else
            print_warning "$service no PID file"
        fi
    done
}

# Start all
start_all() {
    print_header "🚀 Starting Simple Worker System"
    echo "================================"
    echo
    
    setup
    cleanup
    sleep 2
    
    # Check environment
    print_info "📋 Environment check..."
    if [ ! -d "$BACKEND_DIR" ]; then
        print_error "Backend directory not found!"
        exit 1
    fi
    
    cd "$BACKEND_DIR"
    if ! python -c "from app.tasks.celery_app import app" 2>/dev/null; then
        print_error "Celery app import failed!"
        exit 1
    fi
    cd - >/dev/null
    
    print_success "Environment OK"
    echo
    
    # Start workers
    start_worker "data_worker" "price_data,market_data,data_sync"
    start_worker "ml_worker" "ml_prediction,model_training,ml_tasks"
    start_worker "notification_worker" "notifications,alerts,email_tasks"
    start_worker "general_worker" "general,cleanup,maintenance,default"
    
    echo
    start_beat
    start_flower
    
    echo
    print_success "🎉 Simple startup completed!"
    echo
    show_status
}

# Main
case "${1:-start}" in
    "start")
        start_all
        ;;
    "stop")
        cleanup
        ;;
    "status")
        show_status
        ;;
    "restart")
        cleanup
        sleep 3
        start_all
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        ;;
esac