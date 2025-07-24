# File: temp/minimal_scaler_test.py
# Minimal test to isolate MinMaxScaler issue

import sys
import os

# Add backend path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

import warnings
warnings.filterwarnings('ignore')

def test_scaler_issue():
    """Minimal test to reproduce scaler issue"""
    
    print("🧪 Minimal Scaler Issue Test")
    print("=" * 40)
    
    try:
        # Step 1: Test LSTM predictor directly
        print("📋 Step 1: Testing LSTM predictor...")
        from app.ml.models.lstm_predictor import LSTMPredictor
        import pandas as pd
        import numpy as np
        
        # Simple test data
        dates = pd.date_range('2023-01-01', periods=100, freq='1H')
        test_data = pd.DataFrame({
            'timestamp': dates,
            'close_price': np.random.uniform(45000, 55000, 100),
            'volume': np.random.uniform(1000, 10000, 100),
            'open_price': np.random.uniform(44000, 54000, 100)
        })
        
        print(f"✅ Created test data: {len(test_data)} records")
        
        # Test LSTM preparation
        lstm = LSTMPredictor(sequence_length=10, n_features=3, epochs=2)
        
        print("   Testing prepare_data...")
        X, y, target_scaler, feature_scaler = lstm.prepare_data(test_data)
        print(f"   ✅ prepare_data OK: X={X.shape}, y={y.shape}")
        print(f"   ✅ Scalers: target={target_scaler is not None}, feature={feature_scaler is not None}")
        
        # Test training
        print("   Testing training...")
        train_size = int(0.8 * len(X))
        X_train, X_val = X[:train_size], X[train_size:]
        y_train, y_val = y[:train_size], y[train_size:]
        
        training_result = lstm.train(X_train, y_train, X_val, y_val, save_model=False)
        print(f"   ✅ Training OK: loss={training_result['final_loss']:.6f}")
        
        # Test prediction - THIS IS WHERE ERROR MIGHT OCCUR
        print("   Testing prediction...")
        predictions, confidence = lstm.predict(X_val[:3])
        print(f"   ✅ Prediction OK: {predictions.shape}")
        
        print("\n✅ ALL TESTS PASSED - No scaler issue found")
        return True
        
    except Exception as e:
        print(f"\n❌ Error found: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_scaler_issue()
