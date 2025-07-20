#!/bin/bash
# Test Authentication System with api_v1 structure

set -e

echo "🧪 Testing Authentication System (api_v1)"
echo "========================================="

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
echo "📋 Test 1: Security Module Test"
echo "-------------------------------"
python -c "
from app.core.security import security
import sys

try:
    print('Testing Security Manager...')
    
    # Test password hashing
    password = 'test_password_123'
    hashed = security.hash_password(password)
    print('✅ Password hashing works')
    
    # Test password verification
    is_valid = security.verify_password(password, hashed)
    if is_valid:
        print('✅ Password verification works')
    else:
        print('❌ Password verification failed')
        sys.exit(1)
    
    # Test token creation
    data = {'user_id': 1, 'email': 'test@example.com'}
    access_token = security.create_access_token(data)
    refresh_token = security.create_refresh_token(data)
    print('✅ Token creation works')
    
    # Test token verification
    payload = security.verify_token(access_token, 'access')
    if payload.get('user_id') == 1:
        print('✅ Token verification works')
    else:
        print('❌ Token verification failed')
        sys.exit(1)
    
    print('✅ All Security tests passed!')
    
except Exception as e:
    print('❌ Security test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "📋 Test 2: Configuration Test"
echo "-----------------------------"
python -c "
from app.core.config import settings
import sys

try:
    print('Testing Configuration...')
    
    print('✅ PROJECT_NAME: ' + settings.PROJECT_NAME)
    print('✅ DATABASE_URL: ' + settings.DATABASE_URL[:30] + '...')
    print('✅ CORS_ORIGINS: ' + str(len(settings.BACKEND_CORS_ORIGINS)) + ' origins')
    print('✅ SECRET_KEY available: ' + str(bool(settings.SECRET_KEY)))
    print('✅ Algorithm: ' + settings.ALGORITHM)
    
    print('✅ All Configuration tests passed!')
    
except Exception as e:
    print('❌ Configuration test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "📋 Test 3: Dependencies Test"
echo "----------------------------"
python -c "
from app.core.deps import get_current_user_from_token, security_scheme
from app.core.database import get_db
import sys

try:
    print('Testing Dependencies...')
    
    # Test database dependency
    db_gen = get_db()
    db = next(db_gen)
    print('✅ Database dependency works')
    
    # Test security scheme
    scheme = security_scheme
    print('✅ Security scheme configured: ' + str(type(scheme).__name__))
    
    # Close database
    db.close()
    
    print('✅ All Dependencies tests passed!')
    
except Exception as e:
    print('❌ Dependencies test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "📋 Test 4: Auth Service Test"
echo "---------------------------"
python -c "
from app.core.database import SessionLocal
from app.services.auth import auth_service
from app.schemas.user import UserRegister, UserLogin
from app.repositories import user_repository
import sys

db = SessionLocal()

try:
    print('Testing Auth Service...')
    
    # Clean up any existing test user
    existing = user_repository.get_by_email(db, 'auth_test_api_v1@example.com')
    if existing:
        user_repository.delete(db, id=existing.id)
        print('🧹 Cleaned up existing test user')
    
    # Test user registration
    user_data = UserRegister(
        email='auth_test_api_v1@example.com',
        password='SecurePassword123!',
        confirm_password='SecurePassword123!',  # Fixed field name
        first_name='API',
        last_name='Test'
    )
    
    result = auth_service.register_user(db, user_data)
    print('✅ User registration successful')
    print('   User ID: ' + str(result['user']['id']))
    
    # Test user login
    login_data = UserLogin(
        email='auth_test_api_v1@example.com',
        password='SecurePassword123!'
    )
    
    login_result = auth_service.authenticate_user(db, login_data)
    print('✅ User login successful')
    
    # Test token refresh
    refresh_token = login_result['refresh_token']
    new_token = auth_service.refresh_access_token(db, refresh_token)
    print('✅ Token refresh successful')
    
    # Clean up
    user_repository.delete(db, id=result['user']['id'])
    print('🧹 Test cleanup completed')
    
    print('✅ All Auth Service tests passed!')
    
except Exception as e:
    print('❌ Auth Service test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
"

echo ""
echo "📋 Test 5: API Router Test"
echo "--------------------------"
python -c "
from app.api.api_v1.api import api_router
import sys

try:
    print('Testing API Router...')
    
    # Check if auth router is included
    routes = [route.path for route in api_router.routes]
    auth_routes = [route for route in routes if '/auth' in route]
    
    if auth_routes:
        print('✅ Auth routes found: ' + str(len(auth_routes)) + ' routes')
        for route in auth_routes[:3]:  # Show first 3
            print('   - ' + route)
    else:
        print('❌ No auth routes found!')
        sys.exit(1)
    
    # Check original routes still exist
    if '/health' in routes:
        print('✅ Health endpoint preserved')
    else:
        print('❌ Health endpoint missing!')
        sys.exit(1)
        
    if '/info' in routes:
        print('✅ Info endpoint preserved')
    else:
        print('❌ Info endpoint missing!')
        sys.exit(1)
    
    print('✅ All API Router tests passed!')
    
except Exception as e:
    print('❌ API Router test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

cd ..

echo ""
echo "🎉 ALL AUTHENTICATION TESTS PASSED!"
echo "===================================="
echo ""
echo "✅ Security Manager Working"
echo "✅ Configuration Working"  
echo "✅ Dependencies Working"
echo "✅ Auth Service Working"
echo "✅ API Router Working (api_v1 compatible)"
echo "✅ Original endpoints preserved"
echo ""
echo "📅 Day 4 - Phase 2 Progress:"
echo "  ✅ Authentication System - COMPLETED"
echo "  ✅ Compatible with existing api_v1 structure"
echo "  🔄 CRUD API Endpoints - NEXT"
echo ""
echo "🚀 Ready for Phase 3: CRUD API Endpoints Implementation!"