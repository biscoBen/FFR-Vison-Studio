# Windows PowerShell 5.1. Own observer only; never replaces Studio or the loader.
[CmdletBinding()]
param([ValidateSet('Install','Collect','Disable')][string]$Action = 'Install',
      [string]$GamePath, [string]$OutputRoot, [switch]$NoPrompt)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$modName = 'FFRStudioEsperTrace'
$owner = 'FFR Studio read-only esper observer v1'

function Find-Game([string]$Candidate) {
    if (-not $Candidate) { return $null }
    $Candidate = $Candidate.Trim().Trim('"')
    if ((Split-Path -Leaf $Candidate) -match '(?i)\bDEMO\b') { return $null }
    if (Test-Path -LiteralPath ([IO.Path]::Combine($Candidate,'FFRS/Binaries/Win64')) -PathType Container -ErrorAction SilentlyContinue) {
        return [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Candidate).Path)
    }
    return $null
}
function Assert-PlainPath([string]$Path) {
    $part = [IO.Path]::GetFullPath($Path)
    while ($part) {
        if ((Test-Path -LiteralPath $part) -and
            ((Get-Item -LiteralPath $part -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw ('Preserving linked path: ' + $part)
        }
        $parent = [IO.Path]::GetDirectoryName($part)
        if ($part -eq $parent) { break }; $part = $parent
    }
}
function Assert-Closed {
    foreach ($name in @('FFRS-Win64-Shipping','FFRS')) {
        if (Get-Process -Name $name -ErrorAction SilentlyContinue) {
            throw 'Close Resonance before installing or disabling this observer.'
        }
    }
}
function Check-Owned([string]$Folder) {
    Assert-PlainPath $Folder
    if (-not (Test-Path -LiteralPath $Folder)) { return }
    $marker = Join-Path $Folder 'observer.json'
    Assert-PlainPath $marker
    if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) { throw 'Preserving an unknown observer folder.' }
    $record = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
    if ($record.owner -ne $owner -or $record.schema -ne 1) { throw 'Preserving an unknown observer ownership record.' }
    foreach ($relative in @('Scripts/main.lua','enabled.txt')) {
        $path = Join-Path $Folder $relative
        Assert-PlainPath $path
        if (-not (Test-Path -LiteralPath $path)) { continue }
        $expected = if ($relative -eq 'enabled.txt') {
            'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        } else { [string]$record.scriptSha256 }
        if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $expected) {
            throw ('Preserving an edited observer file: ' + $path)
        }
    }
}
function Copy-Shared([string]$Source, [string]$Destination, [long]$TailBytes = 0) {
    $reader = $null; $writer = $null
    try {
        $reader = [IO.File]::Open($Source,'Open','Read',([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
        if ($TailBytes -gt 0 -and $reader.Length -gt $TailBytes) { [void]$reader.Seek(-$TailBytes,'End') }
        [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Destination))
        $writer = [IO.File]::Create($Destination); $reader.CopyTo($writer)
    } finally {
        if ($writer) { $writer.Dispose() }; if ($reader) { $reader.Dispose() }
    }
}

try {
    $game = Find-Game $GamePath
    if ($GamePath -and -not $game) { throw 'The supplied full-game folder must contain FFRS\Binaries\Win64.' }
    if (-not $game) {
        foreach ($drive in @('D','C','E','F','G')) {
            $game = Find-Game ($drive + ':\Steam\steamapps\common\FINAL FANTASY RESONANCE')
            if ($game) { break }
        }
    }
    if (-not $NoPrompt) {
        $prompt = 'Full Resonance folder'; if ($game) { $prompt += ' (Enter for ' + $game + ')' }
        $entered = Read-Host $prompt
        if ($entered) { $game = Find-Game $entered }
    }
    if (-not $game) { throw 'Select the FULL game folder containing FFRS, or pass -GamePath.' }
    $binary = Join-Path $game 'FFRS/Binaries/Win64'
    $mods = Join-Path $binary 'ue4ss/Mods'
    $folder = Join-Path $mods $modName
    if ($Action -eq 'Install' -or $Action -eq 'Disable') {
        Assert-Closed
        Check-Owned $folder
        if ($Action -eq 'Disable') {
            $enabled = Join-Path $folder 'enabled.txt'
            if (Test-Path -LiteralPath $enabled) { Remove-Item -LiteralPath $enabled }
            Write-Host 'Esper observer disabled. Studio and its esper effects are unchanged.' -ForegroundColor Green
            return
        }
        if (-not (Test-Path -LiteralPath (Join-Path $binary 'ue4ss/UE4SS.dll') -PathType Leaf) -or
            -not (Test-Path -LiteralPath $mods -PathType Container)) {
            throw 'Existing Studio UE4SS was not found. This helper does not install or replace a loader.'
        }
        $source = Join-Path $PSScriptRoot 'main.lua'
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw 'Extract the whole ZIP; main.lua is missing.' }
        $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
        [void][IO.Directory]::CreateDirectory((Join-Path $folder 'Scripts'))
        $enabled = Join-Path $folder 'enabled.txt'
        if (Test-Path -LiteralPath $enabled) { Remove-Item -LiteralPath $enabled }
        [pscustomobject]@{schema=1;owner=$owner;scriptSha256=$sourceHash} | ConvertTo-Json |
            Set-Content -LiteralPath (Join-Path $folder 'observer.json') -Encoding UTF8
        Copy-Item -LiteralPath $source -Destination (Join-Path $folder 'Scripts/main.lua') -Force
        [IO.File]::WriteAllText($enabled,'')
        Write-Host 'Read-only esper observer installed. No Studio rebuild/install is needed.' -ForegroundColor Green
        Write-Host 'Start the game. Equip the MR rewards or Spirit of Eiko ON FINA, then summon an esper.'
        Write-Host 'F8: before summoning, while the esper is present, and after its final special. F9 stops tracing.'
        Write-Host 'Run Collect Esper Diagnostics.cmd BEFORE restarting the game; send the resulting ZIP.'
        return
    }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    if (-not $OutputRoot) { $OutputRoot = Join-Path $env:USERPROFILE 'Downloads/FFR Mod' }
    $OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
    $prefix = $game.TrimEnd('\','/') + [IO.Path]::DirectorySeparatorChar
    if ($OutputRoot -eq $game -or $OutputRoot.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) {
        throw 'Choose an output folder outside the game.'
    }
    Assert-PlainPath $OutputRoot
    $tag = 'Esper-Mastery-Diagnostics-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,6)
    $root = Join-Path $OutputRoot $tag
    [void][IO.Directory]::CreateDirectory($root)
    $records = @(); $errors = @(); $trace = @()
    foreach ($relative in @('ue4ss/UE4SS.log','UE4SS.log')) {
        $path = Join-Path $binary $relative
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
        $temporary = Join-Path $root 'log-read.tmp'
        try {
            Copy-Shared $path $temporary 16MB
            $trace += @(Get-Content -LiteralPath $temporary | Where-Object {
                $_ -match '\[FFR Esper(?: Trace)?\]|FFRStudioEsperTrace|FFRStudioFieldLeader|UE4SS - v|Lua.*[Ee]rror'
            })
        } catch { $errors += $relative + ': ' + $_.Exception.Message }
        finally { if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary } }
    }
    $trace | Set-Content -LiteralPath (Join-Path $root 'esper-trace.txt') -Encoding UTF8
    $runtime = Join-Path $mods 'FFRStudioFieldLeader/Scripts/main.lua'
    $config = Join-Path $mods 'FFRStudioFieldLeader/Scripts/config.lua'
    $runtimeText = ''; $configText = ''
    foreach ($relative in @('ue4ss/UE4SS.dll','ue4ss/Mods/mods.txt',
        'ue4ss/Mods/FFRStudioEsperTrace/observer.json','ue4ss/Mods/FFRStudioEsperTrace/enabled.txt',
        'ue4ss/Mods/FFRStudioEsperTrace/Scripts/main.lua',
        'ue4ss/Mods/FFRStudioFieldLeader/enabled.txt','ue4ss/Mods/FFRStudioFieldLeader/Scripts/main.lua',
        'ue4ss/Mods/FFRStudioFieldLeader/Scripts/config.lua')) {
        $path = Join-Path $binary $relative
        $record = [ordered]@{path=$relative;exists=(Test-Path -LiteralPath $path -PathType Leaf)}
        if ($record.exists) {
            try {
                $file = Get-Item -LiteralPath $path
                $record['bytes'] = $file.Length
                $record['sha256'] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
                if (-not $relative.EndsWith('.dll') -and $file.Length -le 2MB) {
                    Copy-Shared $path (Join-Path (Join-Path $root 'installed') $relative)
                    if ($path -eq $runtime) { $runtimeText = [IO.File]::ReadAllText($path) }
                    if ($path -eq $config) { $configText = [IO.File]::ReadAllText($path) }
                }
            } catch { $errors += $relative + ': ' + $_.Exception.Message }
        }
        $records += [pscustomobject]$record
    }
    $ready = @($trace | Where-Object { $_ -match '\[FFR Esper Trace\] READY' }).Count
    $masteryReady = @($trace | Where-Object { $_ -match '\[FFR Esper\] Esper mastery ready' }).Count
    [pscustomobject]@{schema=1;collectedUtc=[DateTime]::UtcNow.ToString('o');game=$game;
        files=$records;errors=$errors;traceLines=$trace.Count;observerReadyMarkers=$ready;
        masteryReadyMarkers=$masteryReady;esperMasteryConfigured=($configText -match '\besperMastery\s*=\s*1\b');
        runtimeContainsEsperCode=$runtimeText.Contains('Esper mastery ready');
        sampled=$true;intervalMs=100;logTailLimitBytes=16MB;absenceProvesNoActivation=$false} |
        ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $root 'report.json') -Encoding UTF8
    $zip = $root + '.zip'
    [IO.Compression.ZipFile]::CreateFromDirectory($root,$zip)
    Write-Host ('Send this ZIP: ' + $zip) -ForegroundColor Green
    if (-not $ready) { Write-Host 'No observer READY marker; send the ZIP anyway to check startup.' -ForegroundColor Yellow }
    Write-Output $zip
} catch {
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
