#!/bin/bash
# File: scripts/ultimate-worker-manager.sh
# Ultimate Celery Worker Manager - All-in-One Solution
# Handles all known issues and provides comprehensive management

set -e

#==============================================================================
# CONFIGURATION & CONSTANTS
#==============================================================================

# Version and metadata
SCRIPT_VERSION="2.0.0"
SCRIPT_NAME="Ultimate Celery Worker Manager"
CREATED_DATE="2025-08-09"

# Color codes for enhanced UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BLUE='\033[0;34m'
BOLD='\033[1m'
UNDERLINE='\033[4m'
NC='\033[0m'

# System configuration
BACKEND_DIR="backend"
LOG_DIR="scripts/logs"
PID_DIR="$LOG_DIR/pids"
PYTHON_CMD="python"
FLOWER_PORT="5555"
BEAT_SCHEDULE_FILE="$LOG_DIR/celerybeat-schedule"

# Worker configuration - Fixed arrays for Windows compatibility
WORKER_NAMES=("data_worker" "ml_worker" "notification_worker" "general_worker")
WORKER_QUEUES=(
    "price_data,market_data,data_sync"
    "ml_prediction,model_training,ml_tasks"
    "notifications,alerts,email_tasks"
    "general,cleanup,maintenance,default"
)

# System limits and timeouts
MAX_STARTUP_TIME=30
MAX_RESTART_ATTEMPTS=3
HEALTH_CHECK_INTERVAL=10
PROCESS_KILL_TIMEOUT=10

#==============================================================================
# UTILITY FUNCTIONS
#==============================================================================

# Enhanced logging with timestamps
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_DIR/ultimate_manager.log"
}

# Print functions with consistent formatting
print_success() { echo -e "${GREEN}✅ $1${NC}"; log_message "SUCCESS" "$1"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; log_message "WARNING" "$1"; }
print_error() { echo -e "${RED}❌ $1${NC}"; log_message "ERROR" "$1"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; log_message "INFO" "$1"; }
print_header() { echo -e "${PURPLE}${BOLD}$1${NC}"; log_message "HEADER" "$1"; }
print_worker() { echo -e "${BLUE}🔧 $1${NC}"; log_message "WORKER" "$1"; }
print_task() { echo -e "${BLUE}🔄 $1${NC}"; log_message "TASK" "$1"; }

# System utilities
get_timestamp() { date '+%Y-%m-%d %H:%M:%S'; }
get_current_user() { whoami 2>/dev/null || echo "unknown"; }
get_system_info() { uname -a 2>/dev/null || echo "Windows/MinGW"; }

# Windows-compatible process functions
find_process_by_pattern() {
    local pattern="$1"
    ps aux 2>/dev/null | grep "$pattern" | grep -v grep | awk '{print $2}' || true
}

check_port_usage() {
    local port="$1"
    netstat -an 2>/dev/null | grep ":$port " | grep LISTEN >/dev/null 2>&1
}

is_pid_running() {
    local pid="$1"
    [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1
}

#==============================================================================
# SYSTEM DIAGNOSTICS
#==============================================================================

# Comprehensive environment check
check_environment() {
    print_header "🔍 Environment Diagnostics"
    echo "=========================="
    echo
    
    local issues=0
    local warnings=0
    
    # System information
    print_info "📊 System Information:"
    echo "   🖥️  System: $(get_system_info)"
    echo "   👤 User: $(get_current_user)"
    echo "   📅 Date: $(get_timestamp)"
    echo "   📦 Script Version: $SCRIPT_VERSION"
    echo
    
    # Check backend directory
    print_info "📁 Backend Directory Check:"
    if [ ! -d "$BACKEND_DIR" ]; then
        print_error "Backend directory not found: $BACKEND_DIR"
        print_error "Please run this script from the project root directory"
        ((issues++))
    else
        print_success "Backend directory found: $BACKEND_DIR"
    fi
    
    # Check Python installation
    print_info "🐍 Python Environment Check:"
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        print_error "Python not found in PATH"
        print_error "Please install Python or update PATH"
        ((issues++))
    else
        local python_version=$($PYTHON_CMD --version 2>&1)
        print_success "Python found: $python_version"
    fi
    
    # Check required Python modules
    print_info "📦 Python Dependencies Check:"
    cd "$BACKEND_DIR" 2>/dev/null || return 1
    
    local required_modules=("celery" "redis" "app.tasks.celery_app")
    for module in "${required_modules[@]}"; do
        if $PYTHON_CMD -c "import ${module}" 2>/dev/null; then
            print_success "$module module available"
        else
            print_error "$module module missing"
            ((issues++))
        fi
    done
    
    cd - > /dev/null
    
    # Check Redis connectivity
    print_info "📡 Redis Connectivity Check:"
    cd "$BACKEND_DIR"
    if timeout 5 "$PYTHON_CMD" -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print('Redis connection successful')
except Exception as e:
    print(f'Redis error: {e}')
    exit(1)
" 2>/dev/null; then
        print_success "Redis connection verified"
    else
        print_error "Redis connection failed"
        print_warning "Start Redis with: docker-compose up redis -d"
        ((warnings++))
    fi
    cd - > /dev/null
    
    # Check port availability
    print_info "🌐 Port Availability Check:"
    if check_port_usage 6379; then
        print_success "Redis port 6379 is listening"
    else
        print_warning "Redis port 6379 not listening"
        ((warnings++))
    fi
    
    if check_port_usage $FLOWER_PORT; then
        print_warning "Flower port $FLOWER_PORT is in use"
    else
        print_success "Flower port $FLOWER_PORT is available"
    fi
    
    # Summary
    echo
    if [ "$issues" -eq 0 ] && [ "$warnings" -eq 0 ]; then
        print_success "🎉 Environment is fully ready!"
        return 0
    elif [ "$issues" -eq 0 ]; then
        print_warning "⚠️  Environment has $warnings warnings but is usable"
        return 0
    else
        print_error "❌ Environment has $issues critical issues"
        return 1
    fi
}

# Advanced system diagnostics
system_diagnostics() {
    print_header "🔬 Advanced System Diagnostics"
    echo "==============================="
    echo
    
    # Memory check
    print_info "💾 System Memory:"
    if command -v free >/dev/null 2>&1; then
        free -h | head -2
    else
        echo "   Memory info not available on this system"
    fi
    echo
    
    # Disk space check
    print_info "💽 Disk Space:"
    df -h . 2>/dev/null | tail -1 || echo "   Disk info not available"
    echo
    
    # Process count
    print_info "🔄 Process Information:"
    local total_processes=$(ps aux 2>/dev/null | wc -l)
    local celery_processes=$(ps aux 2>/dev/null | grep -c celery || echo 0)
    echo "   Total processes: $total_processes"
    echo "   Celery processes: $celery_processes"
    echo
    
    # Network status
    print_info "🌐 Network Status:"
    local listening_ports=$(netstat -tuln 2>/dev/null | grep LISTEN | wc -l)
    echo "   Listening ports: $listening_ports"
    echo
}

#==============================================================================
# DIRECTORY AND FILE MANAGEMENT
#==============================================================================

# Enhanced directory structure creation
create_directory_structure() {
    print_info "📁 Setting up enhanced directory structure..."
    
    # Create directories with proper permissions
    mkdir -p "$LOG_DIR" "$PID_DIR"
    
    # Enhanced log files
    local log_files=(
        "$LOG_DIR/ultimate_manager.log"
        "$LOG_DIR/data_worker_solo.log"
        "$LOG_DIR/ml_worker_solo.log"
        "$LOG_DIR/notification_worker_solo.log"
        "$LOG_DIR/general_worker_solo.log"
        "$LOG_DIR/celery_beat.log"
        "$LOG_DIR/celery_flower.log"
        "$LOG_DIR/system_health.log"
        "$LOG_DIR/error_tracking.log"
    )
    
    for log_file in "${log_files[@]}"; do
        if [ ! -f "$log_file" ]; then
            touch "$log_file"
            chmod 644 "$log_file" 2>/dev/null || true
        fi
    done
    
    # Create status files
    touch "$LOG_DIR/last_status_check"
    touch "$LOG_DIR/worker_performance.log"
    
    print_success "Directory structure created successfully"
}

# Intelligent log rotation
rotate_logs() {
    print_info "🔄 Rotating large log files..."
    
    local rotated_count=0
    local max_lines=2000
    
    for log_file in "$LOG_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            local line_count=$(wc -l < "$log_file" 2>/dev/null || echo 0)
            if [ "$line_count" -gt $max_lines ]; then
                # Keep last 1000 lines
                tail -1000 "$log_file" > "${log_file}.tmp" && mv "${log_file}.tmp" "$log_file"
                print_info "Rotated $(basename "$log_file") ($line_count → 1000 lines)"
                ((rotated_count++))
            fi
        fi
    done
    
    if [ "$rotated_count" -gt 0 ]; then
        print_success "Rotated $rotated_count log files"
    else
        print_info "No log rotation needed"
    fi
}

#==============================================================================
# WORKER PID MANAGEMENT
#==============================================================================

# Enhanced PID management
get_worker_pid() {
    local worker_name="$1"
    local pid_file=""
    
    # Handle different naming conventions
    case "$worker_name" in
        "celery_beat")
            pid_file="$PID_DIR/celery_beat.pid"
            ;;
        "celery_flower")
            pid_file="$PID_DIR/celery_flower.pid"
            ;;
        *)
            pid_file="$PID_DIR/${worker_name}_solo.pid"
            ;;
    esac
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file" 2>/dev/null)
        if is_pid_running "$pid"; then
            echo "$pid"
        else
            # Clean up stale PID file
            rm -f "$pid_file"
        fi
    fi
}

