$ErrorActionPreference = "Stop"

$backendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $backendDir
$python = Join-Path $backendDir ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python-Umgebung fehlt: $python"
}

Set-Location -LiteralPath $projectDir
$runner = Join-Path $backendDir "run_scheduled_import.py"
$firstAttempt = Get-Date

for ($attempt = 1; $attempt -le 3; $attempt++) {
    Write-Host "Automatischer Import: Versuch $attempt von 3."
    & $python $runner

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Der automatische Import war erfolgreich."
        exit 0
    }

    if ($attempt -eq 3) {
        throw "Der automatische Import ist nach drei Versuchen fehlgeschlagen."
    }

    $nextAttempt = $firstAttempt.AddHours($attempt)
    $waitSeconds = [Math]::Max(
        0,
        [Math]::Ceiling(($nextAttempt - (Get-Date)).TotalSeconds)
    )

    Write-Host (
        "Noch keine vollständigen Ergebnisse. " +
        "Nächster Versuch um {0:HH:mm} Uhr." -f $nextAttempt
    )
    Start-Sleep -Seconds $waitSeconds
}
