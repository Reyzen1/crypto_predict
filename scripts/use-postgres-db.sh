#!/bin/bash
# File: scripts/use-postgres-db.sh
# Use default postgres database instead of cryptopredict

echo "🐘 Using Default Postgres Database"
echo "=================================="

echo "📝 Updating configuration..."

# Update config to use postgres database
cd backend

# Activate virtual environment
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Use postgres database instead of cryptopredict
export DATABASE_URL="postgresql://postgres:postgres123@localhost:5432/postgres"

echo "🏗️ Creating tables in postgres database..."
python -c "
from app.core.database import engine, Base
import app.models
Base.metadata.create_all(bind=engine)
print('✅ Tables created in postgres database!')
"

echo "🌱 Seeding data..."
python -c "
from app.core.database import SessionLocal
from app.models import Cryptocurrency

db = SessionLocal()

# Check if data already exists
existing_count = db.query(Cryptocurrency).count()
if existing_count > 0:
    print('⚠️ Data already exists. Skipping seeding.')
else:
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
    print('🎉 Database seeding completed!')

db.close()
"

cd ..

echo ""
echo "🎉 Setup complete using postgres database!"
echo "========================================"
echo ""
echo "Configuration:"
echo "  - Database: postgres (default)"
echo "  - Tables: created"
echo "  - Data: seeded"
echo ""
echo "⚠️  Important: Update start-backend.sh to use postgres database:"
echo "  DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/postgres"
echo ""
echo "Next: ./scripts/start-backend.sh"