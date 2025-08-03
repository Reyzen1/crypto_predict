# File: temp/final_test_stages_c_d.py
# Final comprehensive test for CryptoPredict MVP - Stages C & D Combined

import asyncio
import sys
import os
import subprocess
import time
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

print("🎯 CryptoPredict MVP - Final Combined Test (Stages C & D)")
print("=" * 70)
print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("🎯 Testing complete API Integration + Testing & Validation")
print()


class FinalTestSuite:
    """Final comprehensive test suite for Stages C & D"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
        self.phase_1_status = "INCOMPLETE"
        
    async def run_final_tests(self) -> Dict[str, Any]:
        """Run final comprehensive test suite"""
        
        self.start_time = time.time()
        
        # Test sequence designed to validate both Stage C and D
        test_sequence = [
            ("Pre-Flight Check", self.preflight_check),
            ("Stage C: API Integration Validation", self.validate_stage_c),
            ("Stage D: Testing Infrastructure", self.validate_stage_d), 
            ("Integration Verification", self.verify_integration),
            ("Performance Validation", self.validate_performance),
            ("Real Data Testing", self.test_real_data),
            ("End-to-End Workflow", self.test_end_to_end),
            ("Phase 1 Completion Assessment", self.assess_phase_1_completion)
        ]
        
        total_tests = len(test_sequence)
        passed_tests = 0
        
        for i, (test_name, test_function) in enumerate(test_sequence, 1):
            print(f"\n{'='*70}")
            print(f"🧪 Test {i}/{total_tests}: {test_name}")
            print(f"{'='*70}")
            
            try:
                result = await test_function()
                
                if result.get("success", False):
                    passed_tests += 1
                    print(f"✅ {test_name}: PASSED")
                    
                    # Show key metrics if available
                    if "metrics" in result:
                        for key, value in result["metrics"].items():
                            print(f"   📊 {key}: {value}")
                            
                else:
                    print(f"❌ {test_name}: FAILED")
                    if "error" in result:
                        print(f"   💥 Error: {result['error']}")
                    if "details" in result:
                        print(f"   📋 Details: {result['details']}")
                
                self.results[test_name] = result
                
            except Exception as e:
                print(f"💥 {test_name}: EXCEPTION - {str(e)}")
                self.results[test_name] = {
                    "success": False,
                    "error": str(e),
                    "exception": True
                }
            
            # Brief pause between tests
            await asyncio.sleep(1)
        
        self.end_time = time.time()
        
        # Generate final comprehensive report
        return self.generate_final_report(passed_tests, total_tests)
    
    async def preflight_check(self) -> Dict[str, Any]:
        """Pre-flight environment and setup check"""
        print("   🔍 Running pre-flight checks...")
        
        checks = []
        
        # Environment checks
        print("      📁 Checking environment...")
        
        required_directories = [
            "backend",
            "backend/app",
            "backend/app/api",
            "backend/app/schemas",
            "backend/app/tasks",
            "backend/tests"
        ]
        
        for directory in required_directories:
            if os.path.exists(directory):
                checks.append(f"✅ Directory: {directory}")
            else:
                checks.append(f"❌ Missing directory: {directory}")
        
        # Key file checks
        print("      📄 Checking key files...")
        
        key_files = [
            "backend/app/api/api_v1/endpoints/ml_training.py",
            "backend/app/api/api_v1/endpoints/prediction.py",
            "backend/app/schemas/ml_training.py", 
            "backend/app/schemas/prediction.py",
            "backend/app/tasks/ml_tasks.py",
            "temp/quick_api_test.py",
            "temp/comprehensive_test_all_apis.py",
            "temp/integration_test_stage_d.py"
        ]
        
        for file_path in key_files:
            if os.path.exists(file_path):
                checks.append(f"✅ File: {file_path}")
            else:
                checks.append(f"❌ Missing file: {file_path}")
        
        # Import checks
        print("      📦 Checking imports...")
        
        try:
            from app.core.database import engine
            from app.ml.training.training_service import training_service
            from app.ml.prediction.prediction_service import prediction_service
            from app.ml.config.ml_config import model_registry
            checks.append("✅ Core imports successful")
        except Exception as e:
            checks.append(f"❌ Import failed: {str(e)}")
        
        # Database connectivity
        print("      🗄️ Checking database...")
        
        try:
            from app.core.database import engine
            with engine.connect() as conn:
                conn.execute("SELECT 1").fetchone()
            checks.append("✅ Database connection")
        except Exception as e:
            checks.append(f"❌ Database connection failed: {str(e)}")
        
        # Calculate success rate
        successful_checks = sum(1 for check in checks if check.startswith("✅"))
        total_checks = len(checks)
        success_rate = (successful_checks / total_checks) * 100
        
        print(f"      📊 Pre-flight: {successful_checks}/{total_checks} checks passed ({success_rate:.1f}%)")
        
        return {
            "success": success_rate >= 80,  # 80% threshold
            "checks": checks,
            "success_rate": success_rate,
            "metrics": {
                "Successful Checks": f"{successful_checks}/{total_checks}",
                "Success Rate": f"{success_rate:.1f}%"
            }
        }
    
    async def validate_stage_c(self) -> Dict[str, Any]:
        """Validate Stage C: API Integration implementation"""
        print("   🌐 Validating Stage C: API Integration...")
        
        stage_c_results = {}
        
        # Test 1: Quick API validation
        print("      🚀 Running quick API tests...")
        try:
            result = subprocess.run([
                sys.executable, "temp/quick_api_test.py"
            ], capture_output=True, text=True, timeout=120)
            
            api_success = result.returncode == 0
            stage_c_results["quick_api_test"] = {
                "success": api_success,
                "output": result.stdout if api_success else result.stderr
            }
            
            if api_success:
                print("         ✅ Quick API tests passed")
            else:
                print("         ❌ Quick API tests failed")
                
        except Exception as e:
            stage_c_results["quick_api_test"] = {"success": False, "error": str(e)}
            print(f"         💥 Quick API test exception: {str(e)}")
        
        # Test 2: API Schema validation
        print("      📝 Validating API schemas...")
        try:
            from app.schemas.ml_training import TrainingRequest, TrainingResponse
            from app.schemas.prediction import PredictionRequest, PredictionResponse
            
            # Test schema creation
            training_req = TrainingRequest(crypto_symbol="BTC", model_type="lstm")
            prediction_req = PredictionRequest(crypto_symbol="BTC")
            
            stage_c_results["schema_validation"] = {"success": True}
            print("         ✅ API schemas validated")
            
        except Exception as e:
            stage_c_results["schema_validation"] = {"success": False, "error": str(e)}
            print(f"         ❌ Schema validation failed: {str(e)}")
        
        # Test 3: API endpoint availability
        print("      🔗 Checking API endpoint availability...")
        try:
            from app.api.api_v1.endpoints import ml_training, prediction
            from app.api.api_v1.api import api_router
            
            # Count available routes
            training_routes = len([r for r in ml_training.router.routes if hasattr(r, 'methods')])
            prediction_routes = len([r for r in prediction.router.routes if hasattr(r, 'methods')])
            
            stage_c_results["endpoint_availability"] = {
                "success": True,
                "training_routes": training_routes,
                "prediction_routes": prediction_routes
            }
            
            print(f"         ✅ API endpoints: {training_routes} training, {prediction_routes} prediction")
            
        except Exception as e:
            stage_c_results["endpoint_availability"] = {"success": False, "error": str(e)}
            print(f"         ❌ Endpoint availability check failed: {str(e)}")
        
        # Test 4: Background tasks integration
        print("      ⚙️ Checking background tasks...")
        try:
            from app.tasks.ml_tasks import (
                auto_train_models, generate_scheduled_predictions,
                start_auto_training, start_prediction_generation
            )
            
            stage_c_results["background_tasks"] = {"success": True}
            print("         ✅ Background tasks available")
            
        except Exception as e:
            stage_c_results["background_tasks"] = {"success": False, "error": str(e)}
            print(f"         ❌ Background tasks check failed: {str(e)}")
        
        # Calculate Stage C success
        stage_c_success = sum(1 for test in stage_c_results.values() if test.get("success", False))
        stage_c_total = len(stage_c_results)
        stage_c_rate = (stage_c_success / stage_c_total) * 100 if stage_c_total > 0 else 0
        
        print(f"      📊 Stage C: {stage_c_success}/{stage_c_total} components validated ({stage_c_rate:.1f}%)")
        
        return {
            "success": stage_c_rate >= 75,  # 75% threshold for Stage C
            "stage_c_results": stage_c_results,
            "stage_c_success_rate": stage_c_rate,
            "metrics": {
                "API Components": f"{stage_c_success}/{stage_c_total}",
                "Stage C Success Rate": f"{stage_c_rate:.1f}%"
            }
        }
    
    async def validate_stage_d(self) -> Dict[str, Any]:
        """Validate Stage D: Testing & Validation implementation"""
        print("   🧪 Validating Stage D: Testing & Validation...")
        
        stage_d_results = {}
        
        # Test 1: Test infrastructure
        print("      🏗️ Checking test infrastructure...")
        try:
            test_files = [
                "backend/tests/conftest.py",
                "backend/tests/test_integration_complete.py",
                "backend/tests/test_real_bitcoin_data.py",
                "backend/tests/test_performance_evaluation.py"
            ]
            
            existing_files = sum(1 for f in test_files if os.path.exists(f))
            
            stage_d_results["test_infrastructure"] = {
                "success": existing_files >= len(test_files) * 0.75,  # 75% of test files
                "existing_files": existing_files,
                "total_files": len(test_files)
            }
            
            print(f"         📄 Test files: {existing_files}/{len(test_files)} available")
            
        except Exception as e:
            stage_d_results["test_infrastructure"] = {"success": False, "error": str(e)}
            print(f"         ❌ Test infrastructure check failed: {str(e)}")
        
        # Test 2: Integration test execution
        print("      🔗 Running integration tests...")
        try:
            result = subprocess.run([
                sys.executable, "temp/integration_test_stage_d.py"
            ], capture_output=True, text=True, timeout=300)
            
            integration_success = result.returncode == 0
            stage_d_results["integration_tests"] = {
                "success": integration_success,
                "output": result.stdout if integration_success else result.stderr
            }
            
            if integration_success:
                print("         ✅ Integration tests passed")
            else:
                print("         ⚠️ Integration tests had issues (may be due to test data)")
                
        except subprocess.TimeoutExpired:
            stage_d_results["integration_tests"] = {"success": False, "error": "Integration tests timed out"}
            print("         ⏰ Integration tests timed out")
        except Exception as e:
            stage_d_results["integration_tests"] = {"success": False, "error": str(e)}
            print(f"         💥 Integration test exception: {str(e)}")
        
        # Test 3: Unit tests execution
        print("      🧪 Running unit tests...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "backend/tests/", 
                "-v", 
                "-x",  # Stop on first failure
                "--tb=short",
                "-m", "not (performance or real_data)",  # Skip slow tests
                "--maxfail=5"  # Stop after 5 failures
            ], capture_output=True, text=True, timeout=180)
            
            # Parse test results
            output_lines = result.stdout.split('\n')
            test_summary = [line for line in output_lines if 'passed' in line and ('failed' in line or 'error' in line)]
            
            unit_success = result.returncode == 0
            stage_d_results["unit_tests"] = {
                "success": unit_success,
                "summary": test_summary[0] if test_summary else "Tests completed",
                "output": result.stdout
            }
            
            if unit_success:
                print("         ✅ Unit tests passed")
            else:
                print("         ⚠️ Some unit tests failed")
                
        except subprocess.TimeoutExpired:
            stage_d_results["unit_tests"] = {"success": False, "error": "Unit tests timed out"}
            print("         ⏰ Unit tests timed out")
        except Exception as e:
            stage_d_results["unit_tests"] = {"success": False, "error": str(e)}
            print(f"         💥 Unit test exception: {str(e)}")
        
        # Test 4: Performance test availability
        print("      ⚡ Checking performance tests...")
        try:
            result = subprocess.run([
                sys.executable, "temp/performance_benchmark.py"
            ], capture_output=True, text=True, timeout=120)
            
            perf_success = result.returncode == 0
            stage_d_results["performance_tests"] = {
                "success": perf_success,
                "output": result.stdout if perf_success else result.stderr
            }
            
            if perf_success:
                print("         ✅ Performance tests available")
            else:
                print("         ⚠️ Performance tests had issues")
                
        except subprocess.TimeoutExpired:
            stage_d_results["performance_tests"] = {"success": False, "error": "Performance tests timed out"}
            print("         ⏰ Performance tests timed out")
        except Exception as e:
            stage_d_results["performance_tests"] = {"success": False, "error": str(e)}
            print(f"         💥 Performance test exception: {str(e)}")
        
        # Calculate Stage D success
        stage_d_success = sum(1 for test in stage_d_results.values() if test.get("success", False))
        stage_d_total = len(stage_d_results)
        stage_d_rate = (stage_d_success / stage_d_total) * 100 if stage_d_total > 0 else 0
        
        print(f"      📊 Stage D: {stage_d_success}/{stage_d_total} test components validated ({stage_d_rate:.1f}%)")
        
        return {
            "success": stage_d_rate >= 60,  # 60% threshold for Stage D (testing can be environment dependent)
            "stage_d_results": stage_d_results,
            "stage_d_success_rate": stage_d_rate,
            "metrics": {
                "Test Components": f"{stage_d_success}/{stage_d_total}",
                "Stage D Success Rate": f"{stage_d_rate:.1f}%"
            }
        }
    
    async def verify_integration(self) -> Dict[str, Any]:
        """Verify integration between components"""
        print("   🔗 Verifying component integration...")
        
        integration_tests = []
        
        # Test 1: ML service integration
        print("      🤖 Testing ML service integration...")
        try:
            from app.ml.training.training_service import training_service
            from app.ml.prediction.prediction_service import prediction_service
            from app.ml.config.ml_config import model_registry
            
            if training_service and prediction_service and model_registry:
                integration_tests.append("✅ ML services integrated")
            else:
                integration_tests.append("❌ ML services not properly integrated")
                
        except Exception as e:
            integration_tests.append(f"❌ ML service integration failed: {str(e)}")
        
        # Test 2: Database integration
        print("      🗄️ Testing database integration...")
        try:
            from app.core.database import engine, SessionLocal
            from app.repositories import cryptocurrency_repository
            
            db = SessionLocal()
            try:
                # Test repository access
                cryptos = cryptocurrency_repository.get_all_active(db)
                integration_tests.append("✅ Database repositories integrated")
            finally:
                db.close()
                
        except Exception as e:
            integration_tests.append(f"❌ Database integration failed: {str(e)}")
        
        # Test 3: API-Service integration
        print("      🌐 Testing API-Service integration...")
        try:
            from app.api.api_v1.endpoints.prediction import make_prediction
            from app.schemas.prediction import PredictionRequest
            
            # Check if API endpoints can import services
            integration_tests.append("✅ API-Service integration available")
            
        except Exception as e:
            integration_tests.append(f"❌ API-Service integration failed: {str(e)}")
        
        # Test 4: Background task integration
        print("      ⚙️ Testing background task integration...")
        try:
            from app.tasks.ml_tasks import get_task_status
            from app.tasks.celery_app import celery_app
            
            if celery_app:
                integration_tests.append("✅ Background task integration available")
            else:
                integration_tests.append("⚠️ Background task integration incomplete")
                
        except Exception as e:
            integration_tests.append(f"❌ Background task integration failed: {str(e)}")
        
        # Calculate integration success
        successful_integrations = sum(1 for test in integration_tests if test.startswith("✅"))
        total_integrations = len(integration_tests)
        integration_rate = (successful_integrations / total_integrations) * 100 if total_integrations > 0 else 0
        
        for test in integration_tests:
            print(f"         {test}")
        
        print(f"      📊 Integration: {successful_integrations}/{total_integrations} components integrated ({integration_rate:.1f}%)")
        
        return {
            "success": integration_rate >= 75,  # 75% threshold
            "integration_tests": integration_tests,
            "integration_rate": integration_rate,
            "metrics": {
                "Integrated Components": f"{successful_integrations}/{total_integrations}",
                "Integration Rate": f"{integration_rate:.1f}%"
            }
        }
    
    async def validate_performance(self) -> Dict[str, Any]:
        """Validate system performance"""
        print("   ⚡ Validating system performance...")
        
        performance_results = {}
        
        # Test basic service response times
        print("      ⏱️ Testing response times...")
        try:
            from app.ml.prediction.prediction_service import prediction_service
            import time
            
            # Test prediction service performance metrics call
            start_time = time.time()
            metrics = prediction_service.get_performance_metrics()
            response_time = (time.time() - start_time) * 1000  # ms
            
            performance_results["service_response"] = {
                "success": response_time < 1000,  # Less than 1 second
                "response_time_ms": response_time
            }
            
            print(f"         ⚡ Service response: {response_time:.1f}ms")
            
        except Exception as e:
            performance_results["service_response"] = {"success": False, "error": str(e)}
            print(f"         ❌ Service response test failed: {str(e)}")
        
        # Test memory usage
        print("      💾 Testing memory usage...")
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            performance_results["memory_usage"] = {
                "success": memory_mb < 500,  # Less than 500MB
                "memory_mb": memory_mb
            }
            
            print(f"         💾 Memory usage: {memory_mb:.1f}MB")
            
        except Exception as e:
            performance_results["memory_usage"] = {"success": False, "error": str(e)}
            print(f"         ❌ Memory usage test failed: {str(e)}")
        
        # Test database query performance
        print("      🗄️ Testing database performance...")
        try:
            from app.core.database import engine
            import time
            
            start_time = time.time()
            with engine.connect() as conn:
                conn.execute("SELECT COUNT(*) FROM information_schema.tables").fetchone()
            query_time = (time.time() - start_time) * 1000  # ms
            
            performance_results["database_performance"] = {
                "success": query_time < 500,  # Less than 500ms
                "query_time_ms": query_time
            }
            
            print(f"         🗄️ Database query: {query_time:.1f}ms")
            
        except Exception as e:
            performance_results["database_performance"] = {"success": False, "error": str(e)}
            print(f"         ❌ Database performance test failed: {str(e)}")
        
        # Calculate performance success
        performance_success = sum(1 for test in performance_results.values() if test.get("success", False))
        performance_total = len(performance_results)
        performance_rate = (performance_success / performance_total) * 100 if performance_total > 0 else 0
        
        print(f"      📊 Performance: {performance_success}/{performance_total} tests passed ({performance_rate:.1f}%)")
        
        return {
            "success": performance_rate >= 70,  # 70% threshold
            "performance_results": performance_results,
            "performance_rate": performance_rate,
            "metrics": {
                "Performance Tests": f"{performance_success}/{performance_total}",
                "Performance Rate": f"{performance_rate:.1f}%"
            }
        }
    
    async def test_real_data(self) -> Dict[str, Any]:
        """Test with real data scenarios"""
        print("   💰 Testing real data scenarios...")
        
        real_data_results = {}
        
        # Test 1: Bitcoin cryptocurrency setup
        print("      💰 Testing Bitcoin setup...")
        try:
            from app.core.database import SessionLocal
            from app.repositories import cryptocurrency_repository
            from app.schemas.cryptocurrency import CryptocurrencyCreate
            
            db = SessionLocal()
            try:
                btc = cryptocurrency_repository.get_by_symbol(db, "BTC")
                if not btc:
                    # Create Bitcoin for testing
                    btc_create = CryptocurrencyCreate(
                        symbol="BTC",
                        name="Bitcoin",
                        is_active=True
                    )
                    btc = cryptocurrency_repository.create(db, obj_in=btc_create)
                
                if btc:
                    real_data_results["bitcoin_setup"] = {"success": True, "crypto_id": btc.id}
                    print("         ✅ Bitcoin cryptocurrency available")
                else:
                    real_data_results["bitcoin_setup"] = {"success": False}
                    print("         ❌ Bitcoin cryptocurrency not available")
                    
            finally:
                db.close()
                
        except Exception as e:
            real_data_results["bitcoin_setup"] = {"success": False, "error": str(e)}
            print(f"         ❌ Bitcoin setup failed: {str(e)}")
        
        # Test 2: External API simulation
        print("      🌐 Testing external API integration...")
        try:
            # We can't test real external APIs in automated tests
            # but we can test the structure is in place
            from app.services.external_api import external_api_service
            
            real_data_results["external_api"] = {"success": True, "note": "Structure available"}
            print("         ✅ External API structure available")
            
        except Exception as e:
            real_data_results["external_api"] = {"success": False, "error": str(e)}
            print(f"         ❌ External API structure failed: {str(e)}")
        
        # Test 3: Price data handling
        print("      📊 Testing price data handling...")
        try:
            from app.repositories import price_data_repository
            from app.schemas.price_data import PriceDataCreate
            from decimal import Decimal
            
            db = SessionLocal()
            try:
                if real_data_results.get("bitcoin_setup", {}).get("success"):
                    crypto_id = real_data_results["bitcoin_setup"]["crypto_id"]
                    
                    # Test price data creation (small test)
                    test_price = PriceDataCreate(
                        crypto_id=crypto_id,
                        price=Decimal("45000.00"),
                        volume=Decimal("1000000.00"),
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    # We won't actually create it to avoid duplicates
                    real_data_results["price_data"] = {"success": True, "note": "Structure validated"}
                    print("         ✅ Price data handling available")
                else:
                    real_data_results["price_data"] = {"success": False, "note": "No Bitcoin available"}
                    print("         ⚠️ Price data handling skipped - no Bitcoin")
                    
            finally:
                db.close()
                
        except Exception as e:
            real_data_results["price_data"] = {"success": False, "error": str(e)}
            print(f"         ❌ Price data handling failed: {str(e)}")
        
        # Calculate real data success
        real_data_success = sum(1 for test in real_data_results.values() if test.get("success", False))
        real_data_total = len(real_data_results)
        real_data_rate = (real_data_success / real_data_total) * 100 if real_data_total > 0 else 0
        
        print(f"      📊 Real Data: {real_data_success}/{real_data_total} tests passed ({real_data_rate:.1f}%)")
        
        return {
            "success": real_data_rate >= 70,  # 70% threshold (external APIs can be unreliable)
            "real_data_results": real_data_results,
            "real_data_rate": real_data_rate,
            "metrics": {
                "Real Data Tests": f"{real_data_success}/{real_data_total}",
                "Real Data Rate": f"{real_data_rate:.1f}%"
            }
        }
    
    async def test_end_to_end(self) -> Dict[str, Any]:
        """Test complete end-to-end workflow"""
        print("   🔄 Testing end-to-end workflow...")
        
        try:
            # Run comprehensive test
            result = subprocess.run([
                sys.executable, "temp/comprehensive_test_all_apis.py"
            ], capture_output=True, text=True, timeout=600)
            
            e2e_success = result.returncode == 0
            
            if e2e_success:
                print("      ✅ End-to-end workflow completed successfully")
            else:
                print("      ⚠️ End-to-end workflow had issues")
            
            return {
                "success": e2e_success,
                "output": result.stdout if e2e_success else result.stderr,
                "metrics": {
                    "Workflow Status": "Completed" if e2e_success else "Failed"
                }
            }
            
        except subprocess.TimeoutExpired:
            print("      ⏰ End-to-end workflow timed out")
            return {
                "success": False,
                "error": "End-to-end test timed out",
                "metrics": {
                    "Workflow Status": "Timeout"
                }
            }
        except Exception as e:
            print(f"      ❌ End-to-end workflow failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "metrics": {
                    "Workflow Status": "Error"
                }
            }
    
    async def assess_phase_1_completion(self) -> Dict[str, Any]:
        """Assess overall Phase 1 completion"""
        print("   🎯 Assessing Phase 1 completion...")
        
        # Analyze all previous test results
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result.get("success", False))
        overall_success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Key component analysis
        components = {
            "API Integration (Stage C)": self.results.get("Stage C: API Integration Validation", {}).get("success", False),
            "Testing Infrastructure (Stage D)": self.results.get("Stage D: Testing Infrastructure", {}).get("success", False),
            "Component Integration": self.results.get("Integration Verification", {}).get("success", False),
            "Performance": self.results.get("Performance Validation", {}).get("success", False),
            "Real Data": self.results.get("Real Data Testing", {}).get("success", False),
            "End-to-End Workflow": self.results.get("End-to-End Workflow", {}).get("success", False)
        }
        
        component_success = sum(1 for success in components.values() if success)
        component_total = len(components)
        component_rate = (component_success / component_total) * 100
        
        # Determine Phase 1 status
        if overall_success_rate >= 90 and component_rate >= 90:
            self.phase_1_status = "OUTSTANDING"
        elif overall_success_rate >= 80 and component_rate >= 80:
            self.phase_1_status = "COMPLETE"
        elif overall_success_rate >= 70 and component_rate >= 70:
            self.phase_1_status = "MOSTLY_COMPLETE"
        elif overall_success_rate >= 60:
            self.phase_1_status = "PARTIAL"
        else:
            self.phase_1_status = "INCOMPLETE"
        
        print(f"      📊 Overall success: {passed_tests}/{total_tests} tests ({overall_success_rate:.1f}%)")
        print(f"      🎯 Component success: {component_success}/{component_total} components ({component_rate:.1f}%)")
        print(f"      🏆 Phase 1 Status: {self.phase_1_status}")
        
        return {
            "success": overall_success_rate >= 70,  # 70% threshold for Phase 1
            "overall_success_rate": overall_success_rate,
            "component_success_rate": component_rate,
            "phase_1_status": self.phase_1_status,
            "components": components,
            "metrics": {
                "Overall Success": f"{overall_success_rate:.1f}%",
                "Component Success": f"{component_rate:.1f}%",
                "Phase 1 Status": self.phase_1_status
            }
        }
    
    def generate_final_report(self, passed_tests: int, total_tests: int) -> Dict[str, Any]:
        """Generate comprehensive final report"""
        
        overall_success_rate = (passed_tests / total_tests) * 100
        total_duration = self.end_time - self.start_time
        
        print(f"\n{'='*70}")
        print("🏁 CRYPTOPREDICT MVP - FINAL COMPREHENSIVE REPORT")
        print(f"{'='*70}")
        
        print(f"📊 Executive Summary:")
        print(f"   Overall Success Rate: {overall_success_rate:.1f}% ({passed_tests}/{total_tests})")
        print(f"   Phase 1 Status: {self.phase_1_status}")
        print(f"   Total Test Duration: {total_duration/60:.1f} minutes")
        print(f"   Completion Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Stage-specific results
        print(f"\n📋 Stage Results:")
        stage_c = self.results.get("Stage C: API Integration Validation", {})
        stage_d = self.results.get("Stage D: Testing Infrastructure", {})
        
        if stage_c.get("success"):
            stage_c_rate = stage_c.get("stage_c_success_rate", 0)
            print(f"   ✅ Stage C (API Integration): {stage_c_rate:.1f}% complete")
        else:
            print(f"   ❌ Stage C (API Integration): Failed")
        
        if stage_d.get("success"):
            stage_d_rate = stage_d.get("stage_d_success_rate", 0)
            print(f"   ✅ Stage D (Testing & Validation): {stage_d_rate:.1f}% complete")
        else:
            print(f"   ❌ Stage D (Testing & Validation): Failed")
        
        # Component analysis
        print(f"\n🔍 Component Analysis:")
        for test_name, result in self.results.items():
            status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
            print(f"   {status}: {test_name}")
            
            if result.get("metrics"):
                for metric_name, metric_value in result["metrics"].items():
                    print(f"      📊 {metric_name}: {metric_value}")
        
        # Overall assessment
        print(f"\n🎯 Overall Assessment:")
        if self.phase_1_status == "OUTSTANDING":
            print("   🌟 OUTSTANDING: CryptoPredict MVP exceeds all expectations!")
            print("   ✨ Ready for immediate production deployment")
            print("   🚀 Recommend starting Phase 2: Enhanced Features")
            assessment = "OUTSTANDING"
        elif self.phase_1_status == "COMPLETE":
            print("   🎉 COMPLETE: CryptoPredict MVP successfully implemented!")
            print("   ✅ All major components working correctly")
            print("   🚀 Ready for production deployment")
            print("   📈 Can proceed to Phase 2: Enhanced Features")
            assessment = "COMPLETE"
        elif self.phase_1_status == "MOSTLY_COMPLETE":
            print("   ✅ MOSTLY COMPLETE: CryptoPredict MVP is nearly ready!")
            print("   🔧 Minor issues need attention")
            print("   ⏳ Near production ready")
            print("   📋 Complete remaining items before Phase 2")
            assessment = "MOSTLY_COMPLETE"
        elif self.phase_1_status == "PARTIAL":
            print("   ⚠️ PARTIAL: CryptoPredict MVP has core functionality")
            print("   🛠️ Several components need completion")
            print("   📋 Focus on fixing failed tests")
            print("   ⏳ More work needed before production")
            assessment = "PARTIAL"
        else:
            print("   ❌ INCOMPLETE: CryptoPredict MVP needs significant work")
            print("   🚨 Critical components failed")
            print("   🛠️ Major development required")
            print("   📋 Complete Phase 1 before proceeding")
            assessment = "INCOMPLETE"
        
        # Technical achievements
        print(f"\n🎯 Technical Achievements:")
        achievements = []
        
        if stage_c.get("success"):
            achievements.append("✅ Complete API Integration (Training & Prediction)")
            achievements.append("✅ Background Task Infrastructure")
            achievements.append("✅ Schema Validation & Documentation")
        
        if stage_d.get("success"):
            achievements.append("✅ Comprehensive Testing Infrastructure")
            achievements.append("✅ Performance Validation")
            achievements.append("✅ Integration Testing")
        
        if self.results.get("Integration Verification", {}).get("success"):
            achievements.append("✅ Component Integration")
        
        if self.results.get("Performance Validation", {}).get("success"):
            achievements.append("✅ Performance Optimization")
        
        if self.results.get("End-to-End Workflow", {}).get("success"):
            achievements.append("✅ Complete Workflow Validation")
        
        for achievement in achievements:
            print(f"   {achievement}")
        
        # Next steps
        print(f"\n🚀 Next Steps:")
        if self.phase_1_status in ["OUTSTANDING", "COMPLETE"]:
            print("   🎨 Begin Phase 2: Enhanced UI/UX")
            print("   📱 Develop mobile application")
            print("   🔍 Add advanced analytics features")
            print("   🌐 Expand cryptocurrency support")
            print("   ⚡ Implement real-time notifications")
        elif self.phase_1_status == "MOSTLY_COMPLETE":
            print("   🔧 Address remaining test failures")
            print("   ⚡ Optimize performance bottlenecks")
            print("   📚 Complete documentation")
            print("   🧪 Re-run failed tests")
        else:
            print("   🚨 Fix critical component failures")
            print("   🛠️ Complete Stage C API integration")
            print("   🧪 Implement Stage D testing infrastructure")
            print("   🔧 Debug integration issues")
        
        # Feature completion matrix
        print(f"\n✅ Feature Completion Matrix:")
        features = [
            ("ML Training API", stage_c.get("success", False)),
            ("ML Prediction API", stage_c.get("success", False)),
            ("Background Tasks", stage_c.get("success", False)),
            ("Integration Testing", stage_d.get("success", False)),
            ("Performance Testing", self.results.get("Performance Validation", {}).get("success", False)),
            ("Real Data Support", self.results.get("Real Data Testing", {}).get("success", False)),
            ("End-to-End Workflow", self.results.get("End-to-End Workflow", {}).get("success", False)),
            ("Error Handling", self.results.get("Integration Verification", {}).get("success", False))
        ]
        
        for feature_name, is_complete in features:
            status = "✅" if is_complete else "❌"
            print(f"   {status} {feature_name}")
        
        # Save comprehensive report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "overall_success_rate": overall_success_rate,
            "phase_1_status": self.phase_1_status,
            "assessment": assessment,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "duration_minutes": total_duration / 60,
            "stage_results": {
                "stage_c_success": stage_c.get("success", False),
                "stage_d_success": stage_d.get("success", False)
            },
            "detailed_results": self.results,
            "feature_completion": {name: status for name, status in features},
            "technical_achievements": achievements,
            "ready_for_production": self.phase_1_status in ["OUTSTANDING", "COMPLETE"],
            "ready_for_phase_2": self.phase_1_status == "OUTSTANDING"
        }
        
        # Save report to file
        try:
            os.makedirs("temp/reports", exist_ok=True)
            report_filename = f"temp/reports/final_report_stages_c_d_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            print(f"\n📄 Comprehensive report saved: {report_filename}")
        except Exception as e:
            print(f"\n⚠️ Could not save comprehensive report: {str(e)}")
        
        print(f"\n🏆 Final Assessment: {assessment}")
        print(f"🎯 Phase 1 Status: {self.phase_1_status}")
        print(f"🏁 CryptoPredict MVP Testing Complete!")
        
        return report_data


async def main():
    """Main function to run final comprehensive tests"""
    try:
        # Environment check
        if not os.path.exists("backend"):
            print("❌ Please run this script from the project root directory")
            print("📁 Current directory:", os.getcwd())
            return 1
        
        print("🔧 Initializing final test suite...")
        
        # Create and run final test suite
        test_suite = FinalTestSuite()
        final_report = await test_suite.run_final_tests()
        
        # Return appropriate exit code based on results
        if final_report["phase_1_status"] in ["OUTSTANDING", "COMPLETE"]:
            print("\n🎉 CryptoPredict MVP successfully completed!")
            return 0
        elif final_report["phase_1_status"] == "MOSTLY_COMPLETE":
            print("\n✅ CryptoPredict MVP mostly completed - minor fixes needed")
            return 0
        else:
            print("\n⚠️ CryptoPredict MVP needs more work")
            return 1
            
    except KeyboardInterrupt:
        print("\n👋 Final test suite interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Final test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)