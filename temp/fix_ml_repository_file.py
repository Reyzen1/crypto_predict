# File: temp/fix_ml_repository_file.py
# Fix ML Repository by adding missing methods directly to the file

import os
import sys
from pathlib import Path

def fix_ml_repository():
    """Add missing methods to ml_repository.py file"""
    print("🔧 Fixing ML Repository File...")
    print("=" * 40)
    
    # Find ml_repository.py
    backend_dir = Path(__file__).parent.parent / "backend"
    ml_repo_file = backend_dir / "app" / "repositories" / "ml_repository.py"
    
    if not ml_repo_file.exists():
        print(f"❌ ML repository file not found: {ml_repo_file}")
        return False
    
    print(f"✅ Found ML repository: {ml_repo_file}")
    
    # Read current content
    with open(ml_repo_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if method already exists
    if 'get_recent_data_for_prediction' in content:
        print("⚠️ Method already exists in file")
        return True
    
    # Method to add
    missing_method = '''
    def get_recent_data_for_prediction(
        self,
        db: Session,
        crypto_id: int,
        lookback_hours: int = 168,  # 7 days
        sequence_length: int = 60
    ) -> Optional[Any]:
        """
        Get recent data formatted for ML prediction
        
        Args:
            db: Database session
            crypto_id: Cryptocurrency ID
            lookback_hours: Hours of historical data to fetch
            sequence_length: Number of time steps needed for sequence
            
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
                .limit(lookback_hours)
                .all()
            )
            
            if len(price_records) < sequence_length:
                logger.warning(f"Insufficient data for prediction: {len(price_records)} records, need {sequence_length}")
                return None
            
            # Convert to simple format for ML model
            data = []
            for record in price_records:
                data.append([
                    float(record.close_price),
                    float(record.volume) if record.volume else 0.0,
                    float(record.high_price) - float(record.low_price),  # price range
                ])
            
            if len(data) < sequence_length:
                return None
                
            # Get last sequence_length records
            recent_data = data[-sequence_length:]
            
            # Convert to numpy array
            data_array = np.array(recent_data, dtype=np.float32)
            
            # Simple normalization
            if len(data_array) > 0:
                last_price = data_array[-1, 0]
                if last_price > 0:
                    data_array[:, 0] = data_array[:, 0] / last_price
            
            # Handle NaN values
            data_array = np.nan_to_num(data_array, nan=0.0)
            
            # Reshape for LSTM: (1, sequence_length, n_features)
            return data_array.reshape(1, sequence_length, -1)
            
        except Exception as e:
            logger.error(f"Failed to get recent prediction data: {str(e)}")
            return None

    def get_crypto_data_quality(
        self,
        db: Session,
        crypto_id: int,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Assess data quality for a cryptocurrency
        
        Args:
            db: Database session
            crypto_id: Cryptocurrency ID
            days_back: Number of days to analyze
            
        Returns:
            Dict with quality metrics and recommendations
        """
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days_back)
            
            # Count records
            record_count = (
                db.query(PriceData)
                .filter(
                    and_(
                        PriceData.crypto_id == crypto_id,
                        PriceData.timestamp >= start_date,
                        PriceData.timestamp <= end_date
                    )
                )
                .count()
            )
            
            # Expected records (hourly data)
            expected_records = days_back * 24
            completeness_ratio = min(1.0, record_count / expected_records) if expected_records > 0 else 0.0
            
            # Quality assessment
            if completeness_ratio >= 0.8:
                recommendation = "Excellent - Ready for training"
            elif completeness_ratio >= 0.6:
                recommendation = "Good - Can train with monitoring"
            elif completeness_ratio >= 0.4:
                recommendation = "Fair - Consider getting more data"
            else:
                recommendation = "Poor - Insufficient for reliable training"
            
            return {
                "quality_score": round(completeness_ratio, 2),
                "record_count": record_count,
                "expected_records": expected_records,
                "recommendation": recommendation,
                "days_analyzed": days_back
            }
            
        except Exception as e:
            logger.error(f"Failed to assess data quality: {str(e)}")
            return {
                "quality_score": 0.0,
                "record_count": 0,
                "recommendation": "Error assessing quality"
            }
'''
    
    # Find insertion point (before the last line of the class)
    lines = content.split('\n')
    
    # Find the end of MLRepository class
    class_end_idx = -1
    in_class = False
    for i, line in enumerate(lines):
        if 'class MLRepository' in line:
            in_class = True
        elif in_class and line.startswith('class ') and 'MLRepository' not in line:
            class_end_idx = i
            break
        elif in_class and line.startswith('# Global ML repository instance'):
            class_end_idx = i
            break
    
    if class_end_idx == -1:
        # Find last method in class
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() and not lines[i].startswith('#') and not lines[i].startswith('ml_repository'):
                class_end_idx = i + 1
                break
    
    if class_end_idx == -1:
        print("❌ Could not find insertion point in class")
        return False
    
    # Insert the methods
    lines.insert(class_end_idx, missing_method)
    
    # Write back to file
    new_content = '\n'.join(lines)
    
    # Make backup
    backup_file = ml_repo_file.with_suffix('.py.backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup created: {backup_file}")
    
    # Write updated file
    with open(ml_repo_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ ML Repository file updated with missing methods!")
    print("   • get_recent_data_for_prediction")
    print("   • get_crypto_data_quality") 
    
    return True

def test_fixed_ml_repository():
    """Test the fixed ML repository"""
    print("\n🧪 Testing Fixed ML Repository...")
    print("=" * 40)
    
    try:
        # Add backend to path
        backend_dir = Path(__file__).parent.parent / "backend"
        sys.path.insert(0, str(backend_dir))
        
        # Import (this will reload the file)
        from app.repositories.ml_repository import ml_repository
        
        # Check if methods exist
        methods_to_check = [
            'get_recent_data_for_prediction',
            'get_crypto_data_quality'
        ]
        
        for method_name in methods_to_check:
            if hasattr(ml_repository, method_name):
                print(f"   ✅ {method_name}: Available")
            else:
                print(f"   ❌ {method_name}: Missing")
                return False
        
        print("✅ All required methods are now available!")
        return True
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def restart_backend_message():
    """Show message about restarting backend"""
    print("\n🔄 Next Steps:")
    print("=" * 20)
    print("1. ✅ ML Repository has been fixed")
    print("2. 🔄 Restart your backend server:")
    print("   ./start-backend-local.sh")
    print("3. 🧪 Test the API migration:")
    print("   python temp/api_migration_test.py")
    print("\n💡 The backend needs to be restarted to load the new methods.")

def main():
    """Main function"""
    print("🚀 ML Repository File Fix")
    print("=" * 30)
    
    # Fix the file
    fix_success = fix_ml_repository()
    
    if fix_success:
        # Test the fix
        test_success = test_fixed_ml_repository()
        
        if test_success:
            restart_backend_message()
            print("\n🎉 ML Repository Fix Completed Successfully!")
        else:
            print("\n⚠️ Fix applied but testing failed")
            print("Please restart backend and try API test")
    else:
        print("\n❌ Failed to fix ML Repository")
        print("Please check the error messages above")

if __name__ == "__main__":
    main()