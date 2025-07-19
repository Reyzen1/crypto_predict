#!/bin/bash
# File: scripts/check-tables.sh
# Check existing database tables and their schema

set -e

echo "🔍 Checking Database Tables and Schema"
echo "======================================"

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

# Check tables
echo "📋 Checking existing tables..."
python -c "
import psycopg2
import sys

try:
    conn = psycopg2.connect('postgresql://postgres:postgres123@localhost:5432/cryptopredict')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute('''
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    ''')
    
    tables = cursor.fetchall()
    
    if tables:
        print('📊 Existing tables:')
        for table in tables:
            print(f'  - {table[0]}')
        print()
        
        # Check users table schema
        cursor.execute('''
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        ''')
        
        users_columns = cursor.fetchall()
        if users_columns:
            print('👤 Users table schema:')
            for col in users_columns:
                print(f'  - {col[0]}: {col[1]} (nullable: {col[2]})')
        else:
            print('⚠️ Users table not found')
    else:
        print('⚠️ No tables found in database')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error checking database: {e}')
    sys.exit(1)
"

echo ""
echo "💡 If you see integer types but models use UUID, run:"
echo "   ./scripts/reset-db.sh"
echo ""
echo "💡 If you see UUID types, run:"
echo "   ./scripts/setup-db.sh"

cd ..