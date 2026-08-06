param(
    [ValidateSet("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")]
    [string]$DayOfWeek = "Monday",
    [string]$At = "08:00",
    [string]$StartDate,
    [string]$TaskName = "Tasmania Hackentrick Import"
)

$ErrorActionPreference = "Stop"
$backendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $backendDir "run_scheduled_import.ps1"
$time = [datetime]::ParseExact($At, "HH:mm", [System.Globalization.CultureInfo]::InvariantCulture)

if ($StartDate) {
    $firstRun = [datetime]::ParseExact(
        "$StartDate $At",
        "yyyy-MM-dd HH:mm",
        [System.Globalization.CultureInfo]::InvariantCulture
    )
} else {
    $firstRun = $time
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runner`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $DayOfWeek -At $time
$trigger.StartBoundary = $firstRun.ToString("s")
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -WakeToRun `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Importiert den nächsten Tasmania-Hackentrick-Spieltag und veröffentlicht ihn." `
    -Force

Write-Host "Aufgabe '$TaskName' läuft ab $($firstRun.ToString('dd.MM.yyyy')) jeweils $DayOfWeek um $At Uhr."
Write-Host "Voraussetzung: Windows-Benutzer ist angemeldet und die Login-Sitzungen sind gültig."
