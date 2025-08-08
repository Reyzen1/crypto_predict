#!/bin/bash
# File: temp/stop-workers.sh
# Quick script to stop all Celery workers - Git Bash compatible

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="backend"
LOG_DIR="$BACKEND_DIR/logs"
PID_DIR="$LOG_DIR/pids"

# Helper functions
print_success() { echo -e "${GREEN}$1${NC}"; }
print_warning() { echo -e "${YELLOW}$1${NC}"; }
print_error() { echo -e "${RED}$1${NC}"; }
print_info() { echo -e "${CYAN}$1${NC}"; }

show_help() {
    print_info "🛑 CryptoPredict Worker Stopper"
    print_info "==============================="
    echo ""
    print_info "Usage: ./temp/stop-workers.sh [options]"
    echo ""
    print_info "Options:"
    print_info "  (none)     - Stop all workers"
    print_info "  -f, --force - Force stop (kill -9)"
    print_info "  -s, --status - Show status after stopping"
    print_info "  -h, --help  - Show this help"
    echo ""
    print_info "Examples:"
    print_info "  ./temp/stop-workers.sh         # Normal stop"
    print_info "  ./temp/stop-workers.sh --force # Force stop"
    print_info "  ./temp/stop-workers.sh -s      # Stop and show status"
    exit 0
}

# Check if we're in the right directory
check_environment() {
    if [ ! -d "$BACKEND_DIR" ]; then
        print_error "❌ Backend directory not found. Run from project root."
        exit 1
    fi
}

# Clean stale PID files
clean_stale_pids() {
    local silent="$1"
    
    if [ "$silent" != "silent" ]; then
        print_info "🧹 Cleaning stale PID files..."
    fi
    
    # Clean our custom PID files
    if [ -d "$PID_DIR" ]; then
        for pid_file in "$PID_DIR"/celery_*.pid; do
            if [ -f "$pid_file" ]; then
                local pid=$(cat "$pid_file" 2>/dev/null || echo "")
                if [ -n "$pid" ] && ! ps -p "$pid" > /dev/null 2>&1; then
                    if [ "$silent" != "silent" ]; then
                        print_warning "Removing stale PID file: $pid_file"
                    fi
                    rm -f "$pid_file"
                fi
            fi
        done
    fi
    
    # Clean Celery Beat's own PID file if process is not running
    local celerybeat_pid_file="$BACKEND_DIR/logs/pids/celerybeat.pid"
    if [ -f "$celerybeat_pid_file" ]; then
        local beat_pid=$(cat "$celerybeat_pid_file" 2>/dev/null || echo "")
        if [ -n "$beat_pid" ] && ! ps -p "$beat_pid" > /dev/null 2>&1; then
            if [ "$silent" != "silent" ]; then
                print_warning "Removing stale Celery Beat PID file: $celerybeat_pid_file"
            fi
            rm -f "$celerybeat_pid_file"
        fi
    fi
}

