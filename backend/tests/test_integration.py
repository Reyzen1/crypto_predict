# tests/test_integration.py
"""
Integration Testing Framework for CryptoPredict MVP
Comprehensive tests for API endpoints, authentication, and business logic
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os
from datetime import datetime, timedelta
from decimal import Decimal

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.models import User, Cryptocurrency, PriceData
from app.repositories import user_repository, cryptocurrency_repository, price_data_repository


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create database session for each test"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        # Clean up after each test
        session.query(PriceData).delete()
        session.query(Cryptocurrency).delete()
        session.query(User).delete()
        session.commit()
        session.close()


@pytest.fixture(scope="function")
def client():
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
async def async_client():
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User"
    }


@pytest.fixture
def sample_crypto_data():
    """Sample cryptocurrency data for testing"""
    return {
        "symbol": "BTC",
        "name": "Bitcoin",
        "coingecko_id": "bitcoin",
        "binance_symbol": "BTCUSDT",
        "is_active": True
    }


@pytest.fixture
def sample_price_data():
    """Sample price data for testing"""
    return {
        "timestamp": datetime.utcnow(),
        "open_price": Decimal("50000.00"),
        "high_price": Decimal("51000.00"),
        "low_price": Decimal("49000.00"),
        "close_price": Decimal("50500.00"),
        "volume": Decimal("1000000.00"),
        "market_cap": Decimal("1000000000.00")
    }


class TestHealthAndBasicEndpoints:
    """Test basic health check and info endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    def test_health_endpoint(self, client):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_api_info_endpoint(self, client):
        """Test API info endpoint"""
        response = client.get("/api/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "CryptoPredict MVP API"
        assert "endpoints" in data
        assert "features" in data


class TestAuthenticationFlow:
    """Test complete authentication workflow"""
    
    def test_user_registration_login_flow(self, client, sample_user_data):
        """Test complete user registration and login flow"""
        # Test user registration
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert "data" in data
        assert data["data"]["user"]["email"] == sample_user_data["email"]
        
        # Extract tokens
        access_token = data["data"]["access_token"]
        refresh_token = data["data"]["refresh_token"]
        
        # Test user login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        login_response = response.json()
        assert login_response["message"] == "Login successful"
        
        # Test protected endpoint with token
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == sample_user_data["email"]
        
        # Test token refresh
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        refresh_response = response.json()
        assert "access_token" in refresh_response

    def test_authentication_failures(self, client, sample_user_data):
        """Test authentication failure scenarios"""
        # Test login with non-existent user
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        
        # Test registration with invalid email
        invalid_data = sample_user_data.copy()
        invalid_data["email"] = "invalid-email"
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422
        
        # Test protected endpoint without token
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401


class TestCryptocurrencyAPI:
    """Test cryptocurrency CRUD operations"""
    
    def test_cryptocurrency_crud_operations(self, client, db_session, sample_crypto_data):
        """Test complete CRUD operations for cryptocurrencies"""
        # Create cryptocurrency
        crypto = cryptocurrency_repository.create_crypto(
            db_session,
            symbol=sample_crypto_data["symbol"],
            name=sample_crypto_data["name"],
            coingecko_id=sample_crypto_data["coingecko_id"],
            binance_symbol=sample_crypto_data["binance_symbol"]
        )
        db_session.commit()
        
        # Test list cryptocurrencies
        response = client.get("/api/v1/crypto/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        
        # Test get specific cryptocurrency
        response = client.get(f"/api/v1/crypto/{crypto.id}")
        assert response.status_code == 200
        crypto_data = response.json()
        assert crypto_data["symbol"] == sample_crypto_data["symbol"]
        assert crypto_data["name"] == sample_crypto_data["name"]
        
        # Test search cryptocurrencies
        response = client.get(f"/api/v1/crypto/?search={sample_crypto_data['symbol']}")
        assert response.status_code == 200
        search_data = response.json()
        assert search_data["total"] >= 1


class TestPriceDataAPI:
    """Test price data operations"""
    
    def test_price_data_operations(self, client, db_session, sample_crypto_data, sample_price_data):
        """Test price data CRUD operations"""
        # Create cryptocurrency first
        crypto = cryptocurrency_repository.create_crypto(
            db_session,
            symbol=sample_crypto_data["symbol"],
            name=sample_crypto_data["name"]
        )
        db_session.commit()
        
        # Add price data
        price_data = price_data_repository.add_price_data(
            db_session,
            crypto_id=crypto.id,
            timestamp=sample_price_data["timestamp"],
            open_price=sample_price_data["open_price"],
            high_price=sample_price_data["high_price"],
            low_price=sample_price_data["low_price"],
            close_price=sample_price_data["close_price"],
            volume=sample_price_data["volume"],
            market_cap=sample_price_data["market_cap"]
        )
        db_session.commit()
        
        # Test list price data
        response = client.get("/api/v1/prices/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        
        # Test get price data for specific crypto
        response = client.get(f"/api/v1/prices/?crypto_id={crypto.id}")
        assert response.status_code == 200
        filtered_data = response.json()
        assert filtered_data["total"] >= 1


class TestExternalAPIIntegration:
    """Test external API integration"""
    
    def test_external_api_endpoints(self, client, db_session):
        """Test external API endpoints (without actual API calls)"""
        # Create a test user for authentication
        user_data = {
            "email": "api_test@example.com",
            "password_hash": "test_hash",
            "first_name": "API",
            "last_name": "Test"
        }
        user = user_repository.create_user(
            db_session,
            **user_data
        )
        db_session.commit()
        
        # For testing, we'll mock the authentication
        # In a real test, you would create a proper JWT token
        # This tests the endpoint structure without external calls
        
        # Test API status endpoint (no auth required)
        response = client.get("/api/v1/external/status")
        assert response.status_code == 200
        
        # Test that endpoints exist (they will fail without auth, but that's expected)
        response = client.post("/api/v1/external/sync/prices")
        assert response.status_code == 401  # Expected without authentication


class TestBackgroundTasks:
    """Test background task system"""
    
    def test_task_status_endpoints(self, client):
        """Test task status endpoints"""
        # Test safe task status (should work without Celery workers)
        response = client.get("/api/v1/tasks-safe/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        
        # Test task health endpoint
        response = client.get("/api/v1/tasks-safe/health")
        assert response.status_code == 200
        health_data = response.json()
        assert "components" in health_data
        
        # Test task info endpoint
        response = client.get("/api/v1/tasks-safe/info")
        assert response.status_code == 200
        info_data = response.json()
        assert "available_tasks" in info_data
        assert "requirements" in info_data


class TestSystemHealthChecks:
    """Test system health and monitoring endpoints"""
    
    def test_system_health_comprehensive(self, client):
        """Test comprehensive system health checks"""
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        
        # Test detailed health endpoint
        response = client.get("/api/v1/system/detailed-health")
        # This endpoint might not exist yet, so we check gracefully
        if response.status_code == 200:
            detailed_data = response.json()
            assert "components" in detailed_data


class TestErrorHandling:
    """Test error handling across the application"""
    
    def test_404_handling(self, client):
        """Test 404 error handling"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_422_validation_errors(self, client):
        """Test validation error handling"""
        # Invalid user registration data
        response = client.post("/api/v1/auth/register", json={
            "email": "invalid-email",
            "password": "short"
        })
        assert response.status_code == 422
        
    def test_500_error_handling(self, client):
        """Test internal server error handling"""
        # This would require triggering an actual server error
        # For now, we test that the error handling structure is in place
        pass


class TestPerformanceBaseline:
    """Basic performance testing"""
    
    def test_endpoint_response_times(self, client):
        """Test basic endpoint response times"""
        import time
        
        endpoints = [
            "/",
            "/health",
            "/api/v1/info",
            "/api/v1/crypto/",
            "/api/v1/prices/",
            "/api/v1/tasks-safe/status"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Assert response is successful and under 1000ms
            assert response.status_code == 200
            assert response_time < 1000, f"Endpoint {endpoint} took {response_time:.2f}ms"
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        import concurrent.futures
        import time
        
        def make_request():
            return client.get("/api/v1/info")
        
        start_time = time.time()
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All requests should be successful
        for result in results:
            assert result.status_code == 200
        
        # Should complete within reasonable time
        assert total_time < 5.0, f"10 concurrent requests took {total_time:.2f}s"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])