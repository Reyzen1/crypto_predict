# File: temp/find_scaler_error_location.py
# Find the exact location where MinMaxScaler error is happening

import sys
import os

def find_test_pipeline_file():
    """Find and analyze the test_complete_ml_pipeline.py file"""
    
    test_file = 'temp/test_complete_ml_pipeline.py'
    
    if not os.path.exists(test_file):
        print(f"❌ Test file {test_file} not found")
        return False
    
    print("🔍 Analyzing test_complete_ml_pipeline.py...")
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        print("📋 Looking for LSTM training section...")
        
        # Find the training section
        for i, line in enumerate(lines):
            if 'Testing complete training pipeline' in line:
                print(f"✅ Found training section at line {i+1}")
                
                # Show the next 20 lines to see what's happening
                print("\n📄 Training section code:")
                for j in range(i, min(i+30, len(lines))):
                    print(f"{j+1:3d}: {lines[j]}")
                
                break
        
        # Look for specific scaler usage
        scaler_lines = []
        for i, line in enumerate(lines):
            if 'scaler' in line.lower() and ('fit' in line or 'transform' in line):
                scaler_lines.append((i+1, line.strip()))
        
        if scaler_lines:
            print(f"\n🔍 Found {len(scaler_lines)} lines with scaler usage:")
            for line_num, line_content in scaler_lines:
                print(f"   Line {line_num}: {line_content}")
        
        # Look for training service calls
        training_calls = []
        for i, line in enumerate(lines):
            if 'train_model_for_crypto' in line or 'training_service' in line:
                training_calls.append((i+1, line.strip()))
        
        if training_calls:
            print(f"\n🔍 Found {len(training_calls)} training service calls:")
            for line_num, line_content in training_calls:
                print(f"   Line {line_num}: {line_content}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing file: {e}")
        return False

def create_minimal_test():
    """Create a minimal test to isolate the scaler issue"""
    
    minimal_test = '''# File: temp/minimal_scaler_test.py
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
        
        print("\\n✅ ALL TESTS PASSED - No scaler issue found")
        return True
        
    except Exception as e:
        print(f"\\n❌ Error found: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_scaler_issue()
'''
    
    with open('temp/minimal_scaler_test.py', 'w', encoding='utf-8') as f:
        f.write(minimal_test)
    
    print("✅ Created minimal test: temp/minimal_scaler_test.py")

if __name__ == "__main__":
    print("🔍 Finding MinMaxScaler Error Location")
    print("=" * 50)
    
    if find_test_pipeline_file():
        create_minimal_test()
        print("\n🚀 Next steps:")
        print("1. Run: python temp/minimal_scaler_test.py")
        print("2. This will help isolate the exact scaler issue")
    else:
        print("❌ Could not analyze test file")