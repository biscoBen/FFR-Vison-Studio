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
            return (Resolve-Path -LiteralPath $path).Path
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
    Write-Host 'Crystal Fina battle runtime diagnostics' -ForegroundColor Cyan
    Write-Host 'After testing one Fina attack and resonance, collect the installed runtime and UE4SS log.'
    Write-Host 'No game changes, save files, credentials or game assets are collected.'
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
    if (-not $game) { $game = Find-Game 'D:\Steam\steamapps\common\FINAL FANTASY RESONANCE DEMO' }
    if (-not $game -and ${env:ProgramFiles(x86)}) {
        $game = Find-Game (Join-Path ${env:ProgramFiles(x86)} 'Steam\steamapps\common\FINAL FANTASY RESONANCE DEMO')
    }
    if (-not $NoPrompt) {
        $prompt = 'Resonance game folder'
        if ($game) { $prompt += ' (Enter for ' + $game + ')' }
        $entered = Read-Host $prompt
        if ($entered) { $game = Find-Game $entered }
    }
    if (-not $game) { throw 'Could not find Resonance. Supply its game folder, containing FFRS.' }
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
        foreach ($relative in @('field-leader-state.json', 'build\field-leader\payload.json', 'build\crystal-fina-battle\runtime.json', 'existing-visions-state.json')) {
            $path = Join-Path $engine $relative
            if (Test-Path -LiteralPath $path -PathType Leaf) {
                try { Copy-Shared $path (Join-Path (Join-Path $root 'engine') $relative) }
                catch { $errors += $relative + ': ' + $_.Exception.Message }
            }
        }
    }
    [pscustomobject]@{schema=1; collectedUtc=[DateTime]::UtcNow.ToString('o'); game=$game;
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
