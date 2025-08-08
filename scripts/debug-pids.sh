#!/bin/bash
# File: temp/debug-pids.sh
# Debug script for PID management issues

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

echo -e "${CYAN}🔍 PID Debug Script${NC}"
echo "==================="
echo

# 1. Check directory structure
print_info "1️⃣ Checking directory structure:"
echo "   LOG_DIR: scripts/logs ($([ -d "scripts/logs" ] && echo "exists" || echo "missing"))"
echo "   PID_DIR: scripts/logs/pids ($([ -d "scripts/logs/pids" ] && echo "exists" || echo "missing"))"
echo

# 2. List PID files
print_info "2️⃣ PID Files:"
if [ -d "scripts/logs/pids" ]; then
    ls -la scripts/logs/pids/*.pid 2>/dev/null || echo "   No .pid files found"
    echo
    # Show content of each PID file
    for pid_file in scripts/logs/pids/*.pid; do
        if [ -f "$pid_file" ]; then
            local pid_content=$(cat "$pid_file" 2>/dev/null)
            echo "   $(basename "$pid_file"): $pid_content"
        fi
    done
else
    print_error "PID directory doesn't exist"
fi
echo

# 3. Find all celery processes
print_info "3️⃣ All Celery Processes:"
ps aux 2>/dev/null | grep -E "(celery|python.*worker)" | grep -v grep | while read line; do
    echo "   $line"
done
echo

# 4. Find specific workers
print_info "4️⃣ Specific Worker Processes:"
echo "   data_worker:"
ps aux 2>/dev/null | grep "data_worker" | grep -v grep | awk '{print "      PID: " $2 " CMD: " $11 " " $12 " " $13}'

echo "   notification_worker:"
ps aux 2>/dev/null | grep "notification_worker" | grep -v grep | awk '{print "      PID: " $2 " CMD: " $11 " " $12 " " $13}'

echo "   ml_worker:"
ps aux 2>/dev/null | grep "ml_worker" | grep -v grep | awk '{print "      PID: " $2 " CMD: " $11 " " $12 " " $13}'

echo "   general_worker:"
ps aux 2>/dev/null | grep "general_worker" | grep -v grep | awk '{print "      PID: " $2 " CMD: " $11 " " $12 " " $13}'
echo

# 5. Check log files
print_info "5️⃣ Log Files Status:"
for worker in data_worker ml_worker notification_worker general_worker; do
    local log_file="scripts/logs/${worker}_solo.log"
    if [ -f "$log_file" ]; then
        local size=$(wc -l < "$log_file" 2>/dev/null)
        echo "   $worker: $size lines"
        # Show if worker is ready
        if grep -q "ready" "$log_file" 2>/dev/null; then
            echo "      ✅ Worker shows as READY in logs"
        else
            echo "      ⚠️  Worker not ready or has errors"
        fi
    else
        echo "   $worker: No log file"
    fi
done
echo

# 6. Manual PID retrieval test
print_info "6️⃣ Manual PID Test:"
test_get_pid() {
    local worker_name=$1
    local pid_file="scripts/logs/pids/${worker_name}_solo.pid"
    
    echo "   Testing $worker_name:"
    echo "      PID file path: $pid_file"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file" 2>/dev/null)
        echo "      PID from file: $pid"
        
        if [ -n "$pid" ]; then
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "      ✅ Process $pid is running"
            else
                echo "      ❌ Process $pid is NOT running"
            fi
        else
            echo "      ❌ PID file is empty"
        fi
    else
        echo "      ❌ PID file doesn't exist"
    fi
}

test_get_pid "data_worker"
test_get_pid "ml_worker" 
test_get_pid "notification_worker"
test_get_pid "general_worker"
test_get_pid "celery_beat"
test_get_pid "celery_flower"
echo

# 7. Recommendations
print_info "7️⃣ Recommendations:"
echo "   • If PID files are missing, workers may have failed to save PIDs"
echo "   • If processes exist but PID files don't match, cleanup and restart"
echo "   • Check if workers have write permissions to PID directory"
echo

print_success "Debug completed! Check the output above for issues."