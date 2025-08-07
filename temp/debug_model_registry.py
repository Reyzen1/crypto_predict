# File: temp/debug_model_registry.py
# بررسی اینکه مدل‌ها کجا ذخیره می‌شوند و چرا نمایش داده نمی‌شوند

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def check_model_registry():
    """بررسی model registry"""
    print("🔍 Checking Model Registry...")
    print("=" * 40)
    
    try:
        from app.ml.config.ml_config import model_registry
        
        print("✅ Model registry imported successfully")
        print(f"   Type: {type(model_registry)}")
        
        # Check available methods
        methods = [method for method in dir(model_registry) if not method.startswith('_')]
        print(f"   Available methods: {methods}")
        
        # Try to get all models
        try:
            all_models = model_registry.list_models()
            print(f"✅ Found {len(all_models)} models in registry:")
            
            for model in all_models:
                print(f"   • {model}")
                
        except Exception as e:
            print(f"❌ Error listing models: {str(e)}")
            
        # Check if there are any registered models for BTC
        try:
            btc_models = model_registry.get_models_for_crypto("BTC")
            print(f"✅ BTC models: {len(btc_models) if btc_models else 0}")
            
            if btc_models:
                for model in btc_models:
                    print(f"   • BTC Model: {model}")
            else:
                print("   No BTC models found")
                
        except Exception as e:
            print(f"❌ Error getting BTC models: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model registry check failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_models_storage_path():
    """بررسی مسیر ذخیره مدل‌ها"""
    print("\n🗂️ Checking Model Storage Path...")
    print("=" * 40)
    
    try:
        from app.ml.config.ml_config import ml_config
        
        storage_path = ml_config.models_storage_path
        print(f"✅ Model storage path: {storage_path}")
        
        # Check if path exists
        storage_dir = Path(storage_path)
        if storage_dir.exists():
            print("✅ Storage directory exists")
            
            # List files in storage
            model_files = list(storage_dir.glob("*"))
            print(f"   Files in storage: {len(model_files)}")
            
            for file in model_files:
                print(f"   • {file.name}")
                
        else:
            print("❌ Storage directory does not exist")
            
        return True
        
    except Exception as e:
        print(f"❌ Storage path check failed: {str(e)}")
        return False

def check_training_results():
    """بررسی نتایج training در database"""
    print("\n💾 Checking Training Results in Database...")
    print("=" * 45)
    
    try:
        from app.core.database import SessionLocal
        from app.models import Prediction
        
        db = SessionLocal()
        
        # Check if there are any predictions/models in database
        predictions = db.query(Prediction).all()
        print(f"✅ Found {len(predictions)} predictions in database")
        
        for pred in predictions[:5]:  # Show first 5
            print(f"   • Prediction: {pred.id} - {pred.model_name} - {pred.crypto_id}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {str(e)}")
        return False

def check_training_service_result():
    """بررسی آیا training service درست model می‌سازد"""
    print("\n🧪 Testing Training Service Result...")
    print("=" * 40)
    
    try:
        from app.ml.training.training_service import training_service
        
        print("✅ Training service imported")
        
        # Check if there's a way to get recent training results
        if hasattr(training_service, 'get_recent_models'):
            recent = training_service.get_recent_models()
            print(f"✅ Recent models: {recent}")
        else:
            print("❓ No get_recent_models method")
            
        # Check training service methods
        methods = [m for m in dir(training_service) if not m.startswith('_')]
        print(f"   Training service methods: {methods}")
        
        return True
        
    except Exception as e:
        print(f"❌ Training service check failed: {str(e)}")
        return False

def main():
    """اجرای همه بررسی‌ها"""
    print("🔍 Model Registry Debug Session")
    print("=" * 50)
    
    # Check 1: Model Registry
    registry_ok = check_model_registry()
    
    # Check 2: Storage Path
    storage_ok = check_models_storage_path()
    
    # Check 3: Database
    db_ok = check_training_results()
    
    # Check 4: Training Service
    service_ok = check_training_service_result()
    
    print(f"\n📊 Debug Summary:")
    print(f"   Model Registry: {'✅' if registry_ok else '❌'}")
    print(f"   Storage Path: {'✅' if storage_ok else '❌'}")
    print(f"   Database: {'✅' if db_ok else '❌'}")
    print(f"   Training Service: {'✅' if service_ok else '❌'}")
    
    print(f"\n💡 Likely Issue:")
    if not registry_ok:
        print("   • Model registry is not working properly")
    elif not storage_ok:
        print("   • Model storage path issue")
    else:
        print("   • Models are trained but not properly registered in registry")

if __name__ == "__main__":
    main()