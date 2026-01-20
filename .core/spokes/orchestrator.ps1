# .core/spokes/orchestrator.ps1
# The Studio Hive Heartbeat (State & Task Sync)

Import-Module (Join-Path $PSScriptRoot "..\lib\memory_client.psm1") -Force

$API_BASE = "http://localhost:8000"
$POLL_INTERVAL = 3 # Seconds

Write-Host "`n[HIVE] Orchestrator Heartbeat Started." -ForegroundColor Magenta
Write-Host "[HIVE] Monitoring Task Registry at $API_BASE" -ForegroundColor Gray

while($true) {
    try {
        # 1. Fetch Tasks
        $Tasks = Invoke-RestMethod -Uri "$API_BASE/tasks/list" -Method Get
        $Pending = @($Tasks.tasks | Where-Object { $_.status -eq "pending" })
        $Active = @($Tasks.tasks | Where-Object { $_.status -eq "in_progress" })
        
        # 2. Get Current System State
        $CurrentState = (Invoke-RestMethod -Uri "$API_BASE/state" -Method Get).current_state

        # 3. State Decision Logic
        if ($CurrentState -eq "IDLE") {
            if ($Pending.Count -gt 0) {
                Write-Host "[STATE] Work detected. Transitioning to EXECUTING." -ForegroundColor Cyan
                Invoke-RestMethod -Uri "$API_BASE/state/update" -Method Post -Body (@{new_state="EXECUTING"} | ConvertTo-Json) -ContentType "application/json"
            }
        }
        elseif ($CurrentState -eq "EXECUTING") {
            # If no work is left pending or active, move to REVIEW
            if ($Pending.Count -eq 0 -and $Active.Count -eq 0) {
                Write-Host "[STATE] Execution Complete. Transitioning to REVIEW." -ForegroundColor Yellow
                Invoke-RestMethod -Uri "$API_BASE/state/update" -Method Post -Body (@{new_state="REVIEW"} | ConvertTo-Json) -ContentType "application/json"
            }
        }
        elseif ($CurrentState -eq "REVIEW") {
            # If items need review, stay here (Critic is working).
            # If no items are in 'review' status, we are done.
            $TasksInReview = @($Tasks.tasks | Where-Object { $_.status -eq "review" })
            
            Write-Host "[DEBUG] In Review: $($TasksInReview.Count) | All: $($Tasks.tasks.Count)"

            if ($TasksInReview.Count -eq 0) {
                 # Make sure we don't jump back to IDLE if 'pending' tasks appeared during review (Rejected tasks)
                 if ($Pending.Count -gt 0) {
                     Write-Host "[STATE] Tasks Rejected/Added. Returning to PLANNING." -ForegroundColor Cyan
                     # Note: REVIEW -> PLANNING is valid.
                     Invoke-RestMethod -Uri "$API_BASE/state/update" -Method Post -Body (@{new_state="PLANNING"} | ConvertTo-Json) -ContentType "application/json"
                 }
                 else {
                     Write-Host "[STATE] Review Complete. System IDLE." -ForegroundColor Green
                     Invoke-RestMethod -Uri "$API_BASE/state/update" -Method Post -Body (@{new_state="IDLE"} | ConvertTo-Json) -ContentType "application/json"
                 }
            }
        }
        elseif ($CurrentState -eq "PLANNING") {
             # Simple passthrough for now, assuming Planner did its job or we skip it
             Write-Host "[STATE] Planning phase complete. Engaging Workforce." -ForegroundColor Cyan
             Invoke-RestMethod -Uri "$API_BASE/state/update" -Method Post -Body (@{new_state="EXECUTING"} | ConvertTo-Json) -ContentType "application/json"
        }

        # 4. Cleanup (Future: Decay old tasks, handle timeouts)
        
    } catch {
        Write-Host "[!] Orchestrator Error: $($_.Exception.Message)" -ForegroundColor Red
    }

    Start-Sleep -Seconds $POLL_INTERVAL
}
