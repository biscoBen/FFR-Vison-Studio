$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../windows-test/Update Studio Test.ps1')
$temporary = Join-Path ([IO.Path]::GetTempPath()) ('vision-import-' + [Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($temporary)
$checks = 0

function Assert-Import($Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Write-ImportJson([string]$Path, $Value) {
    [void][IO.Directory]::CreateDirectory((Split-Path $Path -Parent))
    [IO.File]::WriteAllText($Path, (ConvertTo-Json -InputObject $Value -Depth 100), [Text.UTF8Encoding]::new($false))
}
function New-Vision([string]$Key, [long]$Id) {
    $skill = 445000 + ($Id - 13100) * 100
    # Include nested recipes, Unicode and references that must remain unchanged.
    return @"
{"key":"$Key","en":"$Key","jp":"\u30a8\u30b9\u30bf\u30fc","id":$Id,"sort":$($Id+70),
 "command":{"id":$(320+$Id-13500)},"master":{"id":$($Id*100)},
 "ffbe":{"dir":"units/custom/$Key/sprites/990001","id":"990001","baseDir":"units/custom/$Key/sprites/990000"},
 "lb_custom":{"ffbe_lb":"units/custom/$Key/resonance.json","set":{"hitCount":12}},
 "stats":{"Attack":29},"skills":{"$skill":{"from":445020,"set":{"magnification":125}}},
 "awakening":[[["ActiveSkill",$skill],["PassiveSkill",1250]],[],[],[]],
 "synchro":[[],[],[],[],[],[],[],[],[],[["MasterSkill",$($Id*100)]]],
 "ffbeMap":{"skills":{"12345":$skill}}}
"@ | ConvertFrom-Json
}
function New-Official([string]$Name, $Units) {
    $source = Join-Path $temporary $Name
    Write-ImportJson (Join-Path $source 'engine/mods/EstherTsukiko/units.json') @($Units)
    Write-ImportJson (Join-Path $source 'engine/mods/EstherTsukiko/icon_layout.json') @{ scale = 1.25 }
    Write-ImportJson (Join-Path $source 'settings.json') @{ game = 'official game'; theme = 'dark' }
    Write-ImportJson (Join-Path $source 'engine/config.json') @{ gameRoot = 'official game' }
    foreach ($unit in $Units) {
        $assets = Join-Path $source "engine/units/custom/$($unit.key)"
        [void][IO.Directory]::CreateDirectory((Join-Path $assets 'sprites/990001'))
        [IO.File]::WriteAllText((Join-Path $assets 'sprites/990001/sheet.png'), "art-$($unit.key)")
        Write-ImportJson (Join-Path $assets 'resonance.json') @{ hitFrames = @(12,24) }
    }
    return $source
}
function New-TestRoot([string]$Name) {
    $root = Join-Path $temporary $Name
    [void][IO.Directory]::CreateDirectory($root)
    return $root
}
function Spec-Path([string]$Root) { return Join-Path $Root 'Studio Test Data/FFR Vision Studio/engine/mods/EstherTsukiko/units.json' }

try {
    $source = New-Official 'official' @((New-Vision 'esther' 13500))
    $sourceSpec = Join-Path $source 'engine/mods/EstherTsukiko/units.json'
    $sourceHash = (Get-FileHash $sourceSpec).Hash
    $root = New-TestRoot 'empty-test'
    Import-OfficialVisions $root $source
    $imported = Read-VisionSpec (Spec-Path $root)
    Assert-Import ($imported.Count -eq 1 -and $imported[0].id -eq 13500) 'A single official vision was not copied as a list.'
    Assert-Import ($imported[0].jp -eq (New-Vision 'esther' 13500).jp -and $imported[0].awakening.Count -eq 4) 'Unicode or nested vision data was changed.'
    Assert-Import ((Get-FileHash $sourceSpec).Hash -eq $sourceHash) 'The official vision file was modified.'
    Assert-Import ((Get-FileHash (Spec-Path $root)).Hash -eq $sourceHash) 'The copied vision definitions changed.'
    Assert-Import ((Get-Content (Join-Path $root 'Studio Test Data/FFR Vision Studio/engine/units/custom/esther/sprites/990001/sheet.png') -Raw) -eq 'art-esther') 'The vision artwork was not copied.'
    Assert-Import (Test-Path (Join-Path $root 'Studio Test Data/FFR Vision Studio/engine/units/custom/esther/resonance.json')) 'Custom resonance data was not copied.'
    Assert-Import (Test-Path (Join-Path $root 'Studio Test Data/FFR Vision Studio/engine/mods/EstherTsukiko/icon_layout.json')) 'Icon layout was not copied.'
    Assert-Import (-not (Test-Path (Join-Path $root 'Studio Test Data/FFR Vision Studio/settings.json'))) 'Official settings were copied.'
    Assert-Import (-not (Test-Path (Join-Path $root 'Studio Test Data/FFR Vision Studio/engine/config.json'))) 'Official game configuration was copied.'
    $checks++; Write-Host 'PASS: complete visions copy without changing the official profile or test game settings'

    $manySource = New-Official 'multiple-official' @((New-Vision 'esther' 13500), (New-Vision 'tsukiko' 13501))
    $manyRoot = New-TestRoot 'multiple-test'
    Import-OfficialVisions $manyRoot $manySource
    $many = Read-VisionSpec (Spec-Path $manyRoot)
    Assert-Import ($many.Count -eq 2 -and $many[0].key -eq 'esther' -and $many[1].key -eq 'tsukiko') 'A saved vision list was nested or its members were lost.'
    $checks++; Write-Host 'PASS: multiple saved visions remain a flat list'

    $imported[0].stats.Attack = 77
    Write-ImportJson (Spec-Path $root) @($imported)
    Write-ImportJson $sourceSpec @((New-Vision 'later' 13501))
    Import-OfficialVisions $root $source
    $again = Read-VisionSpec (Spec-Path $root)
    Assert-Import ($again.Count -eq 1 -and $again[0].stats.Attack -eq 77) 'A later launch reimported or replaced test edits.'
    $checks++; Write-Host 'PASS: successful import runs only once'

    $existingSource = New-Official 'existing-official' @((New-Vision 'official' 13500))
    $existingRoot = New-TestRoot 'existing-test'
    Write-ImportJson (Spec-Path $existingRoot) @((New-Vision 'testonly' 13500))
    $beforeHash = (Get-FileHash (Spec-Path $existingRoot)).Hash
    Import-OfficialVisions $existingRoot $existingSource
    Assert-Import ((Get-FileHash (Spec-Path $existingRoot)).Hash -eq $beforeHash) 'The import replaced a nonempty test list.'
    Assert-Import (-not (Test-Path (Join-Path $existingRoot 'official-visions-import.json'))) 'An import into a nonempty list was marked complete.'
    $checks++; Write-Host 'PASS: import does not replace a nonempty test list'

    $prepared = New-TestRoot 'prepared-empty-test'
    Write-ImportJson (Spec-Path $prepared) @()
    $emptyHash = (Get-FileHash (Spec-Path $prepared)).Hash
    $settings = Join-Path $prepared 'Studio Test Data/FFR Vision Studio/settings.json'
    Write-ImportJson $settings @{ game = 'copied game'; theme = 'light' }
    $settingsHash = (Get-FileHash $settings).Hash
    Import-OfficialVisions $prepared $existingSource
    Assert-Import ((Read-VisionSpec (Spec-Path $prepared)).Count -eq 1) 'An existing empty list was not populated.'
    Assert-Import ((Get-FileHash $settings).Hash -eq $settingsHash) 'Existing test settings were changed.'
    Assert-Import ((Get-FileHash (Join-Path $prepared 'Official Vision Import/test-units-before-import.json')).Hash -eq $emptyHash) 'The previous empty list was not backed up.'
    $checks++; Write-Host 'PASS: an existing empty test list is populated and settings are retained'

    $lockedSource = New-Official 'open-official' @((New-Vision 'locked' 13500))
    $locked = New-TestRoot 'locked-test'
    $held = [IO.File]::Open((Join-Path $lockedSource 'app.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    try { Import-OfficialVisions $locked $lockedSource }
    finally { $held.Dispose() }
    Assert-Import (-not (Test-Path (Spec-Path $locked))) 'Visions were copied while official Studio was open.'
    Import-OfficialVisions $locked $lockedSource
    Assert-Import ((Read-VisionSpec (Spec-Path $locked)).Count -eq 1) 'The import did not retry after official Studio closed.'
    $checks++; Write-Host 'PASS: open official Studio defers import until it closes'

    $missing = New-TestRoot 'missing-test'
    Import-OfficialVisions $missing (Join-Path $temporary 'no-official-profile')
    $emptySource = New-Official 'empty-official' @()
    Import-OfficialVisions $missing $emptySource
    Assert-Import (-not (Test-Path (Join-Path $missing 'official-visions-import.json'))) 'Missing or empty official data prevented a later import.'
    Write-ImportJson (Join-Path $emptySource 'engine/mods/EstherTsukiko/units.json') @((New-Vision 'later' 13500))
    Import-OfficialVisions $missing $emptySource
    Assert-Import ((Read-VisionSpec (Spec-Path $missing)).Count -eq 1) 'Visions appearing later were not imported.'
    $checks++; Write-Host 'PASS: missing or empty official data can be imported later'

    $badSource = New-Official 'invalid-official' @((New-Vision 'bad' 13500))
    [IO.File]::WriteAllText((Join-Path $badSource 'engine/mods/EstherTsukiko/units.json'), '{broken')
    $badRoot = New-TestRoot 'invalid-test'
    Write-ImportJson (Spec-Path $badRoot) @((New-Vision 'safe' 13500))
    $safeHash = (Get-FileHash (Spec-Path $badRoot)).Hash
    $rejected = $false
    try { Import-OfficialVisions $badRoot $badSource } catch { $rejected = $true }
    Assert-Import ($rejected -and (Get-FileHash (Spec-Path $badRoot)).Hash -eq $safeHash) 'Invalid official data changed the test list.'
    Assert-Import (-not (Test-Path (Join-Path $badRoot 'official-visions-import.json'))) 'A failed import was marked complete.'
    $checks++; Write-Host 'PASS: invalid official data retains test visions and permits retry'

    $retrySource = New-Official 'retry-official' @((New-Vision 'retry' 13500))
    $retry = New-TestRoot 'retry-test'
    $assets = Join-Path $retry 'Studio Test Data/FFR Vision Studio/engine/units'
    [void][IO.Directory]::CreateDirectory((Split-Path $assets -Parent))
    [IO.File]::WriteAllText($assets, 'blocked destination')
    Write-ImportJson (Spec-Path $retry) @()
    $retryHash = (Get-FileHash (Spec-Path $retry)).Hash
    $rejected = $false
    try { Import-OfficialVisions $retry $retrySource } catch { $rejected = $true }
    Assert-Import ($rejected -and (Get-FileHash (Spec-Path $retry)).Hash -eq $retryHash) 'A failed asset copy changed the test list.'
    Assert-Import (-not (Test-Path (Join-Path $retry 'official-visions-import.json'))) 'An incomplete asset copy was marked complete.'
    Assert-Import (@(Get-ChildItem $retry -Filter '.visions-*').Count -eq 0) 'Failed import staging was retained.'
    Remove-Item -LiteralPath $assets
    Import-OfficialVisions $retry $retrySource
    Assert-Import ((Read-VisionSpec (Spec-Path $retry)).Count -eq 1) 'The import could not recover after a copy failure.'
    $checks++; Write-Host 'PASS: asset copy failure keeps the vision list and a later launch recovers'

    $defaultRoot = New-TestRoot 'default-source-test'
    $local = Join-Path $temporary 'local-app-data'
    [void][IO.Directory]::CreateDirectory($local)
    Copy-Item -LiteralPath $retrySource -Destination (Join-Path $local 'FFR Vision Studio') -Recurse
    $previous = $env:LOCALAPPDATA
    try { $env:LOCALAPPDATA = $local; Import-OfficialVisions -Root $defaultRoot }
    finally { $env:LOCALAPPDATA = $previous }
    Assert-Import ((Read-VisionSpec (Spec-Path $defaultRoot)).Count -eq 1) 'The default official data location was not detected.'
    $checks++; Write-Host 'PASS: launcher finds official visions in Windows Local AppData'

    Write-Host "$checks vision import checks passed."
} finally { Remove-Item -LiteralPath $temporary -Recurse -Force }
