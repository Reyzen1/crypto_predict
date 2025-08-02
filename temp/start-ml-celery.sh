#!/bin/bash
# File: temp/start-ml-celery.sh
# Start ML-focused Celery workers for CryptoPredict - Based on existing start-celery.sh pattern

set -e

echo "🤖 Starting CryptoPredict ML Celery Services..."
echo "================================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
WORKERS=2
LOG_LEVEL="info"
BACKEND_DIR="backend"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --workers)
            WORKERS="$2"
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
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --workers NUMBER      Number of worker processes (default: 2)"
            echo "  --log-level LEVEL     Log level: debug, info, warning, error (default: info)"
            echo "  --backend-dir PATH    Backend directory path (default: backend)"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Function to kill processes on a port
kill_port() {
    if port_in_use $1; then
        echo -e "${YELLOW}Killing processes on port $1...${NC}"
        lsof -ti :$1 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

# Check if we're in the right directory
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}Error: Backend directory '$BACKEND_DIR' not found!${NC}"
    echo "Please run this script from the project root directory or specify correct --backend-dir"
    exit 1
fi

# Change to backend directory
cd "$BACKEND_DIR"

# Check for required files
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found in backend directory!${NC}"
    exit 1
fi

# Check Python and dependencies
echo -e "${BLUE}🔍 Checking dependencies...${NC}"

if ! command_exists python; then
    echo -e "${RED}Error: Python not found! Please install Python 3.11+${NC}"
    exit 1
fi

if ! command_exists pip; then
    echo -e "${RED}Error: pip not found! Please install pip${NC}"
    exit 1
fi

# Install/update requirements
echo -e "${BLUE}📦 Installing/updating requirements...${NC}"
pip install -r requirements.txt --quiet

# Check if Celery is installed
if ! python -c "import celery" 2>/dev/null; then
    echo -e "${RED}Error: Celery not installed! Installing...${NC}"
    pip install celery[redis] --quiet
fi

# Check Redis connection
echo -e "${BLUE}🔗 Checking Redis connection...${NC}"
python -c "
import redis
import sys
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    print('Please ensure Redis is running: redis-server')
    sys.exit(1)
" || exit 1

# Check database connection
echo -e "${BLUE}🗄️  Checking database connection...${NC}"
python -c "
from app.core.database import engine
try:
    with engine.connect() as conn:
        conn.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
" || exit 1

# Kill existing Celery processes on standard ports
echo -e "${BLUE}🧹 Cleaning up existing processes...${NC}"
kill_port 5555  # Flower
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true
sleep 2

# Create log directory
mkdir -p logs

# Function to start a service and check if it started successfully
start_service() {
    local service_name="$1"
    local command="$2"
    local log_file="$3"
    local check_string="$4"
    
    echo -e "${BLUE}🚀 Starting $service_name...${NC}"
    
    # Start the service in background
    eval "$command" > "$log_file" 2>&1 &
    local pid=$!
    
    # Wait a moment for startup
    sleep 3
    
    # Check if process is still running
    if ! kill -0 $pid 2>/dev/null; then
        echo -e "${RED}❌ Failed to start $service_name${NC}"
        echo "Check log file: $log_file"
        return 1
    fi
    
    # Check for success string in log
    if [ -n "$check_string" ]; then
        if grep -q "$check_string" "$log_file" 2>/dev/null; then
            echo -e "${GREEN}✅ $service_name started successfully (PID: $pid)${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name started but waiting for initialization...${NC}"
        fi
    else
        echo -e "${GREEN}✅ $service_name started (PID: $pid)${NC}"
    fi
    
    return 0
}

# Start ML-focused Celery worker
echo -e "${YELLOW}🤖 Starting ML Celery Worker...${NC}"
start_service \
    "ML Celery Worker" \
    "celery -A app.tasks.celery_app worker --loglevel=$LOG_LEVEL --concurrency=$WORKERS --queues=ml_tasks --hostname=ml_worker@%h" \
    "logs/celery_ml_worker.log" \
    "ready"

# Start general Celery worker for other tasks
echo -e "${YELLOW}⚙️  Starting General Celery Worker...${NC}"
start_service \
    "General Celery Worker" \
    "celery -A app.tasks.celery_app worker --loglevel=$LOG_LEVEL --concurrency=$WORKERS --queues=price_data,default --hostname=general_worker@%h" \
    "logs/celery_general_worker.log" \
    "ready"

