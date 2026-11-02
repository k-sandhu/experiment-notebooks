<# One-shot hidden WMI launcher with temporary SYSTEM_REQUIRED lease. -Live is explicit; -Probe is harmless. #>
[CmdletBinding()]
param([string]$Python='C:\Python313\python.exe',[string]$Worker,[string]$Root,[string]$Script,[string]$Amendment,[Parameter(Mandatory=$true)][string]$LogDirectory,[switch]$Live,[switch]$Probe,[ValidateSet(2,10)][int]$ProbeLeaseSeconds=2,[switch]$ProbeCleanup)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($ProbeCleanup -and -not $Probe){throw 'Cleanup fault probe requires -Probe'}
if ($Live -and $Probe) {throw 'Probe cannot enable live calls'}
if (-not $Worker) {$Worker=Join-Path $PSScriptRoot 'scale_detached_worker_004.py'}
foreach($path in @($Python,$Worker,$LogDirectory)) {if (-not [IO.Path]::IsPathRooted($path) -or -not (Test-Path -LiteralPath $path)){throw 'Existing explicit absolute paths required'}}
$pythonw=Join-Path (Split-Path -LiteralPath $Python) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonw)){throw 'pythonw.exe required for hidden WMI worker'}
if ($Probe) {$Root=$LogDirectory;$program=@();$mode='probe'} else {
 foreach($path in @($Root,$Script,$Amendment)){if(-not [IO.Path]::IsPathRooted($path) -or -not(Test-Path -LiteralPath $path)){throw 'Existing explicit study paths required'}}
 $expectedScript=[IO.Path]::GetFullPath((Join-Path $Root 'data\scale_v5\intervention_resume_004\source_snapshot\scale_intervention_resume_004.py'))
 $expectedAmendment=[IO.Path]::GetFullPath((Join-Path $Root 'data\scale_v5\intervention_resume_004\amendment_004.json'))
 if([IO.Path]::GetFullPath($Script) -ne $expectedScript -or [IO.Path]::GetFullPath($Amendment) -ne $expectedAmendment){throw 'Exact004snapshot and amendment required'}
 $program=@('-u',$Script,'interventions','--root',$Root,'--amendment',$Amendment);if($Live){$program+='--live'};$mode='study'
}
$tag='scale004_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'_'+[guid]::NewGuid().ToString('N').Substring(0,8)
$base=Join-Path $LogDirectory $tag
$amendmentSHA=if($Probe){'probe-no-model-calls'}else{(Get-FileHash -Algorithm SHA256 -LiteralPath $Amendment).Hash.ToLowerInvariant()}
$leaseSeconds=if($Probe){$ProbeLeaseSeconds}else{57600}
$payload=[ordered]@{startup_nonce=[guid]::NewGuid().ToString('N');ready=$base+'.ready.json';probe_marker=$base+'.probe-marker.json';probe_cleanup=[bool]$ProbeCleanup;amendment_sha256=$amendmentSHA;lease_hard_cap_s=$leaseSeconds;lease=$base+'.lease.jsonl';mode=$mode;python=$Python;root=$Root;program=$program;claim=$base+'.claim.json';started=$base+'.started.json';finished=$base+'.finished.json';stdout=$base+'.stdout.log';stderr=$base+'.stderr.log'}
$payloadPath=$base+'.payload.json'
[IO.File]::WriteAllText($payloadPath,($payload|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
foreach($value in @($pythonw,$Worker,$payloadPath)){if($value.Contains('"') -or $value.EndsWith('\')){throw 'Invalid process path'}}
$command='"'+$pythonw+'" "'+$Worker+'" --payload "'+$payloadPath+'"'
$result=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$command;CurrentDirectory=$Root}
if ($result.ReturnValue -ne 0){throw ('WMI Create failed: '+$result.ReturnValue)}
$receipt=[ordered]@{launcher_version='scale004-wmi-one-shot-v1';worker_pid=$result.ProcessId;mode=$mode;payload=$payloadPath;started=$payload.started;finished=$payload.finished;stdout=$payload.stdout;stderr=$payload.stderr;lease=$payload.lease;startup_gate=$payload.ready;probe_marker=$payload.probe_marker;probe_cleanup=[bool]$ProbeCleanup;lease_hard_cap_seconds=$leaseSeconds;automatic_restart=$false;live_requested=[bool]$Live;wmi_return_value=$result.ReturnValue}
[IO.File]::WriteAllText(($base+'.launch.json'),($receipt|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$receipt|ConvertTo-Json -Depth 6
