# File: temp/api_migration_test.py
# API migration test - Verify new symbol-based endpoints
# Tests compatibility with frontend dashboard requirements

import requests
import json
from datetime import datetime
from typing import Dict, Any


class APIMigrationTester:
    """Test new symbol-based API endpoints for frontend compatibility"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
        # Authentication setup - using existing test user
        self.jwt_token = None
        self.test_user_email = "testuser2@example.com"
        self.test_user_password = "TestPassword123!"
        
    def setup_authentication(self) -> bool:
        """Setup authentication using existing test user credentials"""
        print("\n🔐 Setting up Authentication...")
        print(f"   👤 Using existing test user: {self.test_user_email}")
        
        # Login to get JWT token (skip registration - user already exists)
        print("   🔑 Logging in to get JWT token...")
        
        # Try form data login first (OAuth2 standard)
        login_data = {
            "username": self.test_user_email,  # OAuth2 uses 'username' field
            "password": self.test_user_password
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                data=login_data,  # Form data
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
                proxies={'http': None, 'https': None}  # FIXED: Add proxy bypass
            )
            
            if response.status_code != 200:
                # Try JSON login endpoint as fallback
                print("   🔄 Trying JSON login endpoint...")
                login_payload = {
                    "email": self.test_user_email,
                    "password": self.test_user_password
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/auth/login-json",
                    json=login_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                    proxies={'http': None, 'https': None}  
                )
            
            if response.status_code != 200:
                print(f"   ❌ Login failed with status {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   📄 Error: {error_data}")
                except:
                    print(f"   📄 Response: {response.text}")
                return False
            
            # Extract JWT token
            login_response = response.json()
            self.jwt_token = login_response.get('access_token')
            
            if not self.jwt_token:
                print("   ❌ No access token in login response")
                print(f"   📄 Response: {login_response}")
                return False
            
            print("   ✅ JWT token obtained successfully")
            print(f"   🎫 Token: {self.jwt_token[:20]}...")
            return True
            
        except Exception as e:
            print(f"   ❌ Login failed: {e}")
            return False
    
    def make_authenticated_request(self, method: str, url: str, **kwargs):
        """Make HTTP request with authentication if token is available"""
        
        # DEBUG: Check URL before processing
        print(f"   🔍 make_authenticated_request called:")
        print(f"   🔍   method: '{method}'")
        print(f"   🔍   url: '{url}'")
        
        if self.jwt_token:
            headers = kwargs.get('headers', {})
            headers['Authorization'] = f"Bearer {self.jwt_token}"
            kwargs['headers'] = headers
            print(f"   🔍   Added auth header")
        
        # FIXED: Remove trust_env (not valid for requests.request)
        # FORCE: Disable proxy for localhost requests
        kwargs['proxies'] = {'http': None, 'https': None}
        
        print(f"   🔍   Final URL being sent to requests: '{url}'")
        
        try:
            return requests.request(method, url, **kwargs)
        except Exception as e:
            print(f"   🔍   requests.request failed with: {e}")
            raise
        
    def test_old_vs_new_endpoints(self):
        """Test old vs new endpoint formats"""
        print("🔄 Testing API Migration...")
        print("=" * 50)
        
        # Test old endpoint (should still work)
        print("📝 Testing Old Endpoint Format:")
        old_result = self.test_old_prediction_endpoint()
        
        # Test new endpoint
        print("\n📝 Testing New Endpoint Format:")
        new_result = self.test_new_prediction_endpoint()
        
        # Test dashboard endpoints
        print("\n📝 Testing Dashboard Endpoints:")
        dashboard_result = self.test_dashboard_endpoints()
        
        # Compare results
        print("\n📊 Migration Comparison:")
        self.compare_endpoints(old_result, new_result)
        
        return {
            "old_endpoint": old_result,
            "new_endpoint": new_result,
            "dashboard_endpoints": dashboard_result
        }
    
    def test_old_prediction_endpoint(self) -> Dict[str, Any]:
        """Test old prediction endpoint format"""
        try:
            url = f"{self.base_url}/api/v1/predictions/predict"
            
            # Old request format
            payload = {
                "crypto_id": 1,
                "prediction_horizon": 24,
                "model_type": "LSTM"
            }
            
            print(f"   🔗 POST {url}")
            print(f"   📦 Payload: {payload}")
            
            response = self.make_authenticated_request("POST", url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {response.status_code}")
                print(f"   📄 Response keys: {list(data.keys())}")
                return {"success": True, "data": data, "status": response.status_code}
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   📄 Error: {response.text}")
                return {"success": False, "error": response.text, "status": response.status_code}
        
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
            return {"success": False, "error": str(e)}
    
    def test_new_prediction_endpoint(self) -> Dict[str, Any]:
        """Test new symbol-based prediction endpoint"""
        try:
            symbol = "BTC"
            url = f"{self.base_url}/api/v1/crypto/{symbol}/predict"
            
            # New request format (frontend compatible)
            payload = {
                "days": 1,
                "model_type": "LSTM"
            }
            
            print(f"   🔗 POST {url}")
            print(f"   📦 Payload: {payload}")
            print("   ⏳ Running AI prediction... (this may take up to 60 seconds)")
            
            response = self.make_authenticated_request("POST", url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {response.status_code}")
                print(f"   📄 Response keys: {list(data.keys())}")
                
                # Check for frontend-required fields
                required_fields = ["symbol", "current_price", "predicted_price", "confidence"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"   ⚠️ Missing frontend fields: {missing_fields}")
                else:
                    print(f"   ✅ All frontend fields present")
                
                return {"success": True, "data": data, "status": response.status_code}
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   📄 Error: {response.text}")
                return {"success": False, "error": response.text, "status": response.status_code}
        
        except requests.exceptions.Timeout:
            print(f"   ⏰ Request timed out (>60s) - AI prediction may be processing")
            return {"success": False, "error": "Timeout - prediction taking too long"}
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
            return {"success": False, "error": str(e)}
    
    def test_dashboard_endpoints(self) -> Dict[str, Any]:
        """Test new dashboard endpoints"""
        results = {}
        
        # Test dashboard summary
        print("   🔍 Testing dashboard summary...")
        print("   ⏳ Loading dashboard data... (this may take up to 30 seconds)")
        try:
            url = f"{self.base_url}/api/v1/dashboard/summary?symbols=BTC,ETH"
            response = self.make_authenticated_request("GET", url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ Dashboard summary: {response.status_code}")
                print(f"      📊 Cryptocurrencies: {len(data.get('cryptocurrencies', []))}")
                results["summary"] = {"success": True, "data": data}
            else:
                print(f"      ❌ Dashboard summary: {response.status_code}")
                results["summary"] = {"success": False, "error": response.text}
        
        except requests.exceptions.Timeout:
            print(f"      ⏰ Dashboard summary timed out (>30s)")
            results["summary"] = {"success": False, "error": "Timeout - dashboard loading too slow"}
        except Exception as e:
            print(f"      ❌ Dashboard summary failed: {e}")
            results["summary"] = {"success": False, "error": str(e)}
        
        # Test quick crypto data
        print("   🔍 Testing quick crypto data...")
        try:
            url = f"{self.base_url}/api/v1/dashboard/quick/BTC"
            response = self.make_authenticated_request("GET", url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ Quick crypto data: {response.status_code}")
                print(f"      📈 BTC price: {data.get('current_price', 'N/A')}")
                results["quick_data"] = {"success": True, "data": data}
            else:
                print(f"      ❌ Quick crypto data: {response.status_code}")
                results["quick_data"] = {"success": False, "error": response.text}
        
        except Exception as e:
            print(f"      ❌ Quick crypto data failed: {e}")
            results["quick_data"] = {"success": False, "error": str(e)}
        
        # Test current prices
        print("   🔍 Testing current prices...")
        try:
            url = f"{self.base_url}/api/v1/dashboard/prices?symbols=BTC,ETH"
            response = self.make_authenticated_request("GET", url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ Current prices: {response.status_code}")
                print(f"      💰 Prices: {data.get('prices', {})}")
                results["prices"] = {"success": True, "data": data}
            else:
                print(f"      ❌ Current prices: {response.status_code}")
                results["prices"] = {"success": False, "error": response.text}
        
        except Exception as e:
            print(f"      ❌ Current prices failed: {e}")
            results["prices"] = {"success": False, "error": str(e)}
        
        return results
    
    def compare_endpoints(self, old_result: Dict, new_result: Dict):
        """Compare old vs new endpoint results"""
        print("   🔍 Endpoint Comparison:")
        
        if old_result.get("success") and new_result.get("success"):
            print("      ✅ Both endpoints working")
            
            old_data = old_result.get("data", {})
            new_data = new_result.get("data", {})
            
            # Compare response structures
            print(f"      📋 Old response fields: {list(old_data.keys())}")
            print(f"      📋 New response fields: {list(new_data.keys())}")
            
            # Check frontend compatibility
            frontend_fields = ["symbol", "current_price", "predicted_price", "confidence"]
            new_has_frontend = all(field in new_data for field in frontend_fields)
            
            if new_has_frontend:
                print("      ✅ New endpoint is frontend compatible")
            else:
                missing = [f for f in frontend_fields if f not in new_data]
                print(f"      ⚠️ New endpoint missing: {missing}")
        
        elif new_result.get("success"):
            print("      ✅ New endpoint working (old may be deprecated)")
        
        elif old_result.get("success"):
            print("      ⚠️ Only old endpoint working")
        
        else:
            print("      ❌ Both endpoints failed")
    
    def test_frontend_integration(self):
        """Test frontend integration scenarios"""
        print("\n🌐 Testing Frontend Integration Scenarios...")
        
        return {
            "crypto_card": self.test_crypto_card_scenario(),
            "price_ticker": self.test_price_ticker_scenario(),
            "prediction_display": self.test_prediction_display_scenario(),
            "dashboard_load": self.test_dashboard_load_scenario()
        }
    
    def test_crypto_card_scenario(self) -> Dict[str, Any]:
        """Test crypto card widget scenario"""
        try:
            # Simulate individual crypto card loading
            url = f"{self.base_url}/api/v1/dashboard/quick/BTC"
            response = self.make_authenticated_request("GET", url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields for crypto card
                required_fields = [
                    "symbol", "current_price", "predicted_price", 
                    "confidence", "price_change_24h_percent"
                ]
                
                has_all_fields = all(field in data for field in required_fields)
                
                return {
                    "success": has_all_fields,
                    "required_fields": required_fields,
                    "available_fields": list(data.keys()),
                    "data": data
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_price_ticker_scenario(self) -> Dict[str, Any]:
        """Test price ticker scenario"""
        try:
            # Simulate price ticker loading
            url = f"{self.base_url}/api/v1/dashboard/prices?symbols=BTC,ETH,ADA,DOT"
            response = self.make_authenticated_request("GET", url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                prices = data.get("prices", {})
                changes = data.get("changes_24h", {})
                
                success = len(prices) > 0 and len(changes) > 0
                
                return {
                    "success": success,
                    "prices": prices,
                    "changes": changes,
                    "data": data
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_prediction_display_scenario(self) -> Dict[str, Any]:
        """Test prediction display scenario"""
        try:
            # Simulate prediction request from frontend
            url = f"{self.base_url}/api/v1/crypto/BTC/predict"
            payload = {"days": 1}
            
            response = self.make_authenticated_request("POST", url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check prediction display requirements
                required_fields = ["current_price", "predicted_price", "confidence"]
                has_all_fields = all(field in data for field in required_fields)
                
                return {
                    "success": has_all_fields,
                    "prediction_data": data,
                    "required_fields": required_fields
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_dashboard_load_scenario(self) -> Dict[str, Any]:
        """Test dashboard load scenario"""
        try:
            # Simulate dashboard initial load
            url = f"{self.base_url}/api/v1/dashboard/summary?symbols=BTC,ETH,ADA"
            response = self.make_authenticated_request("GET", url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check dashboard load requirements
                required_keys = ["cryptocurrencies", "market_summary"]
                has_required = all(key in data for key in required_keys)
                
                return {
                    "success": has_required,
                    "dashboard_data": data,
                    "required_keys": required_keys
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}


def main():
    """Run API migration tests"""
    print("🚀 CryptoPredict API Migration Tests")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = APIMigrationTester()
    
    # Setup authentication first
    if not tester.setup_authentication():
        print("❌ Authentication setup failed. Some tests may fail.")
        print("⚠️ Please ensure the test user exists in the database:")
        print("   Email: testuser2@example.com")
        print("   Password: TestPassword123!")
        print("⚠️ Continuing with tests that don't require authentication...")
    else:
        print("✅ Authentication successful. Running all tests...")
    # Test endpoint migration
    migration_results = tester.test_old_vs_new_endpoints()
    
    # Test frontend integration
    frontend_results = tester.test_frontend_integration()
    
    # Summary
    print("\n🎯 Migration Test Summary:")
    print("=" * 50)
    
    # Count successes
    endpoint_successes = sum(
        1 for result in migration_results.values() 
        if isinstance(result, dict) and result.get("success")
    )
    
    frontend_successes = sum(
        1 for result in frontend_results.values()
        if result.get("success")
    )
    
    print(f"📊 Endpoint Tests: {endpoint_successes}/3 passed")
    print(f"📊 Frontend Tests: {frontend_successes}/4 passed")
    
    total_success_rate = (endpoint_successes + frontend_successes) / 7 * 100
    print(f"📊 Overall Success Rate: {total_success_rate:.1f}%")
    
    if total_success_rate >= 80:
        print("\n✅ API Migration Successful!")
        print("   Frontend dashboard can safely migrate to new endpoints")
    elif total_success_rate >= 60:
        print("\n⚠️ API Migration Partially Successful")
        print("   Some issues need to be resolved")
    else:
        print("\n❌ API Migration Failed")
        print("   Significant issues need to be addressed")
    
    print("\n🔗 New Endpoint URLs:")
    print("   • Prediction: POST /api/crypto/{symbol}/predict")
    print("   • Dashboard: GET /api/dashboard/summary")
    print("   • Quick Data: GET /api/dashboard/quick/{symbol}")
    print("   • Prices: GET /api/dashboard/prices")
    print("   • WebSocket: ws://localhost:8000/api/v1/ws/dashboard")


if __name__ == "__main__":
    main()