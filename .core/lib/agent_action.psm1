Import-Module "$PSScriptRoot/governor.psm1"

function Invoke-AgentAction {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Command,
        
        [string]$Path,
        
        [switch]$Force,
        [string]$Reason
    )

    try {
        # Check Governor
        Invoke-Governor -Command $Command -Path $Path -Force:$Force -Reason $Reason

        # Execute
        if ($Path) {
            Invoke-Expression "$Command '$Path'"
        } else {
            Invoke-Expression $Command
        }
        
    } catch {
        Write-Error $_.Exception.Message
    }
}

Export-ModuleMember -Function Invoke-AgentAction