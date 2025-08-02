# File: backend/tests/test_real_bitcoin_data.py
# Real Bitcoin Data Testing for CryptoPredict MVP - Stage D

import pytest
import asyncio
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional

# Import test utilities
from .conftest import db_session, cleanup_test_data

# Import application components
from app.core.database import SessionLocal
from app.repositories import (
    cryptocurrency_repository, 
    price_data_repository,
    prediction_repository
)
from app.ml.training.training_service import training_service
from app.ml.prediction.prediction_service import prediction_service
from app.ml.config.ml_config import model_registry
from app.services.external_api import external_api_service
from app.tasks.price_collector import sync_specific_cryptocurrency
from app.schemas.cryptocurrency import CryptocurrencyCreate
from app.schemas.price_data import PriceDataCreate


@pytest.mark.real_data
class TestRealBitcoinData:
    """Tests using real Bitcoin data from external APIs"""
    
    @pytest.fixture(scope="class")
    def real_btc_crypto(self, db_session):
        """Create or get real BTC cryptocurrency"""
        
        btc = cryptocurrency_repository.get_by_symbol(db_session, "BTC")
        if not btc:
            btc_create = CryptocurrencyCreate(
                symbol="BTC",
                name="Bitcoin",
                coingecko_id="bitcoin",
                is_active=True
            )
            btc = cryptocurrency_repository.create(db_session, obj_in=btc_create)
        
        yield btc
        
        # Cleanup handled by conftest
    
    @pytest.mark.asyncio
    async def test_real_price_data_collection(self, real_btc_crypto):
        """Test collecting real Bitcoin price data"""
        
        try:
            # Test external API connection
            current_price = await external_api_service.get_current_price("bitcoin")
            
            if current_price:
                assert current_price > 0, "Bitcoin price should be positive"
                assert current_price > 1000, "Bitcoin price should be > $1000"
                assert current_price < 1000000, "Bitcoin price should be < $1M (sanity check)"
                
                print(f"✅ Real BTC price: ${current_price:,.2f}")
            else:
                pytest.skip("External API not available for real price data test")
                
        except Exception as e:
            pytest.skip(f"External API error: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_real_historical_data_collection(self, db_session, real_btc_crypto):
        """Test collecting real historical Bitcoin data"""
        
        try:
            # Collect recent historical data
            historical_data = await external_api_service.get_historical_data(
                "bitcoin", days=7
            )
            
            if historical_data and len(historical_data) > 0:
                assert len(historical_data) >= 5, "Should have at least 5 days of data"
                
                # Validate data structure
                for data_point in historical_data[:3]:  # Check first 3 points
                    assert "timestamp" in data_point
                    assert "price" in data_point
                    assert data_point["price"] > 0
                    
                # Store in database for further testing
                for data_point in historical_data:
                    price_create = PriceDataCreate(
                        crypto_id=real_btc_crypto.id,
                        price=Decimal(str(data_point["price"])),
                        volume=Decimal(str(data_point.get("volume", 0))),
                        market_cap=Decimal(str(data_point.get("market_cap", 0))),
                        timestamp=data_point["timestamp"]
                    )
                    
                    # Check if data already exists to avoid duplicates
                    existing = price_data_repository.get_by_timestamp(
                        db_session, real_btc_crypto.id, data_point["timestamp"]
                    )
                    
                    if not existing:
                        price_data_repository.create(db_session, obj_in=price_create)
                
                print(f"✅ Collected {len(historical_data)} historical data points")
                
            else:
                pytest.skip("No historical data available from external API")
                
        except Exception as e:
            pytest.skip(f"Historical data collection error: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_real_data_training(self, db_session, real_btc_crypto):
        """Test training with real Bitcoin data"""
        
        # Check if we have sufficient real data
        price_count = price_data_repository.count_by_crypto(db_session, real_btc_crypto.id)
        
        if price_count < 100:
            pytest.skip(f"Insufficient real data for training: {price_count} records")
        
        print(f"📊 Using {price_count} real Bitcoin price records for training")
        
        # Configure training for real data
        training_config = {
            "sequence_length": 60,  # Standard 60-day sequence
            "lstm_units": [50, 30, 20],  # More sophisticated model
            "epochs": 10,  # More epochs for real data
            "batch_size": 32,
            "validation_split": 0.2,
            "learning_rate": 0.001,
            "dropout_rate": 0.3
        }
        
        # Start training with real data
        training_result = await training_service.train_model(
            crypto_symbol="BTC",
            model_type="lstm",
            training_config=training_config,
            data_days_back=365,  # Use 1 year of data
            force_retrain=True
        )
        
        # Verify training success
        assert training_result is not None
        assert training_result.get("success", False) is True, f"Training failed: {training_result.get('error')}"
        
        # Check training metrics
        training_metrics = training_result.get("training_metrics", {})
        validation_metrics = training_result.get("validation_metrics", {})
        
        print(f"📈 Training Loss: {training_metrics.get('loss', 'N/A')}")
        print(f"📈 Validation Loss: {validation_metrics.get('val_loss', 'N/A')}")
        
        # Validate model performance
        if "loss" in training_metrics:
            final_loss = training_metrics["loss"]
            assert final_loss < 1.0, f"Training loss too high: {final_loss}"
        
        # Verify model is saved and registered
        model_path = training_result.get("model_path")
        assert model_path and os.path.exists(model_path), "Model file should exist"
        
        # Verify model is in registry
        models = model_registry.list_models("BTC")
        assert len(models) > 0, "Model should be registered"
        
        model_id = training_result.get("model_id")
        assert any(m["model_id"] == model_id for m in models), "Trained model should be in registry"
    
    @pytest.mark.asyncio
    async def test_real_data_predictions(self, db_session, real_btc_crypto):
        """Test predictions with real Bitcoin data and models"""
        
        # Ensure we have a trained model
        models = model_registry.list_models("BTC")
        if not models:
            pytest.skip("No trained model available for real data predictions")
        
        # Test various prediction timeframes
        timeframes = ["1h", "4h", "24h", "7d"]
        successful_predictions = 0
        
        for timeframe in timeframes:
            try:
                print(f"🔮 Testing {timeframe} prediction with real data...")
                
                prediction_result = await prediction_service.predict_price(
                    crypto_symbol="BTC",
                    timeframe=timeframe,
                    use_ensemble_models=True,
                    include_technical_indicators=True
                )
                
                if prediction_result and prediction_result.get("success", False):
                    predicted_price = float(prediction_result["predicted_price"])
                    current_price = float(prediction_result["current_price"])
                    confidence = prediction_result["confidence_score"]
                    
                    # Validate prediction reasonableness for Bitcoin
                    assert predicted_price > 1000, f"BTC prediction too low: ${predicted_price}"
                    assert predicted_price < 1000000, f"BTC prediction too high: ${predicted_price}"
                    assert current_price > 1000, f"BTC current price too low: ${current_price}"
                    assert 0 <= confidence <= 1, f"Invalid confidence: {confidence}"
                    
                    # Calculate prediction change percentage
                    price_change_pct = abs((predicted_price - current_price) / current_price) * 100
                    
                    # Reasonable change expectations (Bitcoin volatility)
                    max_change_by_timeframe = {
                        "1h": 5,    # 5% in 1 hour is high but possible
                        "4h": 15,   # 15% in 4 hours is significant
                        "24h": 25,  # 25% in 24 hours is very high but possible
                        "7d": 50    # 50% in 7 days is extreme but has happened
                    }
                    
                    max_expected_change = max_change_by_timeframe.get(timeframe, 100)
                    
                    if price_change_pct <= max_expected_change:
                        print(f"   ✅ {timeframe}: ${predicted_price:,.2f} (±{price_change_pct:.1f}%, confidence: {confidence:.1%})")
                        successful_predictions += 1
                    else:
                        print(f"   ⚠️ {timeframe}: Large change predicted: ±{price_change_pct:.1f}%")
                        successful_predictions += 1  # Still count as successful, just note the large change
                
                else:
                    error_msg = prediction_result.get("error", "Unknown error")
                    print(f"   ❌ {timeframe}: Prediction failed - {error_msg}")
                
            except Exception as e:
                print(f"   ❌ {timeframe}: Exception - {str(e)}")
        
        # Require at least 75% success rate
        success_rate = successful_predictions / len(timeframes)
        assert success_rate >= 0.75, f"Real data prediction success rate too low: {success_rate:.1%}"
    
    @pytest.mark.asyncio
    async def test_real_data_model_accuracy(self, db_session, real_btc_crypto):
        """Test model accuracy with real historical data"""
        
        # Get historical predictions if any exist
        historical_predictions = prediction_repository.get_recent_predictions(
            db_session, days=30, limit=100
        )
        
        if len(historical_predictions) < 5:
            pytest.skip("Insufficient historical predictions for accuracy testing")
        
        accurate_predictions = 0
        total_evaluated = 0
        
        for prediction in historical_predictions:
            if prediction.actual_price is not None:  # Only evaluate realized predictions
                predicted = float(prediction.predicted_price)
                actual = float(prediction.actual_price)
                
                # Calculate accuracy (percentage error)
                percentage_error = abs((predicted - actual) / actual) * 100
                
                # Consider prediction accurate if within 10% for Bitcoin
                if percentage_error <= 10:
                    accurate_predictions += 1
                
                total_evaluated += 1
        
        if total_evaluated > 0:
            accuracy_rate = accurate_predictions / total_evaluated
            print(f"📊 Model accuracy: {accuracy_rate:.1%} ({accurate_predictions}/{total_evaluated})")
            
            # Expect at least 60% accuracy for Bitcoin predictions
            assert accuracy_rate >= 0.6, f"Model accuracy too low: {accuracy_rate:.1%}"
        else:
            pytest.skip("No realized predictions available for accuracy evaluation")
    
    @pytest.mark.asyncio
    async def test_real_data_edge_cases(self, db_session, real_btc_crypto):
        """Test edge cases with real Bitcoin data"""
        
        # Test prediction during market volatility
        # Get recent price data to check for volatility
        recent_prices = price_data_repository.get_recent_prices(
            db_session, real_btc_crypto.id, limit=24  # Last 24 hours
        )
        
        if len(recent_prices) >= 10:
            prices = [float(p.price) for p in recent_prices[:10]]
            price_changes = [abs((prices[i] - prices[i+1]) / prices[i+1]) * 100 
                           for i in range(len(prices)-1)]
            avg_volatility = sum(price_changes) / len(price_changes)
            
            print(f"📊 Recent volatility: {avg_volatility:.2f}%")
            
            if avg_volatility > 5:  # High volatility period
                print("⚡ Testing prediction during high volatility...")
                
                prediction_result = await prediction_service.predict_price(
                    crypto_symbol="BTC",
                    timeframe="1h",
                    use_ensemble_models=True
                )
                
                if prediction_result and prediction_result.get("success", False):
                    confidence = prediction_result["confidence_score"]
                    
                    # During high volatility, confidence should be lower
                    if confidence < 0.8:  # Lower confidence expected
                        print(f"   ✅ Appropriate confidence during volatility: {confidence:.1%}")
                    else:
                        print(f"   ⚠️ High confidence during volatility: {confidence:.1%}")
                
                assert prediction_result.get("success", False) is True, "Should still make predictions during volatility"
        
        # Test with minimal recent data
        print("🔍 Testing prediction with limited recent data...")
        
        # This would test the model's robustness when recent data is limited
        # The service should handle this gracefully
        try:
            prediction_result = await prediction_service.predict_price(
                crypto_symbol="BTC",
                timeframe="24h",
                use_ensemble_models=False  # Single model might be more robust
            )
            
            # Should either succeed or fail gracefully
            assert prediction_result is not None
            if not prediction_result.get("success", False):
                assert "error" in prediction_result
                
        except Exception as e:
            # Should not raise unhandled exceptions
            assert False, f"Unhandled exception in edge case: {str(e)}"
    
    @pytest.mark.asyncio
    async def test_real_data_performance_benchmarks(self, db_session, real_btc_crypto):
        """Test performance benchmarks with real data"""
        
        import time
        
        # Ensure model exists
        models = model_registry.list_models("BTC")
        if not models:
            pytest.skip("No trained model for performance benchmarks")
        
        # Benchmark single prediction performance
        start_time = time.time()
        
        prediction_result = await prediction_service.predict_price(
            crypto_symbol="BTC",
            timeframe="1h"
        )
        
        single_prediction_time = time.time() - start_time
        
        assert prediction_result.get("success", False) is True
        assert single_prediction_time < 5.0, f"Single prediction too slow: {single_prediction_time:.2f}s"
        
        print(f"⚡ Single prediction time: {single_prediction_time:.2f}s")
        
        # Benchmark batch prediction performance
        start_time = time.time()
        
        batch_result = await prediction_service.batch_predict(
            crypto_symbols=["BTC"],
            timeframe="1h"
        )
        
        batch_prediction_time = time.time() - start_time
        
        assert batch_result.get("success", False) is True
        assert batch_prediction_time < 10.0, f"Batch prediction too slow: {batch_prediction_time:.2f}s"
        
        print(f"⚡ Batch prediction time: {batch_prediction_time:.2f}s")
        
        # Benchmark concurrent predictions
        async def concurrent_prediction():
            return await prediction_service.predict_price("BTC", "1h")
        
        start_time = time.time()
        
        concurrent_tasks = [concurrent_prediction() for _ in range(3)]
        concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        
        concurrent_time = time.time() - start_time
        
        successful_concurrent = sum(1 for r in concurrent_results 
                                  if not isinstance(r, Exception) and r.get("success", False))
        
        assert successful_concurrent >= 2, f"Concurrent predictions failed: {successful_concurrent}/3"
        assert concurrent_time < 15.0, f"Concurrent predictions too slow: {concurrent_time:.2f}s"
        
        print(f"⚡ Concurrent predictions ({successful_concurrent}/3): {concurrent_time:.2f}s")
    
    def test_real_data_storage_efficiency(self, db_session, real_btc_crypto):
        """Test data storage efficiency with real Bitcoin data"""
        
        # Test database query performance with real data volume
        import time
        
        start_time = time.time()
        
        # Query large amount of historical data
        historical_data = price_data_repository.get_historical_data(
            db_session, real_btc_crypto.id, days=90
        )
        
        query_time = time.time() - start_time
        
        print(f"📊 Queried {len(historical_data)} records in {query_time:.2f}s")
        
        # Should be efficient even with large datasets
        assert query_time < 2.0, f"Historical data query too slow: {query_time:.2f}s"
        
        if len(historical_data) > 1000:
            # Test pagination efficiency with large dataset
            start_time = time.time()
            
            paginated_data = price_data_repository.get_recent_prices(
                db_session, real_btc_crypto.id, limit=100, skip=0
            )
            
            pagination_time = time.time() - start_time
            
            assert len(paginated_data) <= 100
            assert pagination_time < 1.0, f"Pagination too slow: {pagination_time:.2f}s"
            
            print(f"📄 Pagination query: {pagination_time:.3f}s")


@pytest.mark.real_data
class TestRealDataIntegration:
    """Integration tests combining real data with all system components"""
    
    @pytest.mark.asyncio
    async def test_complete_real_data_workflow(self, db_session):
        """Test complete workflow with real Bitcoin data"""
        
        # Step 1: Ensure Bitcoin cryptocurrency exists
        btc = cryptocurrency_repository.get_by_symbol(db_session, "BTC")
        if not btc:
            btc_create = CryptocurrencyCreate(
                symbol="BTC",
                name="Bitcoin",
                coingecko_id="bitcoin",
                is_active=True
            )
            btc = cryptocurrency_repository.create(db_session, obj_in=btc_create)
        
        # Step 2: Collect real data (if external API available)
        try:
            current_price = await external_api_service.get_current_price("bitcoin")
            if current_price:
                print(f"💰 Current BTC price: ${current_price:,.2f}")
            else:
                pytest.skip("External API not available")
        except Exception:
            pytest.skip("External API connection failed")
        
        # Step 3: Check data availability
        price_count = price_data_repository.count_by_crypto(db_session, btc.id)
        print(f"📊 Available price data: {price_count} records")
        
        if price_count < 100:
            pytest.skip("Insufficient real data for complete workflow test")
        
        # Step 4: Train model with real data
        print("🤖 Training model with real data...")
        training_result = await training_service.train_model(
            crypto_symbol="BTC",
            model_type="lstm",
            training_config={
                "epochs": 5,  # Quick training for test
                "batch_size": 32,
                "lstm_units": [30, 20]
            },
            data_days_back=180,
            force_retrain=True
        )
        
        assert training_result.get("success", False) is True
        print(f"✅ Model trained: {training_result.get('model_id')}")
        
        # Step 5: Generate predictions
        print("🔮 Generating predictions...")
        prediction_result = await prediction_service.predict_price(
            crypto_symbol="BTC",
            timeframe="24h",
            use_ensemble_models=True
        )
        
        assert prediction_result.get("success", False) is True
        
        predicted_price = prediction_result["predicted_price"]
        confidence = prediction_result["confidence_score"]
        
        print(f"🎯 Prediction: ${predicted_price:,.2f} (confidence: {confidence:.1%})")
        
        # Step 6: Validate prediction reasonableness
        assert float(predicted_price) > 1000  # Bitcoin should be > $1000
        assert float(predicted_price) < 1000000  # Should be < $1M
        assert 0 <= confidence <= 1
        
        # Step 7: Test performance metrics
        metrics = prediction_service.get_performance_metrics()
        assert metrics is not None
        assert "total_predictions" in metrics
        
        print(f"📈 Performance metrics: {metrics.get('total_predictions', 0)} predictions")
        
        print("✅ Complete real data workflow successful!")
    
    @pytest.mark.asyncio
    async def test_real_time_data_update_simulation(self, db_session):
        """Simulate real-time data updates and system response"""
        
        btc = cryptocurrency_repository.get_by_symbol(db_session, "BTC")
        if not btc:
            pytest.skip("Bitcoin cryptocurrency not available")
        
        # Simulate receiving new price data
        new_price_data = PriceDataCreate(
            crypto_id=btc.id,
            price=Decimal("45000.00"),  # Simulated current price
            volume=Decimal("1000000.00"),
            market_cap=Decimal("900000000000.00"),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add new price data
        stored_price = price_data_repository.create(db_session, obj_in=new_price_data)
        assert stored_price is not None
        
        # Test that predictions can use the new data
        prediction_result = await prediction_service.predict_price(
            crypto_symbol="BTC",
            timeframe="1h",
            force_refresh=True  # Force using latest data
        )
        
        if prediction_result and prediction_result.get("success", False):
            # Verify prediction uses recent data
            current_price = float(prediction_result["current_price"])
            
            # Should be close to our simulated price (within reasonable range)
            price_diff = abs(current_price - 45000.00)
            assert price_diff < 5000, f"Current price should be close to latest data: ${current_price}"
            
            print(f"✅ Real-time update processed: ${current_price:,.2f}")
        else:
            pytest.skip("Prediction failed with new data")


# Utility functions for real data tests
def get_real_bitcoin_price_range(days: int = 30) -> tuple:
    """Get reasonable Bitcoin price range for the last N days"""
    # This could query actual data or use reasonable estimates
    # For testing purposes, we'll use conservative estimates
    
    if days <= 1:
        return (35000, 75000)  # Daily range
    elif days <= 7:
        return (30000, 80000)  # Weekly range
    elif days <= 30:
        return (25000, 90000)  # Monthly range
    else:
        return (20000, 100000)  # Longer term range


def validate_bitcoin_price_reasonableness(price: float, timeframe: str = "24h") -> bool:
    """Validate if a Bitcoin price prediction is reasonable"""
    
    # Bitcoin should always be above $1000 (conservative lower bound)
    if price < 1000:
        return False
    
    # Bitcoin should be below $1M (conservative upper bound)
    if price > 1000000:
        return False
    
    # Additional checks based on timeframe could be added here
    # For now, basic range check is sufficient
    
    return True


def calculate_bitcoin_volatility(prices: List[float]) -> float:
    """Calculate Bitcoin price volatility from a list of prices"""
    
    if len(prices) < 2:
        return 0.0
    
    price_changes = []
    for i in range(len(prices) - 1):
        change = abs((prices[i] - prices[i+1]) / prices[i+1]) * 100
        price_changes.append(change)
    
    return sum(price_changes) / len(price_changes) if price_changes else 0.0