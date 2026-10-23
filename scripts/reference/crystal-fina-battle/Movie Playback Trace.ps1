[CmdletBinding()]
param([ValidateSet('Install', 'Collect', 'Disable')][string]$Action = 'Install',
      [string]$GamePath, [string]$EnginePath, [switch]$NoPrompt)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
try {
    if (-not $GamePath) {
        foreach ($drive in @('G', 'D', 'C', 'E', 'F')) {
            $candidate = $drive + ':\Steam\steamapps\common\FINAL FANTASY RESONANCE'
            if (Test-Path -LiteralPath (Join-Path $candidate 'FFRS/Binaries/Win64') -PathType Container) {
                $GamePath = $candidate; break
            }
        }
        if (-not $NoPrompt) {
            $entered = Read-Host ('FULL Resonance folder (Enter for ' + $GamePath + ')')
            if ($entered) { $GamePath = $entered.Trim().Trim('"') }
        }
    }
    if (-not $GamePath -or (Split-Path -Leaf $GamePath) -match '(?i)\bDEMO\b' -or
        -not (Test-Path -LiteralPath (Join-Path $GamePath 'FFRS/Binaries/Win64') -PathType Container)) {
        throw 'Select the FULL Resonance folder containing FFRS\Binaries\Win64.'
    }
    $GamePath = (Resolve-Path -LiteralPath $GamePath).Path
    if ($Action -eq 'Collect') {
        & (Join-Path $PSScriptRoot 'Collect Fina Movie Diagnostics.ps1') -GamePath $GamePath -EnginePath $EnginePath -NoPrompt:$NoPrompt
        if (-not $?) { throw 'The movie diagnostics collector failed.' }
        return
    }
    $mods = Join-Path $GamePath 'FFRS/Binaries/Win64/ue4ss/Mods'
    if (-not (Test-Path -LiteralPath $mods -PathType Container)) {
        throw 'The installed Studio UE4SS Mods folder was not found. Keep the existing Studio mod installed.'
    }
    $folder = Join-Path $mods 'FFRStudioMovieTrace'
    $marker = Join-Path $folder 'studio-movie-observer.txt'
    $owner = 'FFR Studio read-only movie observer v1'
    if ((Test-Path -LiteralPath $folder) -and
        (-not (Test-Path -LiteralPath $marker -PathType Leaf) -or
         (Get-Content -LiteralPath $marker -Raw).Trim() -ne $owner)) {
        throw 'An unrecognized FFRStudioMovieTrace folder exists; it will not be changed.'
    }
    if ($Action -eq 'Disable') {
        $enabled = Join-Path $folder 'enabled.txt'
        if (Test-Path -LiteralPath $enabled -PathType Leaf) { Remove-Item -LiteralPath $enabled }
        Write-Host 'Movie observer disabled. Restart Resonance to stop the current observer.' -ForegroundColor Green
        return
    }
    $script = Join-Path $folder 'Scripts/main.lua'
    [void][IO.Directory]::CreateDirectory((Split-Path -Parent $script))
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'movie_trace.lua') -Destination $script -Force
    [IO.File]::WriteAllText($marker, $owner)
    [IO.File]::WriteAllText((Join-Path $folder 'enabled.txt'), '')
    Write-Host 'Read-only movie observer installed in its own UE4SS mod folder.' -ForegroundColor Green
    Write-Host 'Restart Resonance, use Crystal Fina resonance once, then press F8.'
    Write-Host 'Afterward run Collect Movie Trace.cmd and send the resulting ZIP.'
    Write-Host 'No Studio rebuild/install is needed. The observer only logs player/display state.'
} catch {
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
