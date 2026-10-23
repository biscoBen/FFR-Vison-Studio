# Crystal Fina cinematic test

The current runtime-test candidate uses the exact existing **Crystal-Fina-Rotating-Lighter.mp4**
selected by the user, without rerendering the artwork. Alternate artwork work is paused. The source
MP4 is 1920×1080, 30 fps, 192 frames (6.4 seconds); Studio's preview is byte-identical to it. Its SHA-256
is `680e099c04a03f5e0e7206e2a2d5b8bb843613e218f7ee213d390b66a6b649c5`.
The in-game copy is converted to the tested 1280×720 VP9/USM format. It retains the same shot, timing
and matching original chime/air score. The intact crystal rotates continuously and the camera moves
closer, ending with Fina opening ruby-red eyes. There is no shattering or breaking sound.

Revision 1 delayed the LB but displayed no movie. The returned native diagnostics revealed an incorrect
movie pak path, now corrected together with concrete USM header differences. File and native asset
checks do not establish playback inside Resonance; that still needs the user's in-game test. The
revision 2 candidate passes through Windows checks before publication; the verified download is linked
in the fork changelog. Until that package is published, the existing download remains revision 1.

In Studio, use **Preview Crystal Fina cinematic** to view the movie with sound. To test the game path:

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

- VP9, 1280×720, 30 fps, 192 frames, unencrypted CRI USM; no alpha or embedded audio track.
- A private native `PlatformManaMovie`/`FileManaMovie` pair points at `Movies/Studio/CrystalFina_Test.usm`.
  CRI resolves that relative to `Content/Streams`: the companion pak must contain
  `FFRS/Content/Streams/Movies/Studio/CrystalFina_Test.usm`.
- The original Cloud movie master supplies the native Mana/spawn bindings. Its compiled opaque data and director
  locator are retained through binary cloning. Its donor battle events are neutralized. Three private event-only
  children supply Fina’s continuation and inert effect/sound subtracks.
- The movie window is 2.0–8.4 seconds. Fina’s existing LB, reaction, cleanup and sounds shift together, with LB1
  beginning at 8.4 seconds. Her cure recording stays on the original heal application marker. The common opening
  cue moves to the start, and the original score begins with the movie.
- The score uses a separate native HCA sound bank and honors the existing explicit mute/custom-audio choices.
  The game’s audio adapter applies its own host profile. No game-wide sound bank or movie asset is replaced.
- The USM travels in Studio’s normal companion `.pak`; retoc writes the `.utoc`/`.ucas` and preserves that pak.
  The existing three-file installer and Steam Deck snapshot format therefore carry the movie too. Disabling the
  test empties the owned companion movie pak on the next build. Other mods are untouched.
- The developer encoder normalizes video-only USM chunk alignment, metadata byte counts, maximum chunk
  size, declared file size and seek offsets to the captured native conventions. Compressed video packets
  remain byte-identical; no additional image or audio conversion occurs in that step.
- An early template check applies only when this test is enabled. A changed native movie master stops this
  experimental build before sprite conversion; disabling the test leaves ordinary builds available.

## Verification and limits

The MP4 and VP9 stream decode fully. Demuxing the CRI container recovers the exact original IVF stream. Native
readback verifies movie dimensions, duration, spawn times, absence of donor gameplay events and intact opaque
compiled data. The legacy assets reparse, and retoc packages them while retaining the checksum-verified USM pak.
Regression tests cover the default-off switch, independent settings, audio/feedback alignment, archive integrity,
read-only preview and removal of the movie on disable.

Earlier revision 2 local checks: 49 focused Python checks and 31 Flutter checks passed (one Windows-only Flutter check
was skipped). The rendered Blender scene verifies a continuous 15-degree/second spin, continuous camera
approach, closed eyes through frame 156 and fully open eyes from frame 177. MP4/VP9 fully decode, USM demux
recovers the identical IVF, and native readback/package checks pass. The local movie candidate finished at
2026-10-23 10:18 America/Los_Angeles. The selected lighter movie now proceeds through the Windows checks before publication.

These are file/timeline/package checks, **not an in-game playback pass**. The reported revision 1 blank movie
remains unresolved. CRI decoder acceptance, startup delay,
audio/movie synchronization, battle transitions, repeated playback, controller behavior and Steam Deck playback
still need the user’s test. Browser preview validates the movie content independently of the CRI game path.

`scripts/reference/crystal-fina-battle/Crystal-Fina-Movie-Diagnostics.zip` is a separate read-only collector.
It uses the installed Studio reader to capture at most 2 MiB each from the installed private USM and an
original Cloud VP9 USM, plus generated/native descriptors, the private timeline, package hashes, recent logs
and movie-related settings. It neither updates the cinematic nor requires owning Cloud or Terra. Samples
marked `prefixOnly` are incomplete and intended for container/header comparisons. The collector's synthetic
fixture checks cover exact binary extraction, the sample cap, missing movies, scoped collection and unchanged
game/engine trees. Windows PowerShell 5.1 has not yet been exercised for this new collector locally.

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
original score HCA. It checks the source duration/frame count/aspect ratio, keeps the preview bytes,
converts the game stream and normalizes its native container before using the existing archive packager.
The matching score source was checked against the selected MP4 export record. No new artwork is generated.
The archive records the source MP4 name and SHA-256; regression checks pin that exact selection.

```sh
PYTHONPATH=/path/to/wannacri:scripts python scripts/import_crystal_fina_movie.py \
  --source /path/to/Crystal-Fina-Rotating-Lighter.mp4 \
  --scene /path/to/lighter/scene.json --score-hca /path/to/matching/score.hca \
  --output /tmp/fina-game --package assets/existing_visions/payload/fina_cinematic.zip
```

Selected-movie verification: 50 focused Python checks pass; 31 focused Flutter checks pass with one
Windows-only skip locally. The selected preview is byte-identical to the supplied MP4, all 192 native
VP9 frames decode, and USM demux recovers the exact IVF. Native readback confirms the private movie
source, 2.0–8.4 second movie window, three score/LB sound banks and preserved compiled data. The
corrected Streams movie entry survives retoc packaging. The original revision 2 code candidate was
ready at 2026-10-23 10:18 America/Los_Angeles; artwork review and this selected-movie import followed.
Windows CI and actual game playback are separate checks; the latter still needs the user's test.
