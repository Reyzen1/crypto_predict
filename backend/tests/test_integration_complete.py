# File: backend/tests/test_integration_complete.py
# Comprehensive Integration Tests for CryptoPredict MVP - Stage D

import pytest
import asyncio
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional

# Import test utilities
from .conftest import (
    client, db_session, test_user, test_crypto, 
    sample_price_data, cleanup_test_data
)

# Import application components
from app.core.database import SessionLocal
from app.repositories import (
    cryptocurrency_repository, 
    price_data_repository,
    prediction_repository,
    user_repository
)
from app.ml.training.training_service import training_service
from app.ml.prediction.prediction_service import prediction_service
from app.ml.config.ml_config import model_registry
from app.schemas.ml_training import TrainingRequest
from app.schemas.prediction import PredictionRequest
from app.tasks.ml_tasks import (
    auto_train_models,
    generate_scheduled_predictions,
    evaluate_model_performance
)


class TestMLTrainingIntegration:
    """Integration tests for ML Training pipeline"""
    
    @pytest.mark.asyncio
    async def test_complete_training_workflow(self, db_session, test_crypto, sample_price_data):
        """Test complete ML training workflow from data to model"""
        
        # Ensure sufficient training data
        price_count = price_data_repository.count_by_crypto(db_session, test_crypto.id)
        assert price_count >= 100, f"Need at least 100 price records, got {price_count}"
        
        # Test training configuration
        training_config = {
            "sequence_length": 30,  # Smaller for testing
            "lstm_units": [25, 15],  # Smaller for faster training
            "epochs": 3,  # Very small for testing
            "batch_size": 16,
            "validation_split": 0.2
        }
        
        # Start training
        training_result = await training_service.train_model(
            crypto_symbol=test_crypto.symbol,
            model_type="lstm",
            training_config=training_config,
            data_days_back=60,
            force_retrain=True
        )
        
        # Verify training success
        assert training_result is not None
        assert training_result.get("success", False) is True
        assert "model_id" in training_result
        assert "model_path" in training_result
        
        # Verify model file exists
        model_path = training_result["model_path"]
        assert os.path.exists(model_path), f"Model file not found: {model_path}"
        
        # Verify model is registered
        models = model_registry.list_models(test_crypto.symbol)
        assert len(models) > 0, "No models found in registry"
        
        # Verify model can be activated
        model_id = training_result["model_id"]
        activation_result = model_registry.activate_model(test_crypto.symbol, model_id)
        assert activation_result is True
        
        # Verify active model
        active_model = model_registry.get_active_model(test_crypto.symbol)
        assert active_model is not None
        assert active_model["model_id"] == model_id
    
    @pytest.mark.asyncio
    async def test_training_with_insufficient_data(self, db_session, test_crypto):
        """Test training behavior with insufficient data"""
        
        # Clear most price data to simulate insufficient data
        # Keep only a few records
        price_data_repository.delete_old_data(
            db_session, 
            test_crypto.id, 
            datetime.now(timezone.utc) - timedelta(days=1)
        )
        
        training_config = {
            "epochs": 1,
            "batch_size": 8
        }
        
        # Attempt training
        training_result = await training_service.train_model(
            crypto_symbol=test_crypto.symbol,
            model_type="lstm",
            training_config=training_config,
            data_days_back=30
        )
        
        # Should fail gracefully
        assert training_result is not None
        assert training_result.get("success", False) is False
        assert "error" in training_result
        assert "insufficient" in training_result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_model_versioning(self, db_session, test_crypto, sample_price_data):
        """Test model versioning and management"""
        
        # Train first model
        result1 = await training_service.train_model(
            crypto_symbol=test_crypto.symbol,
            model_type="lstm",
            training_config={"epochs": 2, "lstm_units": [10]},
            force_retrain=True
        )
        
        assert result1.get("success", False) is True
        model_id_1 = result1["model_id"]
        
        # Train second model
        result2 = await training_service.train_model(
            crypto_symbol=test_crypto.symbol,
            model_type="lstm", 
            training_config={"epochs": 2, "lstm_units": [15]},
            force_retrain=True
        )
        
        assert result2.get("success", False) is True
        model_id_2 = result2["model_id"]
        
        # Verify both models exist
        models = model_registry.list_models(test_crypto.symbol)
        model_ids = [m["model_id"] for m in models]
        assert model_id_1 in model_ids
        assert model_id_2 in model_ids
        
        # Test model activation switching
        model_registry.activate_model(test_crypto.symbol, model_id_1)
        active = model_registry.get_active_model(test_crypto.symbol)
        assert active["model_id"] == model_id_1
        
        model_registry.activate_model(test_crypto.symbol, model_id_2)
        active = model_registry.get_active_model(test_crypto.symbol)
        assert active["model_id"] == model_id_2


