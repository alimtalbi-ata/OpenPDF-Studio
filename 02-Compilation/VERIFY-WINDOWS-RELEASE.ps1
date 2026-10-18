# Requires a successful native Windows build. No fabricated binary evidence.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$version = (Get-Content (Join-Path $root 'VERSION.txt') -Raw).Trim()
if ($version -notmatch '^\d+\.\d+$') { throw "Invalid VERSION.txt: $version" }
$binary = Join-Path $root '01-Application/binary'
$required = @(
  "OpenPDF-Studio-V$version-Setup.exe",
  "OpenPDF-Studio-Portable-V$version.exe",
  "binary-manifest-v$version.json",
  "windows-installation-v$version.json",
  'windows-smoke-installer.json',
  'windows-smoke-portable.json'
)
foreach ($name in $required) {
  $path = Join-Path $binary $name
  if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing release artifact: $path" }
  if ((Get-Item -LiteralPath $path).Length -eq 0) { throw "Empty release artifact: $path" }
}
$setup = Join-Path $binary $required[0]
$report = Get-Content (Join-Path $binary "windows-installation-v$version.json") -Raw | ConvertFrom-Json
if ($report.passed -ne $true) { throw 'Windows installation qualification did not pass' }
$hash = (Get-FileHash -LiteralPath $setup -Algorithm SHA256).Hash.ToLowerInvariant()
if (-not $report.setup_sha256 -and -not $report.installer_sha256) {
  throw 'Installation report lacks installer SHA256'
}
$reportedHash = if ($report.setup_sha256) { $report.setup_sha256 } else { $report.installer_sha256 }
if ($reportedHash.ToLowerInvariant() -ne $hash) { throw 'Installer hash differs from installation report' }
Write-Host "Qualified Windows artifacts verified for V$version"
