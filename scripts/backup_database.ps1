param(
    [string]$ProjectPath = "C:\Users\arris\Downloads\Benjamin_Immobilier_Alternance",
    [string]$BackupDir = "",
    [string]$PgDumpPath = "pg_dump"
)

$ErrorActionPreference = "Stop"

if (-not $BackupDir) {
    $BackupDir = Join-Path $ProjectPath "data\backups"
}

$EnvPath = Join-Path $ProjectPath ".env"
if (Test-Path $EnvPath) {
    Get-Content $EnvPath | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process")
        }
    }
}

if (-not $env:PG_DB) { throw "PG_DB est manquant dans l'environnement ou .env" }

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutputPath = Join-Path $BackupDir "$($env:PG_DB)_$Timestamp.dump"

$env:PGPASSWORD = $env:PG_PASSWORD
& $PgDumpPath `
    --format=custom `
    --file=$OutputPath `
    --host=$env:PG_HOST `
    --port=$env:PG_PORT `
    --username=$env:PG_USER `
    $env:PG_DB

if ($LASTEXITCODE -ne 0) {
    throw "pg_dump a echoue avec le code $LASTEXITCODE"
}

Write-Host "Sauvegarde creee: $OutputPath"
