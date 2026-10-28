# Crystal Fina cinematic test

## Optional intro restored — 2026-10-28

Studio again has a **Crystal Fina resonance cinematic** switch under the main
game options. It defaults off. Include Fina and turn it on to add the approved
movie and its working cave soundtrack; rebuild/install and restart the game.
Switching it off removes the movie wrapper and its music control while keeping
her original sprite resonance, healing and cure sounds. It also skips movie-only
template/audio/cache work. No vision ID, kit, mastery or acquisition reset is needed.

The implementation and soundtrack evolved through the historical diagnostics
below. The user has confirmed the current HCA-v3-decoded cave music works in game;
restoring the switch does not change those media bytes or the accepted video.

The current test keeps the approved **Crystal-Fina-Rotating-Lighter.mp4** video and
its 6.4-second duration. The user confirms the movie now plays once and hands off
to the sprite LB. Its embedded mono HCA score was audible but garbled in game,
despite clean offline HCA recovery/decoding. That is a failed listening test.

The current correction uses the secret cave's own **BGM_PP_DUNGEON_CAVE1** recording,
from its beginning. A private native Atom timeline/cue reads the installed game's
`BGM_PP` bank and streaming archive. No audio is reencoded or copied into the mod,
and the failing embedded Mana soundtrack is removed. The requested piano/organ
candidate was superseded before publication. In-game listening remains unverified.

Only audio is replaced. Studio's preview copies the approved video stream without
re-encoding; the in-game 192 VP9 color pictures and 192 native Sofdec opacity pictures
are byte-identical to the working single-play version. The source movie's SHA-256
remains `680e099c04a03f5e0e7206e2a2d5b8bb843613e218f7ee213d390b66a6b649c5`.
The new preview has different whole-file bytes because its soundtrack changed.
Its copied video-stream SHA-256 is
`bc7dec7c2a7d0ad08caf0386d2022178fbfdcb965949cfe9204c6fb2681ec1d5`.

In Studio, **Preview Crystal Fina cinematic** shows the picture only; its native game soundtrack is heard in battle. To test the game path:

1. Include Crystal Fina and keep her own FFBE resonance selected.
2. Turn on **Test Crystal Fina cinematic**.
3. Rebuild/install, restart Resonance, then use her resonance in battle.
4. Check that the movie appears with its score, returns to the battle, and plays the existing LB and cure sound.
   Try it again in a second battle to check repeat playback and UI restoration.
5. To remove the intro, switch it off, rebuild/install and restart the game.

The switch is off by default. No MR/acquisition update or kit reset is needed. It does not add a cinematic to the
practice enemy’s AI or alter skills, healing amounts, hit counts, mastery rewards, acquisition or accepted crystal material.
The first test leaves native movie skipping disabled on this private wrapper; skipping needs a separate runtime check.

## Playback and transport

- VP9, 1920×1080, 30 fps, 192 frames; native opaque Sofdec alpha, no embedded audio.
- A private native `PlatformManaMovie`/`FileManaMovie` pair points at `Movies/Studio/CrystalFina_Test.usm`.
  CRI resolves that relative to `Content/Streams`: the companion pak must contain
  `FFRS/Content/Streams/Movies/Studio/CrystalFina_Test.usm`.
- The original Cloud movie master supplies the native Mana/spawn bindings. Its compiled bindings and director
  locator are retained through binary cloning; only validated cached frame bounds are shortened. Its donor battle events are neutralized. Private children supply Fina’s continuation, an inert effect subtrack and the native Atom cave-music subtrack.
- After timing changes, the private sequence, scene, Mana track/section and actor spawn track/section receive
  fresh signatures. Shipping playback still consumed the cooked evaluation export, so its four movie
  endpoints and nine root/subsequence endpoints now change alongside the typed ranges. Every other byte
  remains native. A length/SHA-256 check rejects unknown layouts before patching the private clone.
  The native `UISetVisibility` transition hides battle UI while keeping movie visibility, then restores battle UI
  at the movie end. The earlier separate movie-widget toggle did not reproduce that native transition.
- The movie window is 2.0–8.4 seconds. Fina’s existing LB, reaction, cleanup and sounds shift together, with LB1
  beginning at 8.4 seconds. Her cure recording stays on the original heal application marker. The common opening
  cue moves to the start, and the original score begins with the movie.
