param(
  [Parameter(Mandatory = $true)][string]$EnvFile,
  [string]$ComposeFile = "docker-compose.prod.yml",
  [string]$BackupDirectory = "backups"
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $BackupDirectory | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$target = Join-Path $BackupDirectory "paperforge-postgres-$stamp.dump"
$remote = "/tmp/paperforge-postgres-$stamp.dump"
try {
  $dumpCommand = 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f "' + $remote + '"'
  docker compose --env-file $EnvFile -f $ComposeFile exec -T postgres sh -c $dumpCommand
  if ($LASTEXITCODE -ne 0) { throw "PostgreSQL dump failed inside the container." }
  docker compose --env-file $EnvFile -f $ComposeFile cp "postgres:$remote" $target
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $target) -or (Get-Item $target).Length -eq 0) { throw "PostgreSQL backup copy failed." }
} finally {
  docker compose --env-file $EnvFile -f $ComposeFile exec -T postgres sh -c "rm -f '$remote'" | Out-Null
}
Write-Output "Backup created: $target"
