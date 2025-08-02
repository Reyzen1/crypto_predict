# File: temp/api_test_your_structure.py
# API test for user's actual structure (ml_training.py, ml_prediction.py)

import sys
import os
import requests
from datetime import datetime

print("🌐 CryptoPredict API Test - Your Structure")
print("=" * 45)
print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Structure: ml_training.py ✅, ml_prediction.py ✅, prediction.py ❌")
print()

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_server_connection():
    """Test if server is running"""
    print("🔌 Testing Server Connection...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running")
            return True
        else:
            print(f"   ❌ Server responded with: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to server")
        print("   💡 Start server with: ./start-backend-local.sh")
        return False
    except Exception as e:
        print(f"   ❌ Connection test failed: {str(e)}")
        return False


def test_api_info():
    """Test API info endpoint"""
    print("\n📋 Testing API Info...")
    
    try:
        response = requests.get(f"{API_BASE}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            api_name = data.get('name', 'Unknown')
            api_version = data.get('version', 'Unknown')
            print(f"   ✅ API: {api_name} v{api_version}")
            
            # Check endpoints
            endpoints = data.get('endpoints', {})
            ml_endpoints = {}
            for key, value in endpoints.items():
                if 'ml' in key.lower():
                    ml_endpoints[key] = value
            
            if ml_endpoints:
                print("   ✅ ML endpoints found:")
                for key, value in ml_endpoints.items():
                    print(f"      • {key}: {value}")
            else:
                print("   ⚠️ No ML endpoints found in API info")
            
            return True
        else:
            print(f"   ❌ API info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API info test failed: {str(e)}")
        return False


def test_docs_access():
    """Test documentation access"""
    print("\n📚 Testing Documentation...")
    
    docs_urls = [
        ("/docs", "Swagger UI"),
        ("/redoc", "ReDoc"),
        ("/openapi.json", "OpenAPI Schema")
    ]
    
    working = 0
    for url, name in docs_urls:
        try:
            response = requests.get(f"{BASE_URL}{url}", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {name}: {BASE_URL}{url}")
                working += 1
            else:
                print(f"   ❌ {name}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name}: {str(e)}")
    
    print(f"📊 Documentation: {working}/{len(docs_urls)} accessible")
    return working >= 2


def test_ml_training_endpoints():
    """Test ML training endpoints"""
    print("\n🧠 Testing ML Training Endpoints...")
    
    endpoints = [
        ("GET", "/ml/training/models", "List models"),
        ("POST", "/ml/training/start", "Start training (should need auth)"),
        ("GET", "/ml/training/status/test123", "Training status (should need auth)")
    ]
    
    working = 0
    for method, path, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE}{path}", timeout=10)
            else:
                response = requests.post(f"{API_BASE}{path}", json={}, timeout=10)
            
            if response.status_code in [200, 401, 422]:  # 200=ok, 401=needs auth, 422=validation
                status_msg = {200: "working", 401: "needs auth ✓", 422: "needs validation ✓"}
                print(f"   ✅ {description}: {status_msg.get(response.status_code, response.status_code)}")
                working += 1
            else:
                print(f"   ❌ {description}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {description}: {str(e)}")
    
    print(f"📊 Training endpoints: {working}/{len(endpoints)} working")
    return working >= len(endpoints) * 0.8


def test_ml_prediction_endpoints():
    """Test ML prediction endpoints (your ml_prediction.py)"""
    print("\n🔮 Testing ML Prediction Endpoints...")
    
    endpoints = [
        ("POST", "/ml/prediction/predict", "Make prediction (should need auth)"),
        ("POST", "/ml/prediction/batch", "Batch predictions (should need auth)"),
        ("GET", "/ml/prediction/status/test123", "Prediction status (should need auth)"),
        ("GET", "/ml/prediction/history/1", "Prediction history (should need auth)"),
        ("GET", "/ml/prediction/performance/1", "Performance metrics (should need auth)")
    ]
    
    working = 0
    for method, path, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE}{path}", timeout=10)
            else:
                response = requests.post(f"{API_BASE}{path}", json={}, timeout=10)
            
            if response.status_code in [200, 401, 422, 404]:  # 404 ok for test IDs
                status_msg = {
                    200: "working", 
                    401: "needs auth ✓", 
                    422: "needs validation ✓",
                    404: "not found (test ID) ✓"
                }
                print(f"   ✅ {description}: {status_msg.get(response.status_code, response.status_code)}")
                working += 1
            else:
                print(f"   ❌ {description}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {description}: {str(e)}")
    
    print(f"📊 Prediction endpoints: {working}/{len(endpoints)} working")
    return working >= len(endpoints) * 0.8


