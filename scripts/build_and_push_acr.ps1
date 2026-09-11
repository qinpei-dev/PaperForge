[CmdletBinding()]
param(
  [ValidatePattern('^v\d+\.\d+\.\d+$')]
  [string]$ReleaseVersion = 'v3.7.3',
  [string]$Registry = 'crpi-z345rofd99au0che.cn-chengdu.personal.cr.aliyuncs.com/paperforge',
  [string]$ApiBaseUrl = 'https://aetherislab.xyz/api',
  [ValidateSet('false', 'true')]
  [string]$PreviewAutoLogin = 'false',
  [ValidateSet('production', 'development')]
  [string]$AppEnv = 'production',
  [string]$SourceCommit,
  [switch]$SkipPush
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw 'docker CLI is required.'
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  throw 'git CLI is required.'
}
if ($AppEnv -eq 'production' -and $PreviewAutoLogin -ne 'false') {
  throw 'Production frontend builds must disable preview auto-login.'
}
if ($AppEnv -eq 'production' -and $ApiBaseUrl -notmatch '^https://') {
  throw 'Production frontend builds require an HTTPS API base URL.'
}
if ($AppEnv -eq 'production' -and $ApiBaseUrl -match 'localhost|127\.0\.0\.1') {
  throw 'Production frontend builds must not use a loopback API base URL.'
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backendContext = Join-Path $repoRoot 'paper-ai/backend'
$frontendContext = Join-Path $repoRoot 'paper-ai/frontend'
$source = (& git -C $repoRoot rev-parse HEAD).Trim()
if ($SourceCommit -and $source -ne $SourceCommit) {
  throw "Current HEAD $source does not match requested source commit $SourceCommit."
}
$dirty = (& git -C $repoRoot status --porcelain | Out-String).Trim()
if ($dirty) {
  throw 'Release image builds require a clean worktree; commit and verify the exact source first.'
}

$backendImage = "$Registry/paperforge-backend:$ReleaseVersion"
$frontendImage = "$Registry/paperforge-frontend:$ReleaseVersion"
$registryHost = $Registry.Split('/')[0]
$commonLabels = @(
  '--label', "com.paperforge.release=$ReleaseVersion",
  '--label', "com.paperforge.commit=$source"
)

Write-Output "Release: $ReleaseVersion"
Write-Output "Source commit: $source"
Write-Output "Backend image: $backendImage"
Write-Output "Frontend image: $frontendImage"
Write-Output "Frontend build args: NEXT_PUBLIC_API_BASE_URL=$ApiBaseUrl; NEXT_PUBLIC_PAPERFORGE_PREVIEW_AUTO_LOGIN=$PreviewAutoLogin; NEXT_PUBLIC_PAPERFORGE_APP_ENV=$AppEnv"

& docker build @commonLabels --tag $backendImage --file (Join-Path $backendContext 'Dockerfile') $backendContext
if ($LASTEXITCODE -ne 0) { throw 'Backend image build failed.' }

& docker build @commonLabels `
  --build-arg "NEXT_PUBLIC_API_BASE_URL=$ApiBaseUrl" `
  --build-arg "NEXT_PUBLIC_PAPERFORGE_PREVIEW_AUTO_LOGIN=$PreviewAutoLogin" `
  --build-arg "NEXT_PUBLIC_PAPERFORGE_APP_ENV=$AppEnv" `
  --tag $frontendImage --file (Join-Path $frontendContext 'Dockerfile') $frontendContext
if ($LASTEXITCODE -ne 0) { throw 'Frontend image build failed.' }

if ($SkipPush) {
  Write-Output 'SkipPush specified; images were built but not pushed.'
  exit 0
}

$acrUsername = [Environment]::GetEnvironmentVariable('ACR_USERNAME')
$acrPassword = [Environment]::GetEnvironmentVariable('ACR_PASSWORD')
if ([string]::IsNullOrWhiteSpace($acrUsername) -or [string]::IsNullOrWhiteSpace($acrPassword)) {
  throw 'ACR_USERNAME and ACR_PASSWORD must be provided through the deployment environment.'
}

$acrPassword | & docker login $registryHost --username $acrUsername --password-stdin
if ($LASTEXITCODE -ne 0) { throw 'ACR login failed.' }

& docker push $backendImage
if ($LASTEXITCODE -ne 0) { throw 'Backend image push failed.' }
& docker push $frontendImage
if ($LASTEXITCODE -ne 0) { throw 'Frontend image push failed.' }

Write-Output 'Remote image manifests and digests:'
& docker buildx imagetools inspect $backendImage
if ($LASTEXITCODE -ne 0) { throw 'Backend image digest inspection failed.' }
& docker buildx imagetools inspect $frontendImage
if ($LASTEXITCODE -ne 0) { throw 'Frontend image digest inspection failed.' }
