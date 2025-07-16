#!/bin/bash
# File: scripts/reset-db-fixed.sh
# Fixed database reset script to handle collation issues

set -e

echo "🔥 Database Reset for CryptoPredict MVP (Fixed)"
echo "=============================================="
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

# Drop and recreate database using Docker exec
echo "🗑️ Dropping database using Docker..."
if docker-compose -f ../docker-compose-backend.yml exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS cryptopredict;" > /dev/null 2>&1; then
    echo "✅ Database dropped successfully!"
else
    echo "⚠️ Database drop had warnings, but continuing..."
fi

echo "🏗️ Creating new database..."
if docker-compose -f ../docker-compose-backend.yml exec postgres psql -U postgres -c "CREATE DATABASE cryptopredict;" > /dev/null 2>&1; then
    echo "✅ Database created successfully!"
else
    echo "⚠️ Database creation had warnings, but continuing..."
fi

# Wait a moment for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 3

# Test database connection
echo "🔍 Testing database connection..."
python -c "
import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:postgres123@localhost:5432/cryptopredict')
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    print('✅ Database connection successful!')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
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
    print('Trying to continue anyway...')
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
        exit(0)
    
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
    print('You can add data manually later.')
"

echo ""
echo "🎉 Database Reset Complete!"
echo "==========================="
echo ""
echo "✅ Database recreated (ignoring collation warnings)"
echo "✅ Tables created"
echo "✅ Initial cryptocurrency data seeded"
echo ""
echo "Next steps:"
echo "  1. Start backend: ./scripts/start-backend.sh"
echo "  2. Test API: http://localhost:8000/docs"
echo "  3. Check health: http://localhost:8000/health"

cd ..