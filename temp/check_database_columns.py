# File: temp/check_database_columns.py
# Check what columns actually exist in your database

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import text, inspect
from app.core.database import engine, SessionLocal

def check_table_columns():
    """Check what columns exist in price_data table"""
    print("🔍 Checking actual database columns...")
    
    # Method 1: Using inspector
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📊 Available tables: {tables}")
        
        if 'price_data' in tables:
            columns = inspector.get_columns('price_data')
            print(f"\n📋 price_data table columns:")
            for i, col in enumerate(columns, 1):
                print(f"   {i:2d}. {col['name']:<20} | {col['type']}")
        else:
            print("❌ price_data table does not exist")
            
    except Exception as e:
        print(f"❌ Inspector method failed: {e}")
    
    # Method 2: Using raw SQL query
    try:
        db = SessionLocal()
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'price_data' 
            ORDER BY ordinal_position
        """))
        
        print(f"\n📋 SQL query results:")
        for i, row in enumerate(result.fetchall(), 1):
            print(f"   {i:2d}. {row[0]:<20} | {row[1]:<15} | nullable: {row[2]}")
            
        db.close()
        
    except Exception as e:
        print(f"❌ SQL query method failed: {e}")

if __name__ == "__main__":
    check_table_columns()