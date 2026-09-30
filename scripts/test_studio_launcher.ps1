$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../windows-test/Update Studio Test.ps1')
Add-Type -AssemblyName System.IO.Compression.FileSystem
$temporary = Join-Path ([IO.Path]::GetTempPath()) ('sephira-test-' + [Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($temporary)
$checks = 0

function Assert-Check($Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}
function New-Fixture([long]$Run, [string]$Branch = "Sephira's-Update") {
    $folder = Join-Path $temporary "fixture-$Run"
    [void][IO.Directory]::CreateDirectory((Join-Path $folder 'App'))
    [IO.File]::WriteAllText((Join-Path $folder 'App/FFR Vision Studio.exe'), "MZ-test-$Run")
    [IO.File]::WriteAllText((Join-Path $folder 'App/flutter_windows.dll'), 'fixture runtime')
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '../windows-test/Update Studio Test.ps1') -Destination $folder
    $build = [PSCustomObject]@{
        channel = 'sephira-test'; repository = 'biscoBen/FFR-Vison-Studio'; branch = $Branch
        commit = ('a' * 39) + ($Run % 10); run_id = $Run; build = 15
    }
    $build | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $folder 'test-build.json') -Encoding UTF8
    $zip = Join-Path $temporary "fixture-$Run.zip"
    [IO.Compression.ZipFile]::CreateFromDirectory($folder, $zip)
    $asset = [PSCustomObject]@{
        name = 'Sephira-Studio-Test.zip'; digest = 'sha256:' + (Get-FileHash $zip -Algorithm SHA256).Hash.ToLowerInvariant()
        browser_download_url = "https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-$Run/Sephira-Studio-Test.zip"
    }
    return [PSCustomObject]@{ Build = $build; Asset = $asset; Folder = $folder; Zip = $zip }
}

