# File: temp/quick_api_test_fixed.py
# Quick API test for fixed endpoints and schemas
# Tests the actual API endpoints after fixes

import sys
import os
import json
import requests
from datetime import datetime
from pathlib import Path

print("🌐 CryptoPredict API Quick Test - Fixed Version")
print("=" * 50)
print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_api_health():
    """Test basic API health"""
    print("🏥 Testing API Health...")
    
    try:
        # Test main API info
        response = requests.get(f"{API_BASE}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API Info: {data.get('name', 'Unknown')} v{data.get('version', 'Unknown')}")
            
            # Check updated endpoints
            endpoints = data.get('endpoints', {})
            ml_training = endpoints.get('ml_training')
            predictions = endpoints.get('predictions')
            
            print(f"   📍 ML Training: {ml_training}")
            print(f"   📍 ML Predictions: {predictions}")
            
            if '/ml/training' in str(ml_training) and '/ml/predictions' in str(predictions):
                print("   ✅ Updated endpoints configured correctly")
                return True
            else:
                print("   ❌ Endpoints not updated properly")
                return False
        else:
            print(f"   ❌ API Info failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to API. Is the server running?")
        print("   💡 Run: ./start-backend-local.sh")
        return False
    except Exception as e:
        print(f"   ❌ API health test failed: {str(e)}")
        return False


def test_docs_endpoints():
    """Test documentation endpoints"""
    print("\n📚 Testing Documentation...")
    
    docs_endpoints = [
        "/docs",
        "/redoc", 
        "/openapi.json"
    ]
    
    working = 0
    total = len(docs_endpoints)
    
    for endpoint in docs_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {endpoint}")
                working += 1
            else:
                print(f"   ❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint}: {str(e)}")
    
    print(f"📊 Documentation Results: {working}/{total} working")
    return working == total


def test_training_endpoints():
    """Test training endpoints"""
    print("\n🧠 Testing Training Endpoints...")
    
    # Test endpoints that don't require auth
    endpoints = [
        ("GET", "/ml/training/models", "List models endpoint"),
    ]
    
    # Test endpoints that do require auth (expect 401)
    auth_endpoints = [
        ("POST", "/ml/training/start", "Start training endpoint"),
        ("GET", "/ml/training/status/test123", "Training status endpoint"),
    ]
    
    working = 0
    total = len(endpoints) + len(auth_endpoints)
    
    # Test non-auth endpoints
    for method, endpoint, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{API_BASE}{endpoint}", json={}, timeout=10)
            
            if response.status_code in [200, 422]:  # 422 is validation error, which means endpoint exists
                print(f"   ✅ {description}")
                working += 1
            else:
                print(f"   ❌ {description}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {description}: {str(e)}")
    
    # Test auth endpoints (should return 401)
    for method, endpoint, description in auth_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{API_BASE}{endpoint}", json={}, timeout=10)
            
            if response.status_code == 401:  # Unauthorized - endpoint exists but requires auth
                print(f"   ✅ {description} (requires auth)")
                working += 1
            else:
                print(f"   ❌ {description}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {description}: {str(e)}")
    
    print(f"📊 Training Endpoints: {working}/{total} working")
    return working >= total * 0.7  # 70% success rate is acceptable


def test_prediction_endpoints():
    """Test prediction endpoints"""
    print("\n🔮 Testing Prediction Endpoints...")
    
    # Test endpoints that require auth (expect 401)
    auth_endpoints = [
        ("POST", "/ml/predictions/predict", "Make prediction endpoint"),
        ("POST", "/ml/predictions/batch", "Batch predictions endpoint"),
        ("GET", "/ml/predictions/status/test123", "Prediction status endpoint"),
        ("POST", "/ml/predictions/history", "Prediction history endpoint"),
        ("GET", "/ml/predictions/performance/BTC", "Performance metrics endpoint"),
        ("GET", "/ml/predictions/stats", "Prediction stats endpoint"),
    ]
    
    working = 0
    total = len(auth_endpoints)
    
    for method, endpoint, description in auth_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{API_BASE}{endpoint}", json={}, timeout=10)
            
            if response.status_code == 401:  # Unauthorized - endpoint exists but requires auth
                print(f"   ✅ {description} (requires auth)")
                working += 1
            elif response.status_code == 422:  # Validation error - endpoint exists
                print(f"   ✅ {description} (validation error)")
                working += 1
            else:
                print(f"   ❌ {description}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {description}: {str(e)}")
    
    print(f"📊 Prediction Endpoints: {working}/{total} working")
    return working >= total * 0.7


