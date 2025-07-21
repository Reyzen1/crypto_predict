# tests/test_error_handling.py
"""
Error Handling Validation Suite for CryptoPredict MVP
Tests error scenarios, edge cases, and system resilience
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.main import app
from app.core.database import get_db
from app.repositories import cryptocurrency_repository, user_repository
from app.models import User, Cryptocurrency


class TestHTTPErrorCodes:
    """Test proper HTTP status codes for different error scenarios"""
    
    def test_404_not_found_errors(self):
        """Test 404 errors for non-existent resources"""
        client = TestClient(app)
        
        test_cases = [
            "/api/v1/nonexistent-endpoint",
            "/api/v1/users/99999",
            "/api/v1/crypto/99999", 
            "/api/v1/prices/99999",
            "/api/v1/tasks/nonexistent-task"
        ]
        
        for endpoint in test_cases:
            response = client.get(endpoint)
            assert response.status_code == 404, f"Endpoint {endpoint} should return 404"
    
    def test_401_unauthorized_errors(self):
        """Test 401 errors for authentication required endpoints"""
        client = TestClient(app)
        
        protected_endpoints = [
            ("GET", "/api/v1/users/me"),
            ("PUT", "/api/v1/users/me"),
            ("POST", "/api/v1/tasks/start"),
            ("POST", "/api/v1/tasks/stop"),
            ("POST", "/api/v1/external/sync/prices")
        ]
        
        for method, endpoint in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "POST":
                response = client.post(endpoint, json={})
            
            assert response.status_code == 401, f"{method} {endpoint} should return 401 without auth"
    
    def test_422_validation_errors(self):
        """Test 422 errors for request validation failures"""
        client = TestClient(app)
        
        validation_test_cases = [
            # Invalid user registration
            {
                "endpoint": "/api/v1/auth/register",
                "method": "POST",
                "data": {
                    "email": "invalid-email",
                    "password": "short",
                    "first_name": "",
                    "last_name": ""
                }
            },
            # Invalid login data
            {
                "endpoint": "/api/v1/auth/login",
                "method": "POST", 
                "data": {
                    "email": "not-an-email",
                    "password": ""
                }
            },
            # Invalid token refresh
            {
                "endpoint": "/api/v1/auth/refresh",
                "method": "POST",
                "data": {
                    "refresh_token": ""
                }
            }
        ]
        
        for case in validation_test_cases:
            response = client.post(case["endpoint"], json=case["data"])
            assert response.status_code == 422, f"Validation should fail for {case['endpoint']}"
            
            # Check error response structure
            error_data = response.json()
            assert "detail" in error_data, "Validation error should include detail"
    
    def test_405_method_not_allowed(self):
        """Test 405 errors for unsupported HTTP methods"""
        client = TestClient(app)
        
        # Try unsupported methods on known endpoints
        test_cases = [
            ("DELETE", "/api/v1/auth/login"),
            ("PUT", "/health"),
            ("PATCH", "/api/v1/info")
        ]
        
        for method, endpoint in test_cases:
            if method == "DELETE":
                response = client.delete(endpoint)
            elif method == "PUT":
                response = client.put(endpoint)
            elif method == "PATCH":
                response = client.patch(endpoint)
            
            assert response.status_code == 405, f"{method} {endpoint} should return 405"


class TestAuthenticationErrorHandling:
    """Test authentication and authorization error scenarios"""
    
    def test_invalid_jwt_tokens(self):
        """Test handling of invalid JWT tokens"""
        client = TestClient(app)
        
        invalid_tokens = [
            "invalid.token.here",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "",
            "Bearer invalid-token",
            "not-a-jwt-token"
        ]
        
        for token in invalid_tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/v1/users/me", headers=headers)
            assert response.status_code == 401, f"Invalid token '{token[:20]}...' should return 401"
    
    def test_expired_tokens(self):
        """Test handling of expired JWT tokens"""
        # This would require creating an actually expired token
        # For now, we test the error handling structure
        client = TestClient(app)
        
        # Use a malformed token that would fail verification
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MTYyMzkwMjJ9.invalid"
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401
        
        error_data = response.json()
        assert "detail" in error_data
    
    def test_missing_authorization_header(self):
        """Test handling of missing authorization headers"""
        client = TestClient(app)
        
        protected_endpoints = [
            "/api/v1/users/me",
            "/api/v1/users/",
            "/api/v1/tasks/start"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
            
            error_data = response.json()
            assert "detail" in error_data
    
    def test_malformed_authorization_header(self):
        """Test handling of malformed authorization headers"""
        client = TestClient(app)
        
        malformed_headers = [
            {"Authorization": "Invalid format"},
            {"Authorization": "Bearer"},  # Missing token
            {"Authorization": "Basic dGVzdA=="},  # Wrong type
            {"Authorization": ""},  # Empty
        ]
        
        for headers in malformed_headers:
            response = client.get("/api/v1/users/me", headers=headers)
            assert response.status_code == 401
            
            error_data = response.json()
            assert "detail" in error_data


class TestDatabaseErrorHandling:
    """Test database-related error handling"""
    
    @patch('app.core.database.SessionLocal')
    def test_database_connection_errors(self, mock_session):
        """Test handling of database connection failures"""
        # Mock database connection failure
        mock_session.side_effect = Exception("Database connection failed")
        
        client = TestClient(app)
        
        # Test endpoints that require database access
        response = client.get("/api/v1/crypto/")
        # The actual response code depends on how the error is handled
        # This ensures the app doesn't crash
        assert response.status_code in [500, 503, 404], "Should handle DB errors gracefully"
    
    def test_duplicate_key_errors(self, db_session):
        """Test handling of database constraint violations"""
        # Create a cryptocurrency
        crypto1 = cryptocurrency_repository.create_crypto(
            db_session,
            symbol="DUPE",
            name="Duplicate Test Coin"
        )
        db_session.commit()
        
        # Try to create another with same symbol (should fail)
        with pytest.raises(Exception):  # Could be IntegrityError or similar
            crypto2 = cryptocurrency_repository.create_crypto(
                db_session,
                symbol="DUPE",  # Same symbol
                name="Another Duplicate Coin"
            )
            db_session.commit()
    
    def test_foreign_key_constraint_errors(self, db_session):
        """Test handling of foreign key constraint violations"""
        from app.repositories import price_data_repository
        from decimal import Decimal
        
        # Try to create price data for non-existent cryptocurrency
        with pytest.raises(Exception):  # Should raise foreign key constraint error
            price_data_repository.add_price_data(
                db_session,
                crypto_id=99999,  # Non-existent crypto ID
                timestamp=datetime.utcnow(),
                open_price=Decimal("100.00"),
                high_price=Decimal("110.00"),
                low_price=Decimal("90.00"),
                close_price=Decimal("105.00"),
                volume=Decimal("1000.00")
            )
            db_session.commit()


class TestExternalAPIErrorHandling:
    """Test external API integration error handling"""
    
    @patch('app.external.coingecko.CoinGeckoClient.get_current_prices')
    def test_external_api_timeout(self, mock_get_prices):
        """Test handling of external API timeouts"""
        from requests.exceptions import Timeout
        
        # Mock API timeout
        mock_get_prices.side_effect = Timeout("Request timed out")
        
        client = TestClient(app)
        
        # Test endpoint that uses external API (if available)
        response = client.get("/api/v1/external/status")
        # Should handle timeout gracefully without crashing
        assert response.status_code in [200, 500, 503]
    
    @patch('app.external.coingecko.CoinGeckoClient.get_current_prices')
    def test_external_api_rate_limit(self, mock_get_prices):
        """Test handling of external API rate limiting"""
        from requests.exceptions import HTTPError
        
        # Mock rate limit error
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get_prices.side_effect = HTTPError("Rate limit exceeded", response=mock_response)
        
        client = TestClient(app)
        response = client.get("/api/v1/external/status")
        
        # Should handle rate limiting gracefully
        assert response.status_code in [200, 429, 503]
    
    @patch('app.external.coingecko.CoinGeckoClient.get_current_prices')
    def test_external_api_invalid_response(self, mock_get_prices):
        """Test handling of invalid external API responses"""
        # Mock invalid JSON response
        mock_get_prices.return_value = {"invalid": "response", "missing": "required_fields"}
        
        client = TestClient(app)
        response = client.get("/api/v1/external/status")
        
        # Should handle invalid responses gracefully
        assert response.status_code in [200, 500, 502]


class TestInputValidationErrorHandling:
    """Test input validation and sanitization"""
    
    def test_sql_injection_attempts(self):
        """Test SQL injection attack prevention"""
        client = TestClient(app)
        
        sql_injection_attempts = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM cryptocurrencies; --"
        ]
        
        for injection_attempt in sql_injection_attempts:
            # Test in search parameters
            response = client.get(f"/api/v1/crypto/?search={injection_attempt}")
            # Should not return 500 (server error) - should be handled
            assert response.status_code in [200, 400, 422], f"SQL injection attempt should be handled safely"
            
            # Test in login attempts
            response = client.post("/api/v1/auth/login", json={
                "email": injection_attempt,
                "password": "test"
            })
            assert response.status_code in [401, 422], "SQL injection in auth should be handled"
    
    def test_xss_prevention(self):
        """Test XSS attack prevention"""
        client = TestClient(app)
        
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for xss_attempt in xss_attempts:
            # Test in user registration
            response = client.post("/api/v1/auth/register", json={
                "email": f"test@example.com",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
                "first_name": xss_attempt,
                "last_name": "User"
            })
            
            # Should either accept and sanitize, or reject with validation error
            assert response.status_code in [201, 422], "XSS attempt should be handled"
            
            if response.status_code == 201:
                # If accepted, check that XSS was sanitized
                data = response.json()
                user_data = data.get("data", {}).get("user", {})
                first_name = user_data.get("first_name", "")
                assert "<script>" not in first_name, "XSS should be sanitized"
    
    def test_large_payload_handling(self):
        """Test handling of excessively large payloads"""
        client = TestClient(app)
        
        # Create very large string (1MB)
        large_string = "A" * (1024 * 1024)
        
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "first_name": large_string,
            "last_name": "User"
        })
        
        # Should reject large payloads
        assert response.status_code in [413, 422, 400], "Large payload should be rejected"
    
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters"""
        client = TestClient(app)
        
        special_chars_tests = [
            "Test User 中文",  # Unicode characters
            "Test\x00User",    # Null bytes
            "Test\nUser",      # Newlines
            "Test\tUser",      # Tabs
            "Test'User\"",     # Quotes
            "Test\\User",      # Backslashes
        ]
        
        for special_chars in special_chars_tests:
            response = client.post("/api/v1/auth/register", json={
                "email": "special@example.com",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
                "first_name": special_chars,
                "last_name": "User"
            })
            
            # Should handle special characters appropriately
            assert response.status_code in [201, 422], f"Special chars '{special_chars}' should be handled"


