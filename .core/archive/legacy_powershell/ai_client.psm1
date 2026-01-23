# .core/lib/ai_client.psm1

function Invoke-GroqLLM {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [string]$SystemPrompt,

        [Parameter(Mandatory=$true)]
        [string]$UserPrompt,

        [Parameter()]
        [string]$Model = "llama-3.3-70b-versatile",

        [Parameter()]
        [double]$Temperature = 0.5
    )

    $ApiKey = $env:GROQ_API_KEY
    if ([string]::IsNullOrWhiteSpace($ApiKey)) {
        Write-Error "GROQ_API_KEY environment variable is not set."
        return $null
    }

    $Uri = "https://api.groq.com/openai/v1/chat/completions"
    $Headers = @{
        "Authorization" = "Bearer $ApiKey"
        "Content-Type"  = "application/json"
    }

    $Body = @{
        model = $Model
        messages = @(
            @{ role = "system"; content = $SystemPrompt },
            @{ role = "user";   content = $UserPrompt }
        )
        temperature = $Temperature
    } | ConvertTo-Json -Depth 10

    try {
        $Response = Invoke-RestMethod -Uri $Uri -Method Post -Headers $Headers -Body $Body -ErrorAction Stop
        return $Response.choices[0].message.content
    }
    catch {
        Write-Error "Groq API Error: $($_.Exception.Message)"
        if ($_.Exception.Response) {
            $Stream = $_.Exception.Response.GetResponseStream()
            $Reader = New-Object System.IO.StreamReader($Stream)
            Write-Error "Details: $($Reader.ReadToEnd())"
        }
        return $null
    }
}

Export-ModuleMember -Function Invoke-GroqLLM
