# File: ./scripts/verify-schema-fix.sh
# Verify that schema conflict has been resolved successfully

#!/bin/bash

set -e

echo "🧪 Verifying Schema Fix"
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

echo ""
echo "📋 Test 1: Schema Consistency Check"
echo "-----------------------------------"
python -c "
import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:postgres123@localhost:5432/cryptopredict')
    cursor = conn.cursor()
    
    # Check all ID columns
    tables = ['users', 'cryptocurrencies', 'price_data', 'predictions', 'portfolios']
    all_integer = True
    
    print('ID Column Types:')
    for table in tables:
        cursor.execute('''
            SELECT data_type, udt_name 
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = 'id'
        ''', (table,))
        
        result = cursor.fetchone()
        if result:
            data_type, udt_name = result
            if 'integer' in data_type.lower() or 'serial' in udt_name.lower():
                print(f'✅ {table}: {data_type} ({udt_name})')
            else:
                print(f'❌ {table}: {data_type} ({udt_name}) - NOT INTEGER!')
                all_integer = False
        else:
            print(f'❌ {table}: ID column not found!')
            all_integer = False
    
    if all_integer:
        print('\\n✅ All tables use Integer IDs - Schema is consistent!')
    else:
        print('\\n❌ Schema inconsistency detected!')
        sys.exit(1)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Schema check failed: {e}')
    sys.exit(1)
"

echo ""
echo "📋 Test 2: Models Import and Compatibility"
echo "------------------------------------------"
python -c "
try:
    from app.models import User, Cryptocurrency, PriceData, Prediction, Portfolio
    from sqlalchemy import inspect
    
    # Check that all models have Integer primary keys
    models = [User, Cryptocurrency, PriceData, Prediction, Portfolio]
    
    for model in models:
        mapper = inspect(model)
        pk_columns = mapper.primary_key
        for pk in pk_columns:
            if hasattr(pk.type, 'python_type') and pk.type.python_type == int:
                print(f'✅ {model.__name__}: Integer primary key')
            else:
                print(f'❌ {model.__name__}: Non-integer primary key - {pk.type}')
                import sys
                sys.exit(1)
    
    print('\\n✅ All models use Integer primary keys!')
    
except Exception as e:
    print(f'❌ Models compatibility check failed: {e}')
    import sys
    sys.exit(1)
"

echo ""
echo "📋 Test 3: CRUD Operations Test"
echo "-------------------------------"
python -c "
from app.core.database import SessionLocal
from app.models import User, Cryptocurrency
from datetime import datetime, timezone
import sys

db = SessionLocal()

try:
    # Test basic CRUD operations
    print('Testing CRUD operations...')
    
    # CREATE - Test user creation
    test_user = User(
        email='test_schema@example.com',
        password_hash='test_hash',
        first_name='Schema',
        last_name='Test'
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    if isinstance(test_user.id, int):
        print(f'✅ User created with Integer ID: {test_user.id}')
    else:
        print(f'❌ User ID is not Integer: {type(test_user.id)}')
        sys.exit(1)
    
    # READ - Test cryptocurrency query
    btc = db.query(Cryptocurrency).filter(Cryptocurrency.symbol == 'BTC').first()
    if btc and isinstance(btc.id, int):
        print(f'✅ Bitcoin found with Integer ID: {btc.id}')
    else:
        print('❌ Bitcoin not found or ID is not Integer')
        sys.exit(1)
    
    # UPDATE - Test user update
    test_user.first_name = 'Updated'
    db.commit()
    
    updated_user = db.query(User).filter(User.id == test_user.id).first()
    if updated_user and updated_user.first_name == 'Updated':
        print('✅ User update successful')
    else:
        print('❌ User update failed')
        sys.exit(1)
    
    # DELETE - Clean up test data
    db.delete(test_user)
    db.commit()
    print('✅ Test data cleanup successful')
    
    print('\\n✅ All CRUD operations working correctly!')
    
except Exception as e:
    print(f'❌ CRUD operations test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
"

echo ""
echo "📋 Test 4: Relationships Test"
echo "-----------------------------"
python -c "
from app.models import User, Cryptocurrency, PriceData, Prediction, Portfolio
from sqlalchemy import inspect
import sys

try:
    # Test that relationships are properly defined
    models_relationships = {
        'User': ['predictions', 'portfolios'],
        'Cryptocurrency': ['price_data', 'predictions', 'portfolios'],
        'PriceData': ['cryptocurrency'],
        'Prediction': ['user', 'cryptocurrency'],
        'Portfolio': ['user', 'cryptocurrency']
    }
    
    for model_name, expected_rels in models_relationships.items():
        model = globals()[model_name]
        mapper = inspect(model)
        actual_rels = list(mapper.relationships.keys())
        
        for rel in expected_rels:
            if rel in actual_rels:
                print(f'✅ {model_name}.{rel} relationship exists')
            else:
                print(f'❌ {model_name}.{rel} relationship missing')
                sys.exit(1)
    
    print('\\n✅ All model relationships properly defined!')
    
except Exception as e:
    print(f'❌ Relationships test failed: {e}')
    sys.exit(1)
"

cd ..

echo ""
echo "🎉 SCHEMA FIX VERIFICATION COMPLETE!"
echo "===================================="
echo ""
echo "✅ Database uses Integer IDs consistently"
echo "✅ Models use Integer IDs consistently"  
echo "✅ CRUD operations working"
echo "✅ Model relationships working"
echo "✅ No more UUID vs Integer conflict"
echo ""
echo "🚀 Ready to continue with Day 3 development!"
echo ""
echo "📋 Day 3 Progress:"
echo "  ✅ Database Design (Morning) - COMPLETED"
echo "  🔄 CRUD Operations & Repository Patterns (Afternoon) - NEXT"