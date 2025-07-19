#!/bin/bash
# File: scripts/setup-db.sh
# Simple database setup script without Alembic (fallback option)

set -e

echo "🗄️ Simple Database Setup for CryptoPredict MVP"
echo "=============================================="

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found! Please run from project root."
    exit 1
fi

# Backup existing Alembic versions if they exist
if [ -d "backend/alembic/versions" ] && [ "$(ls -A backend/alembic/versions)" ]; then
    echo "📦 Backing up existing Alembic versions..."
    if [ ! -d "backend/alembic/versions_backup" ]; then
        mkdir -p backend/alembic/versions_backup
    fi
    
    # Create timestamped backup
    backup_dir="backend/alembic/versions_backup/$(date +%Y%m%d_%H%M%S)"
    cp -r backend/alembic/versions "$backup_dir"
    echo "✅ Backup created at: $backup_dir"
    
    # Clear versions directory (including subdirectories)
    rm -rf backend/alembic/versions/*
    rm -rf backend/alembic/versions/__pycache__ 2>/dev/null || true
    echo "🧹 Cleared alembic/versions directory"
else
    echo "ℹ️ No existing Alembic versions found to backup"
fi

cd backend

# Activate virtual environment
if [ -f "venv/Scripts/activate" ]; then
    echo "🔧 Activating virtual environment (Windows)..."
    source venv/Scripts/activate
elif [ -f "venv/scripts/activate" ]; then
    echo "🔧 Activating virtual environment (Git Bash)..."
    source venv/scripts/activate
elif [ -f "venv/bin/activate" ]; then
    echo "🔧 Activating virtual environment (Linux/Mac)..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "Please run: ./scripts/quick-setup.sh first"
    exit 1
fi

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres123@localhost:5432/cryptopredict"
export REDIS_URL="redis://localhost:6379/0"

# Remove existing database file if using SQLite
if [ -f "database.db" ]; then
    echo "🗑️ Removing existing SQLite database..."
    rm database.db
fi

# Create database tables using SQLAlchemy
echo "🏗️ Creating database tables..."
python -c "
from app.core.database import engine, Base
import app.models
import sys

try:
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print('✅ Database tables created successfully!')
except Exception as e:
    print(f'❌ Error creating tables: {e}')
    sys.exit(1)
"

# Seed initial data
echo "🌱 Seeding initial data..."
python -c "
from app.core.database import SessionLocal
from app.models import Cryptocurrency
import sys

try:
    db = SessionLocal()
    
    # Check if data already exists
    existing_count = db.query(Cryptocurrency).count()
    if existing_count > 0:
        print('⚠️ Database already contains cryptocurrency data. Skipping seeding.')
        db.close()
        sys.exit(0)
    
    # Initial cryptocurrencies
    cryptos = [
        {
            'symbol': 'BTC',
            'name': 'Bitcoin', 
            'coingecko_id': 'bitcoin',
            'binance_symbol': 'BTCUSDT'
        },
        {
            'symbol': 'ETH',
            'name': 'Ethereum',
            'coingecko_id': 'ethereum', 
            'binance_symbol': 'ETHUSDT'
        },
        {
            'symbol': 'ADA',
            'name': 'Cardano',
            'coingecko_id': 'cardano',
            'binance_symbol': 'ADAUSDT'
        },
        {
            'symbol': 'DOT',
            'name': 'Polkadot',
            'coingecko_id': 'polkadot',
            'binance_symbol': 'DOTUSDT'
        },
        {
            'symbol': 'LINK',
            'name': 'Chainlink',
            'coingecko_id': 'chainlink',
            'binance_symbol': 'LINKUSDT'
        }
    ]
    
    for crypto_data in cryptos:
        crypto = Cryptocurrency(**crypto_data)
        db.add(crypto)
        print(f'✅ Added {crypto_data[\"name\"]} ({crypto_data[\"symbol\"]})')
    
    db.commit()
    db.close()
    print('🎉 Database seeding completed!')
    
except Exception as e:
    print(f'❌ Error seeding database: {e}')
    sys.exit(1)
"

echo ""
echo "🎉 Database Setup Complete!"
echo "==========================="
echo ""
echo "✅ Database tables created from SQLAlchemy models"
echo "✅ Initial cryptocurrency data seeded"
echo "✅ Alembic versions backed up (if existed)"
echo ""
echo "Database tables:"
echo "  - users (for authentication)"
echo "  - cryptocurrencies (BTC, ETH, ADA, DOT, LINK)"
echo "  - price_data (for historical prices)"
echo "  - predictions (for ML predictions)"
echo "  - portfolios (for user holdings)"
echo ""
echo "⚠️  Important Notes:"
echo "  - This setup bypasses Alembic migrations"
echo "  - For production, consider using Alembic for schema changes"
echo "  - Backup created at: backend/alembic/versions_backup/"
echo ""
echo "Next steps:"
echo "  1. Start backend: ./scripts/start-backend.sh"
echo "  2. Test API: http://localhost:8000/docs"
echo "  3. Check health: http://localhost:8000/health"
echo ""
echo "🔄 To restore Alembic later:"
echo "  cp -r backend/alembic/versions_backup/[timestamp]/* backend/alembic/versions/"

cd ..