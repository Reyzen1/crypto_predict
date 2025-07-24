# File: temp/simple_training_test.py
# تست ساده training pipeline بعد از اصلاح مشکل scaler

import sys
sys.path.append('.')
import warnings
warnings.filterwarnings('ignore')

print("🧪 تست ساده Training Pipeline")
print("=" * 40)

try:
    # Step 1: Import ها
    print("📋 Step 1: Testing imports...")
    from app.ml.models.lstm_predictor import LSTMPredictor
    from app.ml.training.training_service import MLTrainingService
    import pandas as pd
    import numpy as np
    print("✅ همه imports موفق")
    
    # Step 2: ایجاد test data
    print("\n📋 Step 2: Creating test data...")
    dates = pd.date_range('2023-01-01', periods=100, freq='1H')
    test_data = pd.DataFrame({
        'timestamp': dates,
        'open_price': np.random.uniform(45000, 55000, 100),
        'high_price': np.random.uniform(46000, 56000, 100),
        'low_price': np.random.uniform(44000, 54000, 100),
        'close_price': np.random.uniform(45000, 55000, 100),
        'volume': np.random.uniform(1000, 10000, 100),
        'market_cap': np.random.uniform(800000000, 1200000000, 100)
    })
    
    # Fix price relationships
    test_data['high_price'] = np.maximum(test_data['high_price'], 
                                       np.maximum(test_data['open_price'], test_data['close_price']))
    test_data['low_price'] = np.minimum(test_data['low_price'], 
                                      np.minimum(test_data['open_price'], test_data['close_price']))
    
    print(f"✅ Test data created: {len(test_data)} records")
    
    # Step 3: تست LSTM prepare_data
    print("\n📋 Step 3: Testing LSTM prepare_data...")
    lstm = LSTMPredictor(
        sequence_length=10,  # کوتاه برای تست
        n_features=3,
        epochs=2  # کم برای تست سریع
    )
    
    X, y, target_scaler, feature_scaler = lstm.prepare_data(test_data)
    
    print(f"✅ prepare_data successful:")
    print(f"   - X shape: {X.shape}")
    print(f"   - y shape: {y.shape}")
    print(f"   - Target scaler fitted: {target_scaler is not None}")
    print(f"   - Feature scaler fitted: {feature_scaler is not None}")
    
    # Step 4: تست model building
    print("\n📋 Step 4: Testing model building...")
    model = lstm.build_model()
    print(f"✅ Model built with {model.count_params()} parameters")
    
    # Step 5: تست training (فقط چند epoch)
    print("\n📋 Step 5: Testing training...")
    
    # Split data for training
    train_size = int(0.8 * len(X))
    X_train, X_val = X[:train_size], X[train_size:]
    y_train, y_val = y[:train_size], y[train_size:]
    
    print(f"   - Training data: {X_train.shape[0]} samples")
    print(f"   - Validation data: {X_val.shape[0]} samples")
    
    # Training
    training_result = lstm.train(X_train, y_train, X_val, y_val, save_model=False)
    
    print(f"✅ Training completed:")
    print(f"   - Final loss: {training_result['final_loss']:.6f}")
    print(f"   - Final val_loss: {training_result['final_val_loss']:.6f}")
    print(f"   - Duration: {training_result['training_duration_seconds']:.2f}s")
    print(f"   - Epochs trained: {training_result['epochs_trained']}")
    
    # Step 6: تست prediction
    print("\n📋 Step 6: Testing prediction...")
    predictions, confidence = lstm.predict(X_val[:5])
    
    print(f"✅ Prediction successful:")
    print(f"   - Predictions shape: {predictions.shape}")
    print(f"   - Sample predictions: {predictions[:3]}")
    print(f"   - Confidence intervals: {confidence is not None}")
    
    print("\n🎉 همه تست‌ها موفق!")
    print("=" * 40)
    print("مشکل MinMaxScaler برطرف شده است.")
    print("حالا می‌توانید training pipeline کامل را اجرا کنید.")
    
except Exception as e:
    print(f"\n❌ خطا در تست: {e}")
    import traceback
    traceback.print_exc()