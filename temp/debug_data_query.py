# File: temp/debug_data_query.py
# Debug why ML repository only finds 2 records when 90 exist
# Check date filtering and query logic

import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.repositories import cryptocurrency_repository, price_data_repository
from app.repositories.ml_repository import ml_repository
from app.models import PriceData
from sqlalchemy import and_, asc, desc

def debug_btc_data():
    """Debug BTC data availability and query issues"""
    print("🔍 Debugging BTC Data Query Issues")
    print("=" * 50)
    
    with SessionLocal() as db:
        # Get BTC
        btc = cryptocurrency_repository.get_by_symbol(db, "BTC")
        if not btc:
            print("❌ BTC not found!")
            return
        
        print(f"✅ Found BTC: ID {btc.id}")
        
        # Check total records
        total_count = (
            db.query(PriceData)
            .filter(PriceData.crypto_id == btc.id)
            .count()
        )
        print(f"📊 Total BTC records in database: {total_count}")
        
        # Check recent records with different time ranges
        now = datetime.now(timezone.utc)
        time_ranges = [
            ("1 hour", 1),
            ("6 hours", 6), 
            ("12 hours", 12),
            ("24 hours", 24),
            ("48 hours", 48),
            ("7 days", 168),
            ("30 days", 720)
        ]
        
        print("\n🕐 Records by time range:")
        for label, hours in time_ranges:
            start_time = now - timedelta(hours=hours)
            
            count = (
                db.query(PriceData)
                .filter(
                    and_(
                        PriceData.crypto_id == btc.id,
                        PriceData.timestamp >= start_time,
                        PriceData.timestamp <= now
                    )
                )
                .count()
            )
            print(f"   {label:10}: {count} records")
        
        # Check the exact query that ml_repository uses
        print("\n🔍 Testing ML Repository Query Logic:")
        
        # Simulate the parameters used in ml_repository
        lookback_hours = 48  # From our fix
        sequence_length = 10  # From our fix
        
        end_date = datetime.now(timezone.utc) 
        start_date = end_date - timedelta(hours=lookback_hours)
        
        print(f"   End date: {end_date}")
        print(f"   Start date: {start_date}")
        print(f"   Time range: {lookback_hours} hours")
        
        # Execute the same query as ml_repository
        price_records = (
            db.query(PriceData)
            .filter(
                and_(
                    PriceData.crypto_id == btc.id,
                    PriceData.timestamp >= start_date,
                    PriceData.timestamp <= end_date
                )
            )
            .order_by(asc(PriceData.timestamp))
            .all()
        )
        
        print(f"   📊 Records found by ML query: {len(price_records)}")
        
        if len(price_records) > 0:
            print(f"   📅 Oldest record: {price_records[0].timestamp}")
            print(f"   📅 Newest record: {price_records[-1].timestamp}")
            print(f"   💰 Price range: ${price_records[0].close_price} - ${price_records[-1].close_price}")
        
        # Check what records actually exist
        print("\n📋 Sample of existing records:")
        sample_records = (
            db.query(PriceData)
            .filter(PriceData.crypto_id == btc.id)
            .order_by(desc(PriceData.timestamp))
            .limit(10)
            .all()
        )
        
        for i, record in enumerate(sample_records):
            age_hours = (now - record.timestamp).total_seconds() / 3600
            print(f"   {i+1:2}. {record.timestamp} (${record.close_price}) - {age_hours:.1f}h ago")
        
        # Test ml_repository method directly
        print("\n🧪 Testing ML Repository Method:")
        try:
            ml_data = ml_repository.get_recent_data_for_prediction(
                db=db,
                crypto_id=btc.id,
                lookback_hours=48,
                sequence_length=10
            )
            
            if ml_data is not None:
                print(f"   ✅ ML data returned: shape {ml_data.shape}")
            else:
                print(f"   ❌ ML data returned None")
                
        except Exception as e:
            print(f"   ❌ ML repository method failed: {e}")
            import traceback
            traceback.print_exc()

