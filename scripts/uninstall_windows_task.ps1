param(
    [string]$TaskName = "Benjamin Immobilier Automation"
)

$ErrorActionPreference = "Stop"

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Tache planifiee supprimee: $TaskName"
} else {
    Write-Host "Aucune tache trouvee: $TaskName"
}
