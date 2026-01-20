# .core/Conductor.ps1
# The Studio Mode Bootloader

Write-Host "[*] Initializing Studio Mode..." -ForegroundColor Cyan

# 1. Import Client Library
$ModulePath = Join-Path $PSScriptRoot "lib\memory_client.psm1"
if (-not (Test-Path $ModulePath)) {
    Write-Error "CRITICAL: Memory Client module not found at $ModulePath"
    exit 1
}
Import-Module $ModulePath -Force

# 2. Check Memory Daemon
Write-Host "[*] Connecting to Memory Daemon..." -NoNewline
$Health = Get-MemoryHealth
if ($null -eq $Health) {
    Write-Host " [OFFLINE]" -ForegroundColor Red
    Write-Host "[!] Attempting to start Memory Daemon..."
    $DaemonPath = Join-Path $PSScriptRoot "services\memory_server.py"
    Start-Process python -ArgumentList "$DaemonPath" -RedirectStandardOutput ".core\logs\memory_daemon.log" -RedirectStandardError ".core\logs\memory_daemon.err" -NoNewWindow
    Start-Sleep -Seconds 5
    $Health = Get-MemoryHealth
}

if ($Health.status -eq "online") {
    Write-Host " [ONLINE]" -ForegroundColor Green
    Write-Host "    |__ State: $($Health.state)" -ForegroundColor Gray
    Write-Host "    |__ DB:    $($Health.db)" -ForegroundColor Gray
} else {
    Write-Error "FATAL: Could not start Memory Daemon."
    exit 1
}

# 3. Load Personas
$ManagerPersona = Get-Content (Join-Path $PSScriptRoot "agents\manager.md") -Raw
$WorkerPersona = Get-Content (Join-Path $PSScriptRoot "agents\worker.md") -Raw

# 4. Context Handover
Write-Host "`n[*] Studio Mode Ready." -ForegroundColor Cyan
Write-Host "You are now the CONDUCTOR." -ForegroundColor Yellow
Write-Host "Use 'Get-MemoryHealth', 'Search-Memory', and 'Add-MemoryEntry' to manage the session."
Write-Host "---------------------------------------------------------------"
