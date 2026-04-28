param(
    [string]$TaskName = "Benjamin Immobilier Automation",
    [string]$ProjectPath = "C:\Users\arris\Downloads\Benjamin_Immobilier_Alternance",
    [int]$FrequencyHours = 6,
    [string]$StartTime = "06:00",
    [int]$MaxPages = 1,
    [int]$EnrichmentLimit = 100
)

$ErrorActionPreference = "Stop"

$Runner = Join-Path $ProjectPath "scripts\run_automation.ps1"
if (-not (Test-Path $Runner)) {
    throw "Runner introuvable: $Runner"
}

$ActionArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`" -ProjectPath `"$ProjectPath`" -MaxPages $MaxPages -EnrichmentLimit $EnrichmentLimit"
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $ActionArgs -WorkingDirectory $ProjectPath
$Trigger = New-ScheduledTaskTrigger -Once -At $StartTime -RepetitionInterval (New-TimeSpan -Hours $FrequencyHours) -RepetitionDuration (New-TimeSpan -Days 3650)
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 4)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Scraping, scoring, enrichissement et nettoyage Benjamin Immobilier" -Force | Out-Null

Write-Host "Tache planifiee installee: $TaskName"
Write-Host "Frequence: toutes les $FrequencyHours heures a partir de $StartTime"
Write-Host "Runner: $Runner"
