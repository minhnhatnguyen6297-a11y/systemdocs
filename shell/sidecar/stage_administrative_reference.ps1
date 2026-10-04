# Public administrative reference assets only. Also callable against an isolated
# staging tree without staging the backend, office data, or browser downloads.
param([Parameter(Mandatory=$true)][string]$Repository,
      [Parameter(Mandatory=$true)][string]$EngineStage)
$ErrorActionPreference = "Stop"
$referenceSource = Join-Path $Repository "notary_v2\data\administrative_units"
$referenceTarget = Join-Path $EngineStage "notary_v2\data\administrative_units"
New-Item -ItemType Directory -Force -Path (Join-Path $referenceTarget "snapshots") | Out-Null
Copy-Item -LiteralPath (Join-Path $referenceSource "ledger.json") -Destination $referenceTarget -Force
$referenceLedger = Get-Content -Raw -Encoding UTF8 (Join-Path $referenceSource "ledger.json") | ConvertFrom-Json
foreach ($reference in $referenceLedger.sources) {
    if (-not $reference.snapshot) { continue }
    if ($reference.snapshot -notmatch '^snapshots/[a-f0-9]{64}\.raw$') { throw "Invalid public snapshot path" }
    Copy-Item -LiteralPath (Join-Path $referenceSource $reference.snapshot) -Destination (Join-Path $referenceTarget $reference.snapshot) -Force
}
$referenceContract = Join-Path $EngineStage "contracts\administrative-timeline"
New-Item -ItemType Directory -Force -Path $referenceContract | Out-Null
Copy-Item -LiteralPath (Join-Path $Repository "contracts\administrative-timeline\ledger.schema.json") -Destination $referenceContract -Force
$notaryTarget = Join-Path $EngineStage "notary_v2"
Copy-Item -LiteralPath (Join-Path $Repository "notary_v2\administrative_timeline.py") -Destination $notaryTarget -Force
New-Item -ItemType Directory -Force -Path (Join-Path $notaryTarget "services") | Out-Null
Copy-Item -LiteralPath (Join-Path $Repository "notary_v2\services\administrative_address.py") -Destination (Join-Path $notaryTarget "services") -Force
