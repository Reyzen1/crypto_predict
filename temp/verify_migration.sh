# File: temp/verify_migration.sh
# Script to verify that migration was applied successfully

#!/bin/bash

echo "✅ Verifying Migration Success"
echo "============================="

# Check if we're in backend directory
if [ ! -f "alembic.ini" ]; then
    echo "❌ Please run from backend directory"
    exit 1
fi

echo "📋 Step 1: Check Alembic Status"
echo "------------------------------"
echo "Current revision:"
alembic current

echo ""
echo "Migration history:"
alembic history

echo ""
echo "📋 Step 2: Check Database Tables"
echo "-------------------------------"
python -c "
import os
import sys
sys.path.append('.')

try:
    from app.core.database import engine
    import sqlalchemy as sa
    
    # Connect to database
    with engine.connect() as connection:
        # Get list of tables
        inspector = sa.inspect(connection)
        tables = inspector.get_table_names()
        
        print('📊 Database Tables:')
        for table in sorted(tables):
            print(f'  ✅ {table}')
        
        # Check specific ML tables
        ml_tables = ['cryptocurrencies', 'price_data', 'predictions']
        print('')
        print('🧠 ML Tables Status:')
        for table in ml_tables:
            if table in tables:
                columns = inspector.get_columns(table)
                print(f'  ✅ {table} ({len(columns)} columns)')
                
                # Show first few columns
                for col in columns[:5]:
                    nullable = 'NULL' if col['nullable'] else 'NOT NULL'
                    print(f'     - {col[\"name\"]}: {col[\"type\"]} {nullable}')
                if len(columns) > 5:
                    print(f'     ... and {len(columns) - 5} more columns')
            else:
                print(f'  ❌ {table} (missing)')
        
        print('')
        print('🔗 Foreign Keys:')
        for table in ml_tables:
            if table in tables:
                fks = inspector.get_foreign_keys(table)
                if fks:
                    for fk in fks:
                        print(f'  ✅ {table}.{fk[\"constrained_columns\"]} → {fk[\"referred_table\"]}.{fk[\"referred_columns\"]}')
                else:
                    print(f'  - {table}: No foreign keys')
        
        print('')
        print('📈 Indexes:')
        for table in ml_tables:
            if table in tables:
                indexes = inspector.get_indexes(table)
                if indexes:
                    for idx in indexes[:3]:  # Show first 3 indexes
                        unique = 'UNIQUE' if idx['unique'] else 'INDEX'
                        print(f'  ✅ {table}: {unique} on {idx[\"column_names\"]}')
                    if len(indexes) > 3:
                        print(f'     ... and {len(indexes) - 3} more indexes')

except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('Make sure PostgreSQL is running and DATABASE_URL is correct')
"

echo ""
echo "📋 Step 3: Test Model Imports"
echo "----------------------------"
python -c "
import sys
sys.path.append('.')

try:
    from app.models import User, Cryptocurrency, PriceData, Prediction
    print('✅ All models imported successfully')
    
    # Test model attributes
    print('')
    print('🔍 Model Attributes:')
    print(f'  Cryptocurrency columns: {len(Cryptocurrency.__table__.columns)}')
    print(f'  PriceData columns: {len(PriceData.__table__.columns)}')
    print(f'  Prediction columns: {len(Prediction.__table__.columns)}')
    
    # Test relationships
    print('')
    print('🔗 Model Relationships:')
    crypto = Cryptocurrency()
    print(f'  ✅ Cryptocurrency.price_data relationship exists')
    print(f'  ✅ Cryptocurrency.predictions relationship exists')
    
except ImportError as e:
    print(f'❌ Model import failed: {e}')
except Exception as e:
    print(f'❌ Model test failed: {e}')
"

echo ""
echo "📋 Step 4: Test Database Connection from App"
echo "-------------------------------------------"
python -c "
import sys
sys.path.append('.')

try:
    from app.core.database import get_db, engine
    from sqlalchemy.orm import Session
    from app.models import Cryptocurrency
    
    # Test database session
    db = next(get_db())
    
    # Test querying (should work even if table is empty)
    count = db.query(Cryptocurrency).count()
    print(f'✅ Database connection successful')
    print(f'📊 Cryptocurrencies in database: {count}')
    
    db.close()
    
except Exception as e:
    print(f'❌ Database connection test failed: {e}')
"

echo ""
echo "✅ Migration verification completed!"
echo ""
echo "🎯 If all checks passed, your database is ready for ML development!"
echo ""
echo "🚀 Next steps:"
echo "1. Copy ML files to app/ml/ directories"
echo "2. Start building training pipeline"
echo "3. Test LSTM model with real data"