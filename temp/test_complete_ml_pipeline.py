# File: temp/test_complete_ml_pipeline.py
# Complete test for ML pipeline integration

import asyncio
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database import SessionLocal
from app.repositories import cryptocurrency_repository, price_data_repository
from app.repositories.ml_repository import ml_repository
from app.ml.training.training_service import training_service
from app.models import Cryptocurrency, PriceData
from app.schemas.cryptocurrency import CryptocurrencyCreate
from app.schemas.price_data import PriceDataCreate


async def setup_test_data(db):
    """Setup test Bitcoin data if it doesn't exist"""
    print("🔍 Setting up test data...")
    
    # Check if Bitcoin exists
    btc_crypto = cryptocurrency_repository.get_by_symbol(db, "BTC")
    
    if not btc_crypto:
        # Create Bitcoin cryptocurrency
        btc_data = CryptocurrencyCreate(
            symbol="BTC",
            name="Bitcoin",
            is_active=True
        )
        btc_crypto = cryptocurrency_repository.create(db, obj_in=btc_data)
        print("✅ Created Bitcoin cryptocurrency record")
    
    # Check if we have recent price data using existing method
    recent_data = price_data_repository.get_price_history(
        db=db,
        crypto_id=btc_crypto.id,
        start_date=datetime.now(timezone.utc) - timedelta(days=7),
        end_date=datetime.now(timezone.utc),
        limit=100
    )
    
    if len(recent_data) < 50:
        print("📊 Creating sample Bitcoin price data...")
        await create_sample_price_data(db, btc_crypto.id)
    else:
        print(f"✅ Found {len(recent_data)} recent price records")
    
    return btc_crypto


async def create_sample_price_data(db, crypto_id):
    """Create realistic sample Bitcoin price data"""
    
    # Generate 200 hourly price points over the last 8+ days
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=200)
    
    # Start with a realistic Bitcoin price
    base_price = 45000.0
    prices = []
    
    current_time = start_time
    current_price = base_price
    
    for i in range(200):
        # Simulate realistic price movement
        change_percent = np.random.normal(0, 0.02)  # 2% standard deviation
        price_change = current_price * change_percent
        current_price = max(30000, min(80000, current_price + price_change))
        
        # Create OHLCV data with proper price relationships
        open_price = current_price + np.random.normal(0, current_price * 0.005)
        close_price = current_price
        
        # Ensure high >= max(open, close) and low <= min(open, close)
        price_range = abs(np.random.normal(0, current_price * 0.01))
        high_price = max(open_price, close_price) + price_range
        low_price = min(open_price, close_price) - price_range
        
        # Ensure no negative prices
        high_price = max(1000, high_price)
        low_price = max(500, low_price)
        open_price = max(low_price, min(high_price, open_price))
        close_price = max(low_price, min(high_price, close_price))
        
        volume = np.random.uniform(1000000, 5000000)
        
        price_data = PriceDataCreate(
            crypto_id=crypto_id,
            timestamp=current_time,
            open_price=Decimal(str(round(open_price, 2))),
            high_price=Decimal(str(round(high_price, 2))),
            low_price=Decimal(str(round(low_price, 2))),
            close_price=Decimal(str(round(close_price, 2))),
            volume=Decimal(str(round(volume, 2))),
            market_cap=Decimal(str(round(close_price * 19000000, 2)))  # Approx BTC supply
            # Note: Removed data_source, data_interval, is_validated as they don't exist in your DB
        )
        
        price_data_repository.create(db, obj_in=price_data)
        current_time += timedelta(hours=1)
    
    db.commit()
    print("✅ Created 200 sample price records")


async def test_data_quality(crypto_id):
    """Test data quality assessment"""
    print("\n🔍 Testing data quality assessment...")
    
    db = SessionLocal()
    try:
        quality_stats = ml_repository.get_data_quality_stats(db, crypto_id)
        
        print(f"📊 Data Quality Results:")
        print(f"   Total records: {quality_stats['total_records']}")
        print(f"   Validated records: {quality_stats['validated_records']}")
        print(f"   Validation rate: {quality_stats['validation_rate']:.2%}")
        print(f"   Data quality score: {quality_stats['data_quality_score']:.2f}")
        print(f"   Data freshness: {quality_stats['data_freshness_hours']:.1f} hours")
        
        return quality_stats['data_quality_score'] >= 0.5
        
    finally:
        db.close()


