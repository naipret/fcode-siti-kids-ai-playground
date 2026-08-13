# SITI Gala Launcher (Windows PowerShell)
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "🚀 [SITI Gala Launcher] Starting F-Code SITI AI Playground..." -ForegroundColor Green

if (-not (Test-Path ".venv")) {
    Write-Host "📦 Creating virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "🔄 Activating virtual environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

Write-Host "📌 Checking dependencies..." -ForegroundColor Cyan
pip install --quiet -r app/requirements.txt

New-Item -ItemType Directory -Force -Path "app/assets/audio/koon", "app/assets/audio/timnang", "app/assets/video" | Out-Null

Write-Host "🧹 Cleaning up existing processes on ports 8000 & 8001..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8000,8001 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }

Write-Host "🎮 Launching Game 1: Cùng Koon Đi Tìm Cầu Vồng (Port 8000)..." -ForegroundColor Green
$koonProc = Start-Process python -ArgumentList "app/server.py" -PassThru -NoNewWindow

Write-Host "🎮 Launching Game 2: Tìm Nắng Cùng AI (Port 8001)..." -ForegroundColor Green
$tnProc = Start-Process python -ArgumentList "app/timnang_master.py" -PassThru -NoNewWindow

Write-Host ""
Write-Host "✨ Both servers launched!" -ForegroundColor Gold
Write-Host "   - Game 1: http://localhost:8000" -ForegroundColor White
Write-Host "   - Game 2: http://localhost:8001" -ForegroundColor White
Write-Host "Press Enter to stop servers..." -ForegroundColor Yellow

Read-Host
Stop-Process -Id $koonProc.Id -ErrorAction SilentlyContinue
Stop-Process -Id $tnProc.Id -ErrorAction SilentlyContinue
Write-Host "👋 Stopped servers." -ForegroundColor Green
