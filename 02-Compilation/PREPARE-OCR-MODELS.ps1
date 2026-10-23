# V51.3: download ONLY at build time, pin SHA256, fail closed.
# Official Apache-2.0 tesseract-ocr/tessdata_fast eng/fra models.
# Author: Abdelhalim Talbi.
param([string]$TargetDir = '')
$ErrorActionPreference = 'Stop'
if (-not $TargetDir) { $TargetDir = Join-Path (Split-Path -Parent $PSScriptRoot) '03-Sources/build-ocr-models/tessdata' }
$models = @(
  @{Name='eng'; Size=4113088; Sha='7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2'},
  @{Name='fra'; Size=1130365; Sha='ced037562e8c80c13122dece28dd477d399af80911a28791a66a63ac1e3445ca'}
)
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
if ((Get-Item -LiteralPath $TargetDir -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'OCR model directory is a reparse point' }
foreach ($model in $models) {
  $path = Join-Path $TargetDir ($model.Name + '.traineddata')
  $valid = $false
  if (Test-Path -LiteralPath $path -PathType Leaf) {
    $item = Get-Item -LiteralPath $path -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "OCR model is a reparse point: $path" }
    $valid = ($item.Length -eq $model.Size -and (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -eq $model.Sha)
  }
  if (-not $valid) {
    if (Test-Path -LiteralPath $path) { throw "Existing OCR model has wrong SHA256: $path" }
    $temp = "$path.download"
    if (Test-Path -LiteralPath $temp) { throw "Temporary OCR download exists: $temp" }
    try {
      $url = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/$($model.Name).traineddata"
      Invoke-WebRequest -Uri $url -OutFile $temp -UseBasicParsing -MaximumRedirection 3
      $download = Get-Item -LiteralPath $temp
      $hash = (Get-FileHash -LiteralPath $temp -Algorithm SHA256).Hash.ToLowerInvariant()
      if ($download.Length -ne $model.Size -or $hash -ne $model.Sha) { throw "OCR model SHA256 mismatch: $($model.Name)" }
      Move-Item -LiteralPath $temp -Destination $path -ErrorAction Stop
    } finally { Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue }
  }
  Write-Host "OCR model verified: $($model.Name) $($model.Sha)"
}
# Preserve the upstream Apache-2.0 license alongside redistributed model files.
$license = Join-Path $TargetDir 'LICENSE-tessdata-fast.txt'
if (-not (Test-Path -LiteralPath $license -PathType Leaf)) {
  $temp = "$license.download"
  try {
    Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/LICENSE' -OutFile $temp -UseBasicParsing -MaximumRedirection 3
    if ((Get-Item -LiteralPath $temp).Length -lt 5000) { throw 'OCR license download unexpectedly short' }
    Move-Item -LiteralPath $temp -Destination $license -ErrorAction Stop
  } finally { Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue }
}
Write-Host 'OCR_MODELS_BUILD_READY'
