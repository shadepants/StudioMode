
# Studio Mode Conductor
# =====================
# Orchestrates the Governed Hive: Memory Server, Engineer, Critic, and Scout services.

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Resolve-Path "$PSScriptRoot\.."

Write-Host "--- STANDING UP THE GOVERNED HIVE ---" -ForegroundColor Cyan

# 1. Start Memory Server (The Spine)
Write-Host "[1/4] Starting Memory Server (Port 8000)..." -ForegroundColor Yellow
Start-Process python -ArgumentList ".core/services/memory_server.py" -NoNewWindow -PassThru

# 2. Start Engineer Service
Write-Host "[2/4] Starting Engineer Service (Port 8001)..." -ForegroundColor Yellow
Start-Process python -ArgumentList ".core/services/engineer_service.py" -NoNewWindow -PassThru

# 3. Start Critic Service
Write-Host "[3/4] Starting Critic Service (Port 8002)..." -ForegroundColor Yellow
Start-Process python -ArgumentList ".core/services/critic_service.py" -NoNewWindow -PassThru

# 4. Start Scout Service
Write-Host "[4/4] Starting Scout Service (Port 8003)..." -ForegroundColor Yellow
Start-Process python -ArgumentList ".core/services/scout_service.py" -NoNewWindow -PassThru

Write-Host "--- HIVE IS ONLINE ---" -ForegroundColor Green
Write-Host "Memory Server: http://localhost:8000"
Write-Host "Engineer:      http://localhost:8001"
Write-Host "Critic:        http://localhost:8002"
Write-Host "Scout:         http://localhost:8003"
Write-Host ""
Write-Host "To start the autonomous loop, run: .core/Conductor.ps1 -Loop"
