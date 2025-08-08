#!/bin/bash
# File: temp/simple-beat.sh
# Simple Beat Scheduler without PID file conflicts

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

echo -e "${PURPLE}🥁 Simple Beat Scheduler${NC}"
echo "========================="
echo

# Complete cleanup
print_info "🧹 Complete cleanup..."
pkill -f "celery.*beat" 2>/dev/null || true
rm -f scripts/logs/pids/celery_beat.pid
rm -f scripts/logs/celerybeat-schedule*
sleep 2

# Clear log
> scripts/logs/celery_beat.log

print_info "🎯 Starting Beat without PID conflicts..."

cd backend

# Start Beat without pidfile to avoid conflicts
nohup python -m celery -A app.tasks.celery_app beat \
    --loglevel=info \
    --max-interval=60 \
    > ../scripts/logs/celery_beat.log 2>&1 &

beat_pid=$!

cd ..

# Save PID manually
echo "$beat_pid" > scripts/logs/pids/celery_beat.pid

print_info "⏳ Beat PID: $beat_pid - Monitoring..."

# Wait and verify
sleep 5

if ps -p $beat_pid > /dev/null 2>&1; then
    print_success "🎉 Beat Scheduler started successfully!"
    
    # Check log for activity
    if [ -f "scripts/logs/celery_beat.log" ]; then
        print_info "📋 Beat activity:"
        tail -3 scripts/logs/celery_beat.log | sed 's/^/   /'
    fi
else
    print_error "❌ Beat failed to start"
    if [ -f "scripts/logs/celery_beat.log" ]; then
        print_error "Error details:"
        cat scripts/logs/celery_beat.log | sed 's/^/   /'
    fi
fi

echo ""
print_info "💡 Beat Status: PID $beat_pid"
print_info "📋 Monitor: tail -f scripts/logs/celery_beat.log"