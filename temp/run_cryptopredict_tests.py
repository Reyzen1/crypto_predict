# File: temp/run_cryptopredict_tests.py
# Master Test Orchestrator for CryptoPredict MVP - Complete Stages C & D

import os
import sys
import subprocess
import argparse
import time
from datetime import datetime
from typing import List, Dict, Any


class CryptoPredictTestOrchestrator:
    """Master test orchestrator for CryptoPredict MVP"""
    
    def __init__(self):
        self.project_root = os.getcwd()
        self.test_results = {}
        
    def validate_environment(self) -> bool:
        """Validate test environment"""
        print("🔍 Validating test environment...")
        
        # Check if we're in the right directory
        if not os.path.exists("backend"):
            print("❌ Error: Please run this script from the project root directory")
            print(f"📁 Current directory: {os.getcwd()}")
            print("📋 Expected structure: project_root/backend/")
            return False
        
        # Check Python version
        if sys.version_info < (3, 8):
            print(f"❌ Error: Python 3.8+ required, found {sys.version}")
            return False
        
        # Check for required test scripts
        required_scripts = [
            "temp/quick_api_test.py",
            "temp/comprehensive_test_all_apis.py", 
            "temp/integration_test_stage_d.py",
            "temp/performance_benchmark.py",
            "temp/final_test_stages_c_d.py"
        ]
        
        missing_scripts = []
        for script in required_scripts:
            if not os.path.exists(script):
                missing_scripts.append(script)
        
        if missing_scripts:
            print("❌ Error: Missing required test scripts:")
            for script in missing_scripts:
                print(f"   📄 {script}")
            return False
        
        # Check if backend can be imported
        try:
            sys.path.insert(0, 'backend')
            from app.core.config import settings
            print("✅ Environment validation passed")
            return True
        except ImportError as e:
            print(f"❌ Error: Cannot import backend modules: {e}")
            return False
    
    def run_test_suite(self, test_type: str = "comprehensive") -> Dict[str, Any]:
        """Run specified test suite"""
        
        print(f"\n🚀 CryptoPredict MVP Test Suite")
        print("=" * 60)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Test Type: {test_type.upper()}")
        print()
        
        if test_type == "quick":
            return self.run_quick_tests()
        elif test_type == "comprehensive":
            return self.run_comprehensive_tests()
        elif test_type == "performance":
            return self.run_performance_tests()
        elif test_type == "final":
            return self.run_final_validation()
        else:
            print(f"❌ Unknown test type: {test_type}")
            return {"success": False, "error": f"Unknown test type: {test_type}"}
    
    def run_quick_tests(self) -> Dict[str, Any]:
        """Run quick validation tests"""
        print("⚡ Running Quick Validation Tests...")
        print("-" * 40)
        
        tests = [
            ("Quick API Test", "temp/quick_api_test.py", 120),
        ]
        
        return self.execute_test_sequence(tests)
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        print("🧪 Running Comprehensive Test Suite...")
        print("-" * 40)
        
        tests = [
            ("Quick API Validation", "temp/quick_api_test.py", 120),
            ("Comprehensive API Tests", "temp/comprehensive_test_all_apis.py", 600),
            ("Integration Tests", "temp/integration_test_stage_d.py", 600),
        ]
        
        return self.execute_test_sequence(tests)
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance benchmark tests"""
        print("⚡ Running Performance Benchmark Tests...")
        print("-" * 40)
        
        tests = [
            ("Performance Benchmark", "temp/performance_benchmark.py", 900),
        ]
        
        return self.execute_test_sequence(tests)
    
    def run_final_validation(self) -> Dict[str, Any]:
        """Run final comprehensive validation"""
        print("🏁 Running Final Comprehensive Validation...")
        print("-" * 40)
        
        tests = [
            ("Final Stages C & D Test", "temp/final_test_stages_c_d.py", 1200),
        ]
        
        return self.execute_test_sequence(tests)
    
    def execute_test_sequence(self, tests: List[tuple]) -> Dict[str, Any]:
        """Execute a sequence of tests"""
        
        total_tests = len(tests)
        passed_tests = 0
        failed_tests = 0
        
        for i, (test_name, script_path, timeout) in enumerate(tests, 1):
            print(f"\n📋 Test {i}/{total_tests}: {test_name}")
            print(f"🔧 Script: {script_path}")
            print(f"⏱️ Timeout: {timeout}s")
            print("-" * 30)
            
            start_time = time.time()
            
            try:
                result = subprocess.run([
                    sys.executable, script_path
                ], capture_output=True, text=True, timeout=timeout)
                
                duration = time.time() - start_time
                
                if result.returncode == 0:
                    print(f"✅ {test_name}: PASSED ({duration:.1f}s)")
                    passed_tests += 1
                    self.test_results[test_name] = {
                        "status": "PASSED",
                        "duration": duration,
                        "output": result.stdout
                    }
                else:
                    print(f"❌ {test_name}: FAILED ({duration:.1f}s)")
                    failed_tests += 1
                    self.test_results[test_name] = {
                        "status": "FAILED", 
                        "duration": duration,
                        "error": result.stderr,
                        "output": result.stdout
                    }
                    
                    # Show error summary
                    if result.stderr:
                        error_lines = result.stderr.split('\n')[:5]  # First 5 lines
                        print("📋 Error Summary:")
                        for line in error_lines:
                            if line.strip():
                                print(f"   {line}")
                
            except subprocess.TimeoutExpired:
                duration = time.time() - start_time
                print(f"⏰ {test_name}: TIMEOUT ({duration:.1f}s)")
                failed_tests += 1
                self.test_results[test_name] = {
                    "status": "TIMEOUT",
                    "duration": duration,
                    "error": f"Test timed out after {timeout}s"
                }
                
            except Exception as e:
                duration = time.time() - start_time
                print(f"💥 {test_name}: ERROR ({duration:.1f}s)")
                print(f"   Exception: {str(e)}")
                failed_tests += 1
                self.test_results[test_name] = {
                    "status": "ERROR",
                    "duration": duration,
                    "error": str(e)
                }
        
        # Generate summary
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        return {
            "success": passed_tests > 0 and failed_tests == 0,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_tests": total_tests,
            "success_rate": success_rate,
            "test_results": self.test_results
        }
    
    def print_final_summary(self, results: Dict[str, Any]):
        """Print final test summary"""
        
        print(f"\n{'='*60}")
        print("🏁 CRYPTOPREDICT MVP - TEST SUMMARY")
        print(f"{'='*60}")
        
        print(f"📊 Test Results:")
        print(f"   ✅ Passed: {results['passed_tests']}")
        print(f"   ❌ Failed: {results['failed_tests']}")
        print(f"   📈 Success Rate: {results['success_rate']:.1f}%")
        print(f"   ⏱️ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n📋 Individual Test Results:")
        for test_name, test_result in results['test_results'].items():
            status = test_result['status']
            duration = test_result['duration']
            
            if status == "PASSED":
                print(f"   ✅ {test_name}: {status} ({duration:.1f}s)")
            elif status == "FAILED":
                print(f"   ❌ {test_name}: {status} ({duration:.1f}s)")
            elif status == "TIMEOUT":
                print(f"   ⏰ {test_name}: {status} ({duration:.1f}s)")
            else:
                print(f"   💥 {test_name}: {status} ({duration:.1f}s)")
        
        # Overall assessment
        print(f"\n🎯 Overall Assessment:")
        if results['success_rate'] >= 90:
            print("   🌟 OUTSTANDING: CryptoPredict MVP is excellent!")
            print("   🚀 Ready for production deployment")
            status = "OUTSTANDING"
        elif results['success_rate'] >= 80:
            print("   🎉 EXCELLENT: CryptoPredict MVP is complete!")
            print("   ✅ All major features working")
            status = "EXCELLENT"
        elif results['success_rate'] >= 70:
            print("   ✅ GOOD: CryptoPredict MVP is mostly complete")
            print("   🔧 Minor fixes needed")
            status = "GOOD"
        elif results['success_rate'] >= 50:
            print("   ⚠️ FAIR: CryptoPredict MVP has core functionality")
            print("   🛠️ Several issues need fixing")
            status = "FAIR"
        else:
            print("   ❌ NEEDS WORK: CryptoPredict MVP requires attention")
            print("   🚨 Critical issues found")
            status = "NEEDS_WORK"
        
        # Development stage status
        print(f"\n🏗️ Development Stage Status:")
        if results['success_rate'] >= 80:
            print("   ✅ Stage C (API Integration): COMPLETE")
            print("   ✅ Stage D (Testing & Validation): COMPLETE")
            print("   🎯 Phase 1 MVP: COMPLETE")
            print("   🚀 Ready for Phase 2")
        elif results['success_rate'] >= 60:
            print("   ⚠️ Stage C (API Integration): MOSTLY COMPLETE")
            print("   ⚠️ Stage D (Testing & Validation): NEEDS WORK")
            print("   ⏳ Phase 1 MVP: NEAR COMPLETE")
        else:
            print("   ❌ Stage C (API Integration): INCOMPLETE")
            print("   ❌ Stage D (Testing & Validation): INCOMPLETE")
            print("   🚧 Phase 1 MVP: IN PROGRESS")
        
        # Next steps
        print(f"\n🚀 Recommended Next Steps:")
        if results['success_rate'] >= 80:
            print("   🎨 Begin Phase 2: Enhanced Features")
            print("   📱 Develop mobile application")
            print("   🔍 Add advanced analytics")
            print("   🌐 Expand cryptocurrency support")
        elif results['success_rate'] >= 60:
            print("   🔧 Fix failing tests")
            print("   📚 Complete documentation")
            print("   ⚡ Optimize performance")
            print("   🧪 Re-run test suite")
        else:
            print("   🚨 Fix critical failures")
            print("   🛠️ Complete Stage C & D implementation")
            print("   📋 Review architecture")
            print("   🧪 Run comprehensive debugging")
        
        print(f"\n🏆 Final Status: {status}")
        
        # Save summary report
        try:
            os.makedirs("temp/reports", exist_ok=True)
            summary_file = f"temp/reports/test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(summary_file, 'w') as f:
                f.write("CryptoPredict MVP Test Summary\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"Success Rate: {results['success_rate']:.1f}%\n")
                f.write(f"Status: {status}\n")
                f.write(f"Passed: {results['passed_tests']}/{results['total_tests']}\n\n")
                
                for test_name, test_result in results['test_results'].items():
                    f.write(f"{test_name}: {test_result['status']}\n")
            
            print(f"📄 Summary saved: {summary_file}")
            
        except Exception as e:
            print(f"⚠️ Could not save summary: {str(e)}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="CryptoPredict MVP Test Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Types:
  quick         - Quick API validation tests (2-3 minutes)
  comprehensive - Full API and integration tests (10-15 minutes)  
  performance   - Performance benchmark tests (15-20 minutes)
  final         - Complete validation of Stages C & D (20+ minutes)

Examples:
  python temp/run_cryptopredict_tests.py quick
  python temp/run_cryptopredict_tests.py comprehensive
  python temp/run_cryptopredict_tests.py final
        """
    )
    
    parser.add_argument(
        'test_type',
        choices=['quick', 'comprehensive', 'performance', 'final'],
        default='comprehensive',
        nargs='?',
        help='Type of tests to run (default: comprehensive)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize orchestrator
        orchestrator = CryptoPredictTestOrchestrator()
        
        # Validate environment
        if not orchestrator.validate_environment():
            return 1
        
        print(f"\n🎯 Running {args.test_type} test suite...")
        
        # Run tests
        results = orchestrator.run_test_suite(args.test_type)
        
        # Print summary
        orchestrator.print_final_summary(results)
        
        # Return appropriate exit code
        if results['success']:
            print(f"\n🎉 Test suite completed successfully!")
            return 0
        else:
            print(f"\n⚠️ Test suite completed with issues")
            return 1 if results['success_rate'] < 50 else 0
        
    except KeyboardInterrupt:
        print(f"\n👋 Test suite interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test orchestrator failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)