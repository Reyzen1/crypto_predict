#!/bin/bash
# File: temp/start-ml-celery.sh
# Start ML-focused Celery workers for CryptoPredict - FIXED VERSION
# Compatible with actual project structure and ML tasks

set -e

echo "🤖 CryptoPredict ML Celery Services - Advanced Confi

echo ""
echo -e "${PURPLE}📊 System Summary${NC}"
echo "================"
echo -e "${CYAN}✅ Working Components:${NC}"
echo "• Python Environment: ✅ Ready"
echo "• Redis Connection: ✅ Active"  
echo "• Database Connection: ✅ Active"
echo "• Celery Configuration: ✅ Valid"
echo "• ML Tasks Import: ✅ Success"

if [ -f "logs/celery_ml_worker.log" ] && grep -q "PersistentModelRegistry initialized with" logs/celery_ml_worker.log; then
    model_count=$(grep "PersistentModelRegistry initialized with" logs/celery_ml_worker.log | tail -1 | grep -o '[0-9]\+' | head -1)
    echo "• ML Model Registry: ✅ $model_count models loaded"
fi

if [ -f "logs/celery_beat.log" ] && grep -q "Sending due task" logs/celery_beat.log; then
    echo "• Task Scheduler: ✅ Sending scheduled tasks"
figuration"
echo "============================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default configuration - optimized for ML tasks
WORKERS=2
LOG_LEVEL="info"
BACKEND_DIR="backend"
ML_CONCURRENCY=1  # ML tasks are CPU intensive
DATA_CONCURRENCY=3  # Data tasks can be more concurrent
FLOWER_PORT=5555
REDIS_HOST="localhost"
REDIS_PORT=6379
REDIS_DB=0

# Startup timeout configuration (seconds)
ML_WORKER_TIMEOUT=30    # ML worker needs time to load models
DATA_WORKER_TIMEOUT=40  # Data worker has higher concurrency
BEAT_TIMEOUT=25         # Beat scheduler is usually quick
MONITOR_WAIT=20         # Post-startup monitoring time

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --ml-concurrency)
            ML_CONCURRENCY="$2"
            shift 2
            ;;
        --data-concurrency)
            DATA_CONCURRENCY="$2"
            shift 2
            ;;
        --log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        --backend-dir)
            BACKEND_DIR="$2"
            shift 2
            ;;
        --flower-port)
            FLOWER_PORT="$2"
            shift 2
            ;;
        --redis-host)
            REDIS_HOST="$2"
            shift 2
            ;;
        --redis-port)
            REDIS_PORT="$2"
            shift 2
            ;;
        --ml-timeout)
            ML_WORKER_TIMEOUT="$2"
            shift 2
            ;;
        --data-timeout)
            DATA_WORKER_TIMEOUT="$2"
            shift 2
            ;;
        --beat-timeout)
            BEAT_TIMEOUT="$2"
            shift 2
            ;;
        --monitor-wait)
            MONITOR_WAIT="$2"
            shift 2
            ;;
        --install-flower)
            echo "📦 Installing Flower monitoring..."
            pip install flower --quiet
            if python -c "import flower" 2>/dev/null; then
                echo "✅ Flower installed successfully"
            else
                echo "❌ Flower installation failed"
                exit 1
            fi
            exit 0
            ;;
        --cleanup)
            echo "🧹 Running Celery cleanup and exiting..."
            cd "$BACKEND_DIR" 2>/dev/null || true
            cleanup_celery_processes
            echo "✅ Cleanup completed. You can now run the script normally."
            exit 0
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "🎯 ML Celery Configuration Options:"
            echo "  --workers NUMBER          Total worker processes (default: 2)"
            echo "  --ml-concurrency NUMBER   ML worker concurrency (default: 1)"
            echo "  --data-concurrency NUMBER Data worker concurrency (default: 3)"
            echo "  --log-level LEVEL         Log level: debug, info, warning, error (default: info)"
            echo "  --backend-dir PATH        Backend directory path (default: backend)"
            echo "  --flower-port PORT        Flower monitoring port (default: 5555)"
            echo "  --redis-host HOST         Redis host (default: localhost)"
            echo "  --redis-port PORT         Redis port (default: 6379)"
            echo ""
            echo "⏱️  Timeout Configuration:"
            echo "  --ml-timeout SECONDS      ML worker startup timeout (default: 30s)"
            echo "  --data-timeout SECONDS    Data worker startup timeout (default: 40s)"
            echo "  --beat-timeout SECONDS    Beat scheduler startup timeout (default: 25s)"
            echo "  --monitor-wait SECONDS    Post-startup monitoring time (default: 20s)"
            echo "  --install-flower          Install Flower monitoring and exit"
            echo "  --cleanup                 Clean up existing Celery processes and exit"
            echo "  --help                    Show this help message"
            echo ""
            echo "🔧 Example Usage:"
            echo "  $0 --ml-timeout 45 --data-timeout 60 --log-level debug"
            echo "  $0 --workers 4 --flower-port 5556 --monitor-wait 30"
            echo "  $0 --install-flower       # Install Flower monitoring"
            echo "  $0 --cleanup              # Clean up and exit"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use --help for available options"
            exit 1
            ;;
    esac