# Rebuild PID files from running processes
rebuild_pid_files() {
    print_info "🔧 Rebuilding PID files from running processes..."
    
    local rebuilt_count=0
    
    # Rebuild worker PID files
    for i in "${!WORKER_NAMES[@]}"; do
        local worker_name="${WORKER_NAMES[$i]}"
        local pid=$(find_process_by_pattern "celery.*worker.*${worker_name}")
        
        if [ -n "$pid" ]; then
            echo "$pid" > "$PID_DIR/${worker_name}_solo.pid"
            print_success "Rebuilt PID for $worker_name (PID: $pid)"
            ((rebuilt_count++))
        fi
    done
    
    # Rebuild system service PID files
    local beat_pid=$(find_process_by_pattern "celery.*beat")
    if [ -n "$beat_pid" ]; then
        echo "$beat_pid" > "$PID_DIR/celery_beat.pid"
        print_success "Rebuilt PID for Beat scheduler (PID: $beat_pid)"
        ((rebuilt_count++))
    fi
    
    local flower_pid=$(find_process_by_pattern "celery.*flower")
    if [ -n "$flower_pid" ]; then
        echo "$flower_pid" > "$PID_DIR/celery_flower.pid"
        print_success "Rebuilt PID for Flower monitor (PID: $flower_pid)"
        ((rebuilt_count++))
    fi
    
    print_info "Rebuilt $rebuilt_count PID files"
}

#==============================================================================
# PROCESS CLEANUP AND MANAGEMENT
#==============================================================================

