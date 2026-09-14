# Build sidecar exe (PyInstaller onedir) — chay tu shell/sidecar/
# Can venv co fastapi/uvicorn/python-docx/PyMuPDF/pyinstaller.
param([string]$Python = $env:G1_PYTHON)
if (-not $Python) { $Python = "python" }
Push-Location $PSScriptRoot
try {
    & $Python -m PyInstaller --noconfirm --clean g1-shell-sidecar.spec
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "OK: dist/g1-shell-sidecar/g1-shell-sidecar.exe"
} finally { Pop-Location }
