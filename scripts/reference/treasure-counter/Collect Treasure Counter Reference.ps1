# Export native definitions only; no observer, game launch or mod installation.
[CmdletBinding()]
param([string]$EnginePath, [string]$GamePath, [string]$OutputRoot, [switch]$ChooseGamePath, [switch]$Followup)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$nativeView = $null
$ownsNativeView = $false

function Find-Engine([string]$Candidate) {
    if (-not $Candidate) { return $null }
    foreach ($suffix in @('', 'engine', 'Studio Test Data\FFR Vision Studio\engine', 'FFR Vision Studio\engine')) {
        $path = $Candidate.Trim().Trim('"')
        if ($suffix) { $path = Join-Path $path $suffix }
        if (Test-Path -LiteralPath (Join-Path $path 'tools\retoc\retoc.exe') -PathType Leaf) {
            return (Resolve-Path -LiteralPath $path).Path
        }
    }
    return $null
}
function Test-DemoFolder([string]$Candidate) {
    if (-not $Candidate) { return $false }
    $leaf = ($Candidate.Trim().Trim('"').TrimEnd('\','/') -split '[\\/]')[-1]
    return $leaf -match '(?i)RESONANCE\s+DEMO(?:\s|$)'
}
function Find-Game([string]$Candidate) {
    if (-not $Candidate) { return $null }
    $path = $Candidate.Trim().Trim('"')
    if (Test-DemoFolder $path) { return $null }
    # Check the root before Join-Path: an absent Steam drive is a failed
    # candidate, not a terminating PowerShell drive-resolution error.
    if (-not (Test-Path -LiteralPath $path -PathType Container -ErrorAction SilentlyContinue)) { return $null }
    if (Test-Path -LiteralPath (Join-Path $path 'FFRS\Content\Paks\global.utoc') -PathType Leaf -ErrorAction SilentlyContinue) {
        return (Resolve-Path -LiteralPath $path).Path
    }
    return $null
}
function Select-ReferenceAsset([string]$Path) {
    if ($Followup) {
        return ($Path -match '^FFRS/Content/Map/Event/Com/00Eve_(?:87|93|94|96|97|112)/.*_(?:GD(?:_[^/]*)?|PL)\.(?:uasset|umap)$' -or
            $Path -match '^FFRS/Content/BP/Map/Gimmick/BP_MapGimmick_FieldItem\.' -or
            $Path -match '^FFRS/Content/UI/MainMenu/Common/Key/KeyGuide/WBP_KeyGuide\.' -or
            $Path -match '^FFRS/Content/UI/Battle/KeyGuide/Speed/WBP_BtlKeyGuide_Speed\.' -or
            $Path -match '^FFRS/Content/UI/Battle/Command/(?:Data/DA_BtlCmd|ViewModel/VM_BtlCmd)\.' -or
            $Path -match '^FFRS/Content/BP/Map/Unit/BP_MapUnit_Player\.' -or
            $Path -match '^FFRS/Plugins/EnhancedUI/Content/Foundation/Panel/DirGrid/WBP_DirectionGridPanel\.')
    }
    return ($Path -match '^FFRS/Content/Map/(?:Dng|Com)/.*_(?:GD(?:_[^/]*)?|PL)\.(?:uasset|umap)$' -or
        $Path -match '^FFRS/Content/Datatable/Map/(?:MapData/|CDT_MapData|Gimmick/)' -or
        ($Path -match '^FFRS/Content/BP/Map/Gimmick/' -and $Path -notmatch '/Animation/') -or
        $Path -match '^FFRS/Content/BP/Event/GimmickEvent/' -or
        $Path -match '^FFRS/Content/BP/Event/Tutorial/BP_Tutorial_Fragment\.' -or
        $Path -match '^FFRS/Content/UI/Field/(?:Object/Collected/|MiniMap/)')
}

# ZIP support is shared with the previously reviewed source collector.
function New-UploadZip([string]$Destination, [object[]]$Segments) {
    $stream = [System.IO.File]::Open($Destination, [System.IO.FileMode]::CreateNew)
    $archive = $null
    try {
        $archive = New-Object System.IO.Compression.ZipArchive -ArgumentList @(
            $stream, [System.IO.Compression.ZipArchiveMode]::Create, $true)
        $buffer = New-Object byte[] 65536
        foreach ($segment in $Segments) {
            $entry = $archive.CreateEntry($segment.entry, [System.IO.Compression.CompressionLevel]::Optimal)
            $target = $null; $source = $null
            try {
                $target = $entry.Open()
                $source = [System.IO.File]::Open($segment.source, [System.IO.FileMode]::Open,
                    [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
                [void]$source.Seek($segment.offset, [System.IO.SeekOrigin]::Begin)
                $remaining = [long]$segment.bytes
                while ($remaining -gt 0) {
                    $read = $source.Read($buffer, 0, [int][Math]::Min($buffer.Length, $remaining))
                    if ($read -le 0) { throw ('Source file ended early: ' + $segment.source) }
                    $target.Write($buffer, 0, $read)
                    $remaining -= $read
                }
            } finally {
                if ($null -ne $source) { $source.Dispose() }
                if ($null -ne $target) { $target.Dispose() }
            }
        }
    } finally {
        if ($null -ne $archive) { $archive.Dispose() }
        $stream.Dispose()
    }
}

try {
    Write-Host 'Treasure-counter definition export (no game script installed)' -ForegroundColor Cyan
    if ($Followup) { Write-Host 'Small follow-up: special dungeon levels and native input/status widgets only.' -ForegroundColor Cyan }
    $engine = Find-Engine $EnginePath
    if ($EnginePath -and -not $engine) { throw 'Cannot find the Studio engine in the supplied folder.' }
    if (-not $engine) {
        $candidates = @()
        if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA 'FFR Vision Studio') }
        if ($env:USERPROFILE) {
            $candidates += (Join-Path $env:USERPROFILE 'Downloads\Sephira-Studio-Test')
            $candidates += (Join-Path $env:USERPROFILE 'Downloads\FFR Mod\Sephira-Studio-Test')
        }
        foreach ($candidate in $candidates) { $engine = Find-Engine $candidate; if ($engine) { break } }
        if (-not $engine) { $engine = Find-Engine (Read-Host 'Studio folder (or its engine folder)') }
    }
    if (-not $engine) { throw 'Cannot find Studio tools\retoc\retoc.exe.' }
    if ($GamePath -and (Test-DemoFolder $GamePath)) { throw 'Select the full game rather than the demo.' }
    $game = Find-Game $GamePath
    if ($GamePath -and -not $game) { throw 'Cannot find the full game in the supplied folder.' }
    if (-not $game -and -not $ChooseGamePath -and (Test-Path -LiteralPath (Join-Path $engine 'config.json') -PathType Leaf)) {
        try {
            $saved = Get-Content -LiteralPath (Join-Path $engine 'config.json') -Raw -Encoding UTF8 | ConvertFrom-Json
            $property = $saved.PSObject.Properties['gameRoot']
            if ($null -ne $property) { $game = Find-Game ([string]$property.Value) }
            if (-not $game) { Write-Host 'Studio has a saved demo or unavailable game path; looking for the full game.' -ForegroundColor Yellow }
        } catch {
            Write-Host 'Studio game settings could not be read; looking for the full game.' -ForegroundColor Yellow
        }
    }
    if (-not $game -and -not $ChooseGamePath) {
        foreach ($drive in @('G','D','C','E','F')) {
            $game = Find-Game ($drive + ':\Steam\steamapps\common\FINAL FANTASY RESONANCE')
            if ($game) { break }
        }
    }
    if (-not $game) { $game = Find-Game (Read-Host 'Game folder containing FFRS') }
    if (-not $game) { throw 'Cannot find the full-game FFRS\Content\Paks\global.utoc.' }
    Write-Host ('Using game folder: ' + $game) -ForegroundColor Cyan
    $paks = Join-Path $game 'FFRS\Content\Paks'
    if (-not $OutputRoot) { $OutputRoot = Join-Path $env:USERPROFILE 'Downloads\FFR Mod' }
    $prefix = if ($Followup) { 'Treasure-Controls-Followup-' } else { 'Treasure-Counter-Reference-' }
    $tag = $prefix + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,6)
    $root = Join-Path $OutputRoot $tag
    [void][IO.Directory]::CreateDirectory($root)
    $legacy = Join-Path $root 'legacy'
    $nativeView = Join-Path ([IO.Directory]::GetParent($paks).FullName) ('StudioTreasureReference-' + [Guid]::NewGuid().ToString('N'))
    [void](New-Item -ItemType Directory -Path $nativeView -ErrorAction Stop)
    $ownsNativeView = $true
    $containers = @(Get-ChildItem -LiteralPath $paks -File | Where-Object {
        $_.Extension -in @('.utoc','.ucas','.pak') -and
        ($_.BaseName -eq 'global' -or $_.BaseName -match '^FFRS-Windows(?:_[0-9]+_P)?$')
    } | Sort-Object Name)
    if (-not @($containers | Where-Object { $_.Extension -eq '.utoc' -and $_.BaseName -match '^FFRS-Windows' }).Count) {
        throw 'No official FFRS-Windows containers were found.'
    }
    $identity = @()
    foreach ($file in $containers) {
        [void](New-Item -ItemType HardLink -Path (Join-Path $nativeView $file.Name) -Target $file.FullName)
        $entry = @{name=$file.Name;size=$file.Length}
        if ($file.Extension -eq '.utoc') { $entry.sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
        $identity += $entry
    }
    $retoc = Join-Path $engine 'tools\retoc\retoc.exe'
    Write-Host 'Listing official dungeon gameplay levels and pickup definitions...' -ForegroundColor Cyan
    $selected = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
    $listLog = Join-Path $root 'listing.log'
    $previous = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try {
        & $retoc list --path $nativeView 2>&1 | ForEach-Object {
            $line = $_.ToString().Replace('\','/')
            if ($line -match '(?<asset>(?:\.\./)*FFRS/(?:Content|Plugins)/[^\r\n]+?\.(?:uasset|umap))\s*$') {
                $asset = $Matches['asset'] -replace '^(?:\.\./)+',''
                if (Select-ReferenceAsset $asset) { [void]$selected.Add($asset) }
            } elseif ($line -match '(?i)error|failed') {
                Add-Content -LiteralPath $listLog -Value $line -Encoding UTF8
            }
        }
        $code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $previous }
    if ($code -ne 0) { throw 'Official asset listing failed; no success ZIP was created.' }
    $assets = @($selected | Sort-Object)
    $gameplayPattern = if ($Followup) { '/Map/Event/Com/00Eve_(?:87|93|94|96|97|112)/.*_PL\.' } else { '/Map/Dng/.*_GD(?:_[^/]*)?\.' }
    if (-not @($assets | Where-Object { $_ -match $gameplayPattern }).Count -or
        -not @($assets | Where-Object { $_ -match '/BP/Map/Gimmick/BP_MapGimmick_FieldItem\.' }).Count) {
        throw 'Dungeon gameplay and native FieldItem definitions were not found; no success ZIP was created.'
    }
    if ($Followup) {
        foreach ($id in @(87,93,94,96,97,112)) {
            if (-not @($assets | Where-Object { $_ -match ('/Map/Event/Com/00Eve_' + $id + '/.*_PL\.') }).Count) {
                throw ('Missing special dungeon ' + $id + '; no success ZIP was created.')
            }
        }
        if (-not @($assets | Where-Object { $_ -match '/KeyGuide/WBP_KeyGuide\.' }).Count -or
            -not @($assets | Where-Object { $_ -match '/DirGrid/WBP_DirectionGridPanel\.' }).Count) {
            throw 'Native status widgets were not found; no success ZIP was created.'
        }
    }
    $assets | Set-Content -LiteralPath (Join-Path $root 'selected-assets.txt') -Encoding UTF8
    # Batch exact package filters to stay below Windows command-line limits.
    $filters = @($assets | ForEach-Object { $_ -replace '\.(?:uasset|umap)$','' } | Select-Object -Unique)
    for ($offset=0; $offset -lt $filters.Count; $offset+=24) {
        $last = [Math]::Min($offset+23,$filters.Count-1)
        $arguments = @('to-legacy','--no-shaders')
        foreach ($filter in $filters[$offset..$last]) { $arguments += @('--filter',$filter) }
        $arguments += @($nativeView,$legacy)
        Write-Host ('Extracting metadata batch {0}/{1}...' -f ([int]($offset/24)+1),[Math]::Ceiling($filters.Count/24))
        $previous = $ErrorActionPreference; $ErrorActionPreference = 'Continue'; $reportedFailure = $false
        try {
            & $retoc @arguments 2>&1 | ForEach-Object {
                $line = $_.ToString()
                if ($line -match '\(([1-9][0-9]*) failed\)' -or $line -match 'Extracted 0 \(') { $reportedFailure = $true }
                Write-Host $line
                Add-Content -LiteralPath (Join-Path $root 'extraction.log') -Value $line -Encoding UTF8
            }
            $code = $LASTEXITCODE
        } finally { $ErrorActionPreference = $previous }
        if ($code -ne 0 -or $reportedFailure) { throw 'Definition extraction failed; no success ZIP was created. Keep extraction.log.' }
    }
    $fieldItem = Join-Path $legacy 'FFRS\Content\BP\Map\Gimmick\BP_MapGimmick_FieldItem.uasset'
    if (-not (Test-Path -LiteralPath $fieldItem -PathType Leaf)) { throw 'Native FieldItem source is missing; no success ZIP was created.' }
    $missing = @()
    foreach ($asset in $assets) {
        $stem = Join-Path $legacy ($asset -replace '\.(?:uasset|umap)$','')
        if (-not (Test-Path -LiteralPath ($stem+'.uasset') -PathType Leaf) -and
            -not (Test-Path -LiteralPath ($stem+'.umap') -PathType Leaf)) { $missing += $asset }
    }
    if ($missing.Count) { throw ('Incomplete definition export; no success ZIP was created. Missing: ' + (($missing | Select-Object -First 8) -join ', ')) }
    $mappingsFound = $false
    foreach ($candidate in @('extracted\Mappings.usmap','data\Mappings.usmap')) {
        $source = Join-Path $engine $candidate
        if (Test-Path -LiteralPath $source -PathType Leaf) {
            Copy-Item -LiteralPath $source -Destination (Join-Path $root 'Mappings.usmap'); $mappingsFound=$true;break
        }
    }
    if (-not $mappingsFound) { throw 'Studio mappings were not found; no success ZIP was created.' }
    $inventory = @(Get-ChildItem -LiteralPath $legacy -Recurse -File | ForEach-Object {
        @{path=$_.FullName.Substring($legacy.Length).TrimStart('\','/').Replace('\','/');size=$_.Length}
    })
    @{schema=1;purpose='dungeon-treasure-counter-native-definitions';followup=[bool]$Followup;containers=$identity;assets=$assets;files=$inventory} |
        ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $root 'reference.json') -Encoding UTF8
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $files = @(Get-ChildItem -LiteralPath $root -Recurse -File | Sort-Object FullName)
    $tag = [IO.Path]::GetFileName($root)
    $segments = @(); $ledgerFiles = @(); $index = 0
    foreach ($file in $files) {
        $entry = $file.FullName.Substring($root.Length).TrimStart('\', '/').Replace('\', '/')
        if ($file.Length -le 20MB) {
            $segments += [PSCustomObject]@{ source = $file.FullName; entry = $entry; offset = 0L; bytes = $file.Length }
        } else {
            $parts = @(); $offset = 0L; $part = 0
            while ($offset -lt $file.Length) {
                $bytes = [long][Math]::Min(20MB, $file.Length - $offset)
                $chunk = '_reference_chunks/' + $index.ToString('000000') + '/' + $part.ToString('000000') + '.bin'
                $segments += [PSCustomObject]@{ source = $file.FullName; entry = $chunk; offset = $offset; bytes = $bytes }
                $parts += [PSCustomObject]@{ path = $chunk; bytes = $bytes }
                $offset += $bytes; $part++
            }
            $ledgerFiles += [PSCustomObject]@{ path = $entry; bytes = $file.Length; sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant(); parts = @($parts) }
        }
        $index++
    }
    $ledger = Join-Path $root 'split-files.json'
    [ordered]@{ schema = 1; files = @($ledgerFiles) } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ledger -Encoding UTF8
    $segments += [PSCustomObject]@{ source = $ledger; entry = 'split-files.json'; offset = 0L; bytes = (Get-Item -LiteralPath $ledger).Length }
    $batch = @(); $bytes = 0L; $part = 1
    foreach ($segment in $segments) {
        if ($batch.Count -gt 0 -and $bytes + $segment.bytes -gt 22MB) {
            New-UploadZip (Join-Path $OutputRoot ($tag + '-' + $part.ToString('000') + '.zip')) $batch
            $batch = @(); $bytes = 0L; $part++
        }
        $batch += $segment; $bytes += $segment.bytes
    }
    if ($batch.Count) { New-UploadZip (Join-Path $OutputRoot ($tag + '-' + $part.ToString('000') + '.zip')) $batch }
    Write-Host 'Attach all of these ZIPs in the chat:' -ForegroundColor Green
    Get-ChildItem -LiteralPath $OutputRoot -Filter ($tag + '-*.zip') | ForEach-Object { Write-Host $_.FullName -ForegroundColor Cyan }
    Write-Host 'Game assets, saves and installed mods were not modified. No game launch or F8 is required.'
} catch { Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red; exit 1 }
finally {
    if ($ownsNativeView -and $nativeView -and (Test-Path -LiteralPath $nativeView -PathType Container)) {
        Remove-Item -LiteralPath $nativeView -Recurse -Force
    }
}
