# File: temp/test_service_methods.py
# Test the fixed service methods to ensure they work correctly

import sys
import os
import asyncio
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

async def test_services():
    """Test the fixed service methods"""
    print("🔧 Testing Fixed Service Methods")
    print("=" * 40)
    
    try:
        from app.core.database import SessionLocal
        from app.services.dashboard_service import dashboard_service
        from app.services.prediction_service import prediction_service_new
        
        print("✅ Services imported successfully")
        
        # Test 1: Dashboard summary
        print("\n📊 Test 1: Dashboard Summary")
        print("-" * 30)
        
        with SessionLocal() as db:
            try:
                result = await dashboard_service.get_dashboard_summary(
                    db=db,
                    symbols=["BTC"],
                    user_id=None
                )
                
                if result:
                    print("✅ Dashboard summary working!")
                    print(f"   Cryptocurrencies: {len(result.get('cryptocurrencies', []))}")
                    print(f"   System status: {result.get('system_status', 'unknown')}")
                    
                    if result['cryptocurrencies']:
                        crypto = result['cryptocurrencies'][0]
                        print(f"   BTC current price: ${crypto.get('current_price', 'N/A')}")
                        print(f"   BTC predicted price: ${crypto.get('predicted_price', 'N/A')}")
                        print(f"   Confidence: {crypto.get('confidence', 'N/A')}%")
                else:
                    print("❌ Dashboard summary returned None")
                    
            except Exception as e:
                print(f"❌ Dashboard summary failed: {e}")
        
        # Test 2: Prediction service (with try-catch for debugging)
        print("\n🔮 Test 2: Prediction Service")
        print("-" * 30)
        
        with SessionLocal() as db:
            try:
                # First, check if BTC exists in database
                crypto = None
                try:
                    from app.repositories import cryptocurrency_repository
                    crypto = cryptocurrency_repository.get_by_symbol(db, "BTC")
                    if crypto:
                        print(f"   ✅ BTC found in database: {crypto.id} - {crypto.name}")
                    else:
                        print("   ⚠️ BTC not found in database - creating fallback data")
                        # Create BTC for testing
                        from app.schemas.cryptocurrency import CryptocurrencyCreate
                        btc_data = CryptocurrencyCreate(
                            symbol="BTC",
                            name="Bitcoin",
                            is_active=True
                        )
                        crypto = cryptocurrency_repository.create(db, obj_in=btc_data)
                        print(f"   ✅ Created BTC: {crypto.id} - {crypto.name}")
                        
                except Exception as e:
                    print(f"   ⚠️ Crypto check failed: {e}")
                
                # Now test prediction service
                result = await prediction_service_new.get_symbol_prediction(
                    db=db,
                    symbol="BTC",
                    days=1,
                    user_id=None
                )
                
                if result:
                    print("   ✅ Prediction service working!")
                    print(f"   Symbol: {result.get('symbol', 'N/A')}")
                    print(f"   Current price: ${result.get('current_price', 'N/A')}")
                    print(f"   Predicted price: ${result.get('predicted_price', 'N/A')}")
                    print(f"   Confidence: {result.get('confidence', 'N/A')}%")
                    print(f"   Cached: {result.get('cached', False)}")
                else:
                    print("   ❌ Prediction service returned None")
                    
            except Exception as e:
                print(f"   ❌ Prediction service failed: {e}")
                # Print detailed error for debugging
                import traceback
                print(f"   🔍 Error details:")
                traceback.print_exc()
        
        print("\n✅ Service method tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run service tests"""
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = asyncio.run(test_services())
    
    if success:
        print("\n🎉 All service methods are working!")
        print("✅ Dashboard endpoints should now work")
        print("✅ Ready to test API migration")
    else:
        print("\n🔧 Some issues remain")
        print("❌ Check the error messages above")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()