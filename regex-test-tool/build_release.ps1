# Dung ban dong goi cho tool nhan vien: gom loi luat chung + consumer vao
# tool/vendor/ de tool chay doc lap. Khong chep luat, khong giu engine thu hai.
# Chay: powershell -ExecutionPolicy Bypass -File build_release.ps1
$ErrorActionPreference = "Stop"

$toolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $toolRoot
$vendorRoot = Join-Path (Join-Path $toolRoot "tool") "vendor"

$engineSource = Join-Path $repoRoot "tools\regex_workbench\engine"
$adapterSource = Join-Path $repoRoot "upload_lab\extraction_adapter.py"
$validatorSource = Join-Path $repoRoot "upload_lab\kiem_tra_trich_xuat.py"

foreach ($source in @($engineSource, $adapterSource, $validatorSource)) {
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Khong tim thay nguon de dong goi: $source"
    }
}

if (Test-Path -LiteralPath $vendorRoot) {
    Remove-Item -LiteralPath $vendorRoot -Recurse -Force
}

$engineTarget = Join-Path $vendorRoot "tools\regex_workbench\engine"
$uploadLabTarget = Join-Path $vendorRoot "upload_lab"
New-Item -ItemType Directory -Path (Join-Path $vendorRoot "tools\regex_workbench") -Force | Out-Null
New-Item -ItemType Directory -Path $uploadLabTarget -Force | Out-Null

Copy-Item -LiteralPath $engineSource -Destination $engineTarget -Recurse -Force
Copy-Item -LiteralPath $adapterSource -Destination (Join-Path $uploadLabTarget "extraction_adapter.py") -Force
Copy-Item -LiteralPath $validatorSource -Destination (Join-Path $uploadLabTarget "kiem_tra_trich_xuat.py") -Force

# __pycache__ cua lan chay dev khong thuoc ban phat hanh.
Get-ChildItem -LiteralPath $vendorRoot -Recurse -Directory -Filter "__pycache__" |
    Remove-Item -Recurse -Force

Write-Host "Da dung xong: $vendorRoot"
Get-ChildItem -LiteralPath $vendorRoot -Recurse -File | ForEach-Object {
    Write-Host ("  " + $_.FullName.Substring($vendorRoot.Length + 1))
}
