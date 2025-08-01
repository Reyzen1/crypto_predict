# File: temp/test_ml_setup.py
# Script to test ML setup and basic functionality

"""
Test ML Setup
=============

This script tests the ML environment setup and basic functionality:
- Import all ML libraries
- Test TensorFlow/Keras functionality
- Test data processing capabilities
- Test technical analysis functions
- Create sample LSTM model
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

def test_imports():
    """Test importing all required ML libraries"""
    print("🔍 Testing ML Library Imports")
    print("=" * 40)
    
    import_tests = [
        ("TensorFlow", "import tensorflow as tf; print(f'TensorFlow {tf.__version__}')"),
        ("Keras", "from tensorflow import keras; print(f'Keras {keras.__version__}')"),
        ("NumPy", "import numpy as np; print(f'NumPy {np.__version__}')"),
        ("Pandas", "import pandas as pd; print(f'Pandas {pd.__version__}')"),
        ("Scikit-learn", "import sklearn; print(f'Scikit-learn {sklearn.__version__}')"),
        ("Matplotlib", "import matplotlib; print(f'Matplotlib {matplotlib.__version__}')"),
        ("Seaborn", "import seaborn; print(f'Seaborn {seaborn.__version__}')"),
        ("Plotly", "import plotly; print(f'Plotly {plotly.__version__}')"),
        ("SciPy", "import scipy; print(f'SciPy {scipy.__version__}')"),
        ("TA (Technical Analysis)", "import ta; print('TA library imported successfully')"),
        ("Joblib", "import joblib; print(f'Joblib {joblib.__version__}')"),
        ("Polars", "import polars as pl; print(f'Polars {pl.__version__}')"),
    ]
    
    successful_imports = 0
    
    for name, import_code in import_tests:
        try:
            exec(import_code)
            print(f"✅ {name}")
            successful_imports += 1
        except ImportError as e:
            print(f"❌ {name}: {e}")
        except Exception as e:
            print(f"⚠️ {name}: {e}")
    
    print(f"\n📊 Import Success Rate: {successful_imports}/{len(import_tests)}")
    return successful_imports == len(import_tests)

def test_tensorflow():
    """Test TensorFlow basic functionality"""
    print("\n🧠 Testing TensorFlow Functionality")
    print("=" * 40)
    
    try:
        import tensorflow as tf
        
        # Check TensorFlow configuration
        print(f"TensorFlow version: {tf.__version__}")
        print(f"GPU available: {len(tf.config.list_physical_devices('GPU')) > 0}")
        print(f"CPU threads: {tf.config.threading.get_inter_op_parallelism_threads()}")
        
        # Test basic tensor operations
        a = tf.constant([1, 2, 3])
        b = tf.constant([4, 5, 6])
        c = tf.add(a, b)
        print(f"Tensor operation test: [1,2,3] + [4,5,6] = {c.numpy()}")
        
        # Test creating a simple model
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(10, activation='relu', input_shape=(5,)),
            tf.keras.layers.Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        print("✅ Simple Keras model created and compiled successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ TensorFlow test failed: {e}")
        return False

def test_data_processing():
    """Test data processing capabilities"""
    print("\n📊 Testing Data Processing")
    print("=" * 40)
    
    try:
        import pandas as pd
        import numpy as np
        from sklearn.preprocessing import MinMaxScaler
        import ta
        
        # Create sample cryptocurrency data
        dates = pd.date_range('2023-01-01', periods=100, freq='1H')
        np.random.seed(42)
        
        # Simulate price data
        price_data = {
            'timestamp': dates,
            'open_price': np.random.uniform(45000, 55000, 100),
            'high_price': np.random.uniform(46000, 56000, 100),
            'low_price': np.random.uniform(44000, 54000, 100),
            'close_price': np.random.uniform(45000, 55000, 100),
            'volume': np.random.uniform(1000, 10000, 100)
        }
        
        df = pd.DataFrame(price_data)
        
        # Ensure high >= max(open, close) and low <= min(open, close)
        df['high_price'] = np.maximum(df['high_price'], np.maximum(df['open_price'], df['close_price']))
        df['low_price'] = np.minimum(df['low_price'], np.minimum(df['open_price'], df['close_price']))
        
        print(f"✅ Created sample data: {len(df)} records")
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        # Test technical indicators
        df['sma_20'] = ta.trend.sma_indicator(df['close_price'], window=20)
        df['rsi'] = ta.momentum.rsi(df['close_price'], window=14)
        df['macd'] = ta.trend.macd(df['close_price'])
        
        print("✅ Technical indicators calculated successfully")
        
        # Test data scaling
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(df[['close_price', 'volume']].fillna(0))
        print("✅ Data scaling successful")
        
        # Test sequence creation for LSTM
        def create_sequences(data, seq_length=10):
            X, y = [], []
            for i in range(seq_length, len(data)):
                X.append(data[i-seq_length:i])
                y.append(data[i, 0])  # close_price
            return np.array(X), np.array(y)
        
        X, y = create_sequences(scaled_data, seq_length=10)
        print(f"✅ LSTM sequences created: X shape {X.shape}, y shape {y.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data processing test failed: {e}")
        return False

def test_lstm_model():
    """Test creating and training a simple LSTM model"""
    print("\n🎯 Testing LSTM Model Creation")
    print("=" * 40)
    
    try:
        import tensorflow as tf
        import numpy as np
        
        # Create sample data
        sequence_length = 10
        n_features = 2
        n_samples = 100
        
        X = np.random.random((n_samples, sequence_length, n_features))
        y = np.random.random((n_samples, 1))
        
        # Create LSTM model
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(50, return_sequences=True, input_shape=(sequence_length, n_features)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.LSTM(50),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(25),
            tf.keras.layers.Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        print("✅ LSTM model created and compiled")
        
        # Test model summary
        print("\n📋 Model Architecture:")
        model.summary()
        
        # Test model training (just a few epochs)
        print("\n🏋️ Testing model training...")
        history = model.fit(X, y, epochs=2, batch_size=16, verbose=0, validation_split=0.2)
        
        final_loss = history.history['loss'][-1]
        print(f"✅ Model training successful - Final loss: {final_loss:.6f}")
        
        # Test prediction
        predictions = model.predict(X[:5], verbose=0)
        print(f"✅ Model prediction successful - Sample predictions shape: {predictions.shape}")
        
        return True
        
    except Exception as e:
        print(f"❌ LSTM model test failed: {e}")
        return False

def test_performance():
    """Test performance of key operations"""
    print("\n⚡ Testing Performance")
    print("=" * 40)
    
    try:
        import time
        import numpy as np
        import pandas as pd
        
        # Test NumPy performance
        start_time = time.time()
        large_array = np.random.random((10000, 100))
        result = np.dot(large_array, large_array.T)
        numpy_time = time.time() - start_time
        print(f"✅ NumPy matrix multiplication (10k×100): {numpy_time:.4f}s")
        
        # Test Pandas performance
        start_time = time.time()
        large_df = pd.DataFrame(np.random.random((50000, 10)))
        grouped = large_df.groupby(0).mean()
        pandas_time = time.time() - start_time
        print(f"✅ Pandas groupby operation (50k rows): {pandas_time:.4f}s")
        
        # Test Polars performance (if available)
        try:
            import polars as pl
            start_time = time.time()
            large_pl_df = pl.DataFrame(np.random.random((50000, 10)))
            grouped_pl = large_pl_df.groupby(large_pl_df.columns[0]).mean()
            polars_time = time.time() - start_time
            print(f"✅ Polars groupby operation (50k rows): {polars_time:.4f}s")
            print(f"📊 Polars vs Pandas speedup: {pandas_time/polars_time:.2f}x")
        except ImportError:
            print("⚠️ Polars not available for performance comparison")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 CryptoPredict ML Environment Test")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print("")
    
    tests = [
        ("Library Imports", test_imports),
        ("TensorFlow Functionality", test_tensorflow),
        ("Data Processing", test_data_processing),
        ("LSTM Model", test_lstm_model),
        ("Performance", test_performance)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
                print(f"\n✅ {test_name}: PASSED")
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\n💥 {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! ML environment is ready.")
        print("\n🚀 Next steps:")
        print("1. Run: bash temp/create_ml_structure.sh")
        print("2. Add ML model files to backend/app/models/")
        print("3. Create database migration")
        print("4. Start building your LSTM model!")
        return True
    else:
        print("⚠️ Some tests failed. Please check the error messages above.")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure all dependencies are installed correctly")
        print("2. Check Python version compatibility (3.8-3.11 recommended)")
        print("3. Run: pip install --upgrade pip setuptools")
        print("4. Try reinstalling failed packages individually")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)