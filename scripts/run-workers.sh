#!/bin/bash
# File: scripts/run-workers-windows.sh
# Windows/MinGW Compatible Celery Workers Manager

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
BACKEND_DIR="backend"
LOG_DIR="scripts/logs"
PID_DIR="$LOG_DIR/pids"
PYTHON_CMD="python"
FLOWER_PORT="5555"
BEAT_SCHEDULE_FILE="$LOG_DIR/celerybeat-schedule"

# Worker Configuration
declare -A WORKER_CONFIG
WORKER_CONFIG[data_worker]="price_data,market_data,data_sync"
WORKER_CONFIG[ml_worker]="ml_prediction,model_training,ml_tasks"  
WORKER_CONFIG[notification_worker]="notifications,alerts,email_tasks"
WORKER_CONFIG[general_worker]="general,cleanup,maintenance,default"

# Helper functions
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
print_header() { echo -e "${PURPLE}${BOLD}$1${NC}"; }
print_worker() { echo -e "${BLUE}🔧 $1${NC}"; }

# Windows-compatible process finder
find_celery_processes() {
    local pattern=$1
    ps aux 2>/dev/null | grep -i "celery" | grep -v grep | grep "$pattern" || true
}

# Windows-compatible PID finder
find_process_by_pattern() {
    local pattern=$1
    ps aux 2>/dev/null | grep "$pattern" | grep -v grep | awk '{print $2}' || true
}

# Check if port is in use (Windows compatible)
check_port() {
    local port=$1
    netstat -an 2>/dev/null | grep ":$port " | grep LISTEN >/dev/null 2>&1
}

# Get timestamp
get_timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

# Create directories
create_directory_structure() {
    print_info "📁 Setting up directory structure..."
    
    mkdir -p "$LOG_DIR" "$PID_DIR"
    
    local log_files=(
        "$LOG_DIR/data_worker_solo.log"
        "$LOG_DIR/ml_worker_solo.log" 
        "$LOG_DIR/notification_worker_solo.log"
        "$LOG_DIR/general_worker_solo.log"
        "$LOG_DIR/celery_beat.log"
        "$LOG_DIR/celery_flower.log"
        "$LOG_DIR/worker_manager.log"
    )
    
    for log_file in "${log_files[@]}"; do
        if [ ! -f "$log_file" ]; then
            touch "$log_file"
        fi
    done
    
    print_success "Directory structure created"
}

# Check environment
check_environment() {
    print_info "🔍 Checking environment..."
    
    # Check backend directory
    if [ ! -d "$BACKEND_DIR" ]; then
        print_error "Backend directory not found: $BACKEND_DIR"
        return 1
    fi
    print_success "Backend directory found"
    
    # Check Python
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        print_error "Python not found"
        return 1
    fi
    print_success "Python found: $(python --version)"
    
    # Check celery app file
    local app_file="$BACKEND_DIR/app/tasks/celery_app.py"
    if [ ! -f "$app_file" ]; then
        print_error "Celery app file not found: $app_file"
        return 1
    fi
    print_success "Celery app file found"
    
    # Check Redis (simplified)
    cd "$BACKEND_DIR" 2>/dev/null || return 1
    if timeout 5 "$PYTHON_CMD" -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print('Redis OK')
except Exception as e:
    print(f'Redis error: {e}')
    exit(1)
" 2>/dev/null; then
        print_success "Redis connection verified"
    else
        print_warning "Redis connection failed - start with: docker-compose up redis -d"
        return 1
    fi
    cd - > /dev/null
    
    return 0
}

# Get worker PID
get_worker_pid() {
    local worker_name=$1
    local pid_file=""
    
    if [ "$worker_name" = "celery_beat" ]; then
        pid_file="$PID_DIR/celery_beat.pid"
    elif [ "$worker_name" = "celery_flower" ]; then
        pid_file="$PID_DIR/celery_flower.pid"
    else
        pid_file="$PID_DIR/${worker_name}_solo.pid"
    fi
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file" 2>/dev/null)
        if [ -n "$pid" ]; then
            # Check if process exists (Windows compatible)
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "$pid"
            else
                rm -f "$pid_file"
            fi
        fi
    fi
}