- One native `MovieSceneAtomSection` plays `BGM_PP_DUNGEON_CAVE1` from offset zero
  over 2.0–8.4 seconds, stopping at the sprite handoff. The other four Cloud cues
  are disabled. Its typed cooked evaluation ranges are retimed with its section;
  native preloading is retained. Both Mana descriptors have zero audio tracks.
  Fina's separate opening/build-up and cure banks stay on their original markers.
- The USM travels in Studio’s normal companion `.pak`; retoc writes the `.utoc`/`.ucas` and preserves that pak.
  The existing three-file installer and Steam Deck snapshot format therefore carry the movie too. Disabling the
  test empties the owned companion movie pak on the next build. Other mods are untouched.
- The developer encoder normalizes USM chunk alignment, metadata byte counts, maximum chunk
  size, declared file size and seek offsets to the captured native conventions. Compressed video packets
  remain byte-identical; no additional image or audio conversion occurs in that step.
- An early template check applies only when this test is enabled. A changed native movie master stops this
  experimental build before sprite conversion; disabling the test leaves ordinary builds available.

## Verification and limits

The MP4 and VP9 stream decode fully. Demuxing the CRI container recovers the exact original IVF stream. Native
readback verifies movie dimensions, duration, spawn times, absence of donor gameplay events and retimed cooked
ranges with all other compiled bytes preserved. The legacy assets reparse, and retoc packages them while retaining the checksum-verified USM pak.
Regression tests cover the default-off switch, independent settings, audio/feedback alignment, archive integrity,
read-only preview and removal of the movie on disable.

Earlier revision 2 local checks: 49 focused Python checks and 31 Flutter checks passed (one Windows-only Flutter check
was skipped). The rendered Blender scene verifies a continuous 15-degree/second spin, continuous camera
approach, closed eyes through frame 156 and fully open eyes from frame 177. MP4/VP9 fully decode, USM demux
recovers the identical IVF, and native readback/package checks pass. The local movie candidate finished at
2026-10-23 10:18 America/Los_Angeles. The selected lighter movie now proceeds through the Windows checks before publication.

These are file/timeline/package checks, **not an in-game playback pass**. The user confirms visible playback in the opacity update. The subsequent repeat/silent-score
correction still needs a listening and handoff test. Startup delay,
audio/movie synchronization, battle transitions, repeated playback, controller behavior and Steam Deck playback
still need the user’s test. Browser preview validates the movie content independently of the CRI game path.

`scripts/reference/crystal-fina-battle/Crystal-Fina-Movie-Diagnostics.zip` is a separate read-only collector.
It uses the installed Studio reader to capture at most 2 MiB each from the installed private USM and an
original Cloud VP9 USM, plus generated/native descriptors, the private timeline, package hashes, recent logs
and movie-related settings. It neither updates the cinematic nor requires owning Cloud or Terra. Samples
marked `prefixOnly` are incomplete and intended for container/header comparisons. The collector's synthetic
fixture checks cover exact binary extraction, the sample cap, missing movies, scoped collection and unchanged
game/engine trees. Windows PowerShell 5.1 has not yet been exercised for this new collector locally.

### Third return: current package installed, battle playback still blank

`Fina-Movie-Diagnostics-20261023-132758-0c369a.zip` has SHA-256
`62a797821d366cce53bb4b69fd8d7aa06377cee58426210d09c0f6906aea741b`. The user cast the resonance,
paused immediately afterward and collected it. Installed and built companion pak hashes are both
`b2829ef795bc6bfad27eeaf8d64b36b01218f327a29b256c4528cfd40db8e39a`, exactly matching the verified
local native package. That pak contains only the corrected Streams entry with the selected revision 2
USM. Installed/build utoc hashes also match. The obsolete collector's failure to find the old
`Content/Movies` entry does not show that the installed movie is missing.

