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

# On a stock Windows machine, `python`/`python3` on PATH can resolve to the
# Microsoft Store app-execution alias stub instead of a real interpreter - it
# just prints a "not found, install from Store" message and exits non-zero.
# Presence on PATH doesn't prove it works, so probe each candidate by actually
# running it. `py` (the official launcher installed by python.org) is tried
# last: on CI (actions/setup-python), `python`/`python3` are the pinned
# version and always real - `py -3` is a separate, pre-baked system install
# that silently overrides the pinned version if tried first, which is what
# broke the v3.0.0 Windows release build (pyinstaller pinned below couldn't
# satisfy whatever newer Python `py -3` resolved to on the runner).
function Get-PythonCommand {
    $candidates = @(
        @{ Exe = "python"; PreArgs = @() },
        @{ Exe = "python3"; PreArgs = @() },
        @{ Exe = "py"; PreArgs = @("-3") }
    )
    foreach ($c in $candidates) {
        if (-not (Get-Command $c.Exe -ErrorAction SilentlyContinue)) {
            continue
        }
        try {
            $versionOutput = & $c.Exe @($c.PreArgs + "--version") 2>&1
        } catch {
            continue
        }
        if ($LASTEXITCODE -eq 0 -and ($versionOutput -join " ") -match "Python \d") {
            return ("$($c.Exe) $($c.PreArgs -join ' ')").Trim()
        }
    }
    throw "No working Python interpreter found (tried py -3, python, python3). Install Python from python.org (making sure to add it to PATH), or disable the Store app-execution alias for python.exe/python3.exe under Settings > Apps > Advanced app settings > App execution aliases."
}

Write-Host "==> Building Vue frontend"
Push-Location gui\vue
Invoke-Checked "npm ci"
Invoke-Checked "npm run build"
Pop-Location

Write-Host "==> Setting up Python environment"
if (-not (Test-Path .venv)) {
    $pythonCmd = Get-PythonCommand
    Invoke-Checked "$pythonCmd -m venv .venv"
}
Invoke-Checked ".venv\Scripts\pip install --quiet -r requirements.txt"

Write-Host "==> Building Windows app"
Invoke-Checked ".venv\Scripts\pyinstaller `"CRMScript Fetcher.spec`""

Write-Host "==> Done: dist\CRMScript Fetcher\CRMScript Fetcher.exe"