# Clean up processes (Windows compatible)
cleanup_processes() {
    print_info "🧹 Cleaning up processes..."
    
    # Find and kill celery processes
    local celery_pids=$(find_process_by_pattern "celery.*worker")
    if [ -n "$celery_pids" ]; then
        print_warning "Killing celery worker processes..."
        echo "$celery_pids" | xargs -r kill 2>/dev/null || true
        sleep 2
    fi
    
    local beat_pids=$(find_process_by_pattern "celery.*beat")
    if [ -n "$beat_pids" ]; then
        print_warning "Killing celery beat processes..."
        echo "$beat_pids" | xargs -r kill 2>/dev/null || true
        sleep 1
    fi
    
    local flower_pids=$(find_process_by_pattern "celery.*flower")
    if [ -n "$flower_pids" ]; then
        print_warning "Killing celery flower processes..."
        echo "$flower_pids" | xargs -r kill 2>/dev/null || true
        sleep 1
    fi
    
    # Clean PID files
    rm -f "$PID_DIR"/*.pid 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Start solo worker
start_solo_worker() {
    local worker_name=$1
    local queues=${WORKER_CONFIG[$worker_name]}
    local log_file="$LOG_DIR/${worker_name}_solo.log"
    local pid_file="$PID_DIR/${worker_name}_solo.pid"
    
    print_worker "Starting $worker_name with Solo pool..."
    print_info "Queues: $queues"
    
    # Clean up existing
    if [ -f "$pid_file" ]; then
        local old_pid=$(cat "$pid_file" 2>/dev/null)
        if [ -n "$old_pid" ] && ps -p "$old_pid" > /dev/null 2>&1; then
            print_warning "Stopping existing $worker_name (PID: $old_pid)"
            kill "$old_pid" 2>/dev/null || true
            sleep 2
        fi
    fi
    rm -f "$pid_file" 2>/dev/null || true
    
    cd "$BACKEND_DIR"
    
    # Start worker
    nohup $PYTHON_CMD -m celery -A app.tasks.celery_app worker \
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
    sleep 3
    
    cd - > /dev/null
    
    # Verify and save PID
    if ps -p $pid > /dev/null 2>&1; then
        echo $pid > "$pid_file"
        print_success "$worker_name started (PID: $pid)"
        return 0
    else
        print_error "$worker_name failed to start"
        if [ -f "$log_file" ]; then
            print_error "Recent errors:"
            tail -3 "$log_file" | sed 's/^/   /'
        fi
        return 1
    fi
}

# Start beat scheduler
start_beat_scheduler() {
    local log_file="$LOG_DIR/celery_beat.log"
    local pid_file="$PID_DIR/celery_beat.pid"
    
    print_worker "Starting Beat scheduler..."
    
    # Cleanup
    if [ -f "$pid_file" ]; then
        local old_pid=$(cat "$pid_file" 2>/dev/null)
        if [ -n "$old_pid" ] && ps -p "$old_pid" > /dev/null 2>&1; then
            kill "$old_pid" 2>/dev/null || true
            sleep 2
        fi
    fi
    rm -f "$pid_file" 2>/dev/null || true
    
    cd "$BACKEND_DIR"
    
    nohup $PYTHON_CMD -m celery -A app.tasks.celery_app beat \
        --loglevel=info \
        --schedule="../$BEAT_SCHEDULE_FILE" \
        > "../$log_file" 2>&1 &
    
    local pid=$!
    sleep 3
    
    cd - > /dev/null
    
    if ps -p $pid > /dev/null 2>&1; then
        echo $pid > "$pid_file"
        print_success "Beat scheduler started (PID: $pid)"
        return 0
    else
        print_error "Beat scheduler failed to start"
        return 1
    fi
}

# Start flower monitor
start_flower_monitor() {
    local log_file="$LOG_DIR/celery_flower.log"
    local pid_file="$PID_DIR/celery_flower.pid"
    
    # Find available port
    local flower_port=$FLOWER_PORT
    if check_port $flower_port; then
        print_warning "Port $flower_port is busy, trying 5556..."
        flower_port=5556
    fi
    
    print_worker "Starting Flower monitor (Port: $flower_port)..."
    
    # Cleanup
    if [ -f "$pid_file" ]; then
        local old_pid=$(cat "$pid_file" 2>/dev/null)
        if [ -n "$old_pid" ] && ps -p "$old_pid" > /dev/null 2>&1; then
            kill "$old_pid" 2>/dev/null || true
            sleep 2
        fi
    fi
    rm -f "$pid_file" 2>/dev/null || true
    
    cd "$BACKEND_DIR"
    
    nohup $PYTHON_CMD -m celery -A app.tasks.celery_app flower \
        --port="$flower_port" \
        --basic_auth=admin:cryptopredict123 \
        > "../$log_file" 2>&1 &
    
    local pid=$!
    sleep 3
    
    cd - > /dev/null
    
    if ps -p $pid > /dev/null 2>&1; then
        echo $pid > "$pid_file"
        print_success "Flower monitor started (PID: $pid, Port: $flower_port)"
        print_info "Web interface: http://localhost:$flower_port (admin/cryptopredict123)"
        return 0
    else
        print_error "Flower monitor failed to start"
        return 1
    fi
}

# Show status - Fixed for Windows
show_status() {
    print_header "📊 Worker Status"
    print_header "================\n"
    
    local running_workers=0
    local total_workers=4  # Fixed number
    
    print_info "🔧 SOLO POOL WORKERS:"
    printf "%-20s %-10s %-8s %-25s\n" "Worker" "Status" "PID" "Queues"
    echo "---------------------------------------------------------------"
    
    # Check each worker individually to avoid loop issues
    local workers=("data_worker" "ml_worker" "notification_worker" "general_worker")
    
    for worker_name in "${workers[@]}"; do
        local pid=$(get_worker_pid "$worker_name")
        local status="❌ STOPPED"
        local pid_display="N/A"
        local queues=${WORKER_CONFIG[$worker_name]:-"unknown"}
        
        if [ -n "$pid" ]; then
            status="✅ RUNNING"
            pid_display="$pid"
            ((running_workers++))
        fi
        
        # Truncate queues if too long
        local short_queues="${queues:0:25}"
        printf "%-20s %-10s %-8s %-25s\n" "$worker_name" "$status" "$pid_display" "$short_queues"
    done
    
    echo ""
    print_info "📋 SYSTEM SERVICES:"
    printf "%-20s %-10s %-8s %-25s\n" "Service" "Status" "PID" "Details"
    echo "---------------------------------------------------------------"
    
    # Beat scheduler
    local beat_pid=$(get_worker_pid "celery_beat")
    local beat_status="❌ STOPPED"
    local beat_pid_display="N/A"
    if [ -n "$beat_pid" ]; then
        beat_status="✅ RUNNING"
        beat_pid_display="$beat_pid"
    fi
    printf "%-20s %-10s %-8s %-25s\n" "Beat Scheduler" "$beat_status" "$beat_pid_display" "Task Scheduling"
    
    # Flower monitor
    local flower_pid=$(get_worker_pid "celery_flower")
    local flower_status="❌ STOPPED"
    local flower_pid_display="N/A"
    if [ -n "$flower_pid" ]; then
        flower_status="✅ RUNNING"
        flower_pid_display="$flower_pid"
    fi
    printf "%-20s %-10s %-8s %-25s\n" "Flower Monitor" "$flower_status" "$flower_pid_display" "Web Interface"
    
    echo ""
    print_info "📈 SUMMARY: $running_workers/$total_workers workers running"
    
    if [ "$running_workers" -eq "$total_workers" ] && [ -n "$beat_pid" ] && [ -n "$flower_pid" ]; then
        print_success "🎉 All systems operational!"
    elif [ "$running_workers" -gt 0 ]; then
        print_warning "⚠️  Some workers are not running"
    else
        print_error "❌ No workers are running"
    fi
    
    echo ""
    print_info "💡 Useful commands:"
    print_info "   ./scripts/run-workers-win.sh logs     # View recent logs"
    print_info "   ./scripts/run-workers-win.sh restart  # Restart all workers"
}

# Stop workers - Fixed
stop_workers() {
    print_header "🛑 Stopping Workers"
    print_header "===================\n"
    
    local workers=("data_worker" "ml_worker" "notification_worker" "general_worker")
    
    # Stop individual workers
    for worker_name in "${workers[@]}"; do
        local pid=$(get_worker_pid "$worker_name")
        if [ -n "$pid" ]; then
            print_info "Stopping $worker_name (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            sleep 1
            
            # Verify stopped
            if ps -p "$pid" > /dev/null 2>&1; then
                print_warning "Force killing $worker_name..."
                kill -9 "$pid" 2>/dev/null || true
            fi
            print_success "$worker_name stopped"
        else
            print_info "$worker_name was not running"
        fi
    done
    
    # Stop beat scheduler
    local beat_pid=$(get_worker_pid "celery_beat")
    if [ -n "$beat_pid" ]; then
        print_info "Stopping Beat scheduler (PID: $beat_pid)..."
        kill "$beat_pid" 2>/dev/null || true
        sleep 1
        if ps -p "$beat_pid" > /dev/null 2>&1; then
            kill -9 "$beat_pid" 2>/dev/null || true
        fi
        print_success "Beat scheduler stopped"
    else
        print_info "Beat scheduler was not running"
    fi
    
    # Stop flower monitor
    local flower_pid=$(get_worker_pid "celery_flower")
    if [ -n "$flower_pid" ]; then
        print_info "Stopping Flower monitor (PID: $flower_pid)..."
        kill "$flower_pid" 2>/dev/null || true
        sleep 1
        if ps -p "$flower_pid" > /dev/null 2>&1; then
            kill -9 "$flower_pid" 2>/dev/null || true
        fi
        print_success "Flower monitor stopped"
    else
        print_info "Flower monitor was not running"
    fi
    
    # Final cleanup
    cleanup_processes
    print_success "All workers stopped successfully"
}

# Start all workers - Fixed version
start_all_workers() {
    print_header "🚀 Starting All Workers"
    print_header "=======================\n"
    
    # Environment check
    if ! check_environment; then
        print_error "Environment is not ready"
        print_info "💡 Start Redis: docker-compose up redis -d"
        exit 1
    fi
    
    # Setup and cleanup
    create_directory_structure
    cleanup_processes
    sleep 2
    
    local success_count=0
    local total_services=6  # 4 workers + beat + flower
    
    print_info "🎯 Starting Solo Pool workers...\n"
    
    # Start workers one by one with error handling
    local worker_names=("data_worker" "ml_worker" "notification_worker" "general_worker")
    
    for worker_name in "${worker_names[@]}"; do
        print_info "🔄 Processing $worker_name..."
        if start_solo_worker "$worker_name"; then
            ((success_count++))
            print_success "✅ $worker_name completed successfully"
        else
            print_error "❌ $worker_name failed to start"
        fi
        echo ""
        sleep 1  # Small delay between workers
    done
    
    # Start beat scheduler
    print_info "🔄 Processing Beat Scheduler..."
    if start_beat_scheduler; then
        ((success_count++))
        print_success "✅ Beat Scheduler completed successfully"
    else
        print_error "❌ Beat Scheduler failed to start"
    fi
    echo ""
    sleep 1
    
    # Start flower monitor
    print_info "🔄 Processing Flower Monitor..."
    if start_flower_monitor; then
        ((success_count++))
        print_success "✅ Flower Monitor completed successfully"
    else
        print_error "❌ Flower Monitor failed to start"
    fi
    echo ""
    
    # Wait and show status
    print_info "⏳ Waiting for stabilization..."
    sleep 3
    
    echo "🔍 Showing final status..."
    show_status
    
    # Summary
    print_header "\n🎉 STARTUP SUMMARY"
    print_header "==================\n"
    
    print_info "📊 Results: $success_count/$total_services services processed"
    
    if [ "$success_count" -eq "$total_services" ]; then
        print_success "🟢 ALL SERVICES STARTED SUCCESSFULLY!"
        print_info "✨ Solo Pool workers are running securely"
    elif [ "$success_count" -gt 0 ]; then
        print_warning "🟡 PARTIAL SUCCESS: $success_count/$total_services services started"
        print_info "💡 Check logs for failed services"
    else
        print_error "🔴 STARTUP FAILED"
        print_info "💡 Run: ./scripts/run-workers-win.sh logs"
    fi
    
    echo ""
    print_info "🎯 Next steps:"
    print_info "   • Check status: ./scripts/run-workers-win.sh status"
    print_info "   • View logs: ./scripts/run-workers-win.sh logs"
    print_info "   • Monitor: check individual worker logs in scripts/logs/"
}

# Show logs - Enhanced
show_logs() {
    print_header "📋 Recent Logs"
    print_header "===============\n"
    
    local workers=("data_worker" "ml_worker" "notification_worker" "general_worker")
    
    for worker_name in "${workers[@]}"; do
        local log_file="$LOG_DIR/${worker_name}_solo.log"
        print_info "📄 $worker_name logs:"
        
        if [ -f "$log_file" ] && [ -s "$log_file" ]; then
            echo "----------------------------------------"
            tail -5 "$log_file" | sed 's/^/   /'
            echo "----------------------------------------"
        else
            print_warning "No logs available"
        fi
        echo ""
    done
    
    # System services logs
    print_info "📄 Beat Scheduler logs:"
    local beat_log="$LOG_DIR/celery_beat.log"
    if [ -f "$beat_log" ] && [ -s "$beat_log" ]; then
        echo "----------------------------------------"
        tail -3 "$beat_log" | sed 's/^/   /'
        echo "----------------------------------------"
    else
        print_warning "No Beat logs available"
    fi
    echo ""
    
    print_info "📄 Flower Monitor logs:"
    local flower_log="$LOG_DIR/celery_flower.log"
    if [ -f "$flower_log" ] && [ -s "$flower_log" ]; then
        echo "----------------------------------------"
        tail -3 "$flower_log" | sed 's/^/   /'
        echo "----------------------------------------"
    else
        print_warning "No Flower logs available"
    fi
}

# Debug function
debug_workers() {
    print_header "🔍 Debug Information"
    print_header "====================\n"
    
    print_info "📁 Directory structure:"
    echo "   LOG_DIR: $LOG_DIR ($([ -d "$LOG_DIR" ] && echo "exists" || echo "missing"))"
    echo "   PID_DIR: $PID_DIR ($([ -d "$PID_DIR" ] && echo "exists" || echo "missing"))"
    echo ""
    
    print_info "📄 PID files:"
    if [ -d "$PID_DIR" ]; then
        ls -la "$PID_DIR"/*.pid 2>/dev/null || echo "   No PID files found"
    else
        echo "   PID directory missing"
    fi
    echo ""
    
    print_info "📋 Log files:"
    if [ -d "$LOG_DIR" ]; then
        ls -la "$LOG_DIR"/*.log 2>/dev/null || echo "   No log files found"
    else
        echo "   Log directory missing"
    fi
    echo ""
    
    print_info "🔄 Running processes:"
    ps aux 2>/dev/null | grep -E "(celery|python.*worker)" | grep -v grep || echo "   No celery processes found"
    echo ""
    
    print_info "🌐 Port usage:"
    echo "   Redis (6379): $(check_port 6379 && echo "in use" || echo "free")"
    echo "   Flower (5555): $(check_port 5555 && echo "in use" || echo "free")"
    echo "   Flower (5556): $(check_port 5556 && echo "in use" || echo "free")"
}

# Help
show_help() {
    print_header "🚀 Windows Compatible Celery Workers Manager"
    print_header "============================================\n"
    
    print_info "📋 AVAILABLE COMMANDS:"
    echo "   start     - Start all workers"
    echo "   stop      - Stop all workers"
    echo "   restart   - Restart all workers"
    echo "   status    - Show worker status"
    echo "   logs      - Show recent logs"
    echo "   debug     - Show debug information"
    echo "   help      - Show this help\n"
    
    print_info "🎯 EXAMPLES:"
    echo "   ./scripts/run-workers-win.sh start"
    echo "   ./scripts/run-workers-win.sh status"
    echo "   ./scripts/run-workers-win.sh logs"
    echo "   ./scripts/run-workers-win.sh debug\n"
    
    print_info "📋 REQUIREMENTS:"
    echo "   • Redis must be running: docker-compose up redis -d"
    echo "   • Python environment with celery installed\n"
    
    print_info "🔧 TROUBLESHOOTING:"
    echo "   • If workers fail to start, check debug output"
    echo "   • Ensure Redis is accessible on localhost:6379"
    echo "   • Check logs for specific error messages"
    
    exit 0
}

# Main logic
main() {
    local action="${1:-start}"
    
    # Header
    echo -e "${PURPLE}${BOLD}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║          🚀 Windows Compatible Celery Workers Manager         ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
    
    case "$action" in
        "start"|"")
            start_all_workers
            ;;
        "stop")
            stop_workers
            ;;
        "restart")
            print_header "🔄 Restarting Workers"
            stop_workers
            sleep 3
            start_all_workers
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "debug")
            debug_workers
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown action: $action"
            print_info "Available: start, stop, restart, status, logs, debug, help"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"