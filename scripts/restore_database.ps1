param(
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,
    [string]$ProjectPath = (Split-Path -Parent $PSScriptRoot),
    [string]$PgRestorePath = "pg_restore",
    [string]$GpgPath = "gpg"
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

$RestorePath = $BackupPath
$TempPath = $null

if ($BackupPath.EndsWith(".gpg")) {
    $TempPath = Join-Path $env:TEMP ("restore_" + [System.Guid]::NewGuid().ToString() + ".dump")
    & $GpgPath --batch --yes --decrypt --output $TempPath $BackupPath
    if ($LASTEXITCODE -ne 0) {
        throw "gpg a echoue avec le code $LASTEXITCODE"
    }
    $RestorePath = $TempPath
}

try {
    $env:PGPASSWORD = $env:PG_PASSWORD
    & $PgRestorePath `
        --clean `
        --if-exists `
        --no-owner `
        --dbname=$env:PG_DB `
        --host=$env:PG_HOST `
        --port=$env:PG_PORT `
        --username=$env:PG_USER `
        $RestorePath

    if ($LASTEXITCODE -ne 0) {
        throw "pg_restore a echoue avec le code $LASTEXITCODE"
    }
}
finally {
    if ($TempPath -and (Test-Path $TempPath)) {
        Remove-Item -Path $TempPath -Force
    }
}

Write-Host "Base restauree depuis: $BackupPath"
