# File: temp/debug_auth_simple.py  
# Simple auth debugging script

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def check_user_in_database():
    """Check if test user exists and can be authenticated"""
    print("🔍 Checking User in Database")
    print("=" * 30)
    
    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text
        from passlib.context import CryptContext
        
        db = SessionLocal()
        
        # Check if user exists
        result = db.execute(
            text("SELECT id, email, password_hash, is_active FROM users WHERE email = :email"),
            {"email": "testuser2@example.com"}
        )
        user = result.fetchone()
        
        if not user:
            print("❌ User not found in database")
            return False
        
        print(f"✅ User found in database:")
        print(f"   ID: {user[0]}")
        print(f"   Email: {user[1]}")
        print(f"   Active: {user[3]}")
        print(f"   Password Hash: {user[2][:20]}...")
        
        # Test password verification
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password_valid = pwd_context.verify("TestPassword123!", user[2])
        
        if password_valid:
            print("✅ Password verification works")
        else:
            print("❌ Password verification failed")
            return False
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_auth_service_directly():
    """Test auth service components directly"""
    print("\n🔧 Testing Auth Service Components")
    print("=" * 35)
    
    try:
        from app.services.auth import auth_service
        from app.schemas.user import UserLogin
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        
        # Create login data
        login_data = UserLogin(
            email="testuser2@example.com",
            password="TestPassword123!"
        )
        
        print("🔑 Testing auth service authenticate_user...")
        
        # Test authentication directly
        result = auth_service.authenticate_user(db, login_data)
        
        if result:
            print("✅ Auth service works!")
            print(f"   User: {result.get('user', {}).get('email', 'Unknown')}")
            print(f"   Token: {result.get('access_token', 'None')[:20]}...")
        else:
            print("❌ Auth service returned None")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Auth service test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_auth_imports():
    """Test if auth components can be imported"""
    print("\n📦 Testing Auth Imports")
    print("=" * 25)
    
    try:
        from app.api.api_v1.endpoints import auth
        print("✅ Auth endpoints imported")
        
        from app.services.auth import auth_service
        print("✅ Auth service imported")
        
        from app.core.deps import get_current_active_user
        print("✅ Auth dependencies imported")
        
        from app.schemas.user import UserLogin
        print("✅ User schemas imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Auth import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main debugging function"""
    print("🐛 Authentication Debug Tool")
    print("=" * 40)
    
    # Test 1: Imports
    if not test_auth_imports():
        print("\n💡 Fix import issues first")
        return
    
    # Test 2: Database user
    if not check_user_in_database():
        print("\n💡 User or database issue")
        return
    
    # Test 3: Auth service
    if not test_auth_service_directly():
        print("\n💡 Auth service configuration issue")
        return
    
    print("\n🎉 All auth components work!")
    print("💡 The issue might be in the API endpoint itself")
    print("\nSuggestions:")
    print("   • Check backend logs when making login request")
    print("   • Try Swagger UI at http://localhost:8000/docs")
    print("   • Check if there are any middleware issues")

if __name__ == "__main__":
    main()