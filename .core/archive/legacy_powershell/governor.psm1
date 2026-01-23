Import-Module "$PSScriptRoot/logger.psm1"

$ConfigPath = Join-Path $PSScriptRoot "../config/governor.json"
$Config = Get-Content $ConfigPath | ConvertFrom-Json

function Test-GovernorPath {
    param (
        [string]$Path
    )
    
    if ([string]::IsNullOrWhiteSpace($Path)) { return $true }

    # Robust path normalization
    $NormalizedPath = [System.IO.Path]::GetFullPath($Path)

    foreach ($Root in $Config.roots) {
        $NormalizedRoot = [System.IO.Path]::GetFullPath($Root)
        if ($NormalizedPath.StartsWith($NormalizedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    
    return $false
}

function Invoke-Governor {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Command,
        [string]$Path,
        [switch]$Force,
        [string]$Reason
    )

    if ($Force) {
        if ([string]::IsNullOrWhiteSpace($Reason)) {
            throw "Governor Override requires a -Reason."
        }
        Write-CoreLog "Governor Override APPROVED: $Reason" "WARN"
        return $true
    }

    # Blocklist Check
    foreach ($Block in $Config.command_blocklist) {
        if ($Command -match "\b$Block\b") {
            Write-CoreLog "Governor BLOCKED Command: $Command" "WARN"
            throw "Governor Blocked: Command '$Command' is restricted."
        }
    }

    # Path Check
    if ($Path) {
        if (-not (Test-GovernorPath -Path $Path)) {
            Write-CoreLog "Governor BLOCKED Path: $Path" "WARN"
            throw "Governor Blocked: Path '$Path' is outside defined Roots."
        }
    }

    Write-CoreLog "Governor ALLOWED: $Command $Path" "INFO"
    return $true
}

Export-ModuleMember -Function Invoke-Governor, Test-GovernorPath