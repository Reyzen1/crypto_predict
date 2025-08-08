# File: temp/start-workers.ps1
# PowerShell script to manage Celery workers as background jobs

param(
    [string]$Action = "start",
    [switch]$Help
)

# Color functions
function Write-Success { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host $msg -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host $msg -ForegroundColor Red }
function Write-Info { param($msg) Write-Host $msg -ForegroundColor Cyan }

if ($Help) {
    Write-Info "🔧 CryptoPredict Worker Manager"
    Write-Info "=============================="
    Write-Info ""
    Write-Info "Usage: .\temp\start-workers.ps1 [action]"
    Write-Info ""
    Write-Info "Actions:"
    Write-Info "  start    - Start all workers (default)"
    Write-Info "  stop     - Stop all workers"
    Write-Info "  status   - Show worker status"
    Write-Info "  restart  - Restart all workers"
    Write-Info "  logs     - Show recent logs"
    Write-Info ""
    Write-Info "Examples:"
    Write-Info "  .\temp\start-workers.ps1 start"
    Write-Info "  .\temp\start-workers.ps1 status"
    Write-Info "  .\temp\start-workers.ps1 stop"
    exit 0
}

# Change to backend directory
if (-not (Test-Path "backend")) {
    Write-Error "❌ Backend directory not found. Run from project root."
    exit 1
}

Set-Location backend

# Create logs directory
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

function Start-Workers {
    Write-Info "🚀 Starting CryptoPredict Workers"
    Write-Info "================================="

    # Stop existing jobs first
    Stop-Workers -Silent

    # Start Data Worker
    Write-Info "📊 Starting Data Worker..."
    $dataJob = Start-Job -Name "CryptoPredict-DataWorker" -ScriptBlock {
        Set-Location $using:PWD
        celery -A app.tasks.celery_app worker --loglevel=info --queues=price_data,default --pool=solo --concurrency=1 --hostname=data_worker@%h
    }
    
    # Start ML Worker  
    Write-Info "🤖 Starting ML Worker..."
    $mlJob = Start-Job -Name "CryptoPredict-MLWorker" -ScriptBlock {
        Set-Location $using:PWD
        celery -A app.tasks.celery_app worker --loglevel=info --queues=ml_tasks --pool=solo --concurrency=1 --hostname=ml_worker@%h
    }
    
    # Start Beat Scheduler
    Write-Info "⏰ Starting Beat Scheduler..."
    $beatJob = Start-Job -Name "CryptoPredict-Beat" -ScriptBlock {
        Set-Location $using:PWD
        celery -A app.tasks.celery_app beat --loglevel=info --schedule=logs/celerybeat-schedule --pidfile=logs/celerybeat.pid
    }
    
    # Start Flower (optional)
    Write-Info "🌸 Starting Flower Monitor..."
    $flowerJob = Start-Job -Name "CryptoPredict-Flower" -ScriptBlock {
        Set-Location $using:PWD
        celery -A app.tasks.celery_app flower --port=5555 --basic_auth=admin:cryptopredict123
    }

    # Wait a moment for startup
    Start-Sleep 5
    
    # Check status
    Write-Info ""
    Show-Status
    
    Write-Success ""
    Write-Success "🎉 Workers started successfully!"
    Write-Success "================================"
    Write-Success "• Flower Dashboard: http://localhost:5555"
    Write-Success "• Credentials: admin / cryptopredict123"
    Write-Success ""
    Write-Success "Management commands:"
    Write-Success "  Status:  .\temp\start-workers.ps1 status"
    Write-Success "  Stop:    .\temp\start-workers.ps1 stop"
    Write-Success "  Logs:    .\temp\start-workers.ps1 logs"
}

function Stop-Workers {
    param([switch]$Silent)
    
    if (-not $Silent) {
        Write-Warning "🛑 Stopping CryptoPredict Workers"
        Write-Warning "================================="
    }
    
    # Get and stop all CryptoPredict jobs
    $jobs = Get-Job | Where-Object { $_.Name -like "CryptoPredict-*" }
    
    foreach ($job in $jobs) {
        if (-not $Silent) {
            Write-Warning "Stopping $($job.Name)..."
        }
        Stop-Job $job -PassThru | Remove-Job -Force
    }
    
    if (-not $Silent) {
        Write-Success "✅ All workers stopped"
    }
}

function Show-Status {
    Write-Info "📊 Worker Status"
    Write-Info "================"
    
    $jobs = Get-Job | Where-Object { $_.Name -like "CryptoPredict-*" }
    
    if ($jobs.Count -eq 0) {
        Write-Warning "No CryptoPredict workers running"
        return
    }
    
    foreach ($job in $jobs) {
        $status = switch ($job.State) {
            "Running" { "✅ Running" }
            "Failed"  { "❌ Failed" }
            "Stopped" { "⏸️ Stopped" }
            default   { "⚠️ $($job.State)" }
        }
        
        Write-Host "  $($job.Name): $status" -ForegroundColor $(
            switch ($job.State) {
                "Running" { "Green" }
                "Failed"  { "Red" }
                default   { "Yellow" }
            }
        )
    }
}

function Show-Logs {
    Write-Info "📝 Recent Worker Logs"
    Write-Info "===================="
    
    $jobs = Get-Job | Where-Object { $_.Name -like "CryptoPredict-*" -and $_.State -eq "Running" }
    
    foreach ($job in $jobs) {
        Write-Info ""
        Write-Info "--- $($job.Name) ---"
        $output = Receive-Job $job -Keep | Select-Object -Last 5
        if ($output) {
            $output | ForEach-Object { Write-Host $_ }
        } else {
            Write-Warning "No recent output"
        }
    }
}

function Restart-Workers {
    Write-Info "🔄 Restarting Workers"
    Write-Info "===================="
    Stop-Workers
    Start-Sleep 3
    Start-Workers
}

# Main execution
switch ($Action.ToLower()) {
    "start"   { Start-Workers }
    "stop"    { Stop-Workers }
    "status"  { Show-Status }
    "restart" { Restart-Workers }
    "logs"    { Show-Logs }
    default   { 
        Write-Error "❌ Unknown action: $Action"
        Write-Info "Use -Help for usage information"
        exit 1
    }
}