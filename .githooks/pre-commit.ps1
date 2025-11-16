# Minimal Windows wrapper: delegate to the unified Python script
Param([String[]]$Args)

$python = $env:PYTHON
if ([string]::IsNullOrEmpty($python)) { $python = 'python' }

$script = Join-Path $PSScriptRoot 'pre-commit'

& $python $script @Args

exit $LASTEXITCODE
