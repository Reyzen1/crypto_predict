#!/bin/bash
# File: scripts/run-workers.sh
# Enhanced Celery worker script with improved error handling

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Configuration
BACKEND_DIR="backend"
LOG_DIR="scripts/logs"
PID_DIR="$LOG_DIR/pids"
PYTHON_CMD="python"

# Helper functions
print_success() { echo -e "${GREEN}$1${NC}"; }
print_warning() { echo -e "${YELLOW}$1${NC}"; }
print_error() { echo -e "${RED}$1${NC}"; }
print_info() { echo -e "${CYAN}$1${NC}"; }
print_header() { echo -e "${PURPLE}$1${NC}"; }

show_help() {
    print_header "🔧 Enhanced Celery Worker Manager"
    print_header "================================="
# Quick celery app diagnostic
diagnose_celery_app() {
    print_header "🔍 Celery App File Diagnostics"
    print_header "==============================="
    echo ""
    
    local app_file="$BACKEND_DIR/app/tasks/celery_app.py"
    
    print_info "📁 Checking file: $app_file"
    
    if [ ! -f "$app_file" ]; then
        print_error "❌ File does not exist!"
        print_info "💡 Run: ./scripts/run-workers.sh fix"
        return 1
    fi
    
    print_success "✅ File exists"
    
    # Check file size
    local file_size=$(wc -c < "$app_file")
    print_info "📏 File size: $file_size bytes"
    
    if [ "$file_size" -lt 100 ]; then
        print_error "❌ File is too small (likely empty or incomplete)"
        print_info "💡 Run: ./scripts/run-workers.sh fix"
        return 1
    fi
    
    # Check for key components
    print_info "🔍 Checking file contents..."
    
    if grep -q "from celery import Celery" "$app_file"; then
        print_success "✅ Has Celery import"
    else
        print_error "❌ Missing Celery import"
    fi
    
    if grep -q "^app = Celery" "$app_file"; then
        print_success "✅ Has app = Celery definition"
    else
        print_error "❌ Missing 'app = Celery' definition"
        print_info "💡 This is likely the cause of your import error"
    fi
    
    if grep -q "broker_url" "$app_file"; then
        print_success "✅ Has broker configuration"
    else
        print_warning "⚠️  Missing broker configuration"
    fi
    
    # Test Python syntax
    print_info "🐍 Testing Python syntax..."
    cd "$BACKEND_DIR"
    if $PYTHON_CMD -m py_compile app/tasks/celery_app.py 2>/dev/null; then
        print_success "✅ Python syntax is valid"
    else
        print_error "❌ Python syntax errors detected"
        print_error "Syntax check output:"
        $PYTHON_CMD -m py_compile app/tasks/celery_app.py 2>&1 | sed 's/^/   /'
    fi
    cd ..
    
    echo ""
    print_info "📄 File contents (first 20 lines):"
    echo "----------------------------------------"
    head -20 "$app_file" | nl -ba
    echo "----------------------------------------"
    
    return 0
}
    print_info "Usage: ./scripts/run-workers.sh [action]"
    echo ""
    print_header "⚡ Actions:"
    print_info "  (none)    - Start workers (default)"
    print_info "  start     - Start workers"
    print_info "  stop      - Stop all workers"
    print_info "  restart   - Restart workers"
    print_info "  status    - Show worker status"
    print_info "  monitor   - Real-time monitoring"
    print_info "  logs      - Show recent logs"
    print_info "  debug     - Debug issues"
    print_info "  health    - Run system health check"
    print_info "  test      - Test environment and configuration"
    print_info "  fix       - Auto-fix common issues"
    print_info "  diagnose  - Diagnose celery_app.py file issues"
    echo ""
    print_header "🎯 Examples:"
    print_info "  ./scripts/run-workers.sh           # Start workers"
    print_info "  ./scripts/run-workers.sh test      # Test environment"
    print_info "  ./scripts/run-workers.sh fix       # Auto-fix issues"
    print_info "  ./scripts/run-workers.sh diagnose  # Check celery_app.py file"
    print_info "  ./scripts/run-workers.sh debug     # Debug problems"
    exit 0
}

# Create directory structure
create_directory_structure() {
    print_info "📁 Setting up directory structure..."
    
    mkdir -p "$LOG_DIR"
    mkdir -p "$PID_DIR"
    
    local log_files=(
        "$LOG_DIR/celery_beat.log"
        "$LOG_DIR/celery_data_worker.log"
        "$LOG_DIR/celery_ml_worker.log"
        "$LOG_DIR/celery_flower.log"
    )
    
    for log_file in "${log_files[@]}"; do
        if [ ! -f "$log_file" ]; then
            touch "$log_file"
        fi
    done
    
    print_success "✅ Directory structure created"
}

# Check environment and prerequisites
check_environment() {
    print_info "🔍 Checking environment..."
    local issues=0
    
    # Check backend directory
    if [ ! -d "$BACKEND_DIR" ]; then
        print_error "❌ Backend directory not found."
        print_error "   Please run this script from the project root directory."
        exit 1
    fi
    print_success "✅ Backend directory found: $BACKEND_DIR"
    
    # Check Python
    if ! command -v $PYTHON_CMD >/dev/null 2>&1; then
        print_error "❌ Python not found"
        if command -v python3 >/dev/null 2>&1; then
            PYTHON_CMD="python3"
            print_warning "⚠️  Using python3 instead"
        else
            print_error "Python is not installed or not in PATH"
            issues=$((issues + 1))
        fi
    else
        print_success "✅ Python found: $($PYTHON_CMD --version)"
    fi
    
    # Check Redis
    if command -v redis-cli >/dev/null 2>&1; then
        if redis-cli ping >/dev/null 2>&1; then
            print_success "✅ Redis is accessible"
        else
            print_error "❌ Redis is not accessible"
            print_error "   Please start Redis server: redis-server"
            issues=$((issues + 1))
        fi
    else
        print_warning "⚠️  redis-cli not found"
        issues=$((issues + 1))
    fi
    
    create_directory_structure
    
    if [ $issues -gt 0 ]; then
        print_error "❌ $issues environment issues detected"
        print_info "To fix issues: ./scripts/run-workers.sh fix"
        return 1
    fi
    
    return 0
}

