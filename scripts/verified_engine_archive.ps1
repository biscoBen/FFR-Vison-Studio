function Get-VerifiedEngineArchive {
    param(
        [Parameter(Mandatory = $true)][string]$CacheDirectory,
        [Parameter(Mandatory = $true)][string]$Uri,
        [Parameter(Mandatory = $true)][string]$Sha256
    )
    if ($Sha256 -notmatch '^[0-9a-fA-F]{64}$') { throw 'An engine archive SHA-256 is required.' }
    [void][IO.Directory]::CreateDirectory($CacheDirectory)
    $archive = Join-Path $CacheDirectory ($Sha256.ToLowerInvariant() + '.zip')
    if (Test-Path -LiteralPath $archive -PathType Leaf) {
        if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ine $Sha256) {
            throw 'The cached Windows startup test engine checksum did not match.'
        }
        Write-Host 'Using the cached, checksum-verified Windows engine archive.'
        return $archive
    }
    $partial = Join-Path $CacheDirectory ([Guid]::NewGuid().ToString('N') + '.partial')
    try {
        Invoke-WebRequest -Uri $Uri -OutFile $partial -UseBasicParsing -TimeoutSec 120
        if ((Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash -ine $Sha256) {
            throw 'The Windows startup test engine checksum did not match.'
        }
        Move-Item -LiteralPath $partial -Destination $archive
        Write-Host 'Downloaded and verified the Windows engine archive for reuse.'
        return $archive
    } finally {
        if (Test-Path -LiteralPath $partial) { Remove-Item -LiteralPath $partial -Force }
    }
}