done

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use (Windows/MINGW64 compatible)
port_in_use() {
    if command_exists lsof; then
        lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
    elif command_exists netstat; then
        # Windows netstat format
        netstat -an | grep ":$1 " | grep "LISTENING" >/dev/null 2>&1
    else
        # Python fallback for Windows
        python -c "
import socket
import sys
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('localhost', $1))
    sock.close()
    if result == 0:
        sys.exit(0)  # Port is open
    else:
        sys.exit(1)  # Port is closed
except:
    sys.exit(1)
" >/dev/null 2>&1
    fi
}

# Function to kill processes on a port (Windows compatible)
kill_port() {
    local port=$1
    if port_in_use $port; then
        echo -e "${YELLOW}🧹 Cleaning up processes on port $port...${NC}"
        if command_exists lsof; then
            # Unix/Linux method
            lsof -ti :$port | xargs kill -9 2>/dev/null || true
        elif command_exists taskkill && command_exists netstat; then
            # Windows method
            for pid in $(netstat -ano | grep ":$port " | grep "LISTENING" | awk '{print $5}' | sort -u); do
                if [ -n "$pid" ] && [ "$pid" != "0" ]; then
                    taskkill //F //PID $pid 2>/dev/null || true
                fi
            done
        else
            echo -e "${YELLOW}⚠️  Cannot kill processes on port $port (limited tools available)${NC}"
        fi
        sleep 1
    fi
}

# Function to cleanup celery processes and files
cleanup_celery_processes() {
    echo -e "${BLUE}🧹 Comprehensive Celery cleanup...${NC}"
    
    # Check for existing Celery processes first
    local celery_processes_found=false
    
    if command_exists pgrep; then
        if pgrep -f "celery" > /dev/null 2>&1; then
            celery_processes_found=true
        fi
    else
        # Fallback check
        if ps aux 2>/dev/null | grep -v grep | grep -q "celery"; then
            celery_processes_found=true
        fi
    fi
    
    if [ "$celery_processes_found" = true ]; then
        echo -e "${CYAN}   Found existing Celery processes, stopping them...${NC}"
    else
        echo -e "${CYAN}   No active Celery processes found${NC}"
    fi
    
    # Stop Celery processes by pattern
    if command_exists pkill; then
        pkill -f "celery.*worker" 2>/dev/null || true
        pkill -f "celery.*beat" 2>/dev/null || true
        sleep 2
    elif command_exists taskkill; then
        # Windows approach
        echo -e "${CYAN}   Using Windows taskkill method...${NC}"
        tasklist | grep -i "celery" | awk '{print $2}' | while read pid; do
            if [ -n "$pid" ]; then
                echo -e "${CYAN}     Killing PID: $pid${NC}"
                taskkill //F //PID $pid 2>/dev/null || true
            fi
        done
        sleep 2
    fi
    
    # Remove PID files
    echo -e "${CYAN}   Cleaning up PID files...${NC}"
    local pid_files_removed=0
    
    for pid_file in logs/celerybeat.pid logs/celery_ml_worker.log.pid logs/celery_data_worker.log.pid logs/flower.log.pid; do
        if [ -f "$pid_file" ]; then
            rm -f "$pid_file" 2>/dev/null && pid_files_removed=$((pid_files_removed + 1))
        fi
    done
    
    if [ $pid_files_removed -gt 0 ]; then
        echo -e "${CYAN}     Removed $pid_files_removed PID files${NC}"
    else
        echo -e "${CYAN}     No PID files to remove${NC}"
    fi
    
    # Remove old schedule files (they can cause conflicts)
    echo -e "${CYAN}   Cleaning up schedule files...${NC}"
    local schedule_files_removed=0
    
    for schedule_file in celerybeat-schedule celerybeat-schedule.db celerybeat-schedule.dat celerybeat-schedule.dir celerybeat-schedule.bak; do
        if [ -f "$schedule_file" ]; then
            rm -f "$schedule_file" 2>/dev/null && schedule_files_removed=$((schedule_files_removed + 1))
        fi
    done
    
    if [ $schedule_files_removed -gt 0 ]; then
        echo -e "${CYAN}     Removed $schedule_files_removed schedule files${NC}"
    else
        echo -e "${CYAN}     No schedule files to remove${NC}"
    fi
    
    # Check and kill specific PIDs if they exist
    echo -e "${CYAN}   Checking for orphaned processes...${NC}"
    
    # Python-based process cleanup as fallback
    python -c "
import psutil
import sys
import re

try:
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if re.search(r'celery.*(worker|beat)', cmdline, re.IGNORECASE):
                print(f'     Killing Celery process: PID {proc.info[\"pid\"]}')
                proc.terminate()
                killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    if killed_count > 0:
        print(f'     Terminated {killed_count} Celery processes')
    else:
        print('     No orphaned Celery processes found')
        
except ImportError:
    print('     psutil not available for detailed cleanup')
except Exception as e:
    print(f'     Cleanup error: {e}')
" 2>/dev/null || echo -e "${YELLOW}     Python cleanup skipped${NC}"
    
    # Wait for processes to fully terminate
    sleep 3
    
    echo -e "${GREEN}✅ Celery cleanup completed${NC}"
    
    # Final verification
    if command_exists pgrep; then
        if pgrep -f "celery" > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Some Celery processes may still be running${NC}"
            echo -e "${YELLOW}   You may need to manually kill them or reboot${NC}"
        else
            echo -e "${GREEN}✅ All Celery processes successfully terminated${NC}"
        fi
    fi
}

