# temp/debug_workers.py
"""
Debug script to find why workers are stopping
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_basic_imports():
    """Test all basic imports that workers need"""
    print("🧪 Testing Basic Imports...")
    print("=" * 40)
    
    imports_to_test = [
        ("celery", "import celery"),
        ("nest_asyncio", "import nest_asyncio"),
        ("asyncio", "import asyncio"),
        ("redis", "import redis"),
        ("sqlalchemy", "import sqlalchemy"),
        ("task_handler", "from app.tasks.task_handler import AsyncTaskHandler"),
        ("celery_app", "from app.tasks.celery_app import celery_app"),
        ("price_collector", "from app.tasks.price_collector import sync_all_prices"),
        ("database", "from app.core.database import SessionLocal"),
        ("config", "from app.core.config import settings")
    ]
    
    failed_imports = []
    
    for name, import_stmt in imports_to_test:
        try:
            exec(import_stmt)
            print(f"✅ {name}: OK")
        except ImportError as e:
            print(f"❌ {name}: ImportError - {e}")
            failed_imports.append((name, str(e)))
        except Exception as e:
            print(f"⚠️ {name}: Other Error - {e}")
            failed_imports.append((name, str(e)))
    
    return failed_imports


def test_database_connection():
    """Test database connection"""
    print("\n🗄️ Testing Database Connection...")
    print("=" * 40)
    
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        # Try a simple query
        result = db.execute("SELECT 1").fetchone()
        if result:
            print("✅ Database connection: OK")
            db.close()
            return True
        else:
            print("❌ Database connection: No result")
            db.close()
            return False
            
    except Exception as e:
        print(f"❌ Database connection: {e}")
        return False


def test_redis_connection():
    """Test Redis connection"""
    print("\n🔴 Testing Redis Connection...")
    print("=" * 40)
    
    try:
        import redis
        from app.core.config import settings
        
        # Try to connect to Redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        print("✅ Redis connection: OK")
        return True
        
    except Exception as e:
        print(f"❌ Redis connection: {e}")
        return False


def test_async_functionality():
    """Test async functionality with nest_asyncio"""
    print("\n⚡ Testing Async Functionality...")
    print("=" * 40)
    
    try:
        import asyncio
        import nest_asyncio
        
        # Apply nest_asyncio
        nest_asyncio.apply()
        print("✅ nest_asyncio applied")
        
        # Test async function
        async def test_async():
            await asyncio.sleep(0.01)
            return "success"
        
        # Test execution
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(test_async())
        loop.close()
        
        if result == "success":
            print("✅ Async execution: OK")
            return True
        else:
            print("❌ Async execution: Failed")
            return False
            
    except Exception as e:
        print(f"❌ Async functionality: {e}")
        return False


def test_celery_worker_start():
    """Test if Celery worker can start without actually running it"""
    print("\n🔧 Testing Celery Worker Configuration...")
    print("=" * 40)
    
    try:
        from app.tasks.celery_app import celery_app
        
        # Check if app is configured properly
        print(f"✅ Celery app created: {celery_app.main}")
        print(f"✅ Broker URL: {celery_app.conf.broker_url}")
        print(f"✅ Result backend: {celery_app.conf.result_backend}")
        
        # Check if tasks are registered
        registered_tasks = list(celery_app.tasks.keys())
        print(f"✅ Registered tasks: {len(registered_tasks)}")
        
        # Look for our tasks
        our_tasks = [task for task in registered_tasks if 'price_collector' in task]
        print(f"✅ Price collector tasks: {len(our_tasks)}")
        
        if our_tasks:
            print("   Found tasks:", our_tasks)
        
        return True
        
    except Exception as e:
        print(f"❌ Celery worker configuration: {e}")
        return False


def test_task_execution():
    """Test if a simple task can be created (not executed)"""
    print("\n🎯 Testing Task Creation...")
    print("=" * 40)
    
    try:
        from app.tasks.price_collector import sync_all_prices
        
        # Just check if the task object exists
        print(f"✅ sync_all_prices task: {sync_all_prices}")
        print(f"✅ Task name: {sync_all_prices.name}")
        
        # Try to create a task signature (don't execute)
        sig = sync_all_prices.s()
        print(f"✅ Task signature created: {sig}")
        
        return True
        
    except Exception as e:
        print(f"❌ Task creation: {e}")
        return False


def main():
    """Run all diagnostic tests"""
    print("🚀 Worker Diagnostic Test")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Database Connection", test_database_connection),
        ("Redis Connection", test_redis_connection),
        ("Async Functionality", test_async_functionality),
        ("Celery Configuration", test_celery_worker_start),
        ("Task Creation", test_task_execution)
    ]
    
    results = []
    failed_imports = []
    
    for test_name, test_func in tests:
        try:
            if test_name == "Basic Imports":
                result = test_func()
                failed_imports = result
                test_passed = len(result) == 0
                results.append((test_name, test_passed))
            else:
                result = test_func()
                results.append((test_name, result))
        except Exception as e:
            print(f"CRASH: {test_name} test crashed - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🔍 DIAGNOSTIC RESULTS")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    # Show failed imports if any
    if failed_imports:
        print(f"\n❌ Failed Imports ({len(failed_imports)}):")
        for name, error in failed_imports:
            print(f"   • {name}: {error}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    # Recommendations
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Workers should be able to start. The issue might be:")
        print("1. Worker timeout during startup")
        print("2. Memory limits")
        print("3. Port conflicts")
        print("\n🔧 Try:")
        print("   • Check worker logs in detail")
        print("   • Start workers individually")
        print("   • Increase startup timeout")
        
    elif passed >= total * 0.7:
        print("\n⚠️ MOSTLY WORKING - Some issues detected")
        print("🔧 Focus on fixing the failed tests above")
        
    else:
        print("\n❌ MAJOR ISSUES DETECTED")
        print("🚨 Critical problems found. Address failed tests first.")
    
    return passed >= total * 0.7


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)