#!/bin/bash
# File: run_tests.sh
# Bash script to run integration tests for CryptoPredict MVP

# --- Initial Setup ---
# Exit immediately if a command exits with a non-zero status.
set -e
# The return value of a pipeline is the status of the last command to exit with a non-zero status.
set -o pipefail

# --- Variables and Colors ---
# Define color codes for more readable output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Path to the test file
TEST_FILE="backend/tests/test_basic_integration.py"

# Pytest options
PYTEST_OPTIONS="-v --tb=short --no-header -x"

# List of required packages for testing
REQUIRED_PACKAGES=(
    "pytest"
    "pytest-asyncio"
    "httpx"
    "fastapi"
    "sqlalchemy"
)

# --- Function Definitions ---

# Function to check for required dependencies
check_dependencies() {
    echo -e "🔍 ${YELLOW}Checking dependencies...${NC}"
    local missing_packages=()

    # Loop through and check if each package is installed
    for package in "${REQUIRED_PACKAGES[@]}"; do
        # Redirect pip show output to /dev/null to suppress it
        if ! python -m pip show "$package" &> /dev/null; then
            missing_packages+=("$package")
        fi
    done

    # If there are any missing packages, print an error and exit
    if [ ${#missing_packages[@]} -ne 0 ]; then
        echo -e "❌ ${RED}Missing required packages:${NC}"
        for package in "${missing_packages[@]}"; do
            echo "   - $package"
        done
        echo -e "\n📋 ${YELLOW}Install missing packages:${NC}"
        echo "   pip install ${missing_packages[*]}"
        exit 1
    fi

    echo -e "✅ ${GREEN}All dependencies found${NC}"
}

# Function to run the tests
run_tests() {
    echo
    echo -e "🚀 ${GREEN}Running integration tests...${NC}"
    echo "--------------------------------------------------"

    # Check if the test file actually exists
    if [ ! -f "$TEST_FILE" ]; then
        echo -e "❌ ${RED}Test file not found at: $TEST_FILE${NC}"
        exit 1
    fi

    # Run tests with Pytest
    python -m pytest $PYTEST_OPTIONS "$TEST_FILE"
    local exit_code=$? # Store the exit code of the last command

    echo "--------------------------------------------------"

    if [ $exit_code -eq 0 ]; then
        echo -e "🎉 ${GREEN}ALL TESTS PASSED!${NC}"
        echo -e "✅ ${GREEN}Backend is working correctly${NC}"
    else
        echo -e "❌ ${RED}Tests failed with return code: $exit_code${NC}"
        echo -e "📋 ${YELLOW}Please check the output above for issues${NC}"
        exit 1
    fi
}

# --- Main Execution ---

echo -e "🧪 ${GREEN}CryptoPredict MVP - Bash Test Runner${NC}"
echo "=================================================="

check_dependencies
run_tests

echo -e "\n🎯 ${GREEN}Success! All checks and tests completed.${NC}"