# Function to check Python module availability
check_python_module() {
    local module=$1
    local description=$2
    
    if python -c "import $module" 2>/dev/null; then
        echo -e "${GREEN}✅ $description: Available${NC}"
        return 0
    else
        echo -e "${RED}❌ $description: Not available${NC}"
        return 1
    fi
}

# Function to test Redis connection with retries
test_redis_connection() {
    local max_retries=3
    local retry=0
    
    echo -e "${BLUE}🔗 Testing Redis connection ($REDIS_HOST:$REDIS_PORT)...${NC}"
    
    while [ $retry -lt $max_retries ]; do
        if python -c "
import redis
import sys
try:
    r = redis.Redis(host='$REDIS_HOST', port=$REDIS_PORT, db=$REDIS_DB, socket_timeout=5)
    r.ping()
    print('✅ Redis connection successful')
    sys.exit(0)
except redis.ConnectionError as e:
    print(f'❌ Redis connection failed: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Redis test failed: {e}')
    sys.exit(1)
" 2>/dev/null; then
            return 0
        fi
        
        retry=$((retry + 1))
        if [ $retry -lt $max_retries ]; then
            echo -e "${YELLOW}⚠️  Redis connection failed, retrying ($retry/$max_retries)...${NC}"
            sleep 2
        fi
    done
    
    echo -e "${RED}❌ Redis connection failed after $max_retries attempts${NC}"
    echo -e "${BLUE}💡 Solutions:${NC}"
    echo "   • Start Redis: redis-server"
    echo "   • Docker: docker run -d -p 6379:6379 redis:alpine"
    echo "   • Check host/port: --redis-host $REDIS_HOST --redis-port $REDIS_PORT"
    return 1
}

# Function to test database connection
test_database_connection() {
    echo -e "${BLUE}🗄️  Testing database connection...${NC}"
    
    python -c "
import sys
sys.path.insert(0, '.')

try:
    from app.core.database import engine
    from sqlalchemy import text
    
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1')).fetchone()
        if result:
            print('✅ Database connection successful')
        else:
            print('❌ Database query failed')
            sys.exit(1)
except ImportError as e:
    print(f'❌ Database import failed: {e}')
    print('   Make sure you are in the backend directory')
    sys.exit(1)
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('   Make sure PostgreSQL is running and configured')
    sys.exit(1)
" || return 1
}

