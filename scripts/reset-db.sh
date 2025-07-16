#!/bin/bash
# File: scripts/reset-db.sh
# Reset database completely and start fresh

set -e

echo "🔥 Database Reset for CryptoPredict MVP"
echo "======================================"
echo "⚠️  This will DELETE ALL DATA in the database!"
echo ""

# Ask for confirmation
read -p "Are you sure you want to reset the database? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Database reset cancelled."
    exit 0
fi

echo "🔄 Resetting database..."

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
    echo "Please run: ./scripts/quick-setup.sh first"
    exit 1
fi

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres123@localhost:5432/cryptopredict"
export REDIS_URL="redis://localhost:6379/0"

# Drop and recreate database
echo "🗑️ Dropping database..."
python -c "
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    # Connect to PostgreSQL server (not to the database)
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres123',
        database='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Terminate existing connections to the database
    cursor.execute('''
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = 'cryptopredict' AND pid <> pg_backend_pid()
    ''')
    
    # Drop database
    cursor.execute('DROP DATABASE IF EXISTS cryptopredict')
    print('✅ Database dropped successfully!')
    
    # Create new database
    cursor.execute('CREATE DATABASE cryptopredict')
    print('✅ Database created successfully!')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error resetting database: {e}')
    exit(1)
"

# Create tables with new schema
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
echo "🎉 Database Reset Complete!"
echo "==========================="
echo ""
echo "✅ Database dropped and recreated"
echo "✅ Tables created with UUID schema"
echo "✅ Initial cryptocurrency data seeded"
echo ""
echo "Database tables:"
echo "  - users (UUID primary key)"
echo "  - cryptocurrencies (UUID primary key)"
echo "  - price_data (UUID primary key)"
echo "  - predictions (UUID primary key)"
echo "  - portfolios (UUID primary key)"
echo ""
echo "Next steps:"
echo "  1. Start backend: ./scripts/start-backend.sh"
echo "  2. Test API: http://localhost:8000/docs"

cd ..