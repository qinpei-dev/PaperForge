param(
  [Parameter(Mandatory = $true)][string]$BackupDirectory,
  [string[]]$Volume = @(
    "paperforge-uploads",
    "paperforge-outputs",
    "paperforge-template-storage",
    "paperforge-task-states",
    "paperforge-templates"
  )
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $BackupDirectory | Out-Null
$resolved = (Resolve-Path -LiteralPath $BackupDirectory).Path
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
foreach ($volumeName in $Volume) {
  if ($volumeName -notmatch '^paperforge-[a-z0-9-]+$') { throw "Unsafe Docker volume name: $volumeName" }
  $targetName = "$volumeName-$stamp.tar.gz"
  docker run --rm `
    --mount "source=$volumeName,target=/source,readonly" `
    --mount "type=bind,source=$resolved,target=/backup" `
    alpine:3.20 tar -czf "/backup/$targetName" -C /source .
  if ($LASTEXITCODE -ne 0) { throw "File volume backup failed: $volumeName" }
  Write-Output "File volume backup created: $(Join-Path $resolved $targetName)"
}
