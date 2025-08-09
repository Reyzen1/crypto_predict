#!/bin/bash
# File: temp/install-deps.sh
# Install missing Celery dependencies

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

echo -e "${CYAN}📦 Installing Missing Celery Dependencies${NC}"
echo "=========================================="
echo

# Check if in virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    print_success "Virtual environment detected: $(basename $VIRTUAL_ENV)"
else
    print_warning "No virtual environment detected"
    print_info "Consider activating venv: source venv/bin/activate"
fi

echo

# Install flower
print_info "1️⃣ Installing Flower..."
if pip install flower; then
    print_success "Flower installed successfully"
else
    print_error "Failed to install Flower"
    exit 1
fi

# Install other useful Celery packages
print_info "2️⃣ Installing additional Celery tools..."

packages=(
    "celery[redis]"
    "redis"
    "eventlet"
)

for package in "${packages[@]}"; do
    print_info "Installing $package..."
    if pip install "$package" --upgrade; then
        print_success "$package installed"
    else
        print_warning "$package installation failed"
    fi
done

# Verify installations
echo
print_info "3️⃣ Verifying installations..."

# Test flower
if python -c "import flower; print('Flower version:', flower.__version__)" 2>/dev/null; then
    print_success "Flower import successful"
else
    print_error "Flower import failed"
fi

# Test celery flower command
cd backend 2>/dev/null || { print_error "Cannot access backend directory"; exit 1; }

if python -m celery flower --help >/dev/null 2>&1; then
    print_success "Celery flower command available"
else
    print_error "Celery flower command failed"
fi

cd - >/dev/null

# Test redis
if python -c "import redis; print('Redis version:', redis.__version__)" 2>/dev/null; then
    print_success "Redis import successful"
else
    print_warning "Redis import failed"
fi

# Show installed versions
echo
print_info "📋 Installed versions:"
python -c "
try:
    import celery; print('  🔧 Celery:', celery.__version__)
except: print('  ❌ Celery: Not available')

try:
    import flower; print('  🌸 Flower:', flower.__version__)
except: print('  ❌ Flower: Not available')

try:
    import redis; print('  📡 Redis:', redis.__version__)
except: print('  ❌ Redis: Not available')
"

echo
print_success "🎉 Dependency installation completed!"
print_info "💡 Now you can start workers with Flower monitoring:"
print_info "   ./scripts/simple-workers.sh start"
print_info "   ./scripts/run-workers.sh start"