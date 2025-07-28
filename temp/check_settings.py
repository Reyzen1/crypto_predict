# File: temp/check_settings.py
# بررسی تنظیمات JWT در settings شما

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def check_jwt_settings():
    """بررسی تنظیمات JWT"""
    print("🔍 Checking JWT Settings...")
    print("=" * 40)
    
    try:
        from app.core.config import settings
        
        print("✅ Settings imported successfully")
        
        # Check all possible JWT-related attributes
        jwt_attrs = [
            'SECRET_KEY', 'JWT_SECRET_KEY', 
            'ALGORITHM', 'JWT_ALGORITHM',
            'ACCESS_TOKEN_EXPIRE_MINUTES'
        ]
        
        found_settings = {}
        for attr in jwt_attrs:
            if hasattr(settings, attr):
                value = getattr(settings, attr)
                found_settings[attr] = value
                if 'SECRET' in attr or 'KEY' in attr:
                    print(f"   ✅ {attr}: {str(value)[:20]}...")
                else:
                    print(f"   ✅ {attr}: {value}")
            else:
                print(f"   ❌ {attr}: NOT FOUND")
        
        # Determine which keys to use
        secret_key = found_settings.get('SECRET_KEY') or found_settings.get('JWT_SECRET_KEY')
        algorithm = found_settings.get('ALGORITHM') or found_settings.get('JWT_ALGORITHM')
        
        print(f"\n📋 Recommended settings to use:")
        if secret_key:
            key_name = 'SECRET_KEY' if 'SECRET_KEY' in found_settings else 'JWT_SECRET_KEY'
            print(f"   🔑 Secret Key: settings.{key_name}")
        else:
            print(f"   ❌ No secret key found!")
            
        if algorithm:
            alg_name = 'ALGORITHM' if 'ALGORITHM' in found_settings else 'JWT_ALGORITHM'
            print(f"   🔧 Algorithm: settings.{alg_name}")
        else:
            print(f"   ❌ No algorithm found!")
        
        return secret_key is not None and algorithm is not None
        
    except Exception as e:
        print(f"❌ Settings import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_token_creation():
    """تست ایجاد token"""
    print("\n🔐 Testing Token Creation...")
    print("=" * 40)
    
    try:
        from app.core.security import SecurityManager
        
        security = SecurityManager()
        
        # Test token creation
        test_data = {"user_id": 1, "email": "test@example.com"}
        token = security.create_access_token(test_data)
        
        print(f"✅ Token created successfully")
        print(f"   Token: {token[:50]}...")
        
        # Test token verification
        payload = security.verify_token(token, "access")
        print(f"✅ Token verified successfully")
        print(f"   Payload keys: {list(payload.keys())}")
        
        return token
        
    except Exception as e:
        print(f"❌ Token creation/verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """اجرای تست‌ها"""
    print("🧪 JWT Configuration Check")
    print("=" * 50)
    
    # Check 1: Settings
    settings_ok = check_jwt_settings()
    
    # Check 2: Token creation
    if settings_ok:
        token = test_token_creation()
        if token:
            print("\n✅ JWT configuration appears to be working correctly!")
        else:
            print("\n❌ JWT token creation failed")
    else:
        print("\n❌ JWT settings are incomplete")

if __name__ == "__main__":
    main()