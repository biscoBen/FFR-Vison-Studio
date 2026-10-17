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

function New-UploadZip([string]$Destination, [object[]]$Files, [string]$Root) {
    $stream = [System.IO.File]::Open($Destination, [System.IO.FileMode]::CreateNew)
    $archive = $null
    try {
        $archive = New-Object System.IO.Compression.ZipArchive -ArgumentList @(
            $stream, [System.IO.Compression.ZipArchiveMode]::Create, $true)
        foreach ($file in $Files) {
            $entryName = $file.FullName.Substring($Root.Length).TrimStart('\', '/').Replace('\', '/')
            [void][System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                $archive, $file.FullName, $entryName, [System.IO.Compression.CompressionLevel]::Optimal)
        }
    } finally {
        if ($null -ne $archive) { $archive.Dispose() }
        $stream.Dispose()
    }
}

try {
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    Write-Host 'Collect skill effect and installed-route references' -ForegroundColor Cyan
    Write-Host 'This reads the game and writes reference files under Downloads\FFR Mod.'
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
    $tag = 'Skill-Effect-Reference-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 6)
    $runRoot = Join-Path $OutputRoot $tag
    [void][System.IO.Directory]::CreateDirectory($runRoot)
    $assetRoot = Join-Path $runRoot 'legacy'
    [void][System.IO.Directory]::CreateDirectory($assetRoot)
    $script:logFile = Join-Path $runRoot 'extraction.log'
    $retoc = Join-Path $engine 'tools\retoc\retoc.exe'

    $errors = @(); $extractions = @(); $installedFiles = @()
    function Read-Inventory([string]$Container, [string]$Destination) {
        $previousPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            & $retoc list --path $Container 2>&1 | Out-File -LiteralPath $Destination -Encoding UTF8
            $code = $LASTEXITCODE
        } finally { $ErrorActionPreference = $previousPreference }
        if ($code -ne 0) { throw ('Cannot list containers: ' + $Container + ' (exit ' + $code + ')') }
        return (Get-Content -LiteralPath $Destination -Raw -Encoding UTF8)
    }
    function Extract-Reference([string]$Container, [string]$Filter, [string]$Destination, [string]$Scope) {
        $label = $Scope + ': ' + $Filter
        Write-Host $label -ForegroundColor Cyan
        Add-Content -LiteralPath $script:logFile -Value $label -Encoding UTF8
        $reportedFailure = $false
        $previousPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            & $retoc to-legacy --no-shaders --filter $Filter $Container $Destination 2>&1 |
                ForEach-Object {
                    $line = $_.ToString()
                    if ($line -match '\(([1-9][0-9]*) failed\)' -or $line -match 'Extracted 0 \(') {
                        $reportedFailure = $true
                    }
                    Write-Host $line
                    Add-Content -LiteralPath $script:logFile -Value $line -Encoding UTF8
                }
            $code = $LASTEXITCODE
        } finally { $ErrorActionPreference = $previousPreference }
        return [pscustomobject]@{scope=$Scope; filter=$Filter; exitCode=$code; reportedFailure=$reportedFailure}
    }

    # The earlier reference already contains every native timeline. This collects
    # actual effect systems/meshes and installed routes, not the entire mod pack.
    $inventory = Join-Path $runRoot 'game-asset-index.txt'
    $nativeIndex = ''
    try { $nativeIndex = Read-Inventory $paks $inventory }
    catch { $errors += 'Native inventory: ' + $_.Exception.Message }
    # A standalone mod .utoc lacks the game's ScriptObjects chunk. A temporary
    # read-only view combines only that pack and the native global index. Use
    # hard links on the same volume, with copies when Downloads is on another
    # drive. Always remove this view before making upload ZIPs.
    $globalNames = @([regex]::Matches($nativeIndex,
        '(?m)^([A-Za-z0-9_.-]+)\s+\S+\s+(?:ScriptObjects|LoaderInitialLoadMeta|LoaderGlobalNames|LoaderGlobalNameHashes)\s') |
        ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique)
    function Stage-Container([string]$Source, [string]$View) {
        $base = [System.IO.Path]::GetFileNameWithoutExtension($Source)
        $parent = [System.IO.Path]::GetDirectoryName($Source)
        $files = @((Get-Item -LiteralPath $Source))
        $files += @(Get-ChildItem -LiteralPath $parent -Filter ($base + '*.ucas') -File |
            Where-Object { $_.BaseName -eq $base -or $_.BaseName -match ('^' + [regex]::Escape($base) + '_s[0-9]+$') })
        if ($files.Count -lt 2) { throw ('Missing container data beside ' + $Source) }
        foreach ($file in $files) {
            $destination = Join-Path $View $file.Name
            try { New-Item -ItemType HardLink -Path $destination -Value $file.FullName -ErrorAction Stop | Out-Null }
            catch { [System.IO.File]::Copy($file.FullName, $destination, $false) }
        }
    }
    $tables = @(
        'Datatable/Asset/Skill/DT_SkillAsset.uasset',
        'Datatable/Asset/Skill/CDT_SkillAsset_Demo.uasset',
        'Datatable/Skill/DT_SkillData.uasset',
        'Datatable/Skill/DT_SkillEffectData.uasset',
        'Datatable/Battle/Sequencer/DT_BtlHitEffectData.uasset',
        'Datatable/Battle/Sequencer/DT_BtlSkillLoadUnitData.uasset',
        'Datatable/Battle/Sequencer/DT_BtlSkillPointTargetData.uasset'
    )
    # Include matching effects for the whole reported batch. Absence is recorded
    # as absence of this folder, not proof that a skill has no aliased effect.
    $skillIds = @(220050, 500270, 505110, 500230, 402050, 505840, 408040, 503770,
        405050, 500800, 405130, 414410, 503630, 503620, 503610, 501180, 500380, 505020, 500970)
    $effectFolders = @(); $filters = @($tables)
    foreach ($sid in $skillIds) {
        $filter = 'Effect/03_SKL/skl' + $sid + '/'
        $present = $nativeIndex.IndexOf($filter, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
        $effectFolders += [pscustomobject]@{skillId=$sid; folder=$filter; presentInInventory=$present}
        if ($present) { $filters += $filter }
    }
    foreach ($filter in $filters) {
        $result = Extract-Reference $paks $filter $assetRoot 'native'
        $extractions += $result
        if ($result.exitCode -ne 0 -or $result.reportedFailure) { $errors += 'native: ' + $filter }
    }

    # Enumerate only top-level Studio containers, never unrelated mods. Include
    # older names of our own pack too, so duplicate installations are visible.
    $mods = Join-Path $paks '~mods'
    $packs = @()
    if (Test-Path -LiteralPath $mods -PathType Container) {
        $packs = @(Get-ChildItem -LiteralPath $mods -Filter '*EstherTsukiko*.utoc' -File | Sort-Object Name)
    }
    if ($packs.Count -eq 0) { $errors += 'No installed Studio .utoc found in ~mods.' }
    foreach ($pack in $packs) {
        $installed = Join-Path (Join-Path $runRoot 'installed') $pack.BaseName
        [void][System.IO.Directory]::CreateDirectory($installed)
        foreach ($extension in @('.utoc', '.ucas', '.pak')) {
            $path = [System.IO.Path]::ChangeExtension($pack.FullName, $extension)
            $record = [ordered]@{name=[System.IO.Path]::GetFileName($path); exists=(Test-Path -LiteralPath $path -PathType Leaf)}
            if ($record.exists) {
                $item = Get-Item -LiteralPath $path
                $record['bytes'] = $item.Length; $record['modifiedUtc'] = $item.LastWriteTimeUtc.ToString('o')
                if ($extension -eq '.utoc') { $record['sha256'] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
            }
            $installedFiles += [pscustomobject]$record
        }
        $view = Join-Path (Join-Path $runRoot '_temporary-containers') $pack.BaseName
        try {
            $index = Read-Inventory $pack.FullName (Join-Path $installed 'asset-index.txt')
            if (-not $globalNames.Count) { throw 'Native global script-object container was not identified; installed extraction was skipped.' }
            [void][System.IO.Directory]::CreateDirectory($view)
            foreach ($globalName in $globalNames) { Stage-Container (Join-Path $paks ($globalName + '.utoc')) $view }
            Stage-Container $pack.FullName $view
            foreach ($filter in @($tables) + @('Sequencer/Battle/')) {
                if ($index.IndexOf($filter, [System.StringComparison]::OrdinalIgnoreCase) -lt 0) { continue }
                $result = Extract-Reference $view $filter (Join-Path $installed 'legacy') $pack.BaseName
                $extractions += $result
                if ($result.exitCode -ne 0 -or $result.reportedFailure) { $errors += $pack.BaseName + ': ' + $filter }
            }
        } catch { $errors += $pack.BaseName + ': ' + $_.Exception.Message }
        finally { if (Test-Path -LiteralPath $view) { Remove-Item -LiteralPath $view -Recurse -Force } }
    }

    $mapping = $null
    foreach ($relative in @('extracted\Mappings.usmap', 'data\Mappings.usmap')) {
        $candidate = Join-Path $engine $relative
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { $mapping = $candidate; break }
    }
    if ($mapping) { Copy-Item -LiteralPath $mapping -Destination (Join-Path $runRoot 'Mappings.usmap') }

    # Only the animation mode flags, not private sync settings or credentials.
    $modePath = Join-Path $engine 'mods\EstherTsukiko\ability-modes.json'
    if (Test-Path -LiteralPath $modePath -PathType Leaf) {
        $modes = Get-Content -LiteralPath $modePath -Raw -Encoding UTF8 | ConvertFrom-Json
        $selected = [ordered]@{}
        foreach ($name in @('schema', 'showUnverified', 'useChanges', 'useNativeRepairs')) {
            $property = $modes.PSObject.Properties[$name]
            if ($null -ne $property) { $selected[$name] = $property.Value }
        }
        $selected | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runRoot 'ability-modes.json') -Encoding UTF8
    }
    $repairReport = Join-Path $engine 'build\animation-repair-report.json'
    if (Test-Path -LiteralPath $repairReport -PathType Leaf) {
        Copy-Item -LiteralPath $repairReport -Destination (Join-Path $runRoot 'animation-repair-report.json')
    }
    $unitsPath = Join-Path $engine 'mods\EstherTsukiko\units.json'
    if (Test-Path -LiteralPath $unitsPath -PathType Leaf) {
        # PowerShell 5.1 writes a JSON array as one pipeline object. Assign
        # first, then enumerate, so even empty/single-entry rosters stay flat.
        $decoded = Get-Content -LiteralPath $unitsPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $units = @($decoded)
        $selected = @()
        foreach ($unit in $units) {
            $row = [ordered]@{}
            foreach ($name in @('id', 'key', 'en', 'party', 'ffbe', 'awakening', 'synchro', 'skills', 'lb', 'lb_custom')) {
                $property = $unit.PSObject.Properties[$name]
                if ($null -ne $property) { $row[$name] = $property.Value }
            }
            $selected += [pscustomobject]$row
        }
        ConvertTo-Json -InputObject @($selected) -Depth 40 |
            Set-Content -LiteralPath (Join-Path $runRoot 'selected-skill-grants.json') -Encoding UTF8
    }
    $assets = @(Get-ChildItem -LiteralPath $assetRoot -Recurse -Filter '*.uasset' -File)
    $status = 'Collected'
    if ($errors.Count -gt 0 -or -not $mapping -or $assets.Count -eq 0) { $status = 'Partial - upload the ZIPs and log for inspection' }
    [ordered]@{
        schema = 1; scope = 'Native skill effect packages, skill tables, installed Studio battle timelines and routing'
        purpose = 'Inspect Absolute Zero, Aqua Breath and Bioblaster placement; distinguish missing routes from missing effects'
        engine = $engine; game = $gameRoot
        status = $status; nativeAssetCount = $assets.Count; mappingsFound = [bool]$mapping
        installedPacks = @($packs | ForEach-Object { $_.Name }); installedFiles = @($installedFiles)
        nativeScriptObjectContainers = @($globalNames)
        failedFilters = @($errors); extractions = @($extractions); effectFolders = @($effectFolders)
        note = 'Read-only static collection. No runtime trace or fixes are installed. Saves, sync settings and credentials are excluded.'
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $runRoot 'collection.json') -Encoding UTF8
    $files = @(Get-ChildItem -LiteralPath $runRoot -Recurse -File)
    $files | ForEach-Object {
        [PSCustomObject]@{ path = $_.FullName.Substring($runRoot.Length).TrimStart('\', '/'); bytes = $_.Length }
    } | Export-Csv -LiteralPath (Join-Path $runRoot 'files.csv') -NoTypeInformation -Encoding UTF8

    # Separate, ordinary ZIPs, not byte-split ZIP fragments. Leave headroom under
    # the upload limit by limiting each batch to 22 MiB before compression.
    $allFiles = @(Get-ChildItem -LiteralPath $runRoot -Recurse -File | Sort-Object FullName)
    $batch = @(); $batchBytes = 0L; $part = 1
    foreach ($file in $allFiles) {
        if ($file.Length -gt 22MB) { throw ('Unexpected large file: ' + $file.FullName + '. Reference files were kept, but ZIP creation stopped.') }
        if ($batch.Count -gt 0 -and $batchBytes + $file.Length -gt 22MB) {
            $destination = Join-Path $OutputRoot ($tag + '-' + $part.ToString('000') + '.zip')
            New-UploadZip $destination $batch $runRoot
            $part++; $batch = @(); $batchBytes = 0L
        }
        $batch += $file; $batchBytes += $file.Length
    }
    if ($batch.Count -gt 0) {
        $destination = Join-Path $OutputRoot ($tag + '-' + $part.ToString('000') + '.zip')
        New-UploadZip $destination $batch $runRoot
    }
    Write-Host ''
    Write-Host ($status + ': ' + $assets.Count + ' native assets and installed routing references.') -ForegroundColor Green
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
