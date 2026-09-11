param(
  [Parameter(Mandatory = $true)][string]$BackupFile
)
$ErrorActionPreference = "Stop"
$resolved = (Resolve-Path -LiteralPath $BackupFile).Path
if ((Get-Item -LiteralPath $resolved).Length -eq 0) { throw "Backup file is empty." }

# Run pg_restore from a disposable official PostgreSQL image so the host does
# not need PostgreSQL client tools installed. This only reads the dump.
docker run --rm --mount "type=bind,source=$resolved,target=/backup.dump,readonly" postgres:16-alpine pg_restore --list /backup.dump | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Backup archive integrity check failed." }
Write-Output "Backup integrity PASS: $resolved"
