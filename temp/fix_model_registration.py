# File: temp/fix_model_registration.py
# اصلاح مشکل model registration در training service

"""
مشکل: در training_service.py، قسمت model registration failed می‌شود

راه حل: بررسی model_registry.register_model method signature و اصلاح call
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def check_model_registry_signature():
    """بررسی signature method register_model"""
    print("🔍 Checking ModelRegistry.register_model signature...")
    print("=" * 50)
    
    try:
        from app.ml.config.ml_config import model_registry
        import inspect
        
        # Get register_model method signature
        register_method = getattr(model_registry, 'register_model')
        sig = inspect.signature(register_method)
        
        print("✅ register_model signature:")
        print(f"   {register_method.__name__}{sig}")
        
        # Show parameter details
        for param_name, param in sig.parameters.items():
            default = f" = {param.default}" if param.default != inspect.Parameter.empty else ""
            annotation = param.annotation if param.annotation != inspect.Parameter.empty else "Any"
            print(f"   • {param_name}: {annotation}{default}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_registration():
    """تست دستی model registration"""
    print("\n🧪 Testing Manual Model Registration...")
    print("=" * 45)
    
    try:
        from app.ml.config.ml_config import model_registry
        import os
        from datetime import datetime
        
        # Find existing model files
        models_dir = "models"
        if not os.path.exists(models_dir):
            print(f"❌ Models directory not found: {models_dir}")
            return False
        
        # Get latest BTC model
        btc_files = [f for f in os.listdir(models_dir) if f.endswith('.h5') and 'BTC' in f]
        if not btc_files:
            print("❌ No BTC model files found")
            return False
        
        latest_model = max(btc_files)
        model_path = os.path.join(models_dir, latest_model)
        model_id = latest_model.replace('.h5', '')
        
        print(f"📄 Using model: {latest_model}")
        print(f"📍 Model path: {model_path}")
        print(f"🔖 Model ID: {model_id}")
        
        # Test 1: Basic registration
        print("\n🔧 Test 1: Basic Registration")
        try:
            # Try basic call with minimal parameters
            model_registry.register_model(
                model_id=model_id,
                crypto_symbol="BTC",
                model_type="lstm",
                model_path=model_path
                # Remove problematic parameters for now
            )
            print("✅ Basic registration successful")
            
            # Set as active
            model_registry.set_active_model("BTC", model_id)
            print("✅ Set as active model")
            
            return True
            
        except Exception as e:
            print(f"❌ Basic registration failed: {str(e)}")
            
            # Test 2: Try with different parameters
            print("\n🔧 Test 2: Alternative Registration")
            try:
                # Clear any existing data first
                if hasattr(model_registry, 'models'):
                    model_registry.models = {}
                if hasattr(model_registry, 'active_models'):
                    model_registry.active_models = {}
                
                # Try different approach
                model_registry.register_model(
                    model_id=model_id,
                    crypto_symbol="BTC",
                    model_type="lstm",
                    model_path=model_path,
                    performance_metrics={"registered_manually": True},
                    metadata={"created_at": datetime.now().isoformat()}
                )
                print("✅ Alternative registration successful")
                
                model_registry.set_active_model("BTC", model_id)
                print("✅ Set as active model")
                
                return True
                
            except Exception as e2:
                print(f"❌ Alternative registration failed: {str(e2)}")
                return False
        
    except Exception as e:
        print(f"❌ Manual registration test failed: {str(e)}")
        return False

def verify_registration():
    """تأیید اینکه registration موفق بوده"""
    print("\n✅ Verifying Registration...")
    print("=" * 30)
    
    try:
        from app.ml.config.ml_config import model_registry
        
        # Check models list
        models = model_registry.list_models()
        print(f"📋 Total models: {len(models)}")
        
        for model in models:
            print(f"   • {model}")
        
        # Check active model for BTC
        active_model = model_registry.get_active_model("BTC")
        if active_model:
            print(f"🎯 Active BTC model: {active_model}")
            return True
        else:
            print("❌ No active BTC model")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def main():
    """Main execution"""
    print("🔧 Model Registration Fix")
    print("=" * 25)
    
    # Step 1: Check signature
    signature_ok = check_model_registry_signature()
    
    # Step 2: Test manual registration
    if signature_ok:
        registration_ok = test_manual_registration()
        
        # Step 3: Verify
        if registration_ok:
            verify_registration()
    
    print("\n💡 If manual registration worked, the issue was in the")
    print("   training_service.py model registration call parameters.")

if __name__ == "__main__":
    main()