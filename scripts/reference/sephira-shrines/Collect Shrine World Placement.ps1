[CmdletBinding()]
param([string]$EnginePath, [string]$OutputRoot)
$ErrorActionPreference = 'Stop'
$nativeView = $null
try {
    if (-not $EnginePath) { $EnginePath = Read-Host 'Studio folder (containing Studio Test Data)' }
    $engine = $null
    foreach ($suffix in @('', 'engine', 'Studio Test Data\FFR Vision Studio\engine', 'FFR Vision Studio\engine')) {
        $candidate = $EnginePath.Trim().Trim('"')
        if ($suffix) { $candidate = Join-Path $candidate $suffix }
        if (Test-Path -LiteralPath (Join-Path $candidate 'tools\retoc\retoc.exe') -PathType Leaf) {
            $engine = (Resolve-Path -LiteralPath $candidate).Path; break
        }
    }
    if (-not $engine) { throw 'Cannot find the Studio engine.' }
    $config = Get-Content -LiteralPath (Join-Path $engine 'config.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $paks = Join-Path $config.gameRoot 'FFRS\Content\Paks'
    $prepared = Get-Content -LiteralPath (Join-Path $engine 'launch-prep\prepared-game.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $OutputRoot) { $OutputRoot = Join-Path $env:USERPROFILE 'Downloads\FFR Mod' }
    $root = Join-Path $OutputRoot ('Shrine-World-Placement-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    [void][IO.Directory]::CreateDirectory($root)
    $legacy = Join-Path $root 'legacy'
    $filters = @('FFRS/Content/Map/Wld/GD/', 'FFRS/Content/Map/Wld/EV/',
        'FFRS/Content/Map/Wld/04Dir/EV/', 'FFRS/Content/Map/Wld/05Old/EV/',
        'FFRS/Content/Map/Wld/06Zol/EV/', 'FFRS/Content/Map/Wld/07Mys/EV/',
        'FFRS/Content/Datatable/Map/Area/', 'FFRS/Content/Datatable/Map/DA_MapLandmark')
    $maps = Get-ChildItem -LiteralPath (Join-Path $engine 'extracted\rows\Map\MapData') -Filter '*.json' -File
    foreach ($file in $maps) {
        $table = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($row in $table.rows.PSObject.Properties) {
            if ([string]$row.Value.Level -match '^/Game/Map/Com/00Com/00Com_2[0-3][0-9]/') {
                $package = [string]$row.Value.Level
                $nativePackage = 'FFRS/Content/' + ($package -replace '^/Game/', '')
                $directory = $nativePackage -replace '/[^/]+$', '/'
                $filters += @($nativePackage, ($directory + 'GD/'), ($directory + 'EV/'))
            }
        }
    }
    $filters = @($filters | Sort-Object -Unique)
    # Retoc needs global ScriptObjects AND the complete official patch set.
    # Same-volume hard links avoid copying 11 GB and exclude all installed mods.
    # Delete only the temporary links afterward; original containers stay put.
    $nativeView = Join-Path ([IO.Directory]::GetParent($paks).FullName) ('StudioReferenceView-' + [Guid]::NewGuid().ToString('N'))
    [void][IO.Directory]::CreateDirectory($nativeView)
    $containers = @(Get-ChildItem -LiteralPath $paks -File | Where-Object { $_.Extension -in @('.utoc', '.ucas', '.pak') } | Sort-Object Name)
    foreach ($container in $containers) {
        $expected = $prepared.gameIdentity.containers.PSObject.Properties[$container.Name]
        if ($null -eq $expected -or $container.Length -ne $expected.Value.size) { throw 'The game changed since preparation. Prepare it again first.' }
        if ($container.Extension -eq '.utoc') {
            $actual = (Get-FileHash -LiteralPath $container.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($actual -ne $expected.Value.sha256) { throw 'The game changed since preparation. Prepare it again first.' }
        }
        [void](New-Item -ItemType HardLink -Path (Join-Path $nativeView $container.Name) -Target $container.FullName)
    }
    if (-not (Test-Path -LiteralPath (Join-Path $nativeView 'global.utoc'))) { throw 'The official global.utoc file is missing.' }
    $arguments = @('to-legacy', '--no-shaders')
    foreach ($filter in $filters) { $arguments += @('--filter', $filter) }
    $arguments += @($nativeView, $legacy)
    $previous = $ErrorActionPreference; $ErrorActionPreference = 'Continue'; $reportedFailure = $false
    try {
        & (Join-Path $engine 'tools\retoc\retoc.exe') @arguments 2>&1 |
            ForEach-Object {
                $line = $_.ToString()
                if ($line -match '\(([1-9][0-9]*) failed\)' -or $line -match 'Extracted 0 \(') { $reportedFailure = $true }
                Write-Host $line; Add-Content -LiteralPath (Join-Path $root 'extraction.log') -Value $line -Encoding UTF8
            }
        $code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $previous }
    if ($code -ne 0 -or $reportedFailure) { throw 'Native map extraction failed. See extraction.log; no success ZIP was created.' }
    foreach ($candidate in @('extracted\Mappings.usmap', 'data\Mappings.usmap')) {
        $source = Join-Path $engine $candidate
        if (Test-Path -LiteralPath $source -PathType Leaf) { Copy-Item -LiteralPath $source -Destination (Join-Path $root 'Mappings.usmap'); break }
    }
    $prepared.gameIdentity | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $root 'game-identity.json') -Encoding UTF8
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = $root + '.zip'
    [IO.Compression.ZipFile]::CreateFromDirectory($root, $archive)
    Write-Host 'Attach this ZIP in the chat:' -ForegroundColor Green
    Write-Host $archive -ForegroundColor Cyan
} catch { Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red; exit 1 }
finally { if ($nativeView -and (Test-Path -LiteralPath $nativeView)) { Remove-Item -LiteralPath $nativeView -Recurse -Force } }