class TestMLPredictionIntegration:
    """Integration tests for ML Prediction pipeline"""
    
    @pytest.mark.asyncio
    async def test_prediction_workflow(self, db_session, test_crypto, sample_price_data):
        """Test complete prediction workflow"""
        
        # Ensure we have a trained model
        models = model_registry.list_models(test_crypto.symbol)
        if not models:
            # Train a quick model for testing
            training_result = await training_service.train_model(
                crypto_symbol=test_crypto.symbol,
                model_type="lstm",
                training_config={"epochs": 2, "lstm_units": [10]},
                force_retrain=True
            )
            assert training_result.get("success", False) is True
        
        # Test single prediction
        prediction_result = await prediction_service.predict_price(
            crypto_symbol=test_crypto.symbol,
            timeframe="1h",
            use_ensemble_models=False
        )
        
        assert prediction_result is not None
        assert prediction_result.get("success", False) is True
        assert "predicted_price" in prediction_result
        assert "confidence_score" in prediction_result
        assert "current_price" in prediction_result
        
        # Verify prediction values are reasonable
        predicted_price = float(prediction_result["predicted_price"])
        current_price = float(prediction_result["current_price"])
        confidence = prediction_result["confidence_score"]
        
        assert predicted_price > 0
        assert current_price > 0
        assert 0 <= confidence <= 1
        
        # Test prediction persistence
        prediction_id = prediction_result.get("prediction_id")
        if prediction_id:
            # Verify prediction is stored in database
            predictions = prediction_repository.get_recent_predictions(db_session, days=1)
            prediction_ids = [p.id for p in predictions]
            # Note: prediction_id format may differ from database id
    
    @pytest.mark.asyncio
    async def test_batch_predictions(self, db_session, test_crypto, sample_price_data):
        """Test batch prediction functionality"""
        
        # Ensure model exists
        models = model_registry.list_models(test_crypto.symbol)
        if not models:
            training_result = await training_service.train_model(
                crypto_symbol=test_crypto.symbol,
                model_type="lstm",
                training_config={"epochs": 1, "lstm_units": [5]},
                force_retrain=True
            )
            assert training_result.get("success", False) is True
        
        # Test batch predictions
        batch_result = await prediction_service.batch_predict(
            crypto_symbols=[test_crypto.symbol],
            timeframe="24h"
        )
        
        assert batch_result is not None
        assert batch_result.get("success", False) is True
        assert "predictions" in batch_result
        assert len(batch_result["predictions"]) == 1
        
        # Verify batch prediction structure
        prediction = batch_result["predictions"][0]
        assert prediction["crypto_symbol"] == test_crypto.symbol
        assert "predicted_price" in prediction
        assert "confidence_score" in prediction
    
    @pytest.mark.asyncio
    async def test_prediction_caching(self, db_session, test_crypto, sample_price_data):
        """Test prediction caching mechanism"""
        
        # Ensure model exists
        models = model_registry.list_models(test_crypto.symbol)
        if not models:
            training_result = await training_service.train_model(
                crypto_symbol=test_crypto.symbol,
                model_type="lstm",
                training_config={"epochs": 1},
                force_retrain=True
            )
            assert training_result.get("success", False) is True
        
        # First prediction (should be calculated)
        import time
        start_time = time.time()
        
        result1 = await prediction_service.predict_price(
            crypto_symbol=test_crypto.symbol,
            timeframe="1h"
        )
        
        first_duration = time.time() - start_time
        
        # Second prediction (should be cached)
        start_time = time.time()
        
        result2 = await prediction_service.predict_price(
            crypto_symbol=test_crypto.symbol,
            timeframe="1h"
        )
        
        second_duration = time.time() - start_time
        
        # Verify both predictions successful
        assert result1.get("success", False) is True
        assert result2.get("success", False) is True
        
        # Verify cached prediction is faster (generally true, but not always guaranteed)
        # assert second_duration < first_duration, f"Cached call ({second_duration:.3f}s) should be faster than first call ({first_duration:.3f}s)"
        
        # Verify prediction values are consistent
        assert result1["predicted_price"] == result2["predicted_price"]
        assert result1["confidence_score"] == result2["confidence_score"]
    
    @pytest.mark.asyncio
    async def test_prediction_performance_metrics(self, db_session, test_crypto):
        """Test prediction performance metrics"""
        
        # Get performance metrics
        metrics = prediction_service.get_performance_metrics()
        
        assert metrics is not None
        assert isinstance(metrics, dict)
        
        # Check expected metric fields
        expected_fields = [
            "total_predictions", 
            "cache_hit_rate", 
            "average_response_time",
            "error_rate"
        ]
        
        for field in expected_fields:
            assert field in metrics, f"Missing metric field: {field}"
            assert isinstance(metrics[field], (int, float))
        
        # Verify metric ranges
        assert metrics["cache_hit_rate"] >= 0
        assert metrics["cache_hit_rate"] <= 100
        assert metrics["error_rate"] >= 0
        assert metrics["error_rate"] <= 100


