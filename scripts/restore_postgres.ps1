param(
  [Parameter(Mandatory = $true)][string]$EnvFile,
  [Parameter(Mandatory = $true)][string]$BackupFile,
  [string]$ComposeFile = "docker-compose.prod.yml",
  [switch]$ConfirmDestructiveRestore
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $BackupFile)) { throw "Backup file was not found." }
if (-not $ConfirmDestructiveRestore) { throw "DESTRUCTIVE OPERATION: stop application containers, verify the target database and backup, then re-run with -ConfirmDestructiveRestore." }
Get-Content -AsByteStream -ReadCount 0 -LiteralPath $BackupFile | docker compose --env-file $EnvFile -f $ComposeFile exec -T postgres sh -c 'pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
if ($LASTEXITCODE -ne 0) { throw "PostgreSQL restore failed." }
Write-Output "Restore completed. Start only the application image compatible with this database schema."
