# Builds the Windows GUI app in one command: dist\CRMScript Fetcher\CRMScript Fetcher.exe
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# $ErrorActionPreference only governs PowerShell's own cmdlets, not external
# commands (npm, pyinstaller) - those keep running even after a failure
# unless checked explicitly, unlike bash's `set -e`.
function Invoke-Checked {
    param([string]$Command)
    Invoke-Expression $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command"
    }
}

Write-Host "==> Building Vue frontend"
Push-Location gui\vue
Invoke-Checked "npm ci"
Invoke-Checked "npm run build"
Pop-Location

Write-Host "==> Setting up Python environment"
if (-not (Test-Path .venv)) {
    Invoke-Checked "python -m venv .venv"
}
Invoke-Checked ".venv\Scripts\pip install --quiet -r requirements.txt"

Write-Host "==> Building Windows app"
Invoke-Checked ".venv\Scripts\pyinstaller `"CRMScript Fetcher.spec`""

Write-Host "==> Done: dist\CRMScript Fetcher\CRMScript Fetcher.exe"