The returned private master `444011` reparses with the expected private ManaSource, shared external
player/texture, actor spawn binding, 2.0–8.4 second movie range and 16.8 second root duration. Its
opaque compiled data matches the native donor. The actor template's serialized bytes also match the
native donor exactly; its raw-export fallback in the JSON reader is not evidence of modified bytes.
The timeline preserves Fina's cure cue on the heal marker. The returned log contains the later LB
motions but no specific Mana error. This does not establish whether the runtime decoder opened the
file or whether the display actor rendered it.

The separate `Crystal-Fina-Movie-Player-Reference.zip` runs **Collect Fina Movie Player.cmd**.
It exports only `Movies/Sequencer/` and the native `440110/440111` movie sequence into a new output
folder, using the full game's Paks directory so retoc can resolve global script objects. It includes
existing mappings if available and checks for the display actor, player, texture/material, master and
cut sequence. The game can be running or closed; no further cast, pause, rebuild, original vision
unlock or installation is needed. Each extraction is limited to 60 seconds. Nine focused collector
checks pass locally, including read-only scope, exact archive contents and failed-asset reporting even
when the reader exits zero. The subsequent Windows return successfully collected all requested assets.
No new cinematic or Studio runtime package was published for this collection.

### Returned shared player and display assets

`Fina-Movie-Player-Reference-20261023-133927-365eb1.zip` has SHA-256
`1bae3899894a336fad7974942c6029042f21a38780dcfd7157a277eaa5d7f66f`. Both scoped native extractions
succeeded on Windows: five shared movie assets and four Cloud timeline assets, with no reported
failures. The Cloud master hashes match the pinned template. All five shared assets reparse locally.

The display actor's BeginPlay sets `CPP_UI_BattleSubsystem.CinematicManager.bUseMovie` true; Destroyed
sets it false. It does not contain a world-space screen mesh. The shared player references the shared
Mana texture, whose four component textures include an alpha component and whose clear alpha is zero.
The display material uses the UI domain with translucent blending. Native Cloud has a separate alpha
track; the selected Fina USM currently has none. This is a display compatibility hypothesis, not proof
that the Fina decoder has started or that a missing alpha track caused the failure.

The standalone `Crystal-Fina-Movie-Trace.zip` installs a separate `FFRStudioMovieTrace` UE4SS observer.
It logs Mana status/frame progress, source/texture, alpha-track selection, movie actor counts and the
manager's `bUseMovie` flag. Native getters run on the game thread, and ManaPlayer getters are skipped
when its component is uninitialized. It does not open/play/stop a movie or modify native state. A
restart is required to load it; no Studio update/rebuild is required. After one resonance/F8 bookmark,
its collection command uses the existing diagnostics collector. Its disable command removes only its
owned `enabled.txt`; an unknown same-named folder is refused. Four focused checks pass locally,
including executable Lua observations against native-object proxies that reject writes. Windows live
API availability and the actual playback state still require the user's trace. No playback fix or
updated Studio runtime package is claimed.

### Runtime trace: decoding succeeds, movie outlasts its intended window

`Fina-Movie-Diagnostics-20261023-135435-313271.zip` has SHA-256
`7ddf5a2902024e2b49e15d7ddd6c6ac0d839e3db1786b57ce8c63f32b67bede4`. Collection reports no errors.
At 13:53:53–54 the battle Mana player opens `/Game/Movies/Studio/CrystalFina_Test`, reaches Playing
(status 5), and advances its frame counter through bucket 12 (frames 180–194). The cinematic manager
sets `bUseMovie=true`. The same movie then restarts its counter, reaches bucket 12 again, and stops at
13:54:07. The first F8 bookmark is at 13:54:05.763, during that second movie pass; the second is at
13:54:11.562 after the movie stops. Fina's independent sprite LB starts at 13:54:00.362. These are
separate movie and sprite observations; the sprite LB is not being removed or treated as a duplicate.

The live movie/actor window follows the native donor's longer evaluation period despite the edited
2.0–8.4 second ranges. Candidate extension 1.2.72 applies the engine's existing signature-refresh
mechanism for edited movie/spawn tracks, plus the native `UISetVisibility` battle/movie transition.
It does not change the selected MP4, VP9/USM packets, score, descriptor alpha settings, healing or
sprite animation. Missing alpha is no longer a decoder explanation; whether it affects the display
material remains unproven. The old released build's visible playback is still unresolved.

