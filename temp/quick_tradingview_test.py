# File: temp/quick_tradingview_test.py
# Quick TradingView API Test - Simple Version
# Run this first to quickly check TradingView accessibility

import requests
import json
import time
from datetime import datetime, timedelta

def quick_test_tradingview():
    """Quick test of TradingView endpoints"""
    
    print("🚀 Quick TradingView API Test")
    print("=" * 40)
    
    # Headers to mimic browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    # Test endpoints
    tests = [
        {
            'name': 'Symbol Search API',
            'url': 'https://symbol-search.tradingview.com/symbol_search/?text=BTC.D&exchange=&lang=en',
            'method': 'GET'
        },
        {
            'name': 'UDF Config',
            'url': 'https://chartdata1.tradingview.com/api/v1/config',
            'method': 'GET'
        },
        {
            'name': 'UDF Time',
            'url': 'https://chartdata1.tradingview.com/api/v1/time',
            'method': 'GET'
        },
        {
            'name': 'BTC Dominance History',
            'url': 'https://chartdata1.tradingview.com/api/v1/history',
            'method': 'GET',
            'params': {
                'symbol': 'BTC.D',
                'resolution': '1D',
                'from': int((datetime.now() - timedelta(days=7)).timestamp()),
                'to': int(datetime.now().timestamp())
            }
        },
        {
            'name': 'Scanner API',
            'url': 'https://scanner.tradingview.com/crypto/scan',
            'method': 'POST',
            'json': {
                "filter": [{"left": "type", "operation": "equal", "right": "crypto"}],
                "options": {"lang": "en"},
                "columns": ["name", "close", "change"],
                "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
                "range": [0, 5]
            }
        }
    ]
    
    results = {}
    
    for test in tests:
        print(f"\n🧪 Testing {test['name']}...")
        
        try:
            start_time = time.time()
            
            if test['method'] == 'GET':
                response = requests.get(
                    test['url'], 
                    headers=headers,
                    params=test.get('params'),
                    timeout=10
                )
            elif test['method'] == 'POST':
                response = requests.post(
                    test['url'],
                    headers=headers,
                    json=test.get('json'),
                    timeout=10
                )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ SUCCESS - {response.status_code} ({response_time:.2f}s)")
                    
                    # Show sample data
                    if isinstance(data, dict):
                        if 'c' in data and 't' in data:  # UDF history format
                            print(f"   📊 Data points: {len(data.get('t', []))}")
                            if data.get('c'):
                                print(f"   📈 Latest value: {data['c'][-1] if data['c'] else 'N/A'}")
                        elif 'data' in data:  # Scanner format
                            print(f"   📊 Results: {len(data.get('data', []))}")
                        elif isinstance(data, list):
                            print(f"   📊 Items: {len(data)}")
                        else:
                            print(f"   📊 Response type: {type(data)}")
                    
                    results[test['name']] = {
                        'success': True,
                        'status_code': response.status_code,
                        'response_time': response_time,
                        'data_size': len(str(data))
                    }
                    
                except json.JSONDecodeError:
                    print(f"   ⚠️  SUCCESS but not JSON - {response.status_code} ({response_time:.2f}s)")
                    results[test['name']] = {
                        'success': True,
                        'status_code': response.status_code,
                        'response_time': response_time,
                        'note': 'Not JSON response'
                    }
            
            elif response.status_code == 429:
                print(f"   🚫 RATE LIMITED - {response.status_code}")
                results[test['name']] = {
                    'success': False,
                    'status_code': response.status_code,
                    'error': 'Rate limited'
                }
            
            else:
                print(f"   ❌ FAILED - {response.status_code} ({response_time:.2f}s)")
                results[test['name']] = {
                    'success': False,
                    'status_code': response.status_code,
                    'response_time': response_time
                }
        
        except requests.exceptions.Timeout:
            print(f"   ⏰ TIMEOUT")
            results[test['name']] = {
                'success': False,
                'error': 'Timeout'
            }
        
        except Exception as e:
            print(f"   💥 ERROR: {str(e)}")
            results[test['name']] = {
                'success': False,
                'error': str(e)
            }
        
        # Respectful delay
        time.sleep(1)
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print("=" * 40)
    
    successful = sum(1 for r in results.values() if r.get('success', False))
    total = len(results)
    
    print(f"✅ Successful: {successful}/{total} ({successful/total:.1%})")
    
    # Check specific dominance symbols
    print(f"\n🔍 Testing Dominance Symbols:")
    dominance_symbols = ['BTC.D', 'ETH.D', 'OTHERS.D', 'TOTAL2', 'TOTAL3']
    
    for symbol in dominance_symbols:
        print(f"\n   Testing {symbol}...")
        try:
            url = f"https://symbol-search.tradingview.com/symbol_search/?text={symbol}&exchange=&lang=en"
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    print(f"   ✅ {symbol} found")
                else:
                    print(f"   ❌ {symbol} not found")
            else:
                print(f"   ❌ {symbol} failed ({response.status_code})")
        except:
            print(f"   💥 {symbol} error")
        
        time.sleep(0.5)
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("=" * 40)
    
    if successful >= 3:
        print("🟢 GOOD: TradingView API shows promise!")
        print("   → Implement with careful rate limiting")
        print("   → Review Terms of Service")
        print("   → Use as primary or secondary source")
    elif successful >= 1:
        print("🟡 LIMITED: Some endpoints work")
        print("   → Use TradingView as secondary source")
        print("   → Implement CoinGecko as primary")
        print("   → Monitor for changes")
    else:
        print("🔴 BLOCKED: Minimal or no access")
        print("   → Focus on CoinGecko implementation")
        print("   → Contact TradingView for official API")
        print("   → Consider alternative sources")
    
    return results

if __name__ == "__main__":
    results = quick_test_tradingview()
    
    # Save results
    with open('temp/quick_tv_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: temp/quick_tv_test_results.json")
    print("🏁 Quick test completed!")
    
    # Next steps
    print(f"\n🚀 NEXT STEPS:")
    print("1. Review the results above")
    print("2. If successful, run the comprehensive test:")
    print("   python temp/tradingview_api_tester.py")
    print("3. Check TradingView Terms of Service")
    print("4. Implement based on accessibility level")