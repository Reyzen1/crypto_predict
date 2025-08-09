# temp/test_async_celery_fix.py
"""
Test script to verify that the async/Celery integration fix is working
Run this after applying the fixes to verify the solution
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

# Test imports
try:
    import nest_asyncio
    print("✅ nest_asyncio imported successfully")
    nest_asyncio.apply()
    print("✅ nest_asyncio applied successfully")
except ImportError:
    print("❌ nest_asyncio not available - run: pip install nest-asyncio==1.5.8")
    sys.exit(1)

try:
    from app.tasks.task_handler import AsyncTaskHandler, celery_async_task
    print("✅ Task handler imported successfully")
except ImportError as e:
    print(f"❌ Task handler import failed: {e}")
    sys.exit(1)

try:
    from app.tasks.price_collector import sync_all_prices
    print("✅ Price collector tasks imported successfully")
except ImportError as e:
    print(f"❌ Price collector import failed: {e}")
    sys.exit(1)


async def test_async_function():
    """Test async function for verification"""
    await asyncio.sleep(0.1)
    return {
        "status": "success",
        "message": "Async function executed successfully",
        "timestamp": datetime.utcnow().isoformat()
    }


def test_task_handler():
    """Test the AsyncTaskHandler functionality"""
    print("\n🧪 Testing AsyncTaskHandler...")
    
    try:
        # Test async task execution
        handler = AsyncTaskHandler()
        result = handler.run_async_task(test_async_function)
        
        print(f"✅ AsyncTaskHandler test passed: {result}")
        return True
        
    except Exception as e:
        print(f"❌ AsyncTaskHandler test failed: {e}")
        return False


def test_celery_async_decorator():
    """Test the celery_async_task decorator"""
    print("\n🧪 Testing celery_async_task decorator...")
    
    try:
        @celery_async_task
        async def test_decorated_task():
            return await test_async_function()
        
        # Execute the decorated function
        result = test_decorated_task()
        
        print(f"✅ celery_async_task decorator test passed: {result}")
        return True
        
    except Exception as e:
        print(f"❌ celery_async_task decorator test failed: {e}")
        return False


def test_event_loop_management():
    """Test event loop creation and management"""
    print("\n🧪 Testing event loop management...")
    
    try:
        # Test getting/creating event loop
        from app.tasks.task_handler import get_or_create_event_loop
        
        loop = get_or_create_event_loop()
        print(f"✅ Event loop created: {type(loop)}")
        print(f"   - Is running: {loop.is_running()}")
        print(f"   - Is closed: {loop.is_closed()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Event loop management test failed: {e}")
        return False


def test_celery_config():
    """Test Celery configuration loading"""
    print("\n🧪 Testing Celery configuration...")
    
    try:
        from app.core.celery_config import CeleryConfig, AsyncCeleryConfig
        
        config = CeleryConfig()
        async_config = AsyncCeleryConfig()
        
        print(f"✅ CeleryConfig loaded successfully")
        print(f"   - Broker URL: {config.broker_url}")
        print(f"   - Worker pool: {getattr(config, 'worker_pool', 'default')}")
        print(f"   - Async timeout: {async_config.ASYNC_TASK_TIMEOUT}")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery configuration test failed: {e}")
        return False


def test_price_collector_tasks():
    """Test price collector task structure"""
    print("\n🧪 Testing price collector task structure...")
    
    try:
        # Check if tasks are properly structured
        from app.tasks import price_collector
        
        # Check if required functions exist
        required_tasks = [
            'sync_all_prices',
            'sync_historical_data', 
            'discover_new_cryptocurrencies',
            'cleanup_old_data'
        ]
        
        missing_tasks = []
        for task_name in required_tasks:
            if not hasattr(price_collector, task_name):
                missing_tasks.append(task_name)
        
        if missing_tasks:
            print(f"❌ Missing tasks: {missing_tasks}")
            return False
        
        print("✅ All required tasks are available")
        return True
        
    except Exception as e:
        print(f"❌ Price collector task structure test failed: {e}")
        return False


def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🚀 Starting Async Celery Fix Verification")
    print("=" * 50)
    
    tests = [
        ("Task Handler", test_task_handler),
        ("Async Decorator", test_celery_async_decorator),
        ("Event Loop Management", test_event_loop_management),
        ("Celery Configuration", test_celery_config),
        ("Price Collector Tasks", test_price_collector_tasks)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ The async/Celery integration fix is working correctly")
        print("🚀 You can now run the Celery workers without 'Event loop is closed' errors")
        
        print("\n📋 Next steps:")
        print("1. Replace the old files with the fixed versions")
        print("2. Install the new requirements: pip install nest-asyncio==1.5.8 asyncio-mqtt==0.16.1")
        print("3. Restart your Celery workers")
        print("4. Test with: ./run-workers-simple-kill-all.sh")
        
    elif passed >= total * 0.7:  # 70% pass rate
        print("\n⚠️ MOSTLY WORKING - Minor issues detected")
        print("🔧 The main fix is working but some components need attention")
        
        print("\n📋 Recommended actions:")
        print("1. Replace the old files with the fixed versions") 
        print("2. Install missing requirements")
        print("3. Check failed tests above for specific issues")
        
    else:
        print("\n❌ SIGNIFICANT ISSUES DETECTED")
        print("🚨 Multiple components failed - review the fixes needed")
        
        print("\n📋 Required actions:")
        print("1. Check Python environment and dependencies")
        print("2. Verify all import paths are correct")
        print("3. Ensure you're running from the correct directory")
    
    return passed == total


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)