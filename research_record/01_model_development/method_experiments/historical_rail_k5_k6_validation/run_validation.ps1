$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "src\run_rail_k_validation.py"
python $scriptPath @args
