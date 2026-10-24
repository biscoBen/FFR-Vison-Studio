param(
    [Parameter(Mandatory=$true)][string]$InputWave,
    [Parameter(Mandatory=$true)][string]$OutputAdx,
    [Parameter(Mandatory=$true)][string]$VgaudioDll
)
$ErrorActionPreference = 'Stop'
Add-Type -Path $VgaudioDll
$audio = [VGAudio.Containers.Wave.WaveReader]::new().Read([IO.File]::ReadAllBytes($InputWave))
$config = [VGAudio.Containers.Adx.AdxConfiguration]::new()
$config.Version = 4
$config.FrameSize = 18
$config.EncryptionType = 0
[IO.File]::WriteAllBytes($OutputAdx, [VGAudio.Containers.Adx.AdxWriter]::new().GetFile($audio, $config))
