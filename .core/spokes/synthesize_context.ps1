Import-Module "$PSScriptRoot/../lib/logger.psm1"

Write-CoreLog "Starting System Context Synthesis..." "INFO"

$OutFile = "$PSScriptRoot/../../docs/system_context/SYSTEM_CONTEXT.md"
$Header = @"
# System Digital Twin
**Generated:** $(Get-Date)
**Host:** $env:COMPUTERNAME
**User:** $env:USERNAME

---
"@

$Header | Out-File -FilePath $OutFile

# Append Layers
$Layers = @("L0_OS_BASICS.md", "L1_TOOLCHAIN.md", "L2_SERVICES.md", "L3_TOPOLOGY.md")

foreach ($Layer in $Layers) {
    $Path = "$PSScriptRoot/../../docs/system_context/$Layer"
    if (Test-Path $Path) {
        Get-Content $Path | Out-File -FilePath $OutFile -Append
        "`n---`n" | Out-File -FilePath $OutFile -Append
    }
}

# Manual Injection for known repos (Fix for flaky L3 script)
@"
## Manual Project Overrides
| Project | Stack | Path |
| :--- | :--- | :--- |
| Pennys-PIMS | Node/React/Supabase | C:\Users\User\Repositories\Pennys-PIMS |
| Psychometrics | Node/TurboRepo | C:\Users\User\Repositories\Psychometrics |
"@ | Out-File -FilePath $OutFile -Append

Write-CoreLog "System Context synthesized to docs/system_context/SYSTEM_CONTEXT.md" "INFO"