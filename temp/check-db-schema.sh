# File: ./scripts/check-db-schema.sh
# Check current database schema to identify UUID vs Integer conflict

#!/bin/bash

set -e

echo "🔍 Checking Database Schema"
echo "=========================="

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

# Check table schemas
echo "📋 Checking table schemas..."
python -c "
import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:postgres123@localhost:5432/cryptopredict')
    cursor = conn.cursor()
    
    # Check users table schema
    cursor.execute('''
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    ''')
    
    users_columns = cursor.fetchall()
    if users_columns:
        print('👤 Users table schema:')
        for col in users_columns:
            print(f'   {col[0]}: {col[1]} (nullable: {col[3]})')
            if col[0] == 'id':
                if 'uuid' in col[1].lower():
                    print('   ⚠️  ID field is UUID type!')
                elif 'integer' in col[1].lower() or 'serial' in col[1].lower():
                    print('   ✅ ID field is Integer type!')
        print()
    
    # Check cryptocurrencies table schema
    cursor.execute('''
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'cryptocurrencies'
        ORDER BY ordinal_position
    ''')
    
    crypto_columns = cursor.fetchall()
    if crypto_columns:
        print('💰 Cryptocurrencies table schema:')
        for col in crypto_columns:
            print(f'   {col[0]}: {col[1]} (nullable: {col[3]})')
            if col[0] == 'id':
                if 'uuid' in col[1].lower():
                    print('   ⚠️  ID field is UUID type!')
                elif 'integer' in col[1].lower() or 'serial' in col[1].lower():
                    print('   ✅ ID field is Integer type!')
        print()
    
    # Check for any UUID columns in any table
    cursor.execute('''
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE data_type = 'uuid'
        ORDER BY table_name, column_name
    ''')
    
    uuid_columns = cursor.fetchall()
    if uuid_columns:
        print('🆔 Tables with UUID columns:')
        for col in uuid_columns:
            print(f'   {col[0]}.{col[1]}: {col[2]}')
        print()
        print('❌ CONFLICT DETECTED: Database uses UUID but models use Integer!')
    else:
        print('✅ No UUID columns found - Database uses Integer IDs')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error checking database schema: {e}')
    sys.exit(1)
"

cd ..

echo ""
echo "💡 Next steps:"
echo "  If UUID detected: Need to update models to use UUID"
echo "  If Integer detected: Database and models are compatible"