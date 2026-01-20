Import-Module "$PSScriptRoot/../lib/logger.psm1"

Write-CoreLog "Starting L1 Toolchain Discovery..." "INFO"

$Tools = @(
    @{ Name = "Node"; Command = "node -v" },
    @{ Name = "pnpm"; Command = "pnpm -v" },
    @{ Name = "npm"; Command = "npm -v" },
    @{ Name = "Python"; Command = "python --version" },
    @{ Name = "Pip"; Command = "pip --version" },
    @{ Name = "Git"; Command = "git --version" },
    @{ Name = "Go"; Command = "go version" },
    @{ Name = "Docker"; Command = "docker --version" }
)

$Results = @()

foreach ($Tool in $Tools) {
    try {
        $Version = Invoke-Expression $Tool.Command -ErrorAction SilentlyContinue | Out-String
        if ($Version) {
            $Results += [PSCustomObject]@{
                Name    = $Tool.Name
                Version = $Version.Trim()
                Status  = "Installed"
            }
        } else {
            $Results += [PSCustomObject]@{
                Name    = $Tool.Name
                Version = "N/A"
                Status  = "Not Found"
            }
        }
    } catch {
        $Results += [PSCustomObject]@{
            Name    = $Tool.Name
            Version = "N/A"
            Status  = "Not Found"
        }
    }
}

$OutputPath = "$PSScriptRoot/../../docs/system_context/L1_TOOLCHAIN.md"

$MdOutput = @"
# Layer 1: Toolchain
**Last Scanned:** $(Get-Date)

| Tool | Version | Status |
| :--- | :--- | :--- |
"@

foreach ($Row in $Results) {
    $MdOutput += "`n| $($Row.Name) | $($Row.Version) | $($Row.Status) |"
}

$MdOutput | Out-File -FilePath $OutputPath
Write-CoreLog "Toolchain inventory written to docs/system_context/L1_TOOLCHAIN.md" "INFO"