# Comprehensive environment test
test_environment() {
    print_header "🧪 Comprehensive Environment & Configuration Test"
    print_header "================================================="
    echo ""
    
    local issues=0
    
    # 1. Basic tests
    print_info "1. 🏗️ Basic Environment Tests..."
    check_environment || issues=$((issues + 1))
    echo ""
    
    # 2. Python imports test
    print_info "2. 🐍 Python Import Tests..."
    cd "$BACKEND_DIR"
    
    # Test basic import
    if $PYTHON_CMD -c "import sys; print('Python Path:', sys.path[:3])" 2>/dev/null; then
        print_success "   ✅ Python path is accessible"
    else
        print_error "   ❌ Python path issue"
        issues=$((issues + 1))
    fi
    
    # Test celery import
    if $PYTHON_CMD -c "import celery; print('Celery version:', celery.__version__)" 2>/dev/null; then
        print_success "   ✅ Celery is installed"
    else
        print_error "   ❌ Celery is not installed"
        print_info "   Install with: pip install celery[redis]"
        issues=$((issues + 1))
    fi
    
    # Test app import
    local import_output=$($PYTHON_CMD -c "from app.tasks.celery_app import app; print('SUCCESS: Celery app loaded')" 2>&1)
    local import_status=$?
    
    if [ $import_status -eq 0 ] && echo "$import_output" | grep -q "SUCCESS: Celery app loaded"; then
        print_success "   ✅ Celery app can be imported"
        
        # Check if there are ML model loading messages (which are normal)
        if echo "$import_output" | grep -q "Loading existing models\|models loaded"; then
            local model_count=$(echo "$import_output" | grep -o "[0-9]\+ models loaded" | head -1 | grep -o "[0-9]\+")
            if [ -n "$model_count" ]; then
                print_info "   🤖 ML models loaded: $model_count models"
            fi
        fi
    else
        print_error "   ❌ Cannot import Celery app"
        print_error "   Error:"
        echo "$import_output" | grep -E "(Error|Exception|Traceback|ImportError|ModuleNotFoundError)" | head -5 | sed 's/^/      /'
        
        # If no actual errors found, show full output
        if ! echo "$import_output" | grep -qE "(Error|Exception|Traceback|ImportError|ModuleNotFoundError)"; then
            echo "$import_output" | head -5 | sed 's/^/      /'
        fi
        issues=$((issues + 1))
    fi
    
    cd ..
    echo ""
    
    # 3. Required files check
    print_info "3. 📂 Required Files Check..."
    local required_files=(
        "$BACKEND_DIR/app/__init__.py"
        "$BACKEND_DIR/app/tasks/__init__.py"
        "$BACKEND_DIR/app/tasks/celery_app.py"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "   ✅ $file"
        else
            print_error "   ❌ Missing file: $file"
            issues=$((issues + 1))
        fi
    done
    echo ""
    
    # 4. Redis connection test
    print_info "4. 🔗 Redis Connection Test..."
    if command -v redis-cli >/dev/null 2>&1; then
        if redis-cli ping >/dev/null 2>&1; then
            print_success "   ✅ Redis is responding"
            
            # Test queue operations
            local test_key="test_$(date +%s)"
            if redis-cli set "$test_key" "test_value" >/dev/null 2>&1; then
                print_success "   ✅ Redis is writable"
                redis-cli del "$test_key" >/dev/null 2>&1
            else
                print_error "   ❌ Cannot write to Redis"
                issues=$((issues + 1))
            fi
            
            # Show Redis info
            local redis_memory=$(redis-cli info memory 2>/dev/null | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r' || echo "Unknown")
            print_info "   💾 Redis memory usage: $redis_memory"
        else
            print_error "   ❌ Redis is not responding"
            issues=$((issues + 1))
        fi
    else
        print_error "   ❌ redis-cli not found"
        issues=$((issues + 1))
    fi
    echo ""
    
    # 5. Celery commands test
    print_info "5. 🎯 Celery Commands Test..."
    cd "$BACKEND_DIR"
    
    # Test celery inspect
    if timeout 10s $PYTHON_CMD -m celery -A app.tasks.celery_app inspect stats >/dev/null 2>&1; then
        print_success "   ✅ Celery inspect command works"
    else
        print_warning "   ⚠️  Celery inspect command timed out (normal if no workers)"
    fi
    
    # Test celery worker with dry-run
    if timeout 5s $PYTHON_CMD -m celery -A app.tasks.celery_app worker --help >/dev/null 2>&1; then
        print_success "   ✅ Celery worker command is available"
    else
        print_error "   ❌ Celery worker command doesn't work"
        issues=$((issues + 1))
    fi
    
    cd ..
    echo ""
    
    # Test summary
    print_header "🎯 Test Results"
    if [ $issues -eq 0 ]; then
        print_success "🟢 Excellent! All tests passed"
        print_info "Your environment is ready to run Celery workers"
        print_info "You can start workers with: ./scripts/run-workers.sh start"
    elif [ $issues -le 2 ]; then
        print_warning "🟡 Good with warnings ($issues issues)"
        print_info "Minor issues exist but it should work"
    else
        print_error "🔴 Test failed ($issues issues)"
        print_error "Please fix the issues before starting workers"
        print_info "Try auto-fix: ./scripts/run-workers.sh fix"
    fi
    
    echo ""
    print_info "💡 Note: These messages during import are NORMAL:"
    print_info "  • 'Loading existing models on startup' - ML system initializing"
    print_info "  • 'Loaded X models from registry' - ML models being loaded"
    print_info "  • 'Startup complete: X models loaded' - ML initialization finished"
    print_info "  These indicate your ML model system is working correctly."
}

# Auto-fix common issues
auto_fix_issues() {
    print_header "🔧 Auto-fixing Common Issues"
    print_header "============================"
    echo ""
    
    local fixes=0
    
    # 1. Create missing files
    print_info "1. 📂 Checking and creating required files..."
    
    # Create __init__.py files
    local init_files=(
        "$BACKEND_DIR/app/__init__.py"
        "$BACKEND_DIR/app/tasks/__init__.py"
    )
    
    for init_file in "${init_files[@]}"; do
        if [ ! -f "$init_file" ]; then
            mkdir -p "$(dirname "$init_file")"
            touch "$init_file"
            print_success "   ✅ Created: $init_file"
            fixes=$((fixes + 1))
        fi
    done
    
    # Check celery_app.py
    if [ ! -f "$BACKEND_DIR/app/tasks/celery_app.py" ]; then
        print_warning "   ⚠️  celery_app.py not found"
        print_info "   Creating working Celery app template..."
        
        mkdir -p "$BACKEND_DIR/app/tasks"
        cat > "$BACKEND_DIR/app/tasks/celery_app.py" << 'EOF'
"""
Celery application instance for crypto_predict
"""
from __future__ import absolute_import, unicode_literals
from celery import Celery
import os

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

# Create Celery app instance
app = Celery('crypto_predict')

# Load configuration from Django settings
# app.config_from_object('django.conf:settings', namespace='CELERY')

# Manual configuration for standalone use
app.conf.update(
    # Broker and Result Backend
    broker_url='redis://127.0.0.1:6379/0',
    result_backend='redis://127.0.0.1:6379/0',
    
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Task routing
    task_routes={
        'app.tasks.*': {'queue': 'default'},
        'app.ml.*': {'queue': 'ml_tasks'},
        'app.data.*': {'queue': 'price_data'},
    },
    
    # Beat schedule (if using beat scheduler)
    beat_schedule={
        'test-task': {
            'task': 'app.tasks.celery_app.debug_task',
            'schedule': 300.0,  # Every 5 minutes
        },
    },
)

# Auto-discover tasks from all installed Django apps
try:
    app.autodiscover_tasks()
except Exception:
    # Fallback if Django isn't configured
    pass

# Task definitions
@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery functionality"""
    print(f'Request: {self.request!r}')
    return 'Debug task completed successfully'

@app.task(name='price_data_collection')
def price_data_task(symbol=None):
    """Price data collection task"""
    print(f'Collecting price data for symbol: {symbol}')
    return f'Price data collected for {symbol}'

@app.task(name='ml_prediction')  
def ml_prediction_task(data=None):
    """ML prediction task"""
    print(f'Running ML prediction on data: {data}')
    return 'ML prediction completed'

@app.task(name='health_check')
def health_check_task():
    """Health check task"""
    return {
        'status': 'healthy',
        'celery_version': app.version,
        'timestamp': app.now().isoformat()
    }

# Make sure app is available for import
__all__ = ['app']

if __name__ == '__main__':
    app.start()
EOF
        print_success "   ✅ Created working celery_app.py with proper app definition"
        fixes=$((fixes + 1))
    else
        # Check if existing file has proper app definition
        if ! grep -q "^app = " "$BACKEND_DIR/app/tasks/celery_app.py"; then
            print_warning "   ⚠️  Existing celery_app.py missing 'app = ...' definition"
            
            # Check if it has create_celery_app function (factory pattern)
            if grep -q "def create_celery_app" "$BACKEND_DIR/app/tasks/celery_app.py"; then
                print_info "   📝 Found create_celery_app function - adding app instantiation"
                
                # Backup existing file
                cp "$BACKEND_DIR/app/tasks/celery_app.py" "$BACKEND_DIR/app/tasks/celery_app.py.backup.$(date +%s)"
                
                # Add the missing app instantiation at the end
                cat >> "$BACKEND_DIR/app/tasks/celery_app.py" << 'EOF'

# Create the app instance at module level so it can be imported
app = create_celery_app()

# Make sure app is available for import
__all__ = ['app']
EOF
                print_success "   ✅ Added app instantiation to existing file"
                fixes=$((fixes + 1))
            else
                print_info "   Backing up existing file and creating new one..."
                
                # Backup existing file
                cp "$BACKEND_DIR/app/tasks/celery_app.py" "$BACKEND_DIR/app/tasks/celery_app.py.backup.$(date +%s)"
                
                # Create new working file
                cat > "$BACKEND_DIR/app/tasks/celery_app.py" << 'EOF'
"""
Celery application instance for crypto_predict
"""
from __future__ import absolute_import, unicode_literals
from celery import Celery
import os

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

# Create Celery app instance
app = Celery('crypto_predict')

# Manual configuration for standalone use
app.conf.update(
    # Broker and Result Backend
    broker_url='redis://127.0.0.1:6379/0',
    result_backend='redis://127.0.0.1:6379/0',
    
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)

# Auto-discover tasks
try:
    app.autodiscover_tasks()
except Exception:
    pass

# Basic tasks
@app.task(bind=True)
def debug_task(self):
    """Debug task for testing"""
    print(f'Request: {self.request!r}')
    return 'Debug task completed'

@app.task
def health_check_task():
    """Health check task"""
    return {'status': 'healthy'}

# Make sure app is available for import
__all__ = ['app']

if __name__ == '__main__':
    app.start()
EOF
                print_success "   ✅ Fixed celery_app.py with proper app definition"
                fixes=$((fixes + 1))
            fi
        fi
    fi
    echo ""
    
    # 2. Clean locked files
    print_info "2. 🧹 Cleaning locked files..."
    
    # Clean old PID files
    if [ -d "$PID_DIR" ]; then
        local old_pids=$(find "$PID_DIR" -name "*.pid" -type f 2>/dev/null | wc -l)
        if [ "$old_pids" -gt 0 ]; then
            rm -f "$PID_DIR"/*.pid
            # Also clean any old celerybeat.pid files for consistency  
            rm -f "$PID_DIR"/celerybeat.pid 2>/dev/null || true
            print_success "   ✅ Cleaned $old_pids old PID files"
            fixes=$((fixes + 1))
        fi
    fi
    
    # Clean corrupted schedule files
    local schedule_files=(
        "$LOG_DIR/celerybeat-schedule"
        "$LOG_DIR/celerybeat-schedule.bak"
        "$LOG_DIR/celerybeat-schedule.dir"
        "$LOG_DIR/celerybeat-schedule.db"
    )
    
    local cleaned=0
    for schedule_file in "${schedule_files[@]}"; do
        if [ -f "$schedule_file" ]; then
            rm -f "$schedule_file"
            cleaned=$((cleaned + 1))
        fi
    done
    
    if [ $cleaned -gt 0 ]; then
        print_success "   ✅ Cleaned $cleaned corrupted schedule files"
        fixes=$((fixes + 1))
    fi
    echo ""
    
    # 3. Check and install dependencies
    print_info "3. 📦 Checking dependencies..."
    
    cd "$BACKEND_DIR"
    
    # Check requirements.txt
    if [ -f "requirements.txt" ]; then
        print_info "   📋 Found requirements.txt"
        if command -v pip >/dev/null 2>&1; then
            print_info "   📦 Checking installed packages..."
            if pip check >/dev/null 2>&1; then
                print_success "   ✅ All packages are installed"
            else
                print_warning "   ⚠️  Some packages have issues"
                print_info "   💡 Run: pip install -r requirements.txt"
            fi
        fi
    else
        print_warning "   ⚠️  requirements.txt not found"
        print_info "   Installing essential packages..."
        if command -v pip >/dev/null 2>&1; then
            pip install celery[redis] flower >/dev/null 2>&1 && fixes=$((fixes + 1))
        fi
    fi
    
    cd ..
    echo ""
    
    # 4. Fix permissions
    print_info "4. 🔐 Checking permissions..."
    
    if [ ! -w "$LOG_DIR" ]; then
        chmod 755 "$LOG_DIR" 2>/dev/null && fixes=$((fixes + 1))
        print_success "   ✅ Fixed log directory permissions"
    fi
    
    if [ ! -w "$PID_DIR" ]; then
        chmod 755 "$PID_DIR" 2>/dev/null && fixes=$((fixes + 1))
        print_success "   ✅ Fixed PID directory permissions"
    fi
    echo ""
    
    # Results
    print_header "🎯 Fix Results"
    if [ $fixes -gt 0 ]; then
        print_success "✅ $fixes issues fixed"
        print_info "Now you can test: ./scripts/run-workers.sh test"
    else
        print_info "ℹ️  No issues found to fix"
    fi
}

# Get process statistics with better error handling
get_process_stats() {
    local pid="$1"
    if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
        if command -v ps >/dev/null 2>&1; then
            # Try different ps format options
            if ps -p "$pid" -o %cpu,%mem,etime --no-headers 2>/dev/null; then
                return 0
            elif ps -p "$pid" -o pcpu,pmem,etime --no-headers 2>/dev/null; then
                return 0
            elif ps -p "$pid" -o %cpu,%mem --no-headers 2>/dev/null; then
                echo " -"
                return 0
            fi
        fi
    fi
    echo "0.0 0.0 -"
}

# Optimized worker configuration
get_optimized_worker_config() {
    POOL_TYPE="threads"
    CONCURRENCY=2  # Reduced for better stability
    MAX_TASKS_PER_CHILD=500  # Reduced to prevent memory leaks
    PREFETCH_MULTIPLIER=1  # Reduced to prevent queue flooding
    OPTIMIZATION=""  # Remove extra optimizations
    
    print_success "🔄 Optimized settings: Threads pool with high stability"
}

# Enhanced force kill
force_kill_all_celery() {
    local silent="$1"
    local killed_count=0
    
    if [ "$silent" != "silent" ]; then
        print_warning "🔥 Cleaning up existing Celery processes..."
    fi
    
    # Kill specific processes
    local patterns=(
        "celery.*worker"
        "celery.*beat"
        "celery.*flower"
        "python.*celery"
    )
    
    for pattern in "${patterns[@]}"; do
        local pids=$(pgrep -f "$pattern" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            local count=$(echo "$pids" | grep -c . || echo "0")
            killed_count=$((killed_count + count))
            if [ "$silent" != "silent" ]; then
                print_warning "   🗡️  Killing $count processes: $pattern"
            fi
            echo "$pids" | xargs kill -TERM 2>/dev/null || true
            sleep 2
            echo "$pids" | xargs kill -KILL 2>/dev/null || true
        fi
    done
    
    # Clean flower ports
    for port in $(seq 5555 5565); do
        if command -v lsof >/dev/null 2>&1; then
            local port_pids=$(lsof -ti:$port 2>/dev/null || true)
            if [ -n "$port_pids" ]; then
                if [ "$silent" != "silent" ]; then
                    print_warning "   🌐 Killing processes on port $port..."
                fi
                echo "$port_pids" | xargs kill -9 2>/dev/null || true
                killed_count=$((killed_count + 1))
            fi
        fi
    done
    
    # Clean PID files
    if [ -d "$PID_DIR" ]; then
        rm -f "$PID_DIR"/*.pid 2>/dev/null || true
        # Also clean any old celerybeat.pid files for consistency
        rm -f "$PID_DIR"/celerybeat.pid 2>/dev/null || true
    fi
    
    # Clean schedule files
    local schedule_files=(
        "$LOG_DIR/celerybeat-schedule"
        "$LOG_DIR/celerybeat-schedule.bak"
        "$LOG_DIR/celerybeat-schedule.dir"
        "$LOG_DIR/celerybeat-schedule.db"
    )
    
    for schedule_file in "${schedule_files[@]}"; do
        if [ -f "$schedule_file" ]; then
            rm -f "$schedule_file"
        fi
    done
    
    if [ "$silent" != "silent" ]; then
        if [ "$killed_count" -gt 0 ]; then
            print_success "✅ Killed $killed_count Celery processes"
        else
            print_success "✅ No existing Celery processes found"
        fi
    fi
    
    sleep 3
}

# Start worker with improved checking
start_worker_improved() {
    local name="$1"
    local queue="$2"
    
    get_optimized_worker_config
    
    local log_file="$(pwd)/$LOG_DIR/celery_${name}.log"
    local pid_file="$(pwd)/$PID_DIR/celery_${name}.pid"
    
    print_info "🚀 Starting $name worker..."
    print_info "   📋 Queue: $queue"
    print_info "   🧵 Pool: $POOL_TYPE (concurrency: $CONCURRENCY)"
    print_info "   📝 Log: $log_file"
    
    # Clear old log
    echo "=== New start $(date) ===" > "$log_file"
    
    local cmd="$PYTHON_CMD -m celery -A app.tasks.celery_app worker"
    cmd="$cmd --loglevel=info --queues=$queue --pool=$POOL_TYPE --concurrency=$CONCURRENCY"
    cmd="$cmd --hostname=${name}@%h --max-tasks-per-child=$MAX_TASKS_PER_CHILD"
    cmd="$cmd --prefetch-multiplier=$PREFETCH_MULTIPLIER"
    
    cd "$BACKEND_DIR"
    
    # Start worker with timeout
    nohup timeout 300 bash -c "$cmd" >> "../$LOG_DIR/celery_${name}.log" 2>&1 &
    local pid=$!
    echo $pid > "../$PID_DIR/celery_${name}.pid"
    
    cd ..
    
    print_info "   ⏳ Verifying startup..."
    local startup_success=false
    
    # Check startup for 15 seconds
    for i in {1..15}; do
        if ps -p $pid > /dev/null 2>&1; then
            # Check if worker is ready
            sleep 1
            if grep -q "ready" "$log_file" 2>/dev/null; then
                startup_success=true
                break
            fi
        else
            break
        fi
        sleep 1
    done
    
    if [ "$startup_success" = true ] && ps -p $pid > /dev/null 2>&1; then
        print_success "✅ $name worker started successfully! (PID: $pid)"
        
        # Health test
        sleep 2
        cd "$BACKEND_DIR"
        if timeout 10s $PYTHON_CMD -m celery -A app.tasks.celery_app inspect ping -d "${name}@$(hostname)" >/dev/null 2>&1; then
            print_success "   🏥 Health test: passed"
        else
            print_warning "   ⚠️  Health test: failed (worker might be initializing)"
        fi
        cd ..
    else
        print_error "❌ $name worker failed to start"
        if [ -f "$log_file" ]; then
            print_error "🔍 Recent errors from log:"
            tail -10 "$log_file" | sed 's/^/     /' | while IFS= read -r line; do
                print_error "     $line"
            done
        fi
        rm -f "$pid_file"
        return 1
    fi
    echo ""
}

# Find available port
find_available_port() {
    local start_port=5555
    local max_port=5570
    
    for port in $(seq $start_port $max_port); do
        if command -v nc >/dev/null 2>&1; then
            if ! nc -z localhost $port 2>/dev/null; then
                echo $port
                return 0
            fi
        elif command -v lsof >/dev/null 2>&1; then
            if ! lsof -i:$port >/dev/null 2>&1; then
                echo $port
                return 0
            fi
        else
            if ! netstat -an 2>/dev/null | grep ":$port " >/dev/null 2>&1; then
                echo $port
                return 0
            fi
        fi
    done
    
    echo 5555
}

# Start beat or flower service
start_service_improved() {
    local name="$1"
    local command="$2"
    local port="$3"
    
    local log_file="$(pwd)/$LOG_DIR/celery_${name}.log"
    local pid_file="$(pwd)/$PID_DIR/celery_${name}.pid"
    
    print_info "🚀 Starting $name..."
    print_info "   📝 Log: $log_file"
    
    echo "=== New start $(date) ===" > "$log_file"
    
    cd "$BACKEND_DIR"
    nohup bash -c "$command" >> "../$LOG_DIR/celery_${name}.log" 2>&1 &
    local pid=$!
    echo $pid > "../$PID_DIR/celery_${name}.pid"
    cd ..
    
    sleep 5
    if ps -p $pid > /dev/null 2>&1; then
        if [ -n "$port" ]; then
            print_success "✅ $name started successfully (PID: $pid, Port: $port)"
        else
            print_success "✅ $name started successfully (PID: $pid)"
        fi
    else
        print_error "❌ $name failed to start"
        if [ -f "$log_file" ]; then
            print_error "🔍 Recent error:"
            tail -5 "$log_file" | sed 's/^/     /' | while IFS= read -r line; do
                print_error "     $line"
            done
        fi
        rm -f "$pid_file"
        return 1
    fi
    echo ""
}

# Start all workers
start_all_workers() {
    print_header "🚀 Starting Celery Workers (Enhanced Version)"
    print_header "=============================================="
    echo ""
    
    # Check environment
    if ! check_environment; then
        print_error "❌ Environment is not ready. Please fix issues first"
        print_info "💡 To test: ./scripts/run-workers.sh test"
        print_info "💡 To fix: ./scripts/run-workers.sh fix"
        exit 1
    fi
    
    force_kill_all_celery
    echo ""
    
    print_info "🎯 Starting optimized workers..."
    echo ""
    
    local success_count=0
    local total_workers=4  # data_worker, ml_worker, beat, flower
    
    # Start data worker
    if start_worker_improved "data_worker" "price_data,default"; then
        success_count=$((success_count + 1))
    fi
    
    # Start ML worker
    if start_worker_improved "ml_worker" "ml_tasks"; then
        success_count=$((success_count + 1))
    fi
    
    # Start beat scheduler
    print_info "🥁 Starting Celery Beat scheduler..."
    if start_service_improved "beat" "$PYTHON_CMD -m celery -A app.tasks.celery_app beat --loglevel=info --schedule=../scripts/logs/celerybeat-schedule --pidfile=../scripts/logs/pids/beat.pid"; then
        success_count=$((success_count + 1))
    fi
    
    # Start flower monitoring
    print_info "🌸 Starting Flower monitoring dashboard..."
    local flower_port=$(find_available_port)
    if [ "$flower_port" != "5555" ]; then
        print_warning "   ⚠️  Port 5555 is busy, using port $flower_port instead"
    fi
    if start_service_improved "flower" "$PYTHON_CMD -m celery -A app.tasks.celery_app flower --port=$flower_port --basic_auth=admin:cryptopredict123" "$flower_port"; then
        success_count=$((success_count + 1))
    fi
    
    # Show final status
    sleep 3
    show_status
    
    print_header ""
    if [ "$success_count" -eq "$total_workers" ]; then
        print_header "🎉 All Celery Workers Started Successfully!"
        print_header "==========================================="
        print_success "🌐 Flower Dashboard: http://localhost:$flower_port"
        print_success "🔐 Credentials: admin / cryptopredict123"
    else
        print_warning "⚠️  $success_count of $total_workers workers started"
        print_info "For debugging: ./scripts/run-workers.sh debug"
    fi
    
    echo ""
    print_info "💡 Worker Configuration:"
    print_info "   🧵 Pool Type: threads"
    print_info "   ⚡ Concurrency: 2 threads per worker"
    print_info "   🔄 Max Tasks/Child: 500 (prevents memory leaks)"
    print_info "   📦 Prefetch: 1 (optimized for I/O)"
    echo ""
    
    if [ "$success_count" -eq "$total_workers" ]; then
        print_success "✅ All systems operational!"
    else
        print_warning "⚠️  Some workers have issues - check logs"
    fi
}

# Stop workers
stop_workers() {
    local silent="$1"
    
    if [ "$silent" != "silent" ]; then
        print_header "🛑 Stopping All Celery Workers"
        print_header "=============================="
    fi
    
    local stopped=0
    local failed=0
    
    if [ -d "$PID_DIR" ]; then
        for pid_file in "$PID_DIR"/*.pid; do
            [ -f "$pid_file" ] || continue
            
            local pid=$(cat "$pid_file" 2>/dev/null || echo "")
            local name=$(basename "$pid_file" .pid)
            name=${name#celery_}
            
            if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
                if [ "$silent" != "silent" ]; then
                    print_warning "🛑 Stopping $name (PID: $pid)..."
                fi
                
                # Graceful shutdown
                kill -TERM "$pid" 2>/dev/null || true
                
                local shutdown_success=false
                for i in {1..10}; do
                    if ! ps -p "$pid" > /dev/null 2>&1; then
                        shutdown_success=true
                        break
                    fi
                    sleep 1
                done
                
                # Force kill if needed
                if [ "$shutdown_success" = false ] && ps -p "$pid" > /dev/null 2>&1; then
                    if [ "$silent" != "silent" ]; then
                        print_warning "   🔥 Force killing $name..."
                    fi
                    kill -KILL "$pid" 2>/dev/null || true
                    sleep 1
                fi
                
                if [ "$shutdown_success" = true ] || ! ps -p "$pid" > /dev/null 2>&1; then
                    stopped=$((stopped + 1))
                    if [ "$silent" != "silent" ]; then
                        print_success "   ✅ $name stopped successfully"
                    fi
                else
                    failed=$((failed + 1))
                    if [ "$silent" != "silent" ]; then
                        print_error "   ❌ Failed to stop $name"
                    fi
                fi
            else
                if [ "$silent" != "silent" ]; then
                    print_warning "   ⚠️  $name was not running"
                fi
            fi
            rm -f "$pid_file"
        done
    fi
    
    # Final cleanup
    force_kill_all_celery silent
    
    if [ "$silent" != "silent" ]; then
        echo ""
        print_success "✅ Successfully stopped $stopped worker(s)"
        if [ "$failed" -gt 0 ]; then
            print_warning "⚠️  $failed worker(s) required force termination"
        fi
    fi
}

# Show status
show_status() {
    print_header "📊 Celery Workers Status"
    print_header "========================"
    
    local running=0
    local total=0
    local health_issues=0
    
    if [ -d "$PID_DIR" ]; then
        for pid_file in "$PID_DIR"/*.pid; do
            [ -f "$pid_file" ] || continue
            
            local pid=$(cat "$pid_file" 2>/dev/null || echo "")
            local name=$(basename "$pid_file" .pid)
            name=${name#celery_}
            total=$((total + 1))
            
            if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
                local stats=$(get_process_stats "$pid")
                local cpu=$(echo "$stats" | awk '{print $1}' | sed 's/%//')
                local mem=$(echo "$stats" | awk '{print $2}' | sed 's/%//')
                local uptime=$(echo "$stats" | awk '{print $3}' || echo "-")
                
                # Show pool info for workers
                local pool_info=""
                if [[ "$name" == "data_worker" || "$name" == "ml_worker" ]]; then
                    pool_info=" [threads/2]"
                fi
                
                print_success "  🟢 $name: Running (PID: $pid)$pool_info"
                
                # Resource usage with alerts
                if [ "$cpu" != "-" ] && [ "$mem" != "-" ]; then
                    if (( $(echo "$cpu > 80" | bc -l 2>/dev/null || echo "0") )); then
                        print_warning "     🔥 HIGH CPU: ${cpu}%, Memory: ${mem}%"
                        health_issues=$((health_issues + 1))
                    elif (( $(echo "$mem > 70" | bc -l 2>/dev/null || echo "0") )); then
                        print_warning "     ⚠️  CPU: ${cpu}%, HIGH MEMORY: ${mem}%"
                        health_issues=$((health_issues + 1))
                    else
                        print_info "     💻 CPU: ${cpu}%, Memory: ${mem}%"
                    fi
                else
                    print_info "     💻 CPU: -, Memory: - (stats unavailable)"
                fi
                
                if [ "$uptime" != "-" ]; then
                    print_info "     ⏰ Uptime: ${uptime}"
                fi
                
                running=$((running + 1))
            else
                print_warning "  🔴 $name: Not running"
                rm -f "$pid_file"
            fi
            echo ""
        done
    fi
    
    # Summary with health status
    print_header "📈 Summary"
    if [ "$running" -eq "$total" ] && [ "$total" -gt 0 ]; then
        if [ "$health_issues" -eq 0 ]; then
            print_success "🎯 All workers healthy ($running/$total running)"
        else
            print_warning "⚠️  $running/$total workers running, $health_issues health issue(s) detected"
        fi
        print_success "🔄 Optimization active - event loop compatible"
    elif [ "$running" -gt 0 ]; then
        print_warning "⚠️  Some workers down ($running/$total running)"
        print_info "   Run './scripts/run-workers.sh restart' to fix"
    else
        print_warning "❌ No workers running"
        print_info "   Run './scripts/run-workers.sh start' to start workers"
    fi
    
    # Additional info
    if [ "$running" -gt 0 ]; then
        local flower_port=$(find_available_port)
        # Try to find actual flower port
        for port in $(seq 5555 5570); do
            if command -v nc >/dev/null 2>&1; then
                if nc -z localhost $port 2>/dev/null; then
                    flower_port=$port
                    break
                fi
            fi
        done
        
        print_info ""
        print_info "🌐 Flower Dashboard: http://localhost:$flower_port"
        print_info "📝 Log files: $LOG_DIR/"
        print_info "🆔 PID files: $PID_DIR/"
    fi
}

# Show logs
show_logs() {
    print_header "📝 Recent Worker Logs"
    print_header "====================="
    
    if [ -d "$LOG_DIR" ]; then
        for log_file in "$LOG_DIR"/celery_*.log; do
            if [ -f "$log_file" ]; then
                local name=$(basename "$log_file" .log)
                name=${name#celery_}
                local file_size=$(ls -lh "$log_file" 2>/dev/null | awk '{print $5}' || echo "0B")
                
                print_header ""
                print_header "--- $name (last 20 lines, size: $file_size) ---"
                
                if [ -s "$log_file" ]; then
                    tail -20 "$log_file" | while IFS= read -r line; do
                        # Enhanced color coding
                        if [[ "$line" == *"ERROR"* || "$line" == *"CRITICAL"* || "$line" == *"Traceback"* ]]; then
                            echo -e "${RED}$line${NC}"
                        elif [[ "$line" == *"WARNING"* ]]; then
                            echo -e "${YELLOW}$line${NC}"
                        elif [[ "$line" == *"INFO"* ]]; then
                            echo -e "${CYAN}$line${NC}"
                        elif [[ "$line" == *"received task"* || "$line" == *"succeeded"* || "$line" == *"ready"* ]]; then
                            echo -e "${GREEN}$line${NC}"
                        elif [[ "$line" == *"failed"* || "$line" == *"retry"* ]]; then
                            echo -e "${RED}$line${NC}"
                        else
                            echo "$line"
                        fi
                    done
                else
                    print_warning "Log file is empty"
                fi
            fi
        done
        
        echo ""
        print_header "📊 Log Statistics"
        for log_file in "$LOG_DIR"/celery_*.log; do
            if [ -f "$log_file" ]; then
                local name=$(basename "$log_file" .log)
                name=${name#celery_}
                local total_lines=$(wc -l < "$log_file" 2>/dev/null || echo "0")
                local errors=$(grep -c "ERROR\|CRITICAL\|Traceback" "$log_file" 2>/dev/null || echo "0")
                local warnings=$(grep -c "WARNING" "$log_file" 2>/dev/null || echo "0")
                local tasks=$(grep -c "received task\|succeeded" "$log_file" 2>/dev/null || echo "0")
                
                print_info "   📋 $name: $total_lines lines total"
                if [ "$errors" -gt 0 ]; then
                    print_error "      ❌ Errors: $errors"
                fi
                if [ "$warnings" -gt 0 ]; then
                    print_warning "      ⚠️  Warnings: $warnings"
                fi
                if [ "$tasks" -gt 0 ]; then
                    print_success "      ✅ Tasks processed: $tasks"
                fi
            fi
        done
        
        echo ""
        print_info "💡 Useful log commands:"
        print_info "  tail -f $LOG_DIR/celery_[worker_name].log  # Real-time logs"
        print_info "  grep ERROR $LOG_DIR/*.log                   # Find all errors"
        print_info "  grep 'received task' $LOG_DIR/*.log         # Track task activity"
    else
        print_warning "Log directory not found: $LOG_DIR"
    fi
}

# Enhanced debugging
debug_issues() {
    print_header "🔍 Comprehensive System Debug"
    print_header "============================="
    echo ""
    
    local critical_issues=0
    
    # 0. Quick Celery app validation
    print_info "0. 🎯 Celery App Validation..."
    cd "$BACKEND_DIR"
    
    local import_output=$($PYTHON_CMD -c "
try:
    from app.tasks.celery_app import app
    print('SUCCESS: Celery app imported successfully')
    print(f'App name: {app.main}')
    print(f'Broker: {app.conf.broker_url}')
    print('VALIDATION_COMPLETE')
except Exception as e:
    print(f'IMPORT_ERROR: {str(e)}')
    import traceback
    traceback.print_exc()
" 2>&1)
    
    if echo "$import_output" | grep -q "VALIDATION_COMPLETE"; then
        print_success "   ✅ Celery app is working correctly"
        
        # Extract useful info
        local app_name=$(echo "$import_output" | grep "App name:" | cut -d: -f2 | xargs)
        local broker_url=$(echo "$import_output" | grep "Broker:" | cut -d: -f2- | xargs)
        
        print_info "   📝 App name: $app_name"
        print_info "   🔗 Broker: $broker_url"
        
        # Check for ML model loading (this is normal)
        if echo "$import_output" | grep -q "Loading existing models\|models loaded"; then
            local model_count=$(echo "$import_output" | grep -o "[0-9]\+ models loaded" | head -1 | grep -o "[0-9]\+")
            if [ -n "$model_count" ]; then
                print_success "   🤖 ML system: $model_count models loaded successfully"
            fi
        fi
    else
        print_error "   ❌ Celery app validation failed"
        if echo "$import_output" | grep -q "IMPORT_ERROR"; then
            print_error "   Import error details:"
            echo "$import_output" | grep -A 5 "IMPORT_ERROR" | sed 's/^/      /'
        else
            print_error "   Unexpected output:"
            echo "$import_output" | head -5 | sed 's/^/      /'
        fi
        critical_issues=$((critical_issues + 1))
    fi
    
    cd ..
    echo ""
    
    # 1. Redis check
    print_info "1. 🔗 Redis Test..."
    if command -v redis-cli >/dev/null 2>&1; then
        if redis-cli ping >/dev/null 2>&1; then
            print_success "   ✅ Redis connection established"
            
            # Queue analysis
            local queues=("celery" "price_data" "ml_tasks" "default")
            local total_tasks=0
            
            for queue in "${queues[@]}"; do
                local count=$(redis-cli llen "$queue" 2>/dev/null | tr -d ' ' || echo "0")
                total_tasks=$((total_tasks + count))
                if [ "$count" -gt 0 ]; then
                    print_info "   📦 Queue $queue: $count tasks"
                fi
            done
            
            if [ "$total_tasks" -eq 0 ]; then
                print_success "   ✅ All queues empty"
            elif [ "$total_tasks" -gt 50 ]; then
                print_error "   🚨 CRITICAL: High task backlog! ($total_tasks)"
                critical_issues=$((critical_issues + 1))
            else
                print_warning "   ⚠️  Total queued tasks: $total_tasks"
            fi
            
        else
            print_error "   ❌ Redis connection failed"
            critical_issues=$((critical_issues + 1))
        fi
    else
        print_warning "   ⚠️  redis-cli not available"
        critical_issues=$((critical_issues + 1))
    fi
    echo ""
    
    # 2. Import tests
    print_info "2. 🐍 Python Import Tests..."
    cd "$BACKEND_DIR"
    
    local import_output=$($PYTHON_CMD -c "from app.tasks.celery_app import app; print('SUCCESS: Celery app loaded')" 2>&1)
    local import_status=$?
    
    if [ $import_status -eq 0 ] && echo "$import_output" | grep -q "SUCCESS: Celery app loaded"; then
        print_success "   ✅ Celery app can be imported"
        
        # Check if there are ML model loading messages (which are normal)
        if echo "$import_output" | grep -q "Loading existing models\|models loaded"; then
            local model_count=$(echo "$import_output" | grep -o "[0-9]\+ models loaded" | head -1 | grep -o "[0-9]\+")
            if [ -n "$model_count" ]; then
                print_info "   🤖 ML system initialized: $model_count models loaded"
            fi
        fi
    else
        print_error "   ❌ Error importing Celery app"
        print_error "   Details:"
        echo "$import_output" | grep -E "(Error|Exception|Traceback|ImportError|ModuleNotFoundError)" | head -3 | sed 's/^/      /'
        
        # If no actual errors found, show that it might be a different issue
        if ! echo "$import_output" | grep -qE "(Error|Exception|Traceback|ImportError|ModuleNotFoundError)"; then
            print_warning "   ⚠️  Import completed but with unexpected output:"
            echo "$import_output" | head -3 | sed 's/^/      /'
        fi
        critical_issues=$((critical_issues + 1))
    fi
    
    cd ..
    echo ""
    
    # 3. Worker status analysis
    print_info "3. 👥 Worker Status Analysis..."
    show_status
    echo ""
    
    # 4. Recent error analysis
    print_info "4. 📋 Recent Error Analysis..."
    local total_errors=0
    local error_patterns=(
        "ERROR"
        "CRITICAL"
        "Traceback"
        "Exception"
        "failed"
        "ImportError"
        "ModuleNotFoundError"
    )
    
    for log_file in "$LOG_DIR"/celery_*.log; do
        if [ -f "$log_file" ]; then
            local name=$(basename "$log_file" .log)
            name=${name#celery_}
            
            for pattern in "${error_patterns[@]}"; do
                local count=$(grep -c "$pattern" "$log_file" 2>/dev/null || echo "0")
                if [ "$count" -gt 0 ]; then
                    print_warning "   ⚠️  $name: $count '$pattern' occurrences"
                    total_errors=$((total_errors + count))
                fi
            done
        fi
    done
    
    if [ "$total_errors" -eq 0 ]; then
        print_success "   ✅ No recent errors found in logs"
    else
        print_warning "   ⚠️  Total errors detected: $total_errors"
        critical_issues=$((critical_issues + 1))
    fi
    echo ""
    
    # 5. System resources check
    print_info "5. 💻 System Resources Check..."
    
    # Memory check
    if command -v free >/dev/null 2>&1; then
        local mem_info=$(free -m | grep "^Mem:")
        local total_mem=$(echo "$mem_info" | awk '{print $2}')
        local used_mem=$(echo "$mem_info" | awk '{print $3}')
        local mem_percent=$(( (used_mem * 100) / total_mem ))
        
        print_info "   💾 System memory: ${used_mem}MB/${total_mem}MB (${mem_percent}%)"
        
        if [ "$mem_percent" -gt 90 ]; then
            print_error "   🔥 CRITICAL: System memory critically low!"
            critical_issues=$((critical_issues + 1))
        elif [ "$mem_percent" -gt 80 ]; then
            print_warning "   ⚠️  System memory running high"
        fi
    fi
    echo ""
    
    # Summary and recommendations
    print_header "🎯 Debug Summary"
    
    if [ "$critical_issues" -eq 0 ]; then
        print_success "🟢 Excellent! No critical issues detected"
        print_info "Your Celery system is properly configured"
        echo ""
        print_info "💡 Maintenance recommendations:"
        print_info "  • Regular monitoring: ./scripts/run-workers.sh monitor"
        print_info "  • Weekly health checks: ./scripts/run-workers.sh health"
        print_info "  • Check logs: ./scripts/run-workers.sh logs"
    elif [ "$critical_issues" -le 2 ]; then
        print_warning "🟡 Good: Minor issues detected ($critical_issues)"
        echo ""
        print_info "🔧 Recommended actions:"
        print_info "  1. Review warnings above"
        print_info "  2. Restart problematic workers"
        print_info "  3. Monitor for improvement"
    else
        print_error "🔴 Critical: Multiple serious issues ($critical_issues)"
        echo ""
        print_error "🆘 Emergency actions:"
        print_error "  1. ./scripts/run-workers.sh fix"
        print_error "  2. ./scripts/run-workers.sh restart"
        print_error "  3. Check system resources (RAM, disk)"
        print_error "  4. If issues persist, check application code"
    fi
    
    echo ""
    print_info "🔧 Available tools:"
    print_info "  ./scripts/run-workers.sh fix      # Auto-fix issues"
    print_info "  ./scripts/run-workers.sh test     # Complete environment test"
    print_info "  ./scripts/run-workers.sh logs     # View detailed logs"
    print_info "  ./scripts/run-workers.sh restart  # Clean restart"
}

# Real-time monitoring
monitor_workers() {
    print_header "📈 Real-time Worker Monitoring"
    print_header "=============================="
    print_info "Press Ctrl+C to stop monitoring"
    echo ""
    
    trap 'echo -e "\n\n🛑 Monitoring stopped."; exit 0' INT
    
    local iteration=0
    while true; do
        clear
        
        iteration=$((iteration + 1))
        print_header "⏰ $(date '+%Y-%m-%d %H:%M:%S') - Update #$iteration"
        echo ""
        
        show_status
        
        # Show queue status if Redis available
        if command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1; then
            echo ""
            print_header "📦 Queue Status"
            local queue_length=$(redis-cli llen celery 2>/dev/null | tr -d ' ' || echo "0")
            local price_data_length=$(redis-cli llen price_data 2>/dev/null | tr -d ' ' || echo "0")
            local ml_tasks_length=$(redis-cli llen ml_tasks 2>/dev/null | tr -d ' ' || echo "0")
            
            print_info "   📋 Default Queue: $queue_length tasks"
            print_info "   💰 Price Data Queue: $price_data_length tasks"
            print_info "   🤖 ML Tasks Queue: $ml_tasks_length tasks"
            
            local total_queued=$((queue_length + price_data_length + ml_tasks_length))
            if [ "$total_queued" -gt 20 ]; then
                print_warning "   ⚠️  High queue load: $total_queued total tasks"
            elif [ "$total_queued" -gt 0 ]; then
                print_success "   ✅ Normal queue load: $total_queued total tasks"
            else
                print_success "   ✅ All queues empty"
            fi
        fi
        
        echo ""
        print_info "🔄 Auto-refresh in 5 seconds... (Press Ctrl+C to stop)"
        sleep 5
    done
}

# Quick celery app diagnostic
diagnose_celery_app() {
    print_header "🔍 Celery App File Diagnostics"
    print_header "==============================="
    echo ""
    
    local app_file="$BACKEND_DIR/app/tasks/celery_app.py"
    
    print_info "📁 Checking file: $app_file"
    
    if [ ! -f "$app_file" ]; then
        print_error "❌ File does not exist!"
        print_info "💡 Run: ./scripts/run-workers.sh fix"
        return 1
    fi
    
    print_success "✅ File exists"
    
    # Check file size
    local file_size=$(wc -c < "$app_file")
    print_info "📏 File size: $file_size bytes"
    
    if [ "$file_size" -lt 100 ]; then
        print_error "❌ File is too small (likely empty or incomplete)"
        print_info "💡 Run: ./scripts/run-workers.sh fix"
        return 1
    fi
    
    # Check for key components
    print_info "🔍 Checking file contents..."
    
    if grep -q "from celery import Celery" "$app_file"; then
        print_success "✅ Has Celery import"
    else
        print_error "❌ Missing Celery import"
    fi
    
    if grep -q "^app = Celery" "$app_file"; then
        print_success "✅ Has app = Celery definition"
    else
        print_error "❌ Missing 'app = Celery' definition"
        print_info "💡 This is likely the cause of your import error"
    fi
    
    if grep -q "broker_url" "$app_file"; then
        print_success "✅ Has broker configuration"
    else
        print_warning "⚠️  Missing broker configuration"
    fi
    
    # Test Python syntax
    print_info "🐍 Testing Python syntax..."
    cd "$BACKEND_DIR"
    if $PYTHON_CMD -m py_compile app/tasks/celery_app.py 2>/dev/null; then
        print_success "✅ Python syntax is valid"
    else
        print_error "❌ Python syntax errors detected"
        print_error "Syntax check output:"
        $PYTHON_CMD -m py_compile app/tasks/celery_app.py 2>&1 | sed 's/^/   /'
    fi
    cd ..
    
    echo ""
    print_info "📄 File contents (first 20 lines):"
    echo "----------------------------------------"
    head -20 "$app_file" | nl -ba
    echo "----------------------------------------"
    
    return 0
}

# Main execution
ACTION="${1:-start}"

case "$ACTION" in
    "start"|"")
        start_all_workers
        ;;
    "stop")
        stop_workers
        ;;
    "restart")
        print_header "🔄 Restarting Celery Workers"
        print_header "============================"
        echo ""
        stop_workers silent
        echo ""
        print_info "⏳ Waiting for cleanup..."
        sleep 3
        echo ""
        start_all_workers
        ;;
    "status")
        check_environment
        show_status
        ;;
    "monitor")
        check_environment
        monitor_workers
        ;;
    "logs")
        check_environment
        show_logs
        ;;
    "debug")
        debug_issues
        ;;
    "test")
        test_environment
        ;;
    "fix")
        auto_fix_issues
        ;;
    "diagnose")
        diagnose_celery_app
        ;;
    "health")
        test_environment
        echo ""
        debug_issues
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "❌ Unknown action: $ACTION"
        echo ""
        print_info "Available actions:"
        print_info "  start, stop, restart, status, monitor, logs, debug, test, fix, diagnose, health, help"
        echo ""
        print_info "For detailed information: './scripts/run-workers.sh help'"
        exit 1
        ;;
esac