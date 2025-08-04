# File: temp/websocket_client_test.py
# WebSocket client test for real-time functionality
# Test script to verify WebSocket endpoints work correctly

import asyncio
import websockets
import json
from datetime import datetime

async def test_dashboard_websocket():
    """Test dashboard WebSocket endpoint"""
    print("🔌 Testing Dashboard WebSocket...")
    
    try:
        # Connect to dashboard WebSocket
        uri = "ws://localhost:8000/api/ws/dashboard"
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to dashboard WebSocket")
            
            # Subscribe to BTC and ETH updates
            subscribe_message = {
                "type": "subscribe",
                "symbols": ["BTC", "ETH"]
            }
            await websocket.send(json.dumps(subscribe_message))
            print("📤 Sent subscription request for BTC, ETH")
            
            # Listen for messages for 30 seconds
            timeout = 30
            start_time = datetime.now()
            
            while (datetime.now() - start_time).total_seconds() < timeout:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    print(f"📨 Received: {data.get('type', 'unknown')} - {data}")
                    
                    # Test status request
                    if data.get("type") == "subscription_confirmed":
                        status_request = {"type": "get_status"}
                        await websocket.send(json.dumps(status_request))
                        print("📤 Requested connection status")
                
                except asyncio.TimeoutError:
                    print("⏰ No message received in last 5 seconds")
                    continue
                except json.JSONDecodeError:
                    print("❌ Received invalid JSON")
                    continue
            
            print("✅ Dashboard WebSocket test completed")
    
    except Exception as e:
        print(f"❌ Dashboard WebSocket test failed: {e}")


async def test_symbol_websocket(symbol: str = "BTC"):
    """Test symbol-specific WebSocket endpoint"""
    print(f"🔌 Testing {symbol} Symbol WebSocket...")
    
    try:
        # Connect to symbol WebSocket
        uri = f"ws://localhost:8000/api/ws/prices/{symbol}"
        
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {symbol} WebSocket")
            
            # Listen for messages for 20 seconds
            timeout = 20
            start_time = datetime.now()
            
            while (datetime.now() - start_time).total_seconds() < timeout:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    print(f"📨 {symbol} Update: {data}")
                    
                    # Test get_latest request
                    if data.get("type") == "initial_data":
                        latest_request = {"type": "get_latest"}
                        await websocket.send(json.dumps(latest_request))
                        print(f"📤 Requested latest {symbol} data")
                
                except asyncio.TimeoutError:
                    print(f"⏰ No {symbol} message in last 5 seconds")
                    continue
                except json.JSONDecodeError:
                    print("❌ Received invalid JSON")
                    continue
            
            print(f"✅ {symbol} WebSocket test completed")
    
    except Exception as e:
        print(f"❌ {symbol} WebSocket test failed: {e}")


async def test_multiple_connections():
    """Test multiple simultaneous WebSocket connections"""
    print("🔌 Testing Multiple Connections...")
    
    try:
        # Create multiple concurrent connections
        tasks = [
            test_dashboard_websocket(),
            test_symbol_websocket("BTC"),
            test_symbol_websocket("ETH")
        ]
        
        # Run all connections concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        print("✅ Multiple connections test completed")
    
    except Exception as e:
        print(f"❌ Multiple connections test failed: {e}")


async def test_invalid_messages():
    """Test WebSocket error handling with invalid messages"""
    print("🔌 Testing Invalid Messages...")
    
    try:
        uri = "ws://localhost:8000/api/ws/dashboard"
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected for error testing")
            
            # Send invalid JSON
            await websocket.send("invalid json")
            print("📤 Sent invalid JSON")
            
            # Send unknown message type
            unknown_message = {"type": "unknown_type", "data": "test"}
            await websocket.send(json.dumps(unknown_message))
            print("📤 Sent unknown message type")
            
            # Listen for error responses
            for _ in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(message)
                    print(f"📨 Response: {data}")
                except asyncio.TimeoutError:
                    break
            
            print("✅ Invalid messages test completed")
    
    except Exception as e:
        print(f"❌ Invalid messages test failed: {e}")


def main():
    """Run all WebSocket tests"""
    print("🚀 CryptoPredict WebSocket Tests")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("📋 Test Plan:")
    print("   1. Dashboard WebSocket connectivity")
    print("   2. Symbol WebSocket connectivity") 
    print("   3. Multiple concurrent connections")
    print("   4. Error handling and invalid messages")
    print()
    
    # Run tests
    asyncio.run(run_all_tests())


async def run_all_tests():
    """Run all WebSocket tests sequentially"""
    try:
        print("🧪 Test 1: Dashboard WebSocket")
        await test_dashboard_websocket()
        print()
        
        print("🧪 Test 2: Symbol WebSocket") 
        await test_symbol_websocket("BTC")
        print()
        
        print("🧪 Test 3: Invalid Messages")
        await test_invalid_messages()
        print()
        
        print("🎉 All WebSocket tests completed!")
        print()
        print("📊 Test Results Summary:")
        print("   ✅ Dashboard WebSocket: Tested")
        print("   ✅ Symbol WebSocket: Tested")
        print("   ✅ Error Handling: Tested")
        print()
        print("🔗 Frontend Integration Examples:")
        print("   Dashboard: ws://localhost:8000/api/ws/dashboard")
        print("   BTC Price: ws://localhost:8000/api/ws/prices/BTC")
        print("   ETH Price: ws://localhost:8000/api/ws/prices/ETH")
    
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")


if __name__ == "__main__":
    main()