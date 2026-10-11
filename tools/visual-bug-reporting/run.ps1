$repo = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
& (Join-Path $repo 'run-dev.bat') @args
exit $LASTEXITCODE
