# Stage engine + playwright browsers vao shell/build/ cho electron-builder.
# Dung chung cho production (build_sidecar.ps1) va test build
# (test/build-upload-test.ps1) — MIN-69 T9.
#
#   build/engine/<key>/           engine code ship dang source .py
#                                 (engine_roots.bundled_engine_dir —
#                                 KHONG freeze vao exe, giu sys.path
#                                 import giong dev; code/data tach biet)
#   build/playwright-browsers/    chromium-<rev> + chromium_headless_shell
#                                 theo rev pinned trong browsers.json cua
#                                 playwright build — khong tai luc runtime
#
# Engine stage dung ALLOWLIST file/dir — khong ship data, .env, ui_qt,
# tests, DB, downloads cua repo dev. Guard fail neu thay file cam.
param([string]$Python = $env:G1_PYTHON)
if (-not $Python) { $Python = "python" }
$ErrorActionPreference = "Stop"

$sidecar = $PSScriptRoot
$shell = Split-Path $sidecar -Parent
$repo = Split-Path $shell -Parent
$stageRoot = Join-Path $shell "build"

# ------------------------- engine source -------------------------
$engineStage = Join-Path $stageRoot "engine"
if (Test-Path $engineStage) { Remove-Item -Recurse -Force $engineStage }

$allow = @{
    "upload_lab" = @{
        files = @("batch_scan.py", "extract_contract.py",
                  "playwright_uploader.py", "uploader_selectors.py",
                  "__init__.py")
        dirs  = @("providers", "ui")
    }
    "notary_v2" = @{
        files = @("database.py", "models.py")
        dirs  = @("services", "routers", "word_templates",
                  "frontend\templates")
    }
}
foreach ($key in $allow.Keys) {
    $src = Join-Path $repo $key
    $dst = Join-Path $engineStage $key
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    foreach ($f in $allow[$key].files) {
        Copy-Item -Force (Join-Path $src $f) (Join-Path $dst $f)
    }
    foreach ($d in $allow[$key].dirs) {
        $target = Join-Path $dst $d
        New-Item -ItemType Directory -Force `
            -Path (Split-Path $target -Parent) | Out-Null
        Copy-Item -Recurse -Force (Join-Path $src $d) $target
    }
}
# Sach __pycache__ + chan file cam — code only, khong data/Qt.
Get-ChildItem -Recurse -Force -Directory $engineStage |
    Where-Object { $_.Name -eq "__pycache__" } |
    Remove-Item -Recurse -Force
$forbidden = Get-ChildItem -Recurse -Force -File $engineStage |
    Where-Object {
        $_.Name -in @(".env", "notary.db", "registry.sqlite3",
                      "nd_storage_state.json") -or
        $_.FullName -match "ui_qt|tests|poc|tools" -or
        $_.Extension -in @(".db", ".sqlite", ".sqlite3")
    }
if ($forbidden) {
    Write-Error ("Engine stage chua file cam: " +
        ($forbidden | ForEach-Object { $_.FullName }) -join ", ")
}

# -------------------- playwright chromium ------------------------
$rev = & $Python -c (
    "import json,pathlib,playwright;" +
    "p=pathlib.Path(playwright.__file__).parent/" +
    "'driver'/'package'/'browsers.json';" +
    "d=json.loads(p.read_text());" +
    "print(next(b['revision'] for b in d['browsers']" +
    " if b['name']=='chromium'))")
if ($LASTEXITCODE -ne 0 -or -not $rev) {
    throw "khong doc duoc chromium revision tu playwright"
}
$mspw = Join-Path $env:LOCALAPPDATA "ms-playwright"
$pwStage = Join-Path $stageRoot "playwright-browsers"
foreach ($name in @("chromium-$rev",
                    "chromium_headless_shell-$rev")) {
    $srcDir = Join-Path $mspw $name
    if (-not (Test-Path $srcDir)) {
        # Build-time download OK (khong phai runtime cua app).
        Write-Host "Thieu $srcDir — playwright install chromium"
        & $Python -m playwright install chromium
        if ($LASTEXITCODE -ne 0) {
            throw "playwright install chromium that bai"
        }
    }
    $dstDir = Join-Path $pwStage $name
    if (Test-Path $dstDir) { Remove-Item -Recurse -Force $dstDir }
    Copy-Item -Recurse -Force $srcDir $dstDir
    Write-Host "Staged $name -> build/playwright-browsers/"
}
Write-Host "OK stage: $stageRoot"
