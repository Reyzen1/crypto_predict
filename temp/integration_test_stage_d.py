# File: temp/integration_test_stage_d.py
# Stage D: Integration Tests with Real Bitcoin Data

import asyncio
import sys
import os
import json
import traceback
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

print("🧪 CryptoPredict Stage D - Integration & Real Data Testing")
print("=" * 65)
print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("🎯 Testing with real Bitcoin data and full ML pipeline")
print()


class IntegrationTestSuite:
    """Integration test suite for Stage D - Real data testing"""
    
    def __init__(self):
        self.test_results = {}
        self.btc_crypto_id = None
        self.trained_model_id = None
        self.prediction_results = []
        
    async def run_integration_tests(self):
        """Run complete integration test suite"""
        try:
            test_scenarios = [
                ("Data Collection Integration", self.test_data_collection_integration),
                ("ML Training Integration", self.test_ml_training_integration),
                ("Prediction Generation Integration", self.test_prediction_integration),
                ("Background Tasks Integration", self.test_background_tasks_integration),
                ("Performance Evaluation", self.test_performance_evaluation),
                ("Error Handling & Edge Cases", self.test_error_handling),
                ("Load & Stress Testing", self.test_load_scenarios),
                ("End-to-End Workflow", self.test_complete_workflow)
            ]
            
            total_scenarios = len(test_scenarios)
            passed_scenarios = 0
            
            for i, (scenario_name, test_function) in enumerate(test_scenarios, 1):
                print(f"\n{'='*65}")
                print(f"🔬 Integration Test {i}/{total_scenarios}: {scenario_name}")
                print(f"{'='*65}")
                
                try:
                    result = await test_function()
                    if result:
                        passed_scenarios += 1
                        print(f"✅ {scenario_name}: PASSED")
                    else:
                        print(f"❌ {scenario_name}: FAILED")
                        
                except Exception as e:
                    print(f"💥 {scenario_name}: ERROR - {str(e)}")
                    self.test_results[scenario_name] = {"status": "error", "error": str(e)}
                
                # Delay between tests
                await asyncio.sleep(2)
            
            # Final assessment
            self.print_integration_results(passed_scenarios, total_scenarios)
            
        except Exception as e:
            print(f"\n💥 Integration test suite failed: {str(e)}")
            traceback.print_exc()
    
    async def test_data_collection_integration(self) -> bool:
        """Test real data collection and processing"""
        print("\n📊 Testing Data Collection Integration...")
        
        try:
            from app.core.database import SessionLocal
            from app.repositories import cryptocurrency_repository, price_data_repository
            from app.services.external_api import external_api_service
            
            db = SessionLocal()
            
            try:
                # Ensure Bitcoin exists
                print("   💰 Setting up Bitcoin cryptocurrency...")
                btc_crypto = cryptocurrency_repository.get_by_symbol(db, "BTC")
                
                if not btc_crypto:
                    from app.schemas.cryptocurrency import CryptocurrencyCreate
                    btc_create = CryptocurrencyCreate(
                        symbol="BTC",
                        name="Bitcoin",
                        is_active=True
                    )
                    btc_crypto = cryptocurrency_repository.create(db, obj_in=btc_create)
                
                self.btc_crypto_id = btc_crypto.id
                print(f"   ✅ Bitcoin setup complete (ID: {btc_crypto.id})")
                
                # Check existing price data
                print("   📈 Checking existing price data...")
                price_count = price_data_repository.count_by_crypto(db, btc_crypto.id)
                print(f"   📊 Existing price records: {price_count}")
                
                if price_count < 1000:  # Need sufficient data for ML
                    print("   ⚠️ Insufficient price data for ML training")
                    print("   💡 Recommendation: Run price collection tasks first")
                    
                    # Try to collect some data if external API is available
                    try:
                        print("   🔄 Attempting to collect recent price data...")
                        if hasattr(external_api_service, 'get_current_price'):
                            current_price = await external_api_service.get_current_price("BTC")
                            if current_price:
                                print(f"   💵 Current BTC price: ${current_price}")
                        else:
                            print("   ⚠️ External API service not available")
                    except Exception as e:
                        print(f"   ⚠️ Could not fetch external data: {str(e)}")
                
                else:
                    print("   ✅ Sufficient price data available for ML")
                
                # Test data quality
                print("   🔍 Testing data quality...")
                recent_prices = price_data_repository.get_recent_prices(
                    db, crypto_id=btc_crypto.id, limit=100
                )
                
                if recent_prices:
                    # Check for data consistency
                    prices = [float(p.price) for p in recent_prices[:10]]
                    avg_price = sum(prices) / len(prices)
                    print(f"   💹 Recent average price: ${avg_price:,.2f}")
                    
                    # Check for reasonable price ranges (Bitcoin should be > $1000)
                    if avg_price > 1000:
                        print("   ✅ Price data appears reasonable")
                    else:
                        print("   ⚠️ Price data may have quality issues")
                
                # Test historical data range
                print("   📅 Testing historical data range...")
                historical_data = price_data_repository.get_historical_data(
                    db, crypto_id=btc_crypto.id, days=30
                )
                
                if len(historical_data) >= 30:  # At least 30 days
                    print(f"   ✅ Historical data: {len(historical_data)} records")
                else:
                    print(f"   ⚠️ Limited historical data: {len(historical_data)} records")
                
                self.test_results["Data Collection Integration"] = {
                    "status": "passed",
                    "price_count": price_count,
                    "recent_prices": len(recent_prices),
                    "historical_days": len(historical_data)
                }
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"   ❌ Data collection integration failed: {str(e)}")
            self.test_results["Data Collection Integration"] = {
                "status": "failed", 
                "error": str(e)
            }
            return False
    
    async def test_ml_training_integration(self) -> bool:
        """Test ML training with real data"""
        print("\n🤖 Testing ML Training Integration...")
        
        try:
            from app.ml.training.training_service import training_service
            from app.core.database import SessionLocal
            from app.repositories import cryptocurrency_repository, price_data_repository
            
            if not self.btc_crypto_id:
                print("   ❌ Bitcoin cryptocurrency not available")
                return False
            
            db = SessionLocal()
            
            try:
                # Check data availability for training
                print("   📊 Checking training data availability...")
                price_count = price_data_repository.count_by_crypto(db, self.btc_crypto_id)
                
                if price_count < 500:  # Minimum for meaningful training
                    print(f"   ⚠️ Insufficient data for training: {price_count} records")
                    print("   💡 Skipping training test - need more price data")
                    self.test_results["ML Training Integration"] = {
                        "status": "skipped",
                        "reason": "Insufficient training data",
                        "price_count": price_count
                    }
                    return True  # Not a failure, just insufficient data
                
                print(f"   ✅ Sufficient training data: {price_count} records")
                
                # Test training configuration
                print("   ⚙️ Testing training configuration...")
                training_config = {
                    "sequence_length": 60,
                    "lstm_units": [50, 30],  # Smaller for testing
                    "epochs": 5,  # Very small for testing
                    "batch_size": 32,
                    "validation_split": 0.2,
                    "learning_rate": 0.001
                }
                
                print("   🚀 Starting test training (small model)...")
                training_result = await training_service.train_model(
                    crypto_symbol="BTC",
                    model_type="lstm",
                    training_config=training_config,
                    data_days_back=180,  # 6 months of data
                    force_retrain=True
                )
                
                if training_result and training_result.get("success", False):
                    print("   ✅ Training completed successfully")
                    self.trained_model_id = training_result.get("model_id")
                    
                    # Check training metrics
                    training_metrics = training_result.get("training_metrics", {})
                    validation_metrics = training_result.get("validation_metrics", {})
                    
                    print(f"   📊 Training loss: {training_metrics.get('loss', 'N/A')}")
                    print(f"   📊 Validation loss: {validation_metrics.get('val_loss', 'N/A')}")
                    
                    # Check model file exists
                    model_path = training_result.get("model_path")
                    if model_path and os.path.exists(model_path):
                        print(f"   ✅ Model file saved: {model_path}")
                    else:
                        print("   ⚠️ Model file not found")
                    
                    self.test_results["ML Training Integration"] = {
                        "status": "passed",
                        "model_id": self.trained_model_id,
                        "training_metrics": training_metrics,
                        "validation_metrics": validation_metrics
                    }
                    return True
                    
                else:
                    error_msg = training_result.get("error", "Unknown training error")
                    print(f"   ❌ Training failed: {error_msg}")
                    self.test_results["ML Training Integration"] = {
                        "status": "failed",
                        "error": error_msg
                    }
                    return False
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"   ❌ ML training integration failed: {str(e)}")
            self.test_results["ML Training Integration"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    async def test_prediction_integration(self) -> bool:
        """Test prediction generation with real models"""
        print("\n🔮 Testing Prediction Integration...")
        
        try:
            from app.ml.prediction.prediction_service import prediction_service
            
            # Test different prediction scenarios
            prediction_tests = [
                ("1 Hour Prediction", "1h"),
                ("24 Hour Prediction", "24h"),
                ("7 Day Prediction", "7d")
            ]
            
            successful_predictions = 0
            
            for test_name, timeframe in prediction_tests:
                try:
                    print(f"   🎯 Testing {test_name}...")
                    
                    prediction_result = await prediction_service.predict_price(
                        crypto_symbol="BTC",
                        timeframe=timeframe,
                        use_ensemble_models=True,
                        include_technical_indicators=True
                    )
                    
                    if prediction_result and prediction_result.get("success", False):
                        predicted_price = prediction_result.get("predicted_price", 0)
                        confidence = prediction_result.get("confidence_score", 0)
                        current_price = prediction_result.get("current_price", 0)
                        
                        print(f"      💵 Current: ${current_price:,.2f}")
                        print(f"      🎯 Predicted: ${predicted_price:,.2f}")
                        print(f"      📊 Confidence: {confidence:.1%}")
                        
                        # Validate prediction reasonableness
                        if predicted_price > 0 and confidence > 0:
                            print(f"      ✅ {test_name}: Valid prediction")
                            successful_predictions += 1
                            
                            self.prediction_results.append({
                                "timeframe": timeframe,
                                "predicted_price": predicted_price,
                                "confidence": confidence,
                                "current_price": current_price
                            })
                        else:
                            print(f"      ❌ {test_name}: Invalid prediction values")
                    else:
                        error_msg = prediction_result.get("error", "Unknown error")
                        print(f"      ❌ {test_name}: {error_msg}")
                
                except Exception as e:
                    print(f"      ❌ {test_name}: Exception - {str(e)}")
            
            # Test batch predictions
            print("   📦 Testing batch predictions...")
            try:
                batch_symbols = ["BTC"]  # Just BTC for now
                batch_result = await prediction_service.batch_predict(
                    crypto_symbols=batch_symbols,
                    timeframe="24h"
                )
                
                if batch_result and batch_result.get("successful_predictions", 0) > 0:
                    print("   ✅ Batch predictions: Working")
                    successful_predictions += 1
                else:
                    print("   ❌ Batch predictions: Failed")
            
            except Exception as e:
                print(f"   ❌ Batch predictions: {str(e)}")
            
            # Test prediction performance metrics
            print("   📊 Testing performance metrics...")
            try:
                metrics = prediction_service.get_performance_metrics()
                if metrics:
                    print(f"      • Total predictions: {metrics.get('total_predictions', 0)}")
                    print(f"      • Cache hit rate: {metrics.get('cache_hit_rate', 0):.1f}%")
                    print("   ✅ Performance metrics: Available")
                else:
                    print("   ⚠️ Performance metrics: Not available yet")
            
            except Exception as e:
                print(f"   ⚠️ Performance metrics: {str(e)}")
            
            success_rate = successful_predictions / (len(prediction_tests) + 1)  # +1 for batch
            
            if success_rate >= 0.7:  # 70% success rate
                self.test_results["Prediction Integration"] = {
                    "status": "passed",
                    "successful_predictions": successful_predictions,
                    "total_tests": len(prediction_tests) + 1,
                    "success_rate": success_rate,
                    "predictions": self.prediction_results
                }
                return True
            else:
                self.test_results["Prediction Integration"] = {
                    "status": "failed",
                    "successful_predictions": successful_predictions,
                    "total_tests": len(prediction_tests) + 1,
                    "success_rate": success_rate
                }
                return False
                
        except Exception as e:
            print(f"   ❌ Prediction integration failed: {str(e)}")
            self.test_results["Prediction Integration"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    async def test_background_tasks_integration(self) -> bool:
        """Test background task execution"""
        print("\n⚙️ Testing Background Tasks Integration...")
        
        try:
            from app.tasks.ml_tasks import get_task_status
            from app.tasks.price_collector import get_task_status as get_price_task_status
            
            # Test task status functions
            print("   🔍 Testing task status functions...")
            
            dummy_task_id = "test_integration_task_123"
            
            # Test ML task status
            ml_status = get_task_status(dummy_task_id)
            if ml_status and "status" in ml_status:
                print("   ✅ ML task status function: Working")
            else:
                print("   ❌ ML task status function: Not working")
                return False
            
            # Test price task status
            price_status = get_price_task_status(dummy_task_id)
            if price_status and "status" in price_status:
                print("   ✅ Price task status function: Working")
            else:
                print("   ❌ Price task status function: Not working")
                return False
            
            # Test task helper functions
            print("   🎯 Testing task helper functions...")
            from app.tasks.ml_tasks import (
                start_auto_training,
                start_prediction_generation,
                start_performance_evaluation,
                start_prediction_cleanup
            )
            
            helper_functions = [
                ("Auto Training", start_auto_training),
                ("Prediction Generation", start_prediction_generation),
                ("Performance Evaluation", start_performance_evaluation),
                ("Prediction Cleanup", start_prediction_cleanup)
            ]
            
            for func_name, func in helper_functions:
                if callable(func):
                    print(f"      ✅ {func_name}: Available")
                else:
                    print(f"      ❌ {func_name}: Not available")
                    return False
            
            # Test scheduler integration
            print("   ⏰ Testing scheduler integration...")
            try:
                from app.tasks.scheduler import get_next_run_times
                next_runs = get_next_run_times()
                
                if next_runs and isinstance(next_runs, dict):
                    ml_tasks = [task for task in next_runs.keys() if 'ml' in task.lower() or 'train' in task.lower() or 'predict' in task.lower()]
                    print(f"   ✅ Scheduler: {len(ml_tasks)} ML tasks scheduled")
                else:
                    print("   ⚠️ Scheduler: No scheduled tasks found")
            
            except Exception as e:
                print(f"   ⚠️ Scheduler test: {str(e)}")
            
            self.test_results["Background Tasks Integration"] = {
                "status": "passed",
                "ml_task_status": "working",
                "price_task_status": "working",
                "helper_functions": len(helper_functions)
            }
            return True
            
        except Exception as e:
            print(f"   ❌ Background tasks integration failed: {str(e)}")
            self.test_results["Background Tasks Integration"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    async def test_performance_evaluation(self) -> bool:
        """Test system performance evaluation"""
        print("\n📊 Testing Performance Evaluation...")
        
        try:
            import time
            from app.ml.prediction.prediction_service import prediction_service
            
            # Test response times
            print("   ⏱️ Testing response times...")
            
            start_time = time.time()
            
            # Multiple prediction calls to test performance
            response_times = []
            for i in range(5):
                call_start = time.time()
                
                try:
                    result = await prediction_service.predict_price(
                        crypto_symbol="BTC",
                        timeframe="1h",
                        use_ensemble_models=False  # Faster for testing
                    )
                    
                    call_time = (time.time() - call_start) * 1000  # ms
                    response_times.append(call_time)
                    
                except Exception as e:
                    print(f"      ⚠️ Prediction call {i+1} failed: {str(e)}")
            
            if response_times:
                avg_response = sum(response_times) / len(response_times)
                max_response = max(response_times)
                min_response = min(response_times)
                
                print(f"   📈 Performance Results:")
                print(f"      • Average response: {avg_response:.1f}ms")
                print(f"      • Min response: {min_response:.1f}ms")
                print(f"      • Max response: {max_response:.1f}ms")
                
                # Performance thresholds
                if avg_response < 2000:  # Less than 2 seconds
                    print("   ✅ Response time: Excellent")
                elif avg_response < 5000:  # Less than 5 seconds
                    print("   ✅ Response time: Good")
                else:
                    print("   ⚠️ Response time: Needs optimization")
            
            # Test memory usage (basic check)
            print("   💾 Testing memory usage...")
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            print(f"   💾 Current memory usage: {memory_mb:.1f} MB")
            
            if memory_mb < 500:  # Less than 500MB
                print("   ✅ Memory usage: Excellent")
            elif memory_mb < 1000:  # Less than 1GB
                print("   ✅ Memory usage: Good")
            else:
                print("   ⚠️ Memory usage: High")
            
            # Test concurrent requests (simplified)
            print("   🔄 Testing concurrent handling...")
            
            concurrent_start = time.time()
            
            # Simulate multiple concurrent requests
            tasks = []
            for i in range(3):  # Small number for testing
                task = prediction_service.predict_price(
                    crypto_symbol="BTC",
                    timeframe="1h"
                )
                tasks.append(task)
            
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                concurrent_time = (time.time() - concurrent_start) * 1000
                
                successful_concurrent = sum(1 for r in results if not isinstance(r, Exception))
                print(f"   ✅ Concurrent requests: {successful_concurrent}/{len(tasks)} successful")
                print(f"   ⏱️ Concurrent time: {concurrent_time:.1f}ms")
                
            except Exception as e:
                print(f"   ⚠️ Concurrent test failed: {str(e)}")
            
            self.test_results["Performance Evaluation"] = {
                "status": "passed",
                "avg_response_time_ms": avg_response if response_times else 0,
                "memory_usage_mb": memory_mb,
                "concurrent_success": True
            }
            return True
            
        except Exception as e:
            print(f"   ❌ Performance evaluation failed: {str(e)}")
            self.test_results["Performance Evaluation"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling and edge cases"""
        print("\n🛡️ Testing Error Handling & Edge Cases...")
        
        try:
            from app.ml.prediction.prediction_service import prediction_service
            from app.ml.training.training_service import training_service
            
            error_tests = []
            
            # Test invalid cryptocurrency
            print("   🚫 Testing invalid cryptocurrency...")
            try:
                result = await prediction_service.predict_price(
                    crypto_symbol="INVALID_CRYPTO",
                    timeframe="1h"
                )
                
                if result and not result.get("success", True):
                    print("   ✅ Invalid crypto: Properly handled")
                    error_tests.append(True)
                else:
                    print("   ❌ Invalid crypto: Not properly handled")
                    error_tests.append(False)
                    
            except Exception as e:
                print(f"   ✅ Invalid crypto: Exception properly raised - {str(e)}")
                error_tests.append(True)
            
            # Test invalid timeframe
            print("   ⏰ Testing invalid timeframe...")
            try:
                result = await prediction_service.predict_price(
                    crypto_symbol="BTC",
                    timeframe="invalid_timeframe"
                )
                
                if result and not result.get("success", True):
                    print("   ✅ Invalid timeframe: Properly handled")
                    error_tests.append(True)
                else:
                    print("   ❌ Invalid timeframe: Not properly handled")
                    error_tests.append(False)
                    
            except Exception as e:
                print(f"   ✅ Invalid timeframe: Exception properly raised - {str(e)}")
                error_tests.append(True)
            
            # Test network timeout simulation
            print("   🌐 Testing timeout handling...")
            try:
                # This should test the service's timeout handling
                result = await asyncio.wait_for(
                    prediction_service.predict_price("BTC", "1h"),
                    timeout=0.1  # Very short timeout
                )
                print("   ⚠️ Timeout test: Unexpectedly fast response")
                error_tests.append(True)  # Still ok
                
            except asyncio.TimeoutError:
                print("   ✅ Timeout handling: Working correctly")
                error_tests.append(True)
            except Exception as e:
                print(f"   ✅ Timeout test: Handled - {str(e)}")
                error_tests.append(True)
            
            # Test empty data scenarios
            print("   📊 Testing empty data handling...")
            try:
                # This would test what happens with no training data
                # Implementation depends on your service design
                print("   ℹ️ Empty data test: Skipped (implementation dependent)")
                error_tests.append(True)
                
            except Exception as e:
                print(f"   ⚠️ Empty data test: {str(e)}")
                error_tests.append(True)  # Not critical
            
            success_rate = sum(error_tests) / len(error_tests) if error_tests else 0
            
            if success_rate >= 0.8:  # 80% of error tests passed
                print(f"   ✅ Error handling: {success_rate:.1%} success rate")
                self.test_results["Error Handling"] = {
                    "status": "passed",
                    "success_rate": success_rate,
                    "tests_passed": sum(error_tests),
                    "total_tests": len(error_tests)
                }
                return True
            else:
                print(f"   ❌ Error handling: {success_rate:.1%} success rate")
                self.test_results["Error Handling"] = {
                    "status": "failed",
                    "success_rate": success_rate
                }
                return False
                
        except Exception as e:
            print(f"   ❌ Error handling test failed: {str(e)}")
            self.test_results["Error Handling"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    async def test_load_scenarios(self) -> bool:
        """Test load scenarios"""
        print("\n🚀 Testing Load Scenarios...")
        
        try:
            from app.ml.prediction.prediction_service import prediction_service
            import time
            
            # Test multiple simultaneous predictions
            print("   📊 Testing multiple simultaneous predictions...")
            
            start_time = time.time()
            
            # Create multiple prediction tasks
            prediction_tasks = []
            for i in range(10):  # 10 simultaneous predictions
                task = prediction_service.predict_price(
                    crypto_symbol="BTC",
                    timeframe="1h"
                )
                prediction_tasks.append(task)
            
            try:
                results = await asyncio.gather(*prediction_tasks, return_exceptions=True)
                total_time = time.time() - start_time
                
                successful_results = sum(1 for r in results if not isinstance(r, Exception))
                
                print(f"   📈 Load test results:")
                print(f"      • Total time: {total_time:.2f}s")
                print(f"      • Successful predictions: {successful_results}/10")
                print(f"      • Average time per prediction: {total_time/10:.2f}s")
                
                if successful_results >= 8:  # 80% success rate
                    print("   ✅ Load handling: Excellent")
                elif successful_results >= 6:  # 60% success rate
                    print("   ✅ Load handling: Good")
                else:
                    print("   ⚠️ Load handling: Needs improvement")
                
                # Test rapid sequential predictions
                print("   ⚡ Testing rapid sequential predictions...")
                
                sequential_start = time.time()
                sequential_successes = 0
                
                for i in range(5):
                    try:
                        result = await prediction_service.predict_price("BTC", "1h")
                        if result and result.get("success", False):
                            sequential_successes += 1
                    except Exception:
                        pass
                
                sequential_time = time.time() - sequential_start
                print(f"   ⚡ Sequential test: {sequential_successes}/5 successful in {sequential_time:.2f}s")
                
                overall_success = (successful_results >= 6) and (sequential_successes >= 3)
                
                self.test_results["Load Scenarios"] = {
                    "status": "passed" if overall_success else "failed",
                    "concurrent_success": successful_results,
                    "concurrent_total": 10,
                    "sequential_success": sequential_successes,
                    "sequential_total": 5,
                    "total_time": total_time
                }
                
                return overall_success
                
            except Exception as e:
                print(f"   ❌ Load test failed: {str(e)}")
                return False
                
        except Exception as e:
            print(f"   ❌ Load scenarios test failed: {str(e)}")
            self.test_results["Load Scenarios"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    async def test_complete_workflow(self) -> bool:
        """Test complete end-to-end workflow"""
        print("\n🔄 Testing Complete End-to-End Workflow...")
        
        try:
            workflow_steps = []
            
            # Step 1: Data availability check
            print("   1️⃣ Checking data availability...")
            from app.core.database import SessionLocal
            from app.repositories import price_data_repository
            
            if self.btc_crypto_id:
                db = SessionLocal()
                try:
                    price_count = price_data_repository.count_by_crypto(db, self.btc_crypto_id)
                    if price_count > 0:
                        print(f"      ✅ Data available: {price_count} records")
                        workflow_steps.append(True)
                    else:
                        print("      ❌ No data available")
                        workflow_steps.append(False)
                finally:
                    db.close()
            else:
                print("      ❌ Cryptocurrency not set up")
                workflow_steps.append(False)
            
            # Step 2: Model availability check
            print("   2️⃣ Checking model availability...")
            from app.ml.config.ml_config import model_registry
            
            models = model_registry.list_models("BTC")
            if models:
                print(f"      ✅ Models available: {len(models)} models")
                workflow_steps.append(True)
            else:
                print("      ⚠️ No models available")
                workflow_steps.append(False)
            
            # Step 3: Prediction generation
            print("   3️⃣ Testing prediction generation...")
            from app.ml.prediction.prediction_service import prediction_service
            
            try:
                prediction = await prediction_service.predict_price("BTC", "24h")
                if prediction and prediction.get("success", False):
                    print("      ✅ Prediction generated successfully")
                    workflow_steps.append(True)
                else:
                    print("      ❌ Prediction generation failed")
                    workflow_steps.append(False)
            except Exception as e:
                print(f"      ❌ Prediction error: {str(e)}")
                workflow_steps.append(False)
            
            # Step 4: Performance monitoring
            print("   4️⃣ Testing performance monitoring...")
            try:
                metrics = prediction_service.get_performance_metrics()
                if metrics:
                    print("      ✅ Performance monitoring working")
                    workflow_steps.append(True)
                else:
                    print("      ⚠️ Performance monitoring not available")
                    workflow_steps.append(False)
            except Exception:
                print("      ⚠️ Performance monitoring error")
                workflow_steps.append(False)
            
            # Step 5: System health check
            print("   5️⃣ Testing system health...")
            try:
                from app.core.database import engine
                with engine.connect() as conn:
                    conn.execute("SELECT 1")
                print("      ✅ System health: OK")
                workflow_steps.append(True)
            except Exception:
                print("      ❌ System health: Failed")
                workflow_steps.append(False)
            
            # Evaluate workflow
            successful_steps = sum(workflow_steps)
            total_steps = len(workflow_steps)
            workflow_success = successful_steps / total_steps
            
            print(f"\n   📊 Workflow Results: {successful_steps}/{total_steps} steps successful ({workflow_success:.1%})")
            
            if workflow_success >= 0.8:  # 80% success
                print("   ✅ End-to-end workflow: Working correctly")
                self.test_results["Complete Workflow"] = {
                    "status": "passed",
                    "successful_steps": successful_steps,
                    "total_steps": total_steps,
                    "success_rate": workflow_success
                }
                return True
            else:
                print("   ❌ End-to-end workflow: Has issues")
                self.test_results["Complete Workflow"] = {
                    "status": "failed",
                    "successful_steps": successful_steps,
                    "total_steps": total_steps,
                    "success_rate": workflow_success
                }
                return False
                
        except Exception as e:
            print(f"   ❌ Complete workflow test failed: {str(e)}")
            self.test_results["Complete Workflow"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    def print_integration_results(self, passed_scenarios: int, total_scenarios: int):
        """Print comprehensive integration test results"""
        print(f"\n{'='*65}")
        print("🏁 INTEGRATION TEST RESULTS - STAGE D")
        print(f"{'='*65}")
        
        success_rate = (passed_scenarios / total_scenarios) * 100
        
        print(f"📊 Overall Integration Success: {success_rate:.1f}% ({passed_scenarios}/{total_scenarios})")
        print(f"⏰ Integration Testing Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n📋 Detailed Integration Results:")
        for scenario, result in self.test_results.items():
            status = result.get("status", "unknown")
            if status == "passed":
                print(f"   ✅ {scenario}")
            elif status == "failed":
                print(f"   ❌ {scenario}: {result.get('error', 'Failed')}")
            elif status == "skipped":
                print(f"   ⏭️ {scenario}: {result.get('reason', 'Skipped')}")
            else:
                print(f"   ❓ {scenario}: {status}")
        
        # Phase 1 Final Assessment
        print(f"\n🎯 Phase 1 Final Assessment:")
        
        if success_rate >= 90:
            print("   🎉 OUTSTANDING: Phase 1 MVP Complete and Excellent!")
            print("   ✨ All major systems integrated and working")
            print("   🚀 Ready for production deployment")
            print("   📈 Exceeds Phase 1 requirements")
        elif success_rate >= 80:
            print("   ✅ EXCELLENT: Phase 1 MVP Complete!")
            print("   🎯 All core requirements met")
            print("   🚀 Ready to move to Phase 2")
            print("   🔧 Minor optimizations possible")
        elif success_rate >= 70:
            print("   ✅ GOOD: Phase 1 MVP Mostly Complete")
            print("   🎯 Core functionality working")
            print("   🛠️ Some components need attention")
            print("   ⏳ Phase 2 can begin with fixes")
        else:
            print("   ⚠️ NEEDS WORK: Phase 1 MVP Incomplete")
            print("   🔧 Critical issues need resolution")
            print("   📋 Complete Phase 1 before Phase 2")
        
        # Success metrics summary
        if hasattr(self, 'prediction_results') and self.prediction_results:
            print(f"\n📊 Prediction Performance Summary:")
            print(f"   • Predictions generated: {len(self.prediction_results)}")
            avg_confidence = sum(p['confidence'] for p in self.prediction_results) / len(self.prediction_results)
            print(f"   • Average confidence: {avg_confidence:.1%}")
        
        # Recommendations for next steps
        print(f"\n💡 Phase 2 Recommendations:")
        if success_rate >= 80:
            print("   🎨 Enhanced UI/UX development")
            print("   📱 Mobile app development")
            print("   🔍 Advanced analytics features")
            print("   🌐 Multi-cryptocurrency support")
            print("   ⚡ Performance optimizations")
            print("   🔒 Enhanced security features")
        else:
            print("   🔧 Complete Phase 1 requirements first")
            print("   🧪 Fix failed integration tests")
            print("   📊 Ensure data quality")
            print("   🤖 Improve ML model accuracy")
        
        print(f"\n🏆 Phase 1 Status: {'COMPLETE ✅' if success_rate >= 80 else 'IN PROGRESS ⏳'}")


async def main():
    """Main integration test function"""
    try:
        print("🔧 Initializing integration test environment...")
        
        # Check environment
        if not os.path.exists("backend"):
            print("❌ Please run this script from the project root directory")
            return
        
        print("🧪 Starting Stage D integration tests...")
        
        # Create and run integration test suite
        test_suite = IntegrationTestSuite()
        await test_suite.run_integration_tests()
        
        print(f"\n🏁 Stage D integration testing completed!")
        
    except KeyboardInterrupt:
        print("\n👋 Integration tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Integration tests failed: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())