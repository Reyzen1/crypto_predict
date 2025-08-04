# File: temp/create_test_data_proper.py
# Create test data using your existing code patterns
# Creates 60+ price records for BTC and ETH using your methods

import sys
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import random

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import SessionLocal
from app.repositories import cryptocurrency_repository, price_data_repository
from app.schemas.cryptocurrency import CryptocurrencyCreate


def ensure_cryptocurrencies_exist(db):
    """Ensure BTC and ETH exist using your existing code pattern"""
    print("🔍 Ensuring cryptocurrencies exist...")
    
    cryptos_created = []
    cryptos_data = [
        {"symbol": "BTC", "name": "Bitcoin"},
        {"symbol": "ETH", "name": "Ethereum"},
        {"symbol": "ADA", "name": "Cardano"},
        {"symbol": "DOT", "name": "Polkadot"}
    ]
    
    for crypto_info in cryptos_data:
        symbol = crypto_info["symbol"]
        
        # Check if exists using your method
        crypto = cryptocurrency_repository.get_by_symbol(db, symbol)
        
        if not crypto:
            # Create using your schema and method
            crypto_data = CryptocurrencyCreate(
                symbol=symbol,
                name=crypto_info["name"],
                is_active=True
            )
            crypto = cryptocurrency_repository.create(db, obj_in=crypto_data)
            cryptos_created.append(f"{symbol} (ID: {crypto.id})")
            print(f"   ✅ Created {symbol}: ID {crypto.id}")
        else:
            print(f"   ✅ Found {symbol}: ID {crypto.id}")
    
    return cryptos_created


def create_realistic_price_data(db, crypto_id, symbol, num_records=70):
    """Create realistic price data using your existing add_price_data method"""
    print(f"📈 Creating {num_records} price records for {symbol}...")
    
    # Check existing data count
    existing_count = (
        db.query(price_data_repository.model)
        .filter(price_data_repository.model.crypto_id == crypto_id)
        .count()
    )
    
    print(f"   📊 Existing records: {existing_count}")
    
    if existing_count >= 60:
        print(f"   ✅ Sufficient data already exists for {symbol}")
        return existing_count
    
    # Base prices for different cryptos
    base_prices = {
        "BTC": 45000,
        "ETH": 3000,
        "ADA": 0.5,
        "DOT": 8.0
    }
    
    base_price = base_prices.get(symbol, 1000)
    current_time = datetime.now(timezone.utc)
    
    created_count = 0
    
    # Create price data going back in time
    for i in range(num_records):
        try:
            # Calculate timestamp (going back in time)
            hours_back = num_records - i
            timestamp = current_time - timedelta(hours=hours_back)
            
            # Generate realistic price with some volatility
            # Create a trending pattern with random noise
            trend_factor = 1 + (random.uniform(-0.001, 0.002) * i)  # Slight upward trend
            daily_volatility = random.uniform(-0.05, 0.05)  # ±5% daily volatility
            noise = random.uniform(-0.01, 0.01)  # ±1% noise
            
            current_price = base_price * trend_factor * (1 + daily_volatility + noise)
            
            # Create OHLC data (Open, High, Low, Close)
            price_range = current_price * random.uniform(0.005, 0.02)  # 0.5-2% range
            
            open_price = current_price + random.uniform(-price_range/2, price_range/2)
            close_price = current_price + random.uniform(-price_range/2, price_range/2)
            high_price = max(open_price, close_price) + random.uniform(0, price_range/2)
            low_price = min(open_price, close_price) - random.uniform(0, price_range/2)
            
            # Generate realistic volume
            base_volume = {
                "BTC": 2000000,   # 2M BTC volume
                "ETH": 10000000,  # 10M ETH volume
                "ADA": 500000000, # 500M ADA volume
                "DOT": 50000000   # 50M DOT volume
            }
            
            volume_base = base_volume.get(symbol, 1000000)
            volume = volume_base * random.uniform(0.5, 2.0)  # ±100% volume variation
            
            # Calculate market cap
            market_cap = close_price * {
                "BTC": 19700000,  # ~19.7M BTC supply
                "ETH": 120000000, # ~120M ETH supply
                "ADA": 35000000000, # ~35B ADA supply
                "DOT": 1200000000   # ~1.2B DOT supply
            }.get(symbol, 1000000)
            
            # Check if this timestamp already exists to avoid duplicates
            existing = price_data_repository.get_by_timestamp(db, crypto_id, timestamp)
            if existing:
                continue
            
            # Use your existing add_price_data method
            price_record = price_data_repository.add_price_data(
                db=db,
                crypto_id=crypto_id,
                timestamp=timestamp,
                open_price=Decimal(str(round(open_price, 8))),
                high_price=Decimal(str(round(high_price, 8))),
                low_price=Decimal(str(round(low_price, 8))),
                close_price=Decimal(str(round(close_price, 8))),
                volume=Decimal(str(round(volume, 8))),
                market_cap=Decimal(str(round(market_cap, 2)))
            )
            
            created_count += 1
            
            # Show progress
            if created_count % 10 == 0:
                print(f"   📊 Created {created_count}/{num_records} records...")
            
        except Exception as e:
            print(f"   ⚠️ Failed to create record {i}: {e}")
            continue
    
    print(f"   ✅ Successfully created {created_count} price records for {symbol}")
    return created_count


