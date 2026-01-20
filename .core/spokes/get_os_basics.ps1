Import-Module "$PSScriptRoot/../lib/logger.psm1"

Write-CoreLog "Starting OS Basics Discovery..." "INFO"

try {
    $OS = Get-CimInstance Win32_OperatingSystem
    $ComputerInfo = Get-ComputerInfo -Property "WindowsProductName", "WindowsVersion", "OsArchitecture"

    $Context = @{
        OS_Name = $OS.Caption
        Version = $ComputerInfo.WindowsVersion
        Build   = $OS.BuildNumber
        Arch    = $ComputerInfo.OsArchitecture
        LastBoot = $OS.LastBootUpTime
    }

    $OutputPath = "$PSScriptRoot/../../docs/system_context/L0_OS_BASICS.md"
    
    @"
# Layer 0: OS Basics
**Last Scanned:** $(Get-Date)

| Property | Value |
| :--- | :--- |
| OS | $($Context.OS_Name) |
| Version | $($Context.Version) |
| Build | $($Context.Build) |
| Architecture | $($Context.Arch) |
| Last Boot | $($Context.LastBoot) |
"@ | Out-File -FilePath $OutputPath

    Write-CoreLog "OS Basics written to docs/system_context/L0_OS_BASICS.md" "INFO"
} catch {
    Write-CoreLog "Failed to gather OS basics: $_" "ERROR"
}