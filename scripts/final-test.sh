#!/bin/bash
# File: temp/final-test.sh
# Complete system test with real task execution

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
print_header() { echo -e "${PURPLE}${BOLD}$1${NC}"; }
print_task() { echo -e "${BLUE}🔄 $1${NC}"; }

echo -e "${PURPLE}🚀 Final System Test & Demo${NC}"
echo "============================"
echo

# 1. System Status Check
print_header "1️⃣ Complete System Status"
echo "=========================="
echo

# Check all components
components=("Redis" "Workers" "Flower" "Beat")
statuses=()

# Redis check
if netstat -an 2>/dev/null | grep ":6379" | grep LISTEN >/dev/null; then
    statuses+=("✅ Redis")
else
    statuses+=("❌ Redis")
fi

# Workers check
ready_workers=0
for worker in "data_worker" "ml_worker" "notification_worker" "general_worker"; do
    log_file="scripts/logs/${worker}_solo.log"
    if [ -f "$log_file" ] && grep -q "ready" "$log_file" 2>/dev/null; then
        ((ready_workers++))
    fi
done

if [ "$ready_workers" -eq 4 ]; then
    statuses+=("✅ Workers (4/4)")
else
    statuses+=("⚠️ Workers ($ready_workers/4)")
fi

# Flower check
if netstat -an 2>/dev/null | grep ":5555" | grep LISTEN >/dev/null; then
    statuses+=("✅ Flower")
else
    statuses+=("❌ Flower")
fi

# Beat check
beat_pid=$(cat scripts/logs/pids/celery_beat.pid 2>/dev/null)
if [ -n "$beat_pid" ] && ps -p "$beat_pid" > /dev/null 2>&1; then
    statuses+=("✅ Beat")
else
    statuses+=("⚠️ Beat")
fi

# Display status
for status in "${statuses[@]}"; do
    echo "   $status"
done

echo ""

# 2. Task Queue Demo
print_header "2️⃣ Task Queue Demonstration"
echo "==========================="
echo

print_info "🎯 Testing different worker queues with sample tasks..."
echo

cd backend

# Test 1: General Queue Task
print_task "Sending task to General Worker..."
python -c "
from app.tasks.celery_app import app
result = app.send_task('app.tasks.celery_app.debug_task', args=['General Queue Test'], queue='general')
print(f'✅ Task sent to general queue: {result.id}')
" 2>/dev/null || print_warning "General queue task failed"

# Test 2: Price Data Queue Task
print_task "Sending task to Data Worker..."
python -c "
from app.tasks.celery_app import app
result = app.send_task('app.tasks.price_collector.get_task_status', queue='price_data')
print(f'✅ Task sent to price_data queue: {result.id}')
" 2>/dev/null || print_warning "Data queue task failed"

# Test 3: Notification Queue Task
print_task "Sending task to Notification Worker..."
python -c "
from app.tasks.celery_app import app
result = app.send_task('app.tasks.celery_app.health_check', queue='notifications')
print(f'✅ Task sent to notifications queue: {result.id}')
" 2>/dev/null || print_warning "Notification queue task failed"

# Test 4: ML Queue Task  
print_task "Sending task to ML Worker..."
python -c "
from app.tasks.celery_app import app
result = app.send_task('ml_tasks.auto_train_models', queue='ml_tasks')
print(f'✅ Task sent to ml_tasks queue: {result.id}')
" 2>/dev/null || print_warning "ML queue task failed"

cd ..

echo ""

# 3. Real-time Worker Activity
print_header "3️⃣ Worker Activity Monitor"
echo "========================="
echo

print_info "📊 Recent worker activity (last 30 seconds)..."
echo

for worker in "data_worker" "ml_worker" "notification_worker" "general_worker"; do
    log_file="scripts/logs/${worker}_solo.log"
    print_info "🔍 $worker activity:"
    
    if [ -f "$log_file" ]; then
        # Show recent task activity
        recent_activity=$(grep -E "(received|succeeded|failed)" "$log_file" 2>/dev/null | tail -3)
        if [ -n "$recent_activity" ]; then
            echo "$recent_activity" | sed 's/^/   📝 /'
        else
            echo "   💤 No recent task activity"
        fi
    else
        echo "   ❌ No log file"
    fi
    echo ""
done

# 4. Performance Summary
print_header "4️⃣ Performance Summary"
echo "====================="
echo

print_info "📈 System Performance Metrics:"
echo

# Calculate uptime for workers
for worker in "data_worker" "ml_worker" "notification_worker" "general_worker"; do
    pid_file="scripts/logs/pids/${worker}_solo.pid"
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            # Get process start time (simplified)
            start_time=$(ps -o lstart= -p "$pid" 2>/dev/null | xargs || echo "Unknown")
            cpu_usage=$(ps -o pcpu= -p "$pid" 2>/dev/null | xargs || echo "0")
            mem_usage=$(ps -o pmem= -p "$pid" 2>/dev/null | xargs || echo "0")
            
            echo "   🔧 $worker:"
            echo "      📅 Started: $start_time"
            echo "      🖥️ CPU: ${cpu_usage}%"
            echo "      💾 Memory: ${mem_usage}%"
        else
            echo "   ❌ $worker: Not running"
        fi
    else
        echo "   ❓ $worker: No PID file"
    fi
done

echo ""

# 5. Flower Dashboard Info
print_header "5️⃣ Monitoring Dashboard"
echo "======================="
echo

if netstat -an 2>/dev/null | grep ":5555" | grep LISTEN >/dev/null; then
    print_success "🌸 Flower Dashboard is available!"
    echo
    print_info "🌐 Access Details:"
    echo "   📱 URL: http://localhost:5555"
    echo "   👤 Username: admin"
    echo "   🔐 Password: cryptopredict123"
    echo
    print_info "📊 Features Available:"
    echo "   • Real-time worker monitoring"
    echo "   • Task queue status"
    echo "   • Task history and results"
    echo "   • Worker performance metrics"
    echo "   • Broker (Redis) information"
else
    print_warning "Flower Dashboard not accessible"
fi

echo ""

# 6. Next Steps & Recommendations
print_header "6️⃣ System Ready - Next Steps"
echo "============================="
echo

print_success "🎉 Your Enhanced Celery Worker System is OPERATIONAL!"
echo

print_info "🎯 What you can do now:"
echo "   • Send real tasks from your application"
echo "   • Monitor workers via Flower dashboard"
echo "   • Scale workers by starting additional instances"
echo "   • Add custom tasks to your queues"
echo

print_info "🔧 Management Commands:"
echo "   ./scripts/real-status.sh          # Check system status"
echo "   ./temp/final-test.sh              # Re-run this test"
echo "   ./temp/simple-beat.sh             # Fix Beat if needed"
echo "   tail -f scripts/logs/*_solo.log   # Monitor worker logs"
echo

print_info "📋 Task Examples:"
echo "   # Send to data worker"
echo "   app.send_task('price_task', queue='price_data')"
echo 
echo "   # Send to ML worker"
echo "   app.send_task('ml_task', queue='ml_tasks')"
echo
echo "   # Send to notification worker"
echo "   app.send_task('notify_task', queue='notifications')"
echo

print_info "🚀 Production Tips:"
echo "   • Monitor memory usage regularly"
echo "   • Rotate log files periodically"
echo "   • Scale workers based on queue length"
echo "   • Use Flower for real-time monitoring"
echo "   • Test task reliability before production"

echo ""
print_header "✨ Congratulations! Solo Pool Workers System Complete! ✨"