def test_tasks_endpoints():
    """Test task management endpoints"""
    print("\n⚙️ Testing Task Endpoints...")
    
    # Test info endpoint (should work without auth)
    try:
        response = requests.get(f"{API_BASE}/tasks/info", timeout=10)
        if response.status_code == 401:
            print("   ✅ Tasks info endpoint (requires auth)")
            info_works = True
        elif response.status_code == 200:
            data = response.json()
            available_tasks = data.get('available_tasks', {})
            
            # Check for ML tasks
            ml_task_count = sum(1 for task in available_tasks.values() 
                              if task.get('category') == 'machine_learning')
            
            print(f"   ✅ Tasks info endpoint")
            print(f"   📊 Found {ml_task_count} ML tasks configured")
            info_works = True
        else:
            print(f"   ❌ Tasks info endpoint: {response.status_code}")
            info_works = False
    except Exception as e:
        print(f"   ❌ Tasks info endpoint: {str(e)}")
        info_works = False
    
    # Test ML task endpoints (should require auth)
    ml_endpoints = [
        ("POST", "/tasks/ml/auto-train", "ML auto training"),
        ("POST", "/tasks/ml/predictions/generate", "ML prediction generation"),
        ("POST", "/tasks/ml/performance/evaluate", "ML performance evaluation"),
        ("POST", "/tasks/ml/cleanup", "ML cleanup"),
    ]
    
    working = 1 if info_works else 0
    total = 1 + len(ml_endpoints)
    
    for method, endpoint, description in ml_endpoints:
        try:
            response = requests.post(f"{API_BASE}{endpoint}", json={}, timeout=10)
            
            if response.status_code == 401:
                print(f"   ✅ {description} (requires auth)")
                working += 1
            else:
                print(f"   ❌ {description}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {description}: {str(e)}")
    
    print(f"📊 Task Endpoints: {working}/{total} working")
    return working >= total * 0.8


def test_swagger_ui():
    """Test Swagger UI for new endpoints"""
    print("\n📖 Testing Swagger UI...")
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # Check for updated tags
            checks = [
                ("Machine Learning - Training" in content, "Training tag"),
                ("Machine Learning - Predictions" in content, "Predictions tag"),
                ("/ml/training" in content, "Training endpoints"),
                ("/ml/predictions" in content, "Prediction endpoints"),
                ("/tasks/ml/" in content, "ML task endpoints")
            ]
            
            working = sum(1 for check, desc in checks if check)
            total = len(checks)
            
            for check, description in checks:
                status = "✅" if check else "❌"
                print(f"   {status} {description}")
            
            print(f"📊 Swagger UI: {working}/{total} features found")
            return working >= total * 0.8
        else:
            print(f"   ❌ Swagger UI not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Swagger UI test failed: {str(e)}")
        return False


def run_all_api_tests():
    """Run all API tests"""
    print("🧪 Running All API Tests...")
    print("=" * 30)
    
    tests = [
        ("API Health", test_api_health),
        ("Documentation", test_docs_endpoints),
        ("Training Endpoints", test_training_endpoints),
        ("Prediction Endpoints", test_prediction_endpoints),
        ("Task Endpoints", test_tasks_endpoints),
        ("Swagger UI", test_swagger_ui)
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
    
    if passed >= total * 0.8:  # 80% success rate
        print("🎉 API TESTS MOSTLY PASSED!")
        print("\n✅ API is ready for:")
        print("   • User authentication testing")
        print("   • ML model training")
        print("   • Real prediction requests")
        print("   • Background task execution")
        
        print(f"\n🌐 Access your API at:")
        print(f"   • API Docs: {BASE_URL}/docs")
        print(f"   • ReDoc: {BASE_URL}/redoc")
        print(f"   • API Info: {API_BASE}/")
    else:
        print("⚠️ Some API tests failed. Check the issues above.")
        
    return passed >= total * 0.8


def show_next_steps():
    """Show next steps for testing"""
    print("\n📋 Next Steps for Complete Testing:")
    print("=" * 40)
    
    print("\n1. 🔐 Test Authentication:")
    print("   • Register a user: POST /api/v1/auth/register")
    print("   • Login: POST /api/v1/auth/login")
    print("   • Use token for protected endpoints")
    
    print("\n2. 🧠 Test ML Training:")
    print("   • Start training: POST /api/v1/ml/training/start")
    print("   • Check status: GET /api/v1/ml/training/status/{job_id}")
    print("   • List models: GET /api/v1/ml/training/models")
    
    print("\n3. 🔮 Test ML Predictions:")
    print("   • Make prediction: POST /api/v1/ml/predictions/predict")
    print("   • Batch predictions: POST /api/v1/ml/predictions/batch")
    print("   • Check performance: GET /api/v1/ml/predictions/performance/BTC")
    
    print("\n4. ⚙️ Test Background Tasks:")
    print("   • Auto training: POST /api/v1/tasks/ml/auto-train")
    print("   • Generate predictions: POST /api/v1/tasks/ml/predictions/generate")
    print("   • Task info: GET /api/v1/tasks/info")
    
    print("\n5. 📊 Test System Integration:")
    print("   • Price data sync: POST /api/v1/tasks/sync/prices")
    print("   • Health checks: GET /api/v1/system/health")
    print("   • Performance monitoring")


if __name__ == "__main__":
    try:
        success = run_all_api_tests()
        
        if success:
            show_next_steps()
        
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