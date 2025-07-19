# File: ./scripts/update-requirements.sh
# Update requirements.txt with new dependencies

#!/bin/bash

set -e

echo "📝 Updating Requirements.txt"
echo "============================"

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found! Please run from project root."
    exit 1
fi

echo "📝 Creating updated requirements.txt..."

# Create updated requirements.txt
cat > backend/requirements.txt << 'EOF'
# File: ./backend/requirements.txt
# Python dependencies for CryptoPredict MVP Backend - Updated for Day 4

# Core FastAPI and ASGI server
fastapi==0.104.1                  # Modern, fast web framework for building APIs
uvicorn[standard]==0.24.0         # ASGI server for FastAPI
python-multipart==0.0.6           # For handling file uploads (form/multipart)

# Database and ORM
sqlalchemy==2.0.23                # SQL toolkit and ORM
alembic==1.12.1                   # Database migration tool for SQLAlchemy
psycopg2-binary==2.9.9            # PostgreSQL adapter for Python (binary version)

# Cache and Session
redis==5.0.1                      # Redis client for caching and sessions

# Data Validation and Serialization
pydantic[email]==2.5.0            # Data validation with email support
pydantic-settings==2.1.0          # Settings management for Pydantic
email-validator==2.1.0            # Email validation for Pydantic

# Authentication and Security
python-jose[cryptography]==3.3.0  # JWT token handling with cryptographic support
passlib[bcrypt]==1.7.4            # Password hashing utilities with bcrypt
bcrypt==4.0.1                     # Low-level password hashing algorithm

# HTTP Client and External APIs
httpx==0.25.2                     # Async HTTP client for external APIs
requests==2.31.0                  # Synchronous HTTP client (backup)

# Configuration Management
python-decouple==3.8              # Environment variable management
python-dotenv==1.0.0              # Load environment variables from .env files

# Data Processing and ML
pandas>=2.2.0                     # Data manipulation and analysis
numpy>=1.26.0                     # Numerical computing
scikit-learn>=1.4.0               # Machine learning library
tensorflow>=2.16.0                # Deep learning framework
matplotlib==3.8.2                 # Data visualization library

# Background Tasks and Scheduling
apscheduler==3.10.4               # Advanced Python Scheduler for background jobs
celery==5.3.4                     # Distributed task queue (alternative)

# Rate Limiting and WebSockets
slowapi==0.1.9                    # Rate limiting for FastAPI using decorators
python-socketio==5.10.0           # WebSocket client/server support (Socket.IO)

# File Handling
aiofiles==23.2.1                  # Async file operations (read/write with FastAPI)

# Utilities
click==8.1.7                      # CLI utility for creating command-line interfaces

# Testing
pytest==7.4.3                     # Testing framework
pytest-asyncio==0.21.1            # Async testing support with pytest

# Development
black==23.10.1                    # Code formatter
flake8==6.1.0                     # Code linting (style guide enforcement)
isort==5.12.0                     # Sort imports automatically

# Additional API Development
pydantic-extra-types==2.1.0       # Extra types for Pydantic
typing-extensions==4.8.0          # Typing extensions for better type hints
EOF

echo "✅ Requirements.txt updated successfully!"

echo ""
echo "📋 New dependencies added:"
echo "   - pydantic[email] - Email validation"
echo "   - email-validator - Email validation library"
echo "   - python-jose[cryptography] - JWT with crypto"
echo "   - passlib[bcrypt] - Password hashing"
echo "   - httpx - Modern HTTP client"
echo "   - apscheduler - Background job scheduling"
echo "   - pydantic-extra-types - Additional Pydantic types"

echo ""
echo "🎯 Next steps:"
echo "1. Install dependencies: ./scripts/install-schema-dependencies.sh"
echo "2. Test schemas: ./scripts/test-schemas.sh"