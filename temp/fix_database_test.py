# temp/fix_database_test.py
"""
Quick fix for database connection test
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_fixed_database():
    """Test database with proper SQLAlchemy syntax"""
    print("🗄️ Testing Fixed Database Connection...")
    print("=" * 40)
    
    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        
        # Use proper SQLAlchemy text() syntax
        result = db.execute(text("SELECT 1")).fetchone()
        
        if result:
            print("✅ Database connection: OK (Fixed)")
            db.close()
            return True
        else:
            print("❌ Database connection: No result")
            db.close()
            return False
            
    except Exception as e:
        print(f"❌ Database connection: {e}")
        return False

def test_worker_startup_simulation():
    """Simulate what happens when worker starts"""
    print("\n🚀 Simulating Worker Startup...")
    print("=" * 40)
    
    try:
        # Step 1: Import celery app
        from app.tasks.celery_app import celery_app
        print("✅ Step 1: Celery app imported")
        
        # Step 2: Check broker connection
        broker_url = celery_app.conf.broker_url
        print(f"✅ Step 2: Broker URL: {broker_url}")
        
        # Step 3: Test Redis connection
        import redis
        r = redis.from_url(broker_url)
        r.ping()
        print("✅ Step 3: Redis broker connected")
        
        # Step 4: Import tasks
        from app.tasks.price_collector import sync_all_prices
        print("✅ Step 4: Tasks imported")
        
        # Step 5: Test database with proper syntax
        from app.core.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ Step 5: Database connected (fixed)")
        
        # Step 6: Test services
        from app.services.data_sync import DataSyncService
        data_sync = DataSyncService()
        print("✅ Step 6: Services initialized")
        
        print("\n🎉 Worker startup simulation: SUCCESS")
        print("Workers should be able to start now!")
        return True
        
    except Exception as e:
        print(f"❌ Worker startup failed at: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Database Fix Test")
    print("=" * 50)
    
    db_ok = test_fixed_database()
    worker_ok = test_worker_startup_simulation()
    
    if db_ok and worker_ok:
        print("\n✅ ALL FIXED!")
        print("🚀 Now try: ./scripts/run-workers-simple-kill-all.sh")
    else:
        print("\n❌ Still has issues")
        print("🔧 Need more investigation")