The captured engine settings had been turned off and its generated master changed after the
installed build was produced. Those loose generated files are therefore not treated as the live
movie sequence. The installed/build pak and utoc hashes match, and the trace itself establishes the
actual movie source and playback state. Both F8 bookmarks are retained.

Local candidate checks: 10 cinematic tests, 29 existing-vision tests and 13 collector/observer tests
pass. Native rebuilding/readback confirms all six signatures changed, the movie/spawn ranges end at
8.4 seconds, private bindings and opaque bytes remain intact, media pak contents are unchanged, and
the native UI transitions bracket the movie. Actual visibility and live stop timing require the next
user test after the Windows package passes its checks.

### Returned playback diagnostics — 2026-10-23

The returned `Fina-Movie-Diagnostics-20261023-103714-6733b5.zip` has SHA-256
`9f8ab08d4ed4bc0c3f1332dde82a4f61a598b01e3ee2f797e3f8b547a6d7d214`.
It contains the complete installed revision 1 USM, not a truncated prefix. Its SHA-256 is
`d082043c338ebc6d3cad93c9435de3812973c574021c7e753c6b9a0b592a3ba9`, matching the published source.
The installed/build companion pak and utoc hashes match. The returned movie descriptors reparse as
1280×720 VP9, 192 frames, with the expected private file path; master `444011` points to that private
source and retains the original compiled binding data. The movie window remains 2.0–8.4 seconds.
The returned UE4SS log contains no specific Mana playback error, and no FFRS game log was captured.

The collector did **not** obtain the original Cloud movie; its first version checked only top-level
pak entries. Schema 2 also checks the exact loose `Content/Movies/Skill` path, discovers the original
entry by filename when the pak path differs, and records failed lookup details. It reports only
movie/decryption booleans/counts and whether a game key is configured from the installed/cached CRI
settings; it never copies the key or full INI. The cause remains unconfirmed. In particular, packed
file access, video decryption and alpha/display behavior are hypotheses, not established fixes.
All five collector checks pass, including loose-file collection and sanitized settings with differing
installed/cached decoder options. No playback patch, game rebuild or publication is claimed.

### Second return: confirmed stream path mismatch

The second returned collector found Cloud at
`FFRS/Content/Streams/Movies/Skill/MV_Skill440110_vp9.usm`, while its native `FileManaMovie.FilePath`
is `Movies/Skill/MV_Skill440110_vp9.usm`. Our descriptor used the same relative convention but the USM
was packaged directly under `Content/Movies`, omitting `Streams`. Correct the owned companion-pak
entry and remove only the obsolete staged Fina movie on migration. Keep the descriptor path, LB and
healing timing, audio, gameplay and other mods unchanged. The collector accepts both old and corrected
private entries so it can diagnose either installation.

The complete 97 color-video packets in the original 2 MiB sample concatenate into a VP9 IVF stream and
decode without a key. The native and our generated streams both use the same CRI version and IVF packet
framing. Video decryption is not a justified fix. The original sample is incomplete; this is not a full
394-frame native movie decode or an in-game playback pass.

Also correct three concrete container discrepancies against the sample: native seek metadata reports
its chunk's byte size (256), whereas WannaCRI wrote a row count; all native chunks align to 32 bytes;
and the native maximum chunk field includes the complete aligned chunk. Normalize these, the overall
file-size declaration and affected seek offsets without changing a video packet. Unit checks and full
VP9 roundtrip/decode pass. Native sequence/package proof confirms the corrected stream entry survives
retoc. Both the path/format correction and the revised artwork remain unpublished pending review and
an actual game test; the runtime display has not yet been confirmed fixed.

### Refraction comparison exports

The first lighter/denser motion studies were rejected: projecting complete paintings on a shallow
form lost the original independent crystal motion, and the ending visibly dissolved the face.
Do not package or reuse those studies as an accepted cinematic.

The corrected comparison renderer, `scripts/render_crystal_fina_refraction.py`, wraps the original
`scripts/render_crystal_fina_rotation.py`. Both variants retain its full octagonal 3D crystal,
continuous 15-degree/second rotation, stationary character, camera transforms and eye-region-only
awakening. The original closed/open image files remain unchanged. Only the original small eye mask
animates; there is no full-face transition. A static shader makes internal blue crystal highlights
more translucent, while the rotating outer facets supply lighter or denser optical coverage using
`artwork/crystal_fina_optics/refraction.png`. This is illustration-based optical shading, not a
fully modeled character or a physically exact refraction simulation.

