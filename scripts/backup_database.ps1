param(
    [string]$ProjectPath = (Split-Path -Parent $PSScriptRoot),
    [string]$BackupDir = "",
    [string]$PgDumpPath = "pg_dump",
    [string]$GpgPath = "gpg",
    [string]$GpgRecipient = "",
    [int]$RetentionDays = 30,
    [switch]$RestrictAcl,
    [switch]$AllowUnencrypted
)

$ErrorActionPreference = "Stop"

$UsingDefaultBackupDir = -not $BackupDir
if ($UsingDefaultBackupDir) {
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
if ($env:APP_ENV -in @("prod", "production")) {
    if ($UsingDefaultBackupDir) {
        throw "BackupDir doit pointer vers un stockage distinct du projet en production"
    }
    if (-not $GpgRecipient -and -not $AllowUnencrypted) {
        throw "GpgRecipient est obligatoire en production sauf dérogation explicite -AllowUnencrypted"
    }
}

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

if ($RestrictAcl) {
    $Acl = Get-Acl $BackupDir
    $Acl.SetAccessRuleProtection($true, $false)
    $CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $Rule = New-Object System.Security.AccessControl.FileSystemAccessRule($CurrentUser, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
    $Acl.SetAccessRule($Rule)
    Set-Acl -Path $BackupDir -AclObject $Acl
}

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

if ($GpgRecipient) {
    $EncryptedPath = "$OutputPath.gpg"
    & $GpgPath --batch --yes --recipient $GpgRecipient --encrypt --output $EncryptedPath $OutputPath
    if ($LASTEXITCODE -ne 0) {
        throw "gpg a echoue avec le code $LASTEXITCODE"
    }
    Remove-Item -Path $OutputPath -Force
    $OutputPath = $EncryptedPath
}

if ($RetentionDays -gt 0) {
    $Limit = (Get-Date).AddDays(-$RetentionDays)
    Get-ChildItem -Path (Join-Path $BackupDir "*") -File -Include "*.dump","*.dump.gpg" |
        Where-Object { $_.LastWriteTime -lt $Limit } |
        Remove-Item -Force
}

Write-Host "Sauvegarde creee: $OutputPath"
