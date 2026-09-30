function Read-VisionSpec([string]$Path) {
    $json = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    if (-not $json.TrimStart().StartsWith('[')) { throw 'The saved visions are not a list.' }
    # Windows PowerShell 5.1 emits the JSON array as one pipeline object;
    # PowerShell 7 emits its members. Normalize after assigning the result.
    $parsed = $json | ConvertFrom-Json
    $units = @()
    if ($null -ne $parsed) { $units = @($parsed) }
    $keys = @{}
    foreach ($unit in $units) {
        if ([string]::IsNullOrWhiteSpace($unit.key) -or [long]$unit.id -le 0 -or $keys.ContainsKey($unit.key)) {
            throw 'The saved visions contain an invalid or duplicate entry.'
        }
        $keys[$unit.key] = $true
    }
    return ,$units
}

function Move-VisionFile([string]$Pending, [string]$Destination, [string]$Backup) {
    if (Test-Path -LiteralPath $Destination) { [IO.File]::Replace($Pending, $Destination, $Backup) }
    else { [IO.File]::Move($Pending, $Destination) }
}

function Test-StudioDataIsOpen([string]$DataRoot) {
    $path = Join-Path $DataRoot 'app.lock'
    if (-not (Test-Path -LiteralPath $path)) { return $false }
    try {
        $file = [IO.File]::Open($path, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
        $file.Dispose()
        return $false
    } catch [IO.IOException] { return $true }
}

function Import-OfficialVisions([string]$Root, [string]$OfficialData) {
    $marker = Join-Path $Root 'official-visions-import.json'
    if (Test-Path -LiteralPath $marker) { return }
    if ([string]::IsNullOrEmpty($OfficialData)) {
        if ([string]::IsNullOrEmpty($env:LOCALAPPDATA)) { return }
        $OfficialData = Join-Path $env:LOCALAPPDATA 'FFR Vision Studio'
    }
    $OfficialData = [IO.Path]::GetFullPath($OfficialData)
    $testData = Get-PathInsideRoot $Root 'Studio Test Data/FFR Vision Studio'
    if ($OfficialData -eq $testData) { return }
    $sourceEngine = Join-Path $OfficialData 'engine'
    $sourceSpec = Join-Path $sourceEngine 'mods/EstherTsukiko/units.json'
    if (-not (Test-Path -LiteralPath $sourceSpec -PathType Leaf)) { return }
    if (Test-StudioDataIsOpen $OfficialData) {
        Write-Host 'Close official Studio, then reopen this shortcut to copy its saved visions.'
        return
    }
    $official = Read-VisionSpec $sourceSpec
    if ($official.Count -eq 0) { return }
    $testEngine = Join-Path $testData 'engine'
    $testSpec = Join-Path $testEngine 'mods/EstherTsukiko/units.json'
    if ((Test-Path -LiteralPath $testSpec) -and (Read-VisionSpec $testSpec).Count -gt 0) {
        Write-Host 'The test app already has saved visions. Keeping them without importing.'
        return
    }
    $pending = Join-Path $Root ('.visions-' + [Guid]::NewGuid().ToString('N'))
    [void][IO.Directory]::CreateDirectory($pending)
    try {
        # Keep the original JSON for recovery; never write to the official profile.
        [IO.File]::Copy($sourceSpec, (Join-Path $pending 'official-units.json'))
        [IO.File]::Copy((Join-Path $pending 'official-units.json'), (Join-Path $pending 'units.json'))
        $sourceAssets = Join-Path $sourceEngine 'units'
        if (Test-Path -LiteralPath $sourceAssets) {
            foreach ($file in Get-ChildItem -LiteralPath $sourceAssets -File -Recurse) {
                $relative = $file.FullName.Substring($sourceAssets.Length).TrimStart('\', '/')
                $destination = Get-PathInsideRoot (Join-Path $testEngine 'units') $relative
                if (Test-Path -LiteralPath $destination) {
                    if ((Get-FileHash -LiteralPath $destination).Hash -eq (Get-FileHash -LiteralPath $file.FullName).Hash) { continue }
                    throw 'A different test artwork file already exists. Keeping the test files.'
                }
                [void][IO.Directory]::CreateDirectory((Split-Path $destination -Parent))
                $copy = Join-Path $pending 'asset'
                [IO.File]::Copy($file.FullName, $copy)
                [IO.File]::Move($copy, $destination)
            }
        }
        $backup = Join-Path $Root 'Official Vision Import'
        [void][IO.Directory]::CreateDirectory($backup)
        [IO.File]::Copy((Join-Path $pending 'official-units.json'), (Join-Path $backup 'official-units.json'), $true)
        [void][IO.Directory]::CreateDirectory((Split-Path $testSpec -Parent))
        $layout = Join-Path $sourceEngine 'mods/EstherTsukiko/icon_layout.json'
        $testLayout = Join-Path $testEngine 'mods/EstherTsukiko/icon_layout.json'
        if ((Test-Path -LiteralPath $layout) -and -not (Test-Path -LiteralPath $testLayout)) { [IO.File]::Copy($layout, $testLayout) }
        Move-VisionFile (Join-Path $pending 'units.json') $testSpec (Join-Path $backup 'test-units-before-import.json')
        $record = [PSCustomObject]@{ source = $OfficialData; imported = $official.Count; completed_at = (Get-Date -Format o) }
        [IO.File]::WriteAllText((Join-Path $pending 'import.json'), ($record | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
        [IO.File]::Move((Join-Path $pending 'import.json'), $marker)
        Write-Host "Copied $($official.Count) visions from official Studio."
    } finally { if (Test-Path -LiteralPath $pending) { Remove-Item -LiteralPath $pending -Recurse -Force } }
}