Export both at 1920×1080, 30 fps, 192 frames (6.4 seconds), with the same original score. Audit the
saved scenes against the original at every frame, then fully decode both MP4s. Keep comparison
exports separate from the packaged cinematic. Their appearance and the unpublished playback fix
still await review and an actual game test; no upload, push or Windows release is authorized.

Corrected local exports finished at 2026-10-23 12:05 America/Los_Angeles. Both individual MP4s are
1920×1080 with sound, have 192 distinct rendered frames, and fully decode. The side-by-side MP4
also fully decodes. Both saved-scene audits match the original mesh, camera and crystal transforms
at every frame and retain the original eye color/mask graph exactly. No comparison was packaged,
installed or published. These checks verify the rendered content, not playback inside Resonance.

To reproduce a material comparison without changing the packaged movie:

```sh
blender -b -t 4 --python scripts/render_crystal_fina_refraction.py -- \
  --variant lighter --output /tmp/fina-lighter --width 1920 --samples 4
blender -b -t 4 --python scripts/render_crystal_fina_refraction.py -- \
  --variant denser --output /tmp/fina-denser --width 1920 --samples 4
```

## Reproduction

The original Blender/chime recipe below is historical. For current movie audio, use
the stereo ADX rescoring recipe at the end of this document.

The original approved image-generation artwork is `artwork/crystal_fina_cinematic.png`. Its SHA-256 is
`2f9c38115ec78a673f70fb3133b9185561ea5a04bc6b8b1d917c446d2cfeb573`.
The scene uses separated sanctuary/closed-eye/open-eye layers in `artwork/crystal_fina_layers/`, with every layer
checksum recorded in the movie metadata. Only a small registered eye region blends between character layers;
the figure's hair, hands and silhouette stay on the same illustration. The crystal's mesh and reflected facets
turn independently. `scripts/render_crystal_fina_rotation.py` constructs the Blender scene and samples the
camera/spin continuously for all 192 frames. The developer encoder is `scripts/build_crystal_fina_cinematic.py`:

```sh
python scripts/build_crystal_fina_cinematic.py --output /tmp/fina-render
# Encode /tmp/fina-render/score.wav with VGAudio 2.2.1 HcaWriter:
# mono, Highest quality, LimitBitrate=false, unencrypted HCA 2, saved as score.hca.
python scripts/build_crystal_fina_cinematic.py --output /tmp/fina-render \
  --package assets/existing_visions/payload/fina_cinematic.zip
```

