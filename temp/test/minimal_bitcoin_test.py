#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal Bitcoin Test

Simple test script that checks basic connectivity and database access
without complex service imports.
"""

import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def minimal_bitcoin_test():
    """Minimal Bitcoin test without service dependencies"""
    
    try:
        print("🚀 Starting minimal Bitcoin test...")
        
        # Check if we're in virtual environment
        venv_indicator = sys.prefix != sys.base_prefix
        if not venv_indicator:
            print("⚠️  Virtual environment is not active, please activate it first:")
            print("   Windows: backend\\venv\\Scripts\\activate")
            print("   Linux/Mac: source backend/venv/bin/activate")
        
        # Get database URL
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            # Try to load from .env file
            env_path = Path('../../backend/.env')
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith('DATABASE_URL='):
                            db_url = line.strip().split('=', 1)[1].strip('"\'')
                            break
        
        if not db_url:
            print("❌ DATABASE_URL not found")
            print("💡 Please set DATABASE_URL in backend/.env file")
            return False
        
        print(f"   📊 Database URL: {db_url[:50]}...")
        
        # Test database connection
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(bind=engine)
        
        with SessionLocal() as session:
            # Test basic query
            result = session.execute(text("SELECT 1 as test")).fetchone()
            print(f"✅ Database connection successful: {result[0]}")
            
            # Check if assets table exists
            try:
                result = session.execute(text("SELECT COUNT(*) FROM assets")).fetchone()
                print(f"✅ Assets table found with {result[0]} records")
                
                # Check for Bitcoin
                result = session.execute(text("SELECT * FROM assets WHERE symbol = 'BTC' LIMIT 1")).fetchone()
                if result:
                    print(f"✅ Bitcoin found in database: ID={result[0]}")
                else:
                    print("ℹ️  Bitcoin not found in assets table")
                    
            except Exception as e:
                print(f"⚠️  Assets table not accessible: {e}")
        
        engine.dispose()
        print("🎉 Minimal test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    minimal_bitcoin_test()