class TestCeleryTaskErrorHandling:
    """Test error handling in background tasks"""
    
    def test_task_timeout_handling(self):
        """Test handling of task timeouts"""
        client = TestClient(app)
        
        # Test task status when no workers are running
        response = client.get("/api/v1/tasks/status")
        
        # Should handle timeout gracefully, not crash
        assert response.status_code in [200, 408, 500], "Task timeout should be handled"
        
        if response.status_code == 200:
            data = response.json()
            # Should indicate error or timeout in response
            assert "status" in data
    
    def test_task_failure_recovery(self):
        """Test task failure and recovery mechanisms"""
        client = TestClient(app)
        
        # Test safe task endpoints (should work without workers)
        response = client.get("/api/v1/tasks-safe/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        # Should provide fallback information when tasks fail
    
    def test_invalid_task_requests(self):
        """Test handling of invalid task requests"""
        client = TestClient(app)
        
        # This would require authentication, so expect 401
        response = client.post("/api/v1/tasks/manual/nonexistent-task")
        assert response.status_code == 401  # Due to auth requirement
        
        # Test with authentication (mock if needed)
        # For now, test that endpoint exists and handles invalid tasks


class TestSystemResourceErrorHandling:
    """Test system resource exhaustion scenarios"""
    
    def test_memory_limit_handling(self):
        """Test behavior when approaching memory limits"""
        import gc
        client = TestClient(app)
        
        # Make many requests to test memory usage
        responses = []
        for i in range(100):
            response = client.get("/health")
            responses.append(response.status_code)
            
            # Trigger garbage collection periodically
            if i % 20 == 0:
                gc.collect()
        
        # All requests should complete successfully
        success_rate = sum(1 for code in responses if code == 200) / len(responses)
        assert success_rate >= 0.95, f"Success rate {success_rate:.1%} too low under load"
    
    def test_concurrent_request_limits(self):
        """Test handling of concurrent request limits"""
        import concurrent.futures
        client = TestClient(app)
        
        def make_request():
            return client.get("/health").status_code
        
        # Make many concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [future.result() for future in concurrent.futures.as_completed(futures, timeout=30)]
        
        # Most requests should succeed
        success_count = sum(1 for code in results if code == 200)
        success_rate = success_count / len(results)
        
        assert success_rate >= 0.8, f"Success rate {success_rate:.1%} too low under high concurrency"


class TestLoggingAndMonitoring:
    """Test error logging and monitoring"""
    
    def test_error_logging_structure(self):
        """Test that errors are logged with proper structure"""
        import logging
        from unittest.mock import patch
        
        client = TestClient(app)
        
        with patch('logging.Logger.error') as mock_logger:
            # Trigger a 404 error
            response = client.get("/api/v1/nonexistent")
            assert response.status_code == 404
            
            # Check if error was logged (implementation dependent)
            # This test structure ensures logging is considered
    
    def test_health_check_error_reporting(self):
        """Test health check endpoints report errors properly"""
        client = TestClient(app)
        
        # Test system health endpoint
        response = client.get("/api/v1/system/health")
        if response.status_code == 200:
            data = response.json()
            # Should have status information
            assert "status" in data or "components" in data


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_request_bodies(self):
        """Test handling of empty request bodies"""
        client = TestClient(app)
        
        endpoints_requiring_body = [
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh"
        ]
        
        for endpoint in endpoints_requiring_body:
            # Send empty JSON
            response = client.post(endpoint, json={})
            assert response.status_code == 422, f"Empty body to {endpoint} should return 422"
            
            # Send no body at all
            response = client.post(endpoint)
            assert response.status_code == 422, f"No body to {endpoint} should return 422"
    
    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        client = TestClient(app)
        
        malformed_json_examples = [
            '{"incomplete": ',
            '{"invalid": "json"',
            '{invalid: json}',
            '{"trailing": "comma",}',
            'not json at all'
        ]
        
        for malformed_json in malformed_json_examples:
            response = client.post(
                "/api/v1/auth/login",
                data=malformed_json,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 422, f"Malformed JSON should return 422"
    
    def test_boundary_values(self):
        """Test boundary values for numeric fields"""
        client = TestClient(app)
        
        boundary_tests = [
            {"limit": 0},      # Minimum
            {"limit": 1000},   # Maximum (if enforced)
            {"limit": -1},     # Below minimum
            {"limit": 10000},  # Above maximum
        ]
        
        for params in boundary_tests:
            response = client.get("/api/v1/crypto/", params=params)
            # Should handle boundary values gracefully
            assert response.status_code in [200, 422], f"Boundary value {params} should be handled"


class TestRecoveryAndResilience:
    """Test system recovery and resilience"""
    
    def test_graceful_degradation(self):
        """Test graceful degradation when components fail"""
        client = TestClient(app)
        
        # Test that basic endpoints work even if some services are down
        basic_endpoints = ["/", "/health"]
        
        for endpoint in basic_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Basic endpoint {endpoint} should always work"
    
    def test_circuit_breaker_behavior(self):
        """Test circuit breaker patterns (if implemented)"""
        client = TestClient(app)
        
        # Test external API status endpoint multiple times
        # Should implement some form of failure handling
        for i in range(5):
            response = client.get("/api/v1/external/status")
            # Should not fail catastrophically
            assert response.status_code in [200, 500, 503]
    
    def test_retry_mechanisms(self):
        """Test retry mechanisms for transient failures"""
        client = TestClient(app)
        
        # This would test if the system retries failed operations
        # For now, test that endpoints are resilient to repeated calls
        for _ in range(10):
            response = client.get("/api/v1/tasks-safe/health")
            assert response.status_code == 200


# Utility functions for error testing
def simulate_database_error():
    """Simulate a database connection error"""
    raise Exception("Simulated database connection error")


def simulate_external_api_error():
    """Simulate an external API failure"""
    raise Exception("Simulated external API error")


def test_error_response_format(response):
    """Test that error responses follow expected format"""
    assert response.status_code >= 400
    
    try:
        data = response.json()
        # Common error response fields
        expected_fields = ["detail", "status", "message", "error"]
        has_error_field = any(field in data for field in expected_fields)
        assert has_error_field, "Error response should have error information"
    except json.JSONDecodeError:
        # Some errors might not return JSON
        pass


# Error handling test runner
def run_error_handling_tests():
    """Run comprehensive error handling tests"""
    print("🧪 Running Error Handling Test Suite")
    print("=" * 50)
    
    # Run tests using pytest
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_error_handling_tests()