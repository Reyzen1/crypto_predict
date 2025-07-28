# File: temp/check_training_methods.py
# بررسی method signatures در training service

import sys
import inspect
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def check_training_service_methods():
    """بررسی methods موجود در training service"""
    print("🔍 Checking Training Service Methods...")
    print("=" * 50)
    
    try:
        from app.ml.training.training_service import training_service
        
        print("✅ Training service imported successfully")
        print(f"   Type: {type(training_service)}")
        
        # Get all methods
        methods = [method for method in dir(training_service) if not method.startswith('_')]
        print(f"\n📋 Available methods: {len(methods)}")
        for method in methods:
            print(f"   • {method}")
        
        # Check specific method signatures
        target_methods = [
            'train_model_for_crypto',
            'train_model', 
            'start_training',
            'train_crypto_model'
        ]
        
        print(f"\n🔍 Checking target methods:")
        for method_name in target_methods:
            if hasattr(training_service, method_name):
                method = getattr(training_service, method_name)
                try:
                    sig = inspect.signature(method)
                    print(f"   ✅ {method_name}{sig}")
                    
                    # Show parameter details
                    for param_name, param in sig.parameters.items():
                        default = f" = {param.default}" if param.default != inspect.Parameter.empty else ""
                        print(f"      • {param_name}: {param.annotation}{default}")
                        
                except Exception as e:
                    print(f"   ❓ {method_name}: Cannot inspect signature - {e}")
            else:
                print(f"   ❌ {method_name}: NOT FOUND")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_training_service_class():
    """بررسی کلاس MLTrainingService"""
    print("\n🔍 Checking MLTrainingService Class...")
    print("=" * 50)
    
    try:
        from app.ml.training.training_service import MLTrainingService
        
        print("✅ MLTrainingService class imported successfully")
        
        # Create instance
        service = MLTrainingService()
        print("✅ Service instance created")
        
        # Get all methods
        methods = [method for method in dir(service) if not method.startswith('_')]
        print(f"\n📋 Available methods: {len(methods)}")
        for method in methods:
            print(f"   • {method}")
        
        # Check specific method signatures
        target_methods = [
            'train_model_for_crypto',
            'train_model',
            'start_training',
            'train_crypto_model'
        ]
        
        print(f"\n🔍 Checking target methods:")
        for method_name in target_methods:
            if hasattr(service, method_name):
                method = getattr(service, method_name)
                try:
                    sig = inspect.signature(method)
                    print(f"   ✅ {method_name}{sig}")
                    
                    # Show parameter details
                    for param_name, param in sig.parameters.items():
                        default = f" = {param.default}" if param.default != inspect.Parameter.empty else ""
                        annotation = param.annotation if param.annotation != inspect.Parameter.empty else "Any"
                        print(f"      • {param_name}: {annotation}{default}")
                        
                except Exception as e:
                    print(f"   ❓ {method_name}: Cannot inspect signature - {e}")
            else:
                print(f"   ❌ {method_name}: NOT FOUND")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_correct_method_call():
    """تست صحیح method call"""
    print("\n🧪 Testing Correct Method Call...")
    print("=" * 40)
    
    try:
        from app.ml.training.training_service import training_service
        
        # Get the correct signature
        if hasattr(training_service, 'train_model_for_crypto'):
            method = getattr(training_service, 'train_model_for_crypto')
            sig = inspect.signature(method)
            
            print(f"✅ Method signature: train_model_for_crypto{sig}")
            
            # Create test parameters based on actual signature
            test_params = {}
            required_params = []
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                    
                if param.default == inspect.Parameter.empty:
                    required_params.append(param_name)
                    if param_name == 'crypto_symbol':
                        test_params[param_name] = 'BTC'
                    elif 'config' in param_name.lower():
                        test_params[param_name] = {"epochs": 5, "batch_size": 32}
                    else:
                        test_params[param_name] = None
                else:
                    print(f"   Optional param: {param_name} = {param.default}")
            
            print(f"\n📋 Required parameters: {required_params}")
            print(f"📋 Test parameters: {test_params}")
            
            # Show correct call format
            params_str = ", ".join([f"{k}={repr(v)}" for k, v in test_params.items()])
            print(f"\n✅ Correct call format:")
            print(f"   await training_service.train_model_for_crypto({params_str})")
            
            return True
        else:
            print("❌ train_model_for_crypto method not found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """اجرای همه بررسی‌ها"""
    print("🧪 Training Service Method Analysis")
    print("=" * 60)
    
    # Check 1: training_service instance
    service_ok = check_training_service_methods()
    
    # Check 2: MLTrainingService class
    class_ok = check_training_service_class()
    
    # Check 3: Correct method call
    if service_ok or class_ok:
        check_correct_method_call()
    
    print(f"\n📊 Analysis Summary:")
    print(f"   training_service: {'✅' if service_ok else '❌'}")
    print(f"   MLTrainingService: {'✅' if class_ok else '❌'}")

if __name__ == "__main__":
    main()