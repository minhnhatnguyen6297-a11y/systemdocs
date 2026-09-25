# Build sidecar exe (PyInstaller onedir) — chay tu shell/sidecar/
# Can venv co DAY DU deps engine (xem _ENGINE_DEP_PACKAGES trong spec:
# fastapi, uvicorn, sqlalchemy, python-docx, PyMuPDF, openpyxl, Pillow,
# httpx, rapidfuzz, jinja2, python-multipart, pydantic, python-dotenv,
# tzdata, playwright) + pyinstaller — tham chieu notary_v2/requirements.txt.
param([string]$Python = $env:G1_PYTHON)
if (-not $Python) { $Python = "python" }
Push-Location $PSScriptRoot
try {
    & $Python -m PyInstaller --noconfirm --clean g1-shell-sidecar.spec
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "OK: dist/g1-shell-sidecar/g1-shell-sidecar.exe"
} finally { Pop-Location }
