# File: temp/complete_model_fix.py
# اصلاح کامل مشکل model registration و تست

import sys
import os
import glob
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def fix_and_register_models():
    """اصلاح model registry و registration مدل‌های موجود"""
    print("🔧 Complete Model Registration Fix")
    print("=" * 40)
    
    try:
        from app.ml.config.ml_config import model_registry, ml_config
        
        # Step 1: Clear any problematic data
        print("📝 Step 1: Clearing registry...")
        model_registry.models = {}
        model_registry.active_models = {}
        print("   ✅ Registry cleared")
        
        # Step 2: Find model files
        print("\n📁 Step 2: Finding model files...")
        models_dir = ml_config.models_storage_path
        
        if not os.path.exists(models_dir):
            print(f"   ❌ Models directory not found: {models_dir}")
            return False
        
        # Find BTC models
        btc_files = []
        for pattern in ["*btc*.h5", "*BTC*.h5"]:
            btc_files.extend(glob.glob(os.path.join(models_dir, pattern)))
        
        if not btc_files:
            print("   ❌ No BTC model files found")
            return False
        
        print(f"   ✅ Found {len(btc_files)} BTC model files")
        
        # Step 3: Register models manually
        print("\n🔄 Step 3: Registering models...")
        registered_count = 0
        
        for model_file in btc_files:
            try:
                filename = os.path.basename(model_file)
                model_id = filename.replace('.h5', '')
                
                print(f"   📝 Registering: {model_id}")
                
                # Create complete model data
                model_data = {
                    'crypto_symbol': 'BTC',
                    'model_type': 'lstm',
                    'model_path': model_file,
                    'performance_metrics': {
                        'manually_registered': True,
                        'file_size': os.path.getsize(model_file)
                    },
                    'metadata': {
                        'created_at': datetime.now().isoformat(),
                        'registration_method': 'manual_fix'
                    },
                    'registered_at': datetime.now().isoformat(),
                    'is_active': False
                }
                
                # Directly add to registry (bypass any problematic register_model method)
                model_registry.models[model_id] = model_data
                registered_count += 1
                
                print(f"   ✅ Registered: {model_id}")
                
            except Exception as e:
                print(f"   ❌ Failed to register {filename}: {str(e)}")
                continue
        
        # Step 4: Set active model
        if registered_count > 0:
            print(f"\n🎯 Step 4: Setting active model...")
            
            # Get the first registered model
            first_model_id = list(model_registry.models.keys())[0]
            
            # Set as active
            model_registry.active_models['BTC'] = first_model_id
            model_registry.models[first_model_id]['is_active'] = True
            
            print(f"   ✅ Set active model: {first_model_id}")
            
            # Step 5: Verify
            print(f"\n✅ Step 5: Verification...")
            models = model_registry.list_models()
            print(f"   Total models: {len(models)}")
            
            active_model = model_registry.get_active_model('BTC')
            print(f"   Active model: {active_model is not None}")
            
            if models:
                print("   Model details:")
                for model in models:
                    model_id = model.get('model_id', list(model_registry.models.keys())[0])
                    is_active = model.get('is_active', False)
                    crypto = model.get('crypto_symbol', 'Unknown')
                    print(f"      • {model_id} ({crypto}) {'[ACTIVE]' if is_active else ''}")
            
            return True
        else:
            print("   ❌ No models registered")
            return False
            
    except Exception as e:
        print(f"❌ Fix failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """تست API endpoints پس از اصلاح"""
    print("\n🌐 Testing API Endpoints")
    print("=" * 30)
    
    import requests
    
    try:
        # Get auth token
        login_data = {
            "username": "testuser2@example.com",
            "password": "TestPassword123!"
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login", 
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            return False
        
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test models list endpoint
        print("📋 Testing /ml/models/list...")
        response = requests.get("http://localhost:8000/api/v1/ml/models/list", headers=headers)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            models_count = len(data.get('models', []))
            active_count = data.get('active_models', 0)
            
            print(f"   ✅ Models returned: {models_count}")
            print(f"   ✅ Active models: {active_count}")
            
            if models_count > 0:
                print("   Model details:")
                for model in data.get('models', []):
                    print(f"      • {model.get('model_id', 'Unknown')}")
                    print(f"        Symbol: {model.get('crypto_symbol', 'Unknown')}")
                    print(f"        Active: {model.get('is_active', False)}")
                
                return True
            else:
                print("   ⚠️ No models returned (but endpoint works)")
                return False
        else:
            print(f"   ❌ Endpoint failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False

def main():
    """اجرای کامل اصلاح و تست"""
    print("🚀 Complete Model Registration Fix & Test")
    print("=" * 50)
    
    # Step 1: Fix and register
    fix_success = fix_and_register_models()
    
    # Step 2: Test API
    if fix_success:
        api_success = test_api_endpoints()
        
        # Final summary
        print(f"\n📊 Final Results:")
        print(f"   Model Registration: {'✅ SUCCESS' if fix_success else '❌ FAILED'}")
        print(f"   API Endpoints: {'✅ SUCCESS' if api_success else '❌ FAILED'}")
        
        if fix_success and api_success:
            print(f"\n🎉 COMPLETE SUCCESS!")
            print(f"   Models are now registered and accessible via API")
            print(f"   You can proceed to next phase")
        else:
            print(f"\n⚠️ PARTIAL SUCCESS - API needs attention")
            
    else:
        print(f"\n❌ Model registration failed - check model files")

if __name__ == "__main__":
    main()