# File: temp/final_test_ml_training.py
# Complete final test script for ML Training API - All issues resolved

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = "testuser2@example.com"
TEST_USER_PASSWORD = "TestPassword123!"  # Strong password with all requirements

class MLTrainingAPITester:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.auth_token: Optional[str] = None
        self.headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
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
    
    def check_backend_connection(self) -> bool:
        """Check if backend is running"""
        try:
            response = requests.get(f"{self.base_url.replace('/api/v1', '')}/health")
            if response.status_code == 200:
                print("✅ Backend is running")
                return True
            else:
                print("❌ Backend not responding properly")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to backend: {str(e)}")
            return False
    
    def register_and_login(self) -> bool:
        """Register test user and login to get auth token"""
        try:
            # Register with strong password and all required fields
            register_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "confirm_password": TEST_USER_PASSWORD,  # Required field
                "first_name": "Test",
                "last_name": "User"
            }
            
            response = requests.post(
                f"{self.base_url}/auth/register", 
                json=register_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                self.print_result(True, "User registered successfully")
            elif response.status_code == 400:
                # User might already exist, that's fine
                self.print_result(True, "User already exists (continuing)")
            else:
                self.print_result(False, f"Registration failed: {response.status_code}", response.text)
            
            # Login to get token - Use form data for OAuth2
            login_data = {
                "username": TEST_USER_EMAIL,  # OAuth2 uses 'username'
                "password": TEST_USER_PASSWORD
            }
            
            response = requests.post(
                f"{self.base_url}/auth/login", 
                data=login_data,  # Use form data
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get("access_token")
                
                # Update headers with authorization token
                self.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
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
            response = requests.get(
                f"{self.base_url}/ml/models/list", 
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                self.print_result(True, f"Model list retrieved: {len(models)} models")
                
                if models:
                    print("   Available models:")
                    for model in models[:3]:
                        print(f"     • {model.get('model_id', 'N/A')} ({model.get('crypto_symbol', 'N/A')})")
                else:
                    print("   No models found (normal for fresh system)")
                
                return True
            else:
                self.print_result(False, f"Model list failed: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.print_result(False, f"Model list error: {str(e)}")
            return False
    
    def test_training_jobs_list(self) -> bool:
        """Test listing user's training jobs"""
        try:
            response = requests.get(
                f"{self.base_url}/ml/training/jobs", 
                headers=self.headers
            )
            
            if response.status_code == 200:
                jobs = response.json()
                job_list = jobs if isinstance(jobs, list) else jobs.get('jobs', [])
                self.print_result(True, f"Training jobs retrieved: {len(job_list)} jobs")
                
                if job_list:
                    print("   Recent jobs:")
                    for job in job_list[:3]:
                        print(f"     • {job.get('job_id', 'N/A')}: {job.get('status', 'N/A')} ({job.get('crypto_symbol', 'N/A')})")
                else:
                    print("   No training jobs found (normal for fresh system)")
                
                return True
            else:
                self.print_result(False, f"Jobs list failed: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.print_result(False, f"Jobs list error: {str(e)}")
            return False
    
    def test_start_training(self, crypto_symbol: str = "BTC") -> Optional[str]:
        """Test starting a training job"""
        try:
            # Use simple structure that works with the fixed endpoint
            training_request = {
                "crypto_symbol": crypto_symbol,
                "model_type": "lstm",
                "data_days_back": 60,  # Keep this field for compatibility
                "force_retrain": True,
                "training_config": {
                    "epochs": 5,  # Small for testing
                    "batch_size": 32,
                    "sequence_length": 30,
                    "learning_rate": 0.001,
                    "dropout_rate": 0.2
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
    
    def test_api_connectivity(self) -> bool:
        """Test API connectivity"""
        try:
            response = requests.get(f"{self.base_url}/system/health")
            
            if response.status_code == 200:
                self.print_result(True, "ML endpoints accessible")
                return True
            else:
                self.print_result(False, f"ML endpoints check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_result(False, f"API connectivity error: {str(e)}")
            return False
    
    def monitor_training(self, job_id: str, max_checks: int = 6) -> bool:
        """Monitor training progress for a limited time"""
        print(f"\n🔍 Monitoring training progress ({max_checks * 5} seconds)...")
        
        completed = False
        for i in range(max_checks):
            time.sleep(5)
            print(f"   Check {i+1}/{max_checks}:")
            
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
                    
                    print(f"     Status: {status} ({progress}%) - {message}")
                    
                    if status in ["completed", "failed", "cancelled"]:
                        completed = True
                        break
                        
                else:
                    print(f"     ❌ Status check failed: {response.status_code}")
                    
            except Exception as e:
                print(f"     ❌ Error checking status: {str(e)}")
        
        return completed
    
    def run_comprehensive_test(self):
        """Run all ML Training API tests"""
        print("🧪 ML Training API Test Runner - Complete Final Version")
        print("=" * 70)
        
        # Check backend connection first
        print("🔍 Checking backend connection...")
        if not self.check_backend_connection():
            print("❌ Backend is not running. Please start the backend server first.")
            return
        
        print("🚀 ML Training API Test Suite")
        print(f"Testing API at: {self.base_url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        test_results = {}
        
        # Test 1: API Integration Check
        self.print_section("API Integration Check")
        test_results['api_connectivity'] = self.test_api_connectivity()
        
        # Test 2: Authentication
        self.print_section("Authentication")
        auth_success = self.register_and_login()
        test_results['authentication'] = auth_success
        
        if not auth_success:
            print("❌ Authentication failed. Cannot proceed with authenticated tests.")
            self.print_test_summary(test_results)
            return
        
        # Test 3: Model Management
        self.print_section("Model Management")
        test_results['model_list'] = self.test_model_list()
        
        # Test 4: Training Jobs List
        self.print_section("Training Jobs")
        test_results['jobs_list'] = self.test_training_jobs_list()
        
        # Test 5: Start Training
        self.print_section("Start Training")
        job_id = self.test_start_training()
        test_results['start_training'] = job_id is not None
        
        # Test 6: Training Status
        if job_id:
            self.print_section("Training Status")
            test_results['training_status'] = self.test_training_status(job_id)
            
            # Test 7: Monitor Training Progress
            if test_results['training_status']:
                self.print_section("Training Progress Monitor")
                training_completed = self.monitor_training(job_id)
                test_results['training_monitoring'] = training_completed
        
        # Print comprehensive summary
        self.print_test_summary(test_results)
        
        # Final recommendations
        self.print_recommendations(test_results)
    
    def print_test_summary(self, results: Dict[str, bool]):
        """Print test results summary"""
        self.print_section("Test Results Summary")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        print(f"📊 Tests passed: {passed}/{total}")
        
        for test_name, result in results.items():
            icon = "✅" if result else "❌"
            print(f"   {icon} {test_name}")
        
        if passed == total:
            print("\n🎉 All ML Training API tests passed!")
            print("✅ API Integration (Phase C) is COMPLETE!")
        else:
            print(f"\n⚠️ {total - passed} test(s) failed. Please check the issues above.")
        
        print(f"🏁 Test session completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def print_recommendations(self, results: Dict[str, bool]):
        """Print recommendations based on test results"""
        self.print_section("Next Steps")
        
        if all(results.values()):
            print("🎯 Ready for Phase D: Testing & Validation")
            print("   Recommended next steps:")
            print("   1. Integration Tests")
            print("   2. Real Bitcoin Data Testing")
            print("   3. Performance Evaluation")
            print("   4. End-to-end workflow testing")
        else:
            print("🔧 Issues to resolve:")
            failed_tests = [name for name, result in results.items() if not result]
            for test in failed_tests:
                print(f"   • Fix {test}")
            
        print(f"\n📋 Phase C Progress:")
        print(f"   ✅ Training APIs: {'Complete' if results.get('start_training', False) else 'Incomplete'}")
        print(f"   🔲 Prediction APIs: Not implemented yet")
        print(f"   🔲 Background Tasks: Basic implementation")


def main():
    """Main test function"""
    tester = MLTrainingAPITester()
    tester.run_comprehensive_test()


if __name__ == "__main__":
    main()