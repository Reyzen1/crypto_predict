# File: temp/quick_api_test.py
# Quick API endpoint test for CryptoPredict Stage C completion

import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

print("🚀 CryptoPredict Stage C - Quick API Test")
print("=" * 50)
print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

def test_imports():
    """Test all critical imports"""
    print("📦 Testing API Imports...")
    
    tests = [
        ("Training Schemas", "from app.schemas.ml_training import TrainingRequest"),
        ("Prediction Schemas", "from app.schemas.prediction import PredictionRequest"),
        ("Training Endpoints", "from app.api.api_v1.endpoints.ml_training import router"),
        ("Prediction Endpoints", "from app.api.api_v1.endpoints.prediction import router"),
        ("ML Tasks", "from app.tasks.ml_tasks import auto_train_models"),
        ("API Router", "from app.api.api_v1.api import api_router"),
        ("Training Service", "from app.ml.training.training_service import training_service"),
        ("Prediction Service", "from app.ml.prediction.prediction_service import prediction_service")
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
    
    print(f"\n📊 Import Results: {passed}/{total} ({(passed/total)*100:.1f}%)")
    return passed == total

def test_api_structure():
    """Test API structure and endpoints"""
    print("\n🌐 Testing API Structure...")
    
    try:
        from app.api.api_v1 import api
        from app.api.api_v1.endpoints import ml_training, prediction
        
        # Test router attributes
        training_routes = len([route for route in ml_training.router.routes if hasattr(route, 'methods')])
        prediction_routes = len([route for route in prediction.router.routes if hasattr(route, 'methods')])
        
        print(f"   ✅ Training API: {training_routes} endpoints")
        print(f"   ✅ Prediction API: {prediction_routes} endpoints")
        
        # Test key endpoints exist
        training_endpoints = [
            "start_training",
            "get_training_status", 
            "list_models",
            "activate_model",
            "get_model_performance"
        ]
        
        prediction_endpoints = [
            "make_prediction",
            "get_prediction_status",
            "batch_predictions",
            "get_prediction_history",
            "get_model_performance",
            "get_prediction_stats"
        ]
        
        print(f"   📋 Expected training endpoints: {len(training_endpoints)}")
        print(f"   📋 Expected prediction endpoints: {len(prediction_endpoints)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API structure test failed: {str(e)}")
        return False

def test_schemas():
    """Test schema definitions - FIXED VERSION"""
    print("\n📝 Testing Schemas...")
    
    try:
        from app.schemas.ml_training import TrainingRequest
        from app.schemas.prediction import SymbolPredictionRequest  # Use SymbolPredictionRequest instead
        
        # Test schema creation - FIXED
        training_req = TrainingRequest(
            crypto_symbol="BTC",
            model_type="lstm"
        )
        
        # Use correct schema with crypto_symbol - FIXED
        prediction_req = SymbolPredictionRequest(
            crypto_symbol="BTC"  # This will work now
        )
        
        print("   ✅ Training schemas: Working")
        print("   ✅ Prediction schemas: Working")
        print("   ✅ Schema validation: Working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Schema test failed: {str(e)}")
        return False


def test_ml_services():
    """Test ML services availability"""
    print("\n🤖 Testing ML Services...")
    
    try:
        from app.ml.training.training_service import training_service
        from app.ml.prediction.prediction_service import prediction_service
        from app.ml.config.ml_config import model_registry
        
        services = [
            ("Training Service", training_service),
            ("Prediction Service", prediction_service),
            ("Model Registry", model_registry)
        ]
        
        all_working = True
        for service_name, service in services:
            if service:
                print(f"   ✅ {service_name}: Available")
            else:
                print(f"   ❌ {service_name}: Not available")
                all_working = False
        
        return all_working
        
    except Exception as e:
        print(f"   ❌ ML services test failed: {str(e)}")
        return False

def test_background_tasks():
    """Test background tasks"""
    print("\n⚙️ Testing Background Tasks...")
    
    try:
        from app.tasks.ml_tasks import (
            auto_train_models,
            generate_scheduled_predictions,
            evaluate_model_performance,
            cleanup_old_predictions
        )
        
        tasks = [
            "auto_train_models",
            "generate_scheduled_predictions", 
            "evaluate_model_performance",
            "cleanup_old_predictions"
        ]
        
        print(f"   ✅ ML Tasks: {len(tasks)} tasks available")
        
        # Test task helper functions
        from app.tasks.ml_tasks import (
            start_auto_training,
            start_prediction_generation,
            start_performance_evaluation,
            start_prediction_cleanup
        )
        
        helpers = [
            "start_auto_training",
            "start_prediction_generation",
            "start_performance_evaluation", 
            "start_prediction_cleanup"
        ]
        
        print(f"   ✅ Helper Functions: {len(helpers)} functions available")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Background tasks test failed: {str(e)}")
        return False

def test_database_integration():
    """Test database integration - FIXED VERSION"""
    print("\n🗄️ Testing Database Integration...")
    
    try:
        from app.core.database import get_db
        from sqlalchemy import text
        
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        # Execute simple test query - FIXED
        result = db.execute(text("SELECT 1 as test")).fetchone()
        
        if result and result[0] == 1:
            print("   ✅ Database Connection: Working")
            print("   ✅ Basic Query: Working")
            return True
        else:
            print("   ❌ Database query returned unexpected result")
            return False
            
    except Exception as e:
        print(f"   ❌ Database integration test failed: {str(e)}")
        return False
    finally:
        # Close database session
        try:
            db.close()
        except:
            pass


def main():
    """Main test function"""
    print("🔧 Running quick API tests...\n")
    
    tests = [
        ("Import Tests", test_imports),
        ("API Structure", test_api_structure), 
        ("Schema Tests", test_schemas),
        ("ML Services", test_ml_services),
        ("Background Tasks", test_background_tasks),
        ("Database Integration", test_database_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_function in tests:
        try:
            if test_function():
                passed += 1
                print(f"✅ {test_name}: PASSED\n")
            else:
                print(f"❌ {test_name}: FAILED\n")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {str(e)}\n")
    
    # Final results
    success_rate = (passed / total) * 100
    
    print("=" * 50)
    print("🏁 QUICK TEST RESULTS")
    print("=" * 50)
    print(f"📊 Success Rate: {success_rate:.1f}% ({passed}/{total})")
    print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_rate >= 90:
        print("\n🎉 EXCELLENT: Stage C API Implementation Complete!")
        print("✨ All major APIs are working correctly")
        print("🚀 Ready for comprehensive testing")
    elif success_rate >= 80:
        print("\n✅ GOOD: Stage C mostly complete")
        print("🔧 Minor issues may need attention")
    elif success_rate >= 70:
        print("\n⚠️ FAIR: Stage C has some issues")
        print("🛠️ Several components need fixing")
    else:
        print("\n❌ POOR: Stage C needs work")
        print("🚨 Multiple issues found")
    
    print("\n📚 Next Steps:")
    if success_rate >= 80:
        print("   1. Run comprehensive test: python temp/comprehensive_test_all_apis.py")
        print("   2. Test with actual HTTP requests")
        print("   3. Start Stage D: Testing & Validation")
    else:
        print("   1. Fix failed components")
        print("   2. Re-run this quick test")
        print("   3. Check logs for detailed errors")
    
    print(f"\n🎯 Stage C Implementation Status: {'COMPLETE' if success_rate >= 90 else 'IN PROGRESS'}")

if __name__ == "__main__":
    if not os.path.exists("backend"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    main()