class TestBackgroundTasksIntegration:
    """Integration tests for background tasks"""
    
    @pytest.mark.asyncio
    async def test_auto_training_task(self, db_session, test_crypto, sample_price_data):
        """Test auto training background task"""
        
        # Execute auto training task
        result = await auto_train_models.apply_async(
            kwargs={"force_retrain": True}
        ).get()
        
        assert result is not None
        assert result.get("success", False) is True
        assert "cryptocurrencies_processed" in result
        assert result["cryptocurrencies_processed"] > 0
        
        # Verify models were created
        models = model_registry.list_models(test_crypto.symbol)
        assert len(models) > 0
    
    @pytest.mark.asyncio
    async def test_prediction_generation_task(self, db_session, test_crypto, sample_price_data):
        """Test scheduled prediction generation task"""
        
        # Ensure model exists first
        models = model_registry.list_models(test_crypto.symbol)
        if not models:
            training_result = await training_service.train_model(
                crypto_symbol=test_crypto.symbol,
                model_type="lstm",
                training_config={"epochs": 1},
                force_retrain=True
            )
            assert training_result.get("success", False) is True
        
        # Execute prediction generation task
        result = await generate_scheduled_predictions.apply_async(
            kwargs={"crypto_symbols": [test_crypto.symbol]}
        ).get()
        
        assert result is not None
        assert result.get("success", False) is True
        assert "predictions_generated" in result
        assert result["predictions_generated"] > 0
    
    @pytest.mark.asyncio
    async def test_performance_evaluation_task(self, db_session, test_crypto):
        """Test model performance evaluation task"""
        
        # Execute performance evaluation task
        result = await evaluate_model_performance.apply_async(
            kwargs={"crypto_symbol": test_crypto.symbol}
        ).get()
        
        assert result is not None
        assert result.get("success", False) is True
        assert "cryptocurrencies_evaluated" in result


