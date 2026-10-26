# Windows PowerShell 5.1. Copies saves and the roster for a read-only ownership audit.
[CmdletBinding()]
param([string]$SavePath, [string]$StudioPath, [string]$GamePath,
      [string]$OutputRoot, [switch]$NoPrompt)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

function Assert-PlainPath([string]$Path) {
    $part = [IO.Path]::GetFullPath($Path)
    while ($part) {
        if (Test-Path -LiteralPath $part) {
            $item = Get-Item -LiteralPath $part -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw ('Linked paths are not collected: ' + $part) }
        }
        $parent = [IO.Path]::GetDirectoryName($part)
        if ($parent -eq $part) { break }
        $part = $parent
    }
}
function Find-Engine([string]$Candidate) {
    if (-not $Candidate) { return $null }
    foreach ($suffix in @('', 'engine', 'Studio Test Data/FFR Vision Studio/engine')) {
        $path = $Candidate.Trim().Trim('"')
        if ($suffix) { $path = Join-Path $path $suffix }
        if (Test-Path -LiteralPath (Join-Path $path 'mods/EstherTsukiko/units.json') -PathType Leaf) {
            return [IO.Path]::GetFullPath($path)
        }
    }
    return $null
}
function Copy-ReportFile([string]$Source, [string]$Relative, [long]$Limit) {
    Assert-PlainPath $Source
    $file = Get-Item -LiteralPath $Source
    if ($file.Length -gt $Limit) { throw ('File exceeds the collection limit: ' + $file.Name) }
    if ($script:total + $file.Length -gt 67108864) { throw 'Collection exceeds 64 MiB; select just the affected save with -SavePath.' }
    $target = Join-Path $script:root $Relative
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target))
    [IO.File]::Copy($file.FullName, $target, $false)
    $script:total += $file.Length
    $script:files += [pscustomobject]@{file=$Relative; bytes=$file.Length;
        modifiedUtc=$file.LastWriteTimeUtc.ToString('o'); sha256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()}
}

try {
    Write-Host 'Vision save ownership check (read-only)' -ForegroundColor Cyan
    Write-Host 'Close Resonance before running this helper. You do not need to save again.'
    Write-Host 'If you want a new save, use a separate slot and keep the save from before the issue.'
    Write-Host 'The ZIP contains copies of game saves and your vision roster. No save or installed mod is changed.'
    if (Get-Process -Name 'FFRS-Win64-Shipping' -ErrorAction SilentlyContinue) { throw 'Close Resonance first so the save copy is consistent.' }
    $engine = Find-Engine $StudioPath
    if ($StudioPath -and -not $engine) { throw 'Studio folder has no engine/mods/EstherTsukiko/units.json.' }
    if (-not $engine) {
        $candidates = @($PSScriptRoot, (Split-Path $PSScriptRoot -Parent), (Get-Location).Path)
        if ($env:LOCALAPPDATA) { $candidates += Join-Path $env:LOCALAPPDATA 'FFR Vision Studio' }
        if ($env:USERPROFILE) {
            $candidates += Join-Path $env:USERPROFILE 'Desktop/Sephira-Studio-Test'
            $candidates += Join-Path $env:USERPROFILE 'Downloads/Sephira-Studio-Test'
        }
        foreach ($candidate in $candidates) { $engine = Find-Engine $candidate; if ($engine) { break } }
    }
    if (-not $GamePath -and $engine) {
        $config = Join-Path $engine 'config.json'
        if (Test-Path -LiteralPath $config -PathType Leaf) {
            $value = Get-Content -LiteralPath $config -Raw | ConvertFrom-Json
            $property = $value.PSObject.Properties['gameRoot']
            if ($null -ne $property) { $GamePath = [string]$property.Value }
        }
    }
    $saveRoots = @()
    if ($SavePath) { $saveRoots += [IO.Path]::GetFullPath($SavePath.Trim().Trim('"')) }
    else {
        if ($env:LOCALAPPDATA) { $saveRoots += Join-Path $env:LOCALAPPDATA 'FFRS/Saved/SaveGames' }
        if ($GamePath) { $saveRoots += Join-Path $GamePath 'FFRS/Saved/SaveGames' }
    }
    $sources = @()
    foreach ($path in @($saveRoots | Select-Object -Unique)) {
        if (-not (Test-Path -LiteralPath $path)) { continue }
        Assert-PlainPath $path
        if (Test-Path -LiteralPath $path -PathType Leaf) { $sources += Get-Item -LiteralPath $path }
        else {
            # Only descend ordinary directories under Resonance's save folder.
            $queue = New-Object 'Collections.Generic.Queue[string]'
            $queue.Enqueue($path)
            while ($queue.Count -gt 0) {
                $folder = $queue.Dequeue()
                foreach ($entry in @(Get-ChildItem -LiteralPath $folder -Force)) {
                    if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { continue }
                    if ($entry.PSIsContainer) { $queue.Enqueue($entry.FullName) }
                    elseif ($entry.Extension -in @('.sav', '.bin', '.dat')) { $sources += $entry }
                }
            }
        }
    }
    $sources = @($sources | Sort-Object FullName -Unique)
    if ($sources.Count -eq 0 -and -not $NoPrompt) {
        $entered = Read-Host 'Save folder was not found. Paste the path to the affected save file or its SaveGames folder'
        if ($entered) {
            & $PSCommandPath -SavePath $entered -StudioPath $engine -GamePath $GamePath -OutputRoot $OutputRoot -NoPrompt
            exit $LASTEXITCODE
        }
    }
    if ($sources.Count -eq 0) { throw 'No save files found. Run with -SavePath pointing to the affected save or SaveGames folder.' }
    if (-not $OutputRoot) { $OutputRoot = Join-Path $env:USERPROFILE 'Downloads/FFR Mod' }
    $OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
    # Never create output inside a save folder, Studio, or the game.
    foreach ($protected in @($saveRoots) + @($engine, $GamePath)) {
        if (-not $protected) { continue }
        if (Test-Path -LiteralPath $protected -PathType Leaf) { $protected = Split-Path $protected -Parent }
        $protected = [IO.Path]::GetFullPath($protected).TrimEnd('\', '/')
        if ($OutputRoot -eq $protected -or $OutputRoot.StartsWith($protected + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Choose an output folder outside the save, Studio and game folders.'
        }
    }
    Assert-PlainPath $OutputRoot
    $tag = 'Vision-Save-Check-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,6)
    $script:root = Join-Path $OutputRoot $tag
    [void][IO.Directory]::CreateDirectory($script:root)
    $script:files = @(); $script:total = 0
    for ($i = 0; $i -lt $sources.Count; $i++) {
        Copy-ReportFile $sources[$i].FullName ('saves/{0:D3}-{1}' -f $i, $sources[$i].Name) 33554432
    }
    if ($engine) { Copy-ReportFile (Join-Path $engine 'mods/EstherTsukiko/units.json') 'roster/units.json' 16777216 }
    [ordered]@{schema=1; purpose='Read-only vision ownership audit'; saveCount=$sources.Count;
        rosterIncluded=[bool]$engine; rosterSource=$engine; files=$script:files} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $script:root 'report.json') -Encoding UTF8
    if ($engine) { Write-Host ('Roster copied from ' + $engine + '. Check this is your active Studio folder.') }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = $script:root + '.zip'
    [IO.Compression.ZipFile]::CreateFromDirectory($script:root, $archive)
    Write-Host ('Created ' + $archive) -ForegroundColor Green
    Write-Host 'Upload that ZIP in this conversation. This collector does not interpret ownership or repair anything.'
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
