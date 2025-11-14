# Bitcoin Test Scripts
# اسکریپت‌های تست بیتکوین

This directory contains test scripts for Bitcoin data operations.
این پوشه شامل اسکریپت‌های تست برای عملیات داده‌های بیتکوین است.

## Files / فایل‌ها

### Python Scripts / اسکریپت‌های پایتون

- **`check_requirements.py`** - بررسی پیش‌نیازها / Check system requirements
- **`quick_bitcoin_test.py`** - تست سریع بیتکوین / Quick Bitcoin test
- **`test_bitcoin_update.py`** - تست کامل بروزرسانی / Complete Bitcoin update test

### Execution Scripts / اسکریپت‌های اجرا

- **`run_bitcoin_test.ps1`** - PowerShell script for Windows
- **`run_bitcoin_test.bat`** - Batch file for Windows

## Usage / نحوه استفاده

### Quick Start / شروع سریع

```bash
# Navigate to this directory first
cd temp/test1

# Check requirements first
python check_requirements.py

# Run quick test
python quick_bitcoin_test.py

# Run complete test
python test_bitcoin_update.py
```

### Windows Users / کاربران ویندوز

```cmd
# Navigate to this directory first
cd temp\test1

# Using batch file
run_bitcoin_test.bat

# Using PowerShell
.\run_bitcoin_test.ps1
```

## Prerequisites / پیش‌نیازها

1. Python 3.8+ with virtual environment activated
2. Database connection configured
3. Required packages installed: `pip install -r ../../backend/requirements.txt`

## Notes / نکات

- These scripts test Bitcoin data population and aggregation
- Run from temp/test1 directory for proper path resolution
- Ensure virtual environment is activated before running
- Virtual environment path: `../../backend/venv/Scripts/activate` (Windows)

---
*Files moved to temp/test1 on 2025-10-24*