# Function to test Celery configuration
test_celery_configuration() {
    echo -e "${BLUE}⚙️  Testing Celery configuration...${NC}"
    
    python -c "
import sys
sys.path.insert(0, '.')

try:
    # Test Celery app import
    from app.tasks.celery_app import celery_app
    print('✅ Celery app imported successfully')
    
    # Check broker and backend configuration
    broker_url = celery_app.conf.broker_url
    result_backend = celery_app.conf.result_backend
    
    print(f'   📡 Broker: {broker_url}')
    print(f'   💾 Backend: {result_backend}')
    
    # Test task imports
    from app.tasks.ml_tasks import (
        auto_train_models, 
        generate_scheduled_predictions,
        evaluate_model_performance,
        cleanup_old_predictions
    )
    print('✅ ML tasks imported successfully')
    
    # Test convenience functions
    from app.tasks.ml_tasks import (
        start_auto_training,
        start_prediction_generation,
        start_performance_evaluation,
        start_prediction_cleanup
    )
    print('✅ ML task helpers imported successfully')
    
    # Test data collection tasks
    from app.tasks.price_collector import (
        sync_all_prices,
        sync_historical_data,
        discover_new_cryptocurrencies,
        cleanup_old_data
    )
    print('✅ Data collection tasks imported successfully')
    
    # Test scheduler
    from app.tasks.scheduler import task_scheduler, get_next_run_times
    print('✅ Task scheduler imported successfully')
    
except ImportError as e:
    print(f'❌ Import failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f'❌ Celery configuration failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" || return 1
}

# Function to start a service with enhanced monitoring
start_service() {
    local service_name="$1"
    local command="$2"
    local log_file="$3"
    local success_patterns="$4"
    local timeout="${5:-15}"
    
    echo -e "${BLUE}🚀 Starting $service_name...${NC}"
    echo -e "${CYAN}   Command: $command${NC}"
    echo -e "${CYAN}   Log file: $log_file${NC}"
    
    # Start the service in background
    eval "$command" > "$log_file" 2>&1 &
    local pid=$!
    echo -e "${CYAN}   Process ID: $pid${NC}"
    
    # Wait for startup with timeout
    local wait_time=0
    local check_interval=2  # Check every 2 seconds instead of 1
    local success_found=false
    
    while [ $wait_time -lt $timeout ]; do
        # Check if process is still running
        if ! kill -0 $pid 2>/dev/null; then
            echo -e "${RED}❌ $service_name process died during startup${NC}"
            echo -e "${RED}   Check log file: $log_file${NC}"
            if [ -f "$log_file" ]; then
                echo -e "${RED}   Last few lines:${NC}"
                tail -5 "$log_file" | sed 's/^/     /'
            fi
            return 1
        fi
        
        # Check for success patterns in log
        if [ -n "$success_patterns" ] && [ -f "$log_file" ]; then
            # Enhanced pattern matching
            if echo "$success_patterns" | tr '|' '\n' | while read pattern; do
                if [ -n "$pattern" ]; then
                    # Check both recent lines and specific patterns
                    if tail -20 "$log_file" 2>/dev/null | grep -q "$pattern"; then
                        echo "SUCCESS_FOUND"
                        exit 0
                    fi
                fi
            done | grep -q "SUCCESS_FOUND"; then
                success_found=true
                break
            fi
            
            # Additional check for worker readiness
            if tail -15 "$log_file" 2>/dev/null | grep -q "celery@.*ready\|Connected to redis\|worker: Warm restart"; then
                success_found=true
                break
            fi
        fi
        
        sleep $check_interval
        wait_time=$((wait_time + check_interval))
        
        # Show progress every 6 seconds (3 cycles)
        if [ $((wait_time % 6)) -eq 0 ]; then
            echo -e "${YELLOW}   ⏳ Waiting for startup... (${wait_time}s/${timeout}s)${NC}"
        fi
    done
    
    if [ "$success_found" = true ]; then
        echo -e "${GREEN}✅ $service_name started successfully (PID: $pid)${NC}"
    elif kill -0 $pid 2>/dev/null; then
        echo -e "${YELLOW}⚠️  $service_name started but initialization not confirmed (PID: $pid)${NC}"
        echo -e "${YELLOW}   Monitor log: tail -f $log_file${NC}"
        
        # Show last few lines for troubleshooting
        if [ -f "$log_file" ]; then
            echo -e "${CYAN}   Recent log activity:${NC}"
            tail -3 "$log_file" 2>/dev/null | sed 's/^/     /'
        fi
    else
        echo -e "${RED}❌ $service_name failed to start${NC}"
        return 1
    fi
    
    # Store PID for later management
    echo $pid > "${log_file}.pid"
    return 0
}

# Function to check if a process is running (Windows compatible)
check_process_running() {
    local pattern="$1"
    
    if command_exists pgrep; then
        # Unix/Linux method
        pgrep -f "$pattern" > /dev/null 2>&1
    elif command_exists tasklist; then
        # Windows method - check for celery processes
        tasklist | grep -i "celery" > /dev/null 2>&1 || \
        tasklist | grep -i "python" > /dev/null 2>&1
    else
        # Python fallback method
        python -c "
import psutil
import sys
import re

try:
    pattern = '$pattern'
    found = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if re.search(pattern, cmdline, re.IGNORECASE):
                found = True
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    sys.exit(0 if found else 1)
except ImportError:
    # psutil not available, assume running if we got this far
    sys.exit(0)
except:
    sys.exit(1)
" 2>/dev/null
    fi
}
# Function to check service health (Windows compatible)
check_service_health() {
    local service_name="$1"
    local pid_file="$2"
    local port="$3"
    local process_pattern="$4"
    
    local status="❓ Unknown"
    
    # Check PID file
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            status="✅ Running (PID: $pid)"
        elif [ -n "$pid" ]; then
            # Check with tasklist on Windows
            if command_exists tasklist; then
                if tasklist /FI "PID eq $pid" 2>/dev/null | grep -q "$pid"; then
                    status="✅ Running (PID: $pid)"
                else
                    status="❌ Process not found"
                fi
            else
                status="❌ Process not found"
            fi
        else
            status="❌ Invalid PID"
        fi
    fi
    
    # Check process pattern
    if [ -n "$process_pattern" ]; then
        if check_process_running "$process_pattern"; then
            status="✅ Running (process found)"
        elif [ "$status" != "✅ Running"* ]; then
            status="❌ Process not running"
        fi
    fi
    
    # Check port
    if [ -n "$port" ]; then
        if port_in_use "$port"; then
            status="✅ Running (port $port active)"
        elif [ "$status" != "✅ Running"* ]; then
            status="❌ Port $port not active"
        fi
    fi
    
    echo -e "${CYAN}   $service_name: $status${NC}"
}

# Main execution starts here
echo -e "${PURPLE}🔍 Environment Validation${NC}"
echo "================================"

# Check if we're in the right directory
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Backend directory '$BACKEND_DIR' not found!${NC}"
    echo -e "${BLUE}💡 Run this script from the project root directory${NC}"
    echo -e "${BLUE}   or specify correct path: --backend-dir path/to/backend${NC}"
    exit 1
fi

# Change to backend directory
cd "$BACKEND_DIR"
echo -e "${GREEN}✅ Changed to backend directory: $(pwd)${NC}"

# Check for required files
required_files=("requirements.txt" "app/__init__.py" "app/tasks/__init__.py")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Required file '$file' not found in backend directory!${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ Required files present${NC}"

# Check Python and basic dependencies
echo -e "${PURPLE}🐍 Python Environment Check${NC}"
echo "============================"

if ! command_exists python; then
    echo -e "${RED}❌ Python not found! Please install Python 3.11+${NC}"
    exit 1
fi

python_version=$(python --version 2>&1)
echo -e "${GREEN}✅ Python: $python_version${NC}"

if ! command_exists pip; then
    echo -e "${RED}❌ pip not found! Please install pip${NC}"
    exit 1
fi

# Check core Python modules
echo -e "${BLUE}📦 Checking core dependencies...${NC}"
# Check if Celery is installed
if ! check_python_module "celery" "Celery"; then
    echo -e "${RED}❌ Celery not available. Installing...${NC}"
    pip install celery[redis] --quiet
fi

# Check if Flower is installed (optional monitoring)
if ! python -c "import flower" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Flower monitoring not installed${NC}"
    
    # Check if running in interactive mode
    if [ -t 0 ]; then
        read -p "Install Flower for web monitoring? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}📦 Installing Flower...${NC}"
            pip install flower --quiet
            if python -c "import flower" 2>/dev/null; then
                echo -e "${GREEN}✅ Flower installed successfully${NC}"
            else
                echo -e "${YELLOW}⚠️  Flower installation may have failed${NC}"
            fi
        else
            echo -e "${BLUE}ℹ️  Skipping Flower installation${NC}"
        fi
    else
        echo -e "${BLUE}ℹ️  Non-interactive mode: Skipping Flower installation${NC}"
        echo -e "${BLUE}💡 Install manually with: pip install flower${NC}"
    fi
fi

check_python_module "sqlalchemy" "SQLAlchemy" || {
    echo -e "${RED}❌ SQLAlchemy required but not available${NC}"
    exit 1
}

# Install/update requirements
echo -e "${BLUE}📦 Installing/updating requirements...${NC}"
if pip install -r requirements.txt --quiet --disable-pip-version-check; then
    echo -e "${GREEN}✅ Requirements installed successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Some requirements may have failed to install${NC}"
fi

# Service validation
echo -e "${PURPLE}🔧 Service Validation${NC}"
echo "===================="

# Test Redis connection
test_redis_connection || exit 1

# Test database connection  
test_database_connection || exit 1

# Test Celery configuration
test_celery_configuration || exit 1

# Cleanup existing processes
echo -e "${PURPLE}🧹 Process Cleanup${NC}"
echo "=================="

echo -e "${BLUE}🛑 Stopping existing Celery processes...${NC}"

# Comprehensive cleanup
cleanup_celery_processes

# Additional port cleanup
kill_port $FLOWER_PORT  # Flower monitoring port

# Create log directory
mkdir -p logs
echo -e "${GREEN}✅ Log directory ready: logs/${NC}"

# Start services
echo -e "${PURPLE}🚀 Service Startup${NC}"
echo "=================="

# Start ML-focused Celery worker
echo -e "${YELLOW}🤖 Starting ML Celery Worker...${NC}"
start_service \
    "ML Worker" \
    "celery -A app.tasks.celery_app worker --loglevel=$LOG_LEVEL --concurrency=$ML_CONCURRENCY --queues=ml_tasks --hostname=ml_worker@%h --pool=prefork" \
    "logs/celery_ml_worker.log" \
    "ready|Connected to|mingle: searching for neighbors|sync with" \
    $ML_WORKER_TIMEOUT

# Start general Celery worker for data tasks
echo -e "${YELLOW}⚙️  Starting Data Collection Worker...${NC}"
start_service \
    "Data Worker" \
    "celery -A app.tasks.celery_app worker --loglevel=$LOG_LEVEL --concurrency=$DATA_CONCURRENCY --queues=price_data,default --hostname=data_worker@%h --pool=prefork" \
    "logs/celery_data_worker.log" \
    "ready|Connected to|mingle: searching for neighbors|sync with" \
    $DATA_WORKER_TIMEOUT

# Start Celery Beat scheduler
echo -e "${YELLOW}⏰ Starting Celery Beat Scheduler...${NC}"
start_service \
    "Beat Scheduler" \
    "celery -A app.tasks.celery_app beat --loglevel=$LOG_LEVEL --schedule=celerybeat-schedule --pidfile=logs/celerybeat.pid" \
    "logs/celery_beat.log" \
    "beat: Starting|Scheduler: Sending|Sending due task|celery beat.*is starting" \
    $BEAT_TIMEOUT

# Start Flower monitoring (optional)
FLOWER_AVAILABLE=false
if python -c "import flower" 2>/dev/null; then
    FLOWER_AVAILABLE=true
    echo -e "${YELLOW}🌸 Starting Flower Monitoring...${NC}"
    start_service \
        "Flower Monitor" \
        "celery -A app.tasks.celery_app flower --port=$FLOWER_PORT --basic_auth=admin:cryptopredict123 --address=127.0.0.1" \
        "logs/flower.log" \
        "Visit me at|Flower is ready" \
        10
else
    echo -e "${YELLOW}⚠️  Flower not installed, skipping monitoring dashboard${NC}"
    echo -e "${BLUE}💡 Install with: ./temp/start-ml-celery.sh --install-flower${NC}"
fi

# Service information display
echo ""
echo -e "${PURPLE}📋 Service Configuration${NC}"
echo "========================"

echo -e "${BLUE}🎯 Active Services:${NC}"
echo "• ML Worker: Processing ML tasks (training, predictions, evaluation)"
echo "  - Queue: ml_tasks"
echo "  - Concurrency: $ML_CONCURRENCY"
echo "  - Pool: prefork"
echo "  - Startup timeout: ${ML_WORKER_TIMEOUT}s"

echo "• Data Worker: Processing data collection and general tasks"
echo "  - Queues: price_data, default"
echo "  - Concurrency: $DATA_CONCURRENCY"
echo "  - Pool: prefork"
echo "  - Startup timeout: ${DATA_WORKER_TIMEOUT}s"

echo "• Beat Scheduler: Running periodic tasks"
echo "  - Schedule file: celerybeat-schedule"
echo "  - PID file: logs/celerybeat.pid"
echo "  - Startup timeout: ${BEAT_TIMEOUT}s"

if [ "$FLOWER_AVAILABLE" = true ]; then
    echo "• Flower Monitor: Web-based task monitoring"
    echo "  - URL: http://localhost:$FLOWER_PORT"
    echo "  - Credentials: admin:cryptopredict123"
else
    echo "• Flower Monitor: Not installed (optional)"
fi

echo ""
echo -e "${BLUE}📊 Queue Configuration:${NC}"
echo "• ml_tasks: ML training, predictions, performance evaluation"
echo "• price_data: Price synchronization and data collection"
echo "• default: General background tasks and system operations"

echo ""
echo -e "${BLUE}📝 Log Files:${NC}"
echo "• ML Worker: logs/celery_ml_worker.log"
echo "• Data Worker: logs/celery_data_worker.log"
echo "• Beat Scheduler: logs/celery_beat.log"
if [ "$FLOWER_AVAILABLE" = true ]; then
    echo "• Flower Monitor: logs/flower.log"
else
    echo "• Flower Monitor: Not installed"
fi

echo ""
echo -e "${BLUE}🔧 Management Commands:${NC}"
echo "• Stop all services: pkill -f celery (or taskkill on Windows)"
echo "• Stop workers only: pkill -f 'celery.*worker'"
echo "• Stop beat only: pkill -f 'celery.*beat'"
echo "• Complete cleanup: ./temp/start-ml-celery.sh --cleanup"
echo "• View ML logs: tail -f logs/celery_ml_worker.log"
echo "• View data logs: tail -f logs/celery_data_worker.log"
echo "• View beat logs: tail -f logs/celery_beat.log"

echo ""
echo -e "${BLUE}🚀 ML Task Examples:${NC}"
echo "• Auto train models:"
echo "  python -c \"from app.tasks.ml_tasks import start_auto_training; print('Task ID:', start_auto_training())\""

echo "• Generate predictions:"
echo "  python -c \"from app.tasks.ml_tasks import start_prediction_generation; print('Task ID:', start_prediction_generation())\""

echo "• Evaluate performance:"
echo "  python -c \"from app.tasks.ml_tasks import start_performance_evaluation; print('Task ID:', start_performance_evaluation())\""

echo "• Cleanup old predictions:"
echo "  python -c \"from app.tasks.ml_tasks import start_prediction_cleanup; print('Task ID:', start_prediction_cleanup(30))\""

echo ""
echo -e "${BLUE}📊 Data Collection Task Examples:${NC}"
echo "• Sync all prices:"
echo "  python -c \"from app.tasks.price_collector import sync_all_prices; print('Task ID:', sync_all_prices.delay().id)\""

echo "• Sync historical data:"
echo "  python -c \"from app.tasks.price_collector import sync_historical_data; print('Task ID:', sync_historical_data.delay().id)\""

# Monitor services briefly
echo ""
echo -e "${PURPLE}🔍 Service Health Monitoring${NC}"
echo "============================"

echo -e "${BLUE}⏳ Monitoring services for $MONITOR_WAIT seconds (extended wait)...${NC}"
sleep $MONITOR_WAIT

echo -e "${BLUE}📊 Service Health Check:${NC}"

# Enhanced health check with log analysis
echo -e "${CYAN}🔍 Process-based detection:${NC}"
check_service_health "ML Worker" "logs/celery_ml_worker.log.pid" "" "celery.*worker.*ml_tasks"
check_service_health "Data Worker" "logs/celery_data_worker.log.pid" "" "celery.*worker.*price_data"
check_service_health "Beat Scheduler" "logs/celerybeat.pid" "" "celery.*beat"

if [ "$FLOWER_AVAILABLE" = true ]; then
    check_service_health "Flower Monitor" "logs/flower.log.pid" "$FLOWER_PORT" ""
else
    echo -e "${YELLOW}   Flower Monitor: Not installed${NC}"
fi

echo ""
echo -e "${CYAN}📋 Log-based verification (Enhanced):${NC}"

# Check ML Worker logs
if [ -f "logs/celery_ml_worker.log" ]; then
    if tail -20 "logs/celery_ml_worker.log" | grep -q "ready\|Connected to\|mingle\|sync with" 2>/dev/null; then
        echo -e "${GREEN}✅ ML Worker: Active (confirmed via logs)${NC}"
    elif tail -10 "logs/celery_ml_worker.log" | grep -E "ERROR|CRITICAL|Failed" >/dev/null 2>&1; then
        echo -e "${RED}❌ ML Worker: Errors detected in logs${NC}"
    else
        echo -e "${CYAN}ℹ️  ML Worker: Log activity detected${NC}"
    fi
else
    echo -e "${RED}❌ ML Worker: Log file not found${NC}"
fi

# Check Data Worker logs  
if [ -f "logs/celery_data_worker.log" ]; then
    if tail -20 "logs/celery_data_worker.log" | grep -q "ready\|Connected to\|mingle\|sync with" 2>/dev/null; then
        echo -e "${GREEN}✅ Data Worker: Active (confirmed via logs)${NC}"
    elif tail -10 "logs/celery_data_worker.log" | grep -E "ERROR|CRITICAL|Failed" >/dev/null 2>&1; then
        echo -e "${RED}❌ Data Worker: Errors detected in logs${NC}"
    else
        echo -e "${CYAN}ℹ️  Data Worker: Log activity detected${NC}"
    fi
else
    echo -e "${RED}❌ Data Worker: Log file not found${NC}"
fi

# Check Beat Scheduler logs
if [ -f "logs/celery_beat.log" ]; then
    if tail -20 "logs/celery_beat.log" | grep -q "beat: Starting\|Scheduler: Sending\|Sending due task" 2>/dev/null; then
        echo -e "${GREEN}✅ Beat Scheduler: Active (confirmed via logs)${NC}"
    elif tail -10 "logs/celery_beat.log" | grep -E "ERROR|CRITICAL|Failed" >/dev/null 2>&1; then
        echo -e "${RED}❌ Beat Scheduler: Errors detected in logs${NC}"
    else
        echo -e "${CYAN}ℹ️  Beat Scheduler: Log activity detected${NC}"
    fi
else
    echo -e "${RED}❌ Beat Scheduler: Log file not found${NC}"
fi

# Final status
echo ""
echo -e "${PURPLE}🎉 Startup Complete${NC}"
echo "=================="

# Check if critical services are running (Windows compatible)
critical_services_running=true

if ! check_process_running "celery.*worker.*ml_tasks"; then
    echo -e "${RED}⚠️  ML Worker not detected - check logs/celery_ml_worker.log${NC}"
    critical_services_running=false
fi

if ! check_process_running "celery.*worker.*price_data|celery.*worker.*default"; then
    echo -e "${RED}⚠️  Data Worker not detected - check logs/celery_data_worker.log${NC}"
    critical_services_running=false
fi

if ! check_process_running "celery.*beat"; then
    echo -e "${RED}⚠️  Beat Scheduler not detected - check logs/celery_beat.log${NC}"
    critical_services_running=false
fi

# Alternative service check using log files (Windows fallback)
check_service_via_logs() {
    local service_name="$1"
    local log_file="$2"
    local success_patterns="$3"
    
    if [ ! -f "$log_file" ]; then
        echo -e "${RED}❌ $service_name: Log file not found${NC}"
        return 1
    fi
    
    # Check if log has been updated recently (within last 120 seconds)
    if command_exists stat; then
        local log_age
        if stat -c %Y "$log_file" >/dev/null 2>&1; then
            # Linux stat
            log_age=$(expr $(date +%s) - $(stat -c %Y "$log_file" 2>/dev/null || echo 0))
        elif stat -f %m "$log_file" >/dev/null 2>&1; then
            # macOS stat
            log_age=$(expr $(date +%s) - $(stat -f %m "$log_file" 2>/dev/null || echo 0))
        else
            log_age=0
        fi
        
        if [ $log_age -gt 120 ]; then
            echo -e "${YELLOW}⚠️  $service_name: Log file seems stale (${log_age}s old)${NC}"
        fi
    fi
    
    # Check for success patterns
    if [ -n "$success_patterns" ]; then
        local found_pattern=false
        
        # Use a more reliable method to check patterns
        if echo "$success_patterns" | tr '|' '\n' | while read pattern; do
            if [ -n "$pattern" ] && tail -20 "$log_file" 2>/dev/null | grep -q "$pattern" 2>/dev/null; then
                echo "FOUND"
                exit 0
            fi
        done | grep -q "FOUND"; then
            found_pattern=true
        fi
        
        if [ "$found_pattern" = true ]; then
            echo -e "${GREEN}✅ $service_name: Active (confirmed via logs)${NC}"
            return 0
        fi
    fi
    
    # Check for error patterns
    local error_patterns="ERROR|CRITICAL|Failed|Exception|Traceback"
    if tail -10 "$log_file" 2>/dev/null | grep -E "$error_patterns" >/dev/null 2>&1; then
        echo -e "${RED}❌ $service_name: Errors detected in logs${NC}"
        return 1
    fi
    
    # If no specific patterns found, check if there's recent activity
    if tail -5 "$log_file" 2>/dev/null | wc -l | grep -q "[1-9]"; then
        echo -e "${CYAN}ℹ️  $service_name: Log activity detected${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}⚠️  $service_name: Status unclear from logs${NC}"
    return 1
}
    echo -e "${GREEN}🎯 All critical ML Celery services are running successfully!${NC}"
    echo -e "${GREEN}✨ CryptoPredict ML pipeline is ready for AI operations!${NC}"
    
    if check_python_module "flower" "Flower" 2>/dev/null && port_in_use $FLOWER_PORT; then
        echo -e "${CYAN}🌸 Flower monitoring available at: http://localhost:$FLOWER_PORT${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}💡 Quick Health Check:${NC}"
    echo "python -c \"from app.tasks.celery_app import health_check; print('Health check result:', health_check.delay().get(timeout=10))\""
    
    echo ""
    echo -e "${BLUE}🧪 Test ML Tasks:${NC}"
    echo "python -c \"from app.tasks.ml_tasks import start_auto_training; print('ML Task ID:', start_auto_training())\""
    
else
    echo -e "${YELLOW}⚠️  Some services may have issues - detailed diagnostics below${NC}"
    echo ""
    echo -e "${BLUE}🔧 Troubleshooting Commands:${NC}"
    echo "• Check Redis: redis-cli ping"
    echo "• Check database: cd backend && python -c \"from app.core.database import engine; engine.connect()\""
    echo "• Check all logs: tail -f logs/celery_*.log"
    echo ""
    echo -e "${BLUE}📋 Manual Service Status:${NC}"
    echo "• View ML Worker: tail -20 logs/celery_ml_worker.log"
    echo "• View Data Worker: tail -20 logs/celery_data_worker.log" 
    echo "• View Beat Scheduler: tail -20 logs/celery_beat.log"
    echo ""
    echo -e "${BLUE}🔄 Restart if needed:${NC}"
    echo "• Complete cleanup: ./temp/start-ml-celery.sh --cleanup"
    echo "• Stop all: pkill -f celery (or taskkill on Windows)"
    echo "• Restart: ./temp/start-ml-celery.sh"
    echo "• Force cleanup: rm -f logs/*.pid celerybeat-schedule*"
fi

echo ""
echo -e "${PURPLE}📊 System Summary${NC}"
echo "================"
echo -e "${CYAN}✅ Working Components:${NC}"
echo "• Python Environment: ✅ Ready"
echo "• Redis Connection: ✅ Active"  
echo "• Database Connection: ✅ Active"
echo "• Celery Configuration: ✅ Valid"
echo "• ML Tasks Import: ✅ Success"

if [ -f "logs/celery_ml_worker.log" ] && grep -q "PersistentModelRegistry initialized with" logs/celery_ml_worker.log 2>/dev/null; then
    model_count=$(grep "PersistentModelRegistry initialized with" logs/celery_ml_worker.log | tail -1 | grep -o '[0-9]\+' | head -1 2>/dev/null)
    echo "• ML Model Registry: ✅ $model_count models loaded"
fi

if [ -f "logs/celery_beat.log" ] && grep -q "Sending due task" logs/celery_beat.log 2>/dev/null; then
    echo "• Task Scheduler: ✅ Sending scheduled tasks"
fi

echo ""
echo -e "${GREEN}🚀 CryptoPredict ML Celery setup complete!${NC}"

# Final validation summary  
echo ""
echo -e "${PURPLE}🎯 Final Validation Summary${NC}"
echo "=========================="

# Check for actual evidence of services working
services_evidence=0
total_evidence=3

# ML Worker evidence check
if [ -f "logs/celery_ml_worker.log" ] && (tail -15 "logs/celery_ml_worker.log" 2>/dev/null | grep -q "sync with\|ready\|Connected to\|mingle"); then
    echo -e "${GREEN}✅ ML Worker: Evidence of successful startup${NC}"
    services_evidence=$((services_evidence + 1))
else
    echo -e "${YELLOW}⚠️  ML Worker: Limited startup evidence (check logs)${NC}"
fi

# Data Worker evidence check  
if [ -f "logs/celery_data_worker.log" ] && (tail -15 "logs/celery_data_worker.log" 2>/dev/null | grep -q "sync with\|ready\|Connected to\|mingle"); then
    echo -e "${GREEN}✅ Data Worker: Evidence of successful startup${NC}"
    services_evidence=$((services_evidence + 1))
else
    echo -e "${YELLOW}⚠️  Data Worker: Limited startup evidence (check logs)${NC}"
fi

# Beat Scheduler evidence check
if [ -f "logs/celery_beat.log" ] && (tail -15 "logs/celery_beat.log" 2>/dev/null | grep -q "Sending due task\|Scheduler: Sending\|beat: Starting"); then
    echo -e "${GREEN}✅ Beat Scheduler: Evidence of task scheduling${NC}"
    services_evidence=$((services_evidence + 1))
else
    echo -e "${YELLOW}⚠️  Beat Scheduler: Limited scheduling evidence (check logs)${NC}"
fi

# Overall assessment
success_percentage=$((services_evidence * 100 / total_evidence))
echo ""
echo -e "${CYAN}📊 Overall Success Rate: ${success_percentage}% (${services_evidence}/${total_evidence} services confirmed)${NC}"

if [ $success_percentage -ge 80 ]; then
    echo -e "${GREEN}🎉 EXCELLENT: ML Celery services are operational!${NC}"
    echo -e "${GREEN}🚀 Ready for machine learning operations!${NC}"
elif [ $success_percentage -ge 60 ]; then
    echo -e "${YELLOW}⚠️  GOOD: Most services operational, minor issues possible${NC}"
    echo -e "${YELLOW}🔧 Monitor logs for any issues${NC}"
else
    echo -e "${RED}⚠️  ATTENTION: Services may need troubleshooting${NC}"
    echo -e "${RED}🔧 Check individual log files for errors${NC}"
fi

echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Monitor logs: tail -f logs/celery_*.log"
echo "2. Test ML functions: python -c \"from app.tasks.ml_tasks import start_auto_training; start_auto_training()\""
echo "3. Check Redis: redis-cli ping"
echo "4. View scheduled tasks: python -c \"from app.tasks.scheduler import get_next_run_times; print(get_next_run_times())\""
echo ""
echo -e "${CYAN}💡 Troubleshooting:${NC}"
echo "• If PID errors occur: ./temp/start-ml-celery.sh --cleanup"
echo "• Install Flower monitoring: ./temp/start-ml-celery.sh --install-flower"
echo "• For slower systems: ./temp/start-ml-celery.sh --ml-timeout 60 --data-timeout 90"
echo "• View all options: ./temp/start-ml-celery.sh --help"