$ErrorActionPreference = "Stop"

$venvPython = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

function Invoke-Check {
    param([string[]]$Arguments)

    & $python @Arguments
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Write-Host "Running Ruff lint..."
Invoke-Check @("-m", "ruff", "check", ".")

Write-Host "Running Ruff format check..."
Invoke-Check @("-m", "ruff", "format", "--check", ".")

Write-Host "Running Mypy..."
Invoke-Check @("-m", "mypy", "app")

Write-Host "Running Pytest..."
Invoke-Check @("-m", "pytest", "-q")

Write-Host "All quality checks passed." -ForegroundColor Green
