# OpenPDF Studio - cumulative Windows release packaging
# Author: Abdelhalim Talbi
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root
$version = (Get-Content 'VERSION.txt' -Raw).Trim()
if ($version -notmatch '^[0-9]+(\.[0-9]+)*$') { throw "Invalid version: $version" }
$release = Join-Path $root '01-Application/release'
New-Item -ItemType Directory -Force -Path $release | Out-Null
$tempRoot = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [System.IO.Path]::GetTempPath() }
$stage = Join-Path $tempRoot "OpenPDF-Studio-V$version-Windows-Cumulative"
if (Test-Path $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
New-Item -ItemType Directory -Path $stage | Out-Null
$folders = @('01-Application','02-Compilation','03-Sources','04-Tests-et-Qualification','05-Documentation','06-Historique','07-Manifestes')
foreach ($folder in $folders) {
  $src = Join-Path $root $folder
  if (!(Test-Path $src)) { throw "Missing mandatory folder: $folder" }
  $dst = Join-Path $stage $folder
  if ($folder -eq '01-Application') {
    New-Item -ItemType Directory -Path $dst | Out-Null
    Copy-Item (Join-Path $src 'binary') $dst -Recurse -Force
    Get-ChildItem $src -File | Copy-Item -Destination $dst
  } else {
    Copy-Item $src $dst -Recurse -Force
  }
}
foreach ($file in @('README.md','LISEZ-MOI.md','VERSION.txt')) {
  if (Test-Path $file) { Copy-Item $file $stage }
}
$exe = @(Get-ChildItem (Join-Path $stage '01-Application/binary') -Filter '*.exe' -File)
if ($exe.Count -lt 2) { throw 'Expected installer and portable EXE in binary folder' }
$hashes = $exe | ForEach-Object {
  $hash = Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
  [pscustomobject]@{ filename = $_.Name; sha256 = $hash.Hash.ToLowerInvariant(); bytes = $_.Length }
}
$manifestDir = Join-Path $stage '07-Manifestes'
$hashes | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $manifestDir 'WINDOWS-BINARY-SHA256.json') -Encoding UTF8
@(
  "OpenPDF Studio V$version - Windows cumulative delivery"
  "Author: Abdelhalim Talbi"
  "Source commit: $env:GITHUB_SHA"
  "Windows GitHub Actions qualification: automated build and static/unit checks."
  "Real Windows desktop visual inspection: NOT PERFORMED by this CI."
  "Screenshots: only actual existing files, if any; none are fabricated."
  "Existing Word/PDF documentation is included as found in repository; no claim of version-specific refresh."
) | Set-Content (Join-Path $manifestDir 'RELEASE-QUALIFICATION-LIMITS.txt') -Encoding UTF8
# Integrity inventory covers every staged payload file (excluding the inventory itself).
# Sorted paths and SHA256 make archive contents independently verifiable.
$inventory = @(
  Get-ChildItem -LiteralPath $stage -File -Recurse |
    Where-Object { $_.FullName -ne (Join-Path $manifestDir 'RELEASE-FILES-SHA256.json') } |
    Sort-Object FullName |
    ForEach-Object {
      [pscustomobject]@{
        path = $_.FullName.Substring($stage.Length + 1).Replace('\\','/')
        bytes = $_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
      }
    }
)
$inventory | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $manifestDir 'RELEASE-FILES-SHA256.json') -Encoding UTF8
$zip = Join-Path $release "OpenPDF-Studio-V$version-Windows-Cumulative.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -CompressionLevel Optimal
if (!(Test-Path $zip)) { throw 'ZIP was not generated' }
Write-Host "Cumulative release: $zip"
Get-Item $zip | Select-Object Name,Length

# Fail the release if the ZIP does not contain the expected integrity inventory.
Add-Type -AssemblyName System.IO.Compression
$archive = [System.IO.Compression.ZipFile]::OpenRead($zip)
try {
  $entry = $archive.Entries | Where-Object { $_.FullName -eq '07-Manifestes/RELEASE-FILES-SHA256.json' } | Select-Object -First 1
  if (-not $entry) { throw 'Integrity inventory missing from ZIP' }
  if ($archive.Entries.Count -lt $inventory.Count) { throw 'ZIP entries unexpectedly incomplete' }
} finally { $archive.Dispose() }
Write-Host "Integrity inventory: $($inventory.Count) files"
