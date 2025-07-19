#!/bin/bash
# File: scripts/test-db.sh
# Test database connection and models

set -e

echo "🧪 Testing Database Connection and Models"
echo "========================================"

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

# Test database connection
echo "🔍 Testing database connection..."
python -c "
import sys
try:
    from app.core.database import engine, SessionLocal
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute('SELECT 1 as test')
        print('✅ Database connection successful!')
        
    # Test session
    db = SessionLocal()
    db.execute('SELECT 1')
    db.close()
    print('✅ Database session working!')
    
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
"

# Test model imports
echo "🔍 Testing model imports..."
python -c "
import sys
try:
    from app.models import User, Cryptocurrency, PriceData, Prediction, Portfolio
    print('✅ All models imported successfully!')
    
    # Test model attributes
    print(f'✅ User model: {User.__tablename__}')
    print(f'✅ Cryptocurrency model: {Cryptocurrency.__tablename__}')
    print(f'✅ PriceData model: {PriceData.__tablename__}')
    print(f'✅ Prediction model: {Prediction.__tablename__}')
    print(f'✅ Portfolio model: {Portfolio.__tablename__}')
    
except Exception as e:
    print(f'❌ Model import failed: {e}')
    sys.exit(1)
"

# Test table creation
echo "🔍 Testing table creation..."
python -c "
import sys
try:
    from app.core.database import engine, Base
    import app.models
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print('✅ Tables created successfully!')
    
    # Check if tables exist
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public'\"))
        tables = [row[0] for row in result]
        
        expected_tables = ['users', 'cryptocurrencies', 'price_data', 'predictions', 'portfolios']
        for table in expected_tables:
            if table in tables:
                print(f'✅ Table {table} exists')
            else:
                print(f'❌ Table {table} missing')
                sys.exit(1)
    
except Exception as e:
    print(f'❌ Table creation failed: {e}')
    sys.exit(1)
"

# Test data insertion
echo "🔍 Testing data operations..."
python -c "
import sys
try:
    from app.core.database import SessionLocal
    from app.models import Cryptocurrency
    
    db = SessionLocal()
    
    # Test insert
    test_crypto = Cryptocurrency(
        symbol='TEST',
        name='Test Coin',
        coingecko_id='test-coin',
        binance_symbol='TESTUSDT'
    )
    
    db.add(test_crypto)
    db.commit()
    print('✅ Data insertion successful!')
    
    # Test query
    result = db.query(Cryptocurrency).filter(Cryptocurrency.symbol == 'TEST').first()
    if result:
        print(f'✅ Data query successful: {result.name}')
    else:
        print('❌ Data query failed')
        sys.exit(1)
    
    # Clean up test data
    db.delete(result)
    db.commit()
    print('✅ Data deletion successful!')
    
    db.close()
    
except Exception as e:
    print(f'❌ Data operations failed: {e}')
    sys.exit(1)
"

echo ""
echo "🎉 All Database Tests Passed!"
echo "============================"
echo ""
echo "✅ Database connection working"
echo "✅ Models imported correctly"
echo "✅ Tables created successfully"
echo "✅ Data operations working"
echo ""
echo "Database is ready for use!"

cd ..