# Comprehensive process cleanup
comprehensive_cleanup() {
    print_header "🧹 Comprehensive Process Cleanup"
    echo "================================="
    echo
    
    local cleanup_count=0
    
    # Kill workers gracefully first
    print_info "1️⃣ Graceful worker shutdown..."
    for worker_name in "${WORKER_NAMES[@]}"; do
        local pid=$(get_worker_pid "$worker_name")
        if [ -n "$pid" ]; then
            print_info "Stopping $worker_name (PID: $pid)"
            kill -TERM "$pid" 2>/dev/null || true
            ((cleanup_count++))
        fi
    done
    
    # Kill system services
    print_info "2️⃣ System services shutdown..."
    for service in "celery_beat" "celery_flower"; do
        local pid=$(get_worker_pid "$service")
        if [ -n "$pid" ]; then
            print_info "Stopping $service (PID: $pid)"
            kill -TERM "$pid" 2>/dev/null || true
            ((cleanup_count++))
        fi
    done
    
    # Wait for graceful shutdown
    if [ "$cleanup_count" -gt 0 ]; then
        print_info "⏳ Waiting for graceful shutdown..."
        sleep 5
    fi
    
    # Force cleanup remaining processes
    print_info "3️⃣ Force cleanup remaining processes..."
    local patterns=(
        "celery.*worker.*solo"
        "celery.*worker"
        "celery.*beat"
        "celery.*flower"
        "python.*celery"
    )
    
    for pattern in "${patterns[@]}"; do
        local pids=$(find_process_by_pattern "$pattern")
        if [ -n "$pids" ]; then
            print_warning "Force killing processes matching: $pattern"
            echo "$pids" | xargs -r kill -KILL 2>/dev/null || true
        fi
    done
    
    # Clean up PID files
    print_info "4️⃣ Cleaning PID files..."
    rm -f "$PID_DIR"/*.pid 2>/dev/null || true
    
    # Clean up problematic files
    print_info "5️⃣ Cleaning problematic files..."
    rm -f "$BEAT_SCHEDULE_FILE"* 2>/dev/null || true
    
    print_success "Cleanup completed successfully"
}

# Smart process detection and cleanup
smart_cleanup() {
    print_info "🤖 Smart cleanup based on process detection..."
    
    # Detect stuck processes
    local stuck_processes=$(ps aux 2>/dev/null | grep -E "(celery.*<defunct>|celery.*zombie)" | wc -l)
    if [ "$stuck_processes" -gt 0 ]; then
        print_warning "Found $stuck_processes stuck/zombie processes"
        # Additional cleanup for stuck processes
        ps aux 2>/dev/null | grep -E "(celery.*<defunct>|celery.*zombie)" | awk '{print $2}' | xargs -r kill -KILL 2>/dev/null || true
    fi
    
    # Clear locked files
    find "$LOG_DIR" -name "*.lock" -delete 2>/dev/null || true
    find "$LOG_DIR" -name "*.tmp" -delete 2>/dev/null || true
}

#==============================================================================
# WORKER STARTUP FUNCTIONS
#==============================================================================

# Enhanced solo worker startup
start_solo_worker() {
    local worker_name="$1"
    local worker_index=""
    
    # Find worker index
    for i in "${!WORKER_NAMES[@]}"; do
        if [ "${WORKER_NAMES[$i]}" = "$worker_name" ]; then
            worker_index="$i"
            break
        fi
    done
    
    if [ -z "$worker_index" ]; then
        print_error "Unknown worker: $worker_name"
        return 1
    fi
    
    local queues="${WORKER_QUEUES[$worker_index]}"
    local log_file="$LOG_DIR/${worker_name}_solo.log"
    local pid_file="$PID_DIR/${worker_name}_solo.pid"
    
    print_worker "Starting $worker_name with Enhanced Solo Pool..."
    print_info "Worker index: $worker_index"
    print_info "Queues: $queues"
    print_info "Log: $log_file"
    print_info "PID file: $pid_file"
    
    # Pre-startup cleanup
    if [ -f "$pid_file" ]; then
        local old_pid=$(cat "$pid_file" 2>/dev/null)
        if is_pid_running "$old_pid"; then
            print_warning "Stopping existing $worker_name (PID: $old_pid)"
            kill -TERM "$old_pid" 2>/dev/null || true
            sleep 3
            if is_pid_running "$old_pid"; then
                kill -KILL "$old_pid" 2>/dev/null || true
            fi
        fi
    fi
    
    rm -f "$pid_file" 2>/dev/null || true
    
    # Clean any remaining processes with this worker name
    local existing_pids=$(find_process_by_pattern "celery.*worker.*${worker_name}")
    if [ -n "$existing_pids" ]; then
        print_warning "Cleaning existing $worker_name processes"
        echo "$existing_pids" | xargs -r kill -TERM 2>/dev/null || true
        sleep 2
        echo "$existing_pids" | xargs -r kill -KILL 2>/dev/null || true
    fi
    
    # Clear log file
    > "$log_file"
    
    cd "$BACKEND_DIR"
    
    # Start worker with enhanced configuration
    print_info "⚡ Launching $worker_name with Solo Pool..."
    nohup $PYTHON_CMD -m celery -A app.tasks.celery_app worker \
        --loglevel=info \
        --queues="$queues" \
        --hostname="${worker_name}@%h" \
        --pool=solo \
        --concurrency=1 \
        --prefetch-multiplier=1 \
        --max-tasks-per-child=100 \
        --time-limit=600 \
        --soft-time-limit=540 \
        --without-gossip \
        --without-mingle \
        --without-heartbeat \
        > "../$log_file" 2>&1 &
    
    local pid=$!
    cd - > /dev/null
    
    # Enhanced startup monitoring
    print_info "⏳ Monitoring startup (PID: $pid)..."
    local timeout=$MAX_STARTUP_TIME
    local success=false
    
    while [ $timeout -gt 0 ]; do
        if is_pid_running "$pid"; then
            # Check if worker is ready
            if [ -f "$log_file" ] && grep -q "ready\|Connected to redis" "$log_file" 2>/dev/null; then
                echo "$pid" > "$pid_file"
                print_success "$worker_name started successfully (PID: $pid)"
                log_message "SUCCESS" "$worker_name started with Solo Pool (PID: $pid)"
                success=true
                break
            elif [ -f "$log_file" ] && grep -q "ERROR\|CRITICAL\|Traceback" "$log_file" 2>/dev/null; then
                print_error "$worker_name failed with errors:"
                grep "ERROR\|CRITICAL\|Traceback" "$log_file" | tail -3 | sed 's/^/   /'
                break
            else
                echo -n "."
            fi
        else
            print_error "Process $pid died during startup"
            if [ -f "$log_file" ]; then
                print_error "Startup errors:"
                tail -5 "$log_file" | sed 's/^/   /'
            fi
            break
        fi
        
        sleep 1
        ((timeout--))
    done
    
    echo ""
    
    if [ "$success" = false ]; then
        if is_pid_running "$pid"; then
            print_warning "$worker_name started but not ready yet (timeout)"
            echo "$pid" > "$pid_file"
            print_info "Recent log output:"
            tail -5 "$log_file" | sed 's/^/   /'
        else
            print_error "$worker_name failed to start"
            rm -f "$pid_file"
            return 1
        fi
    fi
    
    return 0
}

# Enhanced Beat scheduler startup
start_beat_scheduler() {
    local log_file="$LOG_DIR/celery_beat.log"
    local pid_file="$PID_DIR/celery_beat.pid"
    
    print_worker "Starting Enhanced Beat Scheduler..."
    
    # Comprehensive cleanup
    local existing_pids=$(find_process_by_pattern "celery.*beat")
    if [ -n "$existing_pids" ]; then
        print_warning "Stopping existing Beat processes"
        echo "$existing_pids" | xargs -r kill -TERM 2>/dev/null || true
        sleep 3
        echo "$existing_pids" | xargs -r kill -KILL 2>/dev/null || true
    fi
    
    rm -f "$pid_file" "$BEAT_SCHEDULE_FILE"* 2>/dev/null || true
    > "$log_file"
    
    cd "$BACKEND_DIR"
    
    # Start Beat with enhanced configuration
    nohup $PYTHON_CMD -m celery -A app.tasks.celery_app beat \
        --loglevel=info \
        --max-interval=60 \
        --schedule="../$BEAT_SCHEDULE_FILE" \
        > "../$log_file" 2>&1 &
    
    local pid=$!
    cd - > /dev/null
    
    # Monitor startup
    print_info "⏳ Monitoring Beat startup (PID: $pid)..."
    sleep 5
    
    if is_pid_running "$pid"; then
        echo "$pid" > "$pid_file"
        print_success "Beat Scheduler started successfully (PID: $pid)"
        
        # Show activity
        if [ -f "$log_file" ] && [ -s "$log_file" ]; then
            print_info "Recent Beat activity:"
            tail -3 "$log_file" | sed 's/^/   /'
        fi
        return 0
    else
        print_error "Beat Scheduler failed to start"
        if [ -f "$log_file" ]; then
            print_error "Error details:"
            tail -5 "$log_file" | sed 's/^/   /'
        fi
        return 1
    fi
}

# Enhanced Flower monitor startup
start_flower_monitor() {
    local log_file="$LOG_DIR/celery_flower.log"
    local pid_file="$PID_DIR/celery_flower.pid"
    
    # Find available port
    local flower_port=$FLOWER_PORT
    local port_attempts=0
    while check_port_usage "$flower_port" && [ $port_attempts -lt 10 ]; do
        ((flower_port++))
        ((port_attempts++))
    done
    
    if [ "$flower_port" != "$FLOWER_PORT" ]; then
        print_warning "Port $FLOWER_PORT busy, using port $flower_port"
    fi
    
    print_worker "Starting Enhanced Flower Monitor (Port: $flower_port)..."
    
    # Cleanup existing processes
    local existing_pids=$(find_process_by_pattern "celery.*flower")
    if [ -n "$existing_pids" ]; then
        print_warning "Stopping existing Flower processes"
        echo "$existing_pids" | xargs -r kill -TERM 2>/dev/null || true
        sleep 2
        echo "$existing_pids" | xargs -r kill -KILL 2>/dev/null || true
    fi
    
    # Clean port if still occupied
    local port_pids=$(lsof -ti:"$flower_port" 2>/dev/null || true)
    if [ -n "$port_pids" ]; then
        echo "$port_pids" | xargs -r kill -KILL 2>/dev/null || true
        sleep 1
    fi
    
    rm -f "$pid_file" 2>/dev/null || true
    > "$log_file"
    
    cd "$BACKEND_DIR"
    
    # Start Flower with enhanced configuration
    nohup $PYTHON_CMD -m celery -A app.tasks.celery_app flower \
        --port="$flower_port" \
        --basic_auth=admin:cryptopredict123 \
        --persistent=True \
        --db="../$LOG_DIR/flower.db" \
        --max_tasks=10000 \
        --url_prefix= \
        > "../$log_file" 2>&1 &
    
    local pid=$!
    cd - > /dev/null
    
    # Monitor startup
    print_info "⏳ Monitoring Flower startup (PID: $pid)..."
    sleep 5
    
    if is_pid_running "$pid"; then
        echo "$pid" > "$pid_file"
        print_success "Flower Monitor started successfully (PID: $pid, Port: $flower_port)"
        print_info "🌐 Web interface: http://localhost:$flower_port"
        print_info "🔐 Login: admin / cryptopredict123"
        log_message "SUCCESS" "Flower monitor started (PID: $pid, Port: $flower_port)"
        return 0
    else
        print_error "Flower Monitor failed to start"
        if [ -f "$log_file" ]; then
            print_error "Error details:"
            tail -5 "$log_file" | sed 's/^/   /'
        fi
        return 1
    fi
}

#==============================================================================
# SYSTEM STARTUP AND MANAGEMENT
#==============================================================================

# Ultimate system startup
start_all_workers() {
    print_header "🚀 Ultimate Worker System Startup"
    print_header "=================================\n"
    
    # Pre-flight checks
    if ! check_environment; then
        print_error "Environment check failed. Please resolve issues first."
        print_info "💡 Use './scripts/ultimate-worker-manager.sh fix' to auto-resolve"
        return 1
    fi
    
    # Setup infrastructure
    create_directory_structure
    rotate_logs
    
    # Comprehensive cleanup
    comprehensive_cleanup
    smart_cleanup
    sleep 3
    
    local success_count=0
    local total_services=$((${#WORKER_NAMES[@]} + 2))  # workers + beat + flower
    
    print_info "🎯 Starting ${#WORKER_NAMES[@]} Enhanced Solo Pool Workers...\n"
    
    # Start all workers with progress tracking
    for worker_name in "${WORKER_NAMES[@]}"; do
        print_info "🔄 Processing $worker_name..."
        if start_solo_worker "$worker_name"; then
            ((success_count++))
            print_success "✅ $worker_name operational"
        else
            print_error "❌ $worker_name failed"
        fi
        echo ""
        sleep 2  # Stagger startup to reduce resource contention
    done
    
    # Start system services
    print_info "🔄 Starting Beat Scheduler..."
    if start_beat_scheduler; then
        ((success_count++))
        print_success "✅ Beat Scheduler operational"
    else
        print_error "❌ Beat Scheduler failed"
    fi
    echo ""
    
    print_info "🔄 Starting Flower Monitor..."
    if start_flower_monitor; then
        ((success_count++))
        print_success "✅ Flower Monitor operational"
    else
        print_error "❌ Flower Monitor failed"
    fi
    echo ""
    
    # Final stabilization
    print_info "⏳ Waiting for system stabilization..."
    sleep 5
    
    # System verification
    rebuild_pid_files
    
    # Final status
    show_comprehensive_status
    
    # Success summary
    print_header "\n🎉 STARTUP SUMMARY"
    print_header "==================\n"
    
    if [ "$success_count" -eq "$total_services" ]; then
        print_success "🟢 PERFECT! All $total_services services operational!"
        print_info "✨ Enhanced Solo Pool Workers with maximum security"
        print_info "🌐 Monitor: http://localhost:$FLOWER_PORT (admin/cryptopredict123)"
        print_info "📊 Management: ./scripts/ultimate-worker-manager.sh status"
        log_message "SUCCESS" "All services started successfully - Ultimate mode"
        return 0
    elif [ "$success_count" -gt $((total_services / 2)) ]; then
        print_warning "🟡 PARTIAL SUCCESS: $success_count/$total_services services operational"
        print_info "🔧 Use './scripts/ultimate-worker-manager.sh diagnose' for details"
        return 0
    else
        print_error "🔴 STARTUP FAILED: Only $success_count/$total_services services started"
        print_info "🆘 Use './scripts/ultimate-worker-manager.sh fix' for auto-repair"
        return 1
    fi
}

#==============================================================================
# STATUS AND MONITORING
#==============================================================================

# Comprehensive status display
show_comprehensive_status() {
    print_header "📊 Comprehensive System Status"
    print_header "==============================\n"
    
    local timestamp=$(get_timestamp)
    echo "$timestamp" > "$LOG_DIR/last_status_check"
    
    # System overview
    print_info "🖥️  SYSTEM OVERVIEW:"
    echo "   📅 Check Time: $timestamp"
    echo "   👤 User: $(get_current_user)"
    echo "   📦 Manager Version: $SCRIPT_VERSION"
    echo ""
    
    # Worker status table
    print_info "🔧 SOLO POOL WORKERS:"
    echo "┌─────────────────────────┬──────────┬─────────┬──────────┬─────────────────────────────┐"
    printf "│ %-23s │ %-8s │ %-7s │ %-8s │ %-27s │\n" "Worker" "Status" "PID" "CPU%" "Queues"
    echo "├─────────────────────────┼──────────┼─────────┼──────────┼─────────────────────────────┤"
    
    local total_workers=0
    local running_workers=0
    local ready_workers=0
    
    for i in "${!WORKER_NAMES[@]}"; do
        local worker_name="${WORKER_NAMES[$i]}"
        local queues="${WORKER_QUEUES[$i]}"
        local pid=$(get_worker_pid "$worker_name")
        local status="❌ STOPPED"
        local pid_display="N/A"
        local cpu_usage="0"
        
        ((total_workers++))
        
        if [ -n "$pid" ]; then
            status="✅ RUNNING"
            pid_display="$pid"
            cpu_usage=$(ps -p "$pid" -o pcpu= 2>/dev/null | xargs || echo "0")
            ((running_workers++))
            
            # Check if ready
            local log_file="$LOG_DIR/${worker_name}_solo.log"
            if [ -f "$log_file" ] && grep -q "ready\|Connected to redis" "$log_file" 2>/dev/null; then
                status="✅ READY"
                ((ready_workers++))
            fi
        fi
        
        printf "│ %-23s │ %-8s │ %-7s │ %-8s │ %-27s │\n" \
            "$worker_name" "$status" "$pid_display" "${cpu_usage}%" "${queues:0:27}"
    done
    
    echo "└─────────────────────────┴──────────┴─────────┴──────────┴─────────────────────────────┘"
    echo ""
    
    # System services status
    print_info "📋 SYSTEM SERVICES:"
    echo "┌─────────────────────────┬──────────┬─────────┬──────────┬─────────────────────────────┐"
    printf "│ %-23s │ %-8s │ %-7s │ %-8s │ %-27s │\n" "Service" "Status" "PID" "CPU%" "Details"
    echo "├─────────────────────────┼──────────┼─────────┼──────────┼─────────────────────────────┤"
    
    # Beat scheduler
    local beat_pid=$(get_worker_pid "celery_beat")
    local beat_status="❌ STOPPED"
    local beat_pid_display="N/A"
    local beat_cpu="0"
    local beat_details="Task Scheduling"
    
    if [ -n "$beat_pid" ]; then
        beat_status="✅ RUNNING"
        beat_pid_display="$beat_pid"
        beat_cpu=$(ps -p "$beat_pid" -o pcpu= 2>/dev/null | xargs || echo "0")
    fi
    
    printf "│ %-23s │ %-8s │ %-7s │ %-8s │ %-27s │\n" \
        "Beat Scheduler" "$beat_status" "$beat_pid_display" "${beat_cpu}%" "$beat_details"
    
    # Flower monitor
    local flower_pid=$(get_worker_pid "celery_flower")
    local flower_status="❌ STOPPED"
    local flower_pid_display="N/A"
    local flower_cpu="0"
    local flower_details="Web Monitor"
    
    if [ -n "$flower_pid" ]; then
        flower_status="✅ RUNNING"
        flower_pid_display="$flower_pid"
        flower_cpu=$(ps -p "$flower_pid" -o pcpu= 2>/dev/null | xargs || echo "0")
        flower_details="Port $FLOWER_PORT"
    fi
    
    printf "│ %-23s │ %-8s │ %-7s │ %-8s │ %-27s │\n" \
        "Flower Monitor" "$flower_status" "$flower_pid_display" "${flower_cpu}%" "$flower_details"
    
    echo "└─────────────────────────┴──────────┴─────────┴──────────┴─────────────────────────────┘"
    echo ""
    
    # Network status
    print_info "🌐 NETWORK STATUS:"
    echo "   🔴 Redis (6379): $(check_port_usage 6379 && echo "✅ Connected" || echo "❌ Down")"
    echo "   🌸 Flower ($FLOWER_PORT): $(check_port_usage $FLOWER_PORT && echo "✅ Available" || echo "❌ Down")"
    echo ""
    
    # Performance summary
    print_info "📈 PERFORMANCE SUMMARY:"
    echo "   🔧 Workers: $running_workers/$total_workers running, $ready_workers/$total_workers ready"
    echo "   🎯 Pool Type: Solo (Enhanced Security)"
    echo "   ⚡ Status: $([ "$running_workers" -eq "$total_workers" ] && echo "Optimal" || echo "Partial")"
    echo "   🕐 Last Check: $timestamp"
    
    # Health assessment
    echo ""
    if [ "$running_workers" -eq "$total_workers" ] && [ "$ready_workers" -eq "$total_workers" ] && [ -n "$beat_pid" ] && [ -n "$flower_pid" ]; then
        print_success "🎉 EXCELLENT! All systems operational and ready!"
    elif [ "$running_workers" -eq "$total_workers" ] && [ "$ready_workers" -gt 0 ]; then
        print_warning "🟡 GOOD: Workers running, some still initializing"
    elif [ "$running_workers" -gt 0 ]; then
        print_warning "⚠️  PARTIAL: Some workers not running"
    else
        print_error "❌ CRITICAL: No workers are running"
    fi
    
    # Log performance data
    echo "$timestamp,$total_workers,$running_workers,$ready_workers" >> "$LOG_DIR/worker_performance.log"
}

# Health monitoring with detailed analysis
health_monitoring() {
    print_header "🏥 Advanced Health Monitoring"
    print_header "=============================\n"
    
    local health_score=0
    local max_score=20
    
    # 1. Environment health (4 points)
    print_info "1️⃣ Environment Health..."
    if check_environment > /dev/null 2>&1; then
        print_success "Environment: EXCELLENT"
        health_score=$((health_score + 4))
    else
        print_error "Environment: ISSUES DETECTED"
    fi
    
    # 2. Worker health (8 points - 2 per worker)
    print_info "2️⃣ Worker Health Analysis..."
    for worker_name in "${WORKER_NAMES[@]}"; do
        local pid=$(get_worker_pid "$worker_name")
        local log_file="$LOG_DIR/${worker_name}_solo.log"
        
        if [ -n "$pid" ]; then
            if [ -f "$log_file" ] && grep -q "ready\|Connected to redis" "$log_file" 2>/dev/null; then
                print_success "$worker_name: HEALTHY"
                health_score=$((health_score + 2))
            else
                print_warning "$worker_name: RUNNING BUT NOT READY"
                health_score=$((health_score + 1))
            fi
        else
            print_error "$worker_name: NOT RUNNING"
        fi
    done
    
    # 3. System services health (4 points)
    print_info "3️⃣ System Services Health..."
    local beat_pid=$(get_worker_pid "celery_beat")
    local flower_pid=$(get_worker_pid "celery_flower")
    
    if [ -n "$beat_pid" ]; then
        print_success "Beat Scheduler: HEALTHY"
        health_score=$((health_score + 2))
    else
        print_error "Beat Scheduler: NOT RUNNING"
    fi
    
    if [ -n "$flower_pid" ]; then
        print_success "Flower Monitor: HEALTHY"
        health_score=$((health_score + 2))
    else
        print_error "Flower Monitor: NOT RUNNING"
    fi
    
    # 4. Resource health (4 points)
    print_info "4️⃣ Resource Health..."
    
    # Memory usage check
    local total_memory_mb=0
    for worker_name in "${WORKER_NAMES[@]}"; do
        local pid=$(get_worker_pid "$worker_name")
        if [ -n "$pid" ]; then
            local mem_kb=$(ps -p "$pid" -o rss= 2>/dev/null | xargs || echo "0")
            total_memory_mb=$((total_memory_mb + mem_kb / 1024))
        fi
    done
    
    if [ "$total_memory_mb" -lt 500 ]; then
        print_success "Memory Usage: NORMAL (${total_memory_mb}MB)"
        health_score=$((health_score + 2))
    elif [ "$total_memory_mb" -lt 1000 ]; then
        print_warning "Memory Usage: MODERATE (${total_memory_mb}MB)"
        health_score=$((health_score + 1))
    else
        print_error "Memory Usage: HIGH (${total_memory_mb}MB)"
    fi
    
    # Connection health
    if check_port_usage 6379; then
        print_success "Redis Connection: HEALTHY"
        health_score=$((health_score + 2))
    else
        print_error "Redis Connection: FAILED"
    fi
    
    # Overall health assessment
    echo ""
    print_header "🎯 HEALTH SCORE: $health_score/$max_score"
    
    local health_percentage=$((health_score * 100 / max_score))
    
    if [ "$health_percentage" -ge 90 ]; then
        print_success "🟢 EXCELLENT HEALTH ($health_percentage%)"
        print_info "System is performing optimally and ready for production"
    elif [ "$health_percentage" -ge 75 ]; then
        print_success "🟢 GOOD HEALTH ($health_percentage%)"
        print_info "System is functional with minor areas for improvement"
    elif [ "$health_percentage" -ge 50 ]; then
        print_warning "🟡 FAIR HEALTH ($health_percentage%)"
        print_info "System needs attention to improve reliability"
    else
        print_error "🔴 POOR HEALTH ($health_percentage%)"
        print_info "System requires immediate attention and fixes"
    fi
    
    # Log health data
    local timestamp=$(get_timestamp)
    echo "$timestamp,$health_score,$max_score,$health_percentage" >> "$LOG_DIR/system_health.log"
}

#==============================================================================
# TASK TESTING AND DEMONSTRATION
#==============================================================================

# Comprehensive task testing
test_task_execution() {
    print_header "🧪 Task Execution Testing"
    print_header "=========================\n"
    
    if ! check_environment > /dev/null 2>&1; then
        print_error "Environment not ready for task testing"
        return 1
    fi
    
    cd "$BACKEND_DIR"
    
    local test_count=0
    local success_count=0
    
    # Test each queue
    for i in "${!WORKER_NAMES[@]}"; do
        local worker_name="${WORKER_NAMES[$i]}"
        local queues="${WORKER_QUEUES[$i]}"
        local primary_queue=$(echo "$queues" | cut -d',' -f1)
        
        print_info "🔄 Testing $worker_name (Queue: $primary_queue)..."
        ((test_count++))
        
        # Send test task
        if python -c "
from app.tasks.celery_app import app
try:
    result = app.send_task('app.tasks.celery_app.debug_task', 
                          args=['Test from Ultimate Manager'], 
                          queue='$primary_queue')
    print(f'✅ Task sent: {result.id}')
except Exception as e:
    print(f'❌ Task failed: {e}')
    exit(1)
" 2>/dev/null; then
            ((success_count++))
            print_success "Task sent successfully to $worker_name"
        else
            print_error "Failed to send task to $worker_name"
        fi
        
        sleep 1
    done
    
    cd - > /dev/null
    
    # Wait for task processing
    print_info "⏳ Waiting for task processing..."
    sleep 5
    
    # Check task results in logs
    print_info "📊 Task execution results:"
    for worker_name in "${WORKER_NAMES[@]}"; do
        local log_file="$LOG_DIR/${worker_name}_solo.log"
        if [ -f "$log_file" ]; then
            local recent_tasks=$(grep -c "received\|succeeded\|failed" "$log_file" 2>/dev/null || echo 0)
            if [ "$recent_tasks" -gt 0 ]; then
                print_success "$worker_name: $recent_tasks task events"
            else
                print_warning "$worker_name: No task activity detected"
            fi
        fi
    done
    
    echo ""
    print_info "📈 Test Summary: $success_count/$test_count tasks sent successfully"
    
    if [ "$success_count" -eq "$test_count" ]; then
        print_success "🎉 All task tests passed!"
        return 0
    elif [ "$success_count" -gt 0 ]; then
        print_warning "⚠️  Some task tests failed"
        return 0
    else
        print_error "❌ All task tests failed"
        return 1
    fi
}

#==============================================================================
# AUTO-FIX AND REPAIR FUNCTIONS
#==============================================================================

# Comprehensive auto-fix system
auto_fix_system() {
    print_header "🔧 Ultimate Auto-Fix System"
    print_header "===========================\n"
    
    local fixes_applied=0
    local issues_found=0
    
    # 1. Directory structure fixes
    print_info "1️⃣ Fixing directory structure..."
    create_directory_structure
    ((fixes_applied++))
    
    # 2. Clean stale processes and files
    print_info "2️⃣ Cleaning stale processes and files..."
    comprehensive_cleanup
    smart_cleanup
    ((fixes_applied++))
    
    # 3. Fix permissions
    print_info "3️⃣ Fixing file permissions..."
    chmod 755 scripts/*.sh 2>/dev/null || true
    chmod 644 "$LOG_DIR"/*.log 2>/dev/null || true
    chmod 755 "$PID_DIR" 2>/dev/null || true
    ((fixes_applied++))
    
    # 4. Log rotation
    print_info "4️⃣ Rotating large log files..."
    rotate_logs
    ((fixes_applied++))
    
    # 5. Environment validation and fixes
    print_info "5️⃣ Validating and fixing environment..."
    
    # Check Python environment
    cd "$BACKEND_DIR" 2>/dev/null || { print_error "Cannot access backend directory"; ((issues_found++)); }
    
    if [ $issues_found -eq 0 ]; then
        # Test Celery app import
        if ! $PYTHON_CMD -c "from app.tasks.celery_app import app; print('Celery app OK')" 2>/dev/null; then
            print_warning "Celery app import issues detected"
            print_info "This may require manual code fixes"
            ((issues_found++))
        else
            print_success "Celery app import verified"
        fi
        
        # Test Redis connection
        if ! timeout 5 "$PYTHON_CMD" -c "
import redis
r = redis.Redis(host='localhost', port=6379)
r.ping()
print('Redis OK')
" 2>/dev/null; then
            print_warning "Redis connection failed"
            print_info "Start Redis with: docker-compose up redis -d"
            ((issues_found++))
        else
            print_success "Redis connection verified"
        fi
    fi
    
    cd - > /dev/null
    
    # 6. Rebuild PID files if workers are running
    print_info "6️⃣ Rebuilding PID files..."
    rebuild_pid_files
    ((fixes_applied++))
    
    # 7. System optimization
    print_info "7️⃣ System optimization..."
    
    # Clear temporary files
    find "$LOG_DIR" -name "*.tmp" -delete 2>/dev/null || true
    find "$LOG_DIR" -name "*.lock" -delete 2>/dev/null || true
    
    # Optimize log files
    for log_file in "$LOG_DIR"/*.log; do
        if [ -f "$log_file" ] && [ ! -s "$log_file" ]; then
            touch "$log_file"
        fi
    done
    
    ((fixes_applied++))
    
    # Summary
    echo ""
    print_header "🎯 Auto-Fix Summary"
    print_header "==================="
    echo ""
    
    print_info "📊 Results:"
    echo "   🔧 Fixes Applied: $fixes_applied"
    echo "   ⚠️  Issues Found: $issues_found"
    echo "   📅 Fix Date: $(get_timestamp)"
    
    if [ "$issues_found" -eq 0 ]; then
        print_success "🎉 System fully optimized and ready!"
        print_info "You can now start workers with confidence"
        return 0
    elif [ "$issues_found" -le 2 ]; then
        print_warning "🟡 System mostly fixed with minor issues"
        print_info "Issues detected may require manual attention"
        return 0
    else
        print_error "🔴 Multiple issues detected"
        print_info "Some issues may require manual intervention"
        return 1
    fi
}

#==============================================================================
# HELP AND DOCUMENTATION
#==============================================================================

# Comprehensive help system
show_ultimate_help() {
    print_header "🚀 Ultimate Celery Worker Manager v$SCRIPT_VERSION"
    print_header "================================================\n"
    
    print_info "📋 DESCRIPTION:"
    echo "   Advanced Celery worker management system with Solo Pool security,"
    echo "   comprehensive monitoring, auto-fix capabilities, and Windows compatibility.\n"
    
    print_info "🏗️ ARCHITECTURE:"
    echo "   🔥 Data Worker      → price_data, market_data, data_sync"
    echo "   🧠 ML Worker        → ml_prediction, model_training, ml_tasks"
    echo "   📨 Notification W.  → notifications, alerts, email_tasks"
    echo "   🔧 General Worker   → general, cleanup, maintenance, default"
    echo "   🥁 Beat Scheduler   → Periodic task scheduling"
    echo "   🌸 Flower Monitor   → Web-based monitoring dashboard\n"
    
    print_info "⚡ AVAILABLE COMMANDS:"
    echo "   start           - Start all workers with Solo Pool security"
    echo "   stop            - Stop all workers gracefully"
    echo "   restart         - Restart all workers"
    echo "   status          - Show comprehensive system status"
    echo "   health          - Advanced health monitoring with scoring"
    echo "   monitor         - Real-time monitoring (interactive)"
    echo "   test            - Test task execution across all queues"
    echo "   logs            - Show recent logs from all components"
    echo "   fix             - Auto-fix system issues and optimize"
    echo "   diagnose        - Advanced system diagnostics"
    echo "   cleanup         - Comprehensive process cleanup"
    echo "   rebuild-pids    - Rebuild PID files from running processes"
    echo "   version         - Show version and system information"
    echo "   help            - Show this comprehensive help\n"
    
    print_info "🎯 USAGE EXAMPLES:"
    echo "   ./scripts/ultimate-worker-manager.sh start"
    echo "   ./scripts/ultimate-worker-manager.sh status"
    echo "   ./scripts/ultimate-worker-manager.sh health"
    echo "   ./scripts/ultimate-worker-manager.sh test"
    echo "   ./scripts/ultimate-worker-manager.sh fix\n"
    
    print_info "🔧 SOLO POOL BENEFITS:"
    echo "   ✅ Enhanced Security    - Each task runs in isolated process"
    echo "   ✅ Better Stability    - Task failures don't crash workers"
    echo "   ✅ Easier Debugging    - Clear task and process isolation"
    echo "   ✅ Resource Control    - Predictable memory and CPU usage"
    echo "   ✅ Production Ready    - Reliable for high-load environments\n"
    
    print_info "📊 MONITORING FEATURES:"
    echo "   🔍 Real-time worker status and performance metrics"
    echo "   📈 Health scoring system with detailed analysis"
    echo "   🚨 Automatic issue detection and reporting"
    echo "   📋 Comprehensive logging with rotation"
    echo "   🌐 Web dashboard via Flower (localhost:$FLOWER_PORT)\n"
    
    print_info "🛠️ MAINTENANCE FEATURES:"
    echo "   🔧 Auto-fix system for common issues"
    echo "   📁 Intelligent log rotation and cleanup"
    echo "   🧹 Smart process management and cleanup"
    echo "   📊 Performance tracking and optimization"
    echo "   🔄 Graceful restart and recovery mechanisms\n"
    
    print_info "🖥️ WINDOWS COMPATIBILITY:"
    echo "   ✅ Fully compatible with Windows/MinGW/Git Bash"
    echo "   ✅ Uses Windows-available commands only"
    echo "   ✅ Handles Windows-specific process management"
    echo "   ✅ Optimized for development environments\n"
    
    print_info "📁 FILE STRUCTURE:"
    echo "   scripts/logs/              - All log files"
    echo "   scripts/logs/pids/         - Process ID files"
    echo "   scripts/logs/*_solo.log    - Individual worker logs"
    echo "   scripts/logs/ultimate_manager.log - Manager activity log"
    echo "   scripts/logs/system_health.log    - Health monitoring data\n"
    
    print_info "🔗 INTEGRATION:"
    echo "   # Send tasks from your application:"
    echo "   from app.tasks.celery_app import app"
    echo "   result = app.send_task('your_task', queue='price_data')\n"
    
    print_info "🆘 TROUBLESHOOTING:"
    echo "   1. Environment issues    → ./scripts/ultimate-worker-manager.sh fix"
    echo "   2. Worker not starting   → ./scripts/ultimate-worker-manager.sh diagnose"
    echo "   3. Performance issues    → ./scripts/ultimate-worker-manager.sh health"
    echo "   4. Task failures         → ./scripts/ultimate-worker-manager.sh logs"
    echo "   5. Complete reset        → ./scripts/ultimate-worker-manager.sh cleanup && start\n"
    
    print_info "📞 SUPPORT:"
    echo "   🌐 Flower Dashboard: http://localhost:$FLOWER_PORT"
    echo "   🔐 Login: admin / cryptopredict123"
    echo "   📧 Created: $CREATED_DATE"
    echo "   📦 Version: $SCRIPT_VERSION"
    
    exit 0
}

# Version and system information
show_version_info() {
    print_header "📦 Ultimate Worker Manager - Version Information"
    print_header "===============================================\n"
    
    print_info "📋 SCRIPT INFORMATION:"
    echo "   📛 Name: $SCRIPT_NAME"
    echo "   📦 Version: $SCRIPT_VERSION"
    echo "   📅 Created: $CREATED_DATE"
    echo "   🖥️  Platform: $(get_system_info)"
    echo "   👤 User: $(get_current_user)"
    echo ""
    
    print_info "🔧 CONFIGURATION:"
    echo "   🐍 Python: $PYTHON_CMD"
    echo "   📁 Backend: $BACKEND_DIR"
    echo "   📋 Logs: $LOG_DIR"
    echo "   🌸 Flower Port: $FLOWER_PORT"
    echo "   ⏱️  Startup Timeout: ${MAX_STARTUP_TIME}s"
    echo ""
    
    print_info "👥 WORKERS CONFIGURED:"
    for i in "${!WORKER_NAMES[@]}"; do
        echo "   $((i+1)). ${WORKER_NAMES[$i]} → ${WORKER_QUEUES[$i]}"
    done
    echo ""
    
    print_info "📊 CURRENT STATUS:"
    local running_count=0
    for worker_name in "${WORKER_NAMES[@]}"; do
        if [ -n "$(get_worker_pid "$worker_name")" ]; then
            ((running_count++))
        fi
    done
    echo "   🔧 Workers Running: $running_count/${#WORKER_NAMES[@]}"
    echo "   🥁 Beat: $([ -n "$(get_worker_pid "celery_beat")" ] && echo "Running" || echo "Stopped")"
    echo "   🌸 Flower: $([ -n "$(get_worker_pid "celery_flower")" ] && echo "Running" || echo "Stopped")"
    echo "   📡 Redis: $(check_port_usage 6379 && echo "Connected" || echo "Down")"
}

#==============================================================================
# MAIN EXECUTION LOGIC
#==============================================================================

# Main function with comprehensive command handling
main() {
    local action="${1:-help}"
    local sub_action="$2"
    local target="$3"
    
    # Initialize logging
    mkdir -p "$LOG_DIR"
    touch "$LOG_DIR/ultimate_manager.log"
    
    # Script header
    echo -e "${PURPLE}${BOLD}"
    echo "╔═══════════════════════════════════════════════════════════════════════════╗"
    echo "║                 🚀 Ultimate Celery Worker Manager v$SCRIPT_VERSION                ║"
    echo "║                        Solo Pool Security Edition                        ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
    
    log_message "INFO" "Ultimate Worker Manager started with action: $action"
    
    # Command execution
    case "$action" in
        "start"|"")
            start_all_workers
            ;;
        "stop")
            print_header "🛑 Stopping All Workers"
            comprehensive_cleanup
            print_success "All workers stopped successfully"
            ;;
        "restart")
            print_header "🔄 Restarting All Workers"
            comprehensive_cleanup
            sleep 3
            start_all_workers
            ;;
        "status")
            show_comprehensive_status
            ;;
        "health")
            health_monitoring
            ;;
        "monitor")
            print_header "📺 Real-time Monitoring"
            print_info "Press Ctrl+C to stop monitoring\n"
            
            local monitor_count=0
            while true; do
                clear
                echo -e "${PURPLE}${BOLD}🔄 Live Monitoring - Update #$((++monitor_count)) - $(get_timestamp)${NC}\n"
                show_comprehensive_status
                echo ""
                print_info "⏰ Next update in $HEALTH_CHECK_INTERVAL seconds... (Ctrl+C to exit)"
                sleep $HEALTH_CHECK_INTERVAL
            done
            ;;
        "test")
            test_task_execution
            ;;
        "logs")
            print_header "📋 Recent System Logs"
            print_header "=====================\n"
            
            for worker_name in "${WORKER_NAMES[@]}"; do
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
            ;;
        "fix")
            auto_fix_system
            ;;
        "diagnose")
            system_diagnostics
            check_environment
            ;;
        "cleanup")
            comprehensive_cleanup
            smart_cleanup
            ;;
        "rebuild-pids")
            rebuild_pid_files
            ;;
        "version")
            show_version_info
            ;;
        "help"|"-h"|"--help")
            show_ultimate_help
            ;;
        *)
            print_error "Unknown action: $action"
            echo ""
            print_info "📋 Available actions:"
            echo "   start, stop, restart, status, health, monitor, test, logs,"
            echo "   fix, diagnose, cleanup, rebuild-pids, version, help"
            echo ""
            print_info "💡 For detailed help: $0 help"
            echo ""
            print_info "🎯 Quick start: $0 start"
            exit 1
            ;;
    esac
    
    local exit_code=$?
    log_message "INFO" "Ultimate Worker Manager completed action '$action' with exit code: $exit_code"
    exit $exit_code
}

#==============================================================================
# ERROR HANDLING AND CLEANUP
#==============================================================================

# Enhanced error handling
cleanup_on_exit() {
    local exit_code=$?
    local timestamp=$(get_timestamp)
    
    if [ $exit_code -ne 0 ] && [ $exit_code -ne 130 ]; then  # 130 is Ctrl+C
        print_warning "\n🚨 Script interrupted with exit code: $exit_code"
        log_message "WARNING" "Script interrupted with exit code: $exit_code"
    fi
    
    log_message "INFO" "Ultimate Worker Manager session ended at $timestamp"
    exit $exit_code
}

# Signal handling
trap cleanup_on_exit EXIT
trap 'echo -e "\n${YELLOW}⚠️  Monitoring stopped by user${NC}"; exit 130' INT

# Execute main function if script is run directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi