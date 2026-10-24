[CmdletBinding()]
param([string]$EnginePath, [string]$GamePath, [string]$OutputRoot)
$ErrorActionPreference = 'Stop'
$nativeView = $null
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
    if (-not $GamePath) {
        $config = Get-Content -LiteralPath (Join-Path $engine 'config.json') -Raw -Encoding UTF8 | ConvertFrom-Json
        $GamePath = [string]$config.gameRoot
    }
    if (-not $GamePath) { throw 'The full-game folder is not configured in Studio.' }
    if ($GamePath -match '(?i)RESONANCE DEMO') { throw 'Studio still points to the demo. Select the full game in Studio, or run this script with -GamePath pointing to the full game.' }
    $paks = Join-Path $GamePath 'FFRS\Content\Paks'
    if (-not (Test-Path -LiteralPath (Join-Path $paks 'global.utoc') -PathType Leaf)) {
        throw 'Cannot find full-game FFRS\Content\Paks\global.utoc.'
    }
    Write-Host ('Collecting the cave from: ' + $GamePath) -ForegroundColor Cyan
    if (-not $OutputRoot) { $OutputRoot = Join-Path $env:USERPROFILE 'Downloads\FFR Mod' }
    $root = Join-Path $OutputRoot ('Christine-Cave-Reference-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,6))
    [void][IO.Directory]::CreateDirectory($root)
    $legacy = Join-Path $root 'legacy'
    # Native headers, global ScriptObjects and all official patches must be
    # together. Same-volume hard links avoid copying the game and exclude mods.
    $nativeView = Join-Path ([IO.Directory]::GetParent($paks).FullName) ('StudioCaveReference-' + [Guid]::NewGuid().ToString('N'))
    [void][IO.Directory]::CreateDirectory($nativeView)
    $containers = @(Get-ChildItem -LiteralPath $paks -File | Where-Object {
        $_.Extension -in @('.utoc','.ucas','.pak') -and
        ($_.BaseName -eq 'global' -or $_.BaseName -match '^FFRS-Windows(?:_|$)')
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
    $filters = @('FFRS/Content/Map/Dng/01Gra/01Gra_44/',
        'FFRS/Content/BP/Map/Gimmick/BP_MapGimmick_EventTrigger',
        'FFRS/Content/Sound/Cri/Bgm/BGM_PP/')
    $arguments = @('to-legacy','--no-shaders')
    foreach ($filter in $filters) { $arguments += @('--filter',$filter) }
    $arguments += @($nativeView,$legacy)
    $previous = $ErrorActionPreference; $ErrorActionPreference = 'Continue'; $reportedFailure = $false
    try {
        & (Join-Path $engine 'tools\retoc\retoc.exe') @arguments 2>&1 | ForEach-Object {
            $line = $_.ToString()
            if ($line -match '\(([1-9][0-9]*) failed\)' -or $line -match 'Extracted 0 \(') { $reportedFailure = $true }
            Write-Host $line
            Add-Content -LiteralPath (Join-Path $root 'extraction.log') -Value $line -Encoding UTF8
        }
        $code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $previous }
    if ($code -ne 0 -or $reportedFailure) { throw 'Cave extraction failed. No success ZIP was created; keep extraction.log.' }
    $level = Join-Path $legacy 'FFRS\Content\Map\Dng\01Gra\01Gra_44\Dng_01Gra_44_PL.umap'
    if (-not (Test-Path -LiteralPath $level -PathType Leaf)) { throw 'The expected secret-cave level was not extracted. No success ZIP was created.' }
    $mappingsFound = $false
    foreach ($candidate in @('extracted\Mappings.usmap','data\Mappings.usmap')) {
        $source = Join-Path $engine $candidate
        if (Test-Path -LiteralPath $source -PathType Leaf) { Copy-Item -LiteralPath $source -Destination (Join-Path $root 'Mappings.usmap'); $mappingsFound = $true; break }
    }
    if (-not $mappingsFound) { throw 'Studio mappings were not found. No success ZIP was created.' }
    $music = Join-Path $legacy 'FFRS\Content\Sound\Cri\Bgm\BGM_PP'
    if (-not @(Get-ChildItem -LiteralPath $music -Filter '*.uasset' -File).Count) {
        throw 'The native cave music metadata was not extracted. No success ZIP was created.'
    }
    $inventory = @(Get-ChildItem -LiteralPath $legacy -Recurse -File | ForEach-Object {
        @{path=$_.FullName.Substring($legacy.Length).TrimStart('\','/').Replace('\','/');size=$_.Length}
    })
    @{schema=1;gameRoot=$GamePath;musicCue='BGM_PP_DUNGEON_CAVE1';filters=$filters;containers=$identity;files=$inventory} |
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
    Write-Host 'The game, saves and installed mods were not modified. Game preparation is not required.'
} catch { Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red; exit 1 }
finally {
    if ($nativeView -and (Test-Path -LiteralPath $nativeView)) { Remove-Item -LiteralPath $nativeView -Recurse -Force }
}
