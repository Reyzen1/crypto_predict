@echo off
REM File: temp/start-solo-workers.bat
REM Fixed Celery workers using solo pool for Windows

echo 🔧 CryptoPredict - SOLO POOL WORKERS (Fixed)
echo ============================================

cd backend

REM Stop existing workers
echo 🧹 Stopping existing workers...
taskkill /F /IM celery.exe 2>nul || echo No celery processes to kill
timeout /t 3 >nul

echo.
echo 🚀 MANUAL TERMINAL SETUP REQUIRED
echo ================================
echo.
echo Please open 4 separate terminals and run these commands:
echo.
echo 📊 TERMINAL 1 - Data Worker:
echo    cd backend
echo    celery -A app.tasks.celery_app worker --loglevel=info --queues=price_data,default --pool=solo --concurrency=1 --hostname=data_worker@%%h
echo.
echo 🤖 TERMINAL 2 - ML Worker:
echo    cd backend  
echo    celery -A app.tasks.celery_app worker --loglevel=info --queues=ml_tasks --pool=solo --concurrency=1 --hostname=ml_worker@%%h
echo.
echo ⏰ TERMINAL 3 - Beat Scheduler:
echo    cd backend
echo    celery -A app.tasks.celery_app beat --loglevel=info
echo.
echo 🌸 TERMINAL 4 - Flower Monitor:
echo    cd backend
echo    celery -A app.tasks.celery_app flower --port=5555 --basic_auth=admin:cryptopredict123
echo.
echo 🎯 Expected Results:
echo • Data Worker: Will process 22+ pending tasks in price_data queue
echo • Tasks change from PENDING → RUNNING → SUCCESS
echo • Flower dashboard: http://localhost:5555 (admin:cryptopredict123)
echo • Queue lengths decrease rapidly
echo.
echo ⚡ Why Solo Pool Works:
echo • No subprocess spawning (faster)
echo • ML models load once per worker (not per task)  
echo • Eliminates process overhead issues
echo • Perfect for ML-heavy workloads
echo.
pause