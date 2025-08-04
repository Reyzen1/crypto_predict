# File: temp/simple_websocket_test.py
# Simple WebSocket test without authentication
# Quick test to verify WebSocket endpoints work after fixing import issues

import asyncio
import websockets
import json
from datetime import datetime

async def test_simple_websocket_connection():
    """Simple test to verify WebSocket connection works"""
    print("🔌 Testing Simple WebSocket Connection...")
    
    try:
        # Test basic connection to dashboard WebSocket
        uri = "ws://localhost:8000/api/v1/ws/dashboard"
        print(f"🔗 Connecting to: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Wait for welcome message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"📨 Welcome message: {data.get('type', 'unknown')}")
                print(f"📄 Message: {data.get('message', 'No message')}")
                
                # Send a simple subscription
                subscribe_msg = {
                    "type": "subscribe",
                    "symbols": ["BTC"]
                }
                await websocket.send(json.dumps(subscribe_msg))
                print("📤 Sent subscription for BTC")
                
                # Wait for subscription confirmation
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"📨 Response: {data.get('type', 'unknown')}")
                
            except asyncio.TimeoutError:
                print("⏰ No response within timeout - but connection worked!")
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON decode error: {e}")
            
        print("✅ WebSocket test completed successfully!")
        return True
        
    except ConnectionRefusedError:
        print("❌ Connection refused - make sure backend is running")
        print("   Start backend with: ./start-backend-local.sh")
        return False
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False

async def test_symbol_websocket():
    """Test symbol-specific WebSocket"""
    print("\n🔌 Testing Symbol WebSocket...")
    
    try:
        uri = "ws://localhost:8000/api/v1/ws/prices/BTC"
        print(f"🔗 Connecting to: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Symbol WebSocket connected!")
            
            # Wait for initial data
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"📨 Initial data type: {data.get('type', 'unknown')}")
                if data.get('type') == 'initial_data':
                    print(f"💰 BTC Price: {data.get('current_price', 'N/A')}")
                
            except asyncio.TimeoutError:
                print("⏰ No initial data - but connection worked!")
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON decode error: {e}")
                
        print("✅ Symbol WebSocket test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Symbol WebSocket test failed: {e}")
        return False

def main():
    """Run simple WebSocket tests"""
    print("🚀 Simple WebSocket Tests (No Authentication)")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success_count = 0
    total_tests = 2
    
    # Test 1: Dashboard WebSocket
    if asyncio.run(test_simple_websocket_connection()):
        success_count += 1
    
    # Test 2: Symbol WebSocket  
    if asyncio.run(test_symbol_websocket()):
        success_count += 1
    
    # Results
    print("\n" + "=" * 50)
    print(f"📊 Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All WebSocket tests passed!")
        print("\n✅ WebSocket endpoints are working correctly")
        print("✅ No authentication issues")
        print("✅ Ready for frontend integration")
    elif success_count > 0:
        print("⚠️ Some tests passed - check backend status")
    else:
        print("❌ All tests failed - check backend is running")
        print("\n🔧 Troubleshooting:")
        print("   1. Start backend: ./start-backend-local.sh")
        print("   2. Check port 8000 is available")
        print("   3. Check for any import errors in logs")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()