# File: ./scripts/test-schemas.sh
# Test Pydantic schemas validation and structure

#!/bin/bash

set -e

echo "🧪 Testing Pydantic Schemas"
echo "==========================="

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
echo "📋 Test 1: Schema Import Test"
echo "-----------------------------"
python -c "
try:
    from app.schemas import (
        # Common schemas
        BaseSchema, PaginationParams, SuccessResponse, ErrorResponse,
        # User schemas  
        UserRegister, UserLogin, UserResponse, Token,
        # Cryptocurrency schemas
        CryptocurrencyCreate, CryptocurrencyResponse, MarketData,
        # Price data schemas
        PriceDataCreate, PriceDataResponse, OHLCV,
        # Prediction schemas
        PredictionCreate, PredictionResponse, PredictionRequest
    )
    print('✅ All schemas imported successfully')
    print('   - Common schemas: BaseSchema, PaginationParams, etc.')
    print('   - User schemas: UserRegister, UserLogin, etc.')
    print('   - Crypto schemas: CryptocurrencyCreate, etc.')
    print('   - Price schemas: PriceDataCreate, OHLCV, etc.')
    print('   - Prediction schemas: PredictionCreate, etc.')
except Exception as e:
    print('❌ Schema import failed: ' + str(e))
    import sys
    sys.exit(1)
"

echo ""
echo "📋 Test 2: User Schema Validation"
echo "---------------------------------"
python -c "
from app.schemas import UserRegister, UserLogin, UserResponse
from pydantic import ValidationError
import sys

try:
    print('Testing User Registration Schema...')
    
    # Valid user registration
    valid_user = UserRegister(
        email='test@example.com',
        password='TestPass123',
        confirm_password='TestPass123',
        first_name='John',
        last_name='Doe'
    )
    print('✅ Valid user registration schema works')
    
    # Test password validation
    try:
        invalid_user = UserRegister(
            email='test@example.com',
            password='weak',  # Too weak
            confirm_password='weak',
            first_name='John'
        )
        print('❌ Password validation failed - should reject weak password')
        sys.exit(1)
    except ValidationError:
        print('✅ Password validation working - rejected weak password')
    
    # Test password mismatch
    try:
        mismatch_user = UserRegister(
            email='test@example.com',
            password='TestPass123',
            confirm_password='DifferentPass123',
            first_name='John'
        )
        print('❌ Password mismatch validation failed')
        sys.exit(1)
    except ValidationError:
        print('✅ Password mismatch validation working')
    
    # Test user login schema
    login_data = UserLogin(
        email='test@example.com',
        password='TestPass123'
    )
    print('✅ User login schema works')
    
    print()
    print('✅ All User Schema tests passed!')
    
