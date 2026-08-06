$ErrorActionPreference = "Stop"

$backendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $backendDir
$python = Join-Path $backendDir ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python-Umgebung fehlt: $python"
}

Set-Location -LiteralPath $projectDir
& $python (Join-Path $backendDir "run_scheduled_import.py")

if ($LASTEXITCODE -ne 0) {
    throw "Der automatische Import ist fehlgeschlagen."
}