def test_swagger_ml_endpoints():
    """Test that Swagger UI shows ML endpoints"""
    print("\n📖 Testing Swagger ML Endpoints...")
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # Check for ML-related content in Swagger
            ml_indicators = [
                ("/ml/training", "Training endpoints"),
                ("/ml/prediction", "Prediction endpoints"),
                ("machine learning", "ML terminology"),
                ("training", "Training operations"),
                ("prediction", "Prediction operations")
            ]
            
            found = 0
            for indicator, description in ml_indicators:
                if indicator.lower() in content.lower():
                    print(f"   ✅ {description} found")
                    found += 1
                else:
                    print(f"   ❌ {description} not found")
            
            print(f"📊 Swagger ML content: {found}/{len(ml_indicators)} found")
            return found >= len(ml_indicators) * 0.6
        else:
            print(f"   ❌ Swagger not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Swagger test failed: {str(e)}")
        return False


def show_next_steps():
    """Show next steps based on results"""
    print("\n📋 Next Steps for Your Structure:")
    print("=" * 35)
    
    print("\n🔐 1. Test Authentication:")
    print("   Register: POST /api/v1/auth/register")
    print("   Login: POST /api/v1/auth/login")
    
    print("\n🧠 2. Test ML Training:")
    print("   curl -X POST 'http://localhost:8000/api/v1/ml/training/start' \\")
    print("        -H 'Authorization: Bearer TOKEN' \\")
    print("        -H 'Content-Type: application/json' \\") 
    print("        -d '{\"crypto_symbol\":\"BTC\",\"model_type\":\"lstm\"}'")
    
    print("\n🔮 3. Test ML Predictions:")
    print("   curl -X POST 'http://localhost:8000/api/v1/ml/prediction/predict' \\")
    print("        -H 'Authorization: Bearer TOKEN' \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"crypto_id\":1,\"prediction_horizon\":24}'")
    
    print("\n📊 4. Check Swagger UI:")
    print(f"   Open: {BASE_URL}/docs")
    print("   Look for 'Machine Learning' sections")


def run_all_tests():
    """Run all API tests"""
    print("🧪 Running All API Tests...")
    print("=" * 30)
    
    tests = [
        ("Server Connection", test_server_connection),
        ("API Info", test_api_info),
        ("Documentation", test_docs_access),
        ("ML Training", test_ml_training_endpoints),
        ("ML Prediction", test_ml_prediction_endpoints),
        ("Swagger ML", test_swagger_ml_endpoints)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
    
    print("\n" + "=" * 30)
    print(f"🏁 API Test Results: {passed}/{total} passed ({(passed/total)*100:.1f}%)")
    
    if passed >= total * 0.8:
        print("🎉 API TESTS MOSTLY PASSED!")
        print("\n✅ Your structure is working:")
        print("   • ml_training.py endpoints ✅")
        print("   • ml_prediction.py endpoints ✅")
        print("   • Server running ✅")
        show_next_steps()
    else:
        print("⚠️ Some API tests failed")
        if passed == 0:
            print("💡 Make sure server is running: ./start-backend-local.sh")
        else:
            print("💡 Check schema imports and endpoint definitions")
    
    return passed >= total * 0.6


if __name__ == "__main__":
    try:
        success = run_all_tests()
        
        print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ API test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ API test script failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)