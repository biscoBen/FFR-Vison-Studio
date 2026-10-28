# Windows PowerShell 5.1. Installs only its own F8-only, read-only observer.
[CmdletBinding()]
param([ValidateSet('Install','Collect','Disable')][string]$Action = 'Install',
      [string]$GamePath, [string]$OutputRoot, [switch]$NoPrompt)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$modName = 'FFRStudioBattleCommandTrace'
$owner = 'FFR Studio read-only battle command observer v1'
function Plain([string]$Path) {
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
function Find-Game([string]$Path) {
    if (-not $Path) { return $null }
    $Path = $Path.Trim().Trim('"')
    if ((Split-Path -Leaf $Path) -match '(?i)\bDEMO\b') { return $null }
    if (Test-Path -LiteralPath (Join-Path $Path 'FFRS/Binaries/Win64') -PathType Container) {
        return [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Path).Path)
    }
    return $null
}
function Check-Owned([string]$Folder) {
    Plain $Folder
    if (-not (Test-Path -LiteralPath $Folder)) { return }
    $marker = Join-Path $Folder 'observer.json'; Plain $marker
    if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) { throw 'Preserving an unknown observer folder.' }
    $record = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
    if ($record.owner -ne $owner -or $record.schema -ne 1) { throw 'Preserving an unknown observer ownership record.' }
    foreach ($rel in @('Scripts/main.lua','enabled.txt')) {
        $path = Join-Path $Folder $rel; Plain $path
        if (-not (Test-Path -LiteralPath $path)) { continue }
        $expected = if ($rel -eq 'enabled.txt') {
            'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        } else { [string]$record.scriptSha256 }
        if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $expected) {
            throw ('Preserving an edited observer file: ' + $path)
        }
    }
}
function Copy-Shared([string]$Source, [string]$Target, [long]$TailBytes = 0) {
    $reader = $null; $writer = $null
    try {
        $reader = [IO.File]::Open($Source,'Open','Read',([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
        if ($TailBytes -gt 0 -and $reader.Length -gt $TailBytes) { [void]$reader.Seek(-$TailBytes,'End') }
        $writer = [IO.File]::Create($Target); $reader.CopyTo($writer)
    } finally {
        if ($writer) { $writer.Dispose() }; if ($reader) { $reader.Dispose() }
    }
}
try {
    $game = Find-Game $GamePath
    if ($GamePath -and -not $game) { throw 'The full-game folder must contain FFRS\Binaries\Win64.' }
    if (-not $game) {
        foreach ($drive in @('D','G','C','E','F')) {
            $game = Find-Game ($drive + ':\Steam\steamapps\common\FINAL FANTASY RESONANCE')
            if ($game) { break }
        }
    }
    if (-not $NoPrompt) {
        $entered = Read-Host ('Full Resonance folder (Enter for ' + $game + ')')
        if ($entered) { $game = Find-Game $entered }
    }
    if (-not $game) { throw 'Select the full game folder, or pass -GamePath.' }
    $binary = Join-Path $game 'FFRS/Binaries/Win64'
    $folder = Join-Path $binary ('ue4ss/Mods/' + $modName)
    if ($Action -ne 'Collect') {
        foreach ($name in @('FFRS-Win64-Shipping','FFRS')) {
            if (Get-Process -Name $name -ErrorAction SilentlyContinue) { throw 'Close Resonance before installing or disabling the observer.' }
        }
        Check-Owned $folder
        $enabled = Join-Path $folder 'enabled.txt'
        if ($Action -eq 'Disable') {
            if (Test-Path -LiteralPath $enabled) { Remove-Item -LiteralPath $enabled }
            Write-Host 'Battle command observer disabled. Studio is unchanged.' -ForegroundColor Green
            return
        }
        if (-not (Test-Path -LiteralPath (Join-Path $binary 'ue4ss/UE4SS.dll') -PathType Leaf)) {
            throw 'Existing UE4SS was not found; this helper does not install or replace a loader.'
        }
        $source = Join-Path $PSScriptRoot 'main.lua'
        $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
        [void][IO.Directory]::CreateDirectory((Join-Path $folder 'Scripts'))
        if (Test-Path -LiteralPath $enabled) { Remove-Item -LiteralPath $enabled }
        Copy-Item -LiteralPath $source -Destination (Join-Path $folder 'Scripts/main.lua') -Force
        [pscustomobject]@{schema=1;owner=$owner;scriptSha256=$sourceHash} | ConvertTo-Json |
            Set-Content -LiteralPath (Join-Path $folder 'observer.json') -Encoding UTF8
        [IO.File]::WriteAllText($enabled,'')
        Write-Host 'Installed F8-only command observer. No Studio rebuild is needed.' -ForegroundColor Green
        Write-Host 'Use a skill manually, press F8 at the next command menu; repeat F8 at the start of the next battle.'
        Write-Host 'Then run Collect Battle Commands.cmd before restarting; afterward close the game and disable this observer.'
        return
    }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    if (-not $OutputRoot) { $OutputRoot = Join-Path $env:USERPROFILE 'Downloads/FFR Mod' }
    $OutputRoot = [IO.Path]::GetFullPath($OutputRoot); Plain $OutputRoot
    if ($OutputRoot -eq $game -or $OutputRoot.StartsWith($game.TrimEnd('\','/') + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {
        throw 'Choose an output folder outside the game.'
    }
    $tag = 'Battle-Command-Diagnostics-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,6)
    $root = Join-Path $OutputRoot $tag; [void][IO.Directory]::CreateDirectory($root)
    $lines = @(); $errors = @(); $files = @()
    foreach ($rel in @('ue4ss/UE4SS.log','UE4SS.log')) {
        $path = Join-Path $binary $rel
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
        $temporary = Join-Path $root 'tail.tmp'
        try {
            Copy-Shared $path $temporary 16MB
            $lines += @(Get-Content -LiteralPath $temporary | Where-Object {
                $_ -match '\[FFR Battle Commands\]|FFRStudioBattleCommandTrace|PANIC:|Error executing script|Failed to execute main script'
            })
        } catch { $errors += $rel + ': ' + $_.Exception.Message }
        finally { if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary } }
    }
    $lines | Set-Content -LiteralPath (Join-Path $root 'battle-commands.txt') -Encoding UTF8
    foreach ($rel in @('ue4ss/UE4SS.dll','ue4ss/Mods/FFRStudioBattleCommandTrace/observer.json',
        'ue4ss/Mods/FFRStudioBattleCommandTrace/enabled.txt','ue4ss/Mods/FFRStudioBattleCommandTrace/Scripts/main.lua')) {
        $path = Join-Path $binary $rel
        $r = [ordered]@{path=$rel;exists=(Test-Path -LiteralPath $path -PathType Leaf)}
        if ($r.exists) { $r['sha256'] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
        $files += [pscustomobject]$r
    }
    [pscustomobject]@{schema=1;collectedUtc=[DateTime]::UtcNow.ToString('o');game=$game;files=$files;
        errors=$errors;traceLines=$lines.Count;f8Only=$true;gameplayModified=$false;logTailLimitBytes=16MB} |
        ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $root 'report.json') -Encoding UTF8
    $zip = $root + '.zip'; [IO.Compression.ZipFile]::CreateFromDirectory($root,$zip)
    Write-Host ('Send this ZIP: ' + $zip) -ForegroundColor Green
    Write-Output $zip
} catch {
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
