# Compatible with Windows PowerShell 5.1. Only the output folder is written.
[CmdletBinding()]
param([string]$EnginePath, [string]$GamePath, [string]$OutputRoot, [switch]$NoPrompt)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$script:logFile = $null

function Find-Engine([string]$Candidate) {
    if ([string]::IsNullOrWhiteSpace($Candidate)) { return $null }
    $Candidate = $Candidate.Trim().Trim('"')
    foreach ($suffix in @('', 'engine', 'Studio Test Data\FFR Vision Studio\engine', 'FFR Vision Studio\engine')) {
        $path = $Candidate
        if ($suffix) { $path = Join-Path $Candidate $suffix }
        if (Test-Path -LiteralPath (Join-Path $path 'tools\retoc\retoc.exe') -PathType Leaf) {
            return (Resolve-Path -LiteralPath $path).Path
        }
    }
    return $null
}

function Find-Paks([string]$Candidate) {
    if ([string]::IsNullOrWhiteSpace($Candidate)) { return $null }
    $Candidate = $Candidate.Trim().Trim('"')
    foreach ($suffix in @('', 'FFRS\Content\Paks')) {
        $path = $Candidate
        if ($suffix) { $path = Join-Path $Candidate $suffix }
        if ((Test-Path -LiteralPath $path -PathType Container) -and
            @(Get-ChildItem -LiteralPath $path -Filter '*.utoc' -File).Count -gt 0) {
            return (Resolve-Path -LiteralPath $path).Path
        }
    }
    return $null
}

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
    # retoc writes UTF-8. Windows PowerShell otherwise decodes native stdout
    # using the console OEM code page, corrupting non-ASCII inventory names.
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding -ArgumentList $false
    $OutputEncoding = [Console]::OutputEncoding
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    Write-Host 'Collect native skill routing references' -ForegroundColor Cyan
    Write-Host 'This reads the game and writes reference files under Downloads\FFR Mod.'
    Write-Host 'Full battle references include effects/textures and may take several minutes and multiple ZIPs.'
    Write-Host ''

    $engine = Find-Engine $EnginePath
    if (-not $engine -and $EnginePath) { throw 'The supplied engine path does not contain tools\retoc\retoc.exe.' }
    if (-not $engine) {
        $defaults = @(
            (Join-Path $env:USERPROFILE 'Downloads\Sephira-Studio-Test'),
            (Join-Path $env:USERPROFILE 'Downloads\FFR Mod\Sephira-Studio-Test'),
            $PSScriptRoot
        )
        if ($env:LOCALAPPDATA) { $defaults += (Join-Path $env:LOCALAPPDATA 'FFR Vision Studio') }
        foreach ($candidate in $defaults) {
            $engine = Find-Engine $candidate
            if ($engine) { break }
        }
        $prompt = 'Studio folder or engine folder'
        if ($engine) { $prompt += ' (Enter for ' + $engine + ')' }
        $entered = if ($NoPrompt) { '' } else { Read-Host $prompt }
        if ($entered) { $engine = Find-Engine $entered }
        if (-not $engine) { throw 'Could not find the engine. Select the Studio folder containing Studio Test Data, or its engine folder.' }
    }

    $paks = Find-Paks $GamePath
    if (-not $paks -and $GamePath) { throw 'The supplied game folder does not contain .utoc files in FFRS\Content\Paks.' }
    if (-not $paks) {
        $configFile = Join-Path $engine 'config.json'
        if (Test-Path -LiteralPath $configFile -PathType Leaf) {
            try {
                $config = Get-Content -LiteralPath $configFile -Raw -Encoding UTF8 | ConvertFrom-Json
                $gameProperty = $config.PSObject.Properties['gameRoot']
                if ($null -ne $gameProperty) { $paks = Find-Paks ([string]$gameProperty.Value) }
            } catch { Write-Host 'Could not read the saved game path; enter it below.' }
        }
        if (-not $paks) { $paks = Find-Paks 'D:\Steam\steamapps\common\FINAL FANTASY RESONANCE DEMO' }
        if (-not $paks -and ${env:ProgramFiles(x86)}) {
            $paks = Find-Paks (Join-Path ${env:ProgramFiles(x86)} 'Steam\steamapps\common\FINAL FANTASY RESONANCE DEMO')
        }
        $prompt = 'Resonance game folder or Paks folder'
        if ($paks) { $prompt += ' (Enter for ' + $paks + ')' }
        $entered = if ($NoPrompt) { '' } else { Read-Host $prompt }
        if ($entered) { $paks = Find-Paks $entered }
        if (-not $paks) { throw 'Could not find game containers. Enter the folder containing FFRS, or the Paks folder itself.' }
    }

    if (-not $OutputRoot) { $OutputRoot = Join-Path $env:USERPROFILE 'Downloads\FFR Mod' }
    $OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)
    $gameRoot = [System.IO.Directory]::GetParent($paks).Parent.Parent.FullName
    foreach ($sourceRoot in @($engine, $gameRoot)) {
        $prefix = $sourceRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
        if ($OutputRoot -eq $sourceRoot -or $OutputRoot.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw 'Choose an output folder outside Studio and the game folder. Default: Downloads\FFR Mod.'
        }
    }
    [void][System.IO.Directory]::CreateDirectory($OutputRoot)
    $tag = 'Skill-Routing-Reference-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 6)
    $runRoot = Join-Path $OutputRoot $tag
    [void][System.IO.Directory]::CreateDirectory($runRoot)
    $assetRoot = Join-Path $runRoot 'legacy'
    [void][System.IO.Directory]::CreateDirectory($assetRoot)
    $script:logFile = Join-Path $runRoot 'extraction.log'
    $retoc = Join-Path $engine 'tools\retoc\retoc.exe'

    # Broad battle-reference scope, including original timelines, full visual
    # assets and shared dependencies. Keep complete native package bytes, not
    # only same-number effects: several skills use aliases or another folder.
    $filters = @(
        'FFRS/Content/Datatable/Skill/',
        'FFRS/Content/Datatable/Battle/',
        'FFRS/Content/Datatable/Asset/',
        'FFRS/Content/Datatable/Unit/',
        'FFRS/Content/Datatable/Encount/',
        'FFRS/Content/Datatable/Item/',
        'FFRS/Content/Datatable/Sequencer/',
        'FFRS/Content/Datatable/Color/',
        'FFRS/Content/Datatable/PostProcess/',
        'FFRS/Content/Datatable/Strings/ST_Skill/',
        'FFRS/Content/Datatable/DT_AppDataTableList.uasset',
        'FFRS/Content/Datatable/CDT_AppDataTableList_Demo.uasset',
        'FFRS/Content/Datatable/DT_AppDataTableList_Demo.uasset',
        'FFRS/Content/Sequencer/Battle/',
        'FFRS/Content/Sequencer/Skill/',
        'FFRS/Content/BP/Battle/',
        'FFRS/Content/BP/Camera/',
        'FFRS/Content/BP/Effect/',
        'FFRS/Content/BP/PostProcess/',
        'FFRS/Content/BP/Movie/',
        'FFRS/Content/BP/Map/Unit/',
        'FFRS/Content/Effect/',
        'FFRS/Content/Chara/Unit/',
        'FFRS/Content/Chara/monster/',
        'FFRS/Content/Chara/summon/',
        'FFRS/Content/PostProcess/',
        'FFRS/Content/Sound/Cri/Se/',
        'FFRS/Content/Sound/Cri/Voice/VO_BTL/',
        'FFRS/Content/Movies/Sequencer/',
        'FFRS/Content/Movies/Skill/',
        'FFRS/Content/Movies/summon/',
        'FFRS/Plugins/SpriteStudio6/Content/',
        'Engine/Content/',
        'Engine/Plugins/FX/Niagara/Content/'
    )
    $errors = @()
    for ($index = 0; $index -lt $filters.Count; $index++) {
        $filter = $filters[$index]
        $label = '[' + ($index + 1) + '/' + $filters.Count + '] ' + $filter
        Write-Host $label -ForegroundColor Cyan
        Add-Content -LiteralPath $script:logFile -Value $label -Encoding UTF8
        # Passing a real argument array avoids embedded-command quoting errors.
        # Legacy PowerShell can turn native stderr into errors; preserve it as
        # log output and use the native exit code to decide extraction status.
        $reportedFailure = $false
        $previousPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            & $retoc to-legacy --no-shaders --filter $filter $paks $assetRoot 2>&1 |
                ForEach-Object {
                    $line = $_.ToString()
                    if ($line -match '\(([1-9][0-9]*) failed\)' -or $line -match 'Extracted 0 \(') {
                        $reportedFailure = $true
                    }
                    Write-Host $line
                    Add-Content -LiteralPath $script:logFile -Value $line -Encoding UTF8
                }
            $retocCode = $LASTEXITCODE
        } finally { $ErrorActionPreference = $previousPreference }
        if ($retocCode -ne 0) { $errors += $filter + ' (exit ' + $retocCode + ')' }
        elseif ($reportedFailure) { $errors += $filter + ' (retoc reported missing or failed assets; see log)' }
    }

    $inventory = Join-Path $runRoot 'game-asset-index.txt'
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $retoc list --path $paks 2>&1 | Out-File -LiteralPath $inventory -Encoding UTF8
        $inventoryCode = $LASTEXITCODE
    } finally { $ErrorActionPreference = $previousPreference }
    if ($inventoryCode -ne 0) { $errors += 'Game asset inventory (exit ' + $inventoryCode + ')' }

    $mapping = $null
    foreach ($relative in @('extracted\Mappings.usmap', 'data\Mappings.usmap')) {
        $candidate = Join-Path $engine $relative
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { $mapping = $candidate; break }
    }
    if ($mapping) { Copy-Item -LiteralPath $mapping -Destination (Join-Path $runRoot 'Mappings.usmap') }

    # Container headers are small and identify the exact native installation.
    # Payload containers stay on this PC. Do not enumerate ~mods or other mods.
    $containers = @()
    foreach ($file in (Get-ChildItem -LiteralPath $paks -File | Sort-Object Name)) {
        if ($file.Extension -notin @('.utoc', '.ucas', '.pak')) { continue }
        $digest = $null
        if ($file.Extension -eq '.utoc') {
            $digest = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
        $containers += [PSCustomObject]@{ name = $file.Name; bytes = $file.Length; utocSha256 = $digest }
    }
    [ordered]@{
        schema = 1; nativeContainers = @($containers)
        retocSha256 = (Get-FileHash -LiteralPath $retoc -Algorithm SHA256).Hash.ToLowerInvariant()
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $runRoot 'native-container-index.json') -Encoding UTF8

    # Record source paths and coverage without copying config, saved kits, saves,
    # runtime logs or mod containers. Only gameRoot was read for path discovery.
    $files = @(Get-ChildItem -LiteralPath $assetRoot -Recurse -File)
    $assets = @($files | Where-Object { $_.Extension -in @('.umap', '.uasset') })
    if ($assets.Count -eq 0) { throw ('No assets were extracted. See ' + $script:logFile) }
    $found = @{}
    foreach ($file in $assets) {
        $relative = $file.FullName.Substring($assetRoot.Length).TrimStart('\', '/').Replace('\', '/')
        $found[$relative] = $true
    }
    $expected = @{}
    if ($inventoryCode -eq 0) {
        foreach ($line in (Get-Content -LiteralPath $inventory -Encoding UTF8)) {
            $normalized = $line.Replace('\', '/')
            if ($normalized -notmatch '(?:^|\s)(?:\.\./)+((?:FFRS|Engine)/.+\.(?:uasset|umap))\s*$') { continue }
            $relative = $Matches[1]
            foreach ($filter in $filters) {
                if (($filter.EndsWith('/') -and $relative.StartsWith($filter, [System.StringComparison]::OrdinalIgnoreCase)) -or
                    $relative.Equals($filter, [System.StringComparison]::OrdinalIgnoreCase)) {
                    $expected[$relative] = $true
                    break
                }
            }
        }
    }
    $required = @(
        'FFRS/Content/Datatable/Skill/Other/DT_SkillLinkSequencerData.uasset',
        'FFRS/Content/Datatable/Skill/Other/DT_SkillGeneralData.uasset',
        'FFRS/Content/Datatable/Skill/Other/DT_SkillTargetData.uasset',
        'FFRS/Content/Datatable/Battle/Misc/DT_BtlSkillReactionParamDef.uasset',
        'FFRS/Content/Datatable/Asset/Battle/Unit/DT_BtlUnitAsset.uasset',
        'FFRS/Content/Datatable/Sequencer/DT_BattleSequencerUnitAnimationData.uasset',
        'FFRS/Content/Sequencer/Skill/BP/BP_BtlSequenceEvent.uasset',
        'FFRS/Content/Sequencer/Skill/BP/BP_BtlLevelSequenceDirector.uasset',
        'FFRS/Content/Sequencer/Battle/EnemySkill/500910/500912/SEQ_Battle_500912_Master.uasset',
        'FFRS/Content/Effect/03_SKL/skl500970/NS_EF_SKL500970_Gas_001_Weapon_AtoB.uasset'
    )
    $missing = @(@($required) + @($expected.Keys) | Sort-Object -Unique | Where-Object { -not $found.ContainsKey($_) })
    $status = 'Collected'
    if ($errors.Count -gt 0 -or $missing.Count -gt 0 -or -not $mapping -or $expected.Count -eq 0) {
        $status = 'Partial - upload the ZIPs and log for inspection'
    }
    [ordered]@{
        schema = 2
        scope = 'Complete native battle references: routing/callers/timelines, effects/materials/textures, battle character projects, cue metadata, engine and SpriteStudio/Niagara support'
        purpose = 'Trace missing direct skill routes before authoring any new timeline'
        status = $status; assetCount = $assets.Count; inventoryAssetCount = $expected.Count; mappingsFound = [bool]$mapping
        enginePath = $engine; gamePaksPath = $paks
        failedFilters = @($errors); missingReferences = @($missing); filters = @($filters)
        splitFilesLedger = 'split-files.json'; uploadPartLimitBytes = 22MB
        note = 'Read-only native collection. No loader or runtime mod is installed. Game and Studio files are not modified. Large files are streamed into numbered chunks with a length/SHA256 ledger; all ZIP parts are required.'
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $runRoot 'collection.json') -Encoding UTF8
    $files = @(Get-ChildItem -LiteralPath $runRoot -Recurse -File)
    $files | ForEach-Object {
        [PSCustomObject]@{ path = $_.FullName.Substring($runRoot.Length).TrimStart('\', '/'); bytes = $_.Length }
    } | Export-Csv -LiteralPath (Join-Path $runRoot 'files.csv') -NoTypeInformation -Encoding UTF8

    # Large assets must not abort a comprehensive collection. Each ordinary ZIP
    # stays below 22 MiB before compression. Oversized files are streamed in
    # 16 MiB entries with a restoration ledger, without duplicating them on disk.
    $allFiles = @(Get-ChildItem -LiteralPath $runRoot -Recurse -File | Sort-Object FullName)
    $segments = New-Object 'System.Collections.Generic.List[object]'
    $splitFiles = New-Object 'System.Collections.Generic.List[object]'
    $fileIndex = 0
    foreach ($file in $allFiles) {
        $relative = $file.FullName.Substring($runRoot.Length).TrimStart('\', '/').Replace('\', '/')
        if ($file.Length -le 22MB) {
            $segments.Add([PSCustomObject]@{ source = $file.FullName; entry = $relative; offset = 0L; bytes = $file.Length })
            continue
        }
        $fileIndex++; $offset = 0L; $chunk = 0
        $parts = New-Object 'System.Collections.Generic.List[object]'
        while ($offset -lt $file.Length) {
            $chunk++
            $count = [long][Math]::Min(16MB, $file.Length - $offset)
            $entryName = '_reference_chunks/' + $fileIndex.ToString('000000') + '/' + $chunk.ToString('000000') + '.bin'
            $segments.Add([PSCustomObject]@{ source = $file.FullName; entry = $entryName; offset = $offset; bytes = $count })
            $parts.Add([PSCustomObject]@{ path = $entryName; bytes = $count })
            $offset += $count
        }
        $splitFiles.Add([PSCustomObject]@{
            path = $relative; bytes = $file.Length
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            parts = @($parts.ToArray())
        })
    }
    $ledgerPath = Join-Path $runRoot 'split-files.json'
    [ordered]@{
        schema = 1; files = @($splitFiles.ToArray())
        note = 'Extract ALL ZIPs together. The project restore_reference_chunks.py utility restores large files from these ordered entries and checks their original length/SHA256. No restoration is needed on the collecting PC.'
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ledgerPath -Encoding UTF8
    $ledger = Get-Item -LiteralPath $ledgerPath
    if ($ledger.Length -gt 22MB) { throw 'The split-file ledger exceeds the upload size limit. Extracted files were kept.' }
    $segments.Add([PSCustomObject]@{ source = $ledgerPath; entry = 'split-files.json'; offset = 0L; bytes = $ledger.Length })
    $batch = @(); $batchBytes = 0L; $part = 1
    foreach ($segment in $segments) {
        if ($batch.Count -gt 0 -and $batchBytes + $segment.bytes -gt 22MB) {
            $destination = Join-Path $OutputRoot ($tag + '-' + $part.ToString('000') + '.zip')
            New-UploadZip $destination $batch
            $part++; $batch = @(); $batchBytes = 0L
        }
        $batch += $segment; $batchBytes += $segment.bytes
    }
    if ($batch.Count -gt 0) {
        $destination = Join-Path $OutputRoot ($tag + '-' + $part.ToString('000') + '.zip')
        New-UploadZip $destination $batch
    }
    Write-Host ''
    Write-Host ($status + ': ' + $assets.Count + ' assets.') -ForegroundColor Green
    Write-Host ('Upload ALL ' + $tag + '-*.zip files from:')
    Write-Host $OutputRoot -ForegroundColor Cyan
    if ($status -ne 'Collected') { Write-Host 'Some references are missing. The report in the ZIPs records which ones.' -ForegroundColor Yellow }
    exit 0
} catch {
    $message = 'ERROR: ' + $_.Exception.Message
    Write-Host $message -ForegroundColor Red
    if ($script:logFile) { Add-Content -LiteralPath $script:logFile -Value $message -Encoding UTF8 }
    exit 1
}
