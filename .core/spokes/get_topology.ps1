Import-Module "$PSScriptRoot/../lib/logger.psm1"

Write-CoreLog "Starting L3 Project Topology Discovery..." "INFO"

$SearchPaths = @(
    "C:\Users\User\Repositories",
    "C:\Users\User\Documents",
    "C:\Users\User\Desktop"
)

$Projects = @()

foreach ($Root in $SearchPaths) {
    if (Test-Path $Root) {
        Write-CoreLog "Scanning $Root..." "INFO"
        
        # Find directories containing .git
        $GitDirs = Get-ChildItem -Path $Root -Directory -Recurse -Depth 2 -Filter ".git" -ErrorAction SilentlyContinue
        
        foreach ($GitDir in $GitDirs) {
            $ProjectDir = $GitDir.Parent.FullName
            $Name = $GitDir.Parent.Name
            
            # Determine Stack
            $Stack = "Unknown"
            if (Test-Path "$ProjectDir/package.json") { $Stack = "Node/JS" }
            elseif (Test-Path "$ProjectDir/requirements.txt") { $Stack = "Python" }
            elseif (Test-Path "$ProjectDir/go.mod") { $Stack = "Go" }
            elseif (Test-Path "$ProjectDir/Cargo.toml") { $Stack = "Rust" }
            
            $Projects += [PSCustomObject]@{
                Name = $Name
                Path = $ProjectDir
                Stack = $Stack
                LastMod = (Get-Item $ProjectDir).LastWriteTime
            }
        }
    } else {
        Write-CoreLog "Path not found: $Root" "WARN"
    }
}

$OutputPath = "$PSScriptRoot/../../docs/system_context/L3_TOPOLOGY.md"

$MdOutput = @"
# Layer 3: Project Topology
**Last Scanned:** $(Get-Date)

| Project | Stack | Path | Last Modified |
| :--- | :--- | :--- | :--- |
"@

foreach ($Row in $Projects) {
    $MdOutput += "`n| $($Row.Name) | $($Row.Stack) | $($Row.Path) | $($Row.LastMod) |"
}

$MdOutput | Out-File -FilePath $OutputPath
Write-CoreLog "Topology inventory written to docs/system_context/L3_TOPOLOGY.md" "INFO"