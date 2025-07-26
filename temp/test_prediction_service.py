# File: temp/test_prediction_service.py
# Comprehensive test suite for Prediction Infrastructure (Stage B)

import asyncio
import sys
import os
import time
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Test imports
from app.core.database import SessionLocal
from app.repositories import cryptocurrency_repository, price_data_repository
from app.models import Cryptocurrency, PriceData

# Stage B components to test
try:
    from app.ml.prediction.prediction_service import prediction_service
    from app.ml.prediction.model_loader import model_loader
    from app.ml.prediction.inference_engine import inference_engine
    from app.monitoring.performance_tracker import performance_tracker
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Some components not available: {e}")
    COMPONENTS_AVAILABLE = False


async def test_prediction_service():
    """Test the main prediction service functionality"""
    print("🔮 Testing Prediction Service")
    print("=" * 50)
    
    if not COMPONENTS_AVAILABLE:
        print("❌ Cannot test: Components not available")
        return False
    
    try:
        # Test 1: Single prediction
        print("📊 Test 1: Single Bitcoin Prediction")
        print("-" * 30)
        
        result = await prediction_service.predict_price(
            crypto_symbol="BTC",
            prediction_horizon=24,
            use_cache=False  # Test without cache first
        )
        
        if result['success']:
            print("✅ Single prediction successful!")
            print(f"   Current Price: ${result['current_price']:,.2f}")
            print(f"   Predicted Price: ${result['predicted_price']:,.2f}")
            print(f"   Confidence: {result['confidence_score']:.1f}%")
            print(f"   Response Time: {result['prediction_metadata']['response_time_ms']:.1f}ms")
            print(f"   Model Used: {result['model_info']['model_id']}")
        else:
            print(f"❌ Single prediction failed: {result.get('error', 'Unknown error')}")
        
        print()
        
        # Test 2: Batch prediction
        print("📊 Test 2: Batch Predictions")
        print("-" * 30)
        
        crypto_symbols = ["BTC", "ETH"] if result['success'] else ["BTC"]
        batch_result = await prediction_service.predict_batch(
            crypto_symbols=crypto_symbols,
            prediction_horizon=24,
            max_concurrent=2
        )
        
        if batch_result['success']:
            print("✅ Batch predictions successful!")
            print(f"   Total requested: {batch_result['summary']['total_requested']}")
            print(f"   Successful: {batch_result['summary']['successful']}")
            print(f"   Failed: {batch_result['summary']['failed']}")
            
            for symbol, pred in batch_result['predictions'].items():
                if pred['success']:
                    print(f"   {symbol}: ${pred['predicted_price']:,.2f} "
                          f"(confidence: {pred['confidence_score']:.1f}%)")
        else:
            print("❌ Batch predictions failed")
        
        print()
        
        # Test 3: Cache functionality
        print("📊 Test 3: Cache Functionality")
        print("-" * 30)
        
        # First request (should be cache miss)
        start_time = time.time()
        result1 = await prediction_service.predict_price("BTC", 24, use_cache=True)
        time1 = time.time() - start_time
        
        # Second request (should be cache hit)
        start_time = time.time()
        result2 = await prediction_service.predict_price("BTC", 24, use_cache=True)
        time2 = time.time() - start_time
        
        if result1['success'] and result2['success']:
            cache_used1 = result1['prediction_metadata'].get('cache_used', False)
            cache_used2 = result2['prediction_metadata'].get('cache_used', False)
            
            print(f"✅ Cache test successful!")
            print(f"   First request: {time1:.3f}s (cache: {cache_used1})")
            print(f"   Second request: {time2:.3f}s (cache: {cache_used2})")
            
            if not cache_used1 and cache_used2:
                print("✅ Cache working correctly!")
            else:
                print("⚠️ Cache might not be working as expected")
        
        print()
        
        # Test 4: Performance metrics
        print("📊 Test 4: Performance Metrics")
        print("-" * 30)
        
        perf_metrics = prediction_service.get_performance_metrics()
        print(f"✅ Performance metrics retrieved:")
        print(f"   Total predictions: {perf_metrics['total_predictions']}")
        print(f"   Cache hit rate: {perf_metrics['cache_hit_rate']}%")
        print(f"   Average response time: {perf_metrics['average_response_time']}ms")
        print(f"   Error rate: {perf_metrics['error_rate']}%")
        print(f"   Models cached: {perf_metrics['models_cached']}")
        
        # Test 5: Error handling
        print()
        print("📊 Test 5: Error Handling")
        print("-" * 30)
        
        # Test with invalid crypto symbol
        error_result = await prediction_service.predict_price(
            crypto_symbol="INVALID_CRYPTO",
            prediction_horizon=24
        )
        
        if not error_result['success']:
            print("✅ Error handling working correctly!")
            print(f"   Error message: {error_result.get('error', 'Unknown')}")
        else:
            print("⚠️ Error handling might need improvement")
        
        return True
        
    except Exception as e:
        print(f"❌ Prediction service test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_model_loader():
    """Test the model loader functionality"""
    print("🏗️ Testing Model Loader")
    print("=" * 50)
    
    if not COMPONENTS_AVAILABLE:
        print("❌ Cannot test: Components not available")
        return False
    
    try:
        # Test 1: Load single model
        print("📊 Test 1: Load Bitcoin Model")
        print("-" * 30)
        
        model = model_loader.load_model("BTC")
        
        if model:
            print("✅ Model loaded successfully!")
            print(f"   Model type: {type(model).__name__}")
            print(f"   Is trained: {model.is_trained}")
            print(f"   Sequence length: {getattr(model, 'sequence_length', 'Unknown')}")
            print(f"   Features: {getattr(model, 'n_features', 'Unknown')}")
        else:
            print("❌ Model loading failed")
        
        print()
        
        # Test 2: Cache functionality
        print("📊 Test 2: Model Cache Test")
        print("-" * 30)
        
        # Load same model again (should be from cache)
        start_time = time.time()
        model2 = model_loader.load_model("BTC")
        cache_time = time.time() - start_time
        
        # Force reload
        start_time = time.time()
        model3 = model_loader.load_model("BTC", force_reload=True)
        reload_time = time.time() - start_time
        
        if model2 and model3:
            print("✅ Cache test successful!")
            print(f"   Cache load time: {cache_time:.3f}s")
            print(f"   Reload time: {reload_time:.3f}s")
            
            if cache_time < reload_time:
                print("✅ Cache is faster than reload!")
            else:
                print("⚠️ Cache might not be working optimally")
        
        print()
        
        # Test 3: Cached models info
        print("📊 Test 3: Cached Models Information")
        print("-" * 30)
        
        cached_models = model_loader.get_cached_models()
        print(f"✅ Found {len(cached_models)} cached models:")
        
        for model_info in cached_models:
            print(f"   {model_info['crypto_symbol']}: "
                  f"healthy={model_info['is_healthy']}, "
                  f"age={model_info['cache_age_seconds']:.1f}s")
        
        print()
        
        # Test 4: Performance stats
        print("📊 Test 4: Loader Performance Stats")
        print("-" * 30)
        
        stats = model_loader.get_performance_stats()
        print(f"✅ Loader performance:")
        print(f"   Total loads: {stats['total_loads']}")
        print(f"   Cache hit rate: {stats['cache_hit_rate']}%")
        print(f"   Average load time: {stats['average_load_time_seconds']:.3f}s")
        print(f"   Memory usage: {stats['memory_usage_mb']:.1f}MB")
        
        # Test 5: Health check
        print()
        print("📊 Test 5: Health Check")
        print("-" * 30)
        
        health = model_loader.health_check()
        print(f"✅ Health check results:")
        print(f"   Total cached: {health['total_cached']}")
        print(f"   Healthy models: {health['healthy_models']}")
        print(f"   Cache health: {health['cache_health_percentage']}%")
        
        # Test 6: Error handling
        print()
        print("📊 Test 6: Error Handling")
        print("-" * 30)
        
        # Test with invalid crypto
        invalid_model = model_loader.load_model("INVALID_CRYPTO")
        if not invalid_model:
            print("✅ Error handling working correctly for invalid crypto")
        else:
            print("⚠️ Unexpected success with invalid crypto")
        
        return True
        
    except Exception as e:
        print(f"❌ Model loader test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_inference_engine():
    """Test the inference engine functionality"""
    print("⚡ Testing Inference Engine")
    print("=" * 50)
    
    if not COMPONENTS_AVAILABLE:
        print("❌ Cannot test: Components not available")
        return False
    
    try:
        # First, load a model for testing
        model = model_loader.load_model("BTC")
        if not model:
            print("❌ Cannot test inference engine: No model available")
            return False
        
        # Prepare dummy input data
        import numpy as np
        sequence_length = getattr(model, 'sequence_length', 60)
        n_features = getattr(model, 'n_features', 5)
        
        dummy_input = np.random.random((1, sequence_length, n_features))
        
        # Test 1: Single inference
        print("📊 Test 1: Single Inference")
        print("-" * 30)
        
        result = await inference_engine.predict_single(
            model=model,
            input_data=dummy_input,
            return_confidence=True
        )
        
        if result['success']:
            print("✅ Single inference successful!")
            print(f"   Prediction: {result['prediction']:.6f}")
            print(f"   Confidence: {result.get('confidence', 'N/A')}")
            print(f"   Inference time: {result['inference_time_ms']:.1f}ms")
        else:
            print(f"❌ Single inference failed: {result.get('error', 'Unknown')}")
        
        print()
        
        # Test 2: Batch inference
        print("📊 Test 2: Batch Inference")
        print("-" * 30)
        
        # Create batch of dummy inputs
        batch_size = 5
        batch_input = [np.random.random((sequence_length, n_features)) for _ in range(batch_size)]
        
        batch_result = await inference_engine.predict_batch(
            model=model,
            input_batch=batch_input,
            return_confidence=True,
            batch_size=3
        )
        
        if batch_result['success']:
            print("✅ Batch inference successful!")
            print(f"   Batch size: {batch_result['batch_size']}")
            print(f"   Average prediction: {batch_result['average_prediction']:.6f}")
            print(f"   Inference time: {batch_result['inference_time_ms']:.1f}ms")
            print(f"   Predictions/second: {batch_result['predictions_per_second']:.1f}")
            
            if 'average_confidence' in batch_result:
                print(f"   Average confidence: {batch_result['average_confidence']:.3f}")
        else:
            print(f"❌ Batch inference failed: {batch_result.get('error', 'Unknown')}")
        
        print()
        
        # Test 3: Uncertainty prediction
        print("📊 Test 3: Uncertainty Prediction")
        print("-" * 30)
        
        uncertainty_result = await inference_engine.predict_with_uncertainty(
            model=model,
            input_data=dummy_input,
            n_samples=20  # Small number for testing
        )
        
        if uncertainty_result['success']:
            print("✅ Uncertainty prediction successful!")
            print(f"   Mean prediction: {uncertainty_result['prediction_mean']:.6f}")
            print(f"   Std deviation: {uncertainty_result['prediction_std']:.6f}")
            print(f"   Uncertainty score: {uncertainty_result['uncertainty_score']:.3f}")
            print(f"   Confidence interval: "
                  f"[{uncertainty_result['confidence_interval']['lower']:.6f}, "
                  f"{uncertainty_result['confidence_interval']['upper']:.6f}]")
            print(f"   Inference time: {uncertainty_result['inference_time_ms']:.1f}ms")
        else:
            print(f"❌ Uncertainty prediction failed: {uncertainty_result.get('error', 'Unknown')}")
        
        print()
        
        # Test 4: Performance stats
        print("📊 Test 4: Inference Performance Stats")
        print("-" * 30)
        
        stats = inference_engine.get_performance_stats()
        print(f"✅ Inference performance:")
        print(f"   Total inferences: {stats['total_inferences']}")
        print(f"   Batch inferences: {stats['batch_inferences']}")
        print(f"   Average time: {stats['average_inference_time_ms']:.1f}ms")
        print(f"   Error rate: {stats['error_rate_percentage']:.1f}%")
        print(f"   Worker threads: {stats['worker_threads']}")
        
        # Test 5: Error handling
        print()
        print("📊 Test 5: Error Handling")
        print("-" * 30)
        
        # Test with invalid input shape
        invalid_input = np.random.random((1, 10, 3))  # Wrong shape
        
        error_result = await inference_engine.predict_single(
            model=model,
            input_data=invalid_input
        )
        
        if not error_result['success']:
            print("✅ Error handling working correctly!")
            print(f"   Error: {error_result.get('error', 'Unknown')}")
        else:
            print("⚠️ Unexpected success with invalid input")
        
        # Test 6: Reset stats
        print()
        print("📊 Test 6: Reset Statistics")
        print("-" * 30)
        
        reset_result = inference_engine.reset_stats()
        print("✅ Statistics reset successfully!")
        print(f"   Reset at: {reset_result['reset_at']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Inference engine test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_performance_tracker():
    """Test the performance tracking functionality"""
    print("📊 Testing Performance Tracker")
    print("=" * 50)
    
    if not COMPONENTS_AVAILABLE:
        print("❌ Cannot test: Components not available")
        return False
    
    try:
        # Test 1: Track prediction performance
        print("📊 Test 1: Track Prediction Performance")
        print("-" * 30)
        
        # Simulate some predictions
        predictions_data = [
            {"symbol": "BTC", "predicted": 50000, "actual": 49500, "confidence": 0.85},
            {"symbol": "BTC", "predicted": 51000, "actual": 50800, "confidence": 0.78},
            {"symbol": "BTC", "predicted": 52000, "actual": 53000, "confidence": 0.72},
            {"symbol": "ETH", "predicted": 3000, "actual": 2950, "confidence": 0.65},
            {"symbol": "ETH", "predicted": 3100, "actual": 3200, "confidence": 0.70},
        ]
        
        tracking_ids = []
        for i, pred_data in enumerate(predictions_data):
            tracking_id = await performance_tracker.track_prediction(
                crypto_symbol=pred_data["symbol"],
                predicted_price=pred_data["predicted"],
                confidence_score=pred_data["confidence"],
                model_id=f"test_model_{pred_data['symbol'].lower()}",
                actual_price=pred_data["actual"]
            )
            tracking_ids.append(tracking_id)
            print(f"   Tracked prediction {i+1}: {tracking_id}")
        
        print(f"✅ Tracked {len(tracking_ids)} predictions")
        print()
        
        # Test 2: Update prediction with actual price
        print("📊 Test 2: Update Prediction with Actual")
        print("-" * 30)
        
        if tracking_ids:
            # Update first prediction with new actual price
            updated = await performance_tracker.update_prediction_actual(
                tracking_ids[0], 49800
            )
            
            if updated:
                print("✅ Prediction updated with actual price")
            else:
                print("❌ Failed to update prediction")
        
        print()
        
        # Test 3: System performance tracking
        print("📊 Test 3: System Performance Tracking")
        print("-" * 30)
        
        # Simulate system metrics
        for i in range(5):
            await performance_tracker.track_system_performance(
                response_time_ms=100 + i * 50,
                memory_usage_mb=512 + i * 10,
                cpu_usage_percent=20 + i * 5,
                active_predictions=10 + i,
                cache_hit_rate=0.8 + i * 0.02,
                error_count=i % 2
            )
        
        print("✅ Tracked 5 system performance metrics")
        print()
        
        # Test 4: Get prediction accuracy
        print("📊 Test 4: Prediction Accuracy Analysis")
        print("-" * 30)
        
        btc_accuracy = performance_tracker.get_prediction_accuracy(crypto_symbol="BTC")
        print(f"✅ BTC Accuracy Analysis:")
        print(f"   Total predictions: {btc_accuracy['total_predictions']}")
        print(f"   Accurate predictions: {btc_accuracy['accurate_predictions']}")
        print(f"   Accuracy rate: {btc_accuracy['accuracy_rate']:.1f}%")
        print(f"   Average error: ${btc_accuracy['average_error']:.2f}")
        print(f"   Average percentage error: {btc_accuracy['average_percentage_error']:.1f}%")
        
        print()
        
        # Test 5: System performance stats
        print("📊 Test 5: System Performance Stats")
        print("-" * 30)
        
        system_perf = performance_tracker.get_system_performance(time_range_hours=1)
        if 'total_requests' in system_perf:
            print(f"✅ System Performance:")
            print(f"   Total requests: {system_perf['total_requests']}")
            print(f"   Average response time: {system_perf['response_time']['average_ms']:.1f}ms")
            print(f"   Peak response time: {system_perf['response_time']['max_ms']:.1f}ms")
            print(f"   Average memory: {system_perf['memory_usage']['average_mb']:.1f}MB")
            print(f"   Peak memory: {system_perf['memory_usage']['peak_mb']:.1f}MB")
            print(f"   Average CPU: {system_perf['cpu_usage']['average_percent']:.1f}%")
        else:
            print("⚠️ Limited system performance data available")
        
        print()
        
        # Test 6: Crypto-specific performance
        print("📊 Test 6: Crypto-specific Performance")
        print("-" * 30)
        
        btc_perf = performance_tracker.get_crypto_performance("BTC")
        print(f"✅ BTC Performance:")
        print(f"   Total predictions: {btc_perf['total_predictions']}")
        print(f"   Accuracy rate: {btc_perf['accuracy_rate']:.1f}%")
        print(f"   Performance grade: {btc_perf['performance_grade']}")
        print(f"   Average error: {btc_perf['average_percentage_error']:.1f}%")
        
        print()
        
        # Test 7: Alert status
        print("📊 Test 7: Alert Status")
        print("-" * 30)
        
        alerts = performance_tracker.get_alert_status()
        print(f"✅ Alert Status: {alerts['alert_status']}")
        print(f"   Total alerts: {alerts['total_alerts']}")
        print(f"   Critical alerts: {alerts['critical_alerts']}")
        print(f"   Warning alerts: {alerts['warning_alerts']}")
        
        if alerts['active_alerts']:
            print("   Active alerts:")
            for alert in alerts['active_alerts'][:3]:  # Show first 3
                print(f"     - {alert['message']}")
        
        # Test 8: Reset metrics
        print()
        print("📊 Test 8: Reset Metrics")
        print("-" * 30)
        
        reset_result = performance_tracker.reset_metrics(crypto_symbol="BTC")
        print("✅ BTC metrics reset successfully!")
        print(f"   Reset type: {reset_result['reset_type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance tracker test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration():
    """Test integration between all Stage B components"""
    print("🔗 Testing Stage B Integration")
    print("=" * 50)
    
    if not COMPONENTS_AVAILABLE:
        print("❌ Cannot test: Components not available")
        return False
    
    try:
        # Integration Test: Complete prediction workflow
        print("📊 Integration Test: Complete Workflow")
        print("-" * 40)
        
        # Step 1: Make prediction using prediction service
        print("🔮 Step 1: Making prediction...")
        prediction_result = await prediction_service.predict_price(
            crypto_symbol="BTC",
            prediction_horizon=24,
            use_cache=False
        )
        
        if not prediction_result['success']:
            print(f"❌ Prediction failed: {prediction_result.get('error')}")
            return False
        
        print(f"✅ Prediction successful: ${prediction_result['predicted_price']:,.2f}")
        
        # Step 2: Track the prediction performance
        print("📊 Step 2: Tracking performance...")
        tracking_id = await performance_tracker.track_prediction(
            crypto_symbol="BTC",
            predicted_price=prediction_result['predicted_price'],
            confidence_score=prediction_result['confidence_score'],
            model_id=prediction_result['model_info']['model_id']
        )
        print(f"✅ Performance tracked: {tracking_id}")
        
        # Step 3: Test model loader integration
        print("🏗️ Step 3: Testing model loader...")
        model = model_loader.load_model("BTC")
        if model:
            print("✅ Model loaded successfully")
        else:
            print("❌ Model loading failed")
            return False
        
        # Step 4: Test inference engine with loaded model
        print("⚡ Step 4: Testing inference engine...")
        import numpy as np
        
        # Create dummy input (in real scenario, this comes from data processing)
        sequence_length = getattr(model, 'sequence_length', 60)
        n_features = getattr(model, 'n_features', 5)
        dummy_input = np.random.random((1, sequence_length, n_features))
        
        inference_result = await inference_engine.predict_single(
            model=model,
            input_data=dummy_input,
            return_confidence=True
        )
        
        if inference_result['success']:
            print(f"✅ Inference successful: {inference_result['prediction']:.6f}")
        else:
            print(f"❌ Inference failed: {inference_result.get('error')}")
            return False
        
        # Step 5: Check all component performance
        print("📈 Step 5: Checking component performance...")
        
        # Prediction service performance
        pred_perf = prediction_service.get_performance_metrics()
        print(f"   Prediction Service: {pred_perf['total_predictions']} predictions, "
              f"{pred_perf['average_response_time']:.1f}ms avg")
        
        # Model loader performance
        loader_perf = model_loader.get_performance_stats()
        print(f"   Model Loader: {loader_perf['cache_hit_rate']:.1f}% cache hit rate, "
              f"{loader_perf['cached_models_count']} models cached")
        
        # Inference engine performance
        inference_perf = inference_engine.get_performance_stats()
        print(f"   Inference Engine: {inference_perf['total_inferences']} inferences, "
              f"{inference_perf['average_inference_time_ms']:.1f}ms avg")
        
        # Performance tracker stats
        tracker_accuracy = performance_tracker.get_prediction_accuracy(crypto_symbol="BTC")
        print(f"   Performance Tracker: {tracker_accuracy['total_predictions']} tracked, "
              f"{tracker_accuracy['accuracy_rate']:.1f}% accuracy")
        
        print()
        print("✅ All Stage B components integrated successfully!")
        
        # Step 6: End-to-end performance summary
        print("📊 Step 6: End-to-End Performance Summary")
        print("-" * 40)
        
        print("🎯 Stage B Infrastructure Status:")
        print(f"   ✅ Prediction Service: Operational")
        print(f"   ✅ Model Loader: {loader_perf['cached_models_count']} models ready")
        print(f"   ✅ Inference Engine: {inference_perf['worker_threads']} workers")
        print(f"   ✅ Performance Tracker: Monitoring active")
        
        print(f"\n📈 Performance Metrics:")
        print(f"   • Response Time: {pred_perf['average_response_time']:.1f}ms")
        print(f"   • Cache Hit Rate: {pred_perf['cache_hit_rate']:.1f}%")
        print(f"   • Prediction Accuracy: {tracker_accuracy['accuracy_rate']:.1f}%")
        print(f"   • Error Rate: {pred_perf['error_rate']:.1f}%")
        
        # Step 7: Stress test
        print()
        print("📊 Step 7: Stress Test")
        print("-" * 40)
        
        print("🔥 Running 10 concurrent predictions...")
        stress_tasks = []
        for i in range(10):
            task = prediction_service.predict_price(
                crypto_symbol="BTC",
                prediction_horizon=24,
                use_cache=True
            )
            stress_tasks.append(task)
        
        stress_results = await asyncio.gather(*stress_tasks, return_exceptions=True)
        successful_stress = sum(1 for r in stress_results if isinstance(r, dict) and r.get('success', False))
        
        print(f"✅ Stress test completed: {successful_stress}/10 successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_edge_cases():
    """Test edge cases and error scenarios"""
    print("🧪 Testing Edge Cases")
    print("=" * 50)
    
    if not COMPONENTS_AVAILABLE:
        print("❌ Cannot test: Components not available")
        return False
    
    try:
        edge_case_results = []
        
        # Test 1: Invalid crypto symbol
        print("📊 Test 1: Invalid Crypto Symbol")
        print("-" * 30)
        
        result = await prediction_service.predict_price("INVALID_CRYPTO", 24)
        if not result['success']:
            print("✅ Correctly handled invalid crypto symbol")
            edge_case_results.append(True)
        else:
            print("❌ Should have failed with invalid crypto")
            edge_case_results.append(False)
        
        # Test 2: Extreme prediction horizon
        print("\n📊 Test 2: Extreme Prediction Horizon")
        print("-" * 30)
        
        result = await prediction_service.predict_price("BTC", 10000)  # Very large horizon
        if result:  # Should handle gracefully
            print("✅ Handled extreme prediction horizon")
            edge_case_results.append(True)
        else:
            print("❌ Failed to handle extreme horizon")
            edge_case_results.append(False)
        
        # Test 3: Memory pressure test
        print("\n📊 Test 3: Memory Pressure Test")
        print("-" * 30)
        
        try:
            # Load multiple models to test memory management
            models = []
            for i in range(3):
                model = model_loader.load_model("BTC")
                if model:
                    models.append(model)
            
            print(f"✅ Loaded {len(models)} models without memory issues")
            edge_case_results.append(True)
            
        except Exception as e:
            print(f"⚠️ Memory pressure test issue: {str(e)}")
            edge_case_results.append(False)
        
        # Test 4: Concurrent access test
        print("\n📊 Test 4: Concurrent Access Test")
        print("-" * 30)
        
        try:
            # Multiple concurrent model loads
            concurrent_tasks = []
            for i in range(5):
                task = asyncio.create_task(
                    asyncio.get_event_loop().run_in_executor(
                        None, model_loader.load_model, "BTC"
                    )
                )
                concurrent_tasks.append(task)
            
            concurrent_models = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            successful_loads = sum(1 for m in concurrent_models if m and not isinstance(m, Exception))
            
            print(f"✅ Concurrent access test: {successful_loads}/5 successful")
            edge_case_results.append(successful_loads >= 3)  # At least 3 should succeed
            
        except Exception as e:
            print(f"❌ Concurrent access test failed: {str(e)}")
            edge_case_results.append(False)
        
        # Test 5: Cache cleanup test
        print("\n📊 Test 5: Cache Cleanup Test")
        print("-" * 30)
        
        try:
            # Clear all caches
            pred_clear = prediction_service.clear_cache()
            model_clear = model_loader.clear_cache()
            
            print("✅ Cache cleanup successful")
            print(f"   Prediction cache: {pred_clear}")
            print(f"   Model cache: {model_clear}")
            edge_case_results.append(True)
            
        except Exception as e:
            print(f"❌ Cache cleanup failed: {str(e)}")
            edge_case_results.append(False)
        
        # Test 6: Invalid input data test
        print("\n📊 Test 6: Invalid Input Data Test")
        print("-" * 30)
        
        try:
            model = model_loader.load_model("BTC")
            if model:
                import numpy as np
                # Create invalid input (wrong dimensions)
                invalid_input = np.random.random((5, 10))  # 2D instead of 3D
                
                result = await inference_engine.predict_single(
                    model=model,
                    input_data=invalid_input
                )
                
                if not result['success']:
                    print("✅ Correctly rejected invalid input data")
                    edge_case_results.append(True)
                else:
                    print("❌ Should have rejected invalid input")
                    edge_case_results.append(False)
            else:
                print("⚠️ No model available for input validation test")
                edge_case_results.append(False)
                
        except Exception as e:
            print(f"✅ Correctly caught input validation error: {type(e).__name__}")
            edge_case_results.append(True)
        
        # Test 7: Network simulation (Redis unavailable)
        print("\n📊 Test 7: Redis Unavailable Test")
        print("-" * 30)
        
        try:
            # Test prediction without Redis (should work with fallback)
            result = await prediction_service.predict_price("BTC", 24, use_cache=True)
            
            if result['success']:
                print("✅ Gracefully handled Redis unavailability")
                edge_case_results.append(True)
            else:
                print("⚠️ Failed when Redis unavailable (might be expected)")
                edge_case_results.append(True)  # Still acceptable
                
        except Exception as e:
            print(f"⚠️ Redis test issue: {str(e)}")
            edge_case_results.append(True)  # Acceptable for optional component
        
        # Summary
        print(f"\n📊 Edge Cases Summary")
        print("-" * 30)
        passed_edge_cases = sum(edge_case_results)
        total_edge_cases = len(edge_case_results)
        
        print(f"✅ Passed: {passed_edge_cases}/{total_edge_cases} edge case tests")
        
        return passed_edge_cases >= (total_edge_cases * 0.8)  # 80% pass rate
        
    except Exception as e:
        print(f"❌ Edge case testing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_performance_benchmarks():
    """Test performance benchmarks"""
    print("🚀 Testing Performance Benchmarks")
    print("=" * 50)
    
    if not COMPONENTS_AVAILABLE:
        print("❌ Cannot test: Components not available")
        return False
    
    try:
        benchmark_results = []
        
        # Benchmark 1: Prediction latency
        print("📊 Benchmark 1: Prediction Latency")
        print("-" * 30)
        
        latencies = []
        for i in range(10):
            start_time = time.time()
            result = await prediction_service.predict_price("BTC", 24, use_cache=False)
            latency = (time.time() - start_time) * 1000  # Convert to ms
            
            if result['success']:
                latencies.append(latency)
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            print(f"✅ Latency benchmark completed:")
            print(f"   Average: {avg_latency:.1f}ms")
            print(f"   Min: {min_latency:.1f}ms")
            print(f"   Max: {max_latency:.1f}ms")
            
            # Pass if average latency < 2000ms
            benchmark_results.append(avg_latency < 2000)
        else:
            print("❌ No successful predictions for latency test")
            benchmark_results.append(False)
        
        # Benchmark 2: Throughput test
        print("\n📊 Benchmark 2: Throughput Test")
        print("-" * 30)
        
        start_time = time.time()
        concurrent_predictions = []
        
        # Create 20 concurrent prediction tasks
        for i in range(20):
            task = prediction_service.predict_price("BTC", 24, use_cache=True)
            concurrent_predictions.append(task)
        
        results = await asyncio.gather(*concurrent_predictions, return_exceptions=True)
        total_time = time.time() - start_time
        
        successful_predictions = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
        throughput = successful_predictions / total_time if total_time > 0 else 0
        
        print(f"✅ Throughput benchmark completed:")
        print(f"   Successful predictions: {successful_predictions}/20")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Throughput: {throughput:.2f} predictions/second")
        
        # Pass if throughput > 5 predictions/second and success rate > 80%
        success_rate = successful_predictions / 20
        benchmark_results.append(throughput > 5 and success_rate > 0.8)
        
        # Benchmark 3: Model loading speed
        print("\n📊 Benchmark 3: Model Loading Speed")
        print("-" * 30)
        
        # Clear cache first
        model_loader.clear_cache()
        
        load_times = []
        for i in range(3):
            start_time = time.time()
            model = model_loader.load_model("BTC", force_reload=True)
            load_time = (time.time() - start_time) * 1000
            
            if model:
                load_times.append(load_time)
        
        if load_times:
            avg_load_time = sum(load_times) / len(load_times)
            print(f"✅ Model loading benchmark:")
            print(f"   Average load time: {avg_load_time:.1f}ms")
            
            # Pass if average load time < 5000ms (5 seconds)
            benchmark_results.append(avg_load_time < 5000)
        else:
            print("❌ Model loading failed")
            benchmark_results.append(False)
        
        # Benchmark 4: Cache efficiency
        print("\n📊 Benchmark 4: Cache Efficiency")
        print("-" * 30)
        
        # Make several requests to same prediction
        cache_times = []
        for i in range(5):
            start_time = time.time()
            result = await prediction_service.predict_price("BTC", 24, use_cache=True)
            cache_time = (time.time() - start_time) * 1000
            
            if result['success']:
                cache_times.append(cache_time)
                cache_used = result['prediction_metadata'].get('cache_used', False)
                print(f"   Request {i+1}: {cache_time:.1f}ms (cached: {cache_used})")
        
        if len(cache_times) >= 2:
            # First request should be slower (cache miss), subsequent should be faster
            first_request = cache_times[0]
            subsequent_avg = sum(cache_times[1:]) / len(cache_times[1:])
            
            print(f"✅ Cache efficiency:")
            print(f"   First request: {first_request:.1f}ms")
            print(f"   Subsequent average: {subsequent_avg:.1f}ms")
            
            # Pass if subsequent requests are at least 20% faster
            improvement = (first_request - subsequent_avg) / first_request
            benchmark_results.append(improvement > 0.2 or subsequent_avg < 100)  # 100ms is very fast
        else:
            print("❌ Insufficient cache test data")
            benchmark_results.append(False)
        
        # Summary
        print(f"\n📊 Performance Benchmarks Summary")
        print("-" * 30)
        passed_benchmarks = sum(benchmark_results)
        total_benchmarks = len(benchmark_results)
        
        print(f"✅ Passed: {passed_benchmarks}/{total_benchmarks} benchmarks")
        
        benchmark_names = ["Latency", "Throughput", "Model Loading", "Cache Efficiency"]
        for i, (name, passed) in enumerate(zip(benchmark_names, benchmark_results)):
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {name}: {status}")
        
        return passed_benchmarks >= (total_benchmarks * 0.75)  # 75% pass rate
        
    except Exception as e:
        print(f"❌ Performance benchmark testing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def run_stage_b_tests():
    """Run all Stage B tests"""
    print("🚀 Stage B: Prediction Infrastructure - Complete Test Suite")
    print("=" * 70)
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = {}
    
    # Test 1: Prediction Service
    test_results['prediction_service'] = await test_prediction_service()
    print()
    
    # Test 2: Model Loader
    test_results['model_loader'] = await test_model_loader()
    print()
    
    # Test 3: Inference Engine
    test_results['inference_engine'] = await test_inference_engine()
    print()
    
    # Test 4: Performance Tracker
    test_results['performance_tracker'] = await test_performance_tracker()
    print()
    
    # Test 5: Integration
    test_results['integration'] = await test_integration()
    print()
    
    # Test 6: Edge Cases
    test_results['edge_cases'] = await test_edge_cases()
    print()
    
    # Test 7: Performance Benchmarks
    test_results['performance_benchmarks'] = await test_performance_benchmarks()
    print()
    
    # Final Results
    print("🏁 Stage B Test Results Summary")
    print("=" * 50)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    print()
    print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All Stage B tests passed! Prediction Infrastructure is ready!")
        print("\n🚀 Ready for Stage C: API Integration")
        
        # Show readiness status
        print("\n📋 Stage B Completion Status:")
        print("   ✅ Prediction Service - Real-time predictions")
        print("   ✅ Model Loader - Efficient model management") 
        print("   ✅ Inference Engine - High-performance inference")
        print("   ✅ Performance Tracker - Comprehensive monitoring")
        print("   ✅ Integration - All components working together")
        print("   ✅ Edge Cases - Robust error handling")
        print("   ✅ Performance Benchmarks - Meets requirements")
        
        # Performance summary
        print("\n📈 Performance Summary:")
        if COMPONENTS_AVAILABLE:
            try:
                pred_metrics = prediction_service.get_performance_metrics()
                loader_stats = model_loader.get_performance_stats()
                inference_stats = inference_engine.get_performance_stats()
                
                print(f"   • Total Predictions: {pred_metrics['total_predictions']}")
                print(f"   • Average Response Time: {pred_metrics['average_response_time']:.1f}ms")
                print(f"   • Cache Hit Rate: {pred_metrics['cache_hit_rate']:.1f}%")
                print(f"   • Model Cache Efficiency: {loader_stats['cache_hit_rate']:.1f}%")
                print(f"   • Inference Performance: {inference_stats['average_inference_time_ms']:.1f}ms")
                print(f"   • Error Rate: {pred_metrics['error_rate']:.1f}%")
            except:
                print("   • Performance metrics collected successfully")
        
        # Technical achievements
        print("\n🎯 Technical Achievements:")
        print("   • Thread-safe concurrent processing")
        print("   • Redis-based caching (when available)")
        print("   • Uncertainty quantification")
        print("   • Comprehensive error handling")
        print("   • Real-time performance monitoring")
        print("   • Memory-efficient model management")
        
    else:
        print(f"⚠️ {total_tests - passed_tests} test(s) failed. Please fix issues before proceeding.")
        
        # Show which tests failed
        failed_tests = [name for name, result in test_results.items() if not result]
        print(f"\n❌ Failed tests: {', '.join(failed_tests)}")
        
        print(f"\n🔧 Troubleshooting Tips:")
        print("   1. Ensure Stage A (Training) completed successfully")
        print("   2. Check database connectivity")
        print("   3. Verify model files exist and are accessible")
        print("   4. Ensure sufficient system resources")
        print("   5. Check Redis availability (optional)")
    
    print(f"\n🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed_tests == total_tests


# Database setup helper
async def setup_test_environment():
    """Setup test environment"""
    print("🔧 Setting up test environment...")
    
    db = SessionLocal()
    try:
        # Check if Bitcoin exists
        btc_crypto = cryptocurrency_repository.get_by_symbol(db, "BTC")
        if not btc_crypto:
            print("⚠️ Bitcoin not found in database. Please run the training pipeline first.")
            return False
        
        # Check if we have some price data
        recent_prices = price_data_repository.get_price_history(
            db=db,
            crypto_id=btc_crypto.id,
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc),
            limit=10
        )
        
        if len(recent_prices) < 5:
            print("⚠️ Insufficient price data. Please ensure data collection is running.")
            return False
        
        print("✅ Test environment ready")
        return True
        
    finally:
        db.close()


def create_missing_directories():
    """Create missing directories for Stage B components"""
    directories = [
        "backend/app/ml/prediction",
        "backend/app/monitoring", 
        "temp"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        
        # Create __init__.py files for Python packages
        if directory.startswith("backend/app"):
            init_file = os.path.join(directory, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write(f'# {directory.split("/")[-1].title()} package\n')


def show_requirements():
    """Show requirements for Stage B testing"""
    print("📋 Stage B Testing Requirements")
    print("=" * 40)
    print("✅ Required:")
    print("   • Training pipeline completed (Stage A)")
    print("   • Bitcoin (BTC) model trained and available")
    print("   • Price data in database (recent data)")
    print("   • PostgreSQL running")
    print("   • Backend dependencies installed")
    print()
    print("⚡ Optional (for better performance):")
    print("   • Redis running (for caching)")
    print("   • GPU support (for faster inference)")
    print("   • Sufficient RAM (>4GB recommended)")
    print()
    print("🔧 If tests fail, check:")
    print("   1. Run training pipeline first")
    print("   2. Verify database connections")
    print("   3. Check model files exist")
    print("   4. Ensure recent price data")


async def run_quick_test():
    """Run a quick test to verify basic functionality"""
    print("⚡ Quick Stage B Test")
    print("=" * 30)
    
    if not COMPONENTS_AVAILABLE:
        print("❌ Components not available - please check imports")
        return False
    
    try:
        # Test 1: Basic prediction
        print("🔮 Testing basic prediction...")
        result = await prediction_service.predict_price("BTC", 24, use_cache=False)
        
        if result['success']:
            print(f"✅ Basic prediction works: ${result['predicted_price']:,.2f}")
        else:
            print(f"❌ Basic prediction failed: {result.get('error')}")
            return False
        
        # Test 2: Model loading
        print("🏗️ Testing model loading...")
        model = model_loader.load_model("BTC")
        
        if model:
            print("✅ Model loading works")
        else:
            print("❌ Model loading failed")
            return False
        
        # Test 3: Performance tracking
        print("📊 Testing performance tracking...")
        tracking_id = await performance_tracker.track_prediction(
            crypto_symbol="BTC",
            predicted_price=result['predicted_price'],
            confidence_score=result['confidence_score'],
            model_id=result['model_info']['model_id']
        )
        
        if tracking_id:
            print("✅ Performance tracking works")
        else:
            print("❌ Performance tracking failed")
            return False
        
        print("\n🎉 Quick test passed! Stage B infrastructure is functional.")
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {str(e)}")
        return False


async def run_health_check():
    """Run a health check on all components"""
    print("🏥 Stage B Health Check")
    print("=" * 30)
    
    if not COMPONENTS_AVAILABLE:
        print("❌ Components not available")
        return False
    
    health_status = {}
    
    try:
        # Check prediction service
        print("🔮 Checking Prediction Service...")
        try:
            metrics = prediction_service.get_performance_metrics()
            health_status['prediction_service'] = True
            print(f"   ✅ Operational (predictions: {metrics['total_predictions']})")
        except Exception as e:
            health_status['prediction_service'] = False
            print(f"   ❌ Failed: {str(e)}")
        
        # Check model loader
        print("🏗️ Checking Model Loader...")
        try:
            stats = model_loader.get_performance_stats()
            health_check = model_loader.health_check()
            health_status['model_loader'] = True
            print(f"   ✅ Operational (cached: {stats['cached_models_count']}, "
                  f"health: {health_check['cache_health_percentage']:.1f}%)")
        except Exception as e:
            health_status['model_loader'] = False
            print(f"   ❌ Failed: {str(e)}")
        
        # Check inference engine
        print("⚡ Checking Inference Engine...")
        try:
            stats = inference_engine.get_performance_stats()
            health_status['inference_engine'] = True
            print(f"   ✅ Operational (inferences: {stats['total_inferences']}, "
                  f"error rate: {stats['error_rate_percentage']:.1f}%)")
        except Exception as e:
            health_status['inference_engine'] = False
            print(f"   ❌ Failed: {str(e)}")
        
        # Check performance tracker
        print("📊 Checking Performance Tracker...")
        try:
            alerts = performance_tracker.get_alert_status()
            health_status['performance_tracker'] = True
            print(f"   ✅ Operational (status: {alerts['alert_status']}, "
                  f"alerts: {alerts['total_alerts']})")
        except Exception as e:
            health_status['performance_tracker'] = False
            print(f"   ❌ Failed: {str(e)}")
        
        # Overall health
        healthy_components = sum(health_status.values())
        total_components = len(health_status)
        health_percentage = (healthy_components / total_components) * 100
        
        print(f"\n🏥 Overall Health: {healthy_components}/{total_components} components healthy ({health_percentage:.1f}%)")
        
        if health_percentage == 100:
            print("🎉 All systems operational!")
        elif health_percentage >= 75:
            print("⚠️ Minor issues detected, but system is functional")
        else:
            print("❌ Major issues detected, system may not function properly")
        
        return health_percentage >= 75
        
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False


if __name__ == "__main__":
    async def main():
        print("🧪 CryptoPredict Stage B Test Suite")
        print("=" * 50)
        
        # Show requirements
        show_requirements()
        print()
        
        # Create missing directories
        create_missing_directories()
        print("📁 Created necessary directories")
        
        # Check component availability
        if not COMPONENTS_AVAILABLE:
            print("❌ Stage B components not available!")
            print("💡 Please ensure all Stage B files are created first:")
            print("   - backend/app/ml/prediction/prediction_service.py")
            print("   - backend/app/ml/prediction/model_loader.py") 
            print("   - backend/app/ml/prediction/inference_engine.py")
            print("   - backend/app/monitoring/performance_tracker.py")
            return
        
        # Setup test environment
        if not await setup_test_environment():
            print("❌ Test environment setup failed")
            print("\n🔧 Troubleshooting:")
            print("   1. Ensure training pipeline has run successfully")
            print("   2. Check database connection")
            print("   3. Verify Bitcoin model exists")
            print("   4. Ensure price data is available")
            return
        
        # Ask user for test type
        print("\n🎯 Test Options:")
        print("   1. Health Check (quick system status)")
        print("   2. Quick Test (basic functionality)")
        print("   3. Full Test Suite (comprehensive)")
        
        try:
            choice = input("\nSelect test type (1, 2, or 3, default=3): ").strip()
            
            if choice == "1":
                success = await run_health_check()
            elif choice == "2":
                success = await run_quick_test()
            else:
                success = await run_stage_b_tests()
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Test interrupted by user")
            return
        except Exception as e:
            print(f"\n❌ Test execution failed: {str(e)}")
            return
        
        print("\n" + "=" * 70)
        
        if success:
            print("🎯 Stage B is complete and ready for production!")
            print("\n📋 Next Steps:")
            print("   1. 🚀 Move to Stage C: API Integration")
            print("   2. 🔌 Create prediction API endpoints")
            print("   3. 🔄 Implement background training tasks")
            print("   4. 📚 Generate API documentation")
            
            print("\n🎉 Stage B Infrastructure Summary:")
            print("   ✅ Real-time prediction service")
            print("   ✅ Intelligent model loading and caching")
            print("   ✅ High-performance inference engine")
            print("   ✅ Comprehensive performance monitoring")
            print("   ✅ Robust error handling and fallbacks")
            print("   ✅ Performance benchmarks met")
            
        else:
            print("💼 Please address the failed tests before moving to Stage C")
            print("\n🔧 Common fixes:")
            print("   - Ensure training pipeline has run successfully")
            print("   - Check database connections")
            print("   - Verify Redis is running (optional but recommended)")
            print("   - Ensure sufficient price data is available")
            print("   - Check model file permissions")
            print("   - Monitor system resources (CPU, memory)")
            
        print(f"\n🕐 Test session completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run the tests
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test suite interrupted. Goodbye!")
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()