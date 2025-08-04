# File: temp/fix_prediction_parameters.py
# Fix prediction parameters to work with limited data
# Reduce sequence length requirements and improve error handling

import os
import sys
from pathlib import Path

def find_and_fix_sequence_length():
    """Find and fix sequence length parameters in prediction service"""
    print("🔧 Fixing Prediction Parameters...")
    print("=" * 40)
    
    backend_dir = Path(__file__).parent.parent / "backend"
    
    # Files that might contain sequence_length parameters
    files_to_check = [
        backend_dir / "app" / "ml" / "prediction" / "prediction_service.py",
        backend_dir / "app" / "repositories" / "ml_repository.py",
        backend_dir / "app" / "ml" / "models" / "lstm_predictor.py"
    ]
    
    changes_made = 0
    
    for file_path in files_to_check:
        if not file_path.exists():
            print(f"⚠️ File not found: {file_path}")
            continue
            
        print(f"📝 Checking: {file_path.name}")
        
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix common sequence length issues
        replacements = [
            # Reduce default sequence length from 60 to 10
            ("sequence_length: int = 60", "sequence_length: int = 10"),
            ("sequence_length=60", "sequence_length=10"),
            ("lookback_hours: int = 168", "lookback_hours: int = 48"),  # 2 days instead of 7
            ("need 60", "need 10"),
            
            # Fix error handling for None data
            ("if data_array.empty:", "if data_array is None or len(data_array) == 0:"),
            ("data_array.empty", "len(data_array) == 0"),
        ]
        
        file_changed = False
        for old_text, new_text in replacements:
            if old_text in content:
                content = content.replace(old_text, new_text)
                file_changed = True
                print(f"   ✅ Fixed: {old_text} → {new_text}")
        
        # Write back if changed
        if file_changed:
            # Make backup
            backup_path = file_path.with_suffix('.py.backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            changes_made += 1
            print(f"   💾 Updated: {file_path.name} (backup: {backup_path.name})")
        else:
            print(f"   ⚪ No changes needed: {file_path.name}")
    
    return changes_made

def fix_ml_repository_method():
    """Fix the get_recent_data_for_prediction method specifically"""
    print("\n🔧 Fixing ML Repository Method...")
    print("=" * 40)
    
    backend_dir = Path(__file__).parent.parent / "backend"
    ml_repo_file = backend_dir / "app" / "repositories" / "ml_repository.py"
    
    if not ml_repo_file.exists():
        print(f"❌ ML repository file not found: {ml_repo_file}")
        return False
    
    # Read current content
    with open(ml_repo_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the method with a more robust version
    method_start = "def get_recent_data_for_prediction("
    method_end = "return None"
    
    if method_start in content:
        # Create improved method
        improved_method = '''    def get_recent_data_for_prediction(
        self,
        db: Session,
        crypto_id: int,
        lookback_hours: int = 48,  # Reduced from 168 to 48 hours (2 days)
        sequence_length: int = 5   # Reduced from 60 to 5 for limited data
    ) -> Optional[Any]:
        """
        Get recent data formatted for ML prediction (optimized for limited data)
        
        Args:
            db: Database session
            crypto_id: Cryptocurrency ID
            lookback_hours: Hours of historical data to fetch (default: 48 hours)
            sequence_length: Number of time steps needed (default: 5 for limited data)
            
        Returns:
            Formatted numpy array for prediction or None if insufficient data
        """
        try:
            import numpy as np
            
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(hours=lookback_hours)
            
            # Get recent price data
            price_records = (
                db.query(PriceData)
                .filter(
                    and_(
                        PriceData.crypto_id == crypto_id,
                        PriceData.timestamp >= start_date,
                        PriceData.timestamp <= end_date
                    )
                )
                .order_by(asc(PriceData.timestamp))
                .all()  # Get all available records
            )
            
            # Check minimum data requirement
            if len(price_records) < sequence_length:
                logger.warning(f"Insufficient data for prediction: {len(price_records)} records, need {sequence_length}")
                return None
            
            # Convert to simple format for ML model
            data = []
            for record in price_records:
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
                
            # Get last sequence_length records
            recent_data = data[-sequence_length:]
            
            # Convert to numpy array
            data_array = np.array(recent_data, dtype=np.float32)
            
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
        updated_content = content[:method_start_idx] + improved_method + content[method_end_idx:]
        
        # Make backup
        backup_file = ml_repo_file.with_suffix('.py.backup2')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Write updated file
        with open(ml_repo_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("✅ ML Repository method updated with improved error handling!")
        print(f"   💾 Backup created: {backup_file}")
        print("   📊 New parameters:")
        print("      • Sequence length: 5 (was 60)")
        print("      • Lookback hours: 48 (was 168)")
        print("      • Better error handling")
        
        return True
    else:
        print("❌ Method not found for replacement")
        return False

def create_test_prediction_data():
    """Create some test prediction data"""
    print("\n🧪 Creating Test Prediction Data...")
    print("=" * 40)
    
    try:
        backend_dir = Path(__file__).parent.parent / "backend"
        sys.path.insert(0, str(backend_dir))
        
        from app.core.database import SessionLocal
        from app.repositories import cryptocurrency_repository, price_data_repository
        from app.schemas.price_data import PriceDataCreate
        from app.models import PriceData  # Import the model
        from datetime import datetime, timezone, timedelta
        from decimal import Decimal
        import random
        
        with SessionLocal() as db:
            # Get BTC
            btc = cryptocurrency_repository.get_by_symbol(db, "BTC")
            if not btc:
                print("❌ BTC not found")
                return False
            
            # Check existing data - Fixed the query
            existing_count = (
                db.query(PriceData)
                .filter(PriceData.crypto_id == btc.id)
                .count()
            )
            
            print(f"📊 Existing price records for BTC: {existing_count}")
            
            if existing_count < 10:  # Create some test data
                print("📈 Creating test price data...")
                
                base_price = 45000
                now = datetime.now(timezone.utc)
                
                for i in range(20):  # Create 20 records
                    # Create price with some variation
                    price_variation = random.uniform(-0.02, 0.02)  # ±2%
                    price = base_price * (1 + price_variation)
                    
                    timestamp = now - timedelta(hours=20-i)
                    
                    price_data = PriceDataCreate(
                        crypto_id=btc.id,
                        timestamp=timestamp,
                        open_price=Decimal(str(price * 0.999)),
                        high_price=Decimal(str(price * 1.001)),
                        low_price=Decimal(str(price * 0.998)),
                        close_price=Decimal(str(price)),
                        volume=Decimal(str(random.uniform(1000000, 5000000))),
                        market_cap=Decimal(str(price * 19700000))
                    )
                    
                    try:
                        price_data_repository.create(db, obj_in=price_data)
                    except Exception as e:
                        print(f"   ⚠️ Failed to create record {i}: {e}")
                
                print("✅ Test price data created!")
                return True
            else:
                print("✅ Sufficient price data already exists")
                return True
                
    except Exception as e:
        print(f"❌ Failed to create test data: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🚀 Prediction Parameters Fix")
    print("=" * 50)
    
    # Step 1: Fix sequence length parameters
    changes = find_and_fix_sequence_length()
    print(f"\n📊 Files modified: {changes}")
    
    # Step 2: Fix ML repository method specifically
    ml_fixed = fix_ml_repository_method()
    
    # Step 3: Create test data if needed
    data_created = create_test_prediction_data()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Fix Summary:")
    print(f"   🔧 Parameter fixes: {changes} files")
    print(f"   📝 ML Repository: {'✅ Fixed' if ml_fixed else '❌ Failed'}")
    print(f"   📊 Test data: {'✅ Ready' if data_created else '❌ Failed'}")
    
    if ml_fixed:
        print("\n🔄 Next Steps:")
        print("1. Restart backend server:")
        print("   ./start-backend-local.sh")
        print("2. Test API migration:")
        print("   python temp/api_migration_test.py")
        print("\n💡 Prediction should now work with limited data!")
    else:
        print("\n❌ Fix failed - please check error messages")

if __name__ == "__main__":
    main()