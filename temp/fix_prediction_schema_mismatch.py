# File: temp/fix_prediction_schema_mismatch.py
# Fix prediction schema and database mismatches

def fix_prediction_schema():
    """Fix the mismatch between schema and database model"""
    
    schema_file = 'backend/app/schemas/prediction.py'
    
    try:
        print("🔧 Fixing prediction schema...")
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        fixes_applied = 0
        
        # Fix 1: Change target_date to target_datetime in PredictionBase
        old_pattern1 = 'target_date: datetime = Field(description="Date/time the prediction is for")'
        new_pattern1 = 'target_datetime: datetime = Field(description="Date/time the prediction is for")'
        
        if old_pattern1 in content:
            content = content.replace(old_pattern1, new_pattern1)
            fixes_applied += 1
            print("✅ Fixed target_date to target_datetime in PredictionBase")
        
        # Fix 2: Update validator name
        old_validator = '@field_validator(\'target_date\')'
        new_validator = '@field_validator(\'target_datetime\')'
        
        if old_validator in content:
            content = content.replace(old_validator, new_validator)
            fixes_applied += 1
            print("✅ Fixed target_date validator")
        
        # Fix 3: Update validator function name
        old_func_name = 'def validate_target_date(cls, v):'
        new_func_name = 'def validate_target_datetime(cls, v):'
        
        if old_func_name in content:
            content = content.replace(old_func_name, new_func_name)
            fixes_applied += 1
            print("✅ Fixed validator function name")
        
        # Fix 4: Update error message
        old_error = 'raise ValueError(\'Target date must be in the future\')'
        new_error = 'raise ValueError(\'Target datetime must be in the future\')'
        
        if old_error in content:
            content = content.replace(old_error, new_error)
            fixes_applied += 1
            print("✅ Fixed error message")
        
        # Fix 5: Fix other target_date references
        content = content.replace('target_date: datetime', 'target_datetime: datetime')
        content = content.replace('"Prediction target date"', '"Prediction target datetime"')
        
        if fixes_applied > 0:
            with open(schema_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Applied {fixes_applied} fixes to prediction schema")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing schema: {e}")
        return False

def run_migration_for_model_version():
    """Create and run migration to add model_version column"""
    
    migration_content = '''"""Add model_version column to predictions table

Revision ID: add_model_version_001
Revises: 
Create Date: 2025-07-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_model_version_001'
down_revision = None
depends_on = None

def upgrade():
    """Add model_version column if it doesn't exist"""
    
    # Check if column exists first
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [column['name'] for column in inspector.get_columns('predictions')]
    
    if 'model_version' not in columns:
        print("Adding model_version column...")
        op.add_column('predictions', 
                     sa.Column('model_version', sa.String(20), 
                              nullable=False, 
                              server_default='1.0'))
        print("✅ model_version column added successfully")
    else:
        print("✅ model_version column already exists")

def downgrade():
    """Remove model_version column"""
    op.drop_column('predictions', 'model_version')
'''
    
    # Create migration file
    migration_file = 'backend/alembic/versions/add_model_version_001.py'
    
    try:
        with open(migration_file, 'w', encoding='utf-8') as f:
            f.write(migration_content)
        print(f"✅ Created migration file: {migration_file}")
        
        # Instructions for running migration
        print("\n📋 To apply the migration:")
        print("cd backend")
        print("alembic upgrade head")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating migration: {e}")
        return False

def create_quick_database_fix():
    """Create a quick SQL script to fix database issues"""
    
    sql_script = '''-- Quick fix for prediction table issues
-- File: temp/fix_prediction_table.sql

-- Add model_version column if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'predictions' 
        AND column_name = 'model_version'
    ) THEN
        ALTER TABLE predictions 
        ADD COLUMN model_version VARCHAR(20) NOT NULL DEFAULT '1.0';
        
        COMMENT ON COLUMN predictions.model_version IS 'Version of the ML model used';
        
        RAISE NOTICE 'Added model_version column to predictions table';
    ELSE
        RAISE NOTICE 'model_version column already exists';
    END IF;
END $$;

-- Verify the fix
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'predictions' 
AND column_name = 'model_version';
'''
    
    with open('temp/fix_prediction_table.sql', 'w', encoding='utf-8') as f:
        f.write(sql_script)
    
    print("✅ Created SQL fix script: temp/fix_prediction_table.sql")
    print("\n📋 To apply manually:")
    print("1. Connect to your PostgreSQL database")
    print("2. Run: \\i temp/fix_prediction_table.sql")
    print("3. Or copy-paste the SQL commands")

def test_prediction_creation():
    """Test prediction creation after fixes"""
    
    test_code = '''# File: temp/test_prediction_fix.py
# Test prediction creation after schema fix

import sys
import os
from datetime import datetime, timezone, timedelta

# Add backend path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

def test_prediction_schema():
    """Test if prediction schema works correctly"""
    
    try:
        from app.schemas.prediction import PredictionCreate
        from decimal import Decimal
        
        # Test data
        prediction_data = {
            'crypto_id': 1,
            'user_id': 1,
            'model_name': 'LSTM_test',
            'predicted_price': Decimal('50000.00'),
            'confidence_score': Decimal('0.85'),
            'target_datetime': datetime.now(timezone.utc) + timedelta(hours=24),
            'features_used': '{"feature1": "value1"}'
        }
        
        # Try to create prediction schema
        prediction = PredictionCreate(**prediction_data)
        
        print("✅ PredictionCreate schema works!")
        print(f"   - target_datetime: {prediction.target_datetime}")
        print(f"   - predicted_price: {prediction.predicted_price}")
        print(f"   - confidence_score: {prediction.confidence_score}")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Prediction Schema Fix")
    print("=" * 40)
    test_prediction_schema()
'''
    
    with open('temp/test_prediction_fix.py', 'w', encoding='utf-8') as f:
        f.write(test_code)
    
    print("✅ Created test script: temp/test_prediction_fix.py")

if __name__ == "__main__":
    print("🚀 Fixing Prediction Schema and Database Issues")
    print("=" * 50)
    
    # Fix 1: Schema issues
    if fix_prediction_schema():
        print("\n✅ Schema fixes applied")
    
    # Fix 2: Database migration
    print("\n📋 Database fixes:")
    run_migration_for_model_version()
    create_quick_database_fix()
    
    # Create test
    print("\n🧪 Testing:")
    create_quick_database_fix()
    test_prediction_creation()
    
    print("\n🎯 Next steps:")
    print("1. Run: python temp/test_prediction_fix.py")
    print("2. Apply database fix (choose one):")
    print("   - cd backend && alembic upgrade head")
    print("   - Or run the SQL script manually")
    print("3. Test: cd backend && python ../temp/test_complete_ml_pipeline.py")