@echo off
REM File: run_backend.bat

echo ========================================
echo CryptoPredict MVP Run Script (backend)
echo ========================================
echo.

setlocal EnableDelayedExpansion

set CONTAINER1=postgres
set CONTAINER2=redis

REM ----------------------------
REM --- Try Docker on Windows
REM ----------------------------
where docker > nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Docker not found in Windows, trying WSL...
    goto CheckWSL
)

docker info > nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Docker not running in Windows, trying WSL...
    goto CheckWSL
)

echo [OK] Docker is running on Windows. Using native docker-compose...

call :CheckAndStartContainer %CONTAINER1% docker
call :CheckAndStartContainer %CONTAINER2% docker
goto ContinueBackend

REM ----------------------------
:CheckWSL
REM --- Try Docker in WSL
REM ----------------------------
wsl -e bash -c "docker info" >nul 2>&1
if %errorlevel% neq 0 (
    echo [✖] Docker not running in WSL either. Please start Docker Desktop or WSL Docker daemon.
    pause
    exit /b 1
)

echo [OK] Docker is running inside WSL. Using docker-compose from WSL...

call :CheckAndStartContainer %CONTAINER1% wsl
call :CheckAndStartContainer %CONTAINER2% wsl

goto ContinueBackend

REM ----------------------------
REM --- Container Checker
REM ----------------------------
:CheckAndStartContainer
setlocal
set SERVICE_NAME=%1
set DOCKER_CMD=%2
set CONTAINER_ID=
set CONTAINER_STATE=

echo Checking service: %SERVICE_NAME% ...

REM --- Get container ID using docker-compose ---
if "%DOCKER_CMD%"=="wsl" (
    for /f %%I in ('wsl docker-compose ps -q %SERVICE_NAME%') do set CONTAINER_ID=%%I
    if not defined CONTAINER_ID (
        echo [WARNING] No container found for service '%SERVICE_NAME%'. Creating it...
        wsl docker-compose up -d %SERVICE_NAME%
        goto :eof
    )

    wsl docker inspect -f "{{.State.Running}}" !CONTAINER_ID! > temp.txt 2>nul
    set /p CONTAINER_STATE=<temp.txt
    del temp.txt
) else (
    for /f %%I in ('docker-compose ps -q %SERVICE_NAME%') do set CONTAINER_ID=%%I
    if not defined CONTAINER_ID (
        echo [WARNING] No container found for service '%SERVICE_NAME%'. Creating it...
        docker-compose up -d %SERVICE_NAME%
        goto :eof
    )

    for /f %%S in ('docker inspect -f ^"{{.State.Running}}^" !CONTAINER_ID! 2^>nul') do (
        set CONTAINER_STATE=%%S
    )
)

if "!CONTAINER_STATE!"=="true" (
    echo [OK] Service '%SERVICE_NAME%' is already running.
) else if "!CONTAINER_STATE!"=="false" (
    echo [INFO] Service '%SERVICE_NAME%' exists but is not running.
    if "%DOCKER_CMD%"=="wsl" (
        wsl docker-compose start %SERVICE_NAME%
    ) else (
        docker-compose start %SERVICE_NAME%
    )
) else (
    echo [WARNING] Could not determine status of service '%SERVICE_NAME%'
)

endlocal
goto :eof


REM ----------------------------
REM --- Continue to Backend
REM ----------------------------
:ContinueBackend
echo.
cd backend

echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error activating virtual environment
    pause
    exit /b 1
)

echo Starting backend server...
python -m uvicorn app.main:app --reload
