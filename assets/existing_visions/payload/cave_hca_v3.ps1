param([string]$Source, [string]$Target, [string]$VgaudioDll = (Join-Path $PSScriptRoot 'VGAudio.dll'))
$ErrorActionPreference = 'Stop'
$dll = $VgaudioDll
Add-Type -Path $dll
$raw = [IO.File]::ReadAllBytes($Source)
if ($raw.Length -ge 6 -and $raw[4] -eq 3 -and $raw[5] -eq 0) {
    $references = @($dll)
    if ($PSVersionTable.PSEdition -eq 'Core') {
        $references += Get-ChildItem (Join-Path $PSHOME 'ref') -Filter '*.dll' | ForEach-Object FullName
    }
    Add-Type -Path (Join-Path $PSScriptRoot 'CaveHcaV3.cs') -ReferencedAssemblies $references
    [IO.File]::WriteAllBytes($Target, [FfrStudio.CaveHcaV3]::Decode($raw))
} else {
    $audio = [VGAudio.Containers.Hca.HcaReader]::new().ReadFormat($raw).ToPcm16()
    [IO.File]::WriteAllBytes($Target, [VGAudio.Containers.Wave.WaveWriter]::new().GetFile($audio))
}