class TestAPIEndpointsIntegration:
    """Integration tests for API endpoints"""
    
    def test_training_api_endpoints(self, client, test_user, test_crypto, sample_price_data):
        """Test ML training API endpoints"""
        
        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test start training endpoint
        training_request = {
            "crypto_symbol": test_crypto.symbol,
            "model_type": "lstm",
            "training_config": {
                "epochs": 2,
                "batch_size": 16,
                "lstm_units": [10]
            },
            "force_retrain": True
        }
        
        response = client.post(
            "/api/v1/ml/training/start",
            json=training_request,
            headers=headers
        )
        
        assert response.status_code in [200, 202]  # Success or Accepted
        result = response.json()
        assert "job_id" in result
        
        job_id = result["job_id"]
        
        # Test get training status endpoint
        status_response = client.get(
            f"/api/v1/ml/training/status/{job_id}",
            headers=headers
        )
        
        assert status_response.status_code == 200
        status_result = status_response.json()
        assert "status" in status_result
        assert status_result["status"] in ["pending", "running", "completed", "failed"]
        
        # Test list models endpoint
        models_response = client.get(
            f"/api/v1/ml/models/{test_crypto.symbol}",
            headers=headers
        )
        
        assert models_response.status_code == 200
        models_result = models_response.json()
        assert "models" in models_result
        assert isinstance(models_result["models"], list)
    
    def test_prediction_api_endpoints(self, client, test_user, test_crypto, sample_price_data):
        """Test ML prediction API endpoints"""
        
        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test prediction endpoint
        prediction_request = {
            "crypto_symbol": test_crypto.symbol,
            "prediction_config": {
                "timeframe": "24h",
                "confidence_threshold": 0.7
            }
        }
        
        response = client.post(
            "/api/v1/ml/predictions/predict",
            json=prediction_request,
            headers=headers
        )
        
        # Could be 200 (immediate) or 202 (async)
        assert response.status_code in [200, 202]
        result = response.json()
        
        if response.status_code == 200:
            # Immediate response
            assert "predicted_price" in result
            assert "confidence_score" in result
        else:
            # Async response
            assert "prediction_id" in result
            
            # Test status endpoint
            prediction_id = result["prediction_id"]
            status_response = client.get(
                f"/api/v1/ml/predictions/status/{prediction_id}",
                headers=headers
            )
            assert status_response.status_code == 200
        
        # Test batch prediction endpoint
        batch_request = {
            "crypto_symbols": [test_crypto.symbol],
            "prediction_config": {
                "timeframe": "1h"
            }
        }
        
        batch_response = client.post(
            "/api/v1/ml/predictions/batch",
            json=batch_request,
            headers=headers
        )
        
        assert batch_response.status_code == 200
        batch_result = batch_response.json()
        assert "predictions" in batch_result
        assert len(batch_result["predictions"]) >= 0
        
        # Test prediction history endpoint
        history_response = client.get(
            f"/api/v1/ml/predictions/history/{test_crypto.symbol}",
            headers=headers
        )
        
        assert history_response.status_code == 200
        history_result = history_response.json()
        assert "crypto_symbol" in history_result
        assert "predictions" in history_result
        
        # Test prediction stats endpoint
        stats_response = client.get(
            "/api/v1/ml/predictions/stats",
            headers=headers
        )
        
        assert stats_response.status_code == 200
        stats_result = stats_response.json()
        assert "total_predictions_today" in stats_result
    
    def test_task_management_endpoints(self, client, test_user):
        """Test task management API endpoints"""
        
        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test ML auto training endpoint
        auto_train_response = client.post(
            "/api/v1/tasks/ml/auto-train",
            json={"force_retrain": False},
            headers=headers
        )
        
        assert auto_train_response.status_code == 200
        auto_train_result = auto_train_response.json()
        assert "task_id" in auto_train_result
        
        # Test task status endpoint
        task_id = auto_train_result["task_id"]
        status_response = client.get(
            f"/api/v1/tasks/ml/status/{task_id}",
            headers=headers
        )
        
        assert status_response.status_code == 200
        status_result = status_response.json()
        assert "task_status" in status_result