Rendering requires Blender 4.3, Pillow, NumPy, FFmpeg and [WannaCRI 0.3.3](https://github.com/donmai-me/WannaCRI) (MIT).
Players receive the completed media and need none of those developer tools. Rendering is deterministic for the
authored camera/particle/audio inputs; encoded bytes can vary with encoder versions. The shipped archive pins
every file by SHA-256 and is independent of the optional FFBE animation-library download.

### Current artwork decision — complete scene reference

The user selected the exact lighter triptych as the visual reference and rejected the fitted crystal
clothing that remained in the separated-character motion version. Preserve the selected image unchanged
outside the release checkout as the local `Crystal-Fina-Approved-Reference.png`; its adjacent JSON
records the SHA-256 and requested motion. The selected artwork is approved; the motion exports are not approved replacements for it.

The user suggested complete scene frames. A whole-scene continuation request preserving existing
coverage was rejected by the image tool. No new motion test was produced. The session has no dedicated
video-generation tool. Do not claim that new complete-scene motion exists or replace the approved reference with the older
character design. The user subsequently selected the existing lighter motion export specifically for
in-game testing; only that selection and the required playback fixes are authorized for the test update.

### Reproduce the selected runtime movie

Use `scripts/import_crystal_fina_movie.py` with the selected MP4, its `scene.json`, and its matching
stereo ADX score plus its clean WAV. It checks the source duration/frame count/aspect ratio, keeps the preview video,
converts the game stream and normalizes its native container before using the existing archive packager.
The matching score source was checked against the selected MP4 export record. No new artwork is generated.
The archive records the source MP4 name and SHA-256; regression checks pin that exact selection.

```sh
PYTHONPATH=/path/to/wannacri:scripts python scripts/import_crystal_fina_movie.py \
  --source /path/to/Crystal-Fina-Rotating-Lighter.mp4 \
  --scene /path/to/lighter/scene.json --score-adx /path/to/score.adx --score-wav /path/to/score.wav \
  --output /tmp/fina-game --package assets/existing_visions/payload/fina_cinematic.zip
```

Selected-movie verification: 50 focused Python checks pass; 31 focused Flutter checks pass with one
Windows-only skip locally. The selected preview is byte-identical to the supplied MP4, all 192 native
VP9 frames decode, and USM demux recovers the exact IVF. Native readback confirms the private movie
source, 2.0–8.4 second movie window, three score/LB sound banks and preserved compiled data. The
corrected Streams movie entry survives retoc packaging. The original revision 2 code candidate was
ready at 2026-10-23 10:18 America/Los_Angeles; artwork review and this selected-movie import followed.
Windows CI and actual game playback are separate checks; the latter still needs the user's test.

### Single-pass timing and embedded movie score

The visible opacity build still used 363,200-tick movie endpoints inside the native 3,073-byte
`CompiledData` RawExport, despite the edited typed endpoint of 201,600 ticks. At 24,000 ticks per
second that left the six-second movie active for the donor's thirteen-second window. The private
clone now changes exactly four movie endpoints and nine root/subsequence endpoints. The fixture in
`scripts/fixtures/fina_compiled/` pins the donor layout. All bindings, locators and other bytes remain
unchanged; signatures continue to refresh as well. Native UAsset readback and retoc cooking pass.

The score is now part of the USM, rather than a `SoundPlayHitSound` event during the movie. The
`@SFA` track recovers the exact 154,208-byte source HCA (SHA-256
`3b76ce143df2fdba023506a999ae3eae8fd382cfdadf81fe9095834439344567`). Its 301 blocks
plus header use the 48-kHz sample clock and encoder delay, interleaved with the unchanged 192 color
and 192 opacity packets. Both descriptors read back as mono, 48 kHz, 307,200 samples, type `HCA`.
No duplicate score bank/event is added; Fina's opening/build-up and cure banks still accompany the
sprite/healing timeline. The private USM SHA-256 is
`60eb3c5866361c9eec901e80cb6213d22705183edf3eeb7de42721c7ef124581`.

The exact selected browser MP4 remains unchanged. These corrections require a rebuild/install and
restart; they need no kit/MR/acquisition update. One movie followed by the sprite LB, audible movie
music and reuse in a second battle remain live checks.

### Superseded piano/organ and native ADX candidate (not published)

The user confirms the previous update's video plays once, and only its movie audio
is garbled; retain its cooked/typed timing fixes. Offline recovery/decoding of that
HCA file was insufficient evidence of game compatibility. The native-template
comparison establishes a format difference, not a proven cause inside the decoder.
The replacement matches the original stereo ADX v4 movie path.

The native-format ADX source has SHA-256
`e4220390907bc88b513a2f7a65bda01de2a5e3914abb5018a3595e28ac20815a`.
Its USM SHA-256 is
`008ec41a321eaee17ed4037022f80c0ce78ac5baae42a1cb4d5b1e6fd606fbfe`.
Demuxing must recover the exact ADX file. The 288-byte header precedes 192 stereo
1,800-byte data packets and the ADX end marker; the declared codec is 2 (`Adx`).
Both VGAudio and FFmpeg decode 307,200 stereo frames. Relative to source PCM,
VGAudio readback measures 47.73 dB SNR and FFmpeg 25.14 dB, with correlations
0.999992 and 0.999034 respectively. These are independent offline results, not a
claim that the game's distortion is resolved. Check the installed game's sound.

The user selected this light-to-intense score for the current test. The opening
measures -32.87 dBFS RMS and the final build -14.77 dBFS RMS, an 18.1 dB rise.
The clean source WAV and new preview are included in the media archive. The WAV
peaks at -1.51 dBFS with -21.19 dBFS RMS. `scripts/score_crystal_fina.py` records
the rubato arrangement, instrument programs, velocities and render provenance.
It uses FluidSynth and TimGM6mb (Tim Brechbill, 2004; David Bolton, 2010; GPL-2;
[upstream source](https://github.com/musescore/musescore-old/commit/90c33ef9d87b3f5ff92efd3b07d89eb455fb1fef)).
The SoundFont is not bundled with Studio. `scripts/encode_movie_adx.ps1` uses
VGAudio 2.2.1, ADX version 4, 18-byte blocks, encryption disabled.
`scripts/rescore_crystal_fina_movie.py` replaces only the score and verifies every
color/opacity packet and the copied preview video stream. Players need none of
these developer tools or instrument libraries.

```sh
python scripts/score_crystal_fina.py --soundfont /path/to/TimGM6mb.sf2 --output /tmp/fina-score.wav
pwsh -File scripts/encode_movie_adx.ps1 -InputWave /tmp/fina-score.wav \
  -OutputAdx /tmp/fina-score.adx -VgaudioDll /path/to/VGAudio.dll
PYTHONPATH=/path/to/wannacri:scripts python scripts/rescore_crystal_fina_movie.py \
  --archive assets/existing_visions/payload/fina_cinematic.zip \
  --source /path/to/Crystal-Fina-Rotating-Lighter.mp4 \
  --score-wav /tmp/fina-score.wav --score-adx /tmp/fina-score.adx \
  --destination assets/existing_visions/payload/fina_cinematic.zip --output /tmp/fina-scored
```

### Native cave-music test (revision 4)

The returned `Christine-Cave-Reference-20261023-173751-cbffe5` parts contain 60 native
assets, with zero conversion failures. `BGM_PP` cue index 46 / cue ID 10046 resolves
`BGM_PP_DUNGEON_CAVE1` to streamed waveform 46, stream ID 56, stereo 48 kHz,
3,277,372 samples. The ACB metadata is present; the streamed recording stays in the
user's game. A private clone of the game's BGM Atom cue references that same bank
and exact cue name, with zero starting offset and an explicit stop at movie end.
The picture-only USM SHA-256 is
`172c79078fe12907141b1f5dfb6687fdfd8625dd10c1420cf258df8e4a21d6c7`.

Native descriptor, Atom section/cue, cooked master timing and full retoc packing
read back correctly. These checks cannot establish audible playback/mixing or
return to the battle theme: test the intro, sprite/cure handoff and a second battle.
No original cue, bank, track or shared movie player is modified.

To reproduce the current picture-only payload from the earlier illustrated test:

```sh
PYTHONPATH=/path/to/wannacri python scripts/use_crystal_fina_cave_music.py \
  --archive /path/to/earlier/fina_cinematic.zip \
  --source /path/to/Crystal-Fina-Rotating-Lighter.mp4 \
  --destination assets/existing_visions/payload/fina_cinematic.zip \
  --work /tmp/fina-cave-movie
```

## Native soundtrack parent-track correction

The previous sound child was valid but its native master parent
`MovieSceneSubTrack_4` has `bIsEvalDisabled=True`. Music now occupies the existing
active `Effect_000` subtree; `Sound_001` remains inert. A fixture from the native
master checks the selected parent is active. The compiled movie timing and
single-play handoff are retained. Native serialize/readback and IoStore packing
pass; the user must still confirm the cave track can be heard in battle.

The browser preview can now load the exact cave recording from the selected
installed game. On playback it reads only stream 56 from `Streams/Sound/BGM_PP.awb`,
decrypts in memory with the local game settings, and decodes a 6.4-second WAV using
MIT-licensed VGAudio 2.2.1 (`net45`, bundled with its license). No game key is sent
to the decoder or saved in preview metadata. The short WAV stays in the engine's
local build cache; game music is not added to Studio downloads. Video and audio
play/pause/seek together. The decoder/archive, bounds and stereo trimming are tested;
a synthetic encrypted HCA3/subkey roundtrip decodes successfully. The actual
installed cave AWB is not available in this workspace, so native track playback
in the user's browser remains a live test.
