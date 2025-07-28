# File: temp/test_ml_training_api.py
# Test script for ML Training API endpoints

import asyncio
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

class MLTrainingAPITester:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.auth_token: Optional[str] = None
        self.headers: Dict[str, str] = {}
        
    def print_section(self, title: str):
        """Print a formatted section header"""
        print(f"\n{'='*50}")
        print(f"🧪 {title}")
        print(f"{'='*50}")
    
    def print_result(self, success: bool, message: str, details: Any = None):
        """Print test result"""
        icon = "✅" if success else "❌"
        print(f"{icon} {message}")
        if details:
            print(f"   Details: {details}")
    
    def register_and_login(self) -> bool:
        """Register test user and login to get auth token"""
        try:
            # Try to register (might fail if user exists)
            register_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "full_name": "Test User"
            }
            
            response = requests.post(f"{self.base_url}/auth/register", json=register_data)
            if response.status_code in [200, 201]:
                self.print_result(True, "User registered successfully")
            elif response.status_code == 400:
                self.print_result(True, "User already exists (continuing with login)")
            else:
                self.print_result(False, f"Registration failed: {response.status_code}")
            
            # Login to get token
            login_data = {
                "username": TEST_USER_EMAIL,  # FastAPI OAuth2 uses 'username'
                "password": TEST_USER_PASSWORD
            }
            
            response = requests.post(f"{self.base_url}/auth/login", data=login_data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.auth_token}"}
                self.print_result(True, "Login successful", f"Token: {self.auth_token[:20]}...")
                return True
            else:
                self.print_result(False, f"Login failed: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.print_result(False, f"Authentication error: {str(e)}")
            return False
    
    def test_model_list(self) -> bool:
        """Test listing available models"""
        try:
            response = requests.get(f"{self.base_url}/ml/models/list", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                self.print_result(True, f"Model list retrieved: {data.get('total', 0)} models")
                
                if data.get('models'):
                    print("   Available models:")
                    for model in data['models'][:3]:  # Show first 3
                        print(f"     • {model.get('model_id', 'N/A')} ({model.get('crypto_symbol', 'N/A')})")
                
                return True
            else:
                self.print_result(False, f"Model list failed: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.print_result(False, f"Model list error: {str(e)}")
            return False
    
    def test_start_training(self, crypto_symbol: str = "BTC") -> Optional[str]:
        """Test starting a training job"""
        try:
            training_request = {
                "crypto_symbol": crypto_symbol,
                "model_type": "lstm",
                "data_days_back": 60,  # Reduced for faster testing
                "force_retrain": True,
                "training_config": {
                    "epochs": 5,  # Very small for testing
                    "batch_size": 32,
                    "sequence_length": 30
                }
            }
            
            response = requests.post(
                f"{self.base_url}/ml/training/start", 
                json=training_request,
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get("job_id")
                self.print_result(True, f"Training started successfully", f"Job ID: {job_id}")
                return job_id
            else:
                self.print_result(False, f"Training start failed: {response.status_code}", response.text)
                return None
                
        except Exception as e:
            self.print_result(False, f"Training start error: {str(e)}")
            return None
    
    def test_training_status(self, job_id: str) -> bool:
        """Test checking training status"""
        try:
            response = requests.get(
                f"{self.base_url}/ml/training/{job_id}/status",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                progress = data.get("progress_percentage", 0)
                message = data.get("message", "")
                
                self.print_result(True, f"Status: {status} ({progress}%)", message)
                return True
            else:
                self.print_result(False, f"Status check failed: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.print_result(False, f"Status check error: {str(e)}")
            return False
    
    def test_training_jobs_list(self) -> bool:
        """Test listing user's training jobs"""
        try:
            response = requests.get(f"{self.base_url}/ml/training/jobs", headers=self.headers)
            
            if response.status_code == 200:
                jobs = response.json()
                self.print_result(True, f"Training jobs retrieved: {len(jobs)} jobs")
                
                if jobs:
                    print("   Recent jobs:")
                    for job in jobs[:3]:  # Show first 3
                        print(f"     • {job.get('job_id', 'N/A')}: {job.get('status', 'N/A')} ({job.get('crypto_symbol', 'N/A')})")
                
                return True
            else:
                self.print_result(False, f"Jobs list failed: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.print_result(False, f"Jobs list error: {str(e)}")
            return False
    
    def test_api_info(self) -> bool:
        """Test API info endpoint to check ML endpoints are registered"""
        try:
            response = requests.get(f"{self.base_url}/info")
            
            if response.status_code == 200:
                data = response.json()
                endpoints = data.get("endpoints", {})
                
                if "ml" in endpoints:
                    self.print_result(True, "ML endpoints registered in API")
                    return True
                else:
                    self.print_result(False, "ML endpoints not found in API info")
                    return False
            else:
                self.print_result(False, f"API info failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_result(False, f"API info error: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run all ML Training API tests"""
        print("🚀 ML Training API Test Suite")
        print(f"Testing API at: {self.base_url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        test_results = {}
        
        # Test 1: API Info
        self.print_section("API Integration Check")
        test_results["api_info"] = self.test_api_info()
        
        # Test 2: Authentication
        self.print_section("Authentication")
        test_results["auth"] = self.register_and_login()
        
        if not test_results["auth"]:
            print("\n❌ Cannot proceed without authentication")
            return test_results
        
        # Test 3: Model List
        self.print_section("Model Management")
        test_results["model_list"] = self.test_model_list()
        
        # Test 4: Training Jobs List
        self.print_section("Training Jobs")
        test_results["jobs_list"] = self.test_training_jobs_list()
        
        # Test 5: Start Training
        self.print_section("Start Training")
        job_id = self.test_start_training("BTC")
        test_results["start_training"] = job_id is not None
        
        # Test 6: Check Training Status
        if job_id:
            self.print_section("Training Status")
            test_results["training_status"] = self.test_training_status(job_id)
            
            # Monitor training for a short time
            print("\n🔍 Monitoring training progress (30 seconds)...")
            for i in range(6):  # Check every 5 seconds for 30 seconds
                time.sleep(5)
                print(f"   Check {i+1}/6:")
                self.test_training_status(job_id)
        
        # Results Summary
        self.print_section("Test Results Summary")
        passed = sum(1 for result in test_results.values() if result)
        total = len(test_results)
        
        print(f"📊 Tests passed: {passed}/{total}")
        
        for test_name, result in test_results.items():
            icon = "✅" if result else "❌"
            print(f"   {icon} {test_name}")
        
        if passed == total:
            print("\n🎉 All ML Training API tests passed!")
            print("✅ Ready for Stage C Part 2: Prediction APIs")
        else:
            print(f"\n⚠️ {total - passed} test(s) failed. Please check the issues above.")
        
        return test_results


def main():
    """Run the ML Training API test suite"""
    print("🧪 ML Training API Test Runner - Fixed Version")
    print("=" * 60)
    
    # Check if backend is running with timeout
    print("🔍 Checking backend connection...")
    try:
        import requests
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)  # 5 second timeout
        if response.status_code != 200:
            print("❌ Backend is not responding properly")
            print(f"   Health check returned: {response.status_code}")
            return
        print("✅ Backend is running")
    except requests.exceptions.Timeout:
        print("❌ Backend connection timeout")
        print(f"   Backend might be slow or not running at {API_BASE_URL}")
        return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend")
        print(f"   Make sure backend is running at {API_BASE_URL}")
        print("   Try: cd backend && python -m uvicorn app.main:app --reload")
        return
    except Exception as e:
        print("❌ Unexpected error connecting to backend")
        print(f"   Error: {str(e)}")
        return
    
    # Run tests
    tester = MLTrainingAPITester()
    results = tester.run_comprehensive_test()
    
    # Final status
    print(f"\n🏁 Test session completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user (Ctrl+C)")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"\n\n💥 Unexpected test error: {str(e)}")
        import traceback
        traceback.print_exc()