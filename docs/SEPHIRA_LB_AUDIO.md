# Sephira limit-burst audio

Studio now includes a small, separate selection of the original Memorial sound
recordings for Sephira's visions. It does not require the optional animation
library. Existing audio-off preset defaults are backed up and upgraded once;
later explicit mutes and custom sound banks are retained. No mastery, damage,
hit count, sprite, acquisition or identity changes are part of this update.

The source is the supplied **FFBE Memorial EN Global Events v208 APK**,
SHA-256 `9d21fc8b61c9900eaacb1c2ddef2cabcad1e97d2dc720be16ac09b06fc0086b4`,
and its checksum-verified `SE.acb`, `System.acb`, LB and effect-group masters.
The bundled archive records all source hashes, effect-group offsets, cue frames
and original cue IDs. Audio timing is independent of regional skill mechanics;
it does not replace the build's existing damage or support application data.

## Coverage

Original LB effect-group recordings are supplied for these 23 selected forms:

- A2, Fran, Lunafreya, Minfilia, Folka, Lenneth, Lila and Mystea.
- Reberta, Snow White, Aria, Eiko, Alice, Mog and Freya.
- Trance Terra, Elephim, Jade, Primm, Relm, Rikku, Nalu and Lunera.

The remaining seven have only the original FFBE opening/charging recording:

| Vision | Missing source |
| --- | --- |
| Christine | Exact selected form/LB absent from the supplied Memorial masters. |
| Barusa | Exact selected Global form/LB absent; a different Japanese form is not substituted. |
| Fryevia | Exact selected form/LB absent from the supplied Memorial masters. |
| Lilith | Exact selected form/LB absent from the supplied Memorial masters. |
| Charming Kitty Ariana | Exact selected form/LB absent. The bank's Ariana recordings belong to **Touch It**, a different Ariana. |
| Elza | Exact selected form/LB absent from the supplied Memorial masters. |
| Crystal Fina | Our custom fall/reform sequence has no original FFBE LB soundtrack. Both the standalone and collection versions receive charging audio. |

The APK's other audio deliveries are music, ambience and voices; there is no
second attack sound bank in its catalogs containing the missing Global LBs.
No unrelated soundtrack is silently assigned to these seven visions.

## Conversion and timing

The selection contains **55 attack cue IDs**, plus the common opening cue.
Most recordings retain their original HCA samples. Three attack recordings
(Charm, Cannon and Death Hit) use HFR unsupported by the installed adapter;
their original PCM is re-encoded without HFR using VGAudio 2.2.1 at its Highest
setting. The encrypted opening recording is converted through the same path.
Sample counts, channels and sample rates are checked against the source.

Fran's selected Shatterheart presentation uses its second source variant. Its
Ice Slash sound has three random alternatives, each combining two simultaneous
recordings. Offline mixes preserve both layers with equal gain and 6 dB of
headroom to prevent clipping; the game
cycles the three alternatives using the existing audio adapter. Mog's stop
instructions are retained as source evidence but are never mistaken for new
sound events. None of those stopped cues are started by his selected LB variant.

The build schedules the cues relative to **LB1**, preserving their original
effect-group offsets, repetitions and frame times. It leaves enough playback
time for the final recording to finish. It registers private host-format sound
banks and does not overwrite the game's own sound banks. The existing engine's
`SoundPlayHitSound` battle events carry the recordings; miss/immune playback,
volume and perceived synchronization still need an in-game listening pass.

The developer packer is `scripts/build_sephira_lb_audio.py`. Its inputs are the
verified APK/extracted masters, compatible engine audio tools, and reviewed
offline conversions. VGAudio 2.2.1's `HcaReader` decodes the original HCA,
including the opening recording's type-1 cipher and encoder delay. `HcaWriter`
then encodes PCM with `Quality=Highest` and `LimitBitrate=false`. FFmpeg mixes
the already-decoded PCM layers for Fran. A second readback confirms matching
sample counts and waveform polarity; the encrypted source is never decoded by
FFmpeg. The player does not need these tools
or a new download. The optional full animation library remains separate.
