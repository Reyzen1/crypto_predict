@echo off
REM File: scripts/run.bat
REM Run script for CryptoPredict MVP on Windows
REM Automates the run process, now with a Docker check.

echo ========================================
echo CryptoPredict MVP Run Script (backend)
echo ========================================
echo.

REM -- Check if Docker is running ---
REM -- Disable Docker check if running inside WSL --
ver | findstr /i "Microsoft" > nul
if %errorlevel% equ 0 (
    echo Running inside WSL, skipping Docker Desktop check...
) else (
    echo Checking Docker status...
    docker info > nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Docker is not running.
        echo Please start Docker Desktop and ensure it is running before executing this script.
        echo.
        pause
        exit /b 1
    )
    echo Docker is running.
)

REM --- END: Docker Check ---

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

REM Start the Uvicorn server
echo Starting the application server...
python -m uvicorn app.main:app --reload
