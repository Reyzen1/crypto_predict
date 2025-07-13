@echo off
REM File: scripts/run_frontend.bat
REM Run script for CryptoPredict MVP on Windows
REM Automates the run process

echo ========================================
echo CryptoPredict MVP Run Script (frontend)
echo ========================================
echo.

REM Check if we're in the right directory
if not exist docker-compose.yml (
    echo Error: Please run this script from the project root directory
    pause
    exit /b 1
)

cd frontend

npm run dev

