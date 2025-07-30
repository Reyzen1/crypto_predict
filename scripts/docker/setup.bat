@echo off
REM File: scripts/setup.bat
REM Setup script for CryptoPredict MVP on Windows
REM Automates the initial setup process

echo ========================================
echo CryptoPredict MVP Setup Script
echo ========================================
echo.

REM Check if we're in the right directory
if not exist docker-compose.yml (
    echo Error: Please run this script from the project root directory
    pause
    exit /b 1
)

echo Step 1: Setting up Backend Virtual Environment...
cd backend

REM Test if Python 3.12 is available
py -3.12 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python 3.12 not found. Please ensure Python 3.12 is installed.
    echo Try running: py -3.12 --version
    pause
    exit /b 1
)

echo Python 3.12 found successfully!

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    py -3.12 -m venv venv
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip first
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install Python dependencies
echo Installing Python dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install Python dependencies
    echo Make sure requirements.txt exists in the backend directory
    pause
    exit /b 1
)

