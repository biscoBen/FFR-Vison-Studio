[CmdletBinding()]
param([string]$ReferenceFolder, [string]$OutputRoot)
$ErrorActionPreference = 'Stop'
function New-UploadZip([string]$Destination, [object[]]$Segments) {
    $stream = [System.IO.File]::Open($Destination, [System.IO.FileMode]::CreateNew)
    $archive = $null
    try {
        $archive = New-Object System.IO.Compression.ZipArchive -ArgumentList @(
            $stream, [System.IO.Compression.ZipArchiveMode]::Create, $true)
        $buffer = New-Object byte[] 65536
        foreach ($segment in $Segments) {
            $entry = $archive.CreateEntry($segment.entry, [System.IO.Compression.CompressionLevel]::Optimal)
            $target = $null; $source = $null
            try {
                $target = $entry.Open()
                $source = [System.IO.File]::Open($segment.source, [System.IO.FileMode]::Open,
                    [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
                [void]$source.Seek($segment.offset, [System.IO.SeekOrigin]::Begin)
                $remaining = [long]$segment.bytes
                while ($remaining -gt 0) {
                    $read = $source.Read($buffer, 0, [int][Math]::Min($buffer.Length, $remaining))
                    if ($read -le 0) { throw ('Source file ended early: ' + $segment.source) }
                    $target.Write($buffer, 0, $read)
                    $remaining -= $read
                }
            } finally {
                if ($null -ne $source) { $source.Dispose() }
                if ($null -ne $target) { $target.Dispose() }
            }
        }
    } finally {
        if ($null -ne $archive) { $archive.Dispose() }
        $stream.Dispose()
    }
}

try {
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $base = Join-Path $env:USERPROFILE 'Downloads\FFR Mod'
    if (-not $ReferenceFolder) {
        $latest = Get-ChildItem -LiteralPath $base -Directory -Filter 'Shrine-World-Placement-*' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        $prompt = 'Folder that contains the big world-placement extraction'
        if ($latest) { $prompt += ' (Enter for ' + $latest.FullName + ')' }
        $ReferenceFolder = Read-Host $prompt
        if (-not $ReferenceFolder -and $latest) { $ReferenceFolder = $latest.FullName }
    }
    $ReferenceFolder = (Resolve-Path -LiteralPath $ReferenceFolder.Trim().Trim('"')).Path
    $legacy = Join-Path $ReferenceFolder 'legacy'
    if (-not (Test-Path -LiteralPath $legacy -PathType Container)) { throw 'Select the extracted folder containing legacy, not the large ZIP.' }
    if (-not $OutputRoot) { $OutputRoot = $base }
    [void][IO.Directory]::CreateDirectory($OutputRoot)
    $tag = 'Shrine-World-Small-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
    $work = Join-Path $OutputRoot $tag
    [void][IO.Directory]::CreateDirectory($work)
    $files = @()
    foreach ($file in (Get-ChildItem -LiteralPath $legacy -Recurse -File)) {
        $relative = $file.FullName.Substring($legacy.Length).TrimStart('\', '/').Replace('\', '/')
        $world = $relative -match '^FFRS/Content/Map/Wld/(?:GD|EV|(?:04Dir|05Old|06Zol|07Mys)/EV)/[^/]+\.(?:umap|uexp)$'
        $shrine = $relative -match '^FFRS/Content/Map/Com/00Com/00Com_2(?:0[0-9]|1[0-8]|2[0-9]|3[0-7])/(?:[^/]+_PL|(?:GD|EV)/[^/]+)\.(?:umap|uexp)$'
        $area = $relative -match '^FFRS/Content/Datatable/Map/(?:Area/DA_MapArea|DA_MapLandmark)\.(?:uasset|uexp)$'
        if ($world -or $shrine -or $area) { $files += $file }
    }
    foreach ($name in @('Mappings.usmap', 'game-identity.json')) {
        $candidate = Join-Path $ReferenceFolder $name
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { $files += Get-Item -LiteralPath $candidate }
    }
    if ($files.Count -lt 5) { throw 'Too few map files found. Select the full successful extraction folder.' }
    $segments = @(); $ledgerFiles = @(); $index = 0
    foreach ($file in $files) {
        $entry = $file.FullName.Substring($ReferenceFolder.Length).TrimStart('\', '/').Replace('\', '/')
        if ($file.Length -le 20MB) {
            $segments += [PSCustomObject]@{ source = $file.FullName; entry = $entry; offset = 0L; bytes = $file.Length }
        } else {
            $parts = @(); $offset = 0L; $part = 0
            while ($offset -lt $file.Length) {
                $bytes = [long][Math]::Min(20MB, $file.Length - $offset)
                $chunk = '_reference_chunks/' + $index.ToString('000000') + '/' + $part.ToString('000000') + '.bin'
                $segments += [PSCustomObject]@{ source = $file.FullName; entry = $chunk; offset = $offset; bytes = $bytes }
                $parts += [PSCustomObject]@{ path = $chunk; bytes = $bytes }
                $offset += $bytes; $part++
            }
            $ledgerFiles += [PSCustomObject]@{ path = $entry; bytes = $file.Length; sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant(); parts = @($parts) }
        }
        $index++
    }
    $ledger = Join-Path $work 'split-files.json'
    [ordered]@{ schema = 1; files = @($ledgerFiles) } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ledger -Encoding UTF8
    $segments += [PSCustomObject]@{ source = $ledger; entry = 'split-files.json'; offset = 0L; bytes = (Get-Item -LiteralPath $ledger).Length }
    $batch = @(); $bytes = 0L; $part = 1
    foreach ($segment in $segments) {
        if ($batch.Count -gt 0 -and $bytes + $segment.bytes -gt 22MB) {
            New-UploadZip (Join-Path $OutputRoot ($tag + '-' + $part.ToString('000') + '.zip')) $batch
            $batch = @(); $bytes = 0L; $part++
        }
        $batch += $segment; $bytes += $segment.bytes
    }
    if ($batch.Count) { New-UploadZip (Join-Path $OutputRoot ($tag + '-' + $part.ToString('000') + '.zip')) $batch }
    Write-Host ('Selected ' + $files.Count + ' map/dependency files; omitted backgrounds and lighting builds.') -ForegroundColor Green
    Write-Host ('Attach all ' + $tag + '-*.zip from:')
    Write-Host $OutputRoot -ForegroundColor Cyan
} catch { Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red; exit 1 }
