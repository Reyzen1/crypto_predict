#!/bin/bash
# File: scripts/migrate-db.sh
# Database migration script for CryptoPredict MVP

set -e

echo "🗄️ Database Migration for CryptoPredict MVP"
echo "==========================================="

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

# Check if database is accessible
echo "🔍 Checking database connection..."
if ! python -c "
import psycopg2
from app.core.config import settings
try:
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.close()
    print('✅ Database connection successful!')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"; then
    echo "❌ Cannot connect to database. Make sure PostgreSQL is running."
    echo "Run: ./scripts/quick-setup.sh to start databases"
    exit 1
fi

# Initialize Alembic if not already done
if [ ! -d "alembic" ]; then
    echo "🚀 Initializing Alembic..."
    alembic init alembic
    
    # Copy our custom env.py
    echo "🔧 Configuring Alembic environment..."
    # The env.py file should be manually created from the artifact above
fi

# Generate migration if models have changed
echo "🔄 Generating database migration..."
alembic revision --autogenerate -m "Initial database setup with users, cryptocurrencies, price_data, predictions, and portfolios tables"

# Apply migrations
echo "⬆️ Applying database migrations..."
alembic upgrade head

# Seed initial data
echo "🌱 Seeding initial cryptocurrency data..."
python -c "
from app.core.database import SessionLocal
from app.models import Cryptocurrency
import uuid

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
    # Check if cryptocurrency already exists
    existing = db.query(Cryptocurrency).filter(Cryptocurrency.symbol == crypto_data['symbol']).first()
    if not existing:
        crypto = Cryptocurrency(**crypto_data)
        db.add(crypto)
        print(f'✅ Added {crypto_data[\"name\"]} ({crypto_data[\"symbol\"]})')
    else:
        print(f'⚠️ {crypto_data[\"name\"]} ({crypto_data[\"symbol\"]}) already exists')

db.commit()
db.close()
print('🎉 Database seeding completed!')
"

echo ""
echo "🎉 Database Migration Complete!"
echo "==============================="
echo ""
echo "✅ Migration applied successfully"
echo "✅ Initial cryptocurrency data seeded"
echo ""
echo "Database tables created:"
echo "  - users"
echo "  - cryptocurrencies"
echo "  - price_data"
echo "  - predictions" 
echo "  - portfolios"
echo ""
echo "You can now:"
echo "  - Start the backend: ./scripts/start-backend.sh"
echo "  - Access API docs: http://localhost:8000/docs"
echo "  - Test database endpoints"

cd ..