# Compatible with Windows PowerShell 5.1. Only the output folder is written.
[CmdletBinding()]
param([string]$EnginePath, [string]$GamePath, [string]$OutputRoot)

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
    Write-Host 'Collect Crystal Fina battle attachment references' -ForegroundColor Cyan
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
        $entered = Read-Host $prompt
        if ($entered) { $engine = Find-Engine $entered }
        if (-not $engine) { throw 'Could not find the engine. Select the Studio folder containing Studio Test Data, or its engine folder.' }
    }

    $paks = Find-Paks $GamePath
    if (-not $paks -and $GamePath) { throw 'The supplied game folder does not contain .utoc files in FFRS\Content\Paks.' }
    if (-not $paks) {
        $configFile = Join-Path $engine 'config.json'
        if (Test-Path -LiteralPath $configFile -PathType Leaf) {
            try {
                $config = Get-Content -LiteralPath $configFile -Raw | ConvertFrom-Json
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
        $entered = Read-Host $prompt
        if ($entered) { $paks = Find-Paks $entered }
        if (-not $paks) { throw 'Could not find game containers. Enter the folder containing FFRS, or the Paks folder itself.' }
    }

    if (-not $OutputRoot) { $OutputRoot = Join-Path $env:USERPROFILE 'Downloads\FFR Mod' }
    [void][System.IO.Directory]::CreateDirectory($OutputRoot)
    $OutputRoot = (Resolve-Path -LiteralPath $OutputRoot).Path
    $tag = 'Crystal-Fina-Battle-Reference-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 6)
    $runRoot = Join-Path $OutputRoot $tag
    [void][System.IO.Directory]::CreateDirectory($runRoot)
    $assetRoot = Join-Path $runRoot 'legacy'
    [void][System.IO.Directory]::CreateDirectory($assetRoot)
    $script:logFile = Join-Path $runRoot 'extraction.log'
    $retoc = Join-Path $engine 'tools\retoc\retoc.exe'

    # The unit table/FFBE shell paths are confirmed by the current builder.
    # Blueprint/effect filters are reference searches; empty results are logged.
    $filters = @(
        'Datatable/Asset/Battle/Unit/',
        'Datatable/Battle/Sequencer/',
        'Datatable/Skill/DT_SkillData',
        'Sequencer/Battle/Attack/',
        'Datatable/Asset/Skill/DT_SkillAsset',
        'Sequencer/Battle/Skill/440110/',
        'Sequencer/Battle/Skill/440280/',
        'BP/Battle/',
        'BP_BtlUnit',
        'BP/Unit/',
        'Effect/07_EV/CMN/FinaCristal',
        'Chara/Field_Unit/pc0030/'
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

    $mapping = $null
    foreach ($relative in @('extracted\Mappings.usmap', 'data\Mappings.usmap')) {
        $candidate = Join-Path $engine $relative
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { $mapping = $candidate; break }
    }
    if ($mapping) { Copy-Item -LiteralPath $mapping -Destination (Join-Path $runRoot 'Mappings.usmap') }

    $files = @(Get-ChildItem -LiteralPath $assetRoot -Recurse -File)
    $assets = @($files | Where-Object { $_.Extension -in @('.umap', '.uasset') })
    if ($assets.Count -eq 0) { throw ('No assets were extracted. See ' + $script:logFile) }
    $hasUnit = @($assets | Where-Object { $_.Name -eq 'DT_BtlUnitAsset.uasset' }).Count -gt 0
    $hasEffects = @($assets | Where-Object { $_.Name -match 'Btl.*Unit.*Effect' }).Count -gt 0
    $status = 'Collected'
    if ($errors.Count -gt 0 -or -not $hasUnit -or -not $hasEffects -or -not $mapping) { $status = 'Partial - upload the ZIPs and log for inspection' }
    [ordered]@{
        schema = 1; purpose = 'Trace battle vision effect attachments and crystal/glow lifecycle'
        status = $status; assetCount = $assets.Count; battleUnitTableFound = $hasUnit
        battleUnitEffectsFound = $hasEffects; mappingsFound = [bool]$mapping
        failedFilters = @($errors); filters = @($filters)
        note = 'Read-only collection. Blueprint/effect filter names are leads; missing filters are recorded. No runtime loader or mod is installed. Inspect native unit effects and animation attachment behavior before changing battle visuals.'
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $runRoot 'collection.json') -Encoding UTF8
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
