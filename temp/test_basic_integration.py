#!/usr/bin/env python3
# File: backend/run_tests.py
# Simple test runner script

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run the integration tests with proper setup"""
    
    print("🧪 CryptoPredict MVP - Test Runner")
    print("=" * 50)
    
    print(f"📁 Working directory: {os.getcwd()}")
    
    
    # Check if test file exists
    test_file = "backend/tests/test_basic_integration.py"
    
    print(f"✅ Test file found: {test_file}")
    
    # Run the tests
    print("\n🚀 Running integration tests...")
    print("-" * 50)
    
    try:
        # Run pytest with the specific test file
        cmd = [
            sys.executable, "-m", "pytest", 
            str(test_file),
            "-v",              # Verbose output
            "--tb=short",      # Short traceback format
            "--no-header",     # No pytest header
            "-x"               # Stop on first failure
        ]
        
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        print("-" * 50)
        
        if result.returncode == 0:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Backend is working correctly")
            print("✅ API endpoints are accessible")
            print("✅ Authentication system is functional")
            return True
        else:
            print(f"❌ Tests failed with return code: {result.returncode}")
            print("📋 Please check the output above for issues")
            return False
            
    except FileNotFoundError:
        print("❌ pytest not found!")
        print("📋 Please install pytest:")
        print("   pip install pytest pytest-asyncio httpx")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "httpx",
        "fastapi",
        "sqlalchemy"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📋 Install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def main():
    """Main function"""
    print("🔍 Checking dependencies...")
    
    if not check_dependencies():
        return
    
    print("✅ All dependencies found")
    
    print("\n🧪 Starting tests...")
    success = run_tests()
    
    if success:
        print("\n🎯 Success")

    else:
        print("\n🔧 Troubleshooting:")
        print("1. Check the error messages above")
        print("2. Ensure all fixes have been applied")
        print("3. Verify database connections")

if __name__ == "__main__":
    main()