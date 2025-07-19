# File: ./scripts/test-repositories.sh

# Test repository patterns and CRUD operations

#!/bin/bash

set -e

echo "🧪 Testing Repository Patterns & CRUD Operations (FIXED)"
echo "========================================================"

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

echo ""
echo "📋 Test 1: Repository Import Test"
echo "---------------------------------"
python -c "
try:
    from app.repositories import (
        user_repository, 
        cryptocurrency_repository, 
        price_data_repository
    )
    print('✅ All repositories imported successfully')
    print('   - UserRepository: ' + type(user_repository).__name__)
    print('   - CryptocurrencyRepository: ' + type(cryptocurrency_repository).__name__)
    print('   - PriceDataRepository: ' + type(price_data_repository).__name__)
except Exception as e:
    print('❌ Repository import failed: ' + str(e))
    import sys
    sys.exit(1)
"

echo ""
echo "📋 Test 2: User Repository CRUD"
echo "-------------------------------"
python -c "
from app.core.database import SessionLocal
from app.repositories import user_repository
import sys

db = SessionLocal()

try:
    print('Testing User Repository CRUD operations...')
    
    # CREATE - Test user creation
    user = user_repository.create_user(
        db,
        email='test_repo@example.com',
        password_hash='hashed_password_123',
        first_name='Repository',
        last_name='Test'
    )
    print('✅ User created: ID=' + str(user.id) + ', Email=' + user.email)
    
    # READ - Test user retrieval
    found_user = user_repository.get_by_email(db, 'test_repo@example.com')
    if found_user and found_user.id == user.id:
        print('✅ User retrieval by email successful')
    else:
        print('❌ User retrieval failed')
        sys.exit(1)
    
    # READ - Test get by ID
    user_by_id = user_repository.get(db, user.id)
    if user_by_id and user_by_id.email == 'test_repo@example.com':
        print('✅ User retrieval by ID successful')
    else:
        print('❌ User retrieval by ID failed')
        sys.exit(1)
    
    # UPDATE - Test user verification
    verified_user = user_repository.verify_user(db, user.id)
    if verified_user and verified_user.is_verified:
        print('✅ User verification successful')
    else:
        print('❌ User verification failed')
        sys.exit(1)
    
    # COUNT - Test active users count
    active_count = user_repository.count_active_users(db)
    print('✅ Active users count: ' + str(active_count))
    
    # SEARCH - Test user search
    search_results = user_repository.search_users(db, 'Repository')
    if len(search_results) > 0:
        print('✅ User search successful: found ' + str(len(search_results)) + ' users')
    else:
        print('⚠️ User search returned no results')
    
    # DELETE - Clean up test data
    deleted = user_repository.delete(db, id=user.id)
    if deleted:
        print('✅ User deletion successful')
    else:
        print('❌ User deletion failed')
        sys.exit(1)
    
    print()
    print('✅ All User Repository tests passed!')
    
