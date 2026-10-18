param([Parameter(Mandatory=$true)][ValidateSet('installer','portable')][string]$Mode,[Parameter(Mandatory=$true)][string]$SourceDir,[Parameter(Mandatory=$true)][string]$ReportPath)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path $SourceDir).Path
$exe = if ($Mode -eq 'installer') { Join-Path $source 'dist\OpenPDF-Studio\OpenPDF-Studio.exe' } else { Join-Path (Split-Path -Parent $ReportPath) 'OpenPDF-Studio-Portable-V40.2.exe' }
$report = [ordered]@{version='40.2';mode=$Mode;host=$env:COMPUTERNAME;exe=$exe;exists=$false;checks=@();passed=$false;utc=(Get-Date).ToUniversalTime().ToString('o')}
try {
  if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw "Executable missing: $exe" }
  $report.exists = $true
  foreach ($check in @(@{arg='--self-test';marker='OPENPDF_SELF_TEST_OK'},@{arg='--functional-self-test';marker='OPENPDF_FUNCTIONAL_TEST_OK'})) {
    $out = Join-Path $env:TEMP ([guid]::NewGuid().ToString() + '.out')
    $err = Join-Path $env:TEMP ([guid]::NewGuid().ToString() + '.err')
    $result = [ordered]@{argument=$check.arg;exit_code=$null;stdout='';stderr='';timed_out=$false;passed=$false}
    try {
      $markerFile = Join-Path $env:TEMP ([guid]::NewGuid().ToString() + '.marker')
      $env:OPENPDF_SMOKE_OUTPUT = $markerFile
      try { $p = Start-Process -FilePath $exe -ArgumentList $check.arg -PassThru -RedirectStandardOutput $out -RedirectStandardError $err } finally { Remove-Item Env:OPENPDF_SMOKE_OUTPUT -ErrorAction SilentlyContinue }
      if (-not $p.WaitForExit(90000)) {
        $result.timed_out = $true
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        $p.WaitForExit()
      } else { $result.exit_code = $p.ExitCode }
      $result.stdout = if (Test-Path -LiteralPath $markerFile) { Get-Content -Raw -LiteralPath $markerFile } else { Get-Content -Raw -LiteralPath $out -ErrorAction SilentlyContinue }
      $result.stderr = Get-Content -Raw -LiteralPath $err -ErrorAction SilentlyContinue
      $result.passed = (-not $result.timed_out -and $result.exit_code -eq 0 -and $result.stdout -match $check.marker)
    } finally { Remove-Item -LiteralPath $out,$err,$markerFile -Force -ErrorAction SilentlyContinue }
    $report.checks += $result
    if (-not $result.passed) { break }
  }
  $report.passed = ($report.checks.Count -eq 2 -and @($report.checks | Where-Object { -not $_.passed }).Count -eq 0)
} catch { $report.error = $_.Exception.Message }
$report | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
if (-not $report.passed) { Write-Error "Windows smoke test failed; see $ReportPath"; exit 1 }
Write-Host "Windows smoke test PASS: $Mode"
