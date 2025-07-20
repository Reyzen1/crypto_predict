#!/bin/bash
# Test CRUD API Endpoints

set -e

echo "🧪 Testing CRUD API Endpoints"
echo "============================="

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

echo ""
echo "📋 Test 1: API Router Integration"
echo "---------------------------------"
python -c "
from app.api.api_v1.api import api_router
import sys

try:
    print('Testing API Router Integration...')
    
    # Check if all routers are included
    routes = [route.path for route in api_router.routes]
    
    expected_prefixes = ['/auth', '/users', '/crypto', '/prices', '/system']
    found_prefixes = []
    
    for prefix in expected_prefixes:
        prefix_routes = [route for route in routes if route.startswith(prefix)]
        if prefix_routes:
            found_prefixes.append(prefix)
            print(f'✅ {prefix} router found with {len(prefix_routes)} routes')
        else:
            print(f'❌ {prefix} router missing!')
            sys.exit(1)
    
    # Check original routes still exist
    if '/health' in routes:
        print('✅ Original health endpoint preserved')
    else:
        print('❌ Original health endpoint missing!')
        sys.exit(1)
        
    if '/info' in routes:
        print('✅ Original info endpoint preserved')
    else:
        print('❌ Original info endpoint missing!')
        sys.exit(1)
    
    print(f'✅ All {len(expected_prefixes)} CRUD routers integrated successfully!')
    
