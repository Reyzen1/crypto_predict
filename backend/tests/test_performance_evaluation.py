# File: backend/tests/test_performance_evaluation.py
# Performance Evaluation Tests for CryptoPredict MVP - Stage D

import pytest
import asyncio
import time
import psutil
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

# Import test utilities
from .conftest import db_session, test_crypto, sample_price_data

# Import application components
from app.core.database import SessionLocal, engine
from app.repositories import (
    cryptocurrency_repository, 
    price_data_repository,
    prediction_repository
)
from app.ml.training.training_service import training_service
from app.ml.prediction.prediction_service import prediction_service
from app.ml.config.ml_config import model_registry
from app.core.config import settings


class PerformanceMetrics:
    """Performance metrics collector"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.memory_before = None
        self.memory_after = None
        self.cpu_before = None
        self.cpu_after = None
        
    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        process = psutil.Process()
        self.memory_before = process.memory_info().rss / 1024 / 1024  # MB
        self.cpu_before = process.cpu_percent()
        
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.end_time = time.time()
        process = psutil.Process()
        self.memory_after = process.memory_info().rss / 1024 / 1024  # MB
        self.cpu_after = process.cpu_percent()
        
    def get_duration(self) -> float:
        """Get execution duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
        
    def get_memory_usage(self) -> float:
        """Get memory usage increase in MB"""
        if self.memory_before and self.memory_after:
            return self.memory_after - self.memory_before
        return 0.0
        
    def get_metrics_dict(self) -> Dict[str, float]:
        """Get all metrics as dictionary"""
        return {
            "duration_seconds": self.get_duration(),
            "memory_usage_mb": self.get_memory_usage(),
            "memory_before_mb": self.memory_before or 0,
            "memory_after_mb": self.memory_after or 0,
            "cpu_before_percent": self.cpu_before or 0,
            "cpu_after_percent": self.cpu_after or 0
        }


