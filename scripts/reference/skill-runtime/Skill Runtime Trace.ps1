# Windows PowerShell 5.1. Installs only this observer in an EXISTING UE4SS.
[CmdletBinding()]
param([ValidateSet('Enable', 'Collect', 'Remove')][string]$Action,
    [string]$GamePath, [string]$EnginePath, [string]$OutputRoot, [switch]$NoPrompt)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$modName = 'FFRStudioSkillTrace'
$markerName = '.ffr-skill-trace.json'
$ownedNames = @('Scripts/main.lua', 'enabled.txt')

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
function Assert-Closed {
    foreach ($name in @('FFRS-Win64-Shipping', 'FFRS')) {
        if (Get-Process -Name $name -ErrorAction SilentlyContinue) { throw 'Close Resonance before enabling or removing the trace.' }
    }
}
function Check-Owned([string]$Folder) {
    Assert-PlainPath $Folder
    if (-not (Test-Path -LiteralPath $Folder)) { return }
    $marker = Join-Path $Folder $markerName
    if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) { throw 'Preserving an unowned FFRStudioSkillTrace folder.' }
    Assert-PlainPath $marker
    $state = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
    if ($state.schema -ne 1 -or $state.owner -ne $modName -or @($state.files.PSObject.Properties).Count -ne 2) {
        throw 'Preserving an unknown trace ownership record.'
    }
    foreach ($property in $state.files.PSObject.Properties) {
        if ($ownedNames -notcontains $property.Name -or [string]$property.Value -notmatch '^[0-9a-fA-F]{64}$') {
            throw 'Preserving an invalid trace ownership record.'
        }
        $path = Join-Path $Folder $property.Name
        Assert-PlainPath $path
        if (Test-Path -LiteralPath $path) {
            if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or
                (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $property.Value) {
                throw ('Preserving an edited trace file: ' + $path)
            }
        }
    }
    # Do not recurse through an unexpected directory or junction. Only our
    # known Scripts directory may contain files, and every file is allowlisted.
    foreach ($item in Get-ChildItem -LiteralPath $Folder -Force) {
        Assert-PlainPath $item.FullName
        if ($item.Name -eq 'Scripts' -and $item.PSIsContainer) {
            foreach ($child in Get-ChildItem -LiteralPath $item.FullName -Force) {
                Assert-PlainPath $child.FullName
                if ($child.PSIsContainer -or $child.Name -ne 'main.lua') { throw 'Preserving unknown trace content.' }
            }
        } elseif ($item.PSIsContainer -or @($markerName, 'enabled.txt') -notcontains $item.Name) {
            throw 'Preserving unknown trace content.'
        }
    }
}
function Write-Utf8([string]$Path, [string]$Text) {
    [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false))
}
function Copy-Shared([string]$Source, [string]$Destination) {
    $reader = $null; $writer = $null
    try {
        $reader = [System.IO.File]::Open($Source, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read,
            ([System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete))
        [void][System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($Destination))
        $writer = [System.IO.File]::Create($Destination)
        $reader.CopyTo($writer)
    } finally {
        if ($writer) { $writer.Dispose() }; if ($reader) { $reader.Dispose() }
    }
}

try {
    Write-Host 'Skill runtime trace - uses your existing UE4SS' -ForegroundColor Cyan
    if (-not $Action) {
        if ($NoPrompt) { throw 'Supply -Action Enable, Collect or Remove with -NoPrompt.' }
        Write-Host '1. Enable trace (close the game first)'
        Write-Host '2. Collect trace ZIP after testing (game may stay open)'
        Write-Host '3. Remove trace (close the game first)'
        switch (Read-Host 'Choose 1, 2 or 3') {
            '1' { $Action = 'Enable' }; '2' { $Action = 'Collect' }; '3' { $Action = 'Remove' }
            default { throw 'Choose 1, 2 or 3.' }
        }
    }
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
    $binary = Join-Path $game 'FFRS\Binaries\Win64'
    $mod = Join-Path $binary ('ue4ss\Mods\' + $modName)
    if ($Action -eq 'Enable') {
        Assert-Closed
        Check-Owned $mod
        foreach ($relative in @('dwmapi.dll', 'ue4ss\UE4SS.dll')) {
            $path = Join-Path $binary $relative
            Assert-PlainPath $path
            if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
                throw 'Existing UE4SS was not found. This helper does not install or replace a loader. Send this message in chat.'
            }
        }
        $source = Join-Path $PSScriptRoot 'main.lua'
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw 'Extract all helper files together; main.lua is missing.' }
        $body = [System.IO.File]::ReadAllText($source)
        if (-not $body.StartsWith('-- Optional sampled observer')) { throw 'Unexpected observer source.' }
        # Record ownership first for recovery if publication is interrupted.
        # Remove the enable marker first and publish it last, as Studio does.
        [void][System.IO.Directory]::CreateDirectory((Join-Path $mod 'Scripts'))
        $enabled = Join-Path $mod 'enabled.txt'
        if (Test-Path -LiteralPath $enabled) { Remove-Item -LiteralPath $enabled }
        $hash = [System.Security.Cryptography.SHA256]::Create()
        try { $bodyHash = [BitConverter]::ToString($hash.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($body))).Replace('-', '') }
        finally { $hash.Dispose() }
        $files = [ordered]@{'Scripts/main.lua'=$bodyHash; 'enabled.txt'='E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855'}
        Write-Utf8 (Join-Path $mod $markerName) ([pscustomobject]@{schema=1;owner=$modName;files=$files} | ConvertTo-Json -Depth 4)
        Write-Utf8 (Join-Path $mod 'Scripts\main.lua') $body
        Write-Utf8 $enabled ''
        Write-Host 'Trace enabled. Launch Resonance and reproduce one failed skill plus one working skill.' -ForegroundColor Green
        Write-Host 'Leave enemies time to act. F8 adds a bookmark; F9 stops sampling. Both are optional.'
        Write-Host 'Then run this helper again and choose 2. No Studio rebuild is needed.'
    } elseif ($Action -eq 'Remove') {
        Assert-Closed
        Check-Owned $mod
        if (Test-Path -LiteralPath $mod) {
            foreach ($relative in @('enabled.txt', 'Scripts/main.lua', $markerName)) {
                $path = Join-Path $mod $relative
                if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
            }
            $scripts = Join-Path $mod 'Scripts'
            if (Test-Path -LiteralPath $scripts) { Remove-Item -LiteralPath $scripts }
            Remove-Item -LiteralPath $mod
        }
        Write-Host 'Skill trace removed. The UE4SS loader, Studio runtime and other mods are unchanged.' -ForegroundColor Green
    } else {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        if (-not $OutputRoot) { $OutputRoot = Join-Path $env:USERPROFILE 'Downloads\FFR Mod' }
        $OutputRoot = [System.IO.Path]::GetFullPath($OutputRoot)
        $prefix = $game.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
        if ($OutputRoot -eq $game -or $OutputRoot.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw 'Choose an output folder outside the game. Default: Downloads\FFR Mod.'
        }
        Assert-PlainPath $OutputRoot
        $tag = 'Skill-Runtime-Trace-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,6)
        $root = Join-Path $OutputRoot $tag
        [void][System.IO.Directory]::CreateDirectory($root)
        $records = @(); $errors = @(); $trace = @()
        # Explicit allowlist: filtered trace/own-mod startup records, runtime scripts,
        # loader hashes and presentation report. No full UE4SS log or config.
        foreach ($relative in @('ue4ss\UE4SS.log', 'UE4SS.log')) {
            $path = Join-Path $binary $relative
            if (Test-Path -LiteralPath $path -PathType Leaf) {
                $temporary = Join-Path $root 'log-read.tmp'
                try {
                    Copy-Shared $path $temporary
                    $trace += @(Get-Content -LiteralPath $temporary | Where-Object {
                        $_.Contains('[FFR Skill Trace]') -or $_.Contains('FFRStudioSkillTrace')
                    })
                } catch { $errors += $relative + ': ' + $_.Exception.Message }
                finally { if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary } }
            }
        }
        $trace | Set-Content -LiteralPath (Join-Path $root 'skill-trace.txt') -Encoding UTF8
        foreach ($relative in @('dwmapi.dll', 'ue4ss\UE4SS.dll',
            'ue4ss\Mods\FFRStudioSkillTrace\.ffr-skill-trace.json',
            'ue4ss\Mods\FFRStudioSkillTrace\enabled.txt',
            'ue4ss\Mods\FFRStudioSkillTrace\Scripts\main.lua')) {
            $path = Join-Path $binary $relative
            $record = [ordered]@{path=$relative; exists=(Test-Path -LiteralPath $path -PathType Leaf)}
            if ($record.exists) {
                try {
                    $record['sha256'] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
                    if (-not $relative.EndsWith('.dll')) { Copy-Shared $path (Join-Path (Join-Path $root 'installed') $relative) }
                } catch { $errors += $relative + ': ' + $_.Exception.Message }
            }
            $records += [pscustomobject]$record
        }
        if ($engine) {
            foreach ($relative in @('build/animation-repair-report.json', '.ffr-existing-visions/state.json')) {
                $path = Join-Path $engine $relative
                if (Test-Path -LiteralPath $path -PathType Leaf) {
                    try { Copy-Shared $path (Join-Path (Join-Path $root 'engine') $relative) }
                    catch { $errors += $relative + ': ' + $_.Exception.Message }
                }
            }
        }
        $ready = @($trace | Where-Object { $_.Contains(' READY | ') }).Count
        [pscustomobject]@{schema=1;collectedUtc=[DateTime]::UtcNow.ToString('o');game=$game;engine=$engine;
            files=$records;errors=$errors;traceLines=$trace.Count;readyMarkers=$ready;
            sampled=$true;intervalMs=100;absenceProvesNoPlayback=$false} | ConvertTo-Json -Depth 8 |
            Set-Content -LiteralPath (Join-Path $root 'report.json') -Encoding UTF8
        $zip = $root + '.zip'
        [System.IO.Compression.ZipFile]::CreateFromDirectory($root, $zip)
        Write-Host ('Attach this ZIP in chat: ' + $zip) -ForegroundColor Green
        if (-not $ready) { Write-Host 'No trace READY marker found. Send the ZIP so we can check startup.' -ForegroundColor Yellow }
        Write-Output $zip
    }
} catch {
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
