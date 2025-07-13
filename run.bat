@echo off
REM File: scripts/run.bat
REM Run script for CryptoPredict MVP on Windows
REM Automates the run process

echo ========================================
echo CryptoPredict MVP Run Script
echo ========================================
echo.

REM Check if we're in the right directory
if not exist docker-compose.yml (
    echo Error: Please run this script from the project root directory
    pause
    exit /b 1
)

cd backend

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

python -m uvicorn app.main:app --reload

