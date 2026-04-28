param(
    [string]$ProjectPath = "C:\Users\arris\Downloads\Benjamin_Immobilier_Alternance",
    [string]$PythonPath = "",
    [int]$MaxPages = 1,
    [int]$EnrichmentLimit = 100
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectPath

if (-not $PythonPath) {
    $VenvPython = Join-Path $ProjectPath ".venv\Scripts\python.exe"
    if (Test-Path $VenvPython) {
        $PythonPath = $VenvPython
    } else {
        $PythonPath = "python"
    }
}

& $PythonPath -m services.jobs.run_automation --max-pages $MaxPages --enrichment-limit $EnrichmentLimit