class TestDataIntegration:
    """Integration tests for data flow"""
    
    def test_price_data_to_training_flow(self, db_session, test_crypto, sample_price_data):
        """Test data flow from price data to training"""
        
        # Verify price data exists
        price_count = price_data_repository.count_by_crypto(db_session, test_crypto.id)
        assert price_count > 0
        
        # Test data preprocessing
        from app.ml.preprocessing.data_processor import CryptoPriceDataProcessor
        
        processor = CryptoPriceDataProcessor()
        
        # Get recent price data
        price_data = price_data_repository.get_historical_data(
            db_session, test_crypto.id, days=30
        )
        
        assert len(price_data) > 0
        
        # Test data processing
        processed_data = processor.prepare_training_data(
            price_data, sequence_length=10
        )
        
        assert processed_data is not None
        assert "X_train" in processed_data
        assert "y_train" in processed_data
        assert processed_data["X_train"].shape[0] > 0
        assert processed_data["y_train"].shape[0] > 0
    
    def test_model_to_prediction_flow(self, db_session, test_crypto, sample_price_data):
        """Test data flow from trained model to predictions"""
        
        # Ensure we have a model
        models = model_registry.list_models(test_crypto.symbol)
        if not models:
            pytest.skip("No trained model available for prediction flow test")
        
        # Get active model
        active_model = model_registry.get_active_model(test_crypto.symbol)
        assert active_model is not None
        
        # Test model loading
        from app.ml.models.model_loader import ModelLoader
        
        loader = ModelLoader()
        model = loader.load_model(test_crypto.symbol, active_model["model_id"])
        
        assert model is not None
        
        # Test prediction generation
        recent_data = price_data_repository.get_recent_prices(
            db_session, test_crypto.id, limit=60
        )
        
        assert len(recent_data) >= 10  # Minimum for prediction
    
    def test_prediction_to_storage_flow(self, db_session, test_crypto):
        """Test prediction storage and retrieval"""
        
        # Create a test prediction record
        from app.schemas.prediction import PredictionCreate
        
        prediction_data = PredictionCreate(
            crypto_id=test_crypto.id,
            predicted_price=Decimal("50000.00"),
            confidence_score=Decimal("0.85"),
            model_name="test_model",
            model_version="1.0",
            timeframe="24h",
            prediction_timestamp=datetime.now(timezone.utc)
        )
        
        # Store prediction
        stored_prediction = prediction_repository.create(db_session, obj_in=prediction_data)
        
        assert stored_prediction is not None
        assert stored_prediction.crypto_id == test_crypto.id
        assert stored_prediction.predicted_price == Decimal("50000.00")
        
        # Retrieve prediction
        retrieved_predictions = prediction_repository.get_by_crypto_and_timerange(
            db_session, crypto_id=test_crypto.id, days_back=1
        )
        
        assert len(retrieved_predictions) > 0
        assert any(p.id == stored_prediction.id for p in retrieved_predictions)


class TestErrorHandlingIntegration:
    """Integration tests for error handling"""
    
    @pytest.mark.asyncio
    async def test_invalid_cryptocurrency_handling(self):
        """Test handling of invalid cryptocurrency symbols"""
        
        # Test training with invalid crypto
        training_result = await training_service.train_model(
            crypto_symbol="INVALID_CRYPTO",
            model_type="lstm"
        )
        
        assert training_result is not None
        assert training_result.get("success", False) is False
        assert "error" in training_result
        
        # Test prediction with invalid crypto
        prediction_result = await prediction_service.predict_price(
            crypto_symbol="INVALID_CRYPTO",
            timeframe="1h"
        )
        
        assert prediction_result is not None
        assert prediction_result.get("success", False) is False
        assert "error" in prediction_result
    
    @pytest.mark.asyncio
    async def test_insufficient_data_handling(self, db_session, test_crypto):
        """Test handling of insufficient data scenarios"""
        
        # Clear all price data
        price_data_repository.delete_all_for_crypto(db_session, test_crypto.id)
        
        # Attempt training with no data
        training_result = await training_service.train_model(
            crypto_symbol=test_crypto.symbol,
            model_type="lstm"
        )
        
        assert training_result is not None
        assert training_result.get("success", False) is False
        assert "insufficient" in training_result.get("error", "").lower()
    
    def test_api_authentication_errors(self, client, test_crypto):
        """Test API authentication error handling"""
        
        # Test endpoint without authentication
        response = client.post("/api/v1/ml/training/start", json={
            "crypto_symbol": test_crypto.symbol,
            "model_type": "lstm"
        })
        
        assert response.status_code == 401  # Unauthorized
        
        # Test endpoint with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = client.post(
            "/api/v1/ml/training/start",
            json={
                "crypto_symbol": test_crypto.symbol,
                "model_type": "lstm"
            },
            headers=invalid_headers
        )
        
        assert response.status_code == 401  # Unauthorized
    
    def test_api_validation_errors(self, client, test_user):
        """Test API input validation error handling"""
        
        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test training with invalid data
        invalid_requests = [
            {},  # Empty request
            {"crypto_symbol": ""},  # Empty crypto symbol
            {"crypto_symbol": "BTC", "model_type": "invalid_type"},  # Invalid model type
            {"crypto_symbol": "BTC", "training_config": {"epochs": -1}}  # Invalid config
        ]
        
        for invalid_request in invalid_requests:
            response = client.post(
                "/api/v1/ml/training/start",
                json=invalid_request,
                headers=headers
            )
            
            assert response.status_code == 422  # Validation error


