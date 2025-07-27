# temp/create_fresh_data.py
# Create fresh price data for Stage B testing - FIXED VERSION

import sys
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import SessionLocal
from app.repositories import cryptocurrency_repository, price_data_repository
from app.schemas.price_data import PriceDataCreate


def create_fresh_bitcoin_data():
    """Create fresh Bitcoin data with current timestamps"""
    print("🔄 Creating Fresh Bitcoin Data for Stage B")
    print("=" * 45)
    
    db = SessionLocal()
    try:
        # Get Bitcoin
        btc_crypto = cryptocurrency_repository.get_by_symbol(db, "BTC")
        if not btc_crypto:
            print("❌ Bitcoin not found")
            return False
        
        print(f"✅ Bitcoin found: ID {btc_crypto.id}")
        
        # Create fresh data starting from 48 hours ago to now
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=48)  # 48 hours of data
        
        print(f"📅 Creating data from {start_time} to {now}")
        
        # Start with realistic Bitcoin price
        current_price = 47500.0  # Current realistic BTC price
        created_count = 0
        
        # Create hourly data for last 48 hours
        current_time = start_time
        while current_time <= now:
            try:
                # Realistic price movement (Bitcoin-like volatility)
                price_change = np.random.normal(0, 0.02)  # 2% volatility
                current_price *= (1 + price_change)
                
                # Keep price in realistic range
                current_price = max(current_price, 35000.0)  # Floor
                current_price = min(current_price, 70000.0)  # Ceiling
                
                # Create OHLC data
                open_price = current_price
                intraday_volatility = abs(np.random.normal(0, 0.008))  # 0.8% intraday
                high_price = open_price * (1 + intraday_volatility)
                low_price = open_price * (1 - intraday_volatility)
                close_price = random.uniform(low_price, high_price)
                
                # Realistic volume (Bitcoin daily volume range)
                volume = random.uniform(800_000_000, 1_500_000_000)
                
                # Market cap
                market_cap = close_price * 19_700_000  # BTC supply
                
                # FIXED: Use get_price_history to check if data exists
                # Check last 1 hour window for existing data
                existing_data = price_data_repository.get_price_history(
                    db=db,
                    crypto_id=btc_crypto.id,
                    start_date=current_time - timedelta(minutes=30),
                    end_date=current_time + timedelta(minutes=30),
                    limit=5
                )
                
                # If no exact match found, create new record
                exact_match = any(
                    abs((record.timestamp - current_time).total_seconds()) < 300  # 5 minutes tolerance
                    for record in existing_data
                )
                
                if not exact_match:
                    # Create new price data
                    price_data = PriceDataCreate(
                        crypto_id=btc_crypto.id,
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
                current_price = close_price
                current_time += timedelta(hours=1)
                
                # Progress indicator every 10 records
                if created_count % 10 == 0 and created_count > 0:
                    hours_from_start = (current_time - start_time).total_seconds() / 3600
                    print(f"   📈 Created {created_count} records... ({hours_from_start:.0f}h)")
                
            except Exception as e:
                print(f"⚠️ Error creating data for {current_time}: {str(e)}")
                current_time += timedelta(hours=1)
                continue
        
        print(f"\n✅ Created {created_count} fresh records")
        
        # Verify fresh data
        fresh_data = price_data_repository.get_price_history(
            db=db,
            crypto_id=btc_crypto.id,
            start_date=now - timedelta(hours=24),  # Last 24 hours
            end_date=now,
            limit=100
        )
        
        print(f"📊 Fresh data verification: {len(fresh_data)} records in last 24h")
        
        if len(fresh_data) > 0:
            latest = fresh_data[0]
            time_diff = (now - latest.timestamp).total_seconds() / 3600
            print(f"📅 Latest record: {latest.timestamp}")
            print(f"💰 Latest price: ${latest.close_price}")
            print(f"⏰ Age: {time_diff:.1f} hours ago")
            
            if time_diff < 3:  # Less than 3 hours old
                print("\n🎉 Fresh data created successfully!")
                print("✅ Ready for Stage B testing!")
                return True
            else:
                print(f"\n⚠️ Data still too old ({time_diff:.1f}h)")
                return False
        else:
            print("\n❌ No fresh data found")
            return False
            
    except Exception as e:
        print(f"❌ Error creating fresh data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def test_fresh_data():
    """Test if fresh data is available"""
    print("\n🧪 Testing Fresh Data Availability")
    print("=" * 35)
    
    db = SessionLocal()
    try:
        btc_crypto = cryptocurrency_repository.get_by_symbol(db, "BTC")
        if not btc_crypto:
            return False
        
        now = datetime.now(timezone.utc)
        
        # Test various time ranges
        ranges = [
            ("Last 1 hour", timedelta(hours=1)),
            ("Last 6 hours", timedelta(hours=6)), 
            ("Last 24 hours", timedelta(hours=24)),
            ("Last 48 hours", timedelta(hours=48))
        ]
        
        for name, delta in ranges:
            data = price_data_repository.get_price_history(
                db=db,
                crypto_id=btc_crypto.id,
                start_date=now - delta,
                end_date=now,
                limit=1000
            )
            print(f"📊 {name}: {len(data)} records")
        
        # Get very recent data (last 3 hours)
        recent_data = price_data_repository.get_price_history(
            db=db,
            crypto_id=btc_crypto.id,
            start_date=now - timedelta(hours=3),
            end_date=now,
            limit=10
        )
        
        if len(recent_data) > 0:
            latest = recent_data[0]
            age_hours = (now - latest.timestamp).total_seconds() / 3600
            print(f"\n✅ Latest data: {age_hours:.1f} hours ago")
            
            if age_hours < 4:  # Less than 4 hours old
                print("🎉 Data is fresh enough for Stage B!")
                return True
            else:
                print("⚠️ Data is still too old for Stage B")
                return False
        else:
            print("\n❌ No recent data found")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False
        
    finally:
        db.close()


def clean_old_data_and_create_fresh():
    """Clean old data and create completely fresh data"""
    print("\n🧹 Alternative: Clean & Create Fresh Data")
    print("=" * 42)
    
    db = SessionLocal()
    try:
        btc_crypto = cryptocurrency_repository.get_by_symbol(db, "BTC")
        if not btc_crypto:
            return False
        
        # Don't delete old data, just create recent fresh data
        now = datetime.now(timezone.utc)
        
        # Create last 24 hours of data with fresh timestamps
        print("📅 Creating last 24 hours of fresh data...")
        
        current_time = now - timedelta(hours=24)
        base_price = 47200.0
        created_count = 0
        
        while current_time <= now:
            try:
                # Simple price movement
                price_change = random.uniform(-0.03, 0.03)  # 3% max change
                base_price *= (1 + price_change)
                base_price = max(35000, min(70000, base_price))  # Bounds
                
                # Simple OHLC
                close_price = base_price
                high_price = close_price * (1 + random.uniform(0, 0.01))
                low_price = close_price * (1 - random.uniform(0, 0.01))
                open_price = random.uniform(low_price, high_price)
                
                volume = random.uniform(900_000_000, 1_400_000_000)
                market_cap = close_price * 19_700_000
                
                # Create record
                price_data = PriceDataCreate(
                    crypto_id=btc_crypto.id,
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
                
                current_time += timedelta(hours=1)
                
            except Exception as e:
                print(f"⚠️ Error: {str(e)}")
                current_time += timedelta(hours=1)
                continue
        
        print(f"✅ Created {created_count} fresh records")
        return created_count > 20
        
    except Exception as e:
        print(f"❌ Clean & create failed: {str(e)}")
        return False
        
    finally:
        db.close()


def main():
    """Main function"""
    print("🚀 Stage B Data Preparation - FIXED")
    print("=" * 35)
    
    # Step 1: Try to create fresh data
    fresh_created = create_fresh_bitcoin_data()
    
    if not fresh_created:
        print("\n🔄 Trying alternative approach...")
        fresh_created = clean_old_data_and_create_fresh()
    
    if fresh_created:
        # Step 2: Test fresh data
        fresh_available = test_fresh_data()
        
        if fresh_available:
            print("\n" + "=" * 50)
            print("🎉 SUCCESS! Ready for Stage B")
            print("=" * 50)
            print("\n🚀 Next step:")
            print("   python temp/test_prediction_service.py")
            print("\n✅ Stage B should now pass!")
        else:
            print("\n⚠️ Fresh data created but still not fresh enough")
            print("🔧 Try running Stage B test anyway - it might work")
    else:
        print("\n❌ Could not create fresh data")
        print("🔧 Check database permissions and connections")


if __name__ == "__main__":
    main()