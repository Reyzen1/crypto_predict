# tests/conftest.py
"""
Test configuration and shared fixtures for CryptoPredict MVP
"""

import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db, Base


# Test database configuration
@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine"""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="session")
def test_db_session_factory(test_db_engine):
    """Create session factory for tests"""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_session_factory):
    """Create fresh database session for each test"""
    session = test_db_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def test_client(test_db_session):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


# Test data fixtures
@pytest.fixture
def sample_users():
    """Sample user data for testing"""
    return [
        {
            "email": "user1@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "first_name": "John",
            "last_name": "Doe"
        },
        {
            "email": "user2@example.com", 
            "password": "AnotherPass456!",
            "confirm_password": "AnotherPass456!",
            "first_name": "Jane",
            "last_name": "Smith"
        }
    ]


@pytest.fixture
def sample_cryptocurrencies():
    """Sample cryptocurrency data"""
    return [
        {
            "symbol": "BTC",
            "name": "Bitcoin",
            "coingecko_id": "bitcoin",
            "binance_symbol": "BTCUSDT"
        },
        {
            "symbol": "ETH",
            "name": "Ethereum",
            "coingecko_id": "ethereum",
            "binance_symbol": "ETHUSDT"
        },
        {
            "symbol": "ADA",
            "name": "Cardano", 
            "coingecko_id": "cardano",
            "binance_symbol": "ADAUSDT"
        }
    ]


# Test utilities
def create_auth_header(token: str) -> dict:
    """Create authorization header for authenticated requests"""
    return {"Authorization": f"Bearer {token}"}


def assert_valid_response(response, expected_status: int = 200):
    """Assert response is valid with expected status"""
    assert response.status_code == expected_status
    return response.json()


# Performance testing utilities
@pytest.fixture
def performance_thresholds():
    """Performance testing thresholds"""
    return {
        "api_response_time_ms": 500,
        "database_query_time_ms": 100,
        "concurrent_request_time_s": 5.0
    }