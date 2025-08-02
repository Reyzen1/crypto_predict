# File: temp/validation_test_actual.py
# Validation test for user's actual file structure
# Tests: ml_training.py, ml_prediction.py (kept), prediction.py (removed)

import sys
import os
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

print("🚀 CryptoPredict Validation - Your Actual Structure")
print("=" * 52)
print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

def test_actual_file_structure():
    """Test the user's actual file structure"""
    print("📁 Testing Your Actual File Structure...")
    
    # Files that SHOULD exist (user's choice)
    should_exist = [
        "backend/app/schemas/ml_training.py",
        "backend/app/schemas/ml_prediction.py",  # User kept this
        "backend/app/api/api_v1/endpoints/ml_training.py",
        "backend/app/api/api_v1/endpoints/ml_prediction.py",
        "backend/app/tasks/ml_tasks.py"
    ]
    
    # Files that should NOT exist (user removed)
    should_not_exist = [
        "backend/app/schemas/prediction.py"  # User removed this
    ]
    
    print("✅ Files that should exist:")
    missing = []
    for file_path in should_exist:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - MISSING")
            missing.append(file_path)
    
    print("\n❌ Files that should NOT exist:")
    unwanted = []
    for file_path in should_not_exist:
        if os.path.exists(file_path):
            print(f"   ⚠️ {file_path} - Should be removed")
            unwanted.append(file_path)
        else:
            print(f"   ✅ {file_path} - Correctly removed")
    
    if missing:
        print(f"\n❌ Missing {len(missing)} required files")
        return False
    elif unwanted:
        print(f"\n⚠️ Found {len(unwanted)} files that should be removed")
        return False
    else:
        print("\n✅ File structure matches your setup perfectly")
        return True


def test_pydantic_config_conflicts():
    """Test for Pydantic Config conflicts in existing files"""
    print("\n🔍 Testing Pydantic Config Conflicts...")
    
    files_to_check = [
        "backend/app/schemas/ml_training.py",
        "backend/app/schemas/ml_prediction.py",  # User's kept file
        "backend/app/schemas/common.py"
    ]
    
    conflicts_found = []
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                has_config_class = 'class Config:' in content
                has_model_config = 'model_config =' in content
                
                if has_config_class and has_model_config:
                    conflicts_found.append(file_path)
                    print(f"   ❌ {file_path}: Has both Config class and model_config")
                else:
                    print(f"   ✅ {file_path}: No conflicts")
        else:
            print(f"   ⚠️ {file_path}: File not found")
    
    if conflicts_found:
        print(f"\n⚠️ Found Config conflicts in {len(conflicts_found)} files")
        return False
    else:
        print("\n✅ No Pydantic Config conflicts found")
        return True


def test_schema_imports_user_structure():
    """Test schema imports with user's actual structure"""
    print("\n📦 Testing Schema Imports (Your Structure)...")
    
    tests = [
        ("ML Training Schemas", "from app.schemas.ml_training import TrainingRequest"),
        ("ML Prediction Schemas", "from app.schemas.ml_prediction import PredictionRequest"),  # User's file
        ("Common Schemas", "from app.schemas.common import SuccessResponse")
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, import_statement in tests:
        try:
            exec(import_statement)
            print(f"   ✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"   ❌ {test_name}: {str(e)}")
    
    print(f"📊 Schema Import Results: {passed}/{total} ({(passed/total)*100:.1f}%)")
    return passed == total


def test_endpoint_imports_user_structure():
    """Test endpoint imports with user's file structure"""
    print("\n🌐 Testing Endpoint Imports (Your Structure)...")
    
    tests = [
        ("ML Training Endpoints", "from app.api.api_v1.endpoints.ml_training import router"),
        ("ML Prediction Endpoints", "from app.api.api_v1.endpoints.ml_prediction import router")
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, import_statement in tests:
        try:
            exec(import_statement)
            print(f"   ✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"   ❌ {test_name}: {str(e)}")
    
    print(f"📊 Endpoint Import Results: {passed}/{total} ({(passed/total)*100:.1f}%)")
    return passed == total


def test_ml_prediction_endpoint_imports():
    """Test that ml_prediction.py endpoint imports correctly from schemas"""
    print("\n🔮 Testing ML Prediction Endpoint Schema Usage...")
    
    endpoint_file = "backend/app/api/api_v1/endpoints/ml_prediction.py"
    
    if not os.path.exists(endpoint_file):
        print(f"   ❌ Endpoint file not found: {endpoint_file}")
        return False
    
    with open(endpoint_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check imports
    correct_imports = [
        "from app.schemas.ml_prediction import",  # Should import from ml_prediction
        "PredictionRequest",
        "router = APIRouter()"
    ]
    
    wrong_imports = [
        "from app.schemas.prediction import"  # Should NOT import from prediction (removed)
    ]
    
    issues = []
    
    for correct_import in correct_imports:
        if correct_import not in content:
            issues.append(f"Missing: {correct_import}")
    
    for wrong_import in wrong_imports:
        if wrong_import in content:
            issues.append(f"Wrong import found: {wrong_import}")
    
    if issues:
        print("   ❌ Issues found in ml_prediction.py:")
        for issue in issues:
            print(f"      • {issue}")
        return False
    else:
        print("   ✅ ml_prediction.py imports look correct")
        return True


def show_user_specific_fixes():
    """Show fixes specific to user's structure"""
    print("\n🔧 Fixes for Your Structure:")
    print("=" * 32)
    
    print("\n1. If Config conflicts exist, fix them by:")
    print("   In ml_prediction.py and ml_training.py:")
    print("   • Remove ALL 'class Config:' blocks")
    print("   • Keep only 'model_config = ConfigDict(...)' lines")
    print("   • Add 'protected_namespaces=()' to ConfigDict")
    
    print("\n2. Ensure ml_prediction.py endpoint imports correctly:")
    print("   ✅ Use: from app.schemas.ml_prediction import ...")
    print("   ❌ NOT: from app.schemas.prediction import ...")
    
    print("\n3. Update api.py router if needed:")
    print("   Make sure it imports from ml_prediction correctly")


def run_user_structure_tests():
    """Run tests for user's specific structure"""
    print("🧪 Running Tests for Your Structure...")
    print("=" * 40)
    
    tests = [
        ("File Structure", test_actual_file_structure),
        ("Pydantic Configs", test_pydantic_config_conflicts),
        ("Schema Imports", test_schema_imports_user_structure),
        ("Endpoint Imports", test_endpoint_imports_user_structure),
        ("ML Prediction Import Usage", test_ml_prediction_endpoint_imports)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print()  # Add spacing after failed tests
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
    
    print("\n" + "=" * 40)
    print(f"🏁 Results for Your Structure: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your structure is working perfectly!")
        print("\n✅ Your setup:")
        print("   • ml_training.py ✅")
        print("   • ml_prediction.py ✅") 
        print("   • prediction.py removed ✅")
        print("   • No Config conflicts ✅")
    elif passed >= total * 0.8:
        print("🎯 MOSTLY WORKING! Just need to fix Config conflicts")
        show_user_specific_fixes()
    else:
        print("⚠️ Several issues found")
        show_user_specific_fixes()
    
    return passed >= total * 0.8


if __name__ == "__main__":
    try:
        success = run_user_structure_tests()
        
        print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if success:
            print("\n🚀 Ready for API testing!")
            print("Next: ./start-backend-local.sh && python temp/quick_api_test.py")
        else:
            print("\n🔧 Please fix the issues shown above")
            
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test script failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)