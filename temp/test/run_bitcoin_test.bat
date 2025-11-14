@echo off
REM Bitcoin Data Update Test Script
REM اسکریپت تست بروزرسانی داده‌های بیتکوین

echo 🚀 Bitcoin Data Update Test
echo تست بروزرسانی داده‌های بیتکوین
echo ================================================

REM Activate virtual environment if it exists
if exist "..\..\backend\venv\Scripts\activate.bat" (
    echo 🔧 فعال‌سازی محیط مجازی...
    call ..\..\backend\venv\Scripts\activate.bat
    echo ✅ محیط مجازی فعال شد
) else (
    echo ⚠️ محیط مجازی پیدا نشد، ادامه بدون آن...
)

REM Set Python path
set PYTHONPATH=..\..\backend

echo 🐍 اجرای تست سریع...
python quick_bitcoin_test.py

echo.
echo برای تست کامل:
echo python test_bitcoin_update.py

echo.
pause