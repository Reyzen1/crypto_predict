# File: backend/tests/conftest.py
# Updated test configuration and fixtures for CryptoPredict MVP - Complete Stage D

import pytest
import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Generator, List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import application components
from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.models import User, Cryptocurrency, PriceData, Prediction
from app.repositories import (
    user_repository,
    cryptocurrency_repository,
    price_data_repository,
    prediction_repository
)
from app.schemas.user import UserRegister
from app.schemas.cryptocurrency import CryptocurrencyCreate
from app.schemas.price_data import PriceDataCreate
from app.ml.config.ml_config import ml_config
from app.core.security import get_password_hash


# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/tests/test.db"
TEST_DATABASE_URL = "sqlite:///./backend/tests/test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """Create test database and tables"""
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the database tables after tests
    Base.metadata.drop_all(bind=engine)
    
    # Clean up test database file
    try:
        os.remove("./tests/test.db")
    except FileNotFoundError:
        pass


@pytest.fixture
def db_session() -> Generator:
    """Create a database session for testing"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session) -> Generator:
    """Create a test client - Fixed version"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        test_client = TestClient(app, backend="asyncio")
        yield test_client
    except Exception:
        # Fallback
        test_client = TestClient(app)
        yield test_client
    finally:
        app.dependency_overrides.clear()
        

@pytest.fixture
def test_user(db_session) -> User:
    """Create a test user"""
    user_create = UserRegister(
        email="test@cryptopredict.com",
        password="TestPassword123"
    )
    
    user = user_repository.create(db_session, obj_in=user_create)
    return user


@pytest.fixture
def test_admin_user(db_session) -> User:
    """Create a test admin user"""
    user_create = UserRegister(
        email="admin@cryptopredict.com",
        password="adminpassword123"
    )
    
    user = user_repository.create(db_session, obj_in=user_create)
    # Set as admin (if you have admin functionality)
    user.is_admin = True
    db_session.commit()
    return user


@pytest.fixture
def test_crypto(db_session) -> Cryptocurrency:
    """Create a test cryptocurrency"""
    crypto_create = CryptocurrencyCreate(
        symbol="TESTBTC",
        name="Test Bitcoin",
        coingecko_id="test-bitcoin",
        is_active=True
    )
    
    crypto = cryptocurrency_repository.create(db_session, obj_in=crypto_create)
    return crypto


@pytest.fixture
def real_btc_crypto(db_session) -> Cryptocurrency:
    """Create or get real Bitcoin cryptocurrency for testing"""
    # Check if BTC already exists
    btc = cryptocurrency_repository.get_by_symbol(db_session, "BTC")
    if btc:
        return btc
    
    crypto_create = CryptocurrencyCreate(
        symbol="BTC",
        name="Bitcoin",
        coingecko_id="bitcoin",
        is_active=True
    )
    
    crypto = cryptocurrency_repository.create(db_session, obj_in=crypto_create)
    return crypto


@pytest.fixture
def sample_price_data(db_session, test_crypto) -> List[PriceData]:
    """Create sample price data for testing"""
    price_data_list = []
    base_time = datetime.now(timezone.utc) - timedelta(days=100)
    base_price = Decimal("45000.00")
    
    # Generate 100 days of price data with some realistic variation
    for i in range(100):
        # Add some realistic price variation (±5% daily change)
        import random
        price_change = Decimal(str(random.uniform(-0.05, 0.05)))
        current_price = base_price * (1 + price_change)
        base_price = current_price
        
        price_create = PriceDataCreate(
            crypto_id=test_crypto.id,
            price=current_price,
            volume=Decimal(str(random.uniform(1000000, 10000000))),
            market_cap=current_price * Decimal("19000000"),  # Approximate BTC supply
            timestamp=base_time + timedelta(days=i)
        )
        
        price_data = price_data_repository.create(db_session, obj_in=price_create)
        price_data_list.append(price_data)
    
    return price_data_list


@pytest.fixture
def extensive_price_data(db_session, test_crypto) -> List[PriceData]:
    """Create extensive price data for performance testing"""
    price_data_list = []
    base_time = datetime.now(timezone.utc) - timedelta(days=365)  # 1 year of data
    base_price = Decimal("30000.00")
    
    # Generate 365 days of hourly price data (more realistic for ML)
    for day in range(365):
        for hour in range(24):
            # More realistic price variation
            import random
            price_change = Decimal(str(random.uniform(-0.02, 0.02)))  # ±2% hourly
            current_price = base_price * (1 + price_change)
            base_price = current_price
            
            price_create = PriceDataCreate(
                crypto_id=test_crypto.id,
                price=current_price,
                volume=Decimal(str(random.uniform(500000, 5000000))),
                market_cap=current_price * Decimal("19000000"),
                timestamp=base_time + timedelta(days=day, hours=hour)
            )
            
            price_data = price_data_repository.create(db_session, obj_in=price_create)
            price_data_list.append(price_data)
    
    return price_data_list


@pytest.fixture
def sample_predictions(db_session, test_crypto) -> List[Prediction]:
    """Create sample predictions for testing"""
    from app.schemas.prediction import PredictionCreate
    
    predictions = []
    base_time = datetime.now(timezone.utc) - timedelta(days=30)
    
    for i in range(30):
        prediction_create = PredictionCreate(
            crypto_id=test_crypto.id,
            predicted_price=Decimal(f"{45000 + (i * 100)}"),
            confidence_score=Decimal("0.75"),
            model_name="test_model",
            model_version="1.0",
            timeframe="24h",
            prediction_timestamp=base_time + timedelta(days=i)
        )
        
        prediction = prediction_repository.create(db_session, obj_in=prediction_create)
        predictions.append(prediction)
    
    return predictions


@pytest.fixture
def mock_external_api():
    """Mock external API responses"""
    class MockExternalAPI:
        async def get_current_price(self, symbol: str) -> float:
            return 45000.00
        
        async def get_historical_data(self, symbol: str, days: int) -> List[Dict]:
            base_time = datetime.now(timezone.utc) - timedelta(days=days)
            data = []
            
            for i in range(days):
                data.append({
                    "timestamp": base_time + timedelta(days=i),
                    "price": 45000.00 + (i * 100),
                    "volume": 1000000.00,
                    "market_cap": 850000000000.00
                })
            
            return data
        
        async def get_market_data(self, symbol: str) -> Dict:
            return {
                "price": 45000.00,
                "volume_24h": 1000000.00,
                "market_cap": 850000000000.00,
                "price_change_24h": 2.5
            }
    
    return MockExternalAPI()


@pytest.fixture
def auth_headers(client, test_user) -> Dict[str, str]:
    """Get authentication headers for API requests"""
    login_response = client.post("/api/v1/auth/login", json={
        "email": test_user.email,
        "password": "TestPassword123"
    })
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    else:
        pytest.fail("Failed to authenticate test user")


@pytest.fixture
def admin_auth_headers(client, test_admin_user) -> Dict[str, str]:
    """Get admin authentication headers for API requests"""
    login_response = client.post("/api/v1/auth/login", json={
        "email": test_admin_user.email,
        "password": "adminpassword123"
    })
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    else:
        pytest.fail("Failed to authenticate admin user")


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data after each test"""
    yield
    
    # Clean up any test model files
    import glob
    test_model_pattern = os.path.join(ml_config.models_storage_path, "test*")
    for test_file in glob.glob(test_model_pattern):
        try:
            os.remove(test_file)
        except FileNotFoundError:
            pass
    
    # Clean up any temporary test files
    temp_patterns = [
        "./temp/test_*",
        "./tests/temp_*",
        "./test_*.tmp"
    ]
    
    for pattern in temp_patterns:
        for temp_file in glob.glob(pattern):
            try:
                os.remove(temp_file)
            except FileNotFoundError:
                pass


