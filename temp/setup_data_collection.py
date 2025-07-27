# temp/setup_data_collection.py
# Script to test and setup data collection service - FIXED VERSION

import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import SessionLocal
from app.repositories import cryptocurrency_repository, price_data_repository
from app.services.external_api import external_api_service
from app.schemas.cryptocurrency import CryptocurrencyCreate


def setup_bitcoin_data():
    """Setup Bitcoin and collect initial data - SYNC VERSION"""
    print("🚀 Setting up Bitcoin data collection...")
    
    db = SessionLocal()
    try:
        # Step 1: Ensure Bitcoin exists in database (SYNC method)
        btc_crypto = cryptocurrency_repository.get_by_symbol(db, "BTC")
        
        if not btc_crypto:
            print("📝 Creating Bitcoin record...")
            btc_data = CryptocurrencyCreate(
                symbol="BTC",
                name="Bitcoin",
                is_active=True
            )
            btc_crypto = cryptocurrency_repository.create(db, obj_in=btc_data)
            print(f"✅ Created Bitcoin: ID {btc_crypto.id}")
        else:
            print(f"✅ Found Bitcoin: ID {btc_crypto.id}")
        
        # Step 2: Check existing data (SYNC method)
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        
        existing_data = price_data_repository.get_price_history(
            db=db,
            crypto_id=btc_crypto.id,
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )
        
        print(f"📊 Found {len(existing_data)} existing records in last 7 days")
        
        # Step 3: Create sample data if needed
        if len(existing_data) < 100:  # Need more data
            print("🔄 Creating sample Bitcoin data...")
            created_count = create_sample_data(db, btc_crypto.id)
            print(f"✅ Created {created_count} sample records")
        
        # Step 4: Verify final data count
        final_data = price_data_repository.get_price_history(
            db=db,
            crypto_id=btc_crypto.id,
            start_date=start_date,
            end_date=end_date,
            limit=1000
        )
        
        print(f"📈 Final data count: {len(final_data)} records")
        
        if len(final_data) >= 100:
            print("✅ Sufficient data available for Stage B testing")
            return True
        else:
            print("❌ Still insufficient data for Stage B")
            return False
            
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        return False
        
    finally:
        db.close()


def create_sample_data(db, crypto_id, count=168):  # 7 days of hourly data
    """Create sample Bitcoin data for testing - SYNC VERSION"""
    print(f"📊 Creating {count} sample data points...")
    
    current_time = datetime.now(timezone.utc) - timedelta(hours=count)
    base_price = 47000.0  # Starting Bitcoin price
    
    import random
    import numpy as np
    
    created_count = 0
    for i in range(count):
        try:
            # Realistic price simulation
            price_change = np.random.normal(0, 0.015)  # 1.5% volatility
            base_price *= (1 + price_change)
            base_price = max(base_price, 35000.0)  # Price floor
            base_price = min(base_price, 70000.0)  # Price ceiling
            
            # OHLC simulation
            open_price = base_price
            volatility = abs(np.random.normal(0, 0.005))  # 0.5% intraday volatility
            high_price = open_price * (1 + volatility)
            low_price = open_price * (1 - volatility)
            close_price = random.uniform(low_price, high_price)
            
            # Volume simulation
            volume = random.uniform(800000000, 1500000000)  # Realistic BTC volume
            
            # Market cap calculation
            market_cap = close_price * 19700000  # Approximate BTC supply
            
            # Check if data already exists (SYNC method)
            existing = price_data_repository.get_by_crypto_and_timestamp(
                db, crypto_id, current_time
            )
            
            if not existing:
                from app.schemas.price_data import PriceDataCreate
                
                price_data = PriceDataCreate(
                    crypto_id=crypto_id,
                    timestamp=current_time,
                    open_price=Decimal(str(round(open_price, 2))),
                    high_price=Decimal(str(round(high_price, 2))),
                    low_price=Decimal(str(round(low_price, 2))),
                    close_price=Decimal(str(round(close_price, 2))),
                    volume=Decimal(str(round(volume, 2))),
                    market_cap=Decimal(str(round(market_cap, 2)))
                )
                
                price_data_repository.create(db, obj_in=price_data)
                created_count += 1
            
            # Update for next iteration
            base_price = close_price
            current_time += timedelta(hours=1)
            
        except Exception as e:
            print(f"⚠️ Error creating sample data point {i}: {str(e)}")
            continue
    
    return created_count


