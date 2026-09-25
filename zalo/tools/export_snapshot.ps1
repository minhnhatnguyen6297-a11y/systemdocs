# export_snapshot.ps1 - export flat one-way snapshot of this repo.
#
# Copies the whole repo to $Dest EXCLUDING .git, .venv, runtime,
# node_modules (any depth), __pycache__, *.pyc, .env, .pytest_cache and
# SNAPSHOT_MANIFEST.json, then writes $Dest\SNAPSHOT_MANIFEST.json:
#   {schema_version, source_repo, source_commit, exported_at,
#    files: {<relpath>: <sha256>}}
#
# Dest is a dedicated directory: it is cleaned (contents removed) before
# copy. Cleaning happens INSIDE $Dest only - never outside it.
#
# PowerShell 5.1 compatible. Usage:
#   powershell -File tools\export_snapshot.ps1                 # -> D:\systemdocs\zalo
#   powershell -File tools\export_snapshot.ps1 -Dest <dir>     # custom dest

[CmdletBinding()]
param(
    [string]$Dest = 'D:\systemdocs\zalo'
)

$ErrorActionPreference = 'Stop'

# --- Resolve paths ----------------------------------------------------------

# Source repo = parent of this script's tools/ directory.
$Source = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$destFull = [IO.Path]::GetFullPath($Dest)

# --- Safety guards ----------------------------------------------------------

if ($destFull -ieq $Source) {
    throw "Dest '$destFull' equals source repo '$Source' - refusing."
}
if ($destFull.Length -le 3) {
    throw "Dest '$destFull' is a drive root - refusing to clean it."
}
# Dest inside source would recurse into itself; source inside dest would be
# wiped by the clean step. Neither is a supported layout.
if ($destFull.StartsWith($Source + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Dest '$destFull' is inside source '$Source' - refusing."
}
if ($Source.StartsWith($destFull + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Source '$Source' is inside dest '$destFull' - clean would wipe source. Refusing."
}

# --- Clean destination (inside $Dest only) ----------------------------------

if (Test-Path -LiteralPath $destFull) {
    Get-ChildItem -LiteralPath $destFull -Force | Remove-Item -Recurse -Force
} else {
    New-Item -ItemType Directory -Path $destFull -Force | Out-Null
}

# --- Mirror copy with exclusions ---------------------------------------------

$excludeDirs  = @('.git', '.venv', 'runtime', 'node_modules', '__pycache__', '.pytest_cache')
$excludeFiles = @('*.pyc', '.env', 'SNAPSHOT_MANIFEST.json')

$robocopyArgs = @(
    $Source, $destFull, '/E', '/COPY:DAT', '/DCOPY:T',
    '/NFL', '/NDL', '/NJH', '/NJS', '/NP',
    '/XD') + $excludeDirs + @('/XF') + $excludeFiles

& robocopy @robocopyArgs | Out-Null
# robocopy exit codes 0-7 are success; >=8 is failure.
if ($LASTEXITCODE -ge 8) {
    throw "robocopy failed with exit code $LASTEXITCODE"
}

# --- Manifest -----------------------------------------------------------------

$commit = (& git -C $Source rev-parse HEAD 2>$null)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($commit)) {
    throw "git rev-parse HEAD failed in '$Source' - cannot stamp source_commit."
}
$commit = $commit.Trim()

$files = [ordered]@{}
$destPrefix = $destFull.TrimEnd('\') + '\'
Get-ChildItem -LiteralPath $destFull -Recurse -File -Force | ForEach-Object {
    $rel = $_.FullName.Substring($destPrefix.Length) -replace '\\', '/'
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
    $files[$rel] = $hash
}

$manifest = [ordered]@{
    schema_version = 1
    source_repo    = $Source
    source_commit  = $commit
    exported_at    = (Get-Date).ToUniversalTime().ToString('o')
    files          = $files
}

$json = $manifest | ConvertTo-Json -Depth 5
# UTF-8 without BOM.
[IO.File]::WriteAllText(
    (Join-Path $destFull 'SNAPSHOT_MANIFEST.json'),
    $json,
    (New-Object System.Text.UTF8Encoding($false)))

Write-Output ("Exported {0} files -> {1} (commit {2})" -f $files.Count, $destFull, $commit)
