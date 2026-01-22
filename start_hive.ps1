# start_hive.ps1
# Unified Startup for Studio Mode C.O.R.E.
# Launches Memory Server, Agents, and Orchestrator with logging.

$API_URL = "http://localhost:8000"
$LogsDir = Join-Path $PWD "logs"
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

function Start-ServiceProcess {
    param($Name, $Command, $ScriptArgs, $LogBase)
    Write-Host " [ ] Starting $Name..." -NoNewline
    
    $OutFile = Join-Path $LogsDir "$LogBase.log"
    $ErrFile = Join-Path $LogsDir "$LogBase.err"
    
    # Using RedirectStandardOutput/Error requires the process object to return
    # PowerShell 7 Start-Process -RedirectStandardOutput
    $p = Start-Process $Command -ArgumentList $ScriptArgs -PassThru -WindowStyle Hidden -RedirectStandardOutput $OutFile -RedirectStandardError $ErrFile
    
    if ($p) {
        Write-Host " PID: $($p.Id)" -ForegroundColor Green
    }
    else {
        Write-Host " FAILED!" -ForegroundColor Red
    }
    return $p
}

Write-Host @"
_________________________________________________________________
   _____ _             _ _        __  __           _      
  / ____| |           | (_)      |  \/  |         | |     
 | (___ | |_ _   _  __| |_  ___  | \  / | ___   __| | ___ 
  \___ \| __| | | |/ _` | |/ _ \ | |\/| |/ _ \ / _` |/ _ \
  ____) | |_| |_| | (_| | | (_) | | |  | | (_) | (_| |  __/
 |_____/ \__|\__,_|\__,_|_|\___/  |_|  |_|\___/ \__,_|\___|
                   C.O.R.E. Hive Launcher (Logged)
_________________________________________________________________
"@ -ForegroundColor Cyan

# 1. Start Memory Server
# Use -u for unbuffered python output
$MemProc = Start-ServiceProcess "Memory Server" "python" "-u .core/services/memory_server.py" "memory"

# Wait for Health Check
Write-Host " [?] Waiting for Cortex..." -NoNewline
$Retries = 0
$ServerReady = $false

while (-not $ServerReady -and $Retries -lt 30) {
    try {
        $res = Invoke-RestMethod -Uri "$API_URL" -ErrorAction Stop
        if ($res.status -eq "online") { $ServerReady = $true }
    }
    catch {
        Start-Sleep -Seconds 1
        Write-Host "." -NoNewline
        $Retries++
    }
}

if (-not $ServerReady) {
    Write-Host " FAILED! (Check logs/memory.err)" -ForegroundColor Red
    if ($MemProc) { Stop-Process -Id $MemProc.Id -ErrorAction SilentlyContinue }
    exit
}
Write-Host " ONLINE!" -ForegroundColor Green

# 2. Start Agents
$EngProc = Start-ServiceProcess "Engineer Agent" "python" "-u .core/services/engineer_service.py" "engineer"
$CriticProc = Start-ServiceProcess "Critic Agent" "python" "-u .core/services/critic_service.py" "critic"
$ScoutProc = Start-ServiceProcess "Scout Agent" "python" "-u .core/services/scout_service.py" "scout"

# 3. Start Orchestrator
$OrchProc = Start-ServiceProcess "Orchestrator" "pwsh" "-File .core/spokes/orchestrator.ps1" "orchestrator"

Write-Host "`n[HIVE] System Fully Operational." -ForegroundColor Cyan
Write-Host "[INFO] Logs are in $LogsDir. Press 'Q' then Enter to shutdown." -ForegroundColor Gray

# Loop to keep script alive and listen for exit
while ($true) {
    if ([Console]::KeyAvailable) {
        $key = [Console]::ReadKey($true)
        if ($key.Key -eq 'Q') { break }
    }
    Start-Sleep -Milliseconds 500
}

Write-Host "`n[HIVE] Shutting down..." -ForegroundColor Yellow
$Procs = @($OrchProc, $ScoutProc, $CriticProc, $EngProc, $MemProc)
foreach ($p in $Procs) {
    if ($p) { Stop-Process -Id $p.Id -ErrorAction SilentlyContinue }
}
Write-Host "[HIVE] Offline." -ForegroundColor Red
