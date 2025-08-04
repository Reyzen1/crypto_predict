# File: temp/test_imports.py
# Test imports before registering WebSocket endpoints
# Check if all new files can be imported correctly

import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_new_imports():
    """Test all new imports that will be added to api.py"""
    print("🧪 Testing New Imports for API Registration")
    print("=" * 50)
    
    imports_to_test = [
        ("Dashboard Endpoints", "from app.api.api_v1.endpoints import dashboard"),
        ("WebSocket Endpoints", "from app.api.api_v1.endpoints import websocket"),
        ("Dashboard Service", "from app.services.dashboard_service import dashboard_service"),
        ("Prediction Service", "from app.services.prediction_service import prediction_service_new"),
    ]
    
    passed = 0
    total = len(imports_to_test)
    
    for name, import_statement in imports_to_test:
        print(f"📦 Testing {name}...")
        try:
            exec(import_statement)
            print(f"   ✅ {name}: Import successful")
            passed += 1
        except ImportError as e:
            print(f"   ❌ {name}: Import failed - {e}")
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")
    
    print(f"\n📊 Import Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All imports successful!")
        print("✅ Ready to register WebSocket endpoints in api.py")
        return True
    else:
        print("⚠️ Some imports failed - check file locations")
        return False

def test_file_existence():
    """Test if all new files exist in correct locations"""
    print("\n📁 Testing File Existence...")
    
    files_to_check = [
        "backend/app/services/prediction_service.py",
        "backend/app/services/dashboard_service.py", 
        "backend/app/api/api_v1/endpoints/dashboard.py",
        "backend/app/api/api_v1/endpoints/websocket.py"
    ]
    
    existing = 0
    total = len(files_to_check)
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
            existing += 1
        else:
            print(f"   ❌ {file_path} - NOT FOUND")
    
    print(f"\n📊 File Existence: {existing}/{total} files found")
    return existing == total

def test_basic_fastapi_import():
    """Test basic FastAPI imports work"""
    print("\n🔧 Testing Basic FastAPI Imports...")
    
    try:
        from fastapi import APIRouter, WebSocket
        print("   ✅ FastAPI imports working")
        return True
    except ImportError as e:
        print(f"   ❌ FastAPI import failed: {e}")
        return False

def main():
    """Run all import tests"""
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test file existence
    files_ok = test_file_existence()
    
    # Test basic imports
    fastapi_ok = test_basic_fastapi_import()
    
    # Test new imports
    imports_ok = test_new_imports()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print(f"   📁 Files exist: {'✅' if files_ok else '❌'}")
    print(f"   🔧 FastAPI imports: {'✅' if fastapi_ok else '❌'}")
    print(f"   📦 New imports: {'✅' if imports_ok else '❌'}")
    
    if files_ok and fastapi_ok and imports_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Ready to update api.py with new endpoints")
        print("\n📝 Next steps:")
        print("   1. Update backend/app/api/api_v1/api.py with new imports")
        print("   2. Add new router registrations")
        print("   3. Restart backend")
        print("   4. Test WebSocket connections")
        
        return True
    else:
        print("\n❌ Some tests failed")
        print("🔧 Fix the issues above before proceeding")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sys.exit(0 if success else 1)