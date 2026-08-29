param(
    [string]$ProjectPath = (Split-Path -Parent $PSScriptRoot),
    [string]$PythonPath = "",
    [int]$MaxPages = 1,
    [int]$EnrichmentLimit = 100
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectPath

if (-not $PythonPath) {
    $VenvCandidates = @(
        (Join-Path $ProjectPath "venv\Scripts\python.exe"),
        (Join-Path $ProjectPath ".venv\Scripts\python.exe")
    )
    $ResolvedPython = $VenvCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($ResolvedPython) {
        $PythonPath = $ResolvedPython
    } else {
        $PythonPath = "python"
    }
}

& $PythonPath -m services.jobs.run_automation --max-pages $MaxPages --enrichment-limit $EnrichmentLimit
exit $LASTEXITCODE
