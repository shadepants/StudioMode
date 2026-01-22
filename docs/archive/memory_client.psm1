# .core/lib/memory_client.psm1

$script:BaseUrl = "http://127.0.0.1:8000"

function Get-MemoryHealth {
    [CmdletBinding()]
    [OutputType([PSCustomObject])]
    param()
    process {
        try {
            return Invoke-RestMethod -Uri "$script:BaseUrl/" -Method Get -ErrorAction Stop
        }
        catch {
            Write-Error "Memory Daemon is offline: $($_.Exception.Message)"
            return $null
        }
    }
}

# --- KNOWLEDGE & EPISODIC MEMORY (LanceDB) ---

function Add-MemoryEntry {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [string]$Text,

        [Parameter(Mandatory=$true)]
        [ValidateSet("episodic", "fact", "knowledge")]
        [string]$Type,

        [Parameter()]
        [hashtable]$Metadata = @{}
    )
    process {
        $Body = @{
            text     = $Text
            type     = $Type
            metadata = $Metadata
        } | ConvertTo-Json

        try {
            return Invoke-RestMethod -Uri "$script:BaseUrl/memory/add" -Method Post -Body $Body -ContentType "application/json"
        }
        catch {
            Write-Error "Failed to add memory: $($_.Exception.Message)"
        }
    }
}

function Search-Memory {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [string]$Query,

        [Parameter()]
        [int]$Limit = 3,

        [Parameter()]
        [string]$FilterType
    )
    process {
        $Body = @{
            text        = $Query
            limit       = $Limit
            filter_type = $FilterType
        } | ConvertTo-Json

        try {
            $Response = Invoke-RestMethod -Uri "$script:BaseUrl/memory/query" -Method Post -Body $Body -ContentType "application/json"
            return $Response.results
        }
        catch {
            Write-Error "Failed to query memory: $($_.Exception.Message)"
        }
    }
}

# --- TASK MANAGEMENT (SQLite) ---

function Add-Task {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [string]$Text,

        [Parameter(Mandatory=$true)]
        [string]$Assignee,

        [Parameter()]
        [string]$Priority = "normal",

        [Parameter()]
        [hashtable]$Metadata = @{}
    )
    process {
        $Body = @{
            text     = $Text
            assignee = $Assignee
            priority = $Priority
            metadata = $Metadata
        } | ConvertTo-Json

        try {
            return Invoke-RestMethod -Uri "$script:BaseUrl/tasks/create" -Method Post -Body $Body -ContentType "application/json"
        }
        catch {
            Write-Error "Failed to create task: $($_.Exception.Message)"
        }
    }
}

function Get-Tasks {
    [CmdletBinding()]
    param (
        [Parameter()]
        [string]$Status,

        [Parameter()]
        [string]$Assignee
    )
    process {
        $Uri = "$script:BaseUrl/tasks/list?"
        if ($Status) { $Uri += "status=$Status&" }
        if ($Assignee) { $Uri += "assignee=$Assignee" }

        try {
            $Response = Invoke-RestMethod -Uri $Uri -Method Post
            return $Response.tasks
        }
        catch {
            Write-Error "Failed to list tasks: $($_.Exception.Message)"
        }
    }
}

function Update-Task {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [string]$TaskId,

        [Parameter(Mandatory=$true)]
        [string]$Status,

        [Parameter()]
        [hashtable]$Metadata = @{}
    )
    process {
        $Body = @{
            task_id  = $TaskId
            status   = $Status
            metadata = $Metadata
        } | ConvertTo-Json

        try {
            return Invoke-RestMethod -Uri "$script:BaseUrl/tasks/update" -Method Post -Body $Body -ContentType "application/json"
        }
        catch {
            Write-Error "Failed to update task: $($_.Exception.Message)"
        }
    }
}

# --- STATE MANAGEMENT ---

function Get-AgentState {
    [CmdletBinding()]
    param()
    process {
        try {
            $Response = Invoke-RestMethod -Uri "$script:BaseUrl/state" -Method Get
            return $Response.current_state
        }
        catch {
            Write-Error "Failed to get state: $($_.Exception.Message)"
        }
    }
}

function Set-AgentState {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [ValidateSet("IDLE", "PLANNING", "EXECUTING", "REVIEW")]
        [string]$NewState
    )
    process {
        $Body = @{
            new_state = $NewState
        } | ConvertTo-Json

        try {
            return Invoke-RestMethod -Uri "$script:BaseUrl/state/update" -Method Post -Body $Body -ContentType "application/json"
        }
        catch {
            Write-Error "Failed to update state: $($_.Exception.Message)"
        }
    }
}

Export-ModuleMember -Function Get-MemoryHealth, Add-MemoryEntry, Search-Memory, Add-Task, Get-Tasks, Update-Task, Get-AgentState, Set-AgentState