except Exception as e:
    print('❌ User schema test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "📋 Test 3: Cryptocurrency Schema Validation"
echo "-------------------------------------------"
python -c "
from app.schemas import CryptocurrencyCreate, CryptocurrencyResponse
from pydantic import ValidationError
from datetime import datetime
import sys

try:
    print('Testing Cryptocurrency Schema...')
    
    # Valid cryptocurrency creation
    valid_crypto = CryptocurrencyCreate(
        symbol='BTC',
        name='Bitcoin',
        coingecko_id='bitcoin',
        binance_symbol='BTCUSDT'
    )
    print('✅ Valid cryptocurrency creation schema works')
    print('   Symbol: ' + valid_crypto.symbol)
    print('   Name: ' + valid_crypto.name)
    
    # Test symbol validation (should be uppercase)
    lowercase_crypto = CryptocurrencyCreate(
        symbol='eth',  # Should be converted to uppercase
        name='Ethereum'
    )
    if lowercase_crypto.symbol == 'ETH':
        print('✅ Symbol uppercase conversion working')
    else:
        print('❌ Symbol uppercase conversion failed')
        sys.exit(1)
    
    # Test invalid symbol
    try:
        invalid_crypto = CryptocurrencyCreate(
            symbol='BTC-USD',  # Invalid characters
            name='Bitcoin'
        )
        print('❌ Symbol validation failed - should reject invalid characters')
        sys.exit(1)
    except ValidationError:
        print('✅ Symbol validation working - rejected invalid characters')
    
    print()
    print('✅ All Cryptocurrency Schema tests passed!')
    
except Exception as e:
    print('❌ Cryptocurrency schema test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "📋 Test 4: Price Data Schema Validation"
echo "---------------------------------------"
python -c "
from app.schemas import PriceDataCreate, OHLCV
from pydantic import ValidationError
from datetime import datetime, timezone
from decimal import Decimal
import sys

try:
    print('Testing Price Data Schema...')
    
    # Valid price data
    valid_price = PriceDataCreate(
        crypto_id=1,
        timestamp=datetime.now(timezone.utc),
        open_price=Decimal('50000.00'),
        high_price=Decimal('51000.00'),
        low_price=Decimal('49000.00'),
        close_price=Decimal('50500.00'),
        volume=Decimal('1000000.00')
    )
    print('✅ Valid price data schema works')
    print('   Open: ' + str(valid_price.open_price))
    print('   High: ' + str(valid_price.high_price))
    print('   Low: ' + str(valid_price.low_price))
    print('   Close: ' + str(valid_price.close_price))
    
    # Test OHLCV schema
    ohlcv_data = OHLCV(
        timestamp=datetime.now(timezone.utc),
        open=Decimal('50000.00'),
        high=Decimal('51000.00'),
        low=Decimal('49000.00'),
        close=Decimal('50500.00'),
        volume=Decimal('1000000.00')
    )
    print('✅ OHLCV schema works')
    
    # Test invalid price relationship (high < low)
    try:
        invalid_price = PriceDataCreate(
            crypto_id=1,
            timestamp=datetime.now(timezone.utc),
            open_price=Decimal('50000.00'),
            high_price=Decimal('49000.00'),  # High < Low (invalid)
            low_price=Decimal('51000.00'),
            close_price=Decimal('50500.00')
        )
        print('❌ Price validation failed - should reject high < low')
        sys.exit(1)
    except ValidationError:
        print('✅ Price validation working - rejected high < low')
    
    print()
    print('✅ All Price Data Schema tests passed!')
    
except Exception as e:
    print('❌ Price data schema test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "📋 Test 5: Prediction Schema Validation"
echo "---------------------------------------"
python -c "
from app.schemas import PredictionCreate, PredictionRequest
from pydantic import ValidationError
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import sys

try:
    print('Testing Prediction Schema...')
    
    # Valid prediction
    future_date = datetime.now(timezone.utc) + timedelta(days=7)
    valid_prediction = PredictionCreate(
        user_id=1,
        crypto_id=1,
        model_name='LSTM_v1',
        predicted_price=Decimal('55000.00'),
        confidence_score=Decimal('0.85'),
        target_date=future_date,
        features_used='{\"features\": [\"open\", \"high\", \"low\", \"close\", \"volume\"]}'
    )
    print('✅ Valid prediction schema works')
    print('   Model: ' + valid_prediction.model_name)
    print('   Price: ' + str(valid_prediction.predicted_price))
    print('   Confidence: ' + str(valid_prediction.confidence_score))
    
    # Test prediction request
    pred_request = PredictionRequest(
        crypto_id=1,
        prediction_horizon=7,
        model_type='LSTM'
    )
    print('✅ Prediction request schema works')
    
    # Test invalid target date (past date)
    try:
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        invalid_prediction = PredictionCreate(
            user_id=1,
            crypto_id=1,
            model_name='LSTM_v1',
            predicted_price=Decimal('55000.00'),
            target_date=past_date  # Past date (invalid)
        )
        print('❌ Date validation failed - should reject past dates')
        sys.exit(1)
    except ValidationError:
        print('✅ Date validation working - rejected past date')
    
    # Test invalid model type
    try:
        invalid_request = PredictionRequest(
            crypto_id=1,
            prediction_horizon=7,
            model_type='INVALID_MODEL'
        )
        print('❌ Model validation failed - should reject invalid model')
        sys.exit(1)
    except ValidationError:
        print('✅ Model validation working - rejected invalid model type')
    
    print()
    print('✅ All Prediction Schema tests passed!')
    
except Exception as e:
    print('❌ Prediction schema test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "📋 Test 6: Common Schema Validation"
echo "-----------------------------------"
python -c "
from app.schemas import PaginationParams, SuccessResponse, ErrorResponse
from pydantic import ValidationError
import sys

try:
    print('Testing Common Schemas...')
    
    # Test pagination
    pagination = PaginationParams(
        skip=0,
        limit=50,
        order_by='created_at',
        order_desc=True
    )
    print('✅ Pagination schema works')
    print('   Skip: ' + str(pagination.skip))
    print('   Limit: ' + str(pagination.limit))
    
    # Test success response
    success = SuccessResponse(
        message='Operation completed successfully',
        data={'id': 123, 'status': 'active'}
    )
    print('✅ Success response schema works')
    
    # Test error response
    error = ErrorResponse(
        error='ValidationError',
        message='Invalid input data',
        details={'field': 'email', 'issue': 'invalid format'}
    )
    print('✅ Error response schema works')
    
    # Test invalid pagination (negative skip)
    try:
        invalid_pagination = PaginationParams(
            skip=-1,  # Invalid negative value
            limit=50
        )
        print('❌ Pagination validation failed - should reject negative skip')
        sys.exit(1)
    except ValidationError:
        print('✅ Pagination validation working - rejected negative skip')
    
    print()
    print('✅ All Common Schema tests passed!')
    
except Exception as e:
    print('❌ Common schema test failed: ' + str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

cd ..

echo ""
echo "🎉 ALL SCHEMA TESTS PASSED!"
echo "==========================="
echo ""
echo "✅ Schema Import Working"
echo "✅ User Schema Validation Working"
echo "✅ Cryptocurrency Schema Validation Working"
echo "✅ Price Data Schema Validation Working"
echo "✅ Prediction Schema Validation Working"
echo "✅ Common Schema Validation Working"
echo ""
echo "📅 Day 4 - Morning Progress:"
echo "  ✅ Pydantic Schemas - COMPLETED"
echo "  🔄 JWT Authentication - NEXT"
echo ""
echo "🚀 Ready for Authentication System Implementation!"