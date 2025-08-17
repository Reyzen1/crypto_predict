# File: temp/tradingview_api_tester.py
# TradingView API Complete Testing Script
# ⚠️ Use responsibly and comply with TradingView Terms of Service

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import random
from dataclasses import dataclass
from urllib.parse import urlencode

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Result of a test operation"""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    rate_limited: bool = False

class TradingViewAPITester:
    """
    Comprehensive TradingView API Testing Suite
    ⚠️ IMPORTANT: This script is for testing purposes only
    ⚠️ Make sure to comply with TradingView Terms of Service
    """
    
    def __init__(self):
        self.session = None
        self.base_urls = {
            'symbol_search': 'https://symbol-search.tradingview.com',
            'scanner': 'https://scanner.tradingview.com',
            'charts': 'https://chartdata1.tradingview.com',
            'main': 'https://www.tradingview.com'
        }
        
        # Test symbols for dominance
        self.test_symbols = [
            'BTC.D',           # Bitcoin Dominance
            'ETH.D',           # Ethereum Dominance
            'OTHERS.D',        # Others Dominance
            'TOTAL',           # Total Market Cap
            'TOTAL2',          # Total without BTC
            'TOTAL3',          # Total without BTC and ETH
            'TOTALDEFI'        # DeFi Market Cap
        ]
        
        # Request headers to mimic browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
        }
        
        self.test_results = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def run_comprehensive_test(self) -> Dict:
        """Run all tests and return comprehensive results"""
        logger.info("🚀 Starting TradingView API Comprehensive Test")
        
        # Test categories
        tests = [
            ("Public Endpoints", self.test_public_endpoints),
            ("Symbol Search", self.test_symbol_search),
            ("UDF History", self.test_udf_history),
            ("Real-time Data", self.test_realtime_data),
            ("Scanner API", self.test_scanner_api),
            ("Rate Limiting", self.test_rate_limiting),
            ("Data Quality", self.test_data_quality),
            ("Historical Depth", self.test_historical_depth)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"🧪 Running {test_name} test...")
            try:
                results[test_name] = await test_func()
                await asyncio.sleep(1)  # Respectful delay between tests
            except Exception as e:
                logger.error(f"❌ {test_name} test failed: {e}")
                results[test_name] = TestResult(
                    success=False,
                    error=str(e)
                )
        
        # Generate summary report
        summary = self.generate_summary_report(results)
        results['SUMMARY'] = summary
        
        return results
    
    async def test_public_endpoints(self) -> TestResult:
        """Test publicly accessible endpoints"""
        logger.info("Testing public endpoints accessibility...")
        
        public_endpoints = [
            ('symbol_search', '/symbol_search/?text=BTC&exchange=&lang=en&search_type='),
            ('scanner', '/crypto/scan'),
            ('charts', '/api/v1/config'),
        ]
        
        endpoint_results = {}
        
        for name, endpoint in public_endpoints:
            if name in self.base_urls:
                url = self.base_urls[name] + endpoint
                result = await self._make_request('GET', url)
                endpoint_results[name] = result
        
        # Check if any endpoints are accessible
        accessible_count = sum(1 for r in endpoint_results.values() if r.success)
        
        return TestResult(
            success=accessible_count > 0,
            data={
                'accessible_endpoints': accessible_count,
                'total_tested': len(endpoint_results),
                'details': endpoint_results
            }
        )
    
    async def test_symbol_search(self) -> TestResult:
        """Test symbol search functionality"""
        logger.info("Testing symbol search for dominance symbols...")
        
        search_results = {}
        
        for symbol in self.test_symbols:
            # Try different search endpoints
            search_urls = [
                f"{self.base_urls['symbol_search']}/symbol_search/?text={symbol}&exchange=&lang=en",
                f"{self.base_urls['main']}/symbols/{symbol}/",
            ]
            
            symbol_found = False
            for url in search_urls:
                result = await self._make_request('GET', url)
                if result.success:
                    symbol_found = True
                    break
            
            search_results[symbol] = symbol_found
        
        found_symbols = sum(search_results.values())
        
        return TestResult(
            success=found_symbols > 0,
            data={
                'found_symbols': found_symbols,
                'total_symbols': len(self.test_symbols),
                'symbol_results': search_results
            }
        )
    
    async def test_udf_history(self) -> TestResult:
        """Test UDF (Universal Data Feed) history API"""
        logger.info("Testing UDF history API...")
        
        # UDF endpoints to test
        udf_endpoints = [
            '/api/v1/config',
            '/api/v1/time',
            '/api/v1/symbols',
            '/api/v1/history'
        ]
        
        results = {}
        
        for endpoint in udf_endpoints:
            url = self.base_urls['charts'] + endpoint
            
            if endpoint == '/api/v1/history':
                # Test with specific symbol and parameters
                params = {
                    'symbol': 'BTC.D',
                    'resolution': '1D',
                    'from': int((datetime.now() - timedelta(days=10)).timestamp()),
                    'to': int(datetime.now().timestamp())
                }
                url += '?' + urlencode(params)
            
            result = await self._make_request('GET', url)
            results[endpoint] = result
        
        successful_requests = sum(1 for r in results.values() if r.success)
        
        return TestResult(
            success=successful_requests > 0,
            data={
                'successful_endpoints': successful_requests,
                'total_endpoints': len(udf_endpoints),
                'endpoint_results': results
            }
        )
    
    async def test_realtime_data(self) -> TestResult:
        """Test real-time data accessibility"""
        logger.info("Testing real-time data access...")
        
        # Try different approaches for real-time data
        realtime_tests = {}
        
        # Test 1: WebSocket connection attempt
        try:
            ws_url = "wss://data.tradingview.com/socket.io/websocket"
            realtime_tests['websocket'] = await self._test_websocket(ws_url)
        except Exception as e:
            realtime_tests['websocket'] = TestResult(success=False, error=str(e))
        
        # Test 2: Quote endpoint
        quote_url = f"{self.base_urls['main']}/symbols/BTC.D/"
        realtime_tests['quote_page'] = await self._make_request('GET', quote_url)
        
        # Test 3: API quote endpoint
        api_quote_url = f"{self.base_urls['symbol_search']}/quotes/?symbols=BTC.D"
        realtime_tests['api_quote'] = await self._make_request('GET', api_quote_url)
        
        successful_tests = sum(1 for r in realtime_tests.values() if r.success)
        
        return TestResult(
            success=successful_tests > 0,
            data={
                'successful_tests': successful_tests,
                'total_tests': len(realtime_tests),
                'test_results': realtime_tests
            }
        )
    
    async def test_scanner_api(self) -> TestResult:
        """Test scanner API for crypto data"""
        logger.info("Testing scanner API...")
        
        scanner_payload = {
            "filter": [
                {"left": "type", "operation": "equal", "right": "crypto"},
                {"left": "subtype", "operation": "equal", "right": "crypto"}
            ],
            "options": {"lang": "en"},
            "symbols": {"query": {"types": []}, "tickers": []},
            "columns": ["name", "close", "change", "change_abs", "high", "low", "volume"],
            "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
            "range": [0, 50]
        }
        
        scanner_url = f"{self.base_urls['scanner']}/crypto/scan"
        
        result = await self._make_request('POST', scanner_url, json_data=scanner_payload)
        
        return TestResult(
            success=result.success,
            data=result.data,
            error=result.error,
            response_time=result.response_time
        )
    
    async def test_rate_limiting(self) -> TestResult:
        """Test rate limiting by making multiple requests"""
        logger.info("Testing rate limiting...")
        
        test_url = f"{self.base_urls['symbol_search']}/symbol_search/?text=BTC"
        
        # Make rapid requests to test rate limiting
        requests_count = 10
        delay_between_requests = 0.1  # 100ms
        
        results = []
        start_time = time.time()
        
        for i in range(requests_count):
            result = await self._make_request('GET', test_url)
            results.append(result)
            
            if not result.success and result.status_code == 429:
                logger.warning(f"Rate limited after {i+1} requests")
                break
            
            await asyncio.sleep(delay_between_requests)
        
        total_time = time.time() - start_time
        successful_requests = sum(1 for r in results if r.success)
        rate_limited = any(r.rate_limited or (r.status_code == 429) for r in results)
        
        return TestResult(
            success=True,  # This test always "succeeds" as it's informational
            data={
                'total_requests': len(results),
                'successful_requests': successful_requests,
                'rate_limited': rate_limited,
                'total_time_seconds': total_time,
                'requests_per_second': len(results) / total_time if total_time > 0 else 0
            }
        )
    
    async def test_data_quality(self) -> TestResult:
        """Test data quality and accuracy"""
        logger.info("Testing data quality...")
        
        # Try to get current data for validation
        quality_tests = {}
        
        # Test 1: Get BTC dominance and check if reasonable
        btc_dom_result = await self._get_symbol_data('BTC.D')
        if btc_dom_result.success and btc_dom_result.data:
            btc_dom_value = btc_dom_result.data.get('value', 0)
            quality_tests['btc_dominance'] = {
                'success': True,
                'value': btc_dom_value,
                'reasonable': 30 <= btc_dom_value <= 70,  # Reasonable range
                'source': 'tradingview'
            }
        else:
            quality_tests['btc_dominance'] = {'success': False}
        
        # Test 2: Check data freshness (timestamp)
        quality_tests['data_freshness'] = await self._check_data_freshness()
        
        successful_quality_tests = sum(1 for t in quality_tests.values() 
                                     if isinstance(t, dict) and t.get('success', False))
        
        return TestResult(
            success=successful_quality_tests > 0,
            data={
                'successful_tests': successful_quality_tests,
                'total_tests': len(quality_tests),
                'quality_results': quality_tests
            }
        )
    
    async def test_historical_depth(self) -> TestResult:
        """Test historical data depth and availability"""
        logger.info("Testing historical data depth...")
        
        # Test different time ranges
        time_ranges = [
            ('1_week', 7),
            ('1_month', 30),
            ('3_months', 90),
            ('1_year', 365),
            ('2_years', 730)
        ]
        
        historical_results = {}
        
        for range_name, days in time_ranges:
            from_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
            to_timestamp = int(datetime.now().timestamp())
            
            params = {
                'symbol': 'BTC.D',
                'resolution': '1D',
                'from': from_timestamp,
                'to': to_timestamp
            }
            
            url = f"{self.base_urls['charts']}/api/v1/history?" + urlencode(params)
            result = await self._make_request('GET', url)
            
            historical_results[range_name] = {
                'success': result.success,
                'days_requested': days,
                'data_points': len(result.data.get('t', [])) if result.success and result.data else 0
            }
        
        successful_ranges = sum(1 for r in historical_results.values() if r['success'])
        
        return TestResult(
            success=successful_ranges > 0,
            data={
                'successful_ranges': successful_ranges,
                'total_ranges': len(time_ranges),
                'range_results': historical_results
            }
        )
    
    async def _make_request(self, method: str, url: str, json_data: Dict = None) -> TestResult:
        """Make HTTP request and return standardized result"""
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                async with self.session.get(url) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 429:
                        return TestResult(
                            success=False,
                            error="Rate limited",
                            response_time=response_time,
                            status_code=429,
                            rate_limited=True
                        )
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                        except:
                            data = await response.text()
                        
                        return TestResult(
                            success=True,
                            data=data,
                            response_time=response_time,
                            status_code=200
                        )
                    else:
                        return TestResult(
                            success=False,
                            error=f"HTTP {response.status}",
                            response_time=response_time,
                            status_code=response.status
                        )
            
            elif method.upper() == 'POST':
                async with self.session.post(url, json=json_data) as response:
                    response_time = time.time() - start_time
                    
                    if response.status in [200, 201]:
                        try:
                            data = await response.json()
                            return TestResult(
                                success=True,
                                data=data,
                                response_time=response_time,
                                status_code=response.status
                            )
                        except:
                            return TestResult(
                                success=False,
                                error="Invalid JSON response",
                                response_time=response_time,
                                status_code=response.status
                            )
                    else:
                        return TestResult(
                            success=False,
                            error=f"HTTP {response.status}",
                            response_time=response_time,
                            status_code=response.status
                        )
        
        except asyncio.TimeoutError:
            return TestResult(
                success=False,
                error="Request timeout",
                response_time=time.time() - start_time
            )
        except Exception as e:
            return TestResult(
                success=False,
                error=str(e),
                response_time=time.time() - start_time
            )
    
    async def _test_websocket(self, ws_url: str) -> TestResult:
        """Test WebSocket connection"""
        try:
            async with self.session.ws_connect(ws_url) as ws:
                # Try to send a ping or connection message
                await ws.send_str('{"type":"ping"}')
                
                # Wait for response with timeout
                try:
                    response = await asyncio.wait_for(ws.receive(), timeout=5.0)
                    return TestResult(success=True, data={'response': str(response)})
                except asyncio.TimeoutError:
                    return TestResult(success=False, error="WebSocket timeout")
                    
        except Exception as e:
            return TestResult(success=False, error=f"WebSocket error: {str(e)}")
    
    async def _get_symbol_data(self, symbol: str) -> TestResult:
        """Get current data for a specific symbol"""
        # Try multiple approaches to get symbol data
        approaches = [
            f"{self.base_urls['symbol_search']}/quotes/?symbols={symbol}",
            f"{self.base_urls['charts']}/api/v1/quotes?symbols={symbol}",
        ]
        
        for url in approaches:
            result = await self._make_request('GET', url)
            if result.success:
                return result
        
        return TestResult(success=False, error="All symbol data approaches failed")
    
    async def _check_data_freshness(self) -> Dict:
        """Check if data is fresh/recent"""
        try:
            time_url = f"{self.base_urls['charts']}/api/v1/time"
            result = await self._make_request('GET', time_url)
            
            if result.success and isinstance(result.data, (int, float)):
                server_time = datetime.fromtimestamp(result.data)
                current_time = datetime.now()
                time_diff = abs((current_time - server_time).total_seconds())
                
                return {
                    'success': True,
                    'server_time': server_time.isoformat(),
                    'local_time': current_time.isoformat(),
                    'time_diff_seconds': time_diff,
                    'is_fresh': time_diff < 300  # Less than 5 minutes difference
                }
            else:
                return {'success': False, 'error': 'Could not get server time'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_summary_report(self, results: Dict) -> Dict:
        """Generate comprehensive summary report"""
        successful_tests = 0
        total_tests = 0
        
        key_findings = []
        recommendations = []
        
        for test_name, result in results.items():
            if test_name == 'SUMMARY':
                continue
                
            total_tests += 1
            if result.success:
                successful_tests += 1
            
            # Analyze results and generate findings
            if test_name == "Public Endpoints" and result.success:
                accessible = result.data.get('accessible_endpoints', 0)
                if accessible > 0:
                    key_findings.append(f"✅ {accessible} public endpoints accessible")
                else:
                    key_findings.append("❌ No public endpoints accessible")
            
            elif test_name == "Symbol Search" and result.success:
                found = result.data.get('found_symbols', 0)
                total = result.data.get('total_symbols', 0)
                if found > 0:
                    key_findings.append(f"✅ {found}/{total} dominance symbols found")
                else:
                    key_findings.append("❌ No dominance symbols found")
            
            elif test_name == "Rate Limiting":
                if result.data.get('rate_limited', False):
                    requests_before_limit = result.data.get('successful_requests', 0)
                    key_findings.append(f"⚠️ Rate limited after {requests_before_limit} requests")
                else:
                    key_findings.append("✅ No immediate rate limiting detected")
        
        # Generate recommendations based on findings
        if successful_tests == 0:
            recommendations.extend([
                "❌ TradingView API access severely limited",
                "🔄 Consider using CoinGecko as primary source",
                "📧 Contact TradingView for official API access"
            ])
        elif successful_tests < total_tests / 2:
            recommendations.extend([
                "⚠️ Limited TradingView API access",
                "🔀 Implement hybrid approach (TradingView + CoinGecko)",
                "⏱️ Implement careful rate limiting"
            ])
        else:
            recommendations.extend([
                "✅ Good TradingView API access potential",
                "🚀 Can implement TradingView as primary source",
                "⚖️ Ensure compliance with Terms of Service"
            ])
        
        return {
            'test_summary': {
                'successful_tests': successful_tests,
                'total_tests': total_tests,
                'success_rate': successful_tests / total_tests if total_tests > 0 else 0
            },
            'key_findings': key_findings,
            'recommendations': recommendations,
            'overall_assessment': self._get_overall_assessment(successful_tests, total_tests),
            'next_steps': self._get_next_steps(successful_tests, total_tests)
        }
    
    def _get_overall_assessment(self, successful: int, total: int) -> str:
        """Get overall assessment based on test results"""
        success_rate = successful / total if total > 0 else 0
        
        if success_rate >= 0.8:
            return "🟢 EXCELLENT - Strong TradingView API access potential"
        elif success_rate >= 0.6:
            return "🟡 GOOD - Moderate TradingView API access with limitations"
        elif success_rate >= 0.3:
            return "🟠 LIMITED - Significant restrictions, hybrid approach recommended"
        else:
            return "🔴 BLOCKED - Minimal access, use alternative sources"
    
    def _get_next_steps(self, successful: int, total: int) -> List[str]:
        """Get recommended next steps"""
        success_rate = successful / total if total > 0 else 0
        
        if success_rate >= 0.6:
            return [
                "1. Review TradingView Terms of Service",
                "2. Implement rate limiting and respectful usage",
                "3. Build TradingView client with error handling",
                "4. Set up CoinGecko as backup source",
                "5. Monitor for API changes or restrictions"
            ]
        else:
            return [
                "1. Focus on CoinGecko implementation first",
                "2. Contact TradingView for official API access",
                "3. Monitor TradingView for policy changes", 
                "4. Consider alternative data sources",
                "5. Implement TradingView only if access improves"
            ]

# Main test execution function
async def run_tradingview_tests():
    """Run the complete TradingView API test suite"""
    print("🚀 TradingView API Complete Test Suite")
    print("=" * 50)
    print("⚠️  IMPORTANT: Use responsibly and comply with Terms of Service")
    print("=" * 50)
    
    async with TradingViewAPITester() as tester:
        results = await tester.run_comprehensive_test()
        
        # Print results
        print("\n📊 TEST RESULTS:")
        print("=" * 50)
        
        for test_name, result in results.items():
            if test_name == 'SUMMARY':
                continue
                
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"{status} {test_name}")
            
            if result.error:
                print(f"   Error: {result.error}")
            if result.response_time:
                print(f"   Response Time: {result.response_time:.2f}s")
        
        # Print summary
        if 'SUMMARY' in results:
            summary = results['SUMMARY']
            print(f"\n📋 SUMMARY:")
            print("=" * 50)
            print(f"Success Rate: {summary['test_summary']['success_rate']:.1%}")
            print(f"Assessment: {summary['overall_assessment']}")
            
            print(f"\n🔍 Key Findings:")
            for finding in summary['key_findings']:
                print(f"  {finding}")
            
            print(f"\n💡 Recommendations:")
            for rec in summary['recommendations']:
                print(f"  {rec}")
            
            print(f"\n🚀 Next Steps:")
            for step in summary['next_steps']:
                print(f"  {step}")
    
    return results

# Entry point
if __name__ == "__main__":
    # Run the test
    results = asyncio.run(run_tradingview_tests())
    
    # Save results to file
    with open('temp/tradingview_test_results.json', 'w') as f:
        # Convert results to JSON-serializable format
        json_results = {}
        for key, value in results.items():
            if hasattr(value, '__dict__'):
                json_results[key] = value.__dict__
            else:
                json_results[key] = value
        
        json.dump(json_results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: temp/tradingview_test_results.json")
    print("🏁 Test completed!")