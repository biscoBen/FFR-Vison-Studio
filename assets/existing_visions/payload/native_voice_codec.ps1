param(
    [Parameter(Mandatory=$true)][string]$Mode,
    [Parameter(Mandatory=$true)][string]$InputAudio,
    [Parameter(Mandatory=$true)][string]$OutputAudio,
    [Parameter(Mandatory=$true)][string]$VgaudioDll
)
$ErrorActionPreference = 'Stop'
Add-Type -Path $VgaudioDll
switch ($Mode) {
    'hca-wave' { $audio = [VGAudio.Containers.Hca.HcaReader]::new().Read([IO.File]::ReadAllBytes($InputAudio)) }
    'adx-wave' { $audio = [VGAudio.Containers.Adx.AdxReader]::new().Read([IO.File]::ReadAllBytes($InputAudio)) }
    { $_ -in 'wave-adx','wave-hca' } { $audio = [VGAudio.Containers.Wave.WaveReader]::new().Read([IO.File]::ReadAllBytes($InputAudio)) }
    default { throw 'Unknown native voice conversion.' }
}
switch ($Mode) {
    'wave-adx' {
        $config = [VGAudio.Containers.Adx.AdxConfiguration]::new()
        $config.Version = 4
        $config.FrameSize = 18
        $config.EncryptionType = 0
        $data = [VGAudio.Containers.Adx.AdxWriter]::new().GetFile($audio, $config)
    }
    'wave-hca' {
        $config = [VGAudio.Containers.Hca.HcaConfiguration]::new()
        $config.Quality = [VGAudio.Codecs.CriHca.CriHcaQuality]::Highest
        $config.LimitBitrate = $false
        $data = [VGAudio.Containers.Hca.HcaWriter]::new().GetFile($audio, $config)
    }
    default { $data = [VGAudio.Containers.Wave.WaveWriter]::new().GetFile($audio) }
}
[IO.File]::WriteAllBytes($OutputAudio, $data)