async def test_training_data_loading(crypto_id):
    """Test training data loading"""
    print("\n📊 Testing training data loading...")
    
    db = SessionLocal()
    try:
        training_df = ml_repository.get_training_data_for_crypto(
            db=db,
            crypto_id=crypto_id,
            days_back=30,
            min_records=50
        )
        
        if training_df.empty:
            print("❌ No training data loaded")
            return False
        
        print(f"✅ Loaded training data: {len(training_df)} records")
        print(f"   Columns: {list(training_df.columns)}")
        print(f"   Date range: {training_df['timestamp'].min()} to {training_df['timestamp'].max()}")
        print(f"   Price range: ${training_df['close_price'].min():.2f} - ${training_df['close_price'].max():.2f}")
        
        return len(training_df) >= 50
        
    finally:
        db.close()


async def test_complete_training_pipeline(crypto_symbol):
    """Test complete training pipeline"""
    print(f"\n🧠 Testing complete training pipeline for {crypto_symbol}...")
    
    # Test training configuration
    training_config = {
        'sequence_length': 24,  # Shorter for testing
        'lstm_units': [16, 16],  # Smaller for testing
        'epochs': 3,  # Very few epochs for testing
        'batch_size': 16
    }
    
    try:
        # Run training
        result = await training_service.train_model_for_crypto(
            crypto_symbol=crypto_symbol,
            training_config=training_config
        )
        
        if result['success']:
            print(f"✅ Training completed successfully!")
            print(f"   Model ID: {result['model_id']}")
            print(f"   Training duration: {result['training_duration']:.2f} seconds")
            print(f"   Data points used: {result['data_points_used']}")
            print(f"   Features count: {result['features_count']}")
            
            # Print training metrics
            if 'training_metrics' in result:
                metrics = result['training_metrics']
                print(f"   Final loss: {metrics.get('final_loss', 'N/A'):.6f}")
                print(f"   Final MAE: {metrics.get('final_mae', 'N/A'):.6f}")
            
            # Print evaluation metrics
            if 'evaluation_metrics' in result:
                eval_metrics = result['evaluation_metrics']
                print(f"   Test R² Score: {eval_metrics.get('r2_score', 'N/A'):.4f}")
                print(f"   Test RMSE: {eval_metrics.get('rmse', 'N/A'):.2f}")
            
            return result
        else:
            print(f"❌ Training failed: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Training pipeline error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_model_registry(crypto_symbol):
    """Test model registry functionality"""
    print(f"\n📋 Testing model registry for {crypto_symbol}...")
    
    # Get training status
    status = await training_service.get_training_status(crypto_symbol)
    
    print(f"📊 Training Status:")
    print(f"   Has active model: {status['has_active_model']}")
    print(f"   Total models: {status['total_models']}")
    
    if status['has_active_model']:
        active_model = status['active_model']
        print(f"   Active model: {active_model['model_type']}")
        print(f"   Performance: {active_model.get('performance_metrics', {})}")
    
    return status['has_active_model']


async def test_prediction_storage(crypto_id, model_id):
    """Test prediction storage and evaluation"""
    print(f"\n💾 Testing prediction storage...")
    
    db = SessionLocal()
    try:
        # Store a test prediction
        prediction_data = {
            'model_name': 'lstm',
            'predicted_price': 47500.0,
            'confidence_score': 0.85,
            'prediction_horizon': 24,
            'target_datetime': datetime.now(timezone.utc) + timedelta(hours=24),
            'input_price': 46000.0,
            'features_used': '{"test": true}',
            'notes': 'Test prediction from pipeline test'
        }
        
        prediction = ml_repository.store_prediction(
            db=db,
            crypto_id=crypto_id,
            model_id=model_id,
            prediction_data=prediction_data,
            user_id=1  
        )
        
        print(f"✅ Stored prediction: ID {prediction.id}")
        
        # Test accuracy evaluation
        actual_price = Decimal('47200.0')  # Simulated actual price
        accuracy_result = ml_repository.evaluate_prediction_accuracy(
            db=db,
            prediction_id=prediction.id,
            actual_price=actual_price
        )
        
        print(f"✅ Evaluated prediction accuracy: {accuracy_result['accuracy_percentage']:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Prediction storage error: {str(e)}")
        return False
        
    finally:
        db.close()


async def test_performance_stats(crypto_id):
    """Test model performance statistics"""
    print(f"\n📈 Testing model performance statistics...")
    
    db = SessionLocal()
    try:
        stats = ml_repository.get_model_performance_stats(
            db=db,
            crypto_id=crypto_id,
            days_back=30
        )
        
        print(f"📊 Performance Statistics:")
        print(f"   Total predictions: {stats['total_predictions']}")
        if stats['total_predictions'] > 0:
            print(f"   Accurate predictions: {stats.get('accurate_predictions', 0)}")
            print(f"   Accuracy rate: {stats.get('accuracy_rate', 0):.2%}")
            print(f"   Average accuracy: {stats.get('avg_accuracy_percentage', 0):.2f}%")
            print(f"   Average error: ${stats.get('avg_absolute_error', 0):.2f}")
        else:
            print("   No predictions available for performance analysis")
        
        return stats['total_predictions'] > 0
        
    except Exception as e:
        print(f"❌ Performance stats error: {str(e)}")
        return False
        
    finally:
        db.close()


async def main():
    """Run complete ML pipeline test"""
    print("🧪 Complete ML Pipeline Integration Test")
    print("=" * 50)
    
    crypto_symbol = "BTC"
    test_results = []
    
    # Initialize database
    db = SessionLocal()
    try:
        # Step 1: Setup test data
        print("\n📋 Step 1: Setting up test data")
        btc_crypto = await setup_test_data(db)
        print(f"✅ Bitcoin crypto ID: {btc_crypto.id}")
        test_results.append(True)
        
    finally:
        db.close()
    
    # Step 2: Test data quality
    print("\n📋 Step 2: Testing data quality")
    quality_ok = await test_data_quality(btc_crypto.id)
    test_results.append(quality_ok)
    
    # Step 3: Test training data loading
    print("\n📋 Step 3: Testing training data loading")
    data_loading_ok = await test_training_data_loading(btc_crypto.id)
    test_results.append(data_loading_ok)
    
    # Step 4: Test complete training pipeline
    print("\n📋 Step 4: Testing complete training pipeline")
    training_result = await test_complete_training_pipeline(crypto_symbol)
    training_ok = training_result is not None
    test_results.append(training_ok)
    
    model_id = None
    if training_ok:
        model_id = training_result['model_id']
    
    # Step 5: Test model registry
    print("\n📋 Step 5: Testing model registry")
    registry_ok = await test_model_registry(crypto_symbol)
    test_results.append(registry_ok)
    
    # Step 6: Test prediction storage (if we have a model)
    if model_id:
        print("\n📋 Step 6: Testing prediction storage")
        prediction_ok = await test_prediction_storage(btc_crypto.id, model_id)
        test_results.append(prediction_ok)
        
        # Step 7: Test performance statistics
        print("\n📋 Step 7: Testing performance statistics")
        stats_ok = await test_performance_stats(btc_crypto.id)
        test_results.append(stats_ok)
    else:
        print("\n⚠️  Skipping steps 6-7 due to training failure")
        test_results.extend([False, False])
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY")
    print("=" * 50)
    
    test_names = [
        "Data Setup",
        "Data Quality", 
        "Data Loading",
        "Training Pipeline",
        "Model Registry",
        "Prediction Storage",
        "Performance Stats"
    ]
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {name:<20} {status}")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! ML Pipeline is ready for production.")
        print("\n🚀 Next steps:")
        print("   1. Add API endpoints for training and prediction")
        print("   2. Set up background tasks for automated training")
        print("   3. Create model evaluation dashboard")
        print("   4. Integrate with real Bitcoin data sources")
    elif passed_tests >= 5:
        print("✅ Core functionality working! Minor issues to fix.")
        print("\n🔧 Recommended fixes:")
        if not test_results[3]:
            print("   - Review training configuration and data requirements")
        if not test_results[5]:
            print("   - Check prediction storage implementation")
        if not test_results[6]:
            print("   - Verify performance statistics calculations")
    else:
        print("❌ Major issues detected. Review the failed components.")
        print("\n🚨 Critical fixes needed:")
        for i, (name, result) in enumerate(zip(test_names, test_results)):
            if not result:
                print(f"   - Fix {name.lower()}")
    
    return passed_tests >= 5


if __name__ == "__main__":
    asyncio.run(main())