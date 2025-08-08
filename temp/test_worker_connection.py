# File: temp/test_worker_connection.py
# Quick diagnostic script to test Celery worker queue connection

import sys
import os
sys.path.append('backend')

from app.tasks.celery_app import celery_app
from app.tasks.price_collector import sync_all_prices
import redis

def test_worker_connection():
    """
    Test Celery worker connection and queue routing
    """
    
    print("🔍 CryptoPredict Worker Diagnostic")
    print("=" * 40)
    
    # Test 1: Redis Connection
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis: Connected")
    except Exception as e:
        print(f"❌ Redis: Failed - {e}")
        return
    
    # Test 2: Celery App Configuration
    try:
        print(f"✅ Broker: {celery_app.conf.broker_url}")
        print(f"✅ Backend: {celery_app.conf.result_backend}")
    except Exception as e:
        print(f"❌ Celery Config: {e}")
    
    # Test 3: Check Active Workers
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        registered_tasks = inspect.registered()
        
        if active_workers:
            print(f"✅ Active Workers: {len(active_workers)}")
            for worker, tasks in active_workers.items():
                print(f"   - {worker}: {len(tasks)} active tasks")
        else:
            print("❌ No active workers found")
            
        if registered_tasks:
            print(f"✅ Registered Tasks Found")
            for worker, tasks in registered_tasks.items():
                print(f"   - {worker}: {len(tasks)} registered tasks")
                # Show relevant tasks
                price_tasks = [t for t in tasks if 'price' in t]
                if price_tasks:
                    print(f"     Price-related: {price_tasks[:3]}")
        
    except Exception as e:
        print(f"❌ Worker Inspect: {e}")
    
    # Test 4: Check Queues in Redis
    try:
        queue_lengths = {
            'price_data': r.llen('price_data'),
            'default': r.llen('default'),
            'ml_tasks': r.llen('ml_tasks')
        }
        
        print("📊 Queue Status:")
        for queue, length in queue_lengths.items():
            print(f"   - {queue}: {length} pending tasks")
            
    except Exception as e:
        print(f"❌ Queue Check: {e}")
    
    # Test 5: Send Test Task
    try:
        print("\n🧪 Testing Task Routing...")
        
        # Send to specific queue
        result = sync_all_prices.apply_async(queue='price_data')
        print(f"✅ Test task sent: {result.id}")
        print(f"   Queue: price_data")
        print(f"   Task: app.tasks.price_collector.sync_all_prices")
        
        # Check if task appears in queue
        import time
        time.sleep(2)
        
        queue_after = r.llen('price_data')
        print(f"   Queue length after: {queue_after}")
        
        # Try to get task result (with timeout)
        try:
            task_result = result.get(timeout=10, propagate=False)
            print(f"✅ Task completed: {task_result}")
        except Exception as task_e:
            print(f"⚠️ Task timeout or failed: {task_e}")
            
    except Exception as e:
        print(f"❌ Test Task: {e}")
    
    print("\n🔧 Recommended Actions:")
    print("1. Check worker logs: tail -f backend/logs/celery_data_worker.log")
    print("2. Verify queue configuration in worker startup")
    print("3. Restart workers if queue mismatch found")
    print("4. Check Redis connection stability")

if __name__ == "__main__":
    test_worker_connection()