async def test_external_api():
    """Test external API functionality"""
    print("\n🧪 Testing External API...")
    
    db = SessionLocal()
    try:
        # Test external API if available
        print("1️⃣ Testing CoinGecko API connection...")
        try:
            # Try to get Bitcoin price using external API service
            result = await external_api_service.get_current_price_by_symbol(db, "BTC")
            if result.get('success'):
                price = result['data']['price']
                print(f"✅ External API working: BTC = ${price:.2f}")
                return True
            else:
                print(f"⚠️ External API issue: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ External API test failed: {str(e)}")
            return False
            
    finally:
        db.close()


def test_database_data():
    """Test database data availability"""
    print("\n🗄️ Testing Database Data...")
    
    db = SessionLocal()
    try:
        # Get Bitcoin
        btc_crypto = cryptocurrency_repository.get_by_symbol(db, "BTC")
        if not btc_crypto:
            print("❌ Bitcoin not found in database")
            return False
        
        # Check recent data
        recent_data = price_data_repository.get_price_history(
            db=db,
            crypto_id=btc_crypto.id,
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc),
            limit=100
        )
        
        print(f"✅ Database has {len(recent_data)} recent records")
        
        if len(recent_data) > 0:
            latest = recent_data[0]
            print(f"   Latest price: ${latest.close_price:.2f}")
            print(f"   Latest time: {latest.timestamp}")
        
        return len(recent_data) >= 10  # At least 10 recent records
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False
        
    finally:
        db.close()


def main():
    """Main function to setup data collection"""
    print("🚀 CryptoPredict Data Collection Setup")
    print("=" * 50)
    
    # Step 1: Setup Bitcoin and initial data (SYNC)
    print("\n📋 Step 1: Setting up Bitcoin data...")
    setup_success = setup_bitcoin_data()
    
    if setup_success:
        print("\n✅ Bitcoin data setup completed!")
        
        # Step 2: Test database data (SYNC)
        print("\n📋 Step 2: Testing database...")
        db_success = test_database_data()
        
        # Step 3: Test external API (ASYNC)
        print("\n📋 Step 3: Testing external API...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            api_success = loop.run_until_complete(test_external_api())
            loop.close()
        except Exception as e:
            print(f"⚠️ External API test error: {str(e)}")
            api_success = False
        
        # Summary
        print("\n" + "=" * 50)
        print("🎯 SETUP SUMMARY")
        print("=" * 50)
        
        results = [
            ("Bitcoin Data Setup", setup_success),
            ("Database Test", db_success),
            ("External API Test", api_success)
        ]
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{name:<20} {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed >= 2:  # At least database working
            print("\n🎉 Ready for Stage B testing!")
            print("\n🚀 Next Steps:")
            print("   1. Run: python temp/test_prediction_service.py")
            print("   2. Verify Stage B tests now pass")
            
            if not api_success:
                print("\n⚠️ Note: External API not working, but sample data is sufficient for testing")
                
        else:
            print("\n❌ Setup incomplete!")
            print("🔧 Try:")
            print("   1. Check database connection")
            print("   2. Verify PostgreSQL is running")
            print("   3. Check database permissions")
        
    else:
        print("\n❌ Data setup failed!")
        print("🔧 Try:")
        print("   1. Check database connection")
        print("   2. Verify PostgreSQL is running")
        print("   3. Check backend configuration")


if __name__ == "__main__":
    main()