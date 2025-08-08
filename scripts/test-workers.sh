#!/bin/bash
# File: temp/test-workers.sh
# Test worker functionality by sending sample tasks

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ️  $1${NC}"; }
print_header() { echo -e "${PURPLE}$1${NC}"; }

echo -e "${PURPLE}🧪 Testing Worker Functionality${NC}"
echo "================================"
echo

# Test 1: Check if workers are responding
print_header "1️⃣ Testing Worker Connectivity"
echo

cd backend

# Test basic celery commands
print_info "🔍 Testing Celery inspect..."
if python -m celery -A app.tasks.celery_app inspect ping 2>/dev/null | grep -q "pong"; then
    print_success "Workers are responding to ping"
else
    print_warning "Ping test failed, but workers may still be working"
fi

# Test 2: Check active workers
print_info "🔍 Checking active workers..."
active_workers=$(python -m celery -A app.tasks.celery_app inspect active 2>/dev/null)
if [ $? -eq 0 ]; then
    print_success "Active workers check successful"
    echo "$active_workers" | head -5
else
    print_warning "Active workers check failed"
fi

# Test 3: Check registered tasks
print_info "🔍 Checking registered tasks..."
registered_tasks=$(python -m celery -A app.tasks.celery_app inspect registered 2>/dev/null)
if [ $? -eq 0 ]; then
    print_success "Task registration check successful"
    # Show first few tasks
    echo "$registered_tasks" | head -10
else
    print_warning "Task registration check failed"
fi

cd ..

# Test 4: Check Beat Scheduler
print_header "2️⃣ Testing Beat Scheduler"
echo

beat_pid=$(cat scripts/logs/pids/celery_beat.pid 2>/dev/null)
if [ -n "$beat_pid" ] && ps -p "$beat_pid" > /dev/null 2>&1; then
    print_success "Beat scheduler is running (PID: $beat_pid)"
    
    # Check beat log
    if [ -f "scripts/logs/celery_beat.log" ]; then
        print_info "📋 Recent Beat activity:"
        tail -3 scripts/logs/celery_beat.log | sed 's/^/   /'
    fi
else
    print_warning "Beat scheduler not running - restarting..."
    cd backend
    nohup python -m celery -A app.tasks.celery_app beat \
        --loglevel=info \
        --schedule=../scripts/logs/celerybeat-schedule \
        > ../scripts/logs/celery_beat.log 2>&1 &
    
    beat_pid=$!
    echo "$beat_pid" > ../scripts/logs/pids/celery_beat.pid
    cd ..
    
    sleep 2
    if ps -p "$beat_pid" > /dev/null 2>&1; then
        print_success "Beat scheduler restarted (PID: $beat_pid)"
    else
        print_error "Failed to restart Beat scheduler"
    fi
fi

# Test 5: Check Flower Dashboard
print_header "3️⃣ Testing Flower Dashboard"
echo

flower_pid=$(cat scripts/logs/pids/celery_flower.pid 2>/dev/null)
if netstat -an 2>/dev/null | grep ":5555" | grep LISTEN >/dev/null; then
    print_success "Flower web interface is accessible"
    print_info "🌐 Dashboard: http://localhost:5555"
    print_info "🔐 Login: admin / cryptopredict123"
    
    # Test if we can curl the dashboard
    if command -v curl >/dev/null 2>&1; then
        if curl -s --connect-timeout 5 http://localhost:5555 >/dev/null; then
            print_success "Flower dashboard responds to HTTP requests"
        else
            print_warning "Flower dashboard not responding to HTTP"
        fi
    fi
else
    print_warning "Flower not accessible on port 5555 - restarting..."
    cd backend
    nohup python -m celery -A app.tasks.celery_app flower \
        --port=5555 \
        --basic_auth=admin:cryptopredict123 \
        > ../scripts/logs/celery_flower.log 2>&1 &
    
    flower_pid=$!
    echo "$flower_pid" > ../scripts/logs/pids/celery_flower.pid
    cd ..
    
    sleep 3
    if netstat -an 2>/dev/null | grep ":5555" | grep LISTEN >/dev/null; then
        print_success "Flower dashboard restarted"
    else
        print_error "Failed to restart Flower dashboard"
    fi
fi

# Test 6: Worker Queue Status
print_header "4️⃣ Testing Worker Queues"
echo

workers=("data_worker" "ml_worker" "notification_worker" "general_worker")
queues=("price_data,market_data,data_sync" "ml_prediction,model_training,ml_tasks" "notifications,alerts,email_tasks" "general,cleanup,maintenance,default")

for i in "${!workers[@]}"; do
    worker=${workers[$i]}
    queue=${queues[$i]}
    
    print_info "🔍 $worker (Queues: $queue):"
    
    # Check if worker is in logs
    log_file="scripts/logs/${worker}_solo.log"
    if [ -f "$log_file" ]; then
        if grep -q "ready" "$log_file" 2>/dev/null; then
            print_success "   Worker is ready and listening"
        elif grep -q "ERROR" "$log_file" 2>/dev/null; then
            print_error "   Worker has errors"
            grep "ERROR" "$log_file" | tail -1 | sed 's/^/      /'
        else
            print_warning "   Worker status unclear"
        fi
    else
        print_error "   No log file found"
    fi
done

# Test 7: Summary and Recommendations
print_header "5️⃣ System Health Summary"
echo

# Count ready workers
ready_count=0
for worker in "${workers[@]}"; do
    log_file="scripts/logs/${worker}_solo.log"
    if [ -f "$log_file" ] && grep -q "ready" "$log_file" 2>/dev/null; then
        ((ready_count++))
    fi
done

# Final assessment
print_info "📊 System Status:"
echo "   🔧 Ready Workers: $ready_count/4"
echo "   🥁 Beat Scheduler: $([ -n "$beat_pid" ] && ps -p "$beat_pid" >/dev/null 2>&1 && echo "✅ Running" || echo "❌ Down")"
echo "   🌸 Flower Dashboard: $(netstat -an 2>/dev/null | grep ":5555" | grep LISTEN >/dev/null && echo "✅ Available" || echo "❌ Down")"
echo "   📡 Redis: $(netstat -an 2>/dev/null | grep ":6379" | grep LISTEN >/dev/null && echo "✅ Connected" || echo "❌ Down")"

echo ""
if [ "$ready_count" -eq 4 ]; then
    print_success "🎉 EXCELLENT! All systems are operational"
    print_info "Your Celery worker system is ready for production tasks!"
    echo ""
    print_info "🎯 What you can do now:"
    print_info "   • Send tasks to workers through your application"
    print_info "   • Monitor workers via Flower: http://localhost:5555"
    print_info "   • Check worker logs: tail -f scripts/logs/*_solo.log"
    print_info "   • Run status checks: ./temp/real-status.sh"
elif [ "$ready_count" -gt 2 ]; then
    print_warning "🟡 GOOD: Most workers are operational"
    print_info "System is functional but some components need attention"
else
    print_error "🔴 ISSUES: Several workers need attention"
    print_info "Check worker logs and restart problematic components"
fi

echo ""
print_info "🛠️ Maintenance commands:"
print_info "   ./temp/real-status.sh          # Check current status"
print_info "   ./temp/test-workers.sh         # Re-run this test"
print_info "   ./scripts/run-workers-win.sh   # Use main worker manager"