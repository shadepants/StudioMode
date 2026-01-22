function Write-CoreLog {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Message,
        [ValidateSet("INFO", "WARN", "ERROR")]
        [string]$Level = "INFO"
    )
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    $LogDir = Join-Path $PSScriptRoot "../logs"
    if (!(Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force }
    $LogFile = Join-Path $LogDir "core.log"
    
    $Color = switch ($Level) {
        "ERROR" { "Red" }
        "WARN"  { "Yellow" }
        Default { "Cyan" }
    }
    
    Write-Host $LogEntry -ForegroundColor $Color
    $LogEntry | Out-File -FilePath $LogFile -Append
}

Export-ModuleMember -Function Write-CoreLog