@pytest.fixture
def test_config():
    """Test configuration settings"""
    return {
        "crypto_symbol": "TESTBTC",
        "test_user_email": "test@cryptopredict.com",
        "test_user_password": "TestPassword123",
        "api_timeout": 30,
        "min_price_data_points": 100,
        "training_epochs": 2,  # Small for testing
        "prediction_timeframes": ["1h", "4h", "24h", "7d"],
        "performance_thresholds": {
            "prediction_response_time_ms": 5000,
            "training_time_minutes": 10,
            "memory_usage_mb": 500,
            "database_query_time_ms": 1000
        }
    }


# Test utilities
class TestDataGenerator:
    """Utility class for generating test data"""
    
    @staticmethod
    def generate_realistic_price_data(
        crypto_id: int,
        days: int = 30,
        base_price: float = 45000.0,
        volatility: float = 0.02
    ) -> List[PriceDataCreate]:
        """Generate realistic price data for testing"""
        import random
        
        price_data = []
        base_time = datetime.now(timezone.utc) - timedelta(days=days)
        current_price = Decimal(str(base_price))
        
        for i in range(days * 24):  # Hourly data
            # Random walk with volatility
            change = Decimal(str(random.gauss(0, volatility)))
            current_price = current_price * (1 + change)
            
            # Ensure price doesn't go negative or too extreme
            current_price = max(current_price, Decimal("1000"))
            current_price = min(current_price, Decimal("200000"))
            
            price_data.append(PriceDataCreate(
                crypto_id=crypto_id,
                price=current_price,
                volume=Decimal(str(random.uniform(100000, 5000000))),
                market_cap=current_price * Decimal("19000000"),
                timestamp=base_time + timedelta(hours=i)
            ))
        
        return price_data
    

# Test markers configuration
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "real_data: Tests using real data")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "ml: Machine learning tests")
    config.addinivalue_line("markers", "database: Database tests")


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add automatic markers"""
    for item in items:
        # Add markers based on test file names
        if "test_performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        if "test_real_" in item.nodeid:
            item.add_marker(pytest.mark.real_data)
        
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        if "test_api" in item.nodeid or "/endpoints/" in item.nodeid:
            item.add_marker(pytest.mark.api)
        
        if "ml_" in item.nodeid or "/ml/" in item.nodeid:
            item.add_marker(pytest.mark.ml)


# Cleanup functions
def cleanup_test_environment():
    """Clean up test environment"""
    # Clean up test database
    if os.path.exists("./tests/test.db"):
        os.remove("./tests/test.db")
    
    # Clean up test model files
    import glob
    for pattern in ["./models/test_*", "./temp/test_*"]:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
            except:
                pass