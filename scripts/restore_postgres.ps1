param(
  [Parameter(Mandatory = $true)][string]$EnvFile,
  [Parameter(Mandatory = $true)][string]$BackupFile,
  [string]$ComposeFile = "docker-compose.prod.yml",
  [switch]$ConfirmDestructiveRestore
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $BackupFile)) { throw "Backup file was not found." }
if (-not $ConfirmDestructiveRestore) { throw "DESTRUCTIVE OPERATION: stop application containers, verify the target database and backup, then re-run with -ConfirmDestructiveRestore." }
$remote = "/tmp/paperforge-restore-$([guid]::NewGuid().ToString('N')).dump"
try {
  docker compose --env-file $EnvFile -f $ComposeFile cp $BackupFile "postgres:$remote"
  if ($LASTEXITCODE -ne 0) { throw "PostgreSQL backup copy failed." }
  $restoreCommand = 'pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB" "' + $remote + '"'
  docker compose --env-file $EnvFile -f $ComposeFile exec -T postgres sh -c $restoreCommand
  if ($LASTEXITCODE -ne 0) { throw "PostgreSQL restore failed." }
} finally {
  docker compose --env-file $EnvFile -f $ComposeFile exec -T postgres sh -c "rm -f '$remote'" | Out-Null
}
Write-Output "Restore completed. Start only the application image compatible with this database schema."