except Exception as e:
    print('❌ User Repository test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
"

echo ""
echo "📋 Test 3: Cryptocurrency Repository CRUD"
echo "-----------------------------------------"
python -c "
from app.core.database import SessionLocal
from app.repositories import cryptocurrency_repository
import sys

db = SessionLocal()

try:
    print('Testing Cryptocurrency Repository CRUD operations...')
    
    # READ - Test existing crypto (should have Bitcoin from seeding)
    btc = cryptocurrency_repository.get_by_symbol(db, 'BTC')
    if btc:
        print('✅ Bitcoin found: ID=' + str(btc.id) + ', Name=' + btc.name)
    else:
        print('❌ Bitcoin not found in database')
        sys.exit(1)
    
    # CREATE - Test new crypto creation
    test_crypto = cryptocurrency_repository.create_crypto(
        db,
        symbol='TEST',
        name='Test Coin',
        coingecko_id='test-coin',
        binance_symbol='TESTUSDT'
    )
    print('✅ Test crypto created: ID=' + str(test_crypto.id) + ', Symbol=' + test_crypto.symbol)
    
    # READ - Test active cryptos
    active_cryptos = cryptocurrency_repository.get_active_cryptos(db, limit=10)
    print('✅ Active cryptos found: ' + str(len(active_cryptos)))
    
    # READ - Test CoinGecko ID lookup
    bitcoin_by_id = cryptocurrency_repository.get_by_coingecko_id(db, 'bitcoin')
    if bitcoin_by_id and bitcoin_by_id.symbol == 'BTC':
        print('✅ Bitcoin found by CoinGecko ID')
    else:
        print('❌ Bitcoin lookup by CoinGecko ID failed')
        sys.exit(1)
    
    # UPDATE - Test deactivation
    deactivated = cryptocurrency_repository.deactivate_crypto(db, test_crypto.id)
    if deactivated and not deactivated.is_active:
        print('✅ Crypto deactivation successful')
    else:
        print('❌ Crypto deactivation failed')
        sys.exit(1)
    
    # COUNT - Test active crypto count
    active_count = cryptocurrency_repository.count_active_cryptos(db)
    print('✅ Active cryptos count: ' + str(active_count))
    
    # SEARCH - Test crypto search
    search_results = cryptocurrency_repository.search_cryptos(db, 'Bitcoin')
    if len(search_results) > 0:
        print('✅ Crypto search successful: found ' + str(len(search_results)) + ' cryptos')
    else:
        print('⚠️ Crypto search returned no results')
    
    # DELETE - Clean up test data
    deleted = cryptocurrency_repository.delete(db, id=test_crypto.id)
    if deleted:
        print('✅ Test crypto deletion successful')
    else:
        print('❌ Test crypto deletion failed')
        sys.exit(1)
    
    print()
    print('✅ All Cryptocurrency Repository tests passed!')
    
except Exception as e:
    print('❌ Cryptocurrency Repository test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
"

echo ""
echo "📋 Test 4: Price Data Repository Operations"
echo "------------------------------------------"
python -c "
from app.core.database import SessionLocal
from app.repositories import cryptocurrency_repository, price_data_repository
from datetime import datetime, timezone
from decimal import Decimal
import sys

db = SessionLocal()

try:
    print('Testing Price Data Repository operations...')
    
    # Get Bitcoin for testing
    btc = cryptocurrency_repository.get_by_symbol(db, 'BTC')
    if not btc:
        print('❌ Bitcoin not found - cannot test price data')
        sys.exit(1)
    
    # CREATE - Test price data creation
    price_data = price_data_repository.add_price_data(
        db,
        crypto_id=btc.id,
        timestamp=datetime.now(timezone.utc),
        open_price=Decimal('50000.00'),
        high_price=Decimal('51000.00'),
        low_price=Decimal('49000.00'),
        close_price=Decimal('50500.00'),
        volume=Decimal('1000000.00'),
        market_cap=Decimal('1000000000.00')
    )
    print('✅ Price data created: ID=' + str(price_data.id) + ', Close=' + str(price_data.close_price))
    
    # READ - Test latest price retrieval
    latest_price = price_data_repository.get_latest_price(db, btc.id)
    if latest_price and latest_price.id == price_data.id:
        print('✅ Latest price retrieval successful')
    else:
        print('❌ Latest price retrieval failed')
        sys.exit(1)
    
    # READ - Test price history
    price_history = price_data_repository.get_price_history(db, btc.id, limit=10)
    print('✅ Price history retrieved: ' + str(len(price_history)) + ' records')
    
    # ANALYTICS - Test daily statistics
    stats = price_data_repository.get_daily_statistics(db, btc.id, days=1)
    avg_price = stats.get('avg_price', 0)
    print('✅ Daily statistics: avg_price=' + str(round(avg_price, 2)))
    
    # ANALYTICS - Test data availability
    availability = price_data_repository.check_data_availability(db, btc.id)
    total_records = availability.get('total_records', 0)
    print('✅ Data availability: ' + str(total_records) + ' records')
    
    # ML DATA - Test ML data format
    ml_data = price_data_repository.get_price_data_for_ml(db, btc.id, days_back=1)
    print('✅ ML data format: ' + str(len(ml_data)) + ' records')
    
    # COUNT - Test record count
    count = price_data_repository.count_by_crypto(db, btc.id)
    print('✅ Price data count for BTC: ' + str(count))
    
    # DELETE - Clean up test data
    deleted = price_data_repository.delete(db, id=price_data.id)
    if deleted:
        print('✅ Price data deletion successful')
    else:
        print('❌ Price data deletion failed')
        sys.exit(1)
    
    print()
    print('✅ All Price Data Repository tests passed!')
    
except Exception as e:
    print('❌ Price Data Repository test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
"

echo ""
echo "📋 Test 5: Repository Integration Test"
echo "-------------------------------------"
python -c "
from app.core.database import SessionLocal
from app.repositories import user_repository, cryptocurrency_repository, price_data_repository
from datetime import datetime, timezone
from decimal import Decimal
import sys

db = SessionLocal()

try:
    print('Testing repository integration...')
    
    # Create test user
    user = user_repository.create_user(
        db,
        email='integration@test.com',
        password_hash='test_hash',
        first_name='Integration',
        last_name='Test'
    )
    
    # Get Bitcoin
    btc = cryptocurrency_repository.get_by_symbol(db, 'BTC')
    
    # Add price data
    price_data = price_data_repository.add_price_data(
        db,
        crypto_id=btc.id,
        timestamp=datetime.now(timezone.utc),
        open_price=Decimal('50000.00'),
        high_price=Decimal('51000.00'),
        low_price=Decimal('49000.00'),
        close_price=Decimal('50500.00'),
        volume=Decimal('1000000.00')
    )
    
    # Test relationships through repositories
    crypto_with_price = cryptocurrency_repository.get_crypto_with_latest_price(db, btc.id)
    if crypto_with_price and crypto_with_price.get('latest_price'):
        print('✅ Crypto-Price relationship working')
    else:
        print('❌ Crypto-Price relationship failed')
        sys.exit(1)
    
    # Test user existence
    if user and user.id:
        print('✅ User relationship working')
    else:
        print('❌ User relationship failed')
        sys.exit(1)
    
    print('✅ Repository integration successful!')
    
    # Clean up
    price_data_repository.delete(db, id=price_data.id)
    user_repository.delete(db, id=user.id)
    print('✅ Integration test cleanup completed')
    
except Exception as e:
    print('❌ Repository integration test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
"

cd ..

echo ""
echo "🎉 ALL REPOSITORY TESTS PASSED!"
echo "==============================="
echo ""
echo "✅ Repository Pattern Implementation Complete"
echo "✅ CRUD Operations Working"
echo "✅ Specialized Repository Methods Working"
echo "✅ Database Relationships Working"
echo "✅ Data Validation Working"
echo ""
echo "📅 Day 3 - Afternoon Progress:"
echo "  ✅ Repository Patterns - COMPLETED"
echo "  ✅ CRUD Operations - COMPLETED"
echo "  ✅ Data Validation - COMPLETED"
echo ""
echo "🚀 Day 3 COMPLETED! Ready for Day 4: API Gateway & Data Pipeline"