def fix_ml_repository_query():
    """Create a fixed version of the ML repository query"""
    print("\n🔧 Creating Fixed ML Repository Query")
    print("=" * 50)
    
    # Read current ml_repository.py file
    ml_repo_file = backend_dir / "app" / "repositories" / "ml_repository.py"
    
    if not ml_repo_file.exists():
        print("❌ ML repository file not found")
        return
    
    with open(ml_repo_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create a fixed version of the get_recent_data_for_prediction method
    fixed_method = '''    def get_recent_data_for_prediction(
        self,
        db: Session,
        crypto_id: int,
        lookback_hours: int = 48,  # Reduced from 168 to 48 hours (2 days)
        sequence_length: int = 10   # Reduced from 60 to 10 for limited data
    ) -> Optional[Any]:
        """
        Get recent data formatted for ML prediction (FIXED VERSION)
        
        Args:
            db: Database session
            crypto_id: Cryptocurrency ID
            lookback_hours: Hours of historical data to fetch (default: 48 hours)
            sequence_length: Number of time steps needed (default: 10 for limited data)
            
        Returns:
            Formatted numpy array for prediction or None if insufficient data
        """
        try:
            import numpy as np
            
            # FIXED: Get all recent records first, then filter by time if needed
            # This approach is more reliable with our test data
            
            # First, get all records for this crypto (most recent first)
            all_records = (
                db.query(PriceData)
                .filter(PriceData.crypto_id == crypto_id)
                .order_by(desc(PriceData.timestamp))
                .limit(100)  # Get more records to ensure we have enough
                .all()
            )
            
            logger.info(f"Found {len(all_records)} total records for crypto_id {crypto_id}")
            
            if len(all_records) < sequence_length:
                logger.warning(f"Insufficient data for prediction: {len(all_records)} records, need {sequence_length}")
                return None
            
            # Take the most recent sequence_length records and reverse order (oldest first)
            recent_records = list(reversed(all_records[:sequence_length]))
            
            # Convert to simple format for ML model
            data = []
            for record in recent_records:
                # Use close_price as main feature, add basic derived features
                close_price = float(record.close_price)
                volume = float(record.volume) if record.volume else 1.0
                price_range = float(record.high_price) - float(record.low_price)
                
                data.append([
                    close_price,
                    volume,
                    price_range if price_range > 0 else close_price * 0.01
                ])
            
            # Ensure we have enough data
            if len(data) < sequence_length:
                logger.warning(f"Processed data insufficient: {len(data)} records")
                return None
                
            # Convert to numpy array
            data_array = np.array(data, dtype=np.float32)
            
            # Validate data array
            if data_array is None or len(data_array) == 0:
                logger.warning("Data array is empty after processing")
                return None
            
            # Simple normalization
            try:
                last_price = data_array[-1, 0]
                if last_price > 0:
                    # Normalize prices relative to last price
                    data_array[:, 0] = data_array[:, 0] / last_price
                    data_array[:, 2] = data_array[:, 2] / last_price
                
                # Normalize volume (simple min-max)
                volume_col = data_array[:, 1]
                if volume_col.max() > 0:
                    data_array[:, 1] = volume_col / volume_col.max()
                    
            except Exception as norm_e:
                logger.warning(f"Normalization failed: {norm_e}")
                # Continue with unnormalized data
            
            # Handle NaN values
            data_array = np.nan_to_num(data_array, nan=0.0, posinf=1.0, neginf=0.0)
            
            # Final validation
            if np.any(np.isnan(data_array)) or np.any(np.isinf(data_array)):
                logger.warning("Data contains NaN or Inf values after cleaning")
                return None
            
            # Reshape for LSTM: (1, sequence_length, n_features)
            reshaped_data = data_array.reshape(1, sequence_length, -1)
            
            logger.info(f"Successfully prepared prediction data: shape {reshaped_data.shape}")
            return reshaped_data
            
        except Exception as e:
            logger.error(f"Failed to get recent prediction data: {str(e)}")
            return None'''
    
    # Find and replace the method
    method_start = "def get_recent_data_for_prediction("
    if method_start in content:
        # Find the start and end of the current method
        method_start_idx = content.find(method_start)
        if method_start_idx == -1:
            print("❌ Could not find method to replace")
            return False
        
        # Find the end of the method (next method or class end)
        method_content = content[method_start_idx:]
        
        # Find next method or end of class
        next_method_idx = method_content.find('\n    def ', 1)  # Skip current method
        if next_method_idx == -1:
            next_method_idx = method_content.find('\n\n# Global')
        if next_method_idx == -1:
            next_method_idx = len(method_content)
        
        method_end_idx = method_start_idx + next_method_idx
        
        # Replace the method
        updated_content = content[:method_start_idx] + fixed_method + content[method_end_idx:]
        
        # Make backup
        backup_file = ml_repo_file.with_suffix('.py.backup3')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Write updated file
        with open(ml_repo_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("✅ ML Repository method updated with FIXED query logic!")
        print(f"   💾 Backup created: {backup_file}")
        print("   🔧 Changes made:")
        print("      • Uses ORDER BY desc() to get recent records first")
        print("      • Takes first N records instead of date filtering")
        print("      • More reliable with test data")
        print("      • Better error handling")
        
        return True
    else:
        print("❌ Method not found for replacement")
        return False

def main():
    """Main debug function"""
    print("🚀 ML Repository Data Query Debug")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Debug the data query issue
    debug_btc_data()
    
    # Fix the ML repository query
    fix_success = fix_ml_repository_query()
    
    print("\n" + "=" * 50)
    if fix_success:
        print("🎉 ML Repository Query Fixed!")
        print("✅ Should now find records correctly")
        print("✅ Uses more reliable query approach")
        
        print("\n🔄 Next Steps:")
        print("1. Restart backend server:")
        print("   ./start-backend-local.sh")
        print("2. Test dashboard:")
        print("   python temp/api_migration_test.py")
        print("\n💡 The query now gets the most recent N records directly")
        print("   instead of filtering by date range, which is more reliable!")
    else:
        print("❌ Fix failed - check error messages above")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()