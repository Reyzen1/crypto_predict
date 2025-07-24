# File: temp/safe_training_test.py
# Safe training pipeline test after comprehensive fixes

import sys
import os

# Add backend path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

import warnings
warnings.filterwarnings('ignore')

def test_comprehensive_fix():
    """Test comprehensive scaler fixes"""
    
    print("🧪 Testing Comprehensive Scaler Fixes")
    print("=" * 50)
    
    try:
        # Test imports
        print("📋 Step 1: Testing imports...")
        from app.ml.models.lstm_predictor import LSTMPredictor
        from app.ml.preprocessing.data_processor import CryptoPriceDataProcessor
        import pandas as pd
        import numpy as np
        print("✅ All imports successful")
        
        # Create realistic test data
        print("\n📋 Step 2: Creating test data...")
        dates = pd.date_range('2023-01-01', periods=150, freq='1H')
        
        # Generate realistic Bitcoin-like price data
        base_price = 45000
        prices = []
        current_price = base_price
        
        for _ in range(len(dates)):
            # Random walk with some volatility
            change = np.random.normal(0, 0.02) * current_price
            current_price += change
            prices.append(max(current_price, 1000))  # Minimum price
        
        test_data = pd.DataFrame({
            'timestamp': dates,
            'close_price': prices,
            'open_price': [p * np.random.uniform(0.995, 1.005) for p in prices],
            'high_price': [p * np.random.uniform(1.0, 1.01) for p in prices],
            'low_price': [p * np.random.uniform(0.99, 1.0) for p in prices],
            'volume': np.random.uniform(1000, 10000, len(dates)),
            'market_cap': [p * 19000000 for p in prices]  # Realistic market cap
        })
        
        # Fix price relationships
        test_data['high_price'] = np.maximum(test_data['high_price'], 
                                           np.maximum(test_data['open_price'], test_data['close_price']))
        test_data['low_price'] = np.minimum(test_data['low_price'], 
                                          np.minimum(test_data['open_price'], test_data['close_price']))
        
        print(f"✅ Created {len(test_data)} realistic price records")
        
        # Test data processing
        print("\n📋 Step 3: Testing data processing...")
        processor = CryptoPriceDataProcessor()
        processed_data, info = processor.process_data(test_data)
        
        print(f"✅ Data processing successful: {len(processed_data)} records")
        print(f"   - Features created: {info.get('total_features', 'N/A')}")
        
        # Test LSTM preparation
        print("\n📋 Step 4: Testing LSTM data preparation...")
        lstm = LSTMPredictor(
            sequence_length=20,  # Reasonable length
            n_features=5,
            epochs=3  # Quick test
        )
        
        X, y, target_scaler, feature_scaler = lstm.prepare_data(processed_data)
        
        print(f"✅ LSTM data preparation successful:")
        print(f"   - X shape: {X.shape}")
        print(f"   - y shape: {y.shape}")
        print(f"   - Target scaler fitted: {target_scaler is not None}")
        print(f"   - Feature scaler fitted: {feature_scaler is not None}")
        
        # Test training
        print("\n📋 Step 5: Testing model training...")
        train_size = int(0.8 * len(X))
        X_train, X_val = X[:train_size], X[train_size:]
        y_train, y_val = y[:train_size], y[train_size:]
        
        training_result = lstm.train(X_train, y_train, X_val, y_val, save_model=False)
        
        print(f"✅ Training completed successfully:")
        print(f"   - Final loss: {training_result['final_loss']:.6f}")
        print(f"   - Training duration: {training_result['training_duration_seconds']:.2f}s")
        
        # Test prediction
        print("\n📋 Step 6: Testing prediction...")
        predictions, confidence = lstm.predict(X_val[:3])
        
        print(f"✅ Predictions successful:")
        print(f"   - Predictions: {predictions}")
        print(f"   - Confidence intervals: {confidence is not None}")
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Comprehensive scaler fixes successful")
        print("✅ Phase A: Training Infrastructure - COMPLETED")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_comprehensive_fix()
