# temp/quick_fix_data_test.py
# Quick fix to test existing data properly

import sys
import os
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import SessionLocal
from app.repositories import cryptocurrency_repository, price_data_repository


def main():
    """Quick test and fix for existing data"""
    print("🔧 Quick Data Test & Fix")
    print("=" * 30)
    
    db = SessionLocal()
    try:
        # Get Bitcoin
        btc_crypto = cryptocurrency_repository.get_by_symbol(db, "BTC")
        if not btc_crypto:
            print("❌ Bitcoin not found")
            return False
        
        print(f"✅ Bitcoin found: ID {btc_crypto.id}")
        
        # Test different time ranges
        now = datetime.now(timezone.utc)
        
        # Test 1: Last 7 days
        data_7d = price_data_repository.get_price_history(
            db=db, crypto_id=btc_crypto.id,
            start_date=now - timedelta(days=7),
            end_date=now, limit=1000
        )
        print(f"📊 Last 7 days: {len(data_7d)} records")
        
        # Test 2: Last 1 day  
        data_1d = price_data_repository.get_price_history(
            db=db, crypto_id=btc_crypto.id,
            start_date=now - timedelta(days=1),
            end_date=now, limit=100
        )
        print(f"📊 Last 1 day: {len(data_1d)} records")
        
        # Test 3: All data
        all_data = price_data_repository.get_price_history(
            db=db, crypto_id=btc_crypto.id,
            start_date=now - timedelta(days=30),
            end_date=now, limit=1000
        )
        print(f"📊 Last 30 days: {len(all_data)} records")
        
        # Show latest records
        if len(all_data) > 0:
            latest = all_data[0]
            oldest = all_data[-1] if len(all_data) > 1 else all_data[0]
            
            print(f"\n📈 Data Range:")
            print(f"   Latest: {latest.timestamp} - ${latest.close_price}")
            print(f"   Oldest: {oldest.timestamp} - ${oldest.close_price}")
            
            # Check if data is recent enough
            time_diff = (now - latest.timestamp).total_seconds() / 3600  # hours
            print(f"   Latest data age: {time_diff:.1f} hours ago")
            
            if len(all_data) >= 50:
                print("\n✅ Sufficient data for Stage B testing!")
                print("\n🎯 Ready to run:")
                print("   python temp/test_prediction_service.py")
                return True
            else:
                print(f"\n❌ Need at least 50 records, have {len(all_data)}")
                return False
        else:
            print("\n❌ No data found at all!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 Proceed with Stage B testing!")
    else:
        print("\n🔧 Run sample data creation first:")
        print("   python temp/setup_data_collection_fixed.py")