param(
  [Parameter(Mandatory = $true)][string]$EnvFile,
  [string]$ComposeFile = "docker-compose.prod.yml",
  [string]$BackupDirectory = "backups"
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $BackupDirectory | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$target = Join-Path $BackupDirectory "paperforge-postgres-$stamp.dump"
docker compose --env-file $EnvFile -f $ComposeFile exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > $target
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $target) -or (Get-Item $target).Length -eq 0) { Remove-Item -LiteralPath $target -ErrorAction SilentlyContinue; throw "PostgreSQL backup failed." }
Write-Output "Backup created: $target"