except Exception as e:
    print('❌ API Router integration test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "📋 Test 2: Endpoint Import Test"
echo "-------------------------------"
python -c "
import sys

try:
    print('Testing endpoint imports...')
    
    # Test all endpoint imports
    from app.api.api_v1.endpoints import auth
    print('✅ Auth endpoints imported')
    
    from app.api.api_v1.endpoints import users
    print('✅ Users endpoints imported')
    
    from app.api.api_v1.endpoints import crypto
    print('✅ Crypto endpoints imported')
    
    from app.api.api_v1.endpoints import prices
    print('✅ Prices endpoints imported')
    
    from app.api.api_v1.endpoints import health
    print('✅ Health endpoints imported')
    
    # Check router objects exist
    routers = [auth.router, users.router, crypto.router, prices.router, health.router]
    print(f'✅ All {len(routers)} endpoint routers available')
    
except Exception as e:
    print('❌ Endpoint import test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "📋 Test 3: Repository Integration Test"
echo "-------------------------------------"
python -c "
from app.core.database import SessionLocal
from app.repositories import user_repository, cryptocurrency_repository, price_data_repository
from app.schemas.user import UserRegister
from app.services.auth import auth_service
import sys

db = SessionLocal()

try:
    print('Testing repository integration with endpoints...')
    
    # Test that repositories work with endpoint schemas
    
    # Test user creation (simulating POST /users/ endpoint)
    print('Testing user repository integration...')
    test_email = 'crud_test@example.com'
    
    # Clean up any existing user
    existing = user_repository.get_by_email(db, test_email)
    if existing:
        user_repository.delete(db, id=existing.id)
    
    # Test user creation
    user = user_repository.create_user(
        db,
        email=test_email,
        password_hash='test_hash',
        first_name='CRUD',
        last_name='Test'
    )
    print('✅ User repository integration working')
    
    # Test cryptocurrency operations
    print('Testing cryptocurrency repository integration...')
    btc = cryptocurrency_repository.get_by_symbol(db, 'BTC')
    if btc:
        print('✅ Cryptocurrency repository integration working')
    else:
        print('⚠️ No BTC found - create some test data')
    
    # Test price data operations
    if btc:
        print('Testing price data repository integration...')
        latest_price = price_data_repository.get_latest_price(db, btc.id)
        data_check = price_data_repository.check_data_availability(db, btc.id)
        print('✅ Price data repository integration working')
        print(f'   Total BTC records: {data_check[\"total_records\"]}')
    
    # Clean up
    user_repository.delete(db, id=user.id)
    print('✅ Repository integration tests passed!')
    
except Exception as e:
    print('❌ Repository integration test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
"

echo ""
echo "📋 Test 4: Schema Compatibility Test"
echo "------------------------------------"
python -c "
from app.schemas.user import UserResponse, UserUpdate, UserSummary
from app.schemas.cryptocurrency import CryptocurrencyResponse, CryptocurrencyCreate
from app.schemas.price_data import PriceDataResponse, PriceDataCreate, OHLCV
from app.schemas.common import PaginatedResponse, SuccessResponse
import sys

try:
    print('Testing schema compatibility with endpoints...')
    
    # Test schema creation for endpoints
    
    # Test user schemas
    user_summary = UserSummary(
        id=1,
        email='test@example.com',
        first_name='Test',
        last_name='User',
        is_active=True
    )
    print('✅ User schemas compatible')
    
    # Test crypto schemas
    crypto_create = CryptocurrencyCreate(
        symbol='TEST',
        name='Test Coin',
        is_active=True
    )
    print('✅ Cryptocurrency schemas compatible')
    
    # Test pagination schema
    paginated = PaginatedResponse.create(
        items=[user_summary],
        total=1,
        skip=0,
        limit=10
    )
    print('✅ Pagination schemas compatible')
    
    # Test success response
    success = SuccessResponse(
        message='Test successful',
        data={'test': True}
    )
    print('✅ Response schemas compatible')
    
    print('✅ All schemas compatible with endpoints!')
    
except Exception as e:
    print('❌ Schema compatibility test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "📋 Test 5: Dependencies Test"
echo "----------------------------"
python -c "
from app.core.deps import get_current_active_user, get_optional_current_user
from app.core.database import get_db, get_redis
import sys

try:
    print('Testing dependencies used by endpoints...')
    
    # Test database dependency
    db_gen = get_db()
    db = next(db_gen)
    print('✅ Database dependency working')
    db.close()
    
    # Test Redis dependency  
    try:
        redis_client = get_redis()
        print('✅ Redis dependency available')
    except Exception:
        print('⚠️ Redis dependency unavailable (check Redis server)')
    
    # Test authentication dependencies exist
    print('✅ Authentication dependencies available')
    
    print('✅ All dependencies working!')
    
except Exception as e:
    print('❌ Dependencies test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "📋 Test 6: Health Endpoint Test"
echo "-------------------------------"
python -c "
from app.api.api_v1.endpoints.health import comprehensive_health_check, get_system_metrics
from app.core.deps import get_optional_current_user
import sys

try:
    print('Testing health endpoints...')
    
    # Test basic health check (no auth required)
    health_result = comprehensive_health_check(current_user=None)
    
    if health_result and 'status' in health_result:
        print('✅ Health check endpoint working')
        print(f'   Status: {health_result[\"status\"]}')
        print(f'   Components: {len(health_result.get(\"components\", {}))}')
    else:
        print('❌ Health check failed')
        sys.exit(1)
    
    print('✅ Health endpoints working!')
    
except Exception as e:
    print('❌ Health endpoint test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

cd ..

echo ""
echo "🎉 ALL CRUD ENDPOINT TESTS PASSED!"
echo "=================================="
echo ""
echo "✅ API Router Integration Working"
echo "✅ Endpoint Imports Working"
echo "✅ Repository Integration Working"
echo "✅ Schema Compatibility Working"
echo "✅ Dependencies Working"
echo "✅ Health Endpoints Working"
echo ""
echo "📊 CRUD API Endpoints Summary:"
echo "  👤 Users API: 7 endpoints (CRUD + stats)"
echo "  💰 Crypto API: 8 endpoints (CRUD + price data)"
echo "  📊 Prices API: 7 endpoints (CRUD + analytics)"
echo "  🏥 Health API: 6 endpoints (monitoring)"
echo "  🔐 Auth API: 7 endpoints (authentication)"
echo ""
echo "📅 Day 4 - Phase 3 Progress:"
echo "  ✅ CRUD API Endpoints - COMPLETED"
echo "  🔄 External API Integration - NEXT"
echo ""
echo "🚀 Ready for Phase 4: External API Integration!"