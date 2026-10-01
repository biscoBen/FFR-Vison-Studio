$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'verified_engine_archive.ps1')
$temporary = Join-Path ([IO.Path]::GetTempPath()) ('ffr-cache-test-' + [Guid]::NewGuid().ToString('N'))
$script:requests = 0
$script:failDownload = $false
$script:payload = [Text.Encoding]::UTF8.GetBytes('Checksum test fixture, not the real engine.')
function Invoke-WebRequest {
    param([string]$Uri, [string]$OutFile, [switch]$UseBasicParsing, [int]$TimeoutSec)
    $script:requests++
    [IO.File]::WriteAllBytes($OutFile, $script:payload)
    if ($script:failDownload) { throw 'Simulated engine download failure.' }
}
function Assert-That([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}
function Expect-Failure([scriptblock]$Action, [string]$Message) {
    $caught = $null
    try { & $Action | Out-Null } catch { $caught = $_.Exception.Message }
    Assert-That ($caught -eq $Message) "Expected '$Message', got '$caught'."
}
try {
    [void][IO.Directory]::CreateDirectory($temporary)
    $fixture = Join-Path $temporary 'fixture'
    [IO.File]::WriteAllBytes($fixture, $script:payload)
    $sha = (Get-FileHash -LiteralPath $fixture -Algorithm SHA256).Hash.ToLowerInvariant()
    $cache = Join-Path $temporary 'cache'
    $archive = Get-VerifiedEngineArchive -CacheDirectory $cache -Uri 'https://fixture.invalid/engine.zip' -Sha256 $sha
    Assert-That ($script:requests -eq 1) 'A cache miss must download exactly once.'
    Assert-That ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ieq $sha) 'A cache miss must retain only the verified bytes.'
    $again = Get-VerifiedEngineArchive -CacheDirectory $cache -Uri 'https://fixture.invalid/changed-url' -Sha256 $sha
    Assert-That ($again -eq $archive -and $script:requests -eq 1) 'A valid cache hit must reuse the copy without downloading.'

    [IO.File]::WriteAllText($archive, 'corrupted')
    Expect-Failure { Get-VerifiedEngineArchive -CacheDirectory $cache -Uri 'https://fixture.invalid/engine.zip' -Sha256 $sha } `
        'The cached Windows startup test engine checksum did not match.'
    Assert-That ($script:requests -eq 1) 'A corrupt cache must fail checksum verification without another download.'
    Assert-That ([IO.File]::ReadAllText($archive) -eq 'corrupted') 'A corrupt existing copy must not be overwritten.'

    $failedCache = Join-Path $temporary 'failed-cache'
    $script:failDownload = $true
    Expect-Failure { Get-VerifiedEngineArchive -CacheDirectory $failedCache -Uri 'https://fixture.invalid/engine.zip' -Sha256 $sha } `
        'Simulated engine download failure.'
    Assert-That (@(Get-ChildItem -LiteralPath $failedCache).Count -eq 0) 'A failed download must not retain partial files or a cache entry.'

    $script:failDownload = $false
    $script:payload = [Text.Encoding]::UTF8.GetBytes('The wrong archive.')
    Expect-Failure { Get-VerifiedEngineArchive -CacheDirectory $failedCache -Uri 'https://fixture.invalid/engine.zip' -Sha256 $sha } `
        'The Windows startup test engine checksum did not match.'
    Assert-That (@(Get-ChildItem -LiteralPath $failedCache).Count -eq 0) 'A checksum mismatch must not poison the cache.'

    $requestsBefore = $script:requests
    Expect-Failure { Get-VerifiedEngineArchive -CacheDirectory $cache -Uri 'https://fixture.invalid/engine.zip' -Sha256 '../invalid' } `
        'An engine archive SHA-256 is required.'
    Assert-That ($script:requests -eq $requestsBefore) 'An invalid checksum must fail before downloading.'
    Write-Host 'Engine archive cache tests passed: reuse, verification and failed-download cleanup.'
} finally {
    if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Recurse -Force }
}
