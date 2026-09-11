param(
  [Parameter(Mandatory = $true)][string]$Volume,
  [Parameter(Mandatory = $true)][string]$BackupFile,
  [switch]$ConfirmDestructiveRestore
)
$ErrorActionPreference = "Stop"
if ($Volume -notmatch '^paperforge-[a-z0-9-]+$') { throw "Unsafe Docker volume name: $Volume" }
$resolved = (Resolve-Path -LiteralPath $BackupFile).Path
if (-not $ConfirmDestructiveRestore) { throw "DESTRUCTIVE OPERATION: verify the target volume and re-run with -ConfirmDestructiveRestore." }

# This intentionally clears only the explicitly named Docker volume.
docker run --rm `
  --mount "source=$Volume,target=/target" `
  --mount "type=bind,source=$resolved,target=/backup.tar.gz,readonly" `
  alpine:3.20 sh -c "find /target -mindepth 1 -maxdepth 1 -exec rm -rf {} + && tar -xzf /backup.tar.gz -C /target"
if ($LASTEXITCODE -ne 0) { throw "File volume restore failed: $Volume" }
Write-Output "File volume restore completed: $Volume"
