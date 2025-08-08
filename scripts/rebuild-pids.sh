#!/bin/bash
# File: temp/rebuild-pids.sh
# Rebuild PID files from running processes

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

echo -e "${CYAN}🔧 Rebuild PID Files${NC}"
echo "===================="
echo

# Ensure PID directory exists
mkdir -p scripts/logs/pids

rebuild_count=0

# Function to find and rebuild PID file
rebuild_worker_pid() {
    local worker_name=$1
    local pattern=$2
    local pid_file="scripts/logs/pids/${worker_name}_solo.pid"
    
    print_info "🔍 Looking for $worker_name..."
    
    # Find process PID
    local pid=$(ps aux 2>/dev/null | grep "$pattern" | grep -v grep | awk '{print $2}' | head -1)
    
    if [ -n "$pid" ]; then
        echo "$pid" > "$pid_file"
        print_success "Rebuilt PID file for $worker_name (PID: $pid)"
        ((rebuild_count++))
    else
        print_warning "No running process found for $worker_name"
        rm -f "$pid_file" 2>/dev/null
    fi
}

# Rebuild PID files for each worker
rebuild_worker_pid "data_worker" "celery.*worker.*data_worker"
rebuild_worker_pid "ml_worker" "celery.*worker.*ml_worker"
rebuild_worker_pid "notification_worker" "celery.*worker.*notification_worker"
rebuild_worker_pid "general_worker" "celery.*worker.*general_worker"

# System services
rebuild_worker_pid "celery_beat" "celery.*beat"
rebuild_worker_pid "celery_flower" "celery.*flower"

echo
print_info "📊 Summary: Rebuilt $rebuild_count PID files"

# Verify by showing current status
echo
print_info "🔍 Current PID files:"
for pid_file in scripts/logs/pids/*.pid; do
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        local name=$(basename "$pid_file" .pid)
        echo "   $name: $pid"
    fi
done

echo
print_success "PID rebuild completed! Now try: ./scripts/run-workers-win.sh status"