try {
    $first = New-Fixture 1
    $second = New-Fixture 2
    $root = Join-Path $temporary 'installed'
    Copy-Item -LiteralPath $first.Folder -Destination $root -Recurse
    $data = Join-Path $root 'Studio Test Data/FFR Vision Studio'
    [void][IO.Directory]::CreateDirectory($data)
    [IO.File]::WriteAllText((Join-Path $data 'units.json'), 'my test units')
    [IO.File]::WriteAllText((Join-Path $data 'settings.json'), 'my test settings')
    $getSecond = { $second }.GetNewClosure()
    $copySecond = { param($Url, $File) Copy-Item -LiteralPath $second.Zip -Destination $File }.GetNewClosure()
    $updated = Invoke-StudioTest -Root $root -NoLaunch -NoShortcut -GetUpdate $getSecond -Download $copySecond
    Assert-Check ($updated.run_id -eq 2) 'The new test build was not installed.'
    Assert-Check ((Get-Content -LiteralPath (Join-Path $data 'units.json') -Raw) -eq 'my test units') 'Updating changed unit data.'
    Assert-Check ((Get-Content -LiteralPath (Join-Path $data 'settings.json') -Raw) -eq 'my test settings') 'Updating changed settings.'
    Assert-Check (Test-Path -LiteralPath (Join-Path $root 'App/FFR Vision Studio.exe')) 'The previous app was removed.'
    $checks++; Write-Host 'PASS: update retains settings, units and previous app'

    $again = Invoke-StudioTest -Root $root -NoLaunch -NoShortcut -GetUpdate $getSecond -Download { throw 'Same version downloaded again.' }
    Assert-Check ($again.run_id -eq 2) 'The current version was not retained.'
    $checks++; Write-Host 'PASS: current version needs no download'

    $offline = Invoke-StudioTest -Root $root -NoLaunch -NoShortcut -GetUpdate { throw 'Offline fixture' }
    Assert-Check ($offline.run_id -eq 2) 'Offline startup lost the installed version.'
    $checks++; Write-Host 'PASS: offline startup uses installed version'

    $third = New-Fixture 3
    $bad = [PSCustomObject]@{ Build = $third.Build; Asset = [PSCustomObject]@{
        name = $third.Asset.name; browser_download_url = $third.Asset.browser_download_url; digest = 'sha256:' + ('0' * 64)
    } }
    $stateBefore = Get-Content -LiteralPath (Join-Path $root 'update-state.json') -Raw
    $badResult = Invoke-StudioTest -Root $root -NoLaunch -NoShortcut -GetUpdate { $bad }.GetNewClosure() -Download { param($Url,$File) Copy-Item $third.Zip $File }.GetNewClosure()
    Assert-Check ($badResult.run_id -eq 2) 'A damaged download changed the app.'
    Assert-Check ((Get-Content -LiteralPath (Join-Path $root 'update-state.json') -Raw) -eq $stateBefore) 'A damaged download changed the active state.'
    Assert-Check (-not (Test-Path -LiteralPath (Join-Path $root 'Versions/3'))) 'A damaged download was extracted.'
    Assert-Check ((Get-Content -LiteralPath (Join-Path $root 'update.log') -Raw) -match 'checksum') 'Checksum verification was not exercised.'
    $checks++; Write-Host 'PASS: checksum failure retains working version'

    $partial = Invoke-StudioTest -Root $root -NoLaunch -NoShortcut -GetUpdate { $third }.GetNewClosure() -Download { param($Url,$File) Set-Content $File 'partial'; throw 'Interrupted fixture' }
    Assert-Check ($partial.run_id -eq 2) 'An interrupted download changed the app.'
    Assert-Check (@(Get-ChildItem -LiteralPath $root -Filter '.update-*').Count -eq 0) 'Partial staging folders were retained.'
    $checks++; Write-Host 'PASS: interrupted download retains working version'

    $next = Invoke-StudioTest -Root $root -NoLaunch -NoShortcut -GetUpdate { $third }.GetNewClosure() -Download { param($Url,$File) Copy-Item $third.Zip $File }.GetNewClosure()
    Assert-Check ($next.run_id -eq 3) 'Replacing an existing installed state failed.'
    Assert-Check ((Get-InstalledTestBuild $root).run_id -eq 3) 'The next launch did not select the updated app and updater.'
    $checks++; Write-Host 'PASS: subsequent updates replace active state'

    $wrong = New-Fixture 4 'master'
    $release = [PSCustomObject]@{ draft = $false; prerelease = $true; tag_name = 'sephira-test-4'; target_commitish = $wrong.Build.commit; body = ($wrong.Build | ConvertTo-Json); assets = @($wrong.Asset) }
    $rejected = $false
    try { Select-TestRelease @($release) | Out-Null } catch { $rejected = $true }
    Assert-Check $rejected 'A master build entered the test update channel.'
    $checks++; Write-Host 'PASS: wrong branch is rejected'

    $valid = @($first, $second, $third) | ForEach-Object {
        [PSCustomObject]@{ draft = $false; prerelease = $true; tag_name = "sephira-test-$($_.Build.run_id)";
            target_commitish = $_.Build.commit; body = ($_.Build | ConvertTo-Json); assets = @($_.Asset) }
    }
    $chosen = Select-TestRelease (@($release) + $valid)
    Assert-Check ($chosen.Build.run_id -eq 3) 'The newest validated branch release was not selected.'
    $checks++; Write-Host 'PASS: newest validated branch release is selected'

    $unsafe = Join-Path $temporary 'unsafe.zip'
    $zip = [IO.Compression.ZipFile]::Open($unsafe, [IO.Compression.ZipArchiveMode]::Create)
    [void]$zip.CreateEntry('../outside.txt')
    $zip.Dispose()
    $rejected = $false
    try { Expand-CheckedTestZip $unsafe (Join-Path $root 'unsafe') ('sha256:' + (Get-FileHash $unsafe -Algorithm SHA256).Hash.ToLowerInvariant()) } catch { $rejected = $true }
    Assert-Check $rejected 'Unsafe ZIP entry was accepted.'
    Assert-Check (-not (Test-Path -LiteralPath (Join-Path $root 'outside.txt'))) 'Unsafe ZIP entry escaped extraction.'
    $checks++; Write-Host 'PASS: ZIP paths cannot escape test folder'

    $lockPath = Join-Path $data 'app.lock'
    $held = [IO.File]::Open($lockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    try {
        Assert-Check (Test-StudioIsOpen $root) 'An open app was not detected.'
        $blocked = Invoke-StudioTest -Root $root -NoLaunch -NoShortcut -GetUpdate { throw 'An open app checked for updates.' }
        Assert-Check ($null -eq $blocked) 'An open app allowed an update.'
    } finally { $held.Dispose() }
    Assert-Check (-not (Test-StudioIsOpen $root)) 'A closed app was treated as open.'
    $checks++; Write-Host 'PASS: running app is left alone'

    if ($env:GITHUB_ACTIONS -eq 'true' -and $env:OS -eq 'Windows_NT') {
        $desktopLink = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Sephira Studio Test.lnk'
        Set-TestDesktopShortcut $root (Get-PathInsideRoot $root $next.app)
        try {
            $shell = New-Object -ComObject WScript.Shell
            $link = $shell.CreateShortcut($desktopLink)
            Assert-Check ($link.TargetPath -eq (Join-Path $root 'Start Studio Test.cmd')) 'Desktop shortcut has the wrong target.'
            Assert-Check ($link.WorkingDirectory -eq $root) 'Desktop shortcut has the wrong working folder.'
            $checks++; Write-Host 'PASS: Windows desktop shortcut is created'
        } finally { Remove-Item -LiteralPath $desktopLink -Force }
    }

    Write-Host "$checks launcher checks passed."
} finally { Remove-Item -LiteralPath $temporary -Recurse -Force }
