<#
One-shot hidden Windows launcher. It never restarts a process.
No model execution is enabled unless -Live is explicitly supplied.
Dot-source this file to test Start-ScaleDetachedPython with a harmless probe.
#>
[CmdletBinding()]
param(
    [string]$Python,
    [string]$Script,
    [string]$Root,
    [string]$Amendment,
    [string]$LogDirectory,
    [switch]$Live
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-ScaleAbsolutePath {
    param([string]$Value, [switch]$Directory)
    if (-not $Value -or -not [IO.Path]::IsPathRooted($Value)) {
        throw 'Explicit absolute paths are required.'
    }
    $resolved = (Resolve-Path -LiteralPath $Value -ErrorAction Stop).ProviderPath
    $kind = if ($Directory) { 'Container' } else { 'Leaf' }
    if (-not (Test-Path -LiteralPath $resolved -PathType $kind)) {
        throw "Unexpected path type: $resolved"
    }
    return $resolved
}

function ConvertTo-ScaleQuotedArgument {
    param([string]$Value)
    # Windows file names cannot contain quotes. All arguments here are fixed
    # switches or validated paths, and trailing backslashes are not accepted.
    if ($Value.Contains('"') -or $Value.EndsWith('\')) {
        throw 'Unsupported quote or trailing backslash in argument.'
    }
    return '"' + $Value + '"'
}

function Start-ScaleDetachedPython {
    param(
        [Parameter(Mandatory=$true)][string]$PythonPath,
        [Parameter(Mandatory=$true)][string[]]$ProgramArguments,
        [Parameter(Mandatory=$true)][string]$WorkingDirectory,
        [Parameter(Mandatory=$true)][string]$OutputDirectory,
        [Parameter(Mandatory=$true)][string]$Label
    )
    $executable = Get-ScaleAbsolutePath $PythonPath
    $working = Get-ScaleAbsolutePath $WorkingDirectory -Directory
    if (-not [IO.Path]::IsPathRooted($OutputDirectory)) {
        throw 'Log directory must be an explicit absolute path.'
    }
    if ($Label -notmatch '^[a-z0-9_-]+$') { throw 'Invalid operational log label.' }
    if (-not (Test-Path -LiteralPath $OutputDirectory)) {
        New-Item -ItemType Directory -Path $OutputDirectory -ErrorAction Stop | Out-Null
    }
    $logs = Get-ScaleAbsolutePath $OutputDirectory -Directory
    $tag = $Label + '_' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + '_' + [guid]::NewGuid().ToString('N').Substring(0,8)
    $stdout = Join-Path $logs ($tag + '.stdout.log')
    $stderr = Join-Path $logs ($tag + '.stderr.log')
    $receiptPath = Join-Path $logs ($tag + '.launch.json')
    $arguments = @($ProgramArguments | ForEach-Object { ConvertTo-ScaleQuotedArgument $_ })
    $child = Start-Process -FilePath $executable -ArgumentList $arguments `
        -WorkingDirectory $working -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    $receipt = [ordered]@{
        launcher_version = 'scale-detached-launch-v1'
        pid = $child.Id
        process_created_at_utc = $child.StartTime.ToUniversalTime().ToString('o')
        process_created_utc_ticks = $child.StartTime.ToUniversalTime().Ticks
        python = $executable
        script = $ProgramArguments[1]
        arguments = $ProgramArguments
        working_directory = $working
        stdout_log = $stdout
        stderr_log = $stderr
        receipt = $receiptPath
        automatic_restart = $false
    }
    $json = $receipt | ConvertTo-Json -Depth 5
    # Exclusive receipt creation preserves every prior launch identity.
    $stream = [IO.File]::Open($receiptPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
    try {
        $bytes = [Text.UTF8Encoding]::new($false).GetBytes($json + "`n")
        $stream.Write($bytes, 0, $bytes.Length)
    } finally { $stream.Dispose() }
    return [pscustomobject]$receipt
}

if ($MyInvocation.InvocationName -ne '.') {
    $pythonPath = Get-ScaleAbsolutePath $Python
    $rootPath = Get-ScaleAbsolutePath $Root -Directory
    $scriptPath = Get-ScaleAbsolutePath $Script
    $amendmentPath = Get-ScaleAbsolutePath $Amendment
    $data = Join-Path $rootPath 'data\scale_v5'
    $expectedScript = [IO.Path]::GetFullPath((Join-Path $data 'intervention_resume\source_snapshot\scale_intervention_resume.py'))
    $expectedAmendment = [IO.Path]::GetFullPath((Join-Path $data 'intervention_resume\amendment_002.json'))
    if ($scriptPath -ne $expectedScript -or $amendmentPath -ne $expectedAmendment) {
        throw 'Use the exact reviewed companion snapshot and amendment_002 for this root.'
    }
    $program = @('-u', $scriptPath, 'interventions', '--root', $rootPath, '--amendment', $amendmentPath)
    if ($Live.IsPresent) { $program += '--live' }
    Start-ScaleDetachedPython -PythonPath $pythonPath -ProgramArguments $program `
        -WorkingDirectory $rootPath -OutputDirectory $LogDirectory -Label 'scale_intervention_resume' | ConvertTo-Json -Depth 5
}
