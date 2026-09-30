param([string]$Root = $PSScriptRoot, [switch]$NoLaunch, [switch]$NoShortcut)
$ErrorActionPreference = 'Stop'

function Assert-TestBuild($Build) {
    if ($Build.channel -ne 'sephira-test' -or $Build.branch -cne "Sephira's-Update" -or
        $Build.repository -ne 'biscoBen/FFR-Vison-Studio' -or
        $Build.commit -notmatch '^[0-9a-f]{40}$' -or [long]$Build.run_id -le 0) {
        throw 'This download is not a validated Sephira test build.'
    }
}

function Get-PathInsideRoot([string]$Root, [string]$Relative) {
    if ([string]::IsNullOrWhiteSpace($Relative) -or [IO.Path]::IsPathRooted($Relative)) {
        throw 'Invalid path in the test installation.'
    }
    $path = [IO.Path]::GetFullPath((Join-Path $Root $Relative))
    $prefix = [IO.Path]::GetFullPath($Root).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    if (-not $path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'A download path is outside the test folder.'
    }
    return $path
}

function Assert-TestFolder([string]$Folder, $Expected) {
    $build = Get-Content -LiteralPath (Join-Path $Folder 'test-build.json') -Raw | ConvertFrom-Json
    Assert-TestBuild $build
    if ($build.commit -ne $Expected.commit -or [long]$build.run_id -ne [long]$Expected.run_id) {
        throw 'The package does not match the selected update.'
    }
    foreach ($name in @('App/FFR Vision Studio.exe', 'App/flutter_windows.dll', 'Update Studio Test.ps1')) {
        if (-not (Test-Path -LiteralPath (Join-Path $Folder $name) -PathType Leaf)) {
            throw 'The test package is incomplete.'
        }
    }
}

function Get-InstalledTestBuild([string]$Root) {
    $statePath = Join-Path $Root 'update-state.json'
    if (Test-Path -LiteralPath $statePath) {
        try {
            $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
            Assert-TestBuild $state
            $app = Get-PathInsideRoot $Root $state.app
            $updater = Get-PathInsideRoot $Root $state.updater
            $folder = Split-Path (Split-Path $app -Parent) -Parent
            Assert-TestFolder $folder $state
            if (-not (Test-Path -LiteralPath $updater)) { throw 'The installed updater is missing.' }
            return $state
        } catch {
            Write-Host 'Recovering the bundled test version.'
        }
    }
    $manifest = Join-Path $Root 'test-build.json'
    if (-not (Test-Path -LiteralPath $manifest)) { return $null }
    $build = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
    Assert-TestFolder $Root $build
    return [PSCustomObject]@{
        channel = $build.channel; branch = $build.branch; repository = $build.repository
        commit = $build.commit; run_id = [long]$build.run_id
        app = 'App/FFR Vision Studio.exe'; updater = 'Update Studio Test.ps1'
    }
}

function Select-TestRelease($Releases) {
    $candidates = @()
    foreach ($release in $Releases) {
        if ($release.draft -or -not $release.prerelease -or $release.tag_name -notlike 'sephira-test-*') { continue }
        try {
            $build = $release.body | ConvertFrom-Json
            Assert-TestBuild $build
            if ($release.tag_name -ne "sephira-test-$($build.run_id)" -or $release.target_commitish -ne $build.commit) { continue }
            $assets = @($release.assets | Where-Object { $_.name -eq 'Sephira-Studio-Test.zip' })
            if ($assets.Count -ne 1 -or $assets[0].digest -notmatch '^sha256:[0-9a-f]{64}$') { continue }
            $uri = [Uri]$assets[0].browser_download_url
            $expectedPath = "/biscoBen/FFR-Vison-Studio/releases/download/$($release.tag_name)/Sephira-Studio-Test.zip"
            if ($uri.Scheme -ne 'https' -or $uri.Host -ne 'github.com' -or $uri.AbsolutePath -ne $expectedPath) { continue }
            $candidates += [PSCustomObject]@{ Build = $build; Asset = $assets[0] }
        } catch { continue }
    }
    $selected = $candidates | Sort-Object { [long]$_.Build.run_id } -Descending | Select-Object -First 1
    if ($null -eq $selected) { throw 'There is no tested branch update available yet.' }
    return $selected
}

function Get-PublishedTestRelease {
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    $headers = @{ 'User-Agent' = 'Sephira-Studio-Test'; Accept = 'application/vnd.github+json' }
    $releases = Invoke-RestMethod -Uri 'https://api.github.com/repos/biscoBen/FFR-Vison-Studio/releases?per_page=100' -Headers $headers -TimeoutSec 15
    return Select-TestRelease $releases
}

