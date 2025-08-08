#!/bin/bash
# File: temp/cleanup-workers.sh
# Emergency cleanup script for Celery workers

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

echo -e "${CYAN}🧹 Emergency Celery Cleanup Script${NC}"
echo "=================================="
echo

# 1. Kill all celery processes
print_info "1️⃣ Killing all Celery processes..."
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true  
pkill -f "celery.*flower" 2>/dev/null || true
pkill -f "python.*celery" 2>/dev/null || true
sleep 2

# Force kill if needed
pkill -9 -f "celery" 2>/dev/null || true
print_success "All Celery processes terminated"

# 2. Remove all PID files
print_info "2️⃣ Cleaning PID files..."
rm -f scripts/logs/pids/*.pid 2>/dev/null || true
print_success "PID files cleaned"

# 3. Clear problematic log entries
print_info "3️⃣ Clearing problematic logs..."
for log_file in scripts/logs/*_solo.log; do
    if [ -f "$log_file" ]; then
        > "$log_file"  # Clear the file
    fi
done
print_success "Log files cleared"

# 4. Check for remaining processes
print_info "4️⃣ Checking for remaining processes..."
remaining=$(ps aux | grep -E 'celery|python.*worker' | grep -v grep | wc -l)
if [ "$remaining" -gt 0 ]; then
    print_warning "Found $remaining remaining processes:"
    ps aux | grep -E 'celery|python.*worker' | grep -v grep
else
    print_success "No remaining processes found"
fi

# 5. Verify cleanup
echo
print_info "🔍 Cleanup verification:"
echo "  • PID files: $(ls scripts/logs/pids/*.pid 2>/dev/null | wc -l) remaining"
echo "  • Active processes: $(ps aux | grep celery | grep -v grep | wc -l)"
echo "  • Port 5555 (Flower): $(lsof -ti:5555 2>/dev/null | wc -l) processes"

echo
print_success "🎉 Cleanup completed! You can now start workers safely:"
print_info "  ./scripts/run-workers.sh start"