# PowerShell script to run Bitcoin data update test
# اسکریپت PowerShell برای اجرای تست بروزرسانی داده‌های بیتکوین

Write-Host "🚀 Bitcoin Data Update Test" -ForegroundColor Green
Write-Host "تست بروزرسانی داده‌های بیتکوین" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Yellow

# Check if virtual environment exists
$venvPath = "..\..\backend\venv\Scripts\Activate.ps1"

if (Test-Path $venvPath) {
    Write-Host "🔧 فعال‌سازی محیط مجازی..." -ForegroundColor Cyan
    & $venvPath
    
    Write-Host "✅ محیط مجازی فعال شد" -ForegroundColor Green
} else {
    Write-Host "⚠️ محیط مجازی پیدا نشد، ادامه بدون آن..." -ForegroundColor Yellow
}

# Set environment variables if needed
$env:PYTHONPATH = "..\..\backend"

Write-Host "🐍 اجرای اسکریپت پایتون..." -ForegroundColor Cyan

# Run the Python script
try {
    python test_bitcoin_update.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ تست موفقیت‌آمیز بود!" -ForegroundColor Green
    } else {
        Write-Host "❌ تست ناموفق بود!" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ خطا در اجرای اسکریپت: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "برای اجرای تست سریع:" -ForegroundColor Yellow
Write-Host "python quick_bitcoin_test.py" -ForegroundColor White

Write-Host ""
Write-Host "فشار دهید Enter برای ادامه..." -ForegroundColor Gray
Read-Host