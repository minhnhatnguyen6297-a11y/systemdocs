$ErrorActionPreference = 'Stop'
$reviewWorkspace = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$reviewMoves = @(
    @('.agent\scratch\review-plan-20261004', '.agents\review-plan-20261004\initial-scratch'),
    @('_bmad\render\bmad-code-review\systemdocs-b0d75560fafa\b6afeec7697070399c89', '.agents\review-plan-20261004\bmad-workflow')
)
foreach ($reviewPair in $reviewMoves) {
    $reviewSource = [System.IO.Path]::GetFullPath((Join-Path $reviewWorkspace $reviewPair[0]))
    $reviewDestination = [System.IO.Path]::GetFullPath((Join-Path $reviewWorkspace $reviewPair[1]))
    $reviewPrefix = $reviewWorkspace.TrimEnd('\') + '\'
    if (-not $reviewSource.StartsWith($reviewPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
        -not $reviewDestination.StartsWith($reviewPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Review move escaped workspace'
    }
    if (Test-Path -LiteralPath $reviewSource) {
        if (Test-Path -LiteralPath $reviewDestination) { throw "Destination already exists: $reviewDestination" }
        Move-Item -LiteralPath $reviewSource -Destination $reviewDestination
        Write-Output "Moved own review files to $reviewDestination"
    }
}
