# File: temp/test_with_crypto_creation.py
# Test dashboard service with automatic crypto creation
# Ensures BTC and ETH exist in database before testing

import sys
import os
import asyncio
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

async def ensure_cryptos_exist():
    """Ensure BTC and ETH exist in database"""
    print("🔍 Ensuring Cryptocurrencies Exist...")
    print("=" * 40)
    
    try:
        from app.core.database import SessionLocal
        from app.repositories import cryptocurrency_repository
        from app.schemas.cryptocurrency import CryptocurrencyCreate
        
        with SessionLocal() as db:
            # Define required cryptos
            required_cryptos = [
                {"symbol": "BTC", "name": "Bitcoin"},
                {"symbol": "ETH", "name": "Ethereum"},
                {"symbol": "ADA", "name": "Cardano"},
                {"symbol": "DOT", "name": "Polkadot"}
            ]
            
            created = []
            existing = []
            
            for crypto_data in required_cryptos:
                symbol = crypto_data["symbol"]
                
                # Check if exists
                crypto = cryptocurrency_repository.get_by_symbol(db, symbol)
                
                if crypto:
                    existing.append(f"{symbol} (ID: {crypto.id})")
                else:
                    # Create it
                    try:
                        new_crypto_data = CryptocurrencyCreate(
                            symbol=symbol,
                            name=crypto_data["name"],
                            is_active=True
                        )
                        new_crypto = cryptocurrency_repository.create(db, obj_in=new_crypto_data)
                        created.append(f"{symbol} (ID: {new_crypto.id})")
                        
                    except Exception as e:
                        print(f"   ❌ Failed to create {symbol}: {e}")
            
            # Summary
            if existing:
                print("   ✅ Existing cryptocurrencies:")
                for item in existing:
                    print(f"      • {item}")
            
            if created:
                print("   ✅ Created cryptocurrencies:")
                for item in created:
                    print(f"      • {item}")
            
            total_cryptos = len(existing) + len(created)
            print(f"\n   📊 Total cryptocurrencies: {total_cryptos}")
            
            return total_cryptos > 0
            
    except Exception as e:
        print(f"❌ Failed to ensure cryptos exist: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_dashboard_with_cryptos():
    """Test dashboard service after ensuring cryptos exist"""
    print("\n📊 Testing Dashboard with Cryptos")
    print("=" * 40)
    
    try:
        from app.core.database import SessionLocal
        from app.services.dashboard_service import dashboard_service
        
        with SessionLocal() as db:
            # Test dashboard summary
            result = await dashboard_service.get_dashboard_summary(
                db=db,
                symbols=["BTC", "ETH"],
                user_id=None
            )
            
            if result:
                print("✅ Dashboard summary working!")
                print(f"   Timestamp: {result.get('timestamp')}")
                print(f"   System status: {result.get('system_status')}")
                
                cryptos = result.get('cryptocurrencies', [])
                print(f"   Cryptocurrencies: {len(cryptos)}")
                
                for crypto in cryptos:
                    print(f"      • {crypto.get('symbol')}: ${crypto.get('current_price')} → ${crypto.get('predicted_price')} ({crypto.get('confidence')}%)")
                
                market_overview = result.get('market_overview', {})
                print(f"   Market sentiment: {market_overview.get('market_sentiment', 'unknown')}")
                
                return True
            else:
                print("❌ Dashboard summary returned None")
                return False
                
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_individual_endpoints():
    """Test individual dashboard endpoints"""
    print("\n🔍 Testing Individual Endpoints")
    print("=" * 40)
    
    try:
        from app.core.database import SessionLocal
        from app.services.dashboard_service import dashboard_service
        
        with SessionLocal() as db:
            # Test crypto details
            print("📈 Testing crypto details for BTC...")
            crypto_details = await dashboard_service.get_crypto_details(
                db=db,
                symbol="BTC",
                days_history=7,
                user_id=None
            )
            
            if crypto_details:
                print("   ✅ Crypto details working!")
                print(f"      Current price: ${crypto_details.get('current_price')}")
                print(f"      Predicted price: ${crypto_details.get('predicted_price')}")
                print(f"      Price history records: {len(crypto_details.get('price_history', []))}")
                
                return True
            else:
                print("   ❌ Crypto details failed")
                return False
                
    except Exception as e:
        print(f"❌ Individual endpoints test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Dashboard Service Test with Auto Crypto Creation")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async def run_all_tests():
        """Run all tests in sequence"""
        
        # Step 1: Ensure cryptos exist
        cryptos_ok = await ensure_cryptos_exist()
        if not cryptos_ok:
            print("❌ Failed to ensure cryptocurrencies exist")
            return False
        
        # Step 2: Test dashboard
        dashboard_ok = await test_dashboard_with_cryptos()
        if not dashboard_ok:
            print("❌ Dashboard test failed")
            return False
        
        # Step 3: Test individual endpoints
        endpoints_ok = await test_individual_endpoints()
        
        return dashboard_ok and endpoints_ok
    
    # Run tests
    success = asyncio.run(run_all_tests())
    
    # Summary
    print("\n" + "=" * 60)
    if success:
        print("🎉 All Dashboard Tests Passed!")
        print("✅ Cryptocurrencies created/verified")
        print("✅ Dashboard summary working")
        print("✅ Individual endpoints working")
        print("✅ Ready for API migration test")
        
        print("\n🔗 Next steps:")
        print("   python temp/api_migration_test.py")
        print("   python temp/simple_websocket_test.py")
    else:
        print("❌ Some tests failed")
        print("🔧 Check the error messages above")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()