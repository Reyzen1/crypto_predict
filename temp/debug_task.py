# File: temp/debug_task.py
# Debug script to test individual task execution

import sys
import os
import asyncio
import traceback
from datetime import datetime

# Add backend to path
sys.path.append('backend')

def test_direct_task_execution():
    """
    Test task execution directly (without Celery)
    """
    print("🧪 Direct Task Execution Test")
    print("=" * 40)
    
    try:
        # Import the task function directly
        from app.tasks.price_collector import sync_all_prices
        
        print("✅ Task imported successfully")
        
        # Try to run the task logic directly
        print("🔄 Testing task execution...")
        
        # This should give us more detailed error info
        result = sync_all_prices()
        
        print(f"✅ Task completed successfully!")
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"❌ Task failed: {e}")
        print("📋 Full traceback:")
        traceback.print_exc()

def test_database_connection():
    """
    Test database connection from task context
    """
    print("\n🗄️ Database Connection Test")
    print("=" * 40)
    
    try:
        from app.core.database import engine, get_db
        from sqlalchemy import text
        
        # Test basic connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Check if tables exist
            result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            print(f"📊 Found {len(tables)} tables: {tables[:5]}...")
            
            # Check cryptocurrencies table
            if 'cryptocurrencies' in tables:
                result = connection.execute(text("SELECT COUNT(*) FROM cryptocurrencies"))
                count = result.scalar()
                print(f"💰 Cryptocurrencies in DB: {count}")
            else:
                print("⚠️ Cryptocurrencies table not found!")
                
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        traceback.print_exc()

def test_external_api():
    """
    Test external API connection
    """
    print("\n🌐 External API Test")
    print("=" * 40)
    
    try:
        import requests
        import time
        
        # Test CoinGecko API (simple ping)
        print("🔄 Testing CoinGecko API...")
        response = requests.get("https://api.coingecko.com/api/v3/ping", timeout=10)
        
        if response.status_code == 200:
            print("✅ CoinGecko API is accessible")
        else:
            print(f"⚠️ CoinGecko returned status: {response.status_code}")
            
        # Test simple price fetch
        print("🔄 Testing price fetch...")
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", 
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            btc_price = data.get('bitcoin', {}).get('usd')
            print(f"✅ Bitcoin price fetch successful: ${btc_price}")
        else:
            print(f"❌ Price fetch failed: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ API request timeout - network or API issue")
    except Exception as e:
        print(f"❌ API test failed: {e}")
        traceback.print_exc()

def test_redis_connection():
    """
    Test Redis connection
    """
    print("\n🔴 Redis Connection Test")
    print("=" * 40)
    
    try:
        import redis
        
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
        
        # Check queues
        queues = ['price_data', 'default', 'ml_tasks']
        for queue in queues:
            count = r.llen(queue)
            print(f"📊 Queue {queue}: {count} pending tasks")
            
        # Test write/read
        test_key = "test_worker_connection"
        r.set(test_key, f"test_{datetime.now()}", ex=60)
        value = r.get(test_key)
        
        if value:
            print("✅ Redis read/write test successful")
            r.delete(test_key)
        else:
            print("⚠️ Redis read/write test failed")
            
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        traceback.print_exc()

def comprehensive_system_test():
    """
    Run all tests
    """
    print("🔧 CryptoPredict System Diagnostic")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now()}")
    print()
    
    # Run all tests
    test_redis_connection()
    test_database_connection()
    test_external_api()
    test_direct_task_execution()
    
    print("\n" + "=" * 50)
    print("🏁 Diagnostic complete!")
    print()
    print("💡 Next steps based on results:")
    print("• If DB failed: Check PostgreSQL connection")
    print("• If API failed: Check internet/firewall")
    print("• If Redis failed: Check Redis server")
    print("• If task failed: Check specific error above")

if __name__ == "__main__":
    comprehensive_system_test()