# Windows PowerShell 5.1. Read-only crash collection: no installation or game launch.
[CmdletBinding()]
param([string]$GamePath, [string]$EnginePath, [string]$OutputRoot, [switch]$NoPrompt,
      [switch]$WatchGame, [switch]$OpenOutput, [ValidateRange(0,86400)][int]$StartTimeoutSeconds=0)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

function Find-Game([string]$Candidate) {
    if (-not $Candidate) { return $null }
    $Candidate = $Candidate.Trim().Trim('"')
    foreach ($suffix in @('', '..\..\..')) {
        $path = $Candidate
        if ($suffix) { $path = [IO.Path]::Combine($Candidate,$suffix) }
        if (Test-Path -LiteralPath ([IO.Path]::Combine($path,'FFRS\Binaries\Win64')) -PathType Container -ErrorAction SilentlyContinue) {
            # Normalize existing game roots with the same .NET routine used
            # for output paths. On Windows a TEMP ancestor can use its 8.3
            # alias while GetFullPath expands it to the long spelling.
            $resolved=[System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $path).Path)
            if (($resolved.TrimEnd('\','/') -split '[\\/]')[-1] -match '(?i)\bDEMO\b') { continue }
            return $resolved
        }
    }
    return $null
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
function Assert-PlainPath([string]$Path) {
    $part = [System.IO.Path]::GetFullPath($Path)
    while ($part) {
        if (Test-Path -LiteralPath $part) {
            $item = Get-Item -LiteralPath $part -Force
            if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { throw ('Preserving linked path: ' + $part) }
        }
        $parent = [System.IO.Path]::GetDirectoryName($part)
        if ($parent -eq $part) { break }
        $part = $parent
    }
}
function Copy-Shared([string]$Source, [string]$Destination, [long]$Limit=4194304) {
    $reader = $null; $writer = $null
    try {
        $reader = [System.IO.File]::Open($Source, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read,
            ([System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete))
        [void][System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($Destination))
        $writer = [System.IO.File]::Create($Destination)
        if ($reader.Length -gt $Limit) { [void]$reader.Seek(-$Limit, [System.IO.SeekOrigin]::End) }
        $remaining = [Math]::Min($reader.Length, $Limit)
        $buffer = New-Object byte[] 65536
        while ($remaining -gt 0) {
            $read = $reader.Read($buffer, 0, [int][Math]::Min($buffer.Length, $remaining))
            if ($read -eq 0) { break }
            $writer.Write($buffer, 0, $read); $remaining -= $read
        }
    } finally {
        if ($writer) { $writer.Dispose() }; if ($reader) { $reader.Dispose() }
    }
}

try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    Write-Host 'Resonance logs and crash collector (no game script installed)' -ForegroundColor Cyan
    if (-not $WatchGame) { Write-Host 'Run before launching Resonance again so its latest logs are preserved.' }
    $engine = Find-Engine $EnginePath
    if ($EnginePath -and -not $engine) { throw 'The supplied Studio engine folder was not found.' }
    if (-not $engine) {
        $candidates = @((Join-Path $env:USERPROFILE 'Downloads\Sephira-Studio-Test'),
            (Join-Path $env:USERPROFILE 'Downloads\FFR Mod\Sephira-Studio-Test'))
        if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA 'FFR Vision Studio') }
        foreach ($candidate in $candidates) { $engine = Find-Engine $candidate; if ($engine) { break } }
    }
    $game = Find-Game $GamePath
    if ($GamePath -and -not $game) { throw 'The supplied game folder must contain FFRS\Binaries\Win64.' }
    if (-not $game -and $engine -and (Test-Path -LiteralPath (Join-Path $engine 'config.json'))) {
        $saved = Get-Content -LiteralPath (Join-Path $engine 'config.json') -Raw | ConvertFrom-Json
        $property = $saved.PSObject.Properties['gameRoot']
        if ($null -ne $property) { $game = Find-Game ([string]$property.Value) }
    }
    if (-not $game) {
        foreach ($drive in @('G','D','C','E','F')) {
            $game = Find-Game ($drive + ':\Steam\steamapps\common\FINAL FANTASY RESONANCE')
            if ($game) { break }
        }
    }
    if (-not $game -and ${env:ProgramFiles(x86)}) {
        $game = Find-Game ([IO.Path]::Combine(${env:ProgramFiles(x86)},'Steam\steamapps\common\FINAL FANTASY RESONANCE'))
    }
    if (-not $NoPrompt -and (-not $WatchGame -or -not $game)) {
        $prompt = 'Resonance game folder'
        if ($game) { $prompt += ' (Enter for ' + $game + ')' }
        $entered = Read-Host $prompt
        if ($entered) { $game = Find-Game $entered }
    }
    if (-not $game) { throw 'Could not find Resonance. Supply its game folder, containing FFRS.' }
    Write-Host ('Selected game: ' + $game)
    if (-not $OutputRoot) { $OutputRoot = Join-Path $env:USERPROFILE 'Downloads\FFR Mod' }
    $OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)
    $prefix = $game.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    if ($OutputRoot -eq $game -or $OutputRoot.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Choose an output folder outside the game. Default: Downloads\FFR Mod.'
    }
    Assert-PlainPath $OutputRoot
    $session=$null
    if ($WatchGame) {
        $watcher=Join-Path $PSScriptRoot 'DiagnosticSession.ps1'
        if (-not (Test-Path -LiteralPath $watcher -PathType Leaf)) {
            $watcher=[IO.Path]::GetFullPath([IO.Path]::Combine($PSScriptRoot,'../common/DiagnosticSession.ps1'))
        }
        if (-not (Test-Path -LiteralPath $watcher -PathType Leaf)) { throw 'Extract the whole diagnostic ZIP; DiagnosticSession.ps1 is missing.' }
        . $watcher
        $session=Wait-FFRStudioGameSession -GamePath $game -StartTimeoutSeconds $StartTimeoutSeconds
        Start-Sleep -Milliseconds 1500
    }
    $prefixTag=if ($WatchGame) { 'Resonance-Diagnostic-Session-' } else { 'Resonance-Crash-Reference-' }
    $tag = $prefixTag + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,6)
    $root = Join-Path $OutputRoot $tag
    [void][System.IO.Directory]::CreateDirectory($root)
    $script:records = @(); $script:errors = @()
    function Collect-Text([string]$Source, [string]$Relative, [switch]$Whole) {
        if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) { return }
        try {
            Assert-PlainPath $Source
            $file = Get-Item -LiteralPath $Source
            if ($Whole -and $file.Length -gt 4194304) { throw 'Report exceeds 4 MiB; recorded but not copied.' }
            Copy-Shared $Source (Join-Path $root $Relative)
            $script:records += [pscustomobject]@{path=$Source; collected=$Relative;
                bytes=$file.Length; modifiedUtc=$file.LastWriteTimeUtc.ToString('o'); tailOnly=($file.Length -gt 4194304)}
        } catch { $script:errors += $Source + ': ' + $_.Exception.Message }
    }
    $binary = Join-Path $game 'FFRS\Binaries\Win64'
    # Full recent logs are useful for native/loader stack traces; large logs are bounded tails.
    foreach ($relative in @('ue4ss\UE4SS.log', 'UE4SS.log', 'ue4ss\UE4SS-settings.ini',
                            'ue4ss\Mods\mods.txt', 'ue4ss\Mods\mods.json')) {
        Collect-Text (Join-Path $binary $relative) ('installed/' + $relative)
    }
    # Runtime/version inventory only: do not copy DLLs, mod contents, custom rosters or saves.
    $runtime = @()
    foreach ($relative in @('dwmapi.dll', 'ue4ss\UE4SS.dll',
            'ue4ss\Mods\FFRStudioFieldLeader\enabled.txt',
            'ue4ss\Mods\FFRStudioFieldLeader\Scripts\main.lua',
            'ue4ss\Mods\FFRStudioFieldLeader\Scripts\config.lua',
            'ue4ss\Mods\FFRStudioFieldLeader\Scripts\fina_battle.lua',
            'ue4ss\Mods\FFRStudioBattleCommandTrace\enabled.txt',
            'ue4ss\Mods\FFRStudioBattleCommandTrace\Scripts\main.lua',
            'ue4ss\Mods\FFRStudioBattleCommandTrace\observer.json',
            'ue4ss\Mods\FFRStudioMovieTrace\enabled.txt',
            'ue4ss\Mods\FFRStudioSkillTrace\enabled.txt',
            'ue4ss\Mods\FFRStudioSkillTrace\Scripts\main.lua')) {
        $path = Join-Path $binary $relative
        $record = [ordered]@{path=$relative; exists=(Test-Path -LiteralPath $path -PathType Leaf)}
        if ($record.exists) {
            try {
                Assert-PlainPath $path
                $record['sha256'] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
                $record['bytes'] = (Get-Item -LiteralPath $path).Length
            } catch { $script:errors += $path + ': ' + $_.Exception.Message }
        }
        $runtime += [pscustomobject]$record
    }
    $mods = Join-Path $binary 'ue4ss\Mods'
    $modInventory = @()
    if (Test-Path -LiteralPath $mods -PathType Container) {
        Assert-PlainPath $mods
        foreach ($mod in Get-ChildItem -LiteralPath $mods -Directory -Force) {
            if ($mod.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { continue }
            $modInventory += [pscustomobject]@{name=$mod.Name;
                enabledMarker=(Test-Path -LiteralPath (Join-Path $mod.FullName 'enabled.txt') -PathType Leaf)}
        }
    }
    $pakInventory = @()
    $pakFolder = Join-Path $game 'FFRS\Content\Paks\~mods'
    if (Test-Path -LiteralPath $pakFolder -PathType Container) {
        Assert-PlainPath $pakFolder
        foreach ($pak in Get-ChildItem -LiteralPath $pakFolder -File) {
            if ($pak.Extension -notin @('.pak', '.utoc', '.ucas') -or
                $pak.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { continue }
            $pakInventory += [pscustomobject]@{name=$pak.Name; bytes=$pak.Length; modifiedUtc=$pak.LastWriteTimeUtc.ToString('o')}
        }
    }
    $savedRoots = @((Join-Path $game 'FFRS\Saved'))
    if ($env:LOCALAPPDATA) { $savedRoots += (Join-Path $env:LOCALAPPDATA 'FFRS\Saved') }
    $savedRoots = @($savedRoots | Select-Object -Unique)
    $searched = @(); $crashCount = 0
    for ($index=0; $index -lt $savedRoots.Count; $index++) {
        $savedRoot = $savedRoots[$index]
        $crashes = Join-Path $savedRoot 'Crashes'; $logs = Join-Path $savedRoot 'Logs'
        $searched += [pscustomobject]@{saved=$savedRoot; crashes=(Test-Path -LiteralPath $crashes); logs=(Test-Path -LiteralPath $logs)}
        if (Test-Path -LiteralPath $crashes -PathType Container) {
            Assert-PlainPath $crashes
            $folders = @(Get-ChildItem -LiteralPath $crashes -Directory | Where-Object {
                -not ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
            } | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 3)
            foreach ($folder in $folders) {
                $crashCount++
                foreach ($file in Get-ChildItem -LiteralPath $folder.FullName -File) {
                    if ($file.Name -in @('CrashContext.runtime-xml', 'Diagnostics.txt') -or $file.Extension -eq '.log') {
                        Collect-Text $file.FullName ('saved-' + $index + '/crashes/' + $folder.Name + '/' + $file.Name) -Whole:($file.Extension -ne '.log')
                    }
                }
            }
        }
        if (Test-Path -LiteralPath $logs -PathType Container) {
            Assert-PlainPath $logs
            foreach ($file in @(Get-ChildItem -LiteralPath $logs -Filter '*.log' -File |
                    Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 2)) {
                Collect-Text $file.FullName ('saved-' + $index + '/logs/' + $file.Name)
            }
        }
    }
    if ($engine) {
        foreach ($relative in @('mods\EstherTsukiko\testing.json', 'mods\EstherTsukiko\ability-modes.json',
                '.ffr-existing-visions\state.json', 'existing-visions-state.json', 'build\animation-repair-report.json')) {
            Collect-Text (Join-Path $engine $relative) ('engine/' + $relative) -Whole
        }
    }
    [pscustomobject]@{schema=1; collectedUtc=[DateTime]::UtcNow.ToString('o'); game=$game; engine=$engine;
        files=$script:records; errors=$script:errors; runtime=$runtime; mods=$modInventory; pakInventory=$pakInventory;
        searched=$searched; crashFolders=$crashCount; maxBytesPerFile=4194304;session=$session;
        excludes=@('saves', 'credentials', 'game assets', 'DLL contents', 'memory dumps', 'custom rosters')} |
        ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $root 'report.json') -Encoding UTF8
    $zip = $root + '.zip'
    [System.IO.Compression.ZipFile]::CreateFromDirectory($root, $zip)
    Write-Host ('Attach this ZIP in chat: ' + $zip) -ForegroundColor Green
    if (-not $crashCount) { Write-Host 'No Unreal crash folder was found; send the ZIP anyway for the loader/game logs.' -ForegroundColor Yellow }
    if ($script:errors.Count) { Write-Host 'Some files could not be read; details are in report.json.' -ForegroundColor Yellow }
    Write-Output $zip
    if ($OpenOutput -and $env:OS -eq 'Windows_NT') {
        try { Invoke-Item -LiteralPath $OutputRoot }
        catch { Write-Host ('Export is ready in ' + $OutputRoot) -ForegroundColor Yellow }
    }
} catch {
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
