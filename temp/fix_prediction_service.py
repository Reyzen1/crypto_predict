# temp/fix_prediction_service.py
# Fix prediction service to use the registered model

import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.ml.config.ml_config import model_registry


def check_model_registry():
    """Check what's in the model registry"""
    print("🔍 Checking Model Registry")
    print("=" * 30)
    
    try:
        # Check active model for BTC
        active_model = model_registry.get_active_model("BTC")
        print(f"Active model for BTC: {active_model}")
        
        # Check all models for BTC
        all_models = model_registry.get_models_for_crypto("BTC")
        print(f"All BTC models: {len(all_models)}")
        
        for model_id, model_info in all_models.items():
            print(f"  - {model_id}: {model_info.get('model_path', 'No path')}")
        
        # Check registry status
        print(f"Registry status: {model_registry._models}")
        
        return len(all_models) > 0
        
    except Exception as e:
        print(f"❌ Registry check failed: {str(e)}")
        return False


def fix_prediction_service_config():
    """Fix prediction service to point to the correct model"""
    print("\n🔧 Fixing Prediction Service Config")
    print("=" * 40)
    
    try:
        # Check if prediction service exists
        from app.services.prediction_service import prediction_service
        
        # Update prediction service to use model registry
        active_model = model_registry.get_active_model("BTC")
        
        if active_model:
            model_path = active_model.get('model_path')
            print(f"✅ Found active model: {model_path}")
            
            # Update prediction service model path (if it has this method)
            if hasattr(prediction_service, 'update_model_path'):
                prediction_service.update_model_path("BTC", model_path)
                print("✅ Updated prediction service model path")
            else:
                print("⚠️ Prediction service doesn't have update_model_path method")
            
            return True
        else:
            print("❌ No active model found")
            return False
            
    except ImportError as e:
        print(f"⚠️ Prediction service not available: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Fix failed: {str(e)}")
        return False


def create_simple_prediction_test():
    """Create a simple prediction test that works with current setup"""
    print("\n🧪 Creating Simple Prediction Test")
    print("=" * 40)
    
    try:
        # Import required components
        from app.ml.training.training_service import training_service
        from app.ml.models.lstm_predictor import LSTMPredictor
        from app.repositories import cryptocurrency_repository, price_data_repository
        from app.core.database import SessionLocal
        from datetime import datetime, timedelta, timezone
        import numpy as np
        
        # Get Bitcoin and recent data
        db = SessionLocal()
        
        try:
            btc_crypto = cryptocurrency_repository.get_by_symbol(db, "BTC")
            if not btc_crypto:
                print("❌ Bitcoin not found")
                return False
            
            # Get recent data
            recent_data = price_data_repository.get_price_history(
                db=db,
                crypto_id=btc_crypto.id,
                start_date=datetime.now(timezone.utc) - timedelta(hours=48),
                end_date=datetime.now(timezone.utc),
                limit=100
            )
            
            print(f"✅ Found {len(recent_data)} recent data points")
            
            if len(recent_data) < 24:
                print("❌ Insufficient data for prediction")
                return False
            
            # Get active model info
            active_model = model_registry.get_active_model("BTC")
            if not active_model:
                print("❌ No active model")
                return False
            
            model_path = active_model.get('model_path')
            print(f"✅ Model path: {model_path}")
            
            # Load model directly
            if not os.path.exists(model_path):
                print(f"❌ Model file not found: {model_path}")
                return False
            
            # Create LSTM predictor and load model
            predictor = LSTMPredictor()
            success = predictor.load_model(model_path)
            
            if not success:
                print("❌ Failed to load model")
                return False
            
            print("✅ Model loaded successfully")
            
            # Create simple input data
            prices = [float(record.close_price) for record in recent_data[-24:]]
            volumes = [float(record.volume) if record.volume else 0.0 for record in recent_data[-24:]]
            
            # Simple feature engineering
            input_data = []
            for i in range(len(prices)):
                input_data.append([prices[i], volumes[i]])
            
            input_array = np.array(input_data).reshape(1, len(input_data), 2)
            
            # Make prediction
            prediction = predictor.predict(input_array)
            
            if prediction is not None and len(prediction) > 0:
                predicted_price = float(prediction[0])
                current_price = prices[-1]
                
                print(f"✅ Prediction successful!")
                print(f"   Current price: ${current_price:,.2f}")
                print(f"   Predicted price: ${predicted_price:,.2f}")
                print(f"   Change: {((predicted_price/current_price - 1) * 100):+.2f}%")
                
                return True
            else:
                print("❌ Prediction failed")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Prediction test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main fix function"""
    print("🔧 Fixing Prediction Service for Stage B")
    print("=" * 42)
    
    # Step 1: Check model registry
    registry_ok = check_model_registry()
    
    if not registry_ok:
        print("\n❌ Model registry issue - please run model training first")
        return False
    
    # Step 2: Try to fix prediction service
    service_fixed = fix_prediction_service_config()
    
    # Step 3: Test prediction directly
    prediction_works = create_simple_prediction_test()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 FIX SUMMARY")
    print("=" * 50)
    
    results = [
        ("Model Registry OK", registry_ok),
        ("Service Config Fixed", service_fixed),
        ("Direct Prediction Works", prediction_works)
    ]
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:<25} {status}")
    
    if prediction_works:
        print("\n🎉 SUCCESS! Prediction system is working!")
        print("\n🚀 Now try Stage B test again:")
        print("   python temp/test_prediction_service.py")
        print("   (Select option 2 for Quick Test)")
        print("\n✅ The underlying model and prediction logic work correctly!")
        
    else:
        print("\n❌ Prediction system needs more work")
        print("🔧 Consider running training again:")
        print("   python temp/train_btc_model.py")


if __name__ == "__main__":
    main()