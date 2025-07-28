# File: temp/debug_settings.py
# Debug script to check settings configuration

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def check_settings():
    """Check if settings are properly configured"""
    print("🔍 Checking Settings Configuration")
    print("=" * 40)
    
    try:
        from app.core.config import settings
        
        print("✅ Settings imported successfully")
        
        # Check JWT related settings
        print(f"   SECRET_KEY: {settings.SECRET_KEY[:20]}...")
        print(f"   ALGORITHM: {settings.ALGORITHM}")
        
        # Check if JWT_ALGORITHM exists
        if hasattr(settings, 'JWT_ALGORITHM'):
            print(f"   JWT_ALGORITHM: {settings.JWT_ALGORITHM}")
        else:
            print("   ❌ JWT_ALGORITHM: NOT FOUND")
        
        # Check other important settings
        print(f"   DATABASE_URL: {settings.DATABASE_URL}")
        print(f"   ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
        
        return True
        
    except Exception as e:
        print(f"❌ Settings check failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_ml_endpoints_import():
    """Check if ML endpoints can be imported"""
    print("\n🔍 Checking ML Endpoints Import")
    print("=" * 35)
    
    try:
        # Check if ML training endpoints exist
        ml_files = [
            "backend/app/schemas/ml_training.py",
            "backend/app/api/api_v1/endpoints/ml_training.py"
        ]
        
        for file_path in ml_files:
            if os.path.exists(file_path):
                print(f"✅ {file_path} exists")
            else:
                print(f"❌ {file_path} MISSING")
        
        # Try to import ML training endpoints
        try:
            from app.api.api_v1.endpoints import ml_training
            print("✅ ML training endpoints imported successfully")
            
            # Check if router exists
            if hasattr(ml_training, 'router'):
                print("✅ ML training router found")
            else:
                print("❌ ML training router NOT FOUND")
                
        except ImportError as e:
            print(f"❌ ML training endpoints import failed: {str(e)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ML endpoints check failed: {str(e)}")
        return False

def check_current_api_routes():
    """Check current API routes"""
    print("\n🔍 Checking Current API Routes")
    print("=" * 32)
    
    try:
        from app.api.api_v1.api import api_router
        
        print("✅ API router imported successfully")
        
        # Get routes
        routes = []
        for route in api_router.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        print(f"   Total routes: {len(routes)}")
        print("   Routes:")
        for route in sorted(routes)[:10]:  # Show first 10
            print(f"     • {route}")
        
        if len(routes) > 10:
            print(f"     ... and {len(routes) - 10} more")
        
        # Check if ML routes exist
        ml_routes = [r for r in routes if '/ml/' in r]
        if ml_routes:
            print(f"✅ ML routes found: {len(ml_routes)}")
            for route in ml_routes:
                print(f"     • {route}")
        else:
            print("❌ No ML routes found")
        
        return True
        
    except Exception as e:
        print(f"❌ API routes check failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main debugging function"""
    print("🐛 Settings & ML Endpoints Debug Tool")
    print("=" * 45)
    
    # Test 1: Settings
    settings_ok = check_settings()
    
    # Test 2: ML endpoints
    ml_ok = check_ml_endpoints_import()
    
    # Test 3: API routes
    routes_ok = check_current_api_routes()
    
    print("\n📊 Debug Results Summary")
    print("=" * 28)
    print(f"   {'✅' if settings_ok else '❌'} Settings Configuration")
    print(f"   {'✅' if ml_ok else '❌'} ML Endpoints")
    print(f"   {'✅' if routes_ok else '❌'} API Routes")
    
    if settings_ok and ml_ok and routes_ok:
        print("\n🎉 Everything looks good!")
        print("💡 The issue might be elsewhere")
    else:
        print("\n🔧 Issues found:")
        if not settings_ok:
            print("   • Fix settings configuration")
        if not ml_ok:
            print("   • Create ML endpoints files")
        if not routes_ok:
            print("   • Fix API router configuration")

if __name__ == "__main__":
    main()