# Stop all workers
stop_workers() {
    local force_stop="$1"
    local signal="TERM"
    local signal_name="SIGTERM"
    
    if [ "$force_stop" = "force" ]; then
        signal="KILL"
        signal_name="SIGKILL"
        print_warning "🛑 Force Stopping CryptoPredict Workers"
    else
        print_warning "🛑 Stopping CryptoPredict Workers"
    fi
    print_warning "================================="
    
    local workers_found=false
    local workers_stopped=0
    
    # Stop processes using PID files with celery_ prefix
    if [ -d "$PID_DIR" ]; then
        for pid_file in "$PID_DIR"/celery_*.pid; do
            if [ -f "$pid_file" ]; then
                local pid=$(cat "$pid_file" 2>/dev/null || echo "")
                local name=$(basename "$pid_file" .pid)
                name=${name#celery_}  # Remove celery_ prefix for display
                
                if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
                    workers_found=true
                    print_warning "Stopping $name (PID: $pid) with $signal_name..."
                    
                    if [ "$force_stop" = "force" ]; then
                        kill -9 "$pid" 2>/dev/null || true
                    else
                        kill "$pid" 2>/dev/null || true
                        
                        # Wait for graceful shutdown
                        for i in {1..5}; do
                            if ! ps -p "$pid" > /dev/null 2>&1; then
                                break
                            fi
                            sleep 1
                        done
                        
                        # Force kill if still running
                        if ps -p "$pid" > /dev/null 2>&1; then
                            print_warning "  Force killing $name..."
                            kill -9 "$pid" 2>/dev/null || true
                        fi
                    fi
                    
                    # Verify it's stopped
                    sleep 1
                    if ! ps -p "$pid" > /dev/null 2>&1; then
                        print_success "  ✅ $name stopped"
                        workers_stopped=$((workers_stopped + 1))
                    else
                        print_error "  ❌ $name still running"
                    fi
                fi
                rm -f "$pid_file"
            fi
        done
    fi
    
    # Also stop Celery Beat using its own PID file
    local celerybeat_pid_file="$BACKEND_DIR/logs/pids/celerybeat.pid"
    if [ -f "$celerybeat_pid_file" ]; then
        local beat_pid=$(cat "$celerybeat_pid_file" 2>/dev/null || echo "")
        if [ -n "$beat_pid" ] && ps -p "$beat_pid" > /dev/null 2>&1; then
            workers_found=true
            print_warning "Stopping Celery Beat (PID: $beat_pid) with $signal_name..."
            
            if [ "$force_stop" = "force" ]; then
                kill -9 "$beat_pid" 2>/dev/null || true
            else
                kill "$beat_pid" 2>/dev/null || true
                sleep 2
                if ps -p "$beat_pid" > /dev/null 2>&1; then
                    kill -9 "$beat_pid" 2>/dev/null || true
                fi
            fi
            
            sleep 1
            if ! ps -p "$beat_pid" > /dev/null 2>&1; then
                print_success "  ✅ Celery Beat stopped"
                workers_stopped=$((workers_stopped + 1))
            else
                print_error "  ❌ Celery Beat still running"
            fi
        fi
        rm -f "$celerybeat_pid_file"
    fi
    
    # Fallback: kill any remaining celery processes
    local remaining_processes=$(pgrep -f "celery.*app.tasks.celery_app" 2>/dev/null || true)
    if [ -n "$remaining_processes" ]; then
        workers_found=true
        print_warning "Killing remaining Celery processes..."
        if [ "$force_stop" = "force" ]; then
            pkill -9 -f "celery.*app.tasks.celery_app" 2>/dev/null || true
        else
            pkill -f "celery.*app.tasks.celery_app" 2>/dev/null || true
            sleep 2
            pkill -9 -f "celery.*app.tasks.celery_app" 2>/dev/null || true
        fi
        print_warning "  Fallback cleanup completed"
    fi
    
    # Clean stale files after stopping
    clean_stale_pids silent
    
    echo ""
    if [ "$workers_found" = true ]; then
        if [ "$workers_stopped" -gt 0 ]; then
            print_success "✅ Successfully stopped $workers_stopped worker(s)"
        else
            print_warning "⚠️  Some workers may still be running"
        fi
    else
        print_info "ℹ️  No CryptoPredict workers were running"
    fi
}

# Show worker status
show_status() {
    print_info "📊 Worker Status After Stop"
    print_info "============================"
    
    local any_running=false
    
    # Check our managed workers
    if [ -d "$PID_DIR" ]; then
        for pid_file in "$PID_DIR"/celery_*.pid; do
            if [ -f "$pid_file" ]; then
                local pid=$(cat "$pid_file" 2>/dev/null || echo "")
                local name=$(basename "$pid_file" .pid)
                name=${name#celery_}  # Remove celery_ prefix for display
                
                if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
                    print_error "  $name: ❌ Still running (PID: $pid)"
                    any_running=true
                else
                    print_success "  $name: ✅ Stopped"
                fi
            fi
        done
    fi
    
    # Also check Celery Beat's own PID file
    local celerybeat_pid_file="$BACKEND_DIR/logs/pids/celerybeat.pid"
    if [ -f "$celerybeat_pid_file" ]; then
        local beat_pid=$(cat "$celerybeat_pid_file" 2>/dev/null || echo "")
        if [ -n "$beat_pid" ] && ps -p "$beat_pid" > /dev/null 2>&1; then
            print_error "  beat (system): ❌ Still running (PID: $beat_pid)"
            any_running=true
        fi
    fi
    
    # Check for any remaining Celery processes
    local remaining=$(pgrep -f "celery.*app.tasks.celery_app" 2>/dev/null | wc -l)
    if [ "$remaining" -gt 0 ]; then
        print_error "  ⚠️  $remaining remaining Celery process(es) found"
        print_info "     Use --force to force kill them"
        any_running=true
    fi
    
    if [ "$any_running" = false ]; then
        print_success "✅ All CryptoPredict workers stopped successfully"
    else
        echo ""
        print_warning "⚠️  Some workers may still be running"
        print_info "💡 Try: ./temp/stop-workers.sh --force"
    fi
}

# Parse arguments
FORCE_STOP=false
SHOW_STATUS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE_STOP=true
            shift
            ;;
        -s|--status)
            SHOW_STATUS=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            print_error "❌ Unknown option: $1"
            print_info "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Main execution
check_environment

if [ "$FORCE_STOP" = true ]; then
    stop_workers force
else
    stop_workers normal
fi

if [ "$SHOW_STATUS" = true ]; then
    echo ""
    show_status
fi

echo ""
print_success "🏁 Stop operation completed"
print_info "💡 Use './temp/start-workers.sh' to restart workers"