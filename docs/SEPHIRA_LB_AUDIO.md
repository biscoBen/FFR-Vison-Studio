# Sephira limit-burst audio

Studio now includes a small, separate selection of the original Memorial sound
recordings for Sephira's visions. It does not require the optional animation
library. Existing audio-off preset defaults are backed up and upgraded once;
later explicit mutes and custom sound banks are retained. Audio never changes
damage, hit counts, sprites, acquisition or identities. The subsequent awakening
bonus revision is described in [its balance report](SEPHIRA_AWAKENING_BALANCE.md).

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
- Trance Terra, Aerith, Jade, Primm, Relm, Rikku, Nalu and Lunera.

Two requested adaptations now accompany those original soundtracks:

- Charming Kitty Ariana uses the full clean **Touch It** recording from Ariana
  form `401000106` (SE cue 617), beginning with LB1.
- Crystal Fina uses the original Accumulate buildup (SE 102), followed by Cure
  (SE 25) at her existing healing application marker. Both collection and
  standalone Fina use it. Her custom fall/reform sequence has no original LB
  soundtrack of its own.

Five still have only the original FFBE opening/charging recording:

| Vision | Missing source |
| --- | --- |
| Christine | Exact selected form/LB absent from the supplied Memorial masters. |
| Barusa | Exact selected Global form/LB absent; a different Japanese form is not substituted. |
| Fryevia | Exact selected form/LB absent from the supplied Memorial masters. |
| Lilith | Exact selected form/LB absent from the supplied Memorial masters. |
| Elza | Exact selected form/LB absent from the supplied Memorial masters. |

The APK's other audio deliveries are music, ambience and voices; there is no
second attack sound bank in its catalogs containing the missing Global LBs.
No unrelated soundtrack is silently assigned to these five visions.

The follow-up search checked the older JP LB master as well as the supplied
Memorial master; neither contains the five exact Global LB identities. JP
Barusa's KB Crag Explosion does have routing, but its four hit frames differ
from the selected Global Volcanic Eruption's two. It is not treated as the exact
missing recording. The supplied narrated Christine video has correlations with
shared bank samples, but those partial matches do not yet identify her complete
original soundtrack or its routing. No narrated audio or unverified match is
bundled as an original LB recording.

## Conversion and timing

The selection contains **56 attack cue IDs**, plus the common opening cue.
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
time for the final recording to finish. Fina's explicitly requested Cure clip is
aligned after scheduling to the existing reaction tick, including fallback
timelines; it never introduces another damage/healing event. It registers private host-format sound
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
