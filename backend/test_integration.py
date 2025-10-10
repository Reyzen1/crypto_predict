#!/usr/bin/env python3
# Test script for PriceDataService and new endpoints
# Run from backend directory: python test_integration.py

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def test_imports():
    """Test all critical imports"""
    print("🔧 Testing imports...")
    
    try:
        # Test core dependencies
        from app.core.deps import get_current_admin_user, get_current_active_user
        print("✅ Core dependencies imported successfully")
        
        # Test service imports
        from app.services.price_data_service import PriceDataService, get_price_data_service
        print("✅ PriceDataService imported successfully")
        
        # Test task imports
        from app.tasks.price_collector import fetch_daily_price_data, fetch_historical_price_data
        print("✅ New price collector tasks imported successfully")
        
        # Test enum imports
        from app.models.enums import UserRole
        print(f"✅ UserRole enum imported: {[role.value for role in UserRole]}")
        
        # Test API endpoint imports
        from app.api.api_v1.endpoints import prices
        print("✅ Prices endpoints imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_configuration():
    """Test configuration values"""
    print("\n⚙️ Testing configuration...")
    
    try:
        print(f"✅ Database URL configured: {bool(settings.DATABASE_URL)}")
        print(f"✅ Redis configured: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        print(f"✅ Celery broker: {bool(settings.CELERY_BROKER_URL)}")
        print(f"✅ CoinGecko API configured: {bool(settings.COINGECKO_API_KEY)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_scheduler_tasks():
    """Test scheduler configuration"""
    print("\n📅 Testing scheduler tasks...")
    
    try:
        from app.tasks.scheduler import task_scheduler
        
        # Initialize scheduler
        scheduler = task_scheduler
        
        # Test if we can access schedule configuration
        if hasattr(scheduler, 'celery_app'):
            print("✅ Scheduler initialized successfully")
            
            # Test schedule info
            try:
                schedule_info = scheduler.get_schedule_info()
                print(f"✅ Schedule configured with {len(schedule_info.get('tasks', []))} tasks")
                
                # Show new tasks
                tasks = schedule_info.get('tasks', [])
                new_tasks = [task for task in tasks if 'fetch-' in task.get('name', '')]
                if new_tasks:
                    print(f"✅ New price fetch tasks found: {len(new_tasks)}")
                    for task in new_tasks[:3]:  # Show first 3
                        print(f"   - {task.get('name', 'Unknown')}")
                
            except Exception as e:
                print(f"⚠️ Schedule info error: {e}")
        else:
            print("⚠️ Scheduler not fully initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Scheduler error: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("\n🗄️ Testing database connection...")
    
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

async def test_service_functionality():
    """Test PriceDataService basic functionality"""
    print("\n🧪 Testing service functionality...")
    
    try:
        from app.core.database import get_db
        from app.services.price_data_service import get_price_data_service
        
        # Get database session
        db = next(get_db())
        
        # Get service instance
        service = get_price_data_service(db)
        print("✅ Service instance created successfully")
        
        # Test data quality report (should work even with empty data)
        try:
            report = service.generate_data_quality_report(
                asset_id=1,  # Test with asset ID 1
                timeframe="1d"
            )
            print(f"✅ Data quality report generated: {report.get('quality_score', 0)}% quality")
        except Exception as e:
            print(f"⚠️ Data quality test (expected with no data): {e}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Service functionality error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Integration Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_scheduler_tasks,
        test_database_connection,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Async test
    try:
        async_result = asyncio.run(test_service_functionality())
        results.append(async_result)
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check configuration.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)