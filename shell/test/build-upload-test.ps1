# Build TEST package g1-shell-test (MIN-69 T9) — qua `npm run dist:test`.
#
# Khac production:
#   - appId dev.g1.shell.test, productName g1-shell-test → userData rieng
#   - output dist-test/ (khong cham dist-app/)
#   - sidecar build voi G1_SIDECAR_TEST_BUILD=1 → ship e2e_fixture_hook +
#     upload_portal fixture trong _internal (production KHONG ship)
#   - resources/test-pkg/test-build.json — marker main.js doc de bat seam
#     e2e + build label "test"
#
# Production phai build truoc (npm run build:sidecar && npm run dist) —
# script nay KHONG ghi de artifact production.
param([string]$Python = $env:G1_PYTHON)
if (-not $Python) { $Python = "python" }
$ErrorActionPreference = "Stop"
$shell = Split-Path $PSScriptRoot -Parent
Push-Location $shell
try {
    # Stage engine + browsers (chung voi production).
    & (Join-Path $shell "sidecar\stage_package_assets.ps1") -Python $Python

    # Sidecar test build — cung spec, them fixture pathex/hiddenimport.
    $env:G1_SIDECAR_TEST_BUILD = "1"
    Push-Location (Join-Path $shell "sidecar")
    try {
        & $Python -m PyInstaller --noconfirm --clean `
            --distpath (Join-Path $shell "sidecar\dist-test") `
            g1-shell-sidecar.spec
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        $hook = Join-Path $shell (
            "sidecar\dist-test\g1-shell-sidecar\_internal\" +
            "e2e_fixture_hook*")
        $driver = Join-Path $shell (
            "sidecar\dist-test\g1-shell-sidecar\_internal\" +
            "playwright\driver\node.exe")
        if (-not (Test-Path $driver)) {
            Write-Error "Thieu playwright driver trong test sidecar"
        }
    } finally {
        Pop-Location
        Remove-Item Env:G1_SIDECAR_TEST_BUILD -ErrorAction SilentlyContinue
    }

    & npx electron-builder --config test/electron-builder.test.json --dir
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    # Kiem nhanh: marker phai co, exe phai ton tai.
    $marker = Join-Path $shell (
        "dist-test\win-unpacked\resources\test-pkg\test-build.json")
    if (-not (Test-Path $marker)) {
        Write-Error "Thieu marker test build: $marker"
    }
    Write-Host "OK: dist-test/win-unpacked/g1-shell-test.exe"
} finally { Pop-Location }
