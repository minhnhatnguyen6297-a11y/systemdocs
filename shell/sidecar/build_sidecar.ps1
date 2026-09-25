# Build sidecar exe (PyInstaller onedir) + stage engine/browser cho goi.
# Chay tu shell/sidecar/ hoac qua `npm run build:sidecar`.
# Stage chi tiet: stage_package_assets.ps1 (MIN-69 T9).
param([string]$Python = $env:G1_PYTHON,
      [switch]$SkipStage)
if (-not $Python) { $Python = "python" }
$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    if (-not $SkipStage) {
        & (Join-Path $PSScriptRoot "stage_package_assets.ps1") `
            -Python $Python
    }
    & $Python -m PyInstaller --noconfirm --clean g1-shell-sidecar.spec
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    # Kiem nhanh artifact bat buoc — playwright driver phai trong _internal.
    $driver = Join-Path $PSScriptRoot (
        "dist\g1-shell-sidecar\_internal\playwright\driver\node.exe")
    if (-not (Test-Path $driver)) {
        Write-Error "Thieu playwright driver trong goi: $driver"
    }
    Write-Host "OK: dist/g1-shell-sidecar/g1-shell-sidecar.exe"
} finally { Pop-Location }
