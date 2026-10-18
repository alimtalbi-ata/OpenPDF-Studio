param(
 [Parameter(Mandatory=$true)][string]$SetupExe,
 [Parameter(Mandatory=$true)][string]$ReportPath
)
$ErrorActionPreference='Stop'
$report=[ordered]@{version='40.2';kind='real-installer-install-uninstall';passed=$false;steps=@();utc=(Get-Date).ToUniversalTime().ToString('o')}
$folder=Join-Path $env:TEMP ('OpenPDF-V402-'+[guid]::NewGuid().ToString('N'))
$marker=Join-Path $env:TEMP ('OpenPDF-V402-'+[guid]::NewGuid().ToString('N')+'.marker')
function Run-Checked([string]$file,[string[]]$arguments,[int]$timeout=120000) {
 $p=Start-Process -FilePath $file -ArgumentList $arguments -Wait:$false -PassThru
 if (-not $p.WaitForExit($timeout)) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue;throw "Timed out: $file" }
 if ($p.ExitCode -ne 0) {throw "Exit code $($p.ExitCode): $file"}
}
try {
 if (-not (Test-Path -LiteralPath $SetupExe -PathType Leaf)) {throw 'Installer missing'}
 Run-Checked $SetupExe @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',"/DIR=$folder")
 $report.steps+= 'silent_install_pass'
 $exe=Join-Path $folder 'OpenPDF-Studio.exe'
 if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {throw 'Installed executable missing'}
 $env:OPENPDF_SMOKE_OUTPUT=$marker
 try {Run-Checked $exe @('--self-test')} finally {Remove-Item Env:OPENPDF_SMOKE_OUTPUT -ErrorAction SilentlyContinue}
 if (-not (Test-Path -LiteralPath $marker) -or (Get-Content -Raw $marker) -notmatch 'OPENPDF_SELF_TEST_OK') {throw 'Installed application self-test failed'}
 $report.steps+='installed_launch_pass'
 $unins=Join-Path $folder 'unins000.exe'
 if (-not (Test-Path -LiteralPath $unins -PathType Leaf)) {throw 'Uninstaller missing'}
 Run-Checked $unins @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART')
 $report.steps+='silent_uninstall_pass'
 if (Test-Path -LiteralPath $exe -PathType Leaf) {throw 'Executable remains after uninstall'}
 $report.passed=$true
} catch { $report.error=$_.Exception.Message }
finally {
 Remove-Item -LiteralPath $marker -Force -ErrorAction SilentlyContinue
 if (Test-Path -LiteralPath $folder) {
   $uninstaller=Join-Path $folder 'unins000.exe'
   if (Test-Path -LiteralPath $uninstaller) {
     try { Run-Checked $uninstaller @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') 120000 } catch { $report.cleanup_error=$_.Exception.Message }
   }
 }
 $report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
}
if (-not $report.passed) { Write-Error "Windows installer integration failed: $ReportPath";exit 1 }
Write-Host 'Windows installer integration PASS'
