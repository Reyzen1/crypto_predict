#!/bin/bash
# File: scripts/run-workers.sh
# Ultimate Celery Worker Manager - Fixed PID Detection Issue
# Fixed the PID detection problem for Beat and Flower

# Remove set -e to prevent script from exiting on first error
# set -e

#==============================================================================
# CONFIGURATION & CONSTANTS
#==============================================================================

# Version and metadata
SCRIPT_VERSION="2.0.2"
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

# Enhanced logging with timestamps - FIXED VERSION
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Ensure log directory exists before writing
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR" 2>/dev/null || true
    fi
    
    # Only write to log file if directory exists
    if [ -d "$LOG_DIR" ]; then
        echo "[$timestamp] [$level] $message" >> "$LOG_DIR/ultimate_manager.log" 2>/dev/null || true
    fi
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
get_system_info() { uname -a 2>/dev/null || echo "unknown"; }

# FIXED: Enhanced PID management with better detection
is_pid_running() {
    local pid="$1"
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

# FIXED: Better worker PID detection
get_worker_pid() {
    local worker_name="$1"
    local pid_file="$PID_DIR/${worker_name}_solo.pid"
    
    # Special handling for Beat and Flower (they don't have _solo suffix in PID files)
    if [ "$worker_name" = "celery_beat" ]; then
        pid_file="$PID_DIR/celery_beat.pid"
    elif [ "$worker_name" = "celery_flower" ]; then
        pid_file="$PID_DIR/celery_flower.pid"
    fi
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file" 2>/dev/null | tr -d '\r\n ')  # Remove any whitespace/newlines
        if [ -n "$pid" ] && is_pid_running "$pid"; then
            echo "$pid"
        else
            # PID file exists but process is dead, clean it up
            rm -f "$pid_file" 2>/dev/null || true
            return 1
        fi
    else
        return 1
    fi
}

# Cross-platform process finder - IMPROVED
find_process_by_pattern() {
    local pattern="$1"
    # Use ps aux which works on both Linux and Windows/MinGW
    ps aux 2>/dev/null | grep -E "$pattern" | grep -v grep | awk '{print $2}' | head -1 || true
}

# FIXED: Better process detection with fallback
get_process_pid_by_pattern() {
    local pattern="$1"
    local service_name="$2"
    
    # Try PID file first
    local pid=$(get_worker_pid "$service_name" 2>/dev/null)
    if [ -n "$pid" ]; then
        echo "$pid"
        return 0
    fi
    
    # Fallback to pattern matching
    local found_pid=$(find_process_by_pattern "$pattern")
    if [ -n "$found_pid" ]; then
        echo "$found_pid"
        return 0
    fi
    
    return 1
}

# Safe kill function for Windows/MinGW compatibility
safe_kill() {
    local pid="$1"
    local signal="${2:-TERM}"
    
    if [ -n "$pid" ] && is_pid_running "$pid"; then
        kill -"$signal" "$pid" 2>/dev/null || true
        return 0
    fi
    return 1
}

# Enhanced port checking
check_port_usage() {
    local port="$1"
    netstat -tuln 2>/dev/null | grep -q ":$port " || netstat -an 2>/dev/null | grep -q ":$port "
}

#==============================================================================
# DIRECTORY AND FILE MANAGEMENT - MOVED TO TOP
#==============================================================================

# Enhanced directory structure creation - CALLED FIRST
create_directory_structure() {
    print_info "📁 Setting up enhanced directory structure..."
    
    # Create directories with proper permissions
    mkdir -p "$LOG_DIR" "$PID_DIR" 2>/dev/null || true
    
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
            touch "$log_file" 2>/dev/null || true
        fi
    done
    
    # Set proper permissions if on Unix-like system
    if command -v chmod >/dev/null 2>&1; then
        chmod 755 "$LOG_DIR" "$PID_DIR" 2>/dev/null || true
        chmod 644 "$LOG_DIR"/*.log 2>/dev/null || true
    fi
    
    print_success "Directory structure created successfully"
}

# Log rotation for large files
rotate_logs() {
    local max_size=10485760  # 10MB in bytes
    
    for log_file in "$LOG_DIR"/*.log; do
        if [ -f "$log_file" ] && [ "$(wc -c < "$log_file" 2>/dev/null || echo 0)" -gt "$max_size" ]; then
            local backup_file="${log_file}.$(date +%Y%m%d_%H%M%S).bak"
            mv "$log_file" "$backup_file" 2>/dev/null || true
            touch "$log_file" 2>/dev/null || true
            print_info "Rotated large log: $(basename "$log_file")"
        fi
    done
}

#==============================================================================
# ENVIRONMENT VALIDATION
#==============================================================================

# Comprehensive environment validation
validate_environment() {
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
    
    # Backend directory check
    print_info "📁 Backend Directory Check:"
    if [ ! -d "$BACKEND_DIR" ]; then
        print_error "Backend directory not found: $BACKEND_DIR"
        ((issues++))
    else
        print_success "Backend directory found: $BACKEND_DIR"
    fi
    
    # Python environment check
    print_info "🐍 Python Environment Check:"
    if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
        print_error "Python not found: $PYTHON_CMD"
        ((issues++))
    else
        local python_version=$($PYTHON_CMD --version 2>/dev/null || echo "Unknown")
        print_success "Python found: $python_version"
    fi
    
    # Python dependencies check
    if [ "$issues" -eq 0 ]; then
        print_info "📦 Python Dependencies Check:"
        cd "$BACKEND_DIR" 2>/dev/null || true
        
        # Check celery
        if $PYTHON_CMD -c "import celery" 2>/dev/null; then
            print_success "celery module available"
        else
            print_error "celery module not found"
            ((issues++))
        fi
        
        # Check redis
        if $PYTHON_CMD -c "import redis" 2>/dev/null; then
            print_success "redis module available"
        else
            print_error "redis module not found"
            ((issues++))
        fi
        
        # Check app modules
        if $PYTHON_CMD -c "import app.tasks.celery_app" 2>/dev/null; then
            print_success "app.tasks.celery_app module available"
        else
            print_error "app.tasks.celery_app module not found"
            ((issues++))
        fi
        
        cd - > /dev/null 2>&1 || true
    fi
    
    # Redis connectivity check
    print_info "📡 Redis Connectivity Check:"
    if command -v "$PYTHON_CMD" >/dev/null 2>&1 && [ "$issues" -eq 0 ]; then
        if timeout 5 "$PYTHON_CMD" -c "
import redis
r = redis.Redis(host='localhost', port=6379)
r.ping()
print('Redis connection successful')
" 2>/dev/null; then
            print_success "Redis connection verified"
        else
            print_error "Redis connection failed - start Redis with: docker-compose up redis -d"
            ((issues++))
        fi
    else
        print_warning "Skipping Redis check due to previous issues"
        ((warnings++))
    fi
    
    # Port availability check
    print_info "🌐 Port Availability Check:"
    if check_port_usage 6379; then
        print_success "Redis port 6379 is listening"
    else
        print_warning "Redis port 6379 not listening"
        ((warnings++))
    fi
    
    if check_port_usage "$FLOWER_PORT"; then
        print_warning "Flower port $FLOWER_PORT is already in use"
        ((warnings++))
    else
        print_success "Flower port $FLOWER_PORT is available"
    fi
    
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

#==============================================================================
# PROCESS CLEANUP AND MANAGEMENT
#==============================================================================

# Comprehensive process cleanup - FIXED
comprehensive_cleanup() {
    print_header "🧹 Comprehensive Process Cleanup"
    echo "================================="
    echo
    
    local cleanup_count=0

    # Kill everything
    pkill -f "celery" 2>/dev/null || true
    taskkill //F //IM "python.exe" 2>/dev/null || true
    
    # Kill workers gracefully first
    print_info "1️⃣ Graceful worker shutdown..."
    for worker_name in "${WORKER_NAMES[@]}"; do
        local pid=$(get_worker_pid "$worker_name")
        if [ -n "$pid" ]; then
            print_info "Stopping $worker_name (PID: $pid)"
            safe_kill "$pid" "TERM"
            ((cleanup_count++))
        fi
    done
    
    # Kill system services
    print_info "2️⃣ System services shutdown..."
    for service in "celery_beat" "celery_flower"; do
        local pid=$(get_worker_pid "$service")
        if [ -n "$pid" ]; then
            print_info "Stopping $service (PID: $pid)"
            safe_kill "$pid" "TERM"
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
            print_info "Killing $pattern processes: $pids"
            echo "$pids" | while read -r pid; do
                [ -n "$pid" ] && safe_kill "$pid" "KILL"
            done
            ((cleanup_count++))
        fi
    done
    
    # Clean PID files
    print_info "4️⃣ Cleaning PID files..."
    rm -f "$PID_DIR"/*.pid 2>/dev/null || true
    
    # Clean problematic files
    print_info "5️⃣ Cleaning problematic files..."
    rm -f "$LOG_DIR"/*.lock 2>/dev/null || true
    rm -f "$LOG_DIR"/*.tmp 2>/dev/null || true
    rm -f "$BEAT_SCHEDULE_FILE"* 2>/dev/null || true
    
    print_success "Cleanup completed successfully"
}

# Smart cleanup based on process detection
smart_cleanup() {
    print_info "🤖 Smart cleanup based on process detection..."
    
    # Find zombie and stuck processes
    local stuck_processes=$(ps aux 2>/dev/null | grep -E "(celery.*<defunct>|celery.*zombie)" | wc -l)
    if [ "$stuck_processes" -gt 0 ]; then
        print_warning "Found $stuck_processes stuck/zombie processes"
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
                sleep 1
                ((timeout--))
            fi
        else
            print_error "$worker_name process died unexpectedly"
            if [ -f "$log_file" ] && [ -s "$log_file" ]; then
                print_error "Last log entries:"
                tail -5 "$log_file" | sed 's/^/   /'
            fi
            break
        fi
    done
    
    if [ "$success" = false ]; then
        print_error "$worker_name startup failed or timed out"
        return 1
    fi
    
    return 0
}

# Start all solo workers - IMPROVED ERROR HANDLING
start_all_solo_workers() {
    print_info "🎯 Starting ${#WORKER_NAMES[@]} Enhanced Solo Pool Workers..."
    echo
    
    local started_count=0
    local failed_count=0
    
    for worker_name in "${WORKER_NAMES[@]}"; do
        print_task "Processing $worker_name..."
        if start_solo_worker "$worker_name"; then
            ((started_count++))
        else
            ((failed_count++))
            print_error "$worker_name failed to start"
        fi
        echo
    done
    
    # Summary
    print_header "📊 Startup Summary"
    echo "=================="
    print_info "✅ Successfully started: $started_count workers"
    if [ "$failed_count" -gt 0 ]; then
        print_warning "❌ Failed to start: $failed_count workers"
        return 1
    fi
    
    return 0
}

#==============================================================================
# BEAT SCHEDULER MANAGEMENT
#==============================================================================

# Start beat scheduler
start_beat_scheduler() {
    print_worker "Starting Celery Beat Scheduler..."
    
    local log_file="$LOG_DIR/celery_beat.log"
    local pid_file="$PID_DIR/celery_beat.pid"
    
    # Cleanup existing beat
    if [ -f "$pid_file" ]; then
        local old_pid=$(cat "$pid_file" 2>/dev/null)
        if is_pid_running "$old_pid"; then
            print_warning "Stopping existing Beat scheduler (PID: $old_pid)"
            kill -TERM "$old_pid" 2>/dev/null || true
            sleep 3
            if is_pid_running "$old_pid"; then
                kill -KILL "$old_pid" 2>/dev/null || true
            fi
        fi
    fi
    
    rm -f "$pid_file" 2>/dev/null || true
    rm -f "$BEAT_SCHEDULE_FILE"* 2>/dev/null || true
    
    cd "$BACKEND_DIR"
    
    # Start beat scheduler
    nohup $PYTHON_CMD -m celery -A app.tasks.celery_app beat \
        --loglevel=info \
        --schedule="../$BEAT_SCHEDULE_FILE" \
        > "../$log_file" 2>&1 &
    
    local pid=$!
    cd - > /dev/null
    
    # Monitor startup
    print_info "⏳ Monitoring Beat startup (PID: $pid)..."
    local timeout=15
    local success=false
    
    while [ $timeout -gt 0 ]; do
        if is_pid_running "$pid"; then
            if [ -f "$log_file" ] && grep -q "beat: Starting" "$log_file" 2>/dev/null; then
                echo "$pid" > "$pid_file"
                print_success "Beat scheduler started successfully (PID: $pid)"
                success=true
                break
            elif [ -f "$log_file" ] && grep -q "ERROR\|CRITICAL" "$log_file" 2>/dev/null; then
                print_error "Beat scheduler failed with errors:"
                grep "ERROR\|CRITICAL" "$log_file" | tail -3 | sed 's/^/   /'
                break
            else
                echo -n "."
                sleep 1
                ((timeout--))
            fi
        else
            print_error "Beat scheduler process died unexpectedly"
            break
        fi
    done
    
    if [ "$success" = false ]; then
        print_error "Beat scheduler startup failed or timed out"
        return 1
    fi
    
    return 0
}

#==============================================================================
# FLOWER MONITORING
#==============================================================================

# Start flower monitoring
start_flower_monitor() {
    print_worker "Starting Celery Flower Monitor..."
    
    local log_file="$LOG_DIR/celery_flower.log"
    local pid_file="$PID_DIR/celery_flower.pid"
    
    # Cleanup existing flower
    if [ -f "$pid_file" ]; then
        local old_pid=$(cat "$pid_file" 2>/dev/null)
        if is_pid_running "$old_pid"; then
            print_warning "Stopping existing Flower monitor (PID: $old_pid)"
            kill -TERM "$old_pid" 2>/dev/null || true
            sleep 3
            if is_pid_running "$old_pid"; then
                kill -KILL "$old_pid" 2>/dev/null || true
            fi
        fi
    fi
    
    rm -f "$pid_file" 2>/dev/null || true
    
    cd "$BACKEND_DIR"
    
    # Start flower
    nohup $PYTHON_CMD -m celery -A app.tasks.celery_app flower \
        --port="$FLOWER_PORT" \
        --basic_auth=admin:cryptopredict123 \
        > "../$log_file" 2>&1 &
    
    local pid=$!
    cd - > /dev/null
    
    # Monitor startup
    print_info "⏳ Monitoring Flower startup (PID: $pid)..."
    local timeout=15
    local success=false
    
    while [ $timeout -gt 0 ]; do
        if is_pid_running "$pid"; then
            if check_port_usage "$FLOWER_PORT" || ([ -f "$log_file" ] && grep -q "Visit me at" "$log_file" 2>/dev/null); then
                echo "$pid" > "$pid_file"
                print_success "Flower monitor started successfully (PID: $pid)"
                print_info "🌸 Access at: http://localhost:$FLOWER_PORT (admin:cryptopredict123)"
                success=true
                break
            elif [ -f "$log_file" ] && grep -q "ERROR\|CRITICAL" "$log_file" 2>/dev/null; then
                print_error "Flower monitor failed with errors:"
                grep "ERROR\|CRITICAL" "$log_file" | tail -3 | sed 's/^/   /'
                break
            else
                echo -n "."
                sleep 1
                ((timeout--))
            fi
        else
            print_error "Flower monitor process died unexpectedly"
            break
        fi
    done
    
    if [ "$success" = false ]; then
        print_error "Flower monitor startup failed or timed out"
        return 1
    fi
    
    return 0
}

#==============================================================================
# STATUS AND MONITORING - FIXED VERSION
#==============================================================================

# FIXED: Enhanced status display with better PID detection
show_status() {
    print_header "📊 Comprehensive System Status"
    echo "=============================="
    echo
    
    print_info "🖥️  SYSTEM OVERVIEW:"
    echo "   📅 Check Time: $(get_timestamp)"
    echo "   👤 User: $(get_current_user)"
    echo "   📦 Manager Version: $SCRIPT_VERSION"
    echo
    
    # Worker status table header
    print_info "🔧 SOLO POOL WORKERS:"
    printf "┌─────────────────────────┬──────────┬─────────┬──────────┬─────────────────────────────┐\n"
    printf "│ %-23s │ %-8s │ %-7s │ %-8s │ %-27s │\n" "Worker" "Status" "PID" "CPU%" "Queues"
    printf "├─────────────────────────┼──────────┼─────────┼──────────┼─────────────────────────────┤\n"
    
    local running_workers=0
    local total_workers=${#WORKER_NAMES[@]}
    
    for i in "${!WORKER_NAMES[@]}"; do
        local worker_name="${WORKER_NAMES[$i]}"
        local queues="${WORKER_QUEUES[$i]}"
        local pid=$(get_worker_pid "$worker_name")
        local status="Stopped"
        local cpu_usage="-"
        
        if [ -n "$pid" ]; then
            status="Running"
            ((running_workers++))
            
            # Get CPU usage if possible
            if command -v ps >/dev/null 2>&1; then
                cpu_usage=$(ps -p "$pid" -o %cpu --no-headers 2>/dev/null | xargs || echo "-")
            fi
        fi
        
        printf "│ %-23s │ %-8s │ %-7s │ %-8s │ %-27s │\n" "$worker_name" "$status" "${pid:-"-"}" "$cpu_usage" "${queues:0:27}"
    done
    
    printf "└─────────────────────────┴──────────┴─────────┴──────────┴─────────────────────────────┘\n"
    echo
    
    # FIXED: System services status with better detection
    print_info "🎛️  SYSTEM SERVICES:"
    
    # Beat scheduler - Try multiple detection methods
    local beat_pid=$(get_worker_pid "celery_beat" 2>/dev/null)
    if [ -z "$beat_pid" ]; then
        # Fallback: try to find beat process by pattern
        beat_pid=$(get_process_pid_by_pattern "celery.*beat" "celery_beat" 2>/dev/null)
    fi
    
    if [ -n "$beat_pid" ]; then
        echo "   🥁 Beat Scheduler: Running (PID: $beat_pid)"
    else
        echo "   🥁 Beat Scheduler: Stopped"
    fi
    
    # Flower monitor - Try multiple detection methods
    local flower_pid=$(get_worker_pid "celery_flower" 2>/dev/null)
    if [ -z "$flower_pid" ]; then
        # Fallback: try to find flower process by pattern
        flower_pid=$(get_process_pid_by_pattern "celery.*flower" "celery_flower" 2>/dev/null)
    fi
    
    if [ -n "$flower_pid" ]; then
        echo "   🌸 Flower Monitor: Running (PID: $flower_pid)"
    else
        echo "   🌸 Flower Monitor: Stopped"
    fi
    
    # Redis connection
    if check_port_usage 6379; then
        echo "   📡 Redis Connection: Connected"
    else
        echo "   📡 Redis Connection: Down"
    fi
    
    echo
    
    # Summary
    print_info "📈 SUMMARY:"
    echo "   🔧 Workers: $running_workers/$total_workers running"
    echo "   🎛️  Services: Beat $([ -n "$beat_pid" ] && echo "✅" || echo "❌"), Flower $([ -n "$flower_pid" ] && echo "✅" || echo "❌")"
    echo "   📡 Redis: $(check_port_usage 6379 && echo "✅" || echo "❌")"
    
    # Health check
    if [ "$running_workers" -eq "$total_workers" ] && [ -n "$beat_pid" ] && check_port_usage 6379; then
        echo "   🎉 System Status: HEALTHY"
    elif [ "$running_workers" -gt 0 ]; then
        echo "   ⚠️  System Status: PARTIAL"
    else
        echo "   🚨 System Status: DOWN"
    fi
}

# FIXED: Debug function to show all PID files and processes
debug_pid_detection() {
    print_header "🐛 PID Detection Debug"
    echo "======================"
    echo
    
    print_info "📁 PID Files in $PID_DIR:"
    if [ -d "$PID_DIR" ]; then
        ls -la "$PID_DIR"/ 2>/dev/null || echo "  No PID files found"
    else
        echo "  PID directory does not exist"
    fi
    echo
    
    print_info "🔍 Celery Processes:"
    ps aux 2>/dev/null | grep -E "celery|python.*app\.tasks" | grep -v grep | while read -r line; do
        echo "  $line"
    done
    echo
    
    print_info "🌐 Port Usage:"
    echo "  Redis (6379): $(check_port_usage 6379 && echo "✅ Active" || echo "❌ Inactive")"
    echo "  Flower ($FLOWER_PORT): $(check_port_usage "$FLOWER_PORT" && echo "✅ Active" || echo "❌ Inactive")"
    echo
    
    print_info "📋 Process Detection Test:"
    for service in "celery_beat" "celery_flower"; do
        local pid_method1=$(get_worker_pid "$service" 2>/dev/null)
        local pattern=""
        [ "$service" = "celery_beat" ] && pattern="celery.*beat"
        [ "$service" = "celery_flower" ] && pattern="celery.*flower"
        local pid_method2=$(get_process_pid_by_pattern "$pattern" "$service" 2>/dev/null)
        
        echo "  $service:"
        echo "    PID file method: ${pid_method1:-"Not found"}"
        echo "    Pattern method: ${pid_method2:-"Not found"}"
    done
}

#==============================================================================
# MAIN EXECUTION LOGIC
#==============================================================================

# Initialize environment first
initialize_environment() {
    # Create directory structure BEFORE any logging
    mkdir -p "$LOG_DIR" "$PID_DIR" 2>/dev/null || true
    
    # Initialize log file
    touch "$LOG_DIR/ultimate_manager.log" 2>/dev/null || true
    
    # Script header
    echo -e "${PURPLE}${BOLD}"
    echo "╔═══════════════════════════════════════════════════════════════════════════╗"
    echo "║                 🚀 Ultimate Celery Worker Manager v$SCRIPT_VERSION                ║"
    echo "║                        Solo Pool Security Edition                        ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
    
    # Now it's safe to call other functions that use logging
    create_directory_structure
    rotate_logs
}

# Main function with comprehensive command handling - IMPROVED
main() {
    local action="${1:-help}"
    local sub_action="$2"
    local target="$3"
    
    # Initialize environment first
    initialize_environment
    
    case "$action" in
        "start")
            print_header "🚀 Ultimate Worker System Startup"
            echo "================================="
            echo
            
            # Environment validation
            if ! validate_environment; then
                print_error "Environment validation failed. Please fix issues before starting."
                return 1
            fi
            
            # Cleanup before start
            comprehensive_cleanup
            smart_cleanup
            
            # Start workers
            if start_all_solo_workers; then
                echo
                print_header "🎛️  Starting System Services"
                echo "============================"
                
                # Start beat scheduler
                if start_beat_scheduler; then
                    print_success "Beat scheduler operational"
                else
                    print_warning "Beat scheduler failed - workers still operational"
                fi
                
                echo
                
                # Start flower monitor
                if start_flower_monitor; then
                    print_success "Flower monitor operational"
                else
                    print_warning "Flower monitor failed - system still operational"
                fi
                
                echo
                print_header "🎉 SYSTEM STARTUP COMPLETE!"
                echo "==========================="
                print_success "All workers are running in Solo Pool mode"
                print_info "Monitor at: http://localhost:$FLOWER_PORT"
                print_info "Use './scripts/run-workers.sh status' to check system health"
                return 0
            else
                print_error "Worker startup failed"
                return 1
            fi
            ;;
            
        "stop")
            print_header "🛑 Ultimate Worker System Shutdown"
            echo "=================================="
            echo
            comprehensive_cleanup
            smart_cleanup
            print_success "System shutdown complete"
            return 0
            ;;
            
        "restart")
            print_header "🔄 Ultimate Worker System Restart"
            echo "================================="
            echo
            "$0" stop
            sleep 3
            "$0" start
            return $?
            ;;
            
        "status")
            show_status
            return 0
            ;;
            
        "debug")
            debug_pid_detection
            return 0
            ;;
            
        "logs")
            local worker="${sub_action:-all}"
            print_header "📋 Worker Logs"
            echo "==============="
            
            if [ "$worker" = "all" ]; then
                for worker_name in "${WORKER_NAMES[@]}"; do
                    local log_file="$LOG_DIR/${worker_name}_solo.log"
                    if [ -f "$log_file" ]; then
                        echo
                        print_info "📄 $worker_name logs (last 10 lines):"
                        tail -10 "$log_file" | sed 's/^/   /'
                    fi
                done
                
                # Show Beat and Flower logs too
                for service in "celery_beat" "celery_flower"; do
                    local log_file="$LOG_DIR/${service}.log"
                    if [ -f "$log_file" ]; then
                        echo
                        print_info "📄 $service logs (last 10 lines):"
                        tail -10 "$log_file" | sed 's/^/   /'
                    fi
                done
            else
                local log_file="$LOG_DIR/${worker}_solo.log"
                # Check for service logs too
                if [ ! -f "$log_file" ]; then
                    log_file="$LOG_DIR/${worker}.log"
                fi
                
                if [ -f "$log_file" ]; then
                    print_info "📄 $worker logs:"
                    tail -20 "$log_file"
                else
                    print_error "Log file not found: $log_file"
                    return 1
                fi
            fi
            return 0
            ;;
            
        "cleanup")
            print_header "🧹 System Cleanup"
            echo "=================="
            comprehensive_cleanup
            smart_cleanup
            print_success "Cleanup complete"
            return 0
            ;;
            
        "health")
            print_header "🏥 System Health Check"
            echo "======================"
            validate_environment
            show_status
            return 0
            ;;
            
        "version"|"-v"|"--version")
            print_header "📦 Version Information"
            echo "======================"
            echo "Script: $SCRIPT_NAME"
            echo "Version: $SCRIPT_VERSION"
            echo "Created: $CREATED_DATE"
            echo "Platform: $(get_system_info)"
            return 0
            ;;
            
        "help"|"-h"|"--help"|*)
            print_header "📚 Ultimate Celery Worker Manager Help"
            echo "======================================"
            echo
            print_info "USAGE:"
            echo "   $0 <command> [options]"
            echo
            print_info "COMMANDS:"
            echo "   start          🚀 Start all workers and services"
            echo "   stop           🛑 Stop all workers and services"
            echo "   restart        🔄 Restart all workers and services"
            echo "   status         📊 Show comprehensive system status"
            echo "   debug          🐛 Show PID detection debug info"
            echo "   logs [worker]  📋 Show worker logs (all or specific worker)"
            echo "   cleanup        🧹 Clean up stale processes and files"
            echo "   health         🏥 Run comprehensive health checks"
            echo "   version        📦 Show version information"
            echo "   help           📚 Show this help message"
            echo
            print_info "EXAMPLES:"
            echo "   $0 start                    # Start all workers"
            echo "   $0 logs data_worker        # Show data_worker logs"
            echo "   $0 logs celery_beat        # Show beat scheduler logs"
            echo "   $0 debug                   # Debug PID detection issues"
            echo "   $0 status                  # Check system status"
            echo
            print_info "WORKERS:"
            for i in "${!WORKER_NAMES[@]}"; do
                echo "   ${WORKER_NAMES[$i]} → ${WORKER_QUEUES[$i]}"
            done
            echo
            print_info "MONITORING:"
            echo "   🌸 Flower: http://localhost:$FLOWER_PORT"
            echo "   🔐 Login: admin / cryptopredict123"
            return 0
            ;;
    esac
}

# Improved error handling and cleanup
cleanup_on_exit() {
    local exit_code=$?
    
    # Only show error message for non-zero, non-interrupt exit codes
    if [ $exit_code -ne 0 ] && [ $exit_code -ne 130 ]; then
        print_warning "Script completed with exit code: $exit_code"
    fi
    
    return $exit_code
}

# Set up trap for exit
trap cleanup_on_exit EXIT

# Execute main function
main "$@"