function Expand-CheckedTestZip([string]$Archive, [string]$Destination, [string]$Digest) {
    if ($Digest -notmatch '^sha256:[0-9a-f]{64}$' -or
        (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash -ine $Digest.Substring(7)) {
        throw 'The download checksum did not match. Keeping the installed version.'
    }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::OpenRead($Archive)
    try {
        # Check every entry before writing any of them.
        foreach ($entry in $zip.Entries) {
            $relative = $entry.FullName.Replace('\', '/')
            if ($relative.Contains(':') -or ($relative -split '/') -contains '..') { throw 'Unsafe path in the test download.' }
            [void](Get-PathInsideRoot $Destination $relative)
        }
        foreach ($entry in $zip.Entries) {
            $path = Get-PathInsideRoot $Destination $entry.FullName.Replace('\', '/')
            if ($entry.FullName.EndsWith('/') -or $entry.FullName.EndsWith('\')) {
                [void][IO.Directory]::CreateDirectory($path)
            } else {
                [void][IO.Directory]::CreateDirectory((Split-Path $path -Parent))
                [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $path, $false)
            }
        }
    } finally { $zip.Dispose() }
}

function Install-TestUpdate([string]$Root, $Update, [scriptblock]$Download) {
    $relativeFolder = "Versions/$($Update.Build.run_id)"
    $versionFolder = Get-PathInsideRoot $Root $relativeFolder
    if (-not (Test-Path -LiteralPath $versionFolder)) {
        $temporary = Join-Path $Root ('.update-' + [Guid]::NewGuid().ToString('N'))
        [void][IO.Directory]::CreateDirectory($temporary)
        try {
            $archive = Join-Path $temporary 'download.zip'
            & $Download $Update.Asset.browser_download_url $archive
            $staging = Join-Path $temporary 'package'
            Expand-CheckedTestZip $archive $staging $Update.Asset.digest
            Assert-TestFolder $staging $Update.Build
            [void][IO.Directory]::CreateDirectory((Split-Path $versionFolder -Parent))
            Move-Item -LiteralPath $staging -Destination $versionFolder
        } finally {
            if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Recurse -Force }
        }
    } else { Assert-TestFolder $versionFolder $Update.Build }
    $state = [PSCustomObject]@{
        channel = $Update.Build.channel; branch = $Update.Build.branch; repository = $Update.Build.repository
        commit = $Update.Build.commit; run_id = [long]$Update.Build.run_id
        app = "$relativeFolder/App/FFR Vision Studio.exe"
        updater = "$relativeFolder/Update Studio Test.ps1"
    }
    $statePath = Join-Path $Root 'update-state.json'
    $temporaryState = Join-Path $Root ('.state-' + [Guid]::NewGuid().ToString('N'))
    try {
        [IO.File]::WriteAllText($temporaryState, ($state | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
        if (Test-Path -LiteralPath $statePath) { [IO.File]::Replace($temporaryState, $statePath, (Join-Path $Root 'update-state.previous.json')) }
        else { Move-Item -LiteralPath $temporaryState -Destination $statePath }
    } finally {
        if (Test-Path -LiteralPath $temporaryState) { Remove-Item -LiteralPath $temporaryState }
    }
    return $state
}

function Test-StudioIsOpen([string]$Root) {
    $path = Join-Path $Root 'Studio Test Data/FFR Vision Studio/app.lock'
    if (-not (Test-Path -LiteralPath $path)) { return $false }
    try {
        $file = [IO.File]::Open($path, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
        $file.Dispose()
        return $false
    } catch [IO.IOException] { return $true }
}

function Set-TestDesktopShortcut([string]$Root, [string]$App) {
    if ($env:OS -ne 'Windows_NT') { return }
    $desktop = [Environment]::GetFolderPath('Desktop')
    if ([string]::IsNullOrEmpty($desktop)) { return }
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut((Join-Path $desktop 'Sephira Studio Test.lnk'))
    $shortcut.TargetPath = Join-Path $Root 'Start Studio Test.cmd'
    $shortcut.WorkingDirectory = $Root
    $shortcut.IconLocation = "$App,0"
    $shortcut.Save()
}

function Invoke-StudioTest([string]$Root, [switch]$NoLaunch, [switch]$NoShortcut,
    [scriptblock]$GetUpdate = { Get-PublishedTestRelease },
    [scriptblock]$Download = { param($Url, $File) Invoke-WebRequest -Uri $Url -OutFile $File -UseBasicParsing -TimeoutSec 120 }) {
    $Root = [IO.Path]::GetFullPath($Root)
    [void][IO.Directory]::CreateDirectory($Root)
    $lock = $null
    try {
        try { $lock = [IO.File]::Open((Join-Path $Root 'update.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None) }
        catch [IO.IOException] { Write-Host 'Studio Test is already starting.'; return }
        if (Test-StudioIsOpen $Root) { Write-Host 'Studio Test is already open. Close it before checking for another update.'; return }
        $current = Get-InstalledTestBuild $Root
        Write-Host 'Checking for Studio Test updates...'
        try {
            $update = & $GetUpdate
            Assert-TestBuild $update.Build
            if ($null -eq $current -or [long]$update.Build.run_id -gt [long]$current.run_id) {
                Write-Host 'Installing the tested update...'
                $current = Install-TestUpdate $Root $update $Download
            }
        } catch {
            Add-Content -LiteralPath (Join-Path $Root 'update.log') -Value ("$(Get-Date -Format o) $($_.Exception.Message)")
            if ($null -eq $current) { throw }
            Write-Host 'The update could not be retrieved. Using the installed test version.'
        }
        $app = Get-PathInsideRoot $Root $current.app
        if (-not $NoShortcut) {
            try { Set-TestDesktopShortcut $Root $app }
            catch { Write-Host 'The desktop shortcut could not be created. You can still use Start Studio Test.cmd.' }
        }
        if (-not $NoLaunch) {
            $previousData = $env:LOCALAPPDATA
            try {
                $env:LOCALAPPDATA = Join-Path $Root 'Studio Test Data'
                Write-Host 'Starting Studio Test...'
                Start-Process -FilePath $app -WorkingDirectory (Split-Path $app -Parent)
            } finally { $env:LOCALAPPDATA = $previousData }
        }
        return $current
    } finally { if ($null -ne $lock) { $lock.Dispose() } }
}

if ($MyInvocation.InvocationName -ne '.') {
    try { [void](Invoke-StudioTest -Root $Root -NoLaunch:$NoLaunch -NoShortcut:$NoShortcut) }
    catch { Write-Host "Studio Test could not start: $($_.Exception.Message)"; exit 1 }
}