def verify_data_for_ml(db, crypto_id, symbol):
    """Verify that we have enough data for ML predictions"""
    print(f"🔍 Verifying ML data for {symbol}...")
    
    # Check total count
    total_count = (
        db.query(price_data_repository.model)
        .filter(price_data_repository.model.crypto_id == crypto_id)
        .count()
    )
    
    # Check recent data (last 7 days)
    recent_start = datetime.now(timezone.utc) - timedelta(days=7)
    recent_data = price_data_repository.get_price_history(
        db=db,
        crypto_id=crypto_id,
        start_date=recent_start,
        limit=200
    )
    
    # Check data quality
    if len(recent_data) > 0:
        latest_record = recent_data[-1]
        oldest_record = recent_data[0]
        time_span = latest_record.timestamp - oldest_record.timestamp
        
        print(f"   📊 Total records: {total_count}")
        print(f"   📊 Recent records (7 days): {len(recent_data)}")
        print(f"   📊 Time span: {time_span}")
        print(f"   📊 Latest price: ${latest_record.close_price}")
        
        # ML readiness check
        if total_count >= 60:
            print(f"   ✅ {symbol} is ready for ML predictions!")
            return True
        else:
            print(f"   ⚠️ {symbol} needs more data for ML predictions")
            return False
    else:
        print(f"   ❌ No recent data found for {symbol}")
        return False


def main():
    """Main function to create test data"""
    print("🚀 Creating Test Data Using Your Code Patterns")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with SessionLocal() as db:
        try:
            # Step 1: Ensure cryptocurrencies exist
            created_cryptos = ensure_cryptocurrencies_exist(db)
            
            # Step 2: Create price data for each crypto
            results = {}
            cryptos_to_process = ["BTC", "ETH", "ADA", "DOT"]
            
            for symbol in cryptos_to_process:
                print(f"\n📈 Processing {symbol}...")
                
                # Get crypto
                crypto = cryptocurrency_repository.get_by_symbol(db, symbol)
                if not crypto:
                    print(f"   ❌ {symbol} not found")
                    continue
                
                # Create price data
                created_count = create_realistic_price_data(
                    db=db,
                    crypto_id=crypto.id,
                    symbol=symbol,
                    num_records=70  # Create 70 records to be safe
                )
                
                # Verify ML readiness
                ml_ready = verify_data_for_ml(db, crypto.id, symbol)
                
                results[symbol] = {
                    "crypto_id": crypto.id,
                    "created_count": created_count,
                    "ml_ready": ml_ready
                }
            
            # Step 3: Summary
            print("\n" + "=" * 60)
            print("📊 Data Creation Summary:")
            
            total_created = 0
            ml_ready_count = 0
            
            for symbol, data in results.items():
                status = "✅ ML Ready" if data["ml_ready"] else "⚠️ Needs More Data"
                print(f"   {symbol}: {data['created_count']} records - {status}")
                total_created += data["created_count"]
                if data["ml_ready"]:
                    ml_ready_count += 1
            
            print(f"\n📊 Total Records Created: {total_created}")
            print(f"📊 ML Ready Cryptos: {ml_ready_count}/{len(results)}")
            
            if ml_ready_count >= 2:  # At least BTC and ETH ready
                print("\n🎉 Success! Ready for ML Predictions!")
                print("✅ Dashboard endpoints should now work properly")
                print("✅ Prediction service should have sufficient data")
                
                print("\n🔄 Next Steps:")
                print("1. Restart backend server:")
                print("   ./start-backend-local.sh")
                print("2. Test API migration:")
                print("   python temp/api_migration_test.py")
                print("3. Test WebSocket:")
                print("   python temp/simple_websocket_test.py")
            else:
                print("\n⚠️ Warning: Not enough cryptos are ML-ready")
                print("Consider running this script again or checking data quality")
            
        except Exception as e:
            print(f"❌ Error creating test data: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()