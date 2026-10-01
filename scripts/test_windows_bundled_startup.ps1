$ErrorActionPreference = 'Stop'
$temporary = Join-Path ([IO.Path]::GetTempPath()) ('ffr-engine-' + [Guid]::NewGuid().ToString('N'))
$previousFixture = $env:FFR_STUDIO_ENGINE_FIXTURE
try {
    [void][IO.Directory]::CreateDirectory($temporary)
    # Use the genuine, checksum-pinned supported engine, including its frozen
    # Python runtime. This test does not need a game install or developer Python.
    $expected = '1c6e4d4b348b048404b6578bf10010c4caa873a5599d9dcbb9f64b00d299c41d'
    . (Join-Path $PSScriptRoot 'verified_engine_archive.ps1')
    $cache = if ([string]::IsNullOrWhiteSpace($env:FFR_STUDIO_ENGINE_CACHE)) { $temporary } else { $env:FFR_STUDIO_ENGINE_CACHE }
    $archive = Get-VerifiedEngineArchive -CacheDirectory $cache -Sha256 $expected `
        -Uri 'https://ffr.luminest.io/engine/engine-1.0.0.15.zip'
    $env:FFR_STUDIO_ENGINE_FIXTURE = Join-Path $temporary 'engine'
    Expand-Archive -LiteralPath $archive -DestinationPath $env:FFR_STUDIO_ENGINE_FIXTURE
    flutter test --no-pub test/windows_bundled_startup_test.dart
    if ($LASTEXITCODE -ne 0) { throw 'The fresh Windows bundled startup test failed.' }
} catch {
    # Expose the actual failure through the Checks API as well as the console.
    # This keeps cloud diagnosis possible when the log storage cannot be reached.
    $details = "$($_.Exception.Message)`n$($_.ScriptStackTrace)"
    $details = $details.Replace('%', '%25').Replace("`r", '%0D').Replace("`n", '%0A')
    Write-Output "::error::$details"
    throw
} finally {
    $env:FFR_STUDIO_ENGINE_FIXTURE = $previousFixture
    if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Recurse -Force }
}
