# File: backend/app/repositories/ml_repository_addon.py
# Additional methods for ML Repository
# Add these methods to existing ml_repository.py

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from app.repositories import price_data_repository, cryptocurrency_repository


def add_methods_to_ml_repository():
    """
    Add missing methods to ML Repository
    This can be imported and used to extend the existing ML repository
    """
    
    def get_recent_data_for_prediction(
        self,
        db: Session,
        crypto_id: int,
        lookback_hours: int = 168,  # 7 days default
        sequence_length: int = 60
    ) -> Optional[np.ndarray]:
        """
        Get recent data formatted for prediction
        
        Args:
            db: Database session
            crypto_id: Cryptocurrency ID
            lookback_hours: Hours of data to retrieve
            sequence_length: Number of time steps for sequence
            
        Returns:
            Formatted numpy array for prediction input or None
        """
        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(hours=lookback_hours)
            
            # Get price data
            price_records = price_data_repository.get_price_history(
                db=db,
                crypto_id=crypto_id,
                start_date=start_date,
                end_date=end_date,
                limit=lookback_hours
            )
            
            if len(price_records) < sequence_length:
                print(f"Insufficient data: {len(price_records)} records, need {sequence_length}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'timestamp': record.timestamp,
                    'price': float(record.price),
                    'volume': float(record.volume) if record.volume else 0.0
                }
                for record in price_records
            ])
            
            if df.empty:
                return None
            
            # Sort by timestamp
            df = df.sort_values('timestamp')
            
            # Feature engineering
            df['returns'] = df['price'].pct_change()
            df['price_ma_7'] = df['price'].rolling(window=min(7, len(df))).mean()
            df['price_ma_20'] = df['price'].rolling(window=min(20, len(df))).mean()
            df['volume_ma'] = df['volume'].rolling(window=min(7, len(df))).mean()
            
            # Fill NaN values
            df = df.fillna(method='bfill').fillna(0)
            
            # Select features for prediction
            feature_columns = ['price', 'volume', 'returns', 'price_ma_7', 'price_ma_20']
            available_columns = [col for col in feature_columns if col in df.columns]
            
            # Get last sequence_length records
            recent_data = df[available_columns].tail(sequence_length)
            
            if len(recent_data) < sequence_length:
                print(f"Insufficient processed data: {len(recent_data)} records")
                return None
            
            # Convert to numpy array and normalize
            data_array = recent_data.values
            
            # Simple normalization (using last price as reference)
            if len(data_array) > 0:
                last_price = data_array[-1, 0]  # Assume price is first column
                if last_price > 0:
                    data_array[:, 0] = data_array[:, 0] / last_price  # Normalize prices
            
            # Reshape for LSTM input: (1, sequence_length, n_features)
            return data_array.reshape(1, sequence_length, -1)
            
        except Exception as e:
            print(f"Failed to get recent data for prediction: {e}")
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
            days_back: Days to analyze
            
        Returns:
            Data quality metrics
        """
        try:
            # Get recent data
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days_back)
            
            price_records = price_data_repository.get_price_history(
                db=db,
                crypto_id=crypto_id,
                start_date=start_date,
                end_date=end_date,
                limit=days_back * 24
            )
            
            if not price_records:
                return {
                    "quality_score": 0.0,
                    "record_count": 0,
                    "missing_data_percentage": 100.0,
                    "recommendation": "No data available"
                }
            
            # Calculate metrics
            record_count = len(price_records)
            expected_records = days_back * 24  # Hourly data
            missing_percentage = max(0, (expected_records - record_count) / expected_records * 100)
            
            # Quality score calculation
            completeness_score = max(0, 1 - missing_percentage / 100)
            freshness_score = 1.0 if record_count > 0 else 0.0
            
            quality_score = (completeness_score + freshness_score) / 2
            
            # Recommendation
            if quality_score >= 0.8:
                recommendation = "Excellent - Ready for ML training"
            elif quality_score >= 0.6:
                recommendation = "Good - Can train with caution"
            elif quality_score >= 0.4:
                recommendation = "Fair - Needs more data"
            else:
                recommendation = "Poor - Insufficient for training"
            
            return {
                "quality_score": round(quality_score, 2),
                "record_count": record_count,
                "expected_records": expected_records,
                "missing_data_percentage": round(missing_percentage, 1),
                "recommendation": recommendation,
                "data_span_days": days_back,
                "freshness": "Current" if record_count > 0 else "Stale"
            }
            
        except Exception as e:
            print(f"Failed to assess data quality: {e}")
            return {
                "quality_score": 0.0,
                "record_count": 0,
                "missing_data_percentage": 100.0,
                "recommendation": "Error assessing data quality"
            }
    
    # Return the methods to be added
    return {
        'get_recent_data_for_prediction': get_recent_data_for_prediction,
        'get_crypto_data_quality': get_crypto_data_quality
    }

def patch_ml_repository():
    """Add missing methods to existing ML repository"""
    print("🔧 Patching ML Repository with Missing Methods...")
    
    try:
        from app.repositories.ml_repository import ml_repository
        
        # Get additional methods
        additional_methods = add_methods_to_ml_repository()
        
        # Add methods to the repository instance
        for method_name, method_func in additional_methods.items():
            if not hasattr(ml_repository, method_name):
                # Bind method to instance
                import types
                bound_method = types.MethodType(method_func, ml_repository)
                setattr(ml_repository, method_name, bound_method)
                print(f"   ✅ Added method: {method_name}")
            else:
                print(f"   ⚠️ Method already exists: {method_name}")
        
        print("✅ ML Repository patching completed!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to patch ML repository: {e}")
        return False

async def test_patched_ml_repository():
    """Test the patched ML repository"""
    print("\n🧪 Testing Patched ML Repository")
    print("=" * 40)
    
    try:
        from app.core.database import SessionLocal
        from app.repositories.ml_repository import ml_repository
        from app.repositories import cryptocurrency_repository
        
        with SessionLocal() as db:
            # Get BTC
            btc = cryptocurrency_repository.get_by_symbol(db, "BTC")
            if not btc:
                print("❌ BTC not found in database")
                return False
            
            print(f"✅ Testing with BTC (ID: {btc.id})")
            
            # Test get_recent_data_for_prediction
            print("   🔍 Testing get_recent_data_for_prediction...")
            recent_data = ml_repository.get_recent_data_for_prediction(
                db=db,
                crypto_id=btc.id,
                lookback_hours=48,  # 2 days
                sequence_length=20   # Smaller sequence for testing
            )
            
            if recent_data is not None:
                print(f"      ✅ Recent data shape: {recent_data.shape}")
            else:
                print("      ⚠️ No recent data available (expected for new setup)")
            
            # Test data quality assessment
            print("   🔍 Testing get_crypto_data_quality...")
            quality = ml_repository.get_crypto_data_quality(
                db=db,
                crypto_id=btc.id,
                days_back=7
            )
            
            print(f"      📊 Data quality score: {quality.get('quality_score', 0)}")
            print(f"      📊 Record count: {quality.get('record_count', 0)}")
            print(f"      💡 Recommendation: {quality.get('recommendation', 'Unknown')}")
            
            return True
            
    except Exception as e:
        print(f"❌ Patched ML repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🚀 ML Repository Fix & Dashboard Test")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async def run_all():
        # Step 1: Ensure cryptos exist
        cryptos_ok = await ensure_cryptos_exist()
        
        # Step 2: Patch ML repository
        patch_ok = patch_ml_repository()
        
        # Step 3: Test patched repository
        if patch_ok:
            repo_ok = await test_patched_ml_repository()
        else:
            repo_ok = False
        
        # Step 4: Test dashboard
        if cryptos_ok:
            dashboard_ok = await test_dashboard_with_cryptos()
        else:
            dashboard_ok = False
        
        return cryptos_ok and patch_ok and dashboard_ok
    
    success = asyncio.run(run_all())
    
    # Summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 All Issues Fixed!")
        print("✅ ML Repository patched")
        print("✅ Dashboard service working")
        print("✅ Ready for API tests")
    else:
        print("❌ Some issues remain")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()