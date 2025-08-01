# File: temp/quick_auth_test.py
# تست سریع auth register

import requests
import json

def test_auth_register():
    """Test auth register endpoint"""
    
    print("🧪 Testing Auth Register")
    print("=" * 25)
    
    # Test data
    register_data = {
        "email": "testuser@example.com",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!",  
        "first_name": "Test",
        "last_name": "User"
    }
    
    url = "http://127.0.0.1:8000/api/v1/auth/register"
    
    try:
        print(f"📡 POST {url}")
        print(f"📋 Data: {json.dumps(register_data, indent=2)}")
        
        response = requests.post(
            url,
            json=register_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📈 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"📋 Response Body:")
            print(json.dumps(response_data, indent=2, default=str))
        except:
            print(f"📋 Response Text: {response.text}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            return True
        else:
            print(f"❌ Registration failed with status {response.status_code}; {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running?")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_health_endpoint():
    """Test if server is running"""
    
    print("\n💓 Testing Health Endpoint")
    print("=" * 27)
    
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        print(f"📈 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print("❌ Server health check failed")
            return False
            
    except:
        print("❌ Server not accessible")
        return False

def main():
    """Main test function"""
    
    print("🚀 Quick Auth Test")
    print("=" * 20)
    
    # Check if server is running
    if not test_health_endpoint():
        print("\n💡 Start the server first:")
        print("   cd backend && python main.py")
        return False
    
    # Test registration
    success = test_auth_register()
    
    if success:
        print("\n🎉 Auth register works!")
    else:
        print("\n🔧 Check server logs for detailed error information")
    
    return success

if __name__ == "__main__":
    main()