# File: temp/check_registered_endpoints.py
# Check which endpoints are actually registered in FastAPI app
# This will help debug 404 errors

import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def check_registered_routes():
    """Check which routes are registered in the FastAPI app"""
    print("🔍 Checking Registered API Routes")
    print("=" * 40)
    
    try:
        from app.main import app
        
        routes = []
        websocket_routes = []
        
        # Collect all routes
        for route in app.routes:
            if hasattr(route, 'path'):
                if hasattr(route, 'methods'):
                    # HTTP route
                    methods = ', '.join(route.methods)
                    routes.append(f"{methods:10} {route.path}")
                else:
                    # WebSocket route
                    websocket_routes.append(f"WEBSOCKET  {route.path}")
        
        # Display HTTP routes
        print("📡 HTTP Routes:")
        if routes:
            for route in sorted(routes):
                print(f"   {route}")
        else:
            print("   ❌ No HTTP routes found!")
        
        # Display WebSocket routes
        print(f"\n🔌 WebSocket Routes:")
        if websocket_routes:
            for route in sorted(websocket_routes):
                print(f"   {route}")
        else:
            print("   ❌ No WebSocket routes found!")
        
        # Check for specific endpoints we're looking for
        print("\n🎯 Checking Target Endpoints:")
        
        target_patterns = [
            "/api/v1/ml/predictions/{symbol}/predict",
            "/api/v1/dashboard/summary", 
            "/api/v1/dashboard/quick/{symbol}",
            "/api/v1/dashboard/prices",
            "/api/v1/ws/dashboard",
            "/api/v1/ws/prices/{symbol}"
        ]
        
        all_paths = [route.path for route in app.routes if hasattr(route, 'path')]
        
        for pattern in target_patterns:
            # Check for exact match or similar patterns
            found = False
            for path in all_paths:
                if pattern.replace('{symbol}', 'BTC') in path or pattern == path:
                    found = True
                    break
                # Also check for pattern-like matches
                if pattern.replace('/{symbol}', '') in path:
                    found = True
                    break
            
            status = "✅" if found else "❌"
            print(f"   {status} {pattern}")
        
        print(f"\n📊 Total Routes: {len(routes) + len(websocket_routes)}")
        print(f"   📡 HTTP: {len(routes)}")
        print(f"   🔌 WebSocket: {len(websocket_routes)}")
        
        return len(routes) > 0
        
    except Exception as e:
        print(f"❌ Failed to check routes: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_router_registration():
    """Check if routers are properly registered"""
    print("\n🔧 Checking Router Registration...")
    
    try:
        from app.api.api_v1.api import api_router
        
        # Get router count
        router_count = len([r for r in api_router.routes])
        print(f"   📊 API Router has {router_count} routes")
        
        # Try to import new routers
        try:
            from app.api.api_v1.endpoints import dashboard, websocket
            print("   ✅ Dashboard & WebSocket routers import successfully")
            
            dashboard_routes = len([r for r in dashboard.router.routes])
            websocket_routes = len([r for r in websocket.router.routes])
            
            print(f"   📊 Dashboard router: {dashboard_routes} routes")
            print(f"   📊 WebSocket router: {websocket_routes} routes")
            
            return True
            
        except ImportError as e:
            print(f"   ❌ Failed to import new routers: {e}")
            return False
        
    except Exception as e:
        print(f"   ❌ Failed to check router registration: {e}")
        return False

def main():
    """Main check function"""
    print("🔍 CryptoPredict Endpoint Registration Check")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check routes
    routes_ok = check_registered_routes()
    
    # Check router registration
    routers_ok = check_router_registration()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Check Results:")
    print(f"   📡 Routes registered: {'✅' if routes_ok else '❌'}")
    print(f"   🔧 Routers imported: {'✅' if routers_ok else '❌'}")
    
    if routes_ok and routers_ok:
        print("\n🎉 Everything looks good!")
        print("✅ Endpoints should be accessible")
        print("\n💡 If still getting 404, check:")
        print("   • Backend server is running")
        print("   • Correct URL paths in tests")
        print("   • Server restart after code changes")
    else:
        print("\n🔧 Issues found:")
        if not routes_ok:
            print("   ❌ Routes not properly registered")
        if not routers_ok:
            print("   ❌ Router imports failing")
        
        print("\n🛠️ Fixes needed:")
        print("   1. Check api.py has new router imports")
        print("   2. Check api.py includes new routers") 
        print("   3. Restart backend server")
        print("   4. Check for import errors in logs")

if __name__ == "__main__":
    main()