# temp/check_model_status.py
# Check status of existing trained models

import asyncio
import sys
import os
import glob

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.ml.training.training_service import training_service
from app.ml.config.ml_config import ml_config


def check_model_files():
    """Check if model files exist on disk"""
    print("📁 Checking Model Files")
    print("=" * 25)
    
    models_dir = ml_config.models_storage_path
    print(f"Models directory: {models_dir}")
    
    if not os.path.exists(models_dir):
        print(f"❌ Models directory doesn't exist: {models_dir}")
        return False
    
    # Look for BTC model files
    btc_models = glob.glob(os.path.join(models_dir, "*btc*"))
    btc_models.extend(glob.glob(os.path.join(models_dir, "*BTC*")))
    
    print(f"🔍 Found {len(btc_models)} BTC model files:")
    for model_file in btc_models:
        file_size = os.path.getsize(model_file) / (1024*1024)  # MB
        mod_time = os.path.getmtime(model_file)
        from datetime import datetime
        mod_date = datetime.fromtimestamp(mod_time)
        print(f"   📄 {os.path.basename(model_file)} ({file_size:.1f}MB, {mod_date})")
    
    return len(btc_models) > 0


async def check_training_status():
    """Check training status in registry"""
    print("\n🧠 Checking Training Status")
    print("=" * 30)
    
    try:
        status = await training_service.get_training_status("BTC")
        
        print(f"📊 Bitcoin Training Status:")
        print(f"   Has active model: {status['has_active_model']}")
        print(f"   Total models: {status['total_models']}")
        
        if status['has_active_model']:
            print(f"   Active model ID: {status.get('active_model_id', 'Unknown')}")
            
            metrics = status.get('performance_metrics', {})
            if metrics:
                print(f"   Performance Metrics:")
                for key, value in metrics.items():
                    if isinstance(value, float):
                        print(f"      {key}: {value:.4f}")
                    else:
                        print(f"      {key}: {value}")
            
            return True
        else:
            print("❌ No active model registered")
            return False
            
    except Exception as e:
        print(f"❌ Error checking status: {str(e)}")
        return False


async def try_register_existing_model():
    """Try to register existing model if found"""
    print("\n🔧 Attempting Model Registration")
    print("=" * 35)
    
    # Check if model files exist but not registered
    models_dir = ml_config.models_storage_path
    btc_models = []
    
    if os.path.exists(models_dir):
        btc_models = glob.glob(os.path.join(models_dir, "*btc*.h5"))
        btc_models.extend(glob.glob(os.path.join(models_dir, "*BTC*.h5")))
    
    if not btc_models:
        print("❌ No BTC model files found")
        return False
    
    # Get the most recent model
    latest_model = max(btc_models, key=os.path.getmtime)
    print(f"📄 Latest model file: {os.path.basename(latest_model)}")
    
    try:
        # Extract model ID from filename
        model_filename = os.path.basename(latest_model)
        model_id = model_filename.replace('.h5', '')
        
        print(f"🔄 Attempting to register model: {model_id}")
        
        # Try to manually register using model registry
        from app.ml.config.ml_config import model_registry
        
        # Basic model info
        model_info = {
            'model_id': model_id,
            'crypto_symbol': 'BTC',
            'model_type': 'lstm',
            'model_path': latest_model,
            'performance_metrics': {'manual_registration': True},
            'metadata': {'registered_manually': True}
        }
        
        model_registry.register_model(**model_info)
        model_registry.set_active_model('BTC', model_id)
        
        print(f"✅ Model registered successfully: {model_id}")
        return True
        
    except Exception as e:
        print(f"❌ Registration failed: {str(e)}")
        return False


async def main():
    """Main function to check and fix model status"""
    print("🔍 Model Status Diagnostic")
    print("=" * 27)
    
    # Step 1: Check model files
    files_exist = check_model_files()
    
    # Step 2: Check training status
    status_ok = await check_training_status()
    
    # Step 3: Fix if needed
    if files_exist and not status_ok:
        print("\n🔧 Model files found but not registered - attempting fix...")
        registration_ok = await try_register_existing_model()
        
        if registration_ok:
            # Re-check status
            print("\n🔄 Re-checking status after registration...")
            status_ok = await check_training_status()
    
    # Summary
    print("\n" + "=" * 40)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 40)
    
    results = [
        ("Model Files Exist", files_exist),
        ("Training Status OK", status_ok)
    ]
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:<20} {status}")
    
    if files_exist and status_ok:
        print("\n🎉 SUCCESS! Model is ready")
        print("\n🚀 Next step:")
        print("   python temp/test_prediction_service.py")
        print("   (Select option 2 for Quick Test)")
        
    elif files_exist and not status_ok:
        print("\n⚠️ Model files exist but registration failed")
        print("🔧 Try re-running training:")
        print("   python temp/train_btc_model.py")
        
    else:
        print("\n❌ No model found - need to train")
        print("🔧 Run training:")
        print("   python temp/train_btc_model.py")


if __name__ == "__main__":
    asyncio.run(main())