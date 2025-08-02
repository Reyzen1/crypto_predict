# File: temp/performance_benchmark.py
# Performance Benchmark Suite for CryptoPredict MVP

import asyncio
import time
import sys
import os
import psutil
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Any, Optional
from decimal import Decimal
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

print("⚡ CryptoPredict MVP - Performance Benchmark Suite")
print("=" * 60)
print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()


class PerformanceBenchmark:
    """Comprehensive performance benchmark suite"""
    
    def __init__(self):
        self.results = {}
        self.system_info = self.get_system_info()
        
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmarking context"""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "platform": sys.platform,
                "python_version": sys.version,
                "process_id": os.getpid()
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all performance benchmarks"""
        
        print("🎯 System Information:")
        for key, value in self.system_info.items():
            if key != "python_version":
                print(f"   {key}: {value}")
        print()
        
        # Benchmark categories
        benchmark_categories = [
            ("Database Performance", self.benchmark_database_performance),
            ("ML Training Performance", self.benchmark_ml_training),
            ("ML Prediction Performance", self.benchmark_ml_prediction),
            ("API Response Time", self.benchmark_api_performance),
            ("Concurrent Operations", self.benchmark_concurrent_operations),
            ("Memory Usage", self.benchmark_memory_usage),
            ("System Resource Usage", self.benchmark_system_resources)
        ]
        
        total_benchmarks = len(benchmark_categories)
        completed_benchmarks = 0
        
        for i, (category_name, benchmark_function) in enumerate(benchmark_categories, 1):
            print(f"\n{'='*60}")
            print(f"📊 Benchmark {i}/{total_benchmarks}: {category_name}")
            print(f"{'='*60}")
            
            try:
                start_time = time.time()
                result = await benchmark_function()
                duration = time.time() - start_time
                
                result["benchmark_duration"] = duration
                result["category"] = category_name
                result["success"] = True
                
                self.results[category_name] = result
                completed_benchmarks += 1
                
                print(f"✅ {category_name} completed in {duration:.2f}s")
                
            except Exception as e:
                print(f"❌ {category_name} failed: {str(e)}")
                self.results[category_name] = {
                    "success": False,
                    "error": str(e),
                    "category": category_name
                }
            
            # Small delay between benchmarks
            await asyncio.sleep(1)
        
        # Generate final report
        return self.generate_benchmark_report(completed_benchmarks, total_benchmarks)
    
    async def benchmark_database_performance(self) -> Dict[str, Any]:
        """Benchmark database operations"""
        print("   🗄️ Testing database performance...")
        
        from app.core.database import SessionLocal, engine
        from app.repositories import cryptocurrency_repository, price_data_repository
        from app.schemas.cryptocurrency import CryptocurrencyCreate
        from app.schemas.price_data import PriceDataCreate
        
        results = {}
        
        # Test database connection speed
        connection_times = []
        for i in range(10):
            start_time = time.time()
            with engine.connect() as conn:
                conn.execute("SELECT 1").fetchone()
            connection_times.append((time.time() - start_time) * 1000)
        
        results["connection"] = {
            "avg_ms": statistics.mean(connection_times),
            "min_ms": min(connection_times),
            "max_ms": max(connection_times),
            "std_dev": statistics.stdev(connection_times) if len(connection_times) > 1 else 0
        }
        
        print(f"      🔗 Connection: {results['connection']['avg_ms']:.1f}ms avg")
        
        # Test query performance
        db = SessionLocal()
        try:
            # Setup test data if needed
            test_crypto = cryptocurrency_repository.get_by_symbol(db, "PERFTEST")
            if not test_crypto:
                crypto_create = CryptocurrencyCreate(
                    symbol="PERFTEST",
                    name="Performance Test Coin",
                    is_active=True
                )
                test_crypto = cryptocurrency_repository.create(db, obj_in=crypto_create)
            
            # Ensure some price data exists
            existing_count = price_data_repository.count_by_crypto(db, test_crypto.id)
            if existing_count < 100:
                # Create test price data
                base_time = datetime.now(timezone.utc) - timedelta(days=100)
                for i in range(100 - existing_count):
                    price_create = PriceDataCreate(
                        crypto_id=test_crypto.id,
                        price=Decimal(f"{45000 + i}"),
                        volume=Decimal("1000000"),
                        timestamp=base_time + timedelta(hours=i)
                    )
                    price_data_repository.create(db, obj_in=price_create)
            
            # Test different query sizes
            query_tests = [
                ("Small Query (10 records)", 10),
                ("Medium Query (100 records)", 100),
                ("Large Query (500 records)", 500),
                ("XL Query (1000 records)", 1000)
            ]
            
            query_results = {}
            for test_name, limit in query_tests:
                query_times = []
                for _ in range(5):  # 5 iterations per test
                    start_time = time.time()
                    data = price_data_repository.get_recent_prices(db, test_crypto.id, limit=limit)
                    query_times.append((time.time() - start_time) * 1000)
                
                query_results[test_name] = {
                    "avg_ms": statistics.mean(query_times),
                    "min_ms": min(query_times),
                    "max_ms": max(query_times),
                    "records_returned": len(data) if 'data' in locals() else 0
                }
                
                print(f"      📊 {test_name}: {query_results[test_name]['avg_ms']:.1f}ms avg")
            
            results["queries"] = query_results
            
        finally:
            db.close()
        
        return results
    
    async def benchmark_ml_training(self) -> Dict[str, Any]:
        """Benchmark ML training performance"""
        print("   🤖 Testing ML training performance...")
        
        from app.ml.training.training_service import training_service
        from app.core.database import SessionLocal
        from app.repositories import cryptocurrency_repository, price_data_repository
        
        results = {}
        
        # Test different model sizes
        model_configs = [
            {
                "name": "Tiny Model",
                "config": {
                    "epochs": 2,
                    "batch_size": 16,
                    "lstm_units": [5],
                    "sequence_length": 10
                }
            },
            {
                "name": "Small Model",
                "config": {
                    "epochs": 3,
                    "batch_size": 32,
                    "lstm_units": [10, 5],
                    "sequence_length": 20
                }
            },
            {
                "name": "Medium Model",
                "config": {
                    "epochs": 5,
                    "batch_size": 32,
                    "lstm_units": [20, 15, 10],
                    "sequence_length": 30
                }
            }
        ]
        
        # Check if we have sufficient data
        db = SessionLocal()
        try:
            test_crypto = cryptocurrency_repository.get_by_symbol(db, "PERFTEST")
            if test_crypto:
                data_count = price_data_repository.count_by_crypto(db, test_crypto.id)
                
                if data_count >= 100:
                    training_results = {}
                    
                    for model_config in model_configs:
                        model_name = model_config["name"]
                        print(f"      🏗️ Training {model_name}...")
                        
                        start_time = time.time()
                        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                        
                        try:
                            training_result = await training_service.train_model(
                                crypto_symbol="PERFTEST",
                                model_type="lstm",
                                training_config=model_config["config"],
                                data_days_back=50,
                                force_retrain=True
                            )
                            
                            duration = time.time() - start_time
                            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                            memory_used = end_memory - start_memory
                            
                            if training_result.get("success", False):
                                training_results[model_name] = {
                                    "duration_seconds": duration,
                                    "memory_usage_mb": memory_used,
                                    "epochs": model_config["config"]["epochs"],
                                    "lstm_units": len(model_config["config"]["lstm_units"]),
                                    "success": True
                                }
                                print(f"         ✅ {duration:.1f}s, {memory_used:.1f}MB")
                            else:
                                training_results[model_name] = {
                                    "success": False,
                                    "error": training_result.get("error", "Unknown error")
                                }
                                print(f"         ❌ Failed: {training_result.get('error', 'Unknown error')}")
                        
                        except Exception as e:
                            training_results[model_name] = {
                                "success": False,
                                "error": str(e)
                            }
                            print(f"         ❌ Exception: {str(e)}")
                    
                    results["training"] = training_results
                    
                else:
                    results["training"] = {"skipped": f"Insufficient data: {data_count} records"}
                    print("      ⚠️ Skipped training tests - insufficient data")
            else:
                results["training"] = {"skipped": "No test cryptocurrency found"}
                print("      ⚠️ Skipped training tests - no test crypto")
                
        finally:
            db.close()
        
        return results
    
    async def benchmark_ml_prediction(self) -> Dict[str, Any]:
        """Benchmark ML prediction performance"""
        print("   🔮 Testing ML prediction performance...")
        
        from app.ml.prediction.prediction_service import prediction_service
        from app.ml.config.ml_config import model_registry
        
        results = {}
        
        # Check if models are available
        models = model_registry.list_models("PERFTEST")
        if models:
            # Test single prediction performance
            single_prediction_times = []
            for i in range(10):
                start_time = time.time()
                
                try:
                    result = await prediction_service.predict_price(
                        crypto_symbol="PERFTEST",
                        timeframe="1h",
                        force_refresh=(i == 0)  # Force refresh only on first call
                    )
                    
                    prediction_time = (time.time() - start_time) * 1000
                    single_prediction_times.append(prediction_time)
                    
                    if not result.get("success", False):
                        print(f"         ⚠️ Prediction {i+1} failed")
                
                except Exception as e:
                    print(f"         ❌ Prediction {i+1} exception: {str(e)}")
            
            if single_prediction_times:
                results["single_prediction"] = {
                    "avg_ms": statistics.mean(single_prediction_times),
                    "min_ms": min(single_prediction_times),
                    "max_ms": max(single_prediction_times),
                    "std_dev": statistics.stdev(single_prediction_times) if len(single_prediction_times) > 1 else 0,
                    "count": len(single_prediction_times)
                }
                print(f"      ⚡ Single prediction: {results['single_prediction']['avg_ms']:.1f}ms avg")
            
            # Test batch prediction performance
            batch_sizes = [1, 3, 5]
            batch_results = {}
            
            for batch_size in batch_sizes:
                crypto_symbols = ["PERFTEST"] * batch_size
                
                start_time = time.time()
                
                try:
                    batch_result = await prediction_service.batch_predict(
                        crypto_symbols=crypto_symbols,
                        timeframe="1h"
                    )
                    
                    batch_time = (time.time() - start_time) * 1000
                    time_per_prediction = batch_time / batch_size
                    
                    batch_results[f"batch_{batch_size}"] = {
                        "total_time_ms": batch_time,
                        "time_per_prediction_ms": time_per_prediction,
                        "success": batch_result.get("success", False),
                        "successful_predictions": batch_result.get("successful_predictions", 0)
                    }
                    
                    print(f"      📦 Batch {batch_size}: {batch_time:.1f}ms total ({time_per_prediction:.1f}ms each)")
                
                except Exception as e:
                    batch_results[f"batch_{batch_size}"] = {
                        "error": str(e),
                        "success": False
                    }
                    print(f"      ❌ Batch {batch_size} failed: {str(e)}")
            
            results["batch_prediction"] = batch_results
            
        else:
            results["prediction"] = {"skipped": "No trained models available"}
            print("      ⚠️ Skipped prediction tests - no trained models")
        
        return results
    
    async def benchmark_api_performance(self) -> Dict[str, Any]:
        """Benchmark API response times"""
        print("   🌐 Testing API performance...")
        
        # This would typically use the test client, but for simplicity
        # we'll test the service layer directly
        results = {
            "note": "API performance tested via service layer",
            "simulated_endpoints": {}
        }
        
        # Simulate API endpoint response times by testing service methods directly
        from app.ml.prediction.prediction_service import prediction_service
        from app.ml.config.ml_config import model_registry
        
        # Test service method response times
        service_tests = [
            ("get_performance_metrics", prediction_service.get_performance_metrics),
            ("get_system_stats", prediction_service.get_system_stats)
        ]
        
        for test_name, method in service_tests:
            response_times = []
            
            for i in range(5):
                start_time = time.time()
                
                try:
                    await method()
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                
                except Exception as e:
                    print(f"         ⚠️ {test_name} call {i+1} failed: {str(e)}")
            
            if response_times:
                results["simulated_endpoints"][test_name] = {
                    "avg_ms": statistics.mean(response_times),
                    "min_ms": min(response_times),
                    "max_ms": max(response_times),
                    "count": len(response_times)
                }
                print(f"      🔗 {test_name}: {results['simulated_endpoints'][test_name]['avg_ms']:.1f}ms avg")
        
        return results
    
    async def benchmark_concurrent_operations(self) -> Dict[str, Any]:
        """Benchmark concurrent operation performance"""
        print("   🔄 Testing concurrent operations...")
        
        from app.ml.prediction.prediction_service import prediction_service
        from app.ml.config.ml_config import model_registry
        
        results = {}
        
        # Check if models are available
        models = model_registry.list_models("PERFTEST")
        if models:
            # Test concurrent predictions
            concurrent_loads = [2, 5, 10]
            
            for load in concurrent_loads:
                print(f"      ⚡ Testing {load} concurrent predictions...")
                
                async def make_prediction():
                    return await prediction_service.predict_price(
                        crypto_symbol="PERFTEST",
                        timeframe="1h"
                    )
                
                start_time = time.time()
                
                # Create concurrent tasks
                tasks = [make_prediction() for _ in range(load)]
                results_list = await asyncio.gather(*tasks, return_exceptions=True)
                
                total_time = (time.time() - start_time) * 1000
                
                # Analyze results
                successful = sum(1 for r in results_list if not isinstance(r, Exception) and r.get("success", False))
                failed = load - successful
                avg_time = total_time / load
                
                results[f"concurrent_{load}"] = {
                    "total_time_ms": total_time,
                    "avg_time_per_operation_ms": avg_time,
                    "successful_operations": successful,
                    "failed_operations": failed,
                    "success_rate": (successful / load) * 100
                }
                
                print(f"         📊 {successful}/{load} successful, {total_time:.1f}ms total, {avg_time:.1f}ms avg")
        
        else:
            results["concurrent"] = {"skipped": "No trained models available"}
            print("      ⚠️ Skipped concurrent tests - no trained models")
        
        return results
    
    async def benchmark_memory_usage(self) -> Dict[str, Any]:
        """Benchmark memory usage patterns"""
        print("   💾 Testing memory usage...")
        
        import gc
        
        # Get baseline memory
        gc.collect()
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        results = {
            "baseline_memory_mb": baseline_memory
        }
        
        print(f"      📊 Baseline memory: {baseline_memory:.1f}MB")
        
        # Test memory usage during various operations
        from app.ml.prediction.prediction_service import prediction_service
        from app.ml.config.ml_config import model_registry
        
        models = model_registry.list_models("PERFTEST")
        if models:
            # Memory usage during predictions
            memory_samples = []
            
            for i in range(10):
                try:
                    await prediction_service.predict_price("PERFTEST", "1h")
                    current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    memory_increase = current_memory - baseline_memory
                    memory_samples.append(memory_increase)
                
                except Exception:
                    pass
            
            if memory_samples:
                results["prediction_memory_usage"] = {
                    "avg_increase_mb": statistics.mean(memory_samples),
                    "max_increase_mb": max(memory_samples),
                    "min_increase_mb": min(memory_samples),
                    "samples": len(memory_samples)
                }
                
                print(f"      🔮 Prediction memory: +{results['prediction_memory_usage']['avg_increase_mb']:.1f}MB avg")
            
            # Test for memory leaks
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            for i in range(20):
                try:
                    await prediction_service.predict_price("PERFTEST", "1h")
                except Exception:
                    pass
            
            gc.collect()
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_leak = final_memory - initial_memory
            
            results["memory_leak_test"] = {
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "memory_increase_mb": memory_leak,
                "operations_performed": 20
            }
            
            print(f"      🔍 Memory leak test: +{memory_leak:.1f}MB after 20 operations")
            
            if memory_leak > 50:  # More than 50MB increase
                print("         ⚠️ Potential memory leak detected")
            else:
                print("         ✅ No significant memory leak")
        
        return results
    
    async def benchmark_system_resources(self) -> Dict[str, Any]:
        """Benchmark overall system resource usage"""
        print("   🖥️ Testing system resource usage...")
        
        # Monitor system resources during operations
        initial_cpu = psutil.cpu_percent(interval=1)
        initial_memory = psutil.virtual_memory().percent
        
        results = {
            "initial_cpu_percent": initial_cpu,
            "initial_memory_percent": initial_memory
        }
        
        print(f"      📊 Initial CPU: {initial_cpu:.1f}%, Memory: {initial_memory:.1f}%")
        
        # Perform intensive operations and monitor
        from app.ml.prediction.prediction_service import prediction_service
        from app.ml.config.ml_config import model_registry
        
        models = model_registry.list_models("PERFTEST")
        if models:
            cpu_samples = []
            memory_samples = []
            
            # Perform 20 predictions while monitoring resources
            for i in range(20):
                try:
                    await prediction_service.predict_price("PERFTEST", "1h")
                    
                    # Sample system resources
                    cpu_samples.append(psutil.cpu_percent())
                    memory_samples.append(psutil.virtual_memory().percent)
                    
                    await asyncio.sleep(0.1)  # Small delay
                
                except Exception:
                    pass
            
            if cpu_samples:
                results["during_operations"] = {
                    "avg_cpu_percent": statistics.mean(cpu_samples),
                    "max_cpu_percent": max(cpu_samples),
                    "avg_memory_percent": statistics.mean(memory_samples),
                    "max_memory_percent": max(memory_samples)
                }
                
                print(f"      ⚡ During operations - CPU: {results['during_operations']['avg_cpu_percent']:.1f}% avg, "
                      f"Memory: {results['during_operations']['avg_memory_percent']:.1f}% avg")
        
        # Final resource check
        final_cpu = psutil.cpu_percent(interval=1)
        final_memory = psutil.virtual_memory().percent
        
        results["final_cpu_percent"] = final_cpu
        results["final_memory_percent"] = final_memory
        
        print(f"      📈 Final CPU: {final_cpu:.1f}%, Memory: {final_memory:.1f}%")
        
        return results
    
    def generate_benchmark_report(self, completed_benchmarks: int, total_benchmarks: int) -> Dict[str, Any]:
        """Generate comprehensive benchmark report"""
        
        completion_rate = (completed_benchmarks / total_benchmarks) * 100
        
        print(f"\n{'='*60}")
        print("📊 PERFORMANCE BENCHMARK REPORT")
        print(f"{'='*60}")
        
        print(f"🎯 Benchmark Summary:")
        print(f"   Completion Rate: {completion_rate:.1f}% ({completed_benchmarks}/{total_benchmarks})")
        print(f"   System: {self.system_info.get('cpu_count', 'Unknown')} CPU cores, "
               f"{self.system_info.get('memory_total_gb', 0):.1f}GB RAM")
        print(f"   Platform: {self.system_info.get('platform', 'Unknown')}")
        
        # Performance summary
        print(f"\n📈 Performance Highlights:")
        
        # Database performance
        if "Database Performance" in self.results:
            db_result = self.results["Database Performance"]
            if "connection" in db_result:
                conn_time = db_result["connection"]["avg_ms"]
                print(f"   🗄️ Database Connection: {conn_time:.1f}ms avg")
        
        # ML training performance
        if "ML Training Performance" in self.results:
            ml_result = self.results["ML Training Performance"]
            if "training" in ml_result and isinstance(ml_result["training"], dict):
                successful_trainings = sum(1 for v in ml_result["training"].values() 
                                         if isinstance(v, dict) and v.get("success", False))
                print(f"   🤖 ML Training: {successful_trainings} successful models")
        
        # Prediction performance
        if "ML Prediction Performance" in self.results:
            pred_result = self.results["ML Prediction Performance"]
            if "single_prediction" in pred_result:
                pred_time = pred_result["single_prediction"]["avg_ms"]
                print(f"   🔮 Prediction Speed: {pred_time:.1f}ms avg")
        
        # Concurrent performance
        if "Concurrent Operations" in self.results:
            conc_result = self.results["Concurrent Operations"]
            concurrent_keys = [k for k in conc_result.keys() if k.startswith("concurrent_")]
            if concurrent_keys:
                # Get highest successful concurrent load
                max_concurrent = 0
                for key in concurrent_keys:
                    if conc_result[key].get("success_rate", 0) >= 80:  # 80% success rate
                        load = int(key.split("_")[1])
                        max_concurrent = max(max_concurrent, load)
                
                if max_concurrent > 0:
                    print(f"   🔄 Concurrent Capacity: {max_concurrent} operations")
        
        # Memory efficiency
        if "Memory Usage" in self.results:
            mem_result = self.results["Memory Usage"]
            if "prediction_memory_usage" in mem_result:
                avg_memory = mem_result["prediction_memory_usage"]["avg_increase_mb"]
                print(f"   💾 Memory Efficiency: +{avg_memory:.1f}MB per prediction")
        
        # Performance rating
        print(f"\n🏆 Performance Rating:")
        
        performance_score = 0
        max_score = 0
        
        # Database performance score (max 20 points)
        if "Database Performance" in self.results:
            db_result = self.results["Database Performance"]
            if "connection" in db_result:
                conn_time = db_result["connection"]["avg_ms"]
                if conn_time < 50:
                    performance_score += 20
                elif conn_time < 100:
                    performance_score += 15
                elif conn_time < 200:
                    performance_score += 10
                else:
                    performance_score += 5
            max_score += 20
        
        # Prediction performance score (max 30 points)
        if "ML Prediction Performance" in self.results:
            pred_result = self.results["ML Prediction Performance"]
            if "single_prediction" in pred_result:
                pred_time = pred_result["single_prediction"]["avg_ms"]
                if pred_time < 1000:  # Less than 1 second
                    performance_score += 30
                elif pred_time < 2000:  # Less than 2 seconds
                    performance_score += 25
                elif pred_time < 5000:  # Less than 5 seconds
                    performance_score += 20
                else:
                    performance_score += 10
            max_score += 30
        
        # Concurrent performance score (max 25 points)
        if "Concurrent Operations" in self.results:
            conc_result = self.results["Concurrent Operations"]
            max_successful_load = 0
            
            for key, value in conc_result.items():
                if key.startswith("concurrent_") and isinstance(value, dict):
                    if value.get("success_rate", 0) >= 80:
                        load = int(key.split("_")[1])
                        max_successful_load = max(max_successful_load, load)
            
            if max_successful_load >= 10:
                performance_score += 25
            elif max_successful_load >= 5:
                performance_score += 20
            elif max_successful_load >= 2:
                performance_score += 15
            else:
                performance_score += 5
            max_score += 25
        
        # Memory efficiency score (max 25 points)
        if "Memory Usage" in self.results:
            mem_result = self.results["Memory Usage"]
            if "memory_leak_test" in mem_result:
                memory_increase = mem_result["memory_leak_test"]["memory_increase_mb"]
                if memory_increase < 10:  # Less than 10MB increase
                    performance_score += 25
                elif memory_increase < 25:  # Less than 25MB
                    performance_score += 20
                elif memory_increase < 50:  # Less than 50MB
                    performance_score += 15
                else:
                    performance_score += 5
            max_score += 25
        
        # Calculate final performance rating
        if max_score > 0:
            performance_percentage = (performance_score / max_score) * 100
            
            if performance_percentage >= 90:
                rating = "EXCELLENT"
                rating_emoji = "🌟"
            elif performance_percentage >= 80:
                rating = "VERY GOOD"
                rating_emoji = "⭐"
            elif performance_percentage >= 70:
                rating = "GOOD"
                rating_emoji = "✅"
            elif performance_percentage >= 60:
                rating = "FAIR"
                rating_emoji = "⚠️"
            else:
                rating = "NEEDS IMPROVEMENT"
                rating_emoji = "❌"
            
            print(f"   {rating_emoji} Overall Rating: {rating} ({performance_percentage:.1f}%)")
            print(f"   📊 Performance Score: {performance_score}/{max_score}")
        
        # Recommendations
        print(f"\n💡 Performance Recommendations:")
        
        if completion_rate < 100:
            print("   🔧 Fix benchmark failures before optimization")
        
        # Database recommendations
        if "Database Performance" in self.results:
            db_result = self.results["Database Performance"]
            if "connection" in db_result and db_result["connection"]["avg_ms"] > 100:
                print("   🗄️ Consider database connection pooling optimization")
        
        # Prediction recommendations
        if "ML Prediction Performance" in self.results:
            pred_result = self.results["ML Prediction Performance"]
            if "single_prediction" in pred_result and pred_result["single_prediction"]["avg_ms"] > 2000:
                print("   🔮 Consider model optimization or caching improvements")
        
        # Memory recommendations
        if "Memory Usage" in self.results:
            mem_result = self.results["Memory Usage"]
            if "memory_leak_test" in mem_result and mem_result["memory_leak_test"]["memory_increase_mb"] > 50:
                print("   💾 Investigate potential memory leaks")
        
        # Concurrent recommendations
        if "Concurrent Operations" in self.results:
            print("   🔄 Consider implementing connection pooling for better concurrency")
        
        if performance_percentage >= 80:
            print("   🚀 Performance is good - focus on feature development")
        else:
            print("   ⚡ Focus on performance optimization before adding features")
        
        # Save detailed benchmark report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self.system_info,
            "completion_rate": completion_rate,
            "performance_score": performance_score if max_score > 0 else None,
            "max_score": max_score if max_score > 0 else None,
            "performance_percentage": performance_percentage if max_score > 0 else None,
            "rating": rating if max_score > 0 else "INCOMPLETE",
            "benchmark_results": self.results,
            "completed_benchmarks": completed_benchmarks,
            "total_benchmarks": total_benchmarks
        }
        
        # Save report
        try:
            os.makedirs("temp/reports", exist_ok=True)
            report_filename = f"temp/reports/performance_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            print(f"\n📄 Detailed benchmark report saved: {report_filename}")
        except Exception as e:
            print(f"\n⚠️ Could not save benchmark report: {str(e)}")
        
        print(f"\n🏁 Performance Benchmark Complete!")
        
        return report_data


async def main():
    """Main function to run performance benchmarks"""
    try:
        # Check environment
        if not os.path.exists("backend"):
            print("❌ Please run this script from the project root directory")
            print("📁 Current directory:", os.getcwd())
            return 1
        
        # Initialize and run benchmarks
        benchmark = PerformanceBenchmark()
        final_report = benchmark.run_all_benchmarks()
        
        await final_report
        
        print("\n🎉 Performance benchmarking completed!")
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Performance benchmark interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Performance benchmark failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)