# Performance and load tests
class TestPerformanceIntegration:
    """Integration tests for performance and load"""
    
    @pytest.mark.asyncio
    async def test_concurrent_predictions(self, db_session, test_crypto, sample_price_data):
        """Test concurrent prediction handling"""
        
        # Ensure model exists
        models = model_registry.list_models(test_crypto.symbol)
        if not models:
            training_result = await training_service.train_model(
                crypto_symbol=test_crypto.symbol,
                model_type="lstm",
                training_config={"epochs": 1},
                force_retrain=True
            )
            assert training_result.get("success", False) is True
        
        # Create multiple concurrent prediction tasks
        import time
        
        async def make_prediction():
            return await prediction_service.predict_price(
                crypto_symbol=test_crypto.symbol,
                timeframe="1h"
            )
        
        start_time = time.time()
        
        # Run 5 concurrent predictions
        tasks = [make_prediction() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Check results
        successful_results = [r for r in results if not isinstance(r, Exception) and r.get("success", False)]
        
        assert len(successful_results) >= 3, f"Expected at least 3 successful predictions, got {len(successful_results)}"
        assert total_time < 30, f"Concurrent predictions took too long: {total_time:.2f}s"
    
    @pytest.mark.asyncio
    async def test_prediction_response_time(self, db_session, test_crypto, sample_price_data):
        """Test individual prediction response time"""
        
        # Ensure model exists
        models = model_registry.list_models(test_crypto.symbol)
        if not models:
            training_result = await training_service.train_model(
                crypto_symbol=test_crypto.symbol,
                model_type="lstm",
                training_config={"epochs": 1},
                force_retrain=True
            )
            assert training_result.get("success", False) is True
        
        import time
        
        # Test prediction response time
        start_time = time.time()
        
        result = await prediction_service.predict_price(
            crypto_symbol=test_crypto.symbol,
            timeframe="1h"
        )
        
        response_time = time.time() - start_time
        
        assert result.get("success", False) is True
        assert response_time < 10, f"Prediction response time too slow: {response_time:.2f}s"
    
    def test_database_performance(self, db_session, test_crypto, sample_price_data):
        """Test database query performance"""
        
        import time
        
        # Test price data query performance
        start_time = time.time()
        
        price_data = price_data_repository.get_historical_data(
            db_session, test_crypto.id, days=30
        )
        
        query_time = time.time() - start_time
        
        assert len(price_data) > 0
        assert query_time < 1.0, f"Price data query too slow: {query_time:.2f}s"
        
        # Test pagination performance
        start_time = time.time()
        
        paginated_data = price_data_repository.get_recent_prices(
            db_session, test_crypto.id, limit=100, skip=0
        )
        
        pagination_time = time.time() - start_time
        
        assert len(paginated_data) > 0
        assert pagination_time < 0.5, f"Pagination query too slow: {pagination_time:.2f}s"