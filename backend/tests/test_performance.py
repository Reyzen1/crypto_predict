# tests/test_performance.py
"""
Performance Testing Suite for CryptoPredict MVP
Tests API response times, database performance, and system load handling
"""

import pytest
import time
import asyncio
import concurrent.futures
from httpx import AsyncClient
from fastapi.testclient import TestClient
import psutil
import statistics
from typing import List, Dict, Any
from datetime import datetime

from app.main import app
from app.core.database import SessionLocal
from app.repositories import cryptocurrency_repository, price_data_repository


class PerformanceMetrics:
    """Class to collect and analyze performance metrics"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.memory_usage: List[float] = []
        self.cpu_usage: List[float] = []
        self.start_time: float = 0
        self.end_time: float = 0
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        self.response_times.clear()
        self.memory_usage.clear()
        self.cpu_usage.clear()
    
    def record_response_time(self, response_time: float):
        """Record API response time"""
        self.response_times.append(response_time)
    
    def record_system_metrics(self):
        """Record current system metrics"""
        self.memory_usage.append(psutil.virtual_memory().percent)
        self.cpu_usage.append(psutil.cpu_percent(interval=None))
    
    def stop_monitoring(self):
        """Stop monitoring and calculate final metrics"""
        self.end_time = time.time()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        if not self.response_times:
            return {"error": "No metrics collected"}
        
        return {
            "response_times": {
                "mean": statistics.mean(self.response_times),
                "median": statistics.median(self.response_times),
                "min": min(self.response_times),
                "max": max(self.response_times),
                "p95": self._percentile(self.response_times, 95),
                "p99": self._percentile(self.response_times, 99),
                "count": len(self.response_times)
            },
            "memory_usage": {
                "mean": statistics.mean(self.memory_usage) if self.memory_usage else 0,
                "max": max(self.memory_usage) if self.memory_usage else 0
            },
            "cpu_usage": {
                "mean": statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
                "max": max(self.cpu_usage) if self.cpu_usage else 0
            },
            "total_duration": self.end_time - self.start_time if self.end_time else 0
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]


@pytest.fixture
def performance_metrics():
    """Performance metrics fixture"""
    return PerformanceMetrics()


@pytest.fixture
def test_client():
    """Test client fixture"""
    return TestClient(app)


class TestAPIResponseTimes:
    """Test API endpoint response times"""
    
    def test_health_endpoints_performance(self, test_client, performance_metrics):
        """Test performance of health check endpoints"""
        endpoints = [
            "/health",
            "/api/v1/info",
            "/api/v1/system/health",
            "/api/v1/tasks-safe/health"
        ]
        
        performance_metrics.start_monitoring()
        
        for endpoint in endpoints:
            for _ in range(10):  # Test each endpoint 10 times
                start_time = time.time()
                response = test_client.get(endpoint)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # Convert to ms
                performance_metrics.record_response_time(response_time)
                performance_metrics.record_system_metrics()
                
                # Assert response is successful and under 500ms
                assert response.status_code == 200
                assert response_time < 500, f"Endpoint {endpoint} took {response_time:.2f}ms"
        
        performance_metrics.stop_monitoring()
        summary = performance_metrics.get_summary()
        
        # Performance assertions
        assert summary["response_times"]["mean"] < 200, f"Mean response time {summary['response_times']['mean']:.2f}ms exceeds 200ms"
        assert summary["response_times"]["p95"] < 400, f"95th percentile {summary['response_times']['p95']:.2f}ms exceeds 400ms"
        
        print(f"Health endpoints performance summary: {summary}")
    
    def test_api_endpoints_performance(self, test_client, performance_metrics):
        """Test performance of main API endpoints"""
        endpoints = [
            "/api/v1/crypto/",
            "/api/v1/prices/",
            "/api/v1/tasks-safe/status"
        ]
        
        performance_metrics.start_monitoring()
        
        for endpoint in endpoints:
            for _ in range(5):  # Test each endpoint 5 times
                start_time = time.time()
                response = test_client.get(endpoint)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000
                performance_metrics.record_response_time(response_time)
                
                # Assert response is successful and under 1000ms
                assert response.status_code == 200
                assert response_time < 1000, f"Endpoint {endpoint} took {response_time:.2f}ms"
        
        performance_metrics.stop_monitoring()
        summary = performance_metrics.get_summary()
        
        print(f"API endpoints performance summary: {summary}")


class TestConcurrentLoad:
    """Test system performance under concurrent load"""
    
    def test_concurrent_health_checks(self, test_client, performance_metrics):
        """Test concurrent requests to health check endpoint"""
        def make_health_request():
            start_time = time.time()
            response = test_client.get("/health")
            end_time = time.time()
            return response, (end_time - start_time) * 1000
        
        performance_metrics.start_monitoring()
        
        # Make 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_health_request) for _ in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        performance_metrics.stop_monitoring()
        
        # Analyze results
        response_times = [result[1] for result in results]
        responses = [result[0] for result in results]
        
        # All requests should be successful
        for response in responses:
            assert response.status_code == 200
        
        # Calculate statistics
        mean_time = statistics.mean(response_times)
        max_time = max(response_times)
        
        # Performance assertions
        assert mean_time < 500, f"Mean response time {mean_time:.2f}ms under load exceeds 500ms"
        assert max_time < 2000, f"Max response time {max_time:.2f}ms under load exceeds 2000ms"
        
        print(f"Concurrent load test - Mean: {mean_time:.2f}ms, Max: {max_time:.2f}ms")
    
    def test_mixed_endpoint_load(self, test_client, performance_metrics):
        """Test mixed load across different endpoints"""
        endpoints = [
            "/health",
            "/api/v1/info",
            "/api/v1/crypto/",
            "/api/v1/tasks-safe/status"
        ]
        
        def make_mixed_request(endpoint):
            start_time = time.time()
            response = test_client.get(endpoint)
            end_time = time.time()
            return endpoint, response, (end_time - start_time) * 1000
        
        performance_metrics.start_monitoring()
        
        # Make 30 mixed concurrent requests (different endpoints)
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = []
            for i in range(30):
                endpoint = endpoints[i % len(endpoints)]
                futures.append(executor.submit(make_mixed_request, endpoint))
            
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        performance_metrics.stop_monitoring()
        
        # Analyze results by endpoint
        by_endpoint = {}
        for endpoint, response, response_time in results:
            if endpoint not in by_endpoint:
                by_endpoint[endpoint] = {"times": [], "responses": []}
            by_endpoint[endpoint]["times"].append(response_time)
            by_endpoint[endpoint]["responses"].append(response)
        
        # Assert all responses successful and within limits
        for endpoint, data in by_endpoint.items():
            mean_time = statistics.mean(data["times"])
            success_rate = sum(1 for r in data["responses"] if r.status_code == 200) / len(data["responses"])
            
            assert success_rate == 1.0, f"Endpoint {endpoint} had {success_rate:.1%} success rate"
            assert mean_time < 1000, f"Endpoint {endpoint} mean time {mean_time:.2f}ms exceeds limit"
            
            print(f"{endpoint}: {mean_time:.2f}ms average, {success_rate:.1%} success rate")


class TestDatabasePerformance:
    """Test database operation performance"""
    
    def test_repository_performance(self, performance_metrics):
        """Test repository operation performance"""
        db = SessionLocal()
        
        try:
            performance_metrics.start_monitoring()
            
            # Test cryptocurrency repository operations
            for i in range(100):
                start_time = time.time()
                
                # Create
                crypto = cryptocurrency_repository.create_crypto(
                    db,
                    symbol=f"TEST{i}",
                    name=f"Test Coin {i}",
                    coingecko_id=f"test-coin-{i}"
                )
                
                # Read
                retrieved = cryptocurrency_repository.get_by_symbol(db, f"TEST{i}")
                assert retrieved is not None
                
                # Update (through repository)
                updated = cryptocurrency_repository.activate_crypto(db, crypto.id)
                assert updated is not None
                
                end_time = time.time()
                operation_time = (end_time - start_time) * 1000
                performance_metrics.record_response_time(operation_time)
                
                # Assert operation completed within reasonable time
                assert operation_time < 100, f"Database operation {i} took {operation_time:.2f}ms"
            
            performance_metrics.stop_monitoring()
            summary = performance_metrics.get_summary()
            
            # Performance assertions
            assert summary["response_times"]["mean"] < 50, f"Mean DB operation time {summary['response_times']['mean']:.2f}ms exceeds 50ms"
            
            print(f"Database operations performance: {summary}")
            
        finally:
            # Cleanup
            db.query(cryptocurrency_repository.model).filter(
                cryptocurrency_repository.model.symbol.like("TEST%")
            ).delete()
            db.commit()
            db.close()
    
    def test_bulk_operations_performance(self, performance_metrics):
        """Test bulk database operations performance"""
        db = SessionLocal()
        
        try:
            performance_metrics.start_monitoring()
            
            # Bulk insert test
            start_time = time.time()
            
            cryptos = []
            for i in range(50):
                crypto = cryptocurrency_repository.create_crypto(
                    db,
                    symbol=f"BULK{i}",
                    name=f"Bulk Test Coin {i}",
                    coingecko_id=f"bulk-test-{i}"
                )
                cryptos.append(crypto)
            
            db.commit()  # Commit all at once
            
            end_time = time.time()
            bulk_insert_time = (end_time - start_time) * 1000
            
            # Bulk read test
            start_time = time.time()
            
            active_cryptos = cryptocurrency_repository.get_active_cryptos(db, limit=50)
            
            end_time = time.time()
            bulk_read_time = (end_time - start_time) * 1000
            
            performance_metrics.stop_monitoring()
            
            # Assertions
            assert len(cryptos) == 50, "Failed to create all test cryptocurrencies"
            assert len(active_cryptos) >= 50, "Failed to retrieve active cryptocurrencies"
            assert bulk_insert_time < 2000, f"Bulk insert took {bulk_insert_time:.2f}ms"
            assert bulk_read_time < 500, f"Bulk read took {bulk_read_time:.2f}ms"
            
            print(f"Bulk insert: {bulk_insert_time:.2f}ms, Bulk read: {bulk_read_time:.2f}ms")
            
        finally:
            # Cleanup
            db.query(cryptocurrency_repository.model).filter(
                cryptocurrency_repository.model.symbol.like("BULK%")
            ).delete()
            db.commit()
            db.close()


class TestMemoryUsage:
    """Test memory usage patterns"""
    
    def test_memory_stability_under_load(self, test_client):
        """Test memory usage remains stable under load"""
        initial_memory = psutil.virtual_memory().percent
        
        # Make 100 requests to different endpoints
        for i in range(100):
            endpoint = ["/health", "/api/v1/info", "/api/v1/crypto/"][i % 3]
            response = test_client.get(endpoint)
            assert response.status_code == 200
            
            # Check memory every 10 requests
            if i % 10 == 0:
                current_memory = psutil.virtual_memory().percent
                memory_growth = current_memory - initial_memory
                
                # Memory growth should be minimal (less than 5% increase)
                assert memory_growth < 5.0, f"Memory usage grew by {memory_growth:.1f}% after {i} requests"
        
        final_memory = psutil.virtual_memory().percent
        total_growth = final_memory - initial_memory
        
        print(f"Memory usage - Initial: {initial_memory:.1f}%, Final: {final_memory:.1f}%, Growth: {total_growth:.1f}%")
        
        # Assert total memory growth is reasonable
        assert total_growth < 10.0, f"Total memory growth {total_growth:.1f}% exceeds 10%"


class TestLoadPatterns:
    """Test various load patterns and scenarios"""
    
    def test_burst_load_handling(self, test_client, performance_metrics):
        """Test handling of sudden burst load"""
        # Simulate burst: 50 requests in quick succession
        performance_metrics.start_monitoring()
        
        start_time = time.time()
        
        responses = []
        for _ in range(50):
            response = test_client.get("/health")
            responses.append(response)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        performance_metrics.stop_monitoring()
        
        # All responses should be successful
        success_count = sum(1 for r in responses if r.status_code == 200)
        success_rate = success_count / len(responses)
        
        # Calculate throughput
        throughput = len(responses) / total_time  # requests per second
        
        # Assertions
        assert success_rate >= 0.95, f"Success rate {success_rate:.1%} below 95%"
        assert throughput >= 10, f"Throughput {throughput:.1f} req/s below minimum 10 req/s"
        assert total_time < 30, f"Burst load took {total_time:.2f}s, exceeding 30s limit"
        
        print(f"Burst load - {success_rate:.1%} success rate, {throughput:.1f} req/s throughput")


# Utility functions for performance testing
def measure_endpoint_performance(client: TestClient, endpoint: str, iterations: int = 10) -> Dict[str, float]:
    """Measure endpoint performance over multiple iterations"""
    times = []
    
    for _ in range(iterations):
        start_time = time.time()
        response = client.get(endpoint)
        end_time = time.time()
        
        if response.status_code == 200:
            times.append((end_time - start_time) * 1000)
    
    if not times:
        return {"error": "No successful requests"}
    
    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
        "count": len(times)
    }


def run_performance_benchmark():
    """Run complete performance benchmark suite"""
    print("🚀 Starting Performance Benchmark Suite")
    print("=" * 50)
    
    client = TestClient(app)
    
    # Test key endpoints
    endpoints = [
        "/health",
        "/api/v1/info",
        "/api/v1/crypto/",
        "/api/v1/tasks-safe/status"
    ]
    
    for endpoint in endpoints:
        print(f"\n📊 Testing {endpoint}")
        metrics = measure_endpoint_performance(client, endpoint, 20)
        print(f"Mean: {metrics.get('mean', 0):.2f}ms, "
              f"P95: {metrics.get('max', 0):.2f}ms, "
              f"Requests: {metrics.get('count', 0)}")
    
    print("\n✅ Performance benchmark completed!")


if __name__ == "__main__":
    # Run benchmark when executed directly
    run_performance_benchmark()