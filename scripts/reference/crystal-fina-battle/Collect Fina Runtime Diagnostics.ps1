# Windows PowerShell 5.1. Read-only collection; never starts or changes the game.
[CmdletBinding()]
param([string]$GamePath, [string]$EnginePath, [string]$OutputRoot, [switch]$NoPrompt)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

function Find-Game([string]$Candidate) {
    if (-not $Candidate) { return $null }
    $Candidate = $Candidate.Trim().Trim('"')
    foreach ($suffix in @('', '..\..\..')) {
        $path = $Candidate
        if ($suffix) { $path = Join-Path $Candidate $suffix }
        if (Test-Path -LiteralPath (Join-Path $path 'FFRS\Binaries\Win64') -PathType Container) {
            $resolved = (Resolve-Path -LiteralPath $path).Path
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

try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    Write-Host 'Crystal Fina FULL GAME runtime diagnostics' -ForegroundColor Cyan
    Write-Host 'After testing one Fina attack and resonance, collect the installed runtime and UE4SS log.'
    Write-Host 'No game changes, save files, credentials or game assets are collected.'
    $engine = Find-Engine $EnginePath
    if ($EnginePath -and -not $engine) { throw 'The supplied Studio engine folder was not found.' }
    if (-not $engine) {
        $desktop = [Environment]::GetFolderPath('Desktop')
        $candidates = @()
        if ($desktop) { $candidates += Join-Path $desktop 'Sephira-Studio-Test' }
        $candidates += @((Join-Path $env:USERPROFILE 'Desktop\Sephira-Studio-Test'),
            (Join-Path $env:USERPROFILE 'Downloads\Sephira-Studio-Test'),
            (Join-Path $env:USERPROFILE 'Downloads\FFR Mod\Sephira-Studio-Test'))
        if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA 'FFR Vision Studio') }
        foreach ($candidate in $candidates) { $engine = Find-Engine $candidate; if ($engine) { break } }
    }
    if (-not $engine -and -not $NoPrompt) {
        $entered = Read-Host 'Studio folder (Sephira-Studio-Test, or Enter to collect installed runtime only)'
        if ($entered) {
            $engine = Find-Engine $entered
            if (-not $engine) { throw 'The supplied Studio folder does not contain its engine.' }
        }
    }
    $game = Find-Game $GamePath
    if ($GamePath -and -not $game) { throw 'Select the FULL game folder containing FFRS\Binaries\Win64, not the demo.' }
    if (-not $game -and $engine -and (Test-Path -LiteralPath (Join-Path $engine 'config.json'))) {
        $saved = Get-Content -LiteralPath (Join-Path $engine 'config.json') -Raw | ConvertFrom-Json
        $property = $saved.PSObject.Properties['gameRoot']
        if ($null -ne $property) { $game = Find-Game ([string]$property.Value) }
    }
    if (-not $game) {
        foreach ($candidate in @(Get-SteamGames)) { $game = Find-Game $candidate; if ($game) { break } }
    }
    if (-not $NoPrompt) {
        $prompt = 'FULL Resonance game folder (not the demo)'
        if ($game) { $prompt += ' (Enter for ' + $game + ')' }
        $entered = Read-Host $prompt
        if ($entered) { $game = Find-Game $entered }
    }
    if (-not $game) { throw 'Could not find the FULL game. Supply its folder, containing FFRS (not the demo).' }
    Write-Host ('Full game: ' + $game) -ForegroundColor Cyan
    if ($engine) { Write-Host ('Studio engine: ' + $engine) }
    else { Write-Host 'Studio engine not found; collecting the installed runtime and logs only.' -ForegroundColor Yellow }
    if (-not $OutputRoot) { $OutputRoot = Join-Path $env:USERPROFILE 'Downloads\FFR Mod' }
    $OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)
    $prefix = $game.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    if ($OutputRoot -eq $game -or $OutputRoot.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Choose an output folder outside the game. Default: Downloads\FFR Mod.'
    }
    $tag = 'Fina-Runtime-Diagnostics-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 6)
    $root = Join-Path $OutputRoot $tag
    [void][System.IO.Directory]::CreateDirectory($root)
    $binary = Join-Path $game 'FFRS\Binaries\Win64'
    $records = @(); $errors = @()
    # Explicit allowlist. DLLs are hashed only; no recursive game/Studio scan.
    $files = @('dwmapi.dll', 'ue4ss\UE4SS.dll', 'ue4ss\UE4SS.log', 'UE4SS.log',
        'ue4ss\UE4SS-settings.ini', 'ue4ss\Mods\mods.txt', 'ue4ss\Mods\mods.json',
        'ue4ss\Mods\FFRStudioFieldLeader\enabled.txt',
        'ue4ss\Mods\FFRStudioFieldLeader\Scripts\config.lua',
        'ue4ss\Mods\FFRStudioFieldLeader\Scripts\main.lua')
    foreach ($relative in $files) {
        $path = Join-Path $binary $relative
        $record = [ordered]@{ path = $relative; exists = (Test-Path -LiteralPath $path -PathType Leaf) }
        if ($record.exists) {
            try {
                $file = Get-Item -LiteralPath $path
                $record['modifiedUtc'] = $file.LastWriteTimeUtc.ToString('o')
                $record['bytes'] = $file.Length
                if ($relative.EndsWith('.dll')) { $record['sha256'] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
                else { Copy-Shared $path (Join-Path (Join-Path $root 'installed') $relative) }
            } catch { $errors += $relative + ': ' + $_.Exception.Message }
        }
        $records += [pscustomobject]$record
    }
    if ($engine) {
        $ledger = 'game-installs\' + (Get-InstallKey $game) + '\field-leader-state.json'
        if (-not (Test-Path -LiteralPath (Join-Path $engine $ledger) -PathType Leaf)) { $ledger = 'field-leader-state.json' }
        foreach ($relative in @($ledger, 'build\field-leader\payload.json', 'build\crystal-fina-battle\runtime.json', 'existing-visions-state.json')) {
            $path = Join-Path $engine $relative
            if (Test-Path -LiteralPath $path -PathType Leaf) {
                try { Copy-Shared $path (Join-Path (Join-Path $root 'engine') $relative) }
                catch { $errors += $relative + ': ' + $_.Exception.Message }
            }
        }
    }
    [pscustomobject]@{schema=2; gameEdition='full'; collectedUtc=[DateTime]::UtcNow.ToString('o'); game=$game;
        engine=$engine; files=$records; errors=$errors} | ConvertTo-Json -Depth 8 |
        Set-Content -LiteralPath (Join-Path $root 'report.json') -Encoding UTF8
    $logs = @(Get-ChildItem -LiteralPath $root -Filter 'UE4SS.log' -Recurse -File)
    $lines = @('Fina-specific log lines (full allowlisted UE4SS logs are included):')
    foreach ($log in $logs) {
        $lines += (Select-String -LiteralPath $log.FullName -Pattern 'FFR Fina|FFRStudioFieldLeader|fina_battle|config.lua|main.lua|Error|Exception' |
            Select-Object -Last 150 | ForEach-Object { $_.Line })
    }
    if (-not $logs.Count) { $lines += 'No UE4SS.log found. See report.json for loader and installed-script presence.' }
    $lines | Set-Content -LiteralPath (Join-Path $root 'fina-log-summary.txt') -Encoding UTF8
    $zip = $root + '.zip'
    [System.IO.Compression.ZipFile]::CreateFromDirectory($root, $zip)
    Write-Host ''
    Write-Host ('Attach this ZIP in the chat: ' + $zip) -ForegroundColor Green
    if ($errors.Count) { Write-Host 'Some files could not be read; details are included in report.json.' -ForegroundColor Yellow }
    Write-Output $zip
} catch {
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
