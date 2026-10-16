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
    Write-Host 'Collect party battle knockout references' -ForegroundColor Cyan
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
    $tag = 'Party-Knockout-Reference-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 6)
    $runRoot = Join-Path $OutputRoot $tag
    [void][System.IO.Directory]::CreateDirectory($runRoot)
    $assetRoot = Join-Path $runRoot 'legacy'
    [void][System.IO.Directory]::CreateDirectory($assetRoot)
    $script:logFile = Join-Path $runRoot 'extraction.log'
    $retoc = Join-Path $engine 'tools\retoc\retoc.exe'

    # Exact native battle package names from the demo's supplied asset index.
    # The .uasset suffix excludes the much larger texture packages. retoc also
    # writes each selected package's .uexp / .ubulk companions when present.
    $filters = @('Datatable/Asset/Battle/Unit/DT_BtlUnitAsset.uasset')
    for ($number = 1; $number -le 8; $number++) {
        $name = 'unit' + ($number * 10).ToString('0000')
        $filters += 'Chara/Unit/' + $name + '/' + $name + '.uasset'
    }
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

    $mapping = $null
    foreach ($relative in @('extracted\Mappings.usmap', 'data\Mappings.usmap')) {
        $candidate = Join-Path $engine $relative
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { $mapping = $candidate; break }
    }
    if ($mapping) { Copy-Item -LiteralPath $mapping -Destination (Join-Path $runRoot 'Mappings.usmap') }

    # Keep only party overrides from Studio, not its general settings, tokens
    # or unrelated visions. Include generated motion specs and the current
    # Lasswell sprite inputs to reproduce the reported Cleome replacement.
    $party = @(); $extraMissing = @()
    $specPath = Join-Path $engine 'mods\EstherTsukiko\units.json'
    if (Test-Path -LiteralPath $specPath -PathType Leaf) {
        $saved = @(Get-Content -LiteralPath $specPath -Raw -Encoding UTF8 | ConvertFrom-Json)
        $party = @($saved | Where-Object { $null -ne $_.PSObject.Properties['party'] -and $null -ne $_.party })
        ConvertTo-Json -InputObject @($party) -Depth 60 |
            Set-Content -LiteralPath (Join-Path $runRoot 'party-overrides.json') -Encoding UTF8
    } else { $extraMissing += 'Studio units.json not found' }
    $enginePrefix = $engine.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    foreach ($unit in $party) {
        $id = [int]$unit.id
        if ($id -lt 1001 -or $id -gt 1008) { continue }
        $key = [string]$unit.key
        if ($key -ne ('party_' + $id)) { continue }
        $generated = Join-Path $engine ('build\sprites\' + $key + '\battle\spec.json')
        if (Test-Path -LiteralPath $generated -PathType Leaf) {
            $dest = Join-Path $runRoot ('generated\' + $key + '\spec.json')
            [void][System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($dest))
            Copy-Item -LiteralPath $generated -Destination $dest
        } elseif ($null -ne $unit.PSObject.Properties['ffbe']) {
            $extraMissing += $key + ' generated spec.json missing (rebuild the mod first)'
        }
        if ($id -ne 1002 -or $null -eq $unit.PSObject.Properties['ffbe']) { continue }
        $ffbe = $unit.ffbe
        foreach ($pair in @(@('dir', 'id'), @('baseDir', 'baseForm'))) {
            $directoryProperty = $ffbe.PSObject.Properties[$pair[0]]
            $formProperty = $ffbe.PSObject.Properties[$pair[1]]
            if ($null -eq $directoryProperty -or $null -eq $formProperty) { continue }
            $form = [string]$formProperty.Value
            if ($form -notmatch '^[0-9]+$') { continue }
            $folder = [System.IO.Path]::GetFullPath((Join-Path $engine ([string]$directoryProperty.Value)))
            if (-not $folder.StartsWith($enginePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
                $extraMissing += 'Skipped source folder outside Studio engine'; continue
            }
            foreach ($motion in @('anime', 'cgg', 'idle_cgs', 'dying_cgs', 'dead_cgs')) {
                $name = 'unit_' + $motion + '_' + $form + $(if ($motion -eq 'anime') { '.png' } else { '.csv' })
                $path = Join-Path $folder $name
                if (Test-Path -LiteralPath $path -PathType Leaf) {
                    $dest = Join-Path $runRoot ('replacement-inputs\' + $form + '\' + $name)
                    [void][System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($dest))
                    Copy-Item -LiteralPath $path -Destination $dest
                }
            }
        }
    }
    $files = @(Get-ChildItem -LiteralPath $assetRoot -Recurse -File)
    $assets = @($files | Where-Object { $_.Extension -in @('.umap', '.uasset') })
    if ($assets.Count -eq 0) { throw ('No assets were extracted. See ' + $script:logFile) }
    $native = @($assets | Where-Object { $_.Name -match '^unit00[1-8]0\.uasset$' })
    $status = 'Collected'
    if ($errors.Count -gt 0 -or $native.Count -ne 8 -or -not $mapping -or $extraMissing.Count -gt 0) {
        $status = 'Partial - upload the ZIPs and log for inspection'
    }
    [ordered]@{
        schema = 1; purpose = 'Check native party knockout motion names against FFBE replacement clips'
        status = $status; nativePartyModels = $native.Count; mappingsFound = [bool]$mapping
        failedFilters = @($errors); missingReferences = @($extraMissing); filters = @($filters)
        note = 'Read-only collection. No loader or runtime mod is installed. Game and Studio files are not modified.'
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $runRoot 'collection.json') -Encoding UTF8
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
