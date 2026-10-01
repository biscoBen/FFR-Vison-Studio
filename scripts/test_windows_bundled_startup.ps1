$ErrorActionPreference = 'Stop'
$temporary = Join-Path ([IO.Path]::GetTempPath()) ('ffr-engine-' + [Guid]::NewGuid().ToString('N'))
$previousFixture = $env:FFR_STUDIO_ENGINE_FIXTURE
try {
    [void][IO.Directory]::CreateDirectory($temporary)
    $archive = Join-Path $temporary 'engine.zip'
    # Use the genuine, checksum-pinned supported engine, including its frozen
    # Python runtime. This test does not need a game install or developer Python.
    Invoke-WebRequest -Uri 'https://ffr.luminest.io/engine/engine-1.0.0.15.zip' -OutFile $archive -UseBasicParsing -TimeoutSec 120
    $expected = '1c6e4d4b348b048404b6578bf10010c4caa873a5599d9dcbb9f64b00d299c41d'
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ine $expected) {
        throw 'The Windows startup test engine checksum did not match.'
    }
    $env:FFR_STUDIO_ENGINE_FIXTURE = Join-Path $temporary 'engine'
    Expand-Archive -LiteralPath $archive -DestinationPath $env:FFR_STUDIO_ENGINE_FIXTURE
    flutter test test/windows_bundled_startup_test.dart
    if ($LASTEXITCODE -ne 0) { throw 'The fresh Windows bundled startup test failed.' }
} finally {
    $env:FFR_STUDIO_ENGINE_FIXTURE = $previousFixture
    if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Recurse -Force }
}
