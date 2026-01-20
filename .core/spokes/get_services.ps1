Import-Module "$PSScriptRoot/../lib/logger.psm1"

Write-CoreLog "Starting L2 Services Discovery..." "INFO"

try {
    # Get active TCP listening ports
    $NetTCP = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | 
              Select-Object LocalPort, OwningProcess, LocalAddress

    $Results = @()

    foreach ($Port in $NetTCP) {
        # Filter for localhost/0.0.0.0
        if ($Port.LocalAddress -match "::1|127.0.0.1|0.0.0.0") {
            $Proc = Get-Process -Id $Port.OwningProcess -ErrorAction SilentlyContinue
            
            # Deduplicate
            if ($Results.LocalPort -notcontains $Port.LocalPort) {
                $Results += [PSCustomObject]@{
                    Port    = $Port.LocalPort
                    PID     = $Port.OwningProcess
                    Process = if ($Proc) { $Proc.ProcessName } else { "Unknown" }
                    Path    = if ($Proc) { $Proc.Path } else { "Unknown" }
                }
            }
        }
    }
    
    # Sort by Port
    $Results = $Results | Sort-Object Port

    $OutputPath = "$PSScriptRoot/../../docs/system_context/L2_SERVICES.md"

    $MdOutput = @"
# Layer 2: Active Services
**Last Scanned:** $(Get-Date)

| Port | Process | PID | Path |
| :--- | :--- | :--- | :--- |
"@

    foreach ($Row in $Results) {
        # Clean path for Markdown table
        $CleanPath = if ($Row.Path) { $Row.Path.Replace("\", "\\") } else { "" }
        $MdOutput += "`n| $($Row.Port) | $($Row.Process) | $($Row.PID) | $CleanPath |"
    }

    $MdOutput | Out-File -FilePath $OutputPath
    Write-CoreLog "Services inventory written to docs/system_context/L2_SERVICES.md" "INFO"

} catch {
    Write-CoreLog "Failed to map active services: $_" "ERROR"
}
