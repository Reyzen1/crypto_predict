#!/bin/bash
# File: scripts/drop-tables.sh
# Simple script to drop all tables and recreate

set -e

echo "🗑️ Dropping All Tables"
echo "======================"

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found! Please run from project root."
    exit 1
fi

cd backend

# Activate virtual environment
if [ -f "venv/Scripts/activate" ]; then
    echo "🔧 Activating virtual environment (Windows)..."
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    echo "🔧 Activating virtual environment (Linux/Mac)..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    exit 1
fi

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres123@localhost:5432/cryptopredict"
export REDIS_URL="redis://localhost:6379/0"

# Drop all tables using SQLAlchemy
echo "🗑️ Dropping all tables..."
python -c "
from app.core.database import engine, Base
import app.models
import sys

try:
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    print('✅ All tables dropped successfully!')
except Exception as e:
    print(f'⚠️ Error dropping tables (may not exist): {e}')
    print('Continuing anyway...')
"

# Create tables
echo "🏗️ Creating tables..."
python -c "
from app.core.database import engine, Base
import app.models
import sys

try:
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print('✅ All tables created successfully!')
except Exception as e:
    print(f'❌ Error creating tables: {e}')
    sys.exit(1)
"

# Seed data
echo "🌱 Seeding data..."
python -c "
from app.core.database import SessionLocal
from app.models import Cryptocurrency
import sys

try:
    db = SessionLocal()
    
    # Initial cryptocurrencies
    cryptos = [
        {'symbol': 'BTC', 'name': 'Bitcoin', 'coingecko_id': 'bitcoin', 'binance_symbol': 'BTCUSDT'},
        {'symbol': 'ETH', 'name': 'Ethereum', 'coingecko_id': 'ethereum', 'binance_symbol': 'ETHUSDT'},
        {'symbol': 'ADA', 'name': 'Cardano', 'coingecko_id': 'cardano', 'binance_symbol': 'ADAUSDT'},
        {'symbol': 'DOT', 'name': 'Polkadot', 'coingecko_id': 'polkadot', 'binance_symbol': 'DOTUSDT'},
        {'symbol': 'LINK', 'name': 'Chainlink', 'coingecko_id': 'chainlink', 'binance_symbol': 'LINKUSDT'}
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
echo "🎉 Tables Reset Complete!"
echo "========================"
echo ""
echo "✅ All tables dropped and recreated"
echo "✅ Initial data seeded"
echo ""
echo "Next: ./scripts/start-backend.sh"

cd ..