@pytest.mark.performance
class TestMLTrainingPerformance:
    """Performance tests for ML training pipeline"""
    
    @pytest.mark.asyncio
    async def test_training_performance_benchmarks(self, db_session, test_crypto, sample_price_data):
        """Test ML training performance benchmarks"""
        
        # Ensure sufficient data
        price_count = price_data_repository.count_by_crypto(db_session, test_crypto.id)
        if price_count < 200:
            pytest.skip("Insufficient data for performance testing")
        
        # Test different model sizes for performance comparison
        test_configs = [
            {
                "name": "Small Model",
                "config": {
                    "epochs": 3,
                    "batch_size": 16,
                    "lstm_units": [10, 5],
                    "sequence_length": 20
                }
            },
            {
                "name": "Medium Model", 
                "config": {
                    "epochs": 5,
                    "batch_size": 32,
                    "lstm_units": [25, 15, 10],
                    "sequence_length": 40
                }
            },
            {
                "name": "Large Model",
                "config": {
                    "epochs": 7,
                    "batch_size": 64,
                    "lstm_units": [50, 30, 20, 10],
                    "sequence_length": 60
                }
            }
        ]
        
        performance_results = []
        
        for test_config in test_configs:
            metrics = PerformanceMetrics()
            metrics.start_monitoring()
            
            print(f"\n🧪 Testing {test_config['name']}...")
            
            training_result = await training_service.train_model(
                crypto_symbol=test_crypto.symbol,
                model_type="lstm",
                training_config=test_config["config"],
                data_days_back=60,
                force_retrain=True
            )
            
            metrics.stop_monitoring()
            perf_data = metrics.get_metrics_dict()
            
            # Verify training success
            assert training_result.get("success", False) is True
            
            perf_data.update({
                "model_name": test_config["name"],
                "training_success": True,
                "model_id": training_result.get("model_id"),
                "epochs": test_config["config"]["epochs"],
                "lstm_units": len(test_config["config"]["lstm_units"])
            })
            
            performance_results.append(perf_data)
            
            print(f"   ⏱️ Duration: {perf_data['duration_seconds']:.2f}s")
            print(f"   💾 Memory: {perf_data['memory_usage_mb']:.1f}MB")
            
            # Performance assertions
            assert perf_data["duration_seconds"] < 300, f"Training too slow: {perf_data['duration_seconds']:.2f}s"
            assert perf_data["memory_usage_mb"] < 500, f"Memory usage too high: {perf_data['memory_usage_mb']:.1f}MB"
        
        # Analyze performance scaling
        print(f"\n📊 Performance Scaling Analysis:")
        for i, result in enumerate(performance_results):
            print(f"   {result['model_name']}: {result['duration_seconds']:.2f}s, {result['memory_usage_mb']:.1f}MB")
            
            # Verify reasonable scaling (larger models should take longer but not exponentially)
            if i > 0:
                prev_duration = performance_results[i-1]['duration_seconds']
                current_duration = result['duration_seconds']
                scaling_factor = current_duration / prev_duration
                
                assert scaling_factor < 5.0, f"Training time scaling too aggressive: {scaling_factor:.2f}x"
    
    @pytest.mark.asyncio
    async def test_concurrent_training_performance(self, db_session, test_crypto, sample_price_data):
        """Test performance with concurrent training requests"""
        
        price_count = price_data_repository.count_by_crypto(db_session, test_crypto.id)
        if price_count < 100:
            pytest.skip("Insufficient data for concurrent training test")
        
        # Test concurrent training jobs
        async def train_small_model(suffix: str):
            return await training_service.train_model(
                crypto_symbol=test_crypto.symbol,
                model_type="lstm",
                training_config={
                    "epochs": 2,
                    "batch_size": 16,
                    "lstm_units": [10],
                    "sequence_length": 15
                },
                data_days_back=30,
                force_retrain=True
            )
        
        metrics = PerformanceMetrics()
        metrics.start_monitoring()
        
        # Run 3 concurrent training jobs
        training_tasks = [
            train_small_model("a"),
            train_small_model("b"), 
            train_small_model("c")
        ]
        
        results = await asyncio.gather(*training_tasks, return_exceptions=True)
        
        metrics.stop_monitoring()
        perf_data = metrics.get_metrics_dict()
        
        # Analyze results
        successful_trainings = sum(1 for r in results if not isinstance(r, Exception) and r.get("success", False))
        
        print(f"🔄 Concurrent training results:")
        print(f"   ✅ Successful: {successful_trainings}/3")
        print(f"   ⏱️ Total time: {perf_data['duration_seconds']:.2f}s")
        print(f"   💾 Memory usage: {perf_data['memory_usage_mb']:.1f}MB")
        
        # Performance expectations for concurrent training
        assert successful_trainings >= 2, f"Too many concurrent training failures: {successful_trainings}/3"
        assert perf_data["duration_seconds"] < 180, f"Concurrent training too slow: {perf_data['duration_seconds']:.2f}s"
        assert perf_data["memory_usage_mb"] < 800, f"Concurrent training memory too high: {perf_data['memory_usage_mb']:.1f}MB"
    
    def test_training_memory_efficiency(self, db_session, test_crypto, sample_price_data):
        """Test training memory efficiency and cleanup"""
        
        import gc
        
        price_count = price_data_repository.count_by_crypto(db_session, test_crypto.id)
        if price_count < 100:
            pytest.skip("Insufficient data for memory efficiency test")
        
        # Measure baseline memory
        gc.collect()
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024
        
        print(f"📊 Memory efficiency test:")
        print(f"   📋 Baseline memory: {baseline_memory:.1f}MB")
        
        # Run multiple training cycles to test memory cleanup
        for i in range(3):
            print(f"   🔄 Training cycle {i+1}/3...")
            
            # Train a model
            training_result = asyncio.run(training_service.train_model(
                crypto_symbol=test_crypto.symbol,
                model_type="lstm",
                training_config={
                    "epochs": 2,
                    "batch_size": 16,
                    "lstm_units": [15, 10]
                },
                data_days_back=30,
                force_retrain=True
            ))
            
            assert training_result.get("success", False) is True
            
            # Force garbage collection
            gc.collect()
            
            # Measure memory after training
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - baseline_memory
            
            print(f"      💾 Memory after cycle {i+1}: {current_memory:.1f}MB (+{memory_increase:.1f}MB)")
            
            # Memory should not continuously increase (indicating memory leaks)
            if i > 0:  # After first cycle, check for reasonable memory usage
                assert memory_increase < 200, f"Memory usage too high after cycle {i+1}: +{memory_increase:.1f}MB"
        
        # Final memory check
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - baseline_memory
        
        print(f"   📈 Total memory increase: {total_increase:.1f}MB")
        assert total_increase < 300, f"Total memory increase too high: {total_increase:.1f}MB"


