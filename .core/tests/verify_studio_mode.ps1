# .core/tests/verify_studio_mode.ps1

$ErrorActionPreference = "Stop"
$ModulePath = Join-Path $PSScriptRoot "..\lib\memory_client.psm1"
$ReportPath = Join-Path $PSScriptRoot "..\..\docs\system_context\TEST_REPORT.md"
$TestResults = @()

function Log-Test {
    param (
        [string]$Name,
        [string]$Status,
        [string]$Details
    )
    $Global:TestResults += [PSCustomObject]@{
        TestName = $Name
        Status   = $Status
        Details  = $Details
        Time     = Get-Date -Format "HH:mm:ss"
    }
    
    $Color = if ($Status -eq "PASS") { "Green" } else { "Red" }
    Write-Host "[$Status] $Name" -ForegroundColor $Color
    if ($Status -eq "FAIL") { Write-Host "    |__ $Details" -ForegroundColor Gray }
}

Write-Host "[*] Starting Studio Mode System Verification..." -ForegroundColor Cyan

# 1. Setup & Imports
try {
    Import-Module $ModulePath -Force
    Log-Test "Import Memory Client" "PASS" "Module loaded from $ModulePath"
}
catch {
    Log-Test "Import Memory Client" "FAIL" $_.Exception.Message
    exit 1
}

# 2. Health Check
try {
    $Health = Get-MemoryHealth
    if ($Health.status -eq "online" -and $Health.mode -eq "hybrid") {
        Log-Test "Server Health" "PASS" "Online, Mode: Hybrid, DB: $($Health.db)"
    } else {
        Log-Test "Server Health" "FAIL" "Invalid Response: $($Health | ConvertTo-Json -Depth 1)"
    }
}
catch {
    Log-Test "Server Health" "FAIL" "Connection Refused. Is the daemon running?"
}

# 3. Vector Memory (LanceDB)
try {
    $TestId = "test-vector-$(New-Guid)"
    # IMPORTANT: Include ID in text so semantic search finds it easily
    $Entry = Add-MemoryEntry -Text "This is a unique verification entry for ID $TestId" -Type "fact" -Metadata @{ "test_run" = $TestId }
    
    if ($Entry.status -eq "success") {
        Write-Host "    |__ Waiting 5s for vector index..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
        $Results = Search-Memory -Query $TestId -Limit 1
        
        if ($Results.Count -gt 0 -and $Results[0].text -match $TestId) {
            Log-Test "Vector Read/Write" "PASS" "Successfully wrote and retrieved vector data."
        } else {
            Log-Test "Vector Read/Write" "FAIL" "Retrieved entry did not match. Found: $($Results[0].text)"
        }
    } else {
        Log-Test "Vector Read/Write" "FAIL" "Write failed."
    }
}
catch {
    Log-Test "Vector Read/Write" "FAIL" $_.Exception.Message
}

# 4. Transactional Tasks (SQLite)
try {
    # Create
    $Task = Add-Task -Text "Unit Test Task" -Assignee "Tester" -Priority "low"
    $TaskId = $Task.task_id
    
    # List
    $Pending = Get-Tasks -Status "pending"
    $Found = $Pending | Where-Object { $_.id -eq $TaskId }
    
    # Update
    if ($Found) {
        $Update = Update-Task -TaskId $TaskId -Status "completed"
        $Completed = Get-Tasks -Status "completed"
        $Verify = $Completed | Where-Object { $_.id -eq $TaskId }
        
        if ($Verify) {
            Log-Test "Task CRUD (SQLite)" "PASS" "Create -> List -> Update -> Verify cycle complete."
        } else {
            Log-Test "Task CRUD (SQLite)" "FAIL" "Task update verification failed."
        }
    } else {
        Log-Test "Task CRUD (SQLite)" "FAIL" "Created task not found in pending list."
    }
}
catch {
    Log-Test "Task CRUD (SQLite)" "FAIL" $_.Exception.Message
}

# 5. State Machine & Edge Cases
try {
    # Valid Transition: Reset to IDLE first
    # We use -ErrorAction SilentlyContinue because we might already be IDLE
    try { Set-AgentState -NewState "IDLE" -ErrorAction Stop | Out-Null } catch {}
    
    $Trans1 = Set-AgentState -NewState "PLANNING"
    
    # Invalid Transition Check
    $InvalidTransitionCaught = $false
    try {
        Set-AgentState -NewState "REVIEW" -ErrorAction Stop
    }
    catch {
        $InvalidTransitionCaught = $true
        Log-Test "Edge Case: Invalid State" "PASS" "Server correctly rejected PLANNING -> REVIEW transition."
    }
    
    if (-not $InvalidTransitionCaught) {
         Log-Test "Edge Case: Invalid State" "FAIL" "Server allowed PLANNING -> REVIEW transition."
    }
    
    # Cleanup
    try { Set-AgentState -NewState "IDLE" -ErrorAction Stop | Out-Null } catch {}
}
catch {
    Log-Test "State Machine" "FAIL" "Unexpected error in state flow: $($_.Exception.Message)"
}

# 6. Generate Report
$ReportContent = @"
# Studio Mode System Verification Report
**Date:** $(Get-Date)
**Tester:** Automated Script

## Summary
| Test Case | Status | Details |
| :--- | :--- | :--- |
"@

foreach ($res in $TestResults) {
    $ReportContent += "`n| **$($res.TestName)** | $($res.Status) | $($res.Details) |"
}

$ReportContent | Out-File -FilePath $ReportPath -Encoding utf8
Write-Host "`n[*] Report generated at: $ReportPath" -ForegroundColor Cyan