# Start Celery Beat scheduler
echo -e "${YELLOW}⏰ Starting Celery Beat Scheduler...${NC}"
start_service \
    "Celery Beat" \
    "celery -A app.tasks.celery_app beat --loglevel=$LOG_LEVEL --schedule=celerybeat-schedule" \
    "logs/celery_beat.log" \
    "Scheduler"

# Start Flower monitoring (optional)
if command_exists flower || python -c "import flower" 2>/dev/null; then
    echo -e "${YELLOW}🌸 Starting Flower Monitoring...${NC}"
    start_service \
        "Flower Monitor" \
        "celery -A app.tasks.celery_app flower --port=5555 --basic_auth=admin:cryptopredict123" \
        "logs/flower.log" \
        ""
else
    echo -e "${YELLOW}⚠️  Flower not installed, skipping monitoring dashboard${NC}"
    echo -e "${BLUE}Install with: pip install flower${NC}"
fi

echo ""
echo -e "${GREEN}🎉 ML Celery Services Started Successfully!${NC}"
echo "================================================"

# Display service information
echo -e "${BLUE}📋 Service Information:${NC}"
echo "• ML Worker: Processing ML tasks (training, predictions, evaluation)"
echo "• General Worker: Processing data collection and other tasks"
echo "• Beat Scheduler: Running periodic tasks"
if command_exists flower || python -c "import flower" 2>/dev/null; then
    echo "• Flower Monitor: http://localhost:5555 (admin:cryptopredict123)"
fi

echo ""
echo -e "${BLUE}📊 Queue Information:${NC}"
echo "• ml_tasks: ML training, predictions, performance evaluation"
echo "• price_data: Price synchronization and data collection"
echo "• default: General background tasks"

echo ""
echo -e "${BLUE}📝 Log Files:${NC}"
echo "• ML Worker: logs/celery_ml_worker.log"
echo "• General Worker: logs/celery_general_worker.log"
echo "• Beat Scheduler: logs/celery_beat.log"
if command_exists flower || python -c "import flower" 2>/dev/null; then
    echo "• Flower Monitor: logs/flower.log"
fi

echo ""
echo -e "${BLUE}🔧 Management Commands:${NC}"
echo "• Stop all: pkill -f celery"
echo "• Stop workers: pkill -f 'celery.*worker'"
echo "• Stop beat: pkill -f 'celery.*beat'"
echo "• View logs: tail -f logs/celery_ml_worker.log"

echo ""
echo -e "${BLUE}🚀 ML Task Examples:${NC}"
echo "• Auto train models: python -c \"from app.tasks.ml_tasks import start_auto_training; print(start_auto_training())\""
echo "• Generate predictions: python -c \"from app.tasks.ml_tasks import start_prediction_generation; print(start_prediction_generation())\""
echo "• Evaluate performance: python -c \"from app.tasks.ml_tasks import start_performance_evaluation; print(start_performance_evaluation())\""

echo ""
echo -e "${GREEN}✨ Ready for ML operations!${NC}"

# Monitor services for a few seconds
echo -e "${BLUE}🔍 Monitoring services for 10 seconds...${NC}"
sleep 10

# Check if services are still running
echo -e "${BLUE}📊 Service Status Check:${NC}"
if pgrep -f "celery.*worker.*ml_tasks" > /dev/null; then
    echo -e "${GREEN}✅ ML Worker: Running${NC}"
else
    echo -e "${RED}❌ ML Worker: Not running${NC}"
fi

if pgrep -f "celery.*worker.*price_data" > /dev/null; then
    echo -e "${GREEN}✅ General Worker: Running${NC}"
else
    echo -e "${RED}❌ General Worker: Not running${NC}"
fi

if pgrep -f "celery.*beat" > /dev/null; then
    echo -e "${GREEN}✅ Beat Scheduler: Running${NC}"
else
    echo -e "${RED}❌ Beat Scheduler: Not running${NC}"
fi

if port_in_use 5555; then
    echo -e "${GREEN}✅ Flower Monitor: Running on port 5555${NC}"
else
    echo -e "${YELLOW}⚠️  Flower Monitor: Not running${NC}"
fi

echo ""
echo -e "${GREEN}🎯 ML Celery setup complete! Services are ready for AI operations.${NC}"