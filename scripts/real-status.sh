#!/bin/bash
# File: temp/real-status.sh
# Real-time status checker for Celery workers

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

echo -e "${PURPLE}📊 Real Celery Status Checker${NC}"
echo "=============================="
echo

# Function to check if worker is ready in logs
check_worker_ready() {
    local worker_name=$1
    local log_file="scripts/logs/${worker_name}_solo.log"
    
    if [ -f "$log_file" ]; then
        if grep -q "ready" "$log_file" 2>/dev/null; then
            echo "✅ READY"
        elif grep -q "ERROR\|CRITICAL\|Traceback" "$log_file" 2>/dev/null; then
            echo "❌ ERROR"
        elif grep -q "Connected to redis" "$log_file" 2>/dev/null; then
            echo "🔄 CONNECTING"
        else
            echo "⏳ STARTING"
        fi
    else
        echo "❓ NO_LOG"
    fi
}

# 1. Check all running processes
print_header "🔍 Running Celery Processes"
echo "============================="
echo

all_processes=$(ps aux 2>/dev/null | grep -E "(celery|python.*worker)" | grep -v grep)

if [ -n "$all_processes" ]; then
    echo "$all_processes" | while read line; do
        pid=$(echo "$line" | awk '{print $2}')
        cmd=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
        echo "   PID $pid: $cmd"
    done
else
    print_warning "No Celery processes found"
fi

echo ""

# 2. Check PID files and match with processes
print_header "📁 PID Files Status"
echo "==================="
echo

printf "%-20s %-8s %-10s %-15s %-30s\n" "Service" "PID" "Running?" "Ready?" "Log Info"
echo "-----------------------------------------------------------------------------------------"

services=("data_worker" "ml_worker" "notification_worker" "general_worker" "celery_beat" "celery_flower")

for service in "${services[@]}"; do
    pid_file="scripts/logs/pids/${service}_solo.pid"
    if [ "$service" = "celery_beat" ] || [ "$service" = "celery_flower" ]; then
        pid_file="scripts/logs/pids/${service}.pid"
    fi
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file" 2>/dev/null)
        if [ -n "$pid" ]; then
            if ps -p "$pid" > /dev/null 2>&1; then
                running="✅ YES"
                ready=$(check_worker_ready "$service")
                
                # Get recent log info
                log_file="scripts/logs/${service}_solo.log"
                if [ "$service" = "celery_beat" ] || [ "$service" = "celery_flower" ]; then
                    log_file="scripts/logs/${service}.log"
                fi
                
                if [ -f "$log_file" ]; then
                    log_info=$(tail -1 "$log_file" 2>/dev/null | cut -c1-30)
                else
                    log_info="No log file"
                fi
            else
                running="❌ NO"
                ready="❓ N/A"
                log_info="Process dead"
            fi
        else
            running="❓ EMPTY"
            ready="❓ N/A"
            log_info="Empty PID file"
        fi
    else
        pid="N/A"
        running="❓ NO_PID"
        ready="❓ N/A"
        log_info="No PID file"
    fi
    
    printf "%-20s %-8s %-10s %-15s %-30s\n" "$service" "$pid" "$running" "$ready" "$log_info"
done

echo ""

# 3. Check logs for readiness
print_header "📋 Worker Readiness Check"
echo "=========================="
echo

for worker in "data_worker" "ml_worker" "notification_worker" "general_worker"; do
    log_file="scripts/logs/${worker}_solo.log"
    print_info "🔍 $worker:"
    
    if [ -f "$log_file" ] && [ -s "$log_file" ]; then
        if grep -q "ready" "$log_file" 2>/dev/null; then
            print_success "   Worker is READY and waiting for tasks"
        elif grep -q "mingle: all alone" "$log_file" 2>/dev/null; then
            print_warning "   Worker is ALONE (first worker)"
        elif grep -q "mingle: sync complete" "$log_file" 2>/dev/null; then
            print_success "   Worker synced with other workers"
        elif grep -q "Connected to redis" "$log_file" 2>/dev/null; then
            print_info "   Worker connected to Redis, still initializing..."
        elif grep -q "ERROR\|CRITICAL" "$log_file" 2>/dev/null; then
            print_error "   Worker has errors:"
            grep "ERROR\|CRITICAL" "$log_file" | tail -1 | sed 's/^/      /'
        else
            print_warning "   Worker status unclear"
        fi
        
        # Show last log line
        last_line=$(tail -1 "$log_file" 2>/dev/null)
        echo "   📝 Latest: ${last_line:0:80}"
    else
        print_error "   No logs available"
    fi
    echo ""
done

# 4. Network check
print_header "🌐 Network Status"
echo "================="
echo

# Check Redis
print_info "Redis (6379):"
if netstat -an 2>/dev/null | grep ":6379" | grep LISTEN >/dev/null; then
    print_success "   Redis is listening on port 6379"
else
    print_warning "   Redis port 6379 not detected"
fi

# Check Flower
print_info "Flower (5555):"
if netstat -an 2>/dev/null | grep ":5555" | grep LISTEN >/dev/null; then
    print_success "   Flower web interface is available"
    print_info "   📱 Open: http://localhost:5555 (admin/cryptopredict123)"
else
    print_warning "   Flower not accessible on port 5555"
fi

echo ""

# 5. Summary and recommendations
print_header "📊 Summary & Next Steps"
echo "======================="
echo

# Count workers
total_workers=4
ready_workers=0
running_workers=0

for worker in "data_worker" "ml_worker" "notification_worker" "general_worker"; do
    pid_file="scripts/logs/pids/${worker}_solo.pid"
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file" 2>/dev/null)
        if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
            ((running_workers++))
            log_file="scripts/logs/${worker}_solo.log"
            if [ -f "$log_file" ] && grep -q "ready" "$log_file" 2>/dev/null; then
                ((ready_workers++))
            fi
        fi
    fi
done

print_info "📈 Workers Status: $running_workers/$total_workers running, $ready_workers/$total_workers ready"

if [ "$ready_workers" -eq "$total_workers" ]; then
    print_success "🎉 All workers are ready and operational!"
elif [ "$running_workers" -eq "$total_workers" ]; then
    print_warning "⏳ All workers running but some still initializing"
    print_info "💡 Wait 30-60 seconds and check again"
elif [ "$running_workers" -gt 0 ]; then
    print_warning "⚠️  Some workers failed to start"
    print_info "💡 Check logs above for error details"
else
    print_error "❌ No workers are running"
    print_info "💡 Run: ./temp/manual-start.sh"
fi

echo ""
print_info "🔧 Useful commands:"
print_info "   tail -f scripts/logs/data_worker_solo.log    # Monitor specific worker"
print_info "   ./temp/real-status.sh                       # Re-run this status check"
print_info "   http://localhost:5555                       # Flower web dashboard"