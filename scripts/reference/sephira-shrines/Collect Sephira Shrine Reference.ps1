# Windows PowerShell 5.1. Read prepared native tables; write only the output.
[CmdletBinding()]
param([string]$EnginePath, [string]$OutputRoot)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
try {
    if (-not $EnginePath) { $EnginePath = Read-Host 'Studio folder (the folder containing Studio Test Data)' }
    $engine = $null
    foreach ($suffix in @('', 'engine', 'Studio Test Data\FFR Vision Studio\engine', 'FFR Vision Studio\engine')) {
        $candidate = $EnginePath.Trim().Trim('"')
        if ($suffix) { $candidate = Join-Path $candidate $suffix }
        if (Test-Path -LiteralPath (Join-Path $candidate 'extracted\rows\Map') -PathType Container) {
            $engine = (Resolve-Path -LiteralPath $candidate).Path; break
        }
    }
    if (-not $engine) { throw 'Prepared map tables were not found. Select the Studio folder used to prepare the full game.' }
    $stamp = Join-Path $engine 'launch-prep\prepared-game.json'
    if (-not (Test-Path -LiteralPath $stamp -PathType Leaf)) { throw 'Prepare the full game in Studio first.' }
    $prepared = Get-Content -LiteralPath $stamp -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $OutputRoot) { $OutputRoot = Join-Path $env:USERPROFILE 'Downloads\FFR Mod' }
    $OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
    $prefix = $engine.TrimEnd('\') + '\'
    if ($OutputRoot -eq $engine -or $OutputRoot.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Choose an output folder outside Studio. Default: Downloads\FFR Mod.'
    }
    $tag = 'Sephira-Shrine-Reference-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
    $destination = Join-Path $OutputRoot $tag
    [void][IO.Directory]::CreateDirectory($destination)
    $copied = 0
    foreach ($scope in @('Map', 'Encount')) {
        $source = Join-Path $engine ('extracted\rows\' + $scope)
        if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw ('Missing prepared tables: ' + $scope) }
        foreach ($file in (Get-ChildItem -LiteralPath $source -Recurse -Filter '*.json' -File)) {
            $text = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8
            if ($text -match 'Studio_(?:Crystal|Sephira|Resonance|Practice)') {
                throw 'These prepared tables contain a Studio mod. Restore the mod, prepare the official game again, then collect.'
            }
            $relative = $file.FullName.Substring($engine.Length).TrimStart('\')
            $target = Join-Path $destination $relative
            [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target))
            Copy-Item -LiteralPath $file.FullName -Destination $target
            $copied++
        }
    }
    $npc = Join-Path $destination 'extracted\rows\Map\NPC'
    $gimmick = Join-Path $destination 'extracted\rows\Map\Gimmick'
    if (-not (Test-Path -LiteralPath $npc) -or -not (Test-Path -LiteralPath $gimmick)) {
        throw 'NPC/crystal tables were not prepared. Please send a screenshot of this message.'
    }
    # Only build provenance; do not include configuration, user kits or saves.
    $prepared | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $destination 'prepared-game.json') -Encoding UTF8
    $archive = $destination + '.zip'
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::CreateFromDirectory($destination, $archive)
    Write-Host ('Collected ' + $copied + ' prepared map/encounter tables.') -ForegroundColor Green
    Write-Host 'Attach this ZIP in the chat:'
    Write-Host $archive -ForegroundColor Cyan
} catch {
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
