#!/bin/bash
# File: scripts/celery-manager.sh  
# Enhanced Celery management with start/stop/status commands

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
print_header() { echo -e "${BLUE}$1${NC}"; }

# Global variables
LOG_DIR="scripts/logs"
PID_DIR="$LOG_DIR/pids"
WORKERS=("data_worker" "ml_worker" "notification_worker" "general_worker")

# Check environment
check_environment() {
    if [ ! -d "backend" ]; then
        print_error "Please run from project root directory"
        exit 1
    fi
    
    # Create directories if they don't exist
    mkdir -p "$PID_DIR"
}

# Show usage
show_usage() {
    echo "Usage: $0 {start|stop|status|restart}"
    echo
    echo "Commands:"
    echo "  start   - Start all Celery services (workers, beat, flower)"
    echo "  stop    - Stop all Celery services"
    echo "  status  - Show status of all services"
    echo "  restart - Stop and start all services"
    echo
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 stop"
    echo "  $0 status"
    echo "  $0 restart"
}

# Kill all Celery processes
cleanup_processes() {
    print_info "🧹 Cleaning up processes..."
    
    # Kill Celery processes
    pkill -f "celery" 2>/dev/null || true
    
    # On Windows, also kill Python processes (be careful!)
    if command -v taskkill >/dev/null 2>&1; then
        taskkill //F //IM "python.exe" //FI "WINDOWTITLE eq celery*" 2>/dev/null || true
    fi
    
    # Clean PID files
    rm -f "$PID_DIR"/*.pid 2>/dev/null || true
    
    sleep 3
    print_success "Cleanup completed"
}

# Clean log files
clean_logs() {
    print_info "📝 Cleaning log files..."
    
    # Create empty log files
    > "$LOG_DIR/celery_beat.log"
    > "$LOG_DIR/celery_flower.log"
    
    for worker in "${WORKERS[@]}"; do
        > "$LOG_DIR/${worker}.log"
    done
    
    print_success "Log files cleaned"
}

# Start workers
start_workers() {
    print_info "👷 Starting workers..."
    
    cd backend
    
    # Data worker
    print_info "Starting data worker..."
    nohup python -m celery -A app.tasks.celery_app worker \
        --loglevel=info \
        --queues=price_data,market_data,data_sync \
        --hostname=data_worker@%h \
        --pool=solo \
        --concurrency=1 \
        > "../$LOG_DIR/data_worker_simple.log" 2>&1 &
    echo $! > "../$PID_DIR/data_worker_solo.pid"
    sleep 2
    
    # ML worker
    print_info "Starting ml worker..."
    nohup python -m celery -A app.tasks.celery_app worker \
        --loglevel=info \
        --queues=ml_prediction,model_training,ml_tasks \
        --hostname=ml_worker@%h \
        --pool=solo \
        --concurrency=1 \
        > "../$LOG_DIR/ml_worker_simple.log" 2>&1 &
    echo $! > "../$PID_DIR/ml_worker_solo.pid"
    sleep 2
    
    # Notification worker
    print_info "Starting notification worker..."
    nohup python -m celery -A app.tasks.celery_app worker \
        --loglevel=info \
        --queues=notifications,alerts,email_tasks \
        --hostname=notification_worker@%h \
        --pool=solo \
        --concurrency=1 \
        > "../$LOG_DIR/notification_worker_simple.log" 2>&1 &
    echo $! > "../$PID_DIR/notification_worker_solo.pid"
    sleep 2
    
    # General worker
    print_info "Starting general worker..."
    nohup python -m celery -A app.tasks.celery_app worker \
        --loglevel=info \
        --queues=general,cleanup,maintenance,default \
        --hostname=general_worker@%h \
        --pool=solo \
        --concurrency=1 \
        > "../$LOG_DIR/general_worker_simple.log" 2>&1 &
    echo $! > "../$PID_DIR/general_worker_solo.pid"
    
    cd ..
    
    sleep 3
    print_success "Workers started"
}

# Start Beat scheduler
start_beat() {
    print_info "⏰ Starting Beat Scheduler..."
    
    cd backend
    
    # Remove existing beat schedule files
    rm -f celerybeat-schedule* 2>/dev/null || true
    rm -f "../$LOG_DIR/celerybeat-schedule"* 2>/dev/null || true
    
    nohup python -m celery -A app.tasks.celery_app beat \
        --loglevel=info \
        > "../$LOG_DIR/celery_beat.log" 2>&1 &
    
    BEAT_PID=$!
    echo "$BEAT_PID" > "../$PID_DIR/celery_beat.pid"
    
    cd ..
    
    sleep 5
    if ps -p "$BEAT_PID" > /dev/null 2>&1; then
        print_success "Beat Scheduler started (PID: $BEAT_PID)"
    else
        print_warning "Beat Scheduler may have issues - check logs"
    fi
}

# Start Flower monitor
start_flower() {
    print_info "🌸 Starting Flower Monitor..."
    
    cd backend
    
    nohup python -m celery -A app.tasks.celery_app flower \
        --port=5555 \
        --basic_auth=admin:cryptopredict123 \
        > "../$LOG_DIR/celery_flower.log" 2>&1 &
    
    FLOWER_PID=$!
    echo "$FLOWER_PID" > "../$PID_DIR/celery_flower.pid"
    
    cd ..
    
    sleep 5
    if ps -p "$FLOWER_PID" > /dev/null 2>&1; then
        print_success "Flower Monitor started (PID: $FLOWER_PID)"
        print_info "🌐 Access at: http://localhost:5555"
        print_info "🔐 Login: admin / cryptopredict123"
    else
        print_warning "Flower Monitor may have issues - check logs"
    fi
}

# Check if a process is running by PID
is_process_running() {
    local pid_file="$1"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "$pid"
            return 0
        fi
    fi
    return 1
}

# Show status of all services
show_status() {
    print_header "📊 Celery Services Status"
    print_header "=========================="
    echo
    
    local all_running=0
    local total_services=0
    
    # Check workers
    echo "Workers:"
    for worker in "${WORKERS[@]}"; do
        ((total_services++))
        pid_file="$PID_DIR/${worker}_solo.pid"
        if pid=$(is_process_running "$pid_file"); then
            echo "  ✅ $worker: Running (PID: $pid)"
            ((all_running++))
        else
            echo "  ❌ $worker: Stopped"
        fi
    done
    
    echo
    echo "Services:"
    
    # Check Beat
    ((total_services++))
    if pid=$(is_process_running "$PID_DIR/celery_beat.pid"); then
        echo "  ✅ Beat Scheduler: Running (PID: $pid)"
        ((all_running++))
    else
        echo "  ❌ Beat Scheduler: Stopped"
    fi
    
    # Check Flower
    ((total_services++))
    if pid=$(is_process_running "$PID_DIR/celery_flower.pid"); then
        echo "  ✅ Flower Monitor: Running (PID: $pid)"
        echo "      🌐 http://localhost:5555"
        ((all_running++))
    else
        echo "  ❌ Flower Monitor: Stopped"
    fi
    
    echo
    echo "Summary: $all_running/$total_services services running"
    
    if [ $all_running -eq $total_services ]; then
        print_success "🎉 All services are running!"
    elif [ $all_running -eq 0 ]; then
        print_warning "❌ No services are running"
    else
        print_warning "⚠️  Some services need attention"
    fi
}

# Stop all services
stop_services() {
    print_header "🛑 Stopping Celery Services"
    print_header "==========================="
    echo
    
    local stopped_count=0
    
    # Stop workers
    print_info "Stopping workers..."
    for worker in "${WORKERS[@]}"; do
        pid_file="$PID_DIR/${worker}_solo.pid"
        if pid=$(is_process_running "$pid_file"); then
            kill "$pid" 2>/dev/null || true
            rm -f "$pid_file"
            print_info "$worker stopped"
            ((stopped_count++))
        fi
    done
    
    # Stop Beat
    print_info "Stopping Beat Scheduler..."
    if pid=$(is_process_running "$PID_DIR/celery_beat.pid"); then
        kill "$pid" 2>/dev/null || true
        rm -f "$PID_DIR/celery_beat.pid"
        print_info "Beat Scheduler stopped"
        ((stopped_count++))
    fi
    
    # Stop Flower
    print_info "Stopping Flower Monitor..."
    if pid=$(is_process_running "$PID_DIR/celery_flower.pid"); then
        kill "$pid" 2>/dev/null || true
        rm -f "$PID_DIR/celery_flower.pid"
        print_info "Flower Monitor stopped"
        ((stopped_count++))
    fi
    
    # Final cleanup
    sleep 3
    cleanup_processes
    
    if [ $stopped_count -gt 0 ]; then
        print_success "Services stopped successfully"
    else
        print_info "No running services found"
    fi
}

# Start all services
start_services() {
    print_header "🚀 Starting Celery Services"
    print_header "============================"
    echo
    
    # Clean logs
    clean_logs
    
    # Start services in order
    start_workers
    sleep 2
    start_beat
    sleep 2
    start_flower
    
    echo
    print_info "🔄 Checking final status..."
    sleep 5
    show_status
}

# Restart services
restart_services() {
    print_header "🔄 Restarting Celery Services"
    print_header "=============================="
    echo
    
    stop_services
    sleep 3
    start_services
}

# Main script logic
main() {
    check_environment
    
    case "${1:-}" in
        "start")
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "status")
            show_status
            ;;
        "restart")
            restart_services
            ;;
        "")
            print_error "No command specified"
            echo
            show_usage
            exit 1
            ;;
        *)
            print_error "Unknown command: $1"
            echo
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"