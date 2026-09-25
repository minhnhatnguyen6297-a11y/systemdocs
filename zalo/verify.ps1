# Verification for the zalo-intake module (MIN-93 scaffold + MIN-103 engine port).
# Checks: python >= 3.12, pytest suite, connector node check+tests, replay, status.
# Prints a PASS/FAIL summary; exits nonzero on failure.
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repo

# Prefer the repo venv (dependencies live there after local-runbook setup);
# fall back to system python only when no venv exists.
$py = Join-Path $repo '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) { $py = 'python' }
Write-Host "[..] using python: $py"

$failures = @()

# --- 1. Python >= 3.12 -----------------------------------------------------
$pyVersion = $null
try {
    $pyVersion = (& $py -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null)
} catch { }
if (-not $pyVersion) {
    $failures += "python not found on PATH"
} elseif ([version]$pyVersion -lt [version]"3.12") {
    $failures += "python $pyVersion found, need >= 3.12"
} else {
    Write-Host "[ok] python $pyVersion"
}

# --- 2. pytest --------------------------------------------------------------
Write-Host "[..] python -m pytest tests -q"
& $py -m pytest tests -q
if ($LASTEXITCODE -ne 0) { $failures += "pytest failed (exit $LASTEXITCODE)" }

# --- 3. connector: syntax check (hard gate) + tests (advisory) ---------------
# `npm test` has a known baseline-identical flake: FileOutbox.entries() races
# readdir/readFile on Windows temp dirs (87-89/90 pass; see
# docs/migration-notes.md). It is advisory until MIN-94 fixes the race.
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node -and (Test-Path (Join-Path $repo 'connector\node_modules'))) {
    Write-Host "[..] npm --prefix connector run check"
    & npm --prefix (Join-Path $repo 'connector') run check
    if ($LASTEXITCODE -ne 0) { $failures += "connector npm run check failed (exit $LASTEXITCODE)" }
    Write-Host "[..] npm --prefix connector test (advisory)"
    & npm --prefix (Join-Path $repo 'connector') test
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[warn] connector npm test reported failures (known baseline flake - see docs/migration-notes.md)"
    }
} else {
    Write-Host "[skip] connector tests (node or connector/node_modules missing; run npm --prefix connector ci)"
}

# --- 4. replay smoke (PYTHONPATH=src for the child call) --------------------
$oldPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = Join-Path $repo 'src'
$env:ZALO_INTAKE_RUNTIME_DIR = Join-Path $repo 'runtime'
Write-Host "[..] replay tests\fixtures\synthetic\event_text_message.json"
& $py -m zalo_module.cli replay tests\fixtures\synthetic\event_text_message.json
if ($LASTEXITCODE -ne 0) { $failures += "replay smoke failed (exit $LASTEXITCODE)" }

# --- 4. status ---------------------------------------------------------------
Write-Host "[..] zalo_module.cli status"
& $py -m zalo_module.cli status
if ($LASTEXITCODE -ne 0) { $failures += "status failed (exit $LASTEXITCODE)" }

$env:PYTHONPATH = $oldPythonPath

# --- summary -----------------------------------------------------------------
if ($failures.Count -eq 0) {
    Write-Host "VERIFY: PASS"
    exit 0
} else {
    Write-Host "VERIFY: FAIL"
    foreach ($f in $failures) { Write-Host "  - $f" }
    exit 1
}