@pytest.mark.performance
class TestMLPredictionPerformance:
    """Performance tests for ML prediction pipeline"""
    
    @pytest.mark.asyncio
    async def test_prediction_response_time_benchmarks(self, db_session, test_crypto, sample_price_data):
        """Test prediction response time benchmarks"""
        
        # Ensure model exists
        models = model_registry.list_models(test_crypto.symbol)
        if not models:
            # Train a quick model
            training_result = await training_service.train_model(
                crypto_symbol=test_crypto.symbol,
                model_type="lstm",
                training_config={"epochs": 2, "lstm_units": [10]},
                force_retrain=True
            )
            assert training_result.get("success", False) is True
        
        # Test response times for different scenarios
        test_scenarios = [
            ("Cold Start", True),   # Force refresh (no cache)
            ("Warm Cache", False),  # Use cache if available
            ("Different Timeframe", False),  # Different timeframe
        ]
        
        timeframes = ["1h", "24h", "7d"]
        response_times = []
        
        for scenario_name, force_refresh in test_scenarios:
            for timeframe in timeframes:
                start_time = time.time()
                
                result = await prediction_service.predict_price(
                    crypto_symbol=test_crypto.symbol,
                    timeframe=timeframe,
                    force_refresh=force_refresh
                )
                
                response_time = (time.time() - start_time) * 1000  # ms
                response_times.append(response_time)
                
                print(f"   {scenario_name} ({timeframe}): {response_time:.1f}ms")
                
                assert result.get("success", False) is True
                assert response_time < 5000, f"Response time too slow: {response_time:.1f}ms"
        
        # Analyze response time statistics
        avg_response = sum(response_times) / len(response_times)
        max_response = max(response_times)
        min_response = min(response_times)
        
        print(f"📊 Response time statistics:")
        print(f"   📈 Average: {avg_response:.1f}ms")
        print(f"   📊 Range: {min_response:.1f}ms - {max_response:.1f}ms")
        
        assert avg_response < 2000, f"Average response time too slow: {avg_response:.1f}ms"
        assert max_response < 8000, f"Max response time too slow: {max_response:.1f}ms"
    
    @pytest.mark.asyncio
    async def test_batch_prediction_performance(self, db_session, test_crypto, sample_price_data):
        """Test batch prediction performance"""
        
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
        
        # Test batch sizes
        batch_sizes = [1, 3, 5]
        batch_performance = []
        
        for batch_size in batch_sizes:
            crypto_symbols = [test_crypto.symbol] * batch_size
            
            start_time = time.time()
            
            batch_result = await prediction_service.batch_predict(
                crypto_symbols=crypto_symbols,
                timeframe="1h"
            )
            
            batch_time = (time.time() - start_time) * 1000  # ms
            
            assert batch_result.get("success", False) is True
            successful_predictions = batch_result.get("successful_predictions", 0)
            
            # Calculate performance per prediction
            time_per_prediction = batch_time / batch_size if batch_size > 0 else batch_time
            
            batch_performance.append({
                "batch_size": batch_size,
                "total_time_ms": batch_time,
                "time_per_prediction_ms": time_per_prediction,
                "successful_predictions": successful_predictions
            })
            
            print(f"   Batch size {batch_size}: {batch_time:.1f}ms total, {time_per_prediction:.1f}ms per prediction")
            
            assert batch_time < 10000, f"Batch prediction too slow: {batch_time:.1f}ms"
            assert successful_predictions >= batch_size * 0.8, f"Too many batch failures: {successful_predictions}/{batch_size}"
        
        # Verify batch efficiency (batching should be more efficient than individual calls)
        if len(batch_performance) >= 2:
            single_time = batch_performance[0]["time_per_prediction_ms"]
            batch_time = batch_performance[-1]["time_per_prediction_ms"]
            
            if batch_time < single_time * 0.9:  # At least 10% improvement
                print(f"✅ Batch efficiency: {((single_time - batch_time) / single_time) * 100:.1f}% improvement")
            else:
                print(f"⚠️ Batch efficiency: Minimal improvement")
    
    @pytest.mark.asyncio
    async def test_concurrent_prediction_performance(self, db_session, test_crypto, sample_price_data):
        """Test concurrent prediction performance"""
        
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
        
        # Test concurrent prediction loads
        concurrent_loads = [5, 10, 15]
        
        for load in concurrent_loads:
            print(f"🔄 Testing {load} concurrent predictions...")
            
            async def make_prediction():
                return await prediction_service.predict_price(
                    crypto_symbol=test_crypto.symbol,
                    timeframe="1h"
                )
            
            start_time = time.time()
            
            # Create concurrent tasks
            tasks = [make_prediction() for _ in range(load)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = (time.time() - start_time) * 1000  # ms
            
            # Analyze results
            successful_predictions = sum(1 for r in results if not isinstance(r, Exception) and r.get("success", False))
            success_rate = successful_predictions / load
            avg_time_per_prediction = total_time / load
            
            print(f"   📊 Load {load}: {successful_predictions}/{load} successful ({success_rate:.1%})")
            print(f"   ⏱️ Total time: {total_time:.1f}ms, avg: {avg_time_per_prediction:.1f}ms per prediction")
            
            # Performance expectations
            assert success_rate >= 0.8, f"Success rate too low for load {load}: {success_rate:.1%}"
            assert total_time < 30000, f"Total time too high for load {load}: {total_time:.1f}ms"
            assert avg_time_per_prediction < 5000, f"Average time too high for load {load}: {avg_time_per_prediction:.1f}ms"
    
    @pytest.mark.asyncio
    async def test_prediction_caching_performance(self, db_session, test_crypto, sample_price_data):
        """Test prediction caching performance impact"""
        
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
        
        # Test cache performance
        timeframe = "1h"
        
        # First call (should populate cache)
        start_time = time.time()
        result1 = await prediction_service.predict_price(
            crypto_symbol=test_crypto.symbol,
            timeframe=timeframe,
            force_refresh=True  # Ensure fresh calculation
        )
        first_call_time = (time.time() - start_time) * 1000
        
        assert result1.get("success", False) is True
        
        # Second call (should use cache)
        start_time = time.time()
        result2 = await prediction_service.predict_price(
            crypto_symbol=test_crypto.symbol,
            timeframe=timeframe
        )
        second_call_time = (time.time() - start_time) * 1000
        
        assert result2.get("success", False) is True
        
        # Third call (should also use cache)
        start_time = time.time()
        result3 = await prediction_service.predict_price(
            crypto_symbol=test_crypto.symbol,
            timeframe=timeframe
        )
        third_call_time = (time.time() - start_time) * 1000
        
        assert result3.get("success", False) is True
        
        print(f"🏆 Cache performance test:")
        print(f"   First call (no cache): {first_call_time:.1f}ms")
        print(f"   Second call (cached): {second_call_time:.1f}ms")
        print(f"   Third call (cached): {third_call_time:.1f}ms")
        
        # Calculate cache efficiency
        if first_call_time > 0:
            cache_speedup_2 = (first_call_time - second_call_time) / first_call_time * 100
            cache_speedup_3 = (first_call_time - third_call_time) / first_call_time * 100
            
            print(f"   Cache speedup: {cache_speedup_2:.1f}% (2nd), {cache_speedup_3:.1f}% (3rd)")
            
            # Cache should provide some speedup (though not guaranteed due to various factors)
            # We'll just verify that cached calls aren't significantly slower
            assert second_call_time <= first_call_time * 1.5, "Cached call should not be much slower"
            assert third_call_time <= first_call_time * 1.5, "Cached call should not be much slower"
        
        # Verify prediction consistency
        assert result1["predicted_price"] == result2["predicted_price"]
        assert result2["predicted_price"] == result3["predicted_price"]


@pytest.mark.performance  
class TestDatabasePerformance:
    """Performance tests for database operations"""
    
    def test_price_data_query_performance(self, db_session, test_crypto, sample_price_data):
        """Test price data query performance"""
        
        # Test different query sizes
        query_limits = [100, 500, 1000, 2000]
        query_times = []
        
        for limit in query_limits:
            start_time = time.time()
            
            price_data = price_data_repository.get_recent_prices(
                db_session, test_crypto.id, limit=limit
            )
            
            query_time = (time.time() - start_time) * 1000  # ms
            query_times.append(query_time)
            
            print(f"   Query {limit} records: {query_time:.1f}ms")
            
            assert len(price_data) <= limit
            assert query_time < 2000, f"Query too slow for {limit} records: {query_time:.1f}ms"
        
        # Test query scaling
        if len(query_times) >= 2:
            scaling_factors = []
            for i in range(1, len(query_times)):
                factor = query_times[i] / query_times[i-1]
                scaling_factors.append(factor)
            
            avg_scaling = sum(scaling_factors) / len(scaling_factors)
            print(f"   Average query scaling factor: {avg_scaling:.2f}x")
            
            # Query time should scale reasonably (not exponentially)
            assert avg_scaling < 3.0, f"Query scaling too poor: {avg_scaling:.2f}x"
    
    def test_database_connection_performance(self):
        """Test database connection performance"""
        
        # Test connection pool performance
        connection_times = []
        
        for i in range(10):
            start_time = time.time()
            
            with engine.connect() as conn:
                result = conn.execute("SELECT 1").fetchone()
                assert result[0] == 1
            
            connection_time = (time.time() - start_time) * 1000  # ms
            connection_times.append(connection_time)
        
        avg_connection_time = sum(connection_times) / len(connection_times)
        max_connection_time = max(connection_times)
        
        print(f"📊 Database connection performance:")
        print(f"   Average: {avg_connection_time:.1f}ms")
        print(f"   Max: {max_connection_time:.1f}ms")
        
        assert avg_connection_time < 100, f"Average connection time too slow: {avg_connection_time:.1f}ms"
        assert max_connection_time < 500, f"Max connection time too slow: {max_connection_time:.1f}ms"
    
    def test_bulk_operations_performance(self, db_session, test_crypto):
        """Test bulk database operations performance"""
        
        from app.schemas.price_data import PriceDataCreate
        from decimal import Decimal
        
        # Test bulk insert performance
        bulk_sizes = [100, 500, 1000]
        
        for size in bulk_sizes:
            print(f"🔄 Testing bulk insert of {size} records...")
            
            # Generate test data
            test_data = []
            base_time = datetime.now(timezone.utc)
            
            for i in range(size):
                test_data.append(PriceDataCreate(
                    crypto_id=test_crypto.id,
                    price=Decimal(f"{45000 + i}"),
                    volume=Decimal("1000000"),
                    timestamp=base_time + timedelta(minutes=i)
                ))
            
            start_time = time.time()
            
            # Bulk insert
            for data in test_data:
                price_data_repository.create(db_session, obj_in=data)
            
            bulk_time = (time.time() - start_time) * 1000  # ms
            time_per_record = bulk_time / size
            
            print(f"   Bulk insert {size}: {bulk_time:.1f}ms total, {time_per_record:.2f}ms per record")
            
            assert bulk_time < 10000, f"Bulk insert too slow for {size} records: {bulk_time:.1f}ms"
            assert time_per_record < 20, f"Time per record too slow: {time_per_record:.2f}ms"


@pytest.mark.performance
class TestSystemResourcePerformance:
    """Performance tests for system resource usage"""
    
    def test_system_resource_monitoring(self):
        """Test system resource monitoring during operations"""
        
        import psutil
        
        # Get baseline system metrics
        baseline_cpu = psutil.cpu_percent(interval=1)
        baseline_memory = psutil.virtual_memory().percent
        baseline_disk = psutil.disk_usage('/').percent
        
        print(f"📊 System baseline:")
        print(f"   CPU: {baseline_cpu:.1f}%")
        print(f"   Memory: {baseline_memory:.1f}%")
        print(f"   Disk: {baseline_disk:.1f}%")
        
        # System health checks
        assert baseline_cpu < 80, f"System CPU too high: {baseline_cpu:.1f}%"
        assert baseline_memory < 90, f"System memory too high: {baseline_memory:.1f}%"
        assert baseline_disk < 90, f"System disk too full: {baseline_disk:.1f}%"
        
        # Test process-specific resource usage
        process = psutil.Process()
        process_memory = process.memory_info().rss / 1024 / 1024  # MB
        process_cpu = process.cpu_percent()
        
        print(f"📊 Process metrics:")
        print(f"   Memory: {process_memory:.1f}MB")
        print(f"   CPU: {process_cpu:.1f}%")
        
        # Process resource limits
        assert process_memory < 1000, f"Process memory too high: {process_memory:.1f}MB"
    
    def test_file_system_performance(self):
        """Test file system performance for model storage"""
        
        from app.ml.config.ml_config import ml_config
        import tempfile
        
        models_storage_path = ml_config.models_storage_path
        
        # Test directory access
        start_time = time.time()
        
        # List files in model storage
        if os.path.exists(models_storage_path):
            files = os.listdir(models_storage_path)
            list_time = (time.time() - start_time) * 1000
            
            print(f"📁 Model storage performance:")
            print(f"   Directory list: {list_time:.1f}ms ({len(files)} files)")
            
            assert list_time < 1000, f"Directory listing too slow: {list_time:.1f}ms"
        
        # Test file I/O performance
        test_file_size = 1024 * 1024  # 1MB test file
        test_data = b"0" * test_file_size
        
        with tempfile.NamedTemporaryFile() as temp_file:
            # Test write performance
            start_time = time.time()
            temp_file.write(test_data)
            temp_file.flush()
            write_time = (time.time() - start_time) * 1000
            
            # Test read performance
            start_time = time.time()
            temp_file.seek(0)
            read_data = temp_file.read()
            read_time = (time.time() - start_time) * 1000
            
            print(f"💾 File I/O performance (1MB):")
            print(f"   Write: {write_time:.1f}ms")
            print(f"   Read: {read_time:.1f}ms")
            
            assert len(read_data) == test_file_size
            assert write_time < 1000, f"File write too slow: {write_time:.1f}ms"
            assert read_time < 500, f"File read too slow: {read_time:.1f}ms"


# Performance test utilities
def benchmark_function(func, *args, **kwargs) -> Tuple[Any, float]:
    """Benchmark a function and return result and execution time"""
    start_time = time.time()
    result = func(*args, **kwargs)
    execution_time = time.time() - start_time
    return result, execution_time


async def benchmark_async_function(func, *args, **kwargs) -> Tuple[Any, float]:
    """Benchmark an async function and return result and execution time"""
    start_time = time.time()
    result = await func(*args, **kwargs)
    execution_time = time.time() - start_time
    return result, execution_time


def measure_memory_usage(func, *args, **kwargs) -> Tuple[Any, float]:
    """Measure memory usage of a function"""
    import tracemalloc
    
    tracemalloc.start()
    result = func(*args, **kwargs)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return result, peak / 1024 / 1024  # MB


def get_system_load() -> Dict[str, float]:
    """Get current system load metrics"""
    import psutil
    
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "load_average": os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0
    }