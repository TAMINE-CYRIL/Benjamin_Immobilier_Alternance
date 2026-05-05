param(
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,
    [string]$ProjectPath = "C:\Users\arris\Downloads\Benjamin_Immobilier_Alternance",
    [string]$PgRestorePath = "pg_restore"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupPath)) {
    throw "Sauvegarde introuvable: $BackupPath"
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

$env:PGPASSWORD = $env:PG_PASSWORD
& $PgRestorePath `
    --clean `
    --if-exists `
    --no-owner `
    --dbname=$env:PG_DB `
    --host=$env:PG_HOST `
    --port=$env:PG_PORT `
    --username=$env:PG_USER `
    $BackupPath

if ($LASTEXITCODE -ne 0) {
    throw "pg_restore a echoue avec le code $LASTEXITCODE"
}

Write-Host "Base restauree depuis: $BackupPath"
