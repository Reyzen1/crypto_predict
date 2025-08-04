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
            
            response = requests.post(url, json=payload, timeout=10)
            
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
            
            response = requests.post(url, json=payload, timeout=10)
            
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
        
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
            return {"success": False, "error": str(e)}
    
    def test_dashboard_endpoints(self) -> Dict[str, Any]:
        """Test new dashboard endpoints"""
        results = {}
        
        # Test dashboard summary
        print("   🔍 Testing dashboard summary...")
        try:
            url = f"{self.base_url}/api/v1/dashboard/summary?symbols=BTC,ETH"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ Dashboard summary: {response.status_code}")
                print(f"      📊 Cryptocurrencies: {len(data.get('cryptocurrencies', []))}")
                results["summary"] = {"success": True, "data": data}
            else:
                print(f"      ❌ Dashboard summary: {response.status_code}")
                results["summary"] = {"success": False, "error": response.text}
        
        except Exception as e:
            print(f"      ❌ Dashboard summary failed: {e}")
            results["summary"] = {"success": False, "error": str(e)}
        
        # Test quick crypto data
        print("   🔍 Testing quick crypto data...")
        try:
            url = f"{self.base_url}/api/v1/dashboard/quick/BTC"
            response = requests.get(url, timeout=10)
            
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
            response = requests.get(url, timeout=10)
            
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
        
        scenarios = [
            ("Dashboard Load", self.test_dashboard_load_scenario),
            ("Crypto Card Widget", self.test_crypto_card_scenario),
            ("Price Ticker", self.test_price_ticker_scenario),
            ("Prediction Display", self.test_prediction_display_scenario)
        ]
        
        results = {}
        for scenario_name, test_func in scenarios:
            print(f"\n   📱 {scenario_name}:")
            try:
                result = test_func()
                results[scenario_name] = result
                if result.get("success"):
                    print(f"      ✅ {scenario_name} compatible")
                else:
                    print(f"      ❌ {scenario_name} failed")
            except Exception as e:
                print(f"      ❌ {scenario_name} error: {e}")
                results[scenario_name] = {"success": False, "error": str(e)}
        
        return results
    
    def test_dashboard_load_scenario(self) -> Dict[str, Any]:
        """Test dashboard page load scenario"""
        try:
            # Simulate dashboard loading multiple cryptocurrencies
            url = f"{self.base_url}/api/v1/dashboard/summary?symbols=BTC,ETH,ADA"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                cryptos = data.get("cryptocurrencies", [])
                
                # Check if we have data for each requested symbol
                symbols_received = [crypto.get("symbol") for crypto in cryptos]
                expected_symbols = ["BTC", "ETH", "ADA"]
                
                success = all(symbol in symbols_received for symbol in expected_symbols)
                
                return {
                    "success": success,
                    "symbols_requested": expected_symbols,
                    "symbols_received": symbols_received,
                    "data": data
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_crypto_card_scenario(self) -> Dict[str, Any]:
        """Test crypto card widget scenario"""
        try:
            # Simulate individual crypto card loading
            url = f"{self.base_url}/api/v1/dashboard/quick/BTC"
            response = requests.get(url, timeout=10)
            
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
            response = requests.get(url, timeout=10)
            
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
            
            response = requests.post(url, json=payload, timeout=10)
            
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


def main():
    """Run API migration tests"""
    print("🚀 CryptoPredict API Migration Tests")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = APIMigrationTester()
    
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