# Windows PowerShell 5.1. Read-only movie playback collection; no installation or game changes.
[CmdletBinding()]
param([string]$GamePath, [string]$EnginePath, [string]$OutputRoot, [switch]$NoPrompt,
      [switch]$PlayerReference, [switch]$CaveMusic)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

function Find-Game([string]$Candidate) {
    if (-not $Candidate) { return $null }
    $Candidate = $Candidate.Trim().Trim('"')
    foreach ($suffix in @('', '..\..\..')) {
        $path = $Candidate
        if ($suffix) { $path = Join-Path $Candidate $suffix }
        if (Test-Path -LiteralPath (Join-Path $path 'FFRS\Binaries\Win64') -PathType Container) {
            # Match output normalization even when TEMP uses an 8.3 alias.
            $resolved = [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $path).Path)
            if ((Split-Path -Leaf $resolved) -match '(?i)\bDEMO\b') { return $null }
            return $resolved
        }
    }
    return $null
}
function Get-SteamGames {
    $roots = @()
    foreach ($key in @('HKCU:\Software\Valve\Steam', 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam')) {
        $entry = Get-ItemProperty -LiteralPath $key -ErrorAction SilentlyContinue
        if ($entry) {
            foreach ($name in @('SteamPath', 'InstallPath')) {
                $property = $entry.PSObject.Properties[$name]
                if ($null -ne $property -and $property.Value) { $roots += [string]$property.Value }
            }
        }
    }
    if (${env:ProgramFiles(x86)}) { $roots += Join-Path ${env:ProgramFiles(x86)} 'Steam' }
    foreach ($drive in @('G', 'D', 'C', 'E', 'F')) { $roots += $drive + ':\Steam' }
    foreach ($root in @($roots | Select-Object -Unique)) {
        if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
        $libraries = @($root)
        $vdf = Join-Path $root 'steamapps\libraryfolders.vdf'
        if (Test-Path -LiteralPath $vdf -PathType Leaf) {
            $text = Get-Content -LiteralPath $vdf -Raw
            foreach ($match in [regex]::Matches($text, '"(?:path|\d+)"\s+"([^"\r\n]+)"')) {
                $libraries += $match.Groups[1].Value.Replace('\\', '\')
            }
        }
        foreach ($library in @($libraries | Select-Object -Unique)) {
            Join-Path $library 'steamapps\common\FINAL FANTASY RESONANCE'
        }
    }
}
function Get-InstallKey([string]$Game) {
    $key = [System.IO.Path]::GetFullPath($Game)
    if ([System.IO.Path]::DirectorySeparatorChar -eq '\') { $key = $key.Replace('/', '\').ToLowerInvariant() }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($key)))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
function Find-Engine([string]$Candidate) {
    if (-not $Candidate) { return $null }
    foreach ($suffix in @('', 'engine', 'Studio Test Data\FFR Vision Studio\engine')) {
        $path = $Candidate.Trim().Trim('"')
        if ($suffix) { $path = Join-Path $path $suffix }
        if (Test-Path -LiteralPath (Join-Path $path 'tools\make_vision_mod.py') -PathType Leaf) {
            return (Resolve-Path -LiteralPath $path).Path
        }
    }
    return $null
}
function Copy-Shared([string]$Source, [string]$Destination) {
    $inputStream = $null; $outputStream = $null
    try {
        $share = [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
        $inputStream = [System.IO.File]::Open($Source, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, $share)
        [void][System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($Destination))
        $outputStream = [System.IO.File]::Create($Destination)
        $inputStream.CopyTo($outputStream)
    } finally {
        if ($outputStream) { $outputStream.Dispose() }
        if ($inputStream) { $inputStream.Dispose() }
    }
}

# Stream binary stdout directly. PowerShell's ordinary native-command redirect
# converts bytes to text on Windows PowerShell 5.1 and would corrupt a USM.
function Quote-Argument([string]$Value) {
    return '"' + ([regex]::Replace([regex]::Replace($Value, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1')) + '"'
}

function Collect-PlayerReference([string]$Engine, [string]$Game) {
    # Read the native display/player assets from the complete container directory:
    # retoc needs global.utoc there to resolve script objects. Never extract into
    # the game or Studio, and never run a builder or modify installed packages.
    $retoc = Join-Path $Engine 'tools/retoc/retoc.exe'
    if (-not (Test-Path -LiteralPath $retoc -PathType Leaf)) {
        throw 'Studio retoc reader was not found: ' + $retoc
    }
    $paks = Join-Path $Game 'FFRS/Content/Paks'
    $legacy = Join-Path $script:root 'native/legacy'
    [void][IO.Directory]::CreateDirectory($legacy)
    $attempts = New-Object 'Collections.Generic.List[object]'
    $filters = @('Movies/Sequencer/', 'Sequencer/Battle/Skill/440110/440111/')
    foreach ($filter in $filters) {
        Write-Host ('Reading native movie player: ' + $filter) -ForegroundColor Cyan
        $process = New-Object Diagnostics.Process
        $process.StartInfo = New-Object Diagnostics.ProcessStartInfo
        $process.StartInfo.FileName = $retoc
        $process.StartInfo.Arguments = (@('to-legacy', '--no-shaders', '--filter', $filter, $paks, $legacy) |
            ForEach-Object { Quote-Argument $_ }) -join ' '
        $process.StartInfo.UseShellExecute = $false
        $process.StartInfo.CreateNoWindow = $true
        $process.StartInfo.RedirectStandardOutput = $true
        $process.StartInfo.RedirectStandardError = $true
        $started = $false
        $record = [ordered]@{filter=$filter; timeoutSeconds=60}
        try {
            $started = $process.Start()
            $stdout = $process.StandardOutput.ReadToEndAsync()
            $stderr = $process.StandardError.ReadToEndAsync()
            $watch = [Diagnostics.Stopwatch]::StartNew()
            while (-not $process.WaitForExit(250)) {
                if ($watch.Elapsed.TotalSeconds -gt 60) { throw 'Native extraction timed out after 60 seconds.' }
            }
            $message = $stdout.GetAwaiter().GetResult() + $stderr.GetAwaiter().GetResult()
            $record['exitCode'] = $process.ExitCode
            $record['log'] = $message
            Write-Host $message
            if ($process.ExitCode -ne 0 -or $message -match '\([1-9][0-9]* failed\)') {
                $script:errors.Add('Native player extraction failed for ' + $filter + '; see extraction report.')
            }
        } catch {
            $record['error'] = $_.Exception.Message
            $script:errors.Add($filter + ': ' + $_.Exception.Message)
        } finally {
            if ($started -and -not $process.HasExited) { $process.Kill(); [void]$process.WaitForExit(5000) }
            $process.Dispose()
        }
        $attempts.Add([pscustomobject]$record)
    }
    $expected = @('Movies/Sequencer/BP_BtlSequencerMovieActor', 'Movies/Sequencer/MP_BtlManaPlayer',
                  'Movies/Sequencer/MSB_BtlSequencer_Texture', 'Movies/Sequencer/MSB_BtlSequencer_Texture_Mat',
                  'Sequencer/Battle/Skill/440110/440111/SEQ_Battle_440111_Master',
                  'Sequencer/Battle/Skill/440110/440111/Track/SEQ_Battle_440111_Cut_000')
    foreach ($stem in $expected) {
        if (-not (Test-Path -LiteralPath (Join-Path $legacy ('FFRS/Content/' + $stem + '.uasset')) -PathType Leaf)) {
            $script:errors.Add('Missing native player reference: ' + $stem)
        }
    }
    foreach ($relative in @('extracted/Mappings.usmap', 'data/Mappings.usmap')) {
        $candidate = Join-Path $Engine $relative
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            Copy-Shared $candidate (Join-Path $script:root 'native/Mappings.usmap')
            break
        }
    }
    $files = @(Get-ChildItem -LiteralPath $legacy -Recurse -File | ForEach-Object {
        [pscustomobject]@{path=$_.FullName.Substring($legacy.Length + 1).Replace('\', '/');
            bytes=$_.Length; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
    })
    [pscustomobject]@{schema=1; purpose='native-movie-player'; gameEdition='full';
        collectedUtc=[DateTime]::UtcNow.ToString('o'); game=$Game; engine=$Engine;
        extraction=$attempts.ToArray(); files=$files; errors=$script:errors.ToArray()} |
        ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $script:root 'report.json') -Encoding UTF8
    $zip = $script:root + '.zip'
    [IO.Compression.ZipFile]::CreateFromDirectory($script:root, $zip)
    Write-Host ('Attach this ZIP in the chat: ' + $zip) -ForegroundColor Green
    if ($script:errors.Count) { Write-Host 'Some assets were unavailable. Send the ZIP anyway; the report lists them.' -ForegroundColor Yellow }
    Write-Output $zip
}
function Export-PakEntry([string]$Tool, [string]$Pak, [string]$Entry, [string]$Destination) {
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = New-Object System.Diagnostics.ProcessStartInfo
    $process.StartInfo.FileName = $Tool
    $process.StartInfo.Arguments = (@('get', $Pak, $Entry) | ForEach-Object { Quote-Argument $_ }) -join ' '
    $process.StartInfo.UseShellExecute = $false
    $process.StartInfo.CreateNoWindow = $true
    $process.StartInfo.RedirectStandardOutput = $true
    $process.StartInfo.RedirectStandardError = $true
    $stream = $null; $started = $false; $truncated = $false; $bytes = 0
    try {
        [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Destination))
        $started = $process.Start()
        $stderr = $process.StandardError.ReadToEndAsync()
        $stream = [IO.File]::Create($Destination)
        $buffer = New-Object byte[] 65536
        $watch = [Diagnostics.Stopwatch]::StartNew()
        # A bounded prefix includes the CRI metadata and initial video packets.
        # It is enough to compare codec/container layout without a large movie export.
        $limit = 2MB
        while ($true) {
            $read = $process.StandardOutput.BaseStream.ReadAsync($buffer, 0, $buffer.Length)
            while (-not $read.Wait(250)) {
                if ($watch.Elapsed.TotalSeconds -gt 45) { throw 'Movie extraction timed out after 45 seconds.' }
            }
            $count = $read.Result
            if (-not $count) { break }
            $take = [Math]::Min($count, $limit - $bytes)
            if ($take) { $stream.Write($buffer, 0, $take); $bytes += $take }
            if ($count -gt $take) { $truncated = $true; break }
        }
        if ($truncated -and -not $process.HasExited) { $process.Kill() }
        if (-not $process.WaitForExit(5000)) { throw 'Movie extraction did not exit.' }
        $message = $stderr.GetAwaiter().GetResult()
        if (-not $truncated -and $process.ExitCode -ne 0) { throw ($message.Trim()) }
        if ($bytes -lt 4) { throw 'Movie was missing or empty.' }
        $stream.Dispose(); $stream = $null
        $signatureStream = [IO.File]::OpenRead($Destination)
        try { $signature = New-Object byte[] 4; [void]$signatureStream.Read($signature, 0, 4) }
        finally { $signatureStream.Dispose() }
        if ([Text.Encoding]::ASCII.GetString($signature) -ne 'CRID') { throw 'Movie does not begin with a CRI USM header.' }
        return [pscustomobject]@{pak=$Pak; entry=$Entry; capturedBytes=$bytes; prefixOnly=$truncated;
            sha256=(Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash}
    } catch {
        if ($stream) { $stream.Dispose(); $stream = $null }
        if (Test-Path -LiteralPath $Destination) { Remove-Item -LiteralPath $Destination }
        throw
    } finally {
        if ($stream) { $stream.Dispose() }
        if ($started -and -not $process.HasExited) { $process.Kill(); [void]$process.WaitForExit(5000) }
        $process.Dispose()
    }
}
function Collect-File([string]$Source, [string]$Relative, [switch]$HashOnly) {
    $record = [ordered]@{path=$Source; collectedAs=$Relative; exists=(Test-Path -LiteralPath $Source -PathType Leaf)}
    if ($record.exists) {
        try {
            $file = Get-Item -LiteralPath $Source
            $record['bytes'] = $file.Length
            $record['modifiedUtc'] = $file.LastWriteTimeUtc.ToString('o')
            if ($HashOnly) { $record['sha256'] = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash }
            elseif ($file.Length -le 4MB) { Copy-Shared $Source (Join-Path $script:root $Relative) }
            elseif ($file.Extension -eq '.log') {
                $inputStream = $null; $outputStream = $null
                try {
                    $inputStream = [IO.File]::Open($Source, 'Open', 'Read', ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
                    [void]$inputStream.Seek(-4MB, 'End')
                    $destination = Join-Path $script:root $Relative
                    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination))
                    $outputStream = [IO.File]::Create($destination); $inputStream.CopyTo($outputStream)
                } finally {
                    if ($outputStream) { $outputStream.Dispose() }
                    if ($inputStream) { $inputStream.Dispose() }
                }
                $record['tailOnly'] = $true
            } else { $record['omitted'] = 'Over 4 MiB; metadata only.' }
        } catch { $script:errors.Add($Source + ': ' + $_.Exception.Message) }
    }
    $script:records.Add([pscustomobject]$record)
}
function Read-MovieProfile([string]$Text, [string]$Source) {
    # Never export the numeric game decryption key or the rest of the config.
    $section = [regex]::Match($Text, '(?ms)^\[/Script/CriWareRuntime\.CriWarePluginSettings\]\s*$(.*?)(?=^\[|\z)')
    $profile = [ordered]@{source=$Source; sectionFound=$section.Success; options=[ordered]@{}}
    if ($section.Success) {
        foreach ($line in ($section.Groups[1].Value -split '\r?\n')) {
            $setting = [regex]::Match($line, '^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$')
            if (-not $setting.Success) { continue }
            $name = $setting.Groups[1].Value; $value = $setting.Groups[2].Value
            if ($name -eq 'DecryptKey') { $profile['keyConfigured'] = ($value -match '^\d+$' -and $value -ne '0'); continue }
            if ($name -match '(?i)key|token|password|credential') { continue }
            if ($name -match '(?i)mana|movie|video|decrypt' -and $value -match '^(?i:true|false|[0-9]+)$') {
                $profile.options[$name] = $value
            }
        }
    }
    return [pscustomobject]$profile
}
function Copy-MoviePrefix([string]$Source, [string]$Destination) {
    $inputStream = $null; $outputStream = $null
    try {
        $inputStream = [IO.File]::Open($Source, 'Open', 'Read', ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
        $signature = New-Object byte[] 4
        if ($inputStream.Read($signature, 0, 4) -ne 4 -or [Text.Encoding]::ASCII.GetString($signature) -ne 'CRID') {
            throw 'Original movie does not begin with a CRI USM header.'
        }
        $inputStream.Position = 0
        [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Destination))
        $outputStream = [IO.File]::Create($Destination)
        $buffer = New-Object byte[] 65536; $bytes = 0
        while ($bytes -lt 2MB) {
            $count = $inputStream.Read($buffer, 0, [Math]::Min($buffer.Length, 2MB - $bytes))
            if (-not $count) { break }
            $outputStream.Write($buffer, 0, $count); $bytes += $count
        }
        $outputStream.Dispose(); $outputStream = $null
        return [pscustomobject]@{file=$Source; capturedBytes=$bytes; prefixOnly=($inputStream.Length -gt $bytes);
            sha256=(Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash}
    } finally {
        if ($outputStream) { $outputStream.Dispose() }
        if ($inputStream) { $inputStream.Dispose() }
    }
}

try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    Write-Host 'Crystal Fina movie playback diagnostics (FULL GAME)' -ForegroundColor Cyan
    if ($PlayerReference) { Write-Host 'Collects the native movie display actor, player, texture/material and Cloud movie sequence.' }
    else { Write-Host 'Collects movie metadata, small CRI movie samples and recent game logs.' }
    Write-Host 'Does not install, change or start the game. No saves or credentials are collected.'
    $engine = Find-Engine $EnginePath
    if ($EnginePath -and -not $engine) { throw 'The supplied Studio engine folder was not found.' }
    if (-not $engine) {
        $candidates = @()
        $desktop = [Environment]::GetFolderPath('Desktop')
        if ($desktop) { $candidates += Join-Path $desktop 'Sephira-Studio-Test' }
        $candidates += @((Join-Path $env:USERPROFILE 'Desktop\Sephira-Studio-Test'),
            (Join-Path $env:USERPROFILE 'Downloads\Sephira-Studio-Test'),
            (Join-Path $env:USERPROFILE 'Downloads\FFR Mod\Sephira-Studio-Test'))
        if ($env:LOCALAPPDATA) { $candidates += Join-Path $env:LOCALAPPDATA 'FFR Vision Studio' }
        foreach ($candidate in $candidates) { $engine = Find-Engine $candidate; if ($engine) { break } }
    }
    if (-not $engine -and -not $NoPrompt) { $engine = Find-Engine (Read-Host 'Studio folder (Sephira-Studio-Test)') }
    if (-not $engine) { throw 'Studio engine is required for its repak movie reader. Supply -EnginePath or select the Studio folder.' }
    $repak = Join-Path $engine 'tools\repak\repak.exe'
    if (-not (Test-Path -LiteralPath $repak -PathType Leaf)) { throw 'Studio repak reader was not found: ' + $repak }
    $game = Find-Game $GamePath
    if ($GamePath -and -not $game) { throw 'Select the FULL game folder, not the demo.' }
    if (-not $game -and (Test-Path -LiteralPath (Join-Path $engine 'config.json'))) {
        $saved = Get-Content -LiteralPath (Join-Path $engine 'config.json') -Raw | ConvertFrom-Json
        $property = $saved.PSObject.Properties['gameRoot']
        if ($property) { $game = Find-Game ([string]$property.Value) }
    }
    if (-not $game) { foreach ($candidate in @(Get-SteamGames)) { $game = Find-Game $candidate; if ($game) { break } } }
    if (-not $NoPrompt) {
        $prompt = 'FULL Resonance game folder (Enter for ' + $game + ')'
        $entered = Read-Host $prompt
        if ($entered) { $game = Find-Game $entered }
    }
    if (-not $game) { throw 'Full game not found. Select the folder containing FFRS\Binaries\Win64.' }
    if (-not $OutputRoot) { $OutputRoot = Join-Path $env:USERPROFILE 'Downloads\FFR Mod' }
    $OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
    foreach ($protected in @($game, $engine)) {
        $prefix = $protected.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
        if ($OutputRoot -eq $protected -or $OutputRoot.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Choose an output folder outside the game and Studio engine.'
        }
    }
    Write-Host ('Full game: ' + $game) -ForegroundColor Cyan
    Write-Host ('Studio engine: ' + $engine)
    $prefix = if ($CaveMusic) { 'Cave-Music-Diagnostics-' } elseif ($PlayerReference) { 'Fina-Movie-Player-Reference-' } else { 'Fina-Movie-Diagnostics-' }
    $tag = $prefix + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,6)
    $script:root = Join-Path $OutputRoot $tag
    [void][IO.Directory]::CreateDirectory($script:root)
    $script:errors = New-Object 'Collections.Generic.List[string]'
    $script:records = New-Object 'Collections.Generic.List[object]'
    if ($PlayerReference) { Collect-PlayerReference $engine $game; return }
    $samples = New-Object 'Collections.Generic.List[object]'
    $profiles = New-Object 'Collections.Generic.List[object]'
    $nativeAttempts = New-Object 'Collections.Generic.List[object]'
    foreach ($relative in @('build/fina-cinematic/pak-managed.json', 'build/fina-cinematic/timeline.json',
                            'mods/EstherTsukiko/testing.json')) {
        Collect-File (Join-Path $engine $relative) ('engine/' + $relative)
    }
    if ($CaveMusic) {
        foreach ($relative in @('mods/EstherTsukiko/sephira-settings.json', 'build/launch-game.json',
            'build/fina-cinematic/cave-cue.json', 'build/fina-cinematic/cave-soundtrack.json')) {
            Collect-File (Join-Path $engine $relative) ('engine/' + $relative)
        }
        $roster = Join-Path $engine 'mods/EstherTsukiko/units.json'
        if (Test-Path -LiteralPath $roster) {
            $summary = @(Get-Content -LiteralPath $roster -Raw | ConvertFrom-Json | ForEach-Object {
                $u = $_; $selected = [ordered]@{}
                foreach ($name in @('id','key','en','ffbe','sephiraVision','studioAcquisition','bundledPreset')) {
                    $p = $u.PSObject.Properties[$name]; if ($p) { $selected[$name] = $p.Value }
                }
                [pscustomobject]$selected
            })
            $summary | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath (Join-Path $script:root 'roster-summary.json') -Encoding UTF8
        }
        $stems = @('Map/Dng/01Gra/01Gra_44/Dng_01Gra_44_PL',
            'Sequencer/Event/StudioSephira/Studio_ChristineCrystal_EV',
                'Map/Dng/01Gra/01Gra_44/GD/Dng_01Gra_44_01_GD',
            'Sound/Cri/Studio/Studio_FinaCaveMusic_Cue')
        foreach ($stem in $stems) { foreach ($extension in @('.umap','.uasset','.uexp')) {
            $relative = 'build/visions_mod/assets/FFRS/Content/' + $stem + $extension
            Collect-File (Join-Path $engine $relative) ('engine/' + $relative)
        } }
        $view = Join-Path (Join-Path $game 'FFRS/Content') ('StudioDiagnostics-' + [Guid]::NewGuid().ToString('N'))
        try {
            [void][IO.Directory]::CreateDirectory($view)
            $paks = Join-Path $game 'FFRS/Content/Paks'
            foreach ($file in (Get-ChildItem -LiteralPath $paks -File | Where-Object {
                $_.Extension -in @('.utoc','.ucas','.pak') -and ($_.BaseName -eq 'global' -or $_.BaseName -match '^FFRS-Windows(?:_|$)')
            })) { [void](New-Item -ItemType HardLink -Path (Join-Path $view $file.Name) -Target $file.FullName) }
            foreach ($extension in @('.utoc','.ucas','.pak')) {
                $file = Join-Path $paks ('~mods/zzz_EstherTsukiko_P' + $extension)
                if (Test-Path -LiteralPath $file) { [void](New-Item -ItemType HardLink -Path (Join-Path $view (Split-Path -Leaf $file)) -Target $file) }
            }
            $filters = @('Map/Dng/01Gra/01Gra_44/Dng_01Gra_44_PL',
                'Sequencer/Event/StudioSephira/Studio_ChristineCrystal_EV',
                'Map/Dng/01Gra/01Gra_44/GD/Dng_01Gra_44_01_GD',
                'Sound/Cri/Studio/Studio_FinaCaveMusic_Cue', 'Datatable/Map/MapData/DT_MapData_01Gra',
                'Datatable/Map/CDT_MapData_Prod')
            $trace = Join-Path $engine 'build/fina-cinematic/timeline.json'
            if (Test-Path -LiteralPath $trace) {
                $t = Get-Content -LiteralPath $trace -Raw | ConvertFrom-Json
                if ($t.asset -match '^FFRS/Content/Sequencer/Battle/Skill/\d{6}/\d{6}/SEQ_Battle_\d{6}_Master$') {
                    $filters += ([string]$t.asset).Substring(13) -replace '/SEQ_Battle_\d{6}_Master$', '/'
                }
            }
            $arguments = @('to-legacy','--no-shaders')
            foreach ($filter in $filters) { $arguments += @('--filter',$filter) }
            $arguments += @($view,(Join-Path $script:root 'installed/legacy'))
            $previousPreference = $ErrorActionPreference
            try {
                $ErrorActionPreference = 'Continue'
                & (Join-Path $engine 'tools/retoc/retoc.exe') @arguments 2>&1 | ForEach-Object { Write-Host $_ }
                if ($LASTEXITCODE -ne 0) { $script:errors.Add('Installed asset reader exit code: ' + $LASTEXITCODE) }
            } finally { $ErrorActionPreference = $previousPreference }
            foreach ($candidate in @('extracted/Mappings.usmap','data/Mappings.usmap')) {
                $file = Join-Path $engine $candidate
                if (Test-Path -LiteralPath $file) { Copy-Shared $file (Join-Path $script:root 'installed/Mappings.usmap'); break }
            }
        } finally { if (Test-Path -LiteralPath $view) { Remove-Item -LiteralPath $view -Recurse -Force } }
    }
    $archivePath = Join-Path $engine 'tools/fina_cinematic.zip'
    if (Test-Path -LiteralPath $archivePath) {
        $archive = [IO.Compression.ZipFile]::OpenRead($archivePath)
        try {
            foreach ($name in @('manifest.json', 'spec.json')) {
                $entry = $archive.GetEntry($name)
                if ($entry -and $entry.Length -le 128KB) {
                    $destination = Join-Path $script:root ('media/' + $name)
                    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination))
                    [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $destination)
                }
            }
        } finally { $archive.Dispose() }
    }
    $private = 'FFRS/Content/Movies/Studio/CrystalFina_Test'
    $native = 'FFRS/Content/Movies/Skill/MV_Skill440110'
    foreach ($stem in @("build/visions_mod/assets/$private", "build/visions_mod/assets/${private}_vp9",
                         "extracted/legacy/$native", "extracted/legacy/${native}_vp9")) {
        foreach ($suffix in @('.uasset', '.uexp')) {
            $relative = $stem + $suffix
            Collect-File (Join-Path $engine $relative) ('engine/' + $relative)
        }
    }
    $timelinePath = Join-Path $engine 'build/fina-cinematic/timeline.json'
    if (Test-Path -LiteralPath $timelinePath) {
        try {
            $timeline = Get-Content -LiteralPath $timelinePath -Raw | ConvertFrom-Json
            if ($timeline.asset -match '^FFRS/Content/Sequencer/Battle/Skill/(\d{6})/(\d{6})/SEQ_Battle_\2_Master$') {
                $asset = [string]$timeline.asset
                $base = $asset.Substring(0, $asset.LastIndexOf('/'))
                $id = $Matches[2]
                foreach ($part in @($asset, ($base + '/Track/SEQ_Battle_' + $id + '_Cut_000'), ($base + '/Track/SEQ_Battle_' + $id + '_Sound_001'), ($base + '/Track/SEQ_Battle_' + $id + '_Effect_000'))) {
                    foreach ($suffix in @('.uasset', '.uexp')) {
                        $relative = 'build/visions_mod/assets/' + $part + $suffix
                        Collect-File (Join-Path $engine $relative) ('engine/' + $relative)
                    }
                }
            } else { $script:errors.Add('Unexpected private master path; skipped generated sequence collection.') }
        } catch { $script:errors.Add('Timeline: ' + $_.Exception.Message) }
    }
    $paks = Join-Path $game 'FFRS/Content/Paks'
    $ownedName = 'zzz_EstherTsukiko_P'
    foreach ($folder in @((Join-Path $paks '~mods'), (Join-Path $engine 'build/out'))) {
        foreach ($suffix in @('.pak', '.utoc')) {
            Collect-File (Join-Path $folder ($ownedName + $suffix)) '' -HashOnly
        }
        $ucas = Join-Path $folder ($ownedName + '.ucas')
        if (Test-Path -LiteralPath $ucas) {
            $f = Get-Item -LiteralPath $ucas
            $script:records.Add([pscustomobject]@{path=$ucas; bytes=$f.Length; modifiedUtc=$f.LastWriteTimeUtc.ToString('o'); metadataOnly=$true})
        }
    }
    $installed = Join-Path (Join-Path $paks '~mods') ($ownedName + '.pak')
    if (Test-Path -LiteralPath $installed) {
        $foundInstalled = $false; $installedErrors = @()
        foreach ($entryPath in @('FFRS/Content/Streams/Movies/Studio/CrystalFina_Test.usm', ($private + '.usm'))) {
            try {
                $samples.Add((Export-PakEntry $repak $installed $entryPath (Join-Path $script:root 'movies/installed-fina.usm-prefix')))
                $foundInstalled = $true; break
            } catch { $installedErrors += $_.Exception.Message }
        }
        if (-not $foundInstalled) { $script:errors.Add('Installed Fina movie: ' + ($installedErrors -join ' / ')) }
    } else { $script:errors.Add('Installed Studio companion pak was not found.') }
    $foundNative = $false
    $originalName = 'Movies/Skill/MV_Skill440110_vp9.usm'
    foreach ($content in @((Join-Path $game 'FFRS/Content'), (Join-Path $game 'Content'))) {
        $loose = Join-Path $content $originalName
        $attempt = [ordered]@{file=$loose; exists=(Test-Path -LiteralPath $loose -PathType Leaf)}
        if ($attempt.exists) {
            try {
                $samples.Add((Copy-MoviePrefix $loose (Join-Path $script:root 'movies/original-cloud.usm-prefix')))
                $foundNative = $true
            } catch { $attempt['error'] = $_.Exception.Message }
        }
        $nativeAttempts.Add([pscustomobject]$attempt)
        if ($foundNative) { break }
    }
    if (Test-Path -LiteralPath $paks) {
        $basePaks = @(Get-ChildItem -LiteralPath $paks -Filter '*.pak' -File | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 10)
        # The game settings are already used by Studio's audio adapter. Collect
        # only movie/decryption booleans and counts, never the key or full INI.
        foreach ($pak in $basePaks) {
            try {
                $configLines = @(& $repak get $pak.FullName 'FFRS/Config/DefaultEngine.ini' 2>&1)
                if ($LASTEXITCODE -eq 0) {
                    $profiles.Add((Read-MovieProfile ($configLines -join "`n") ($pak.FullName + ':FFRS/Config/DefaultEngine.ini')))
                    break
                }
            } catch { $nativeAttempts.Add([pscustomobject]@{pak=$pak.Name; operation='settings'; error=$_.Exception.Message}) }
        }
        foreach ($pak in $basePaks) {
            if ($foundNative) { break }
            $attempt = [ordered]@{pak=$pak.Name; bytes=$pak.Length}
            try {
                $listing = @(& $repak list $pak.FullName 2>&1)
                if ($LASTEXITCODE -ne 0) { throw (($listing | Select-Object -First 1) -join '') }
                $movieEntries = @($listing | Where-Object { ([string]$_).Replace('\', '/') -match '(^|/)Movies/Skill/MV_Skill440110_vp9\.usm$' })
                $attempt['matchingEntries'] = $movieEntries
                if ($movieEntries.Count) {
                    $samples.Add((Export-PakEntry $repak $pak.FullName ([string]$movieEntries[0]) (Join-Path $script:root 'movies/original-cloud.usm-prefix')))
                    $foundNative = $true
                }
            } catch { $attempt['error'] = $_.Exception.Message }
            $nativeAttempts.Add([pscustomobject]$attempt)
        }
    }
    $cachedConfig = Join-Path $engine 'extracted/pak/FFRS/Config/DefaultEngine.ini'
    if (Test-Path -LiteralPath $cachedConfig) {
        $profiles.Add((Read-MovieProfile (Get-Content -LiteralPath $cachedConfig -Raw) $cachedConfig))
    }
    if (-not $foundNative) { $script:errors.Add('Original Cloud VP9 movie was not found as a loose movie or in the top-level game paks. See nativeMovieAttempts.') }
    $logRoots = @((Join-Path $game 'FFRS/Saved'))
    if ($env:LOCALAPPDATA) { $logRoots += Join-Path $env:LOCALAPPDATA 'FFRS/Saved' }
    $index = 0
    foreach ($savedRoot in $logRoots) {
        $index++
        $logFolder = Join-Path $savedRoot 'Logs'
        if (Test-Path -LiteralPath $logFolder) {
            $latest = Get-ChildItem -LiteralPath $logFolder -Filter 'FFRS*.log' -File | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
            if ($latest) { Collect-File $latest.FullName ('logs/' + $index + '-' + $latest.Name) }
        }
        foreach ($platform in @('Windows', 'WindowsNoEditor')) {
            $ini = Join-Path $savedRoot ('Config/' + $platform + '/GameUserSettings.ini')
            if (Test-Path -LiteralPath $ini) {
                $options = @(Get-Content -LiteralPath $ini | Where-Object { $_ -match '^[^;#=]*(Movie|Cinematic|CG|Resonance.*(Anim|Video))[^=]*=' })
                if ($options.Count) {
                    $script:records.Add([pscustomobject]@{path=$ini; movieSettings=$options})
                }
            }
        }
    }
    foreach ($relative in @('ue4ss/UE4SS.log', 'UE4SS.log')) {
        Collect-File (Join-Path (Join-Path $game 'FFRS/Binaries/Win64') $relative) ('logs/' + $relative)
    }
    [pscustomobject]@{schema=2; gameEdition='full'; collectedUtc=[DateTime]::UtcNow.ToString('o'); game=$game;
        engine=$engine; movieSampleLimit=2MB; files=$script:records.ToArray(); samples=$samples.ToArray();
        movieProfiles=$profiles.ToArray(); nativeMovieAttempts=$nativeAttempts.ToArray(); errors=$script:errors.ToArray()} |
        ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $script:root 'report.json') -Encoding UTF8
    $zip = $script:root + '.zip'
    [IO.Compression.ZipFile]::CreateFromDirectory($script:root, $zip)
    Write-Host ('Attach this ZIP in the chat: ' + $zip) -ForegroundColor Green
    if ($script:errors.Count) { Write-Host 'Some items were unavailable. Send the ZIP anyway; its report lists them.' -ForegroundColor Yellow }
    Write-Output $zip
} catch {
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
