# Crystal Fina cinematic test

This optional test adds a **6.4-second illustrated cinematic** before Crystal Fina’s existing FFBE resonance.
The approved artwork uses crystal refraction and light for coverage, without the initially invented outfit.
It is an animated illustration with camera movement, light, motes, fractures and a glass release, rather than
a fully animated 3D character. The chime/air/glass score is original synthesized audio without dialogue.

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
- An early template check applies only when this test is enabled. A changed native movie master stops this
  experimental build before sprite conversion; disabling the test leaves ordinary builds available.

## Verification and limits

The MP4 and VP9 stream decode fully. Demuxing the CRI container recovers the exact original IVF stream. Native
readback verifies movie dimensions, duration, spawn times, absence of donor gameplay events and intact opaque
compiled data. The legacy assets reparse, and retoc packages them while retaining the checksum-verified USM pak.
Regression tests cover the default-off switch, independent settings, audio/feedback alignment, archive integrity,
read-only preview and removal of the movie on disable.

These are file/timeline/package checks, **not an in-game playback pass**. CRI decoder acceptance, startup delay,
audio/movie synchronization, battle transitions, repeated playback, controller behavior and Steam Deck playback
still need the user’s test. Browser preview validates the movie content independently of the CRI game path.

## Reproduction

The image-generation artwork is `artwork/crystal_fina_cinematic.png`. Its SHA-256 is
`2f9c38115ec78a673f70fb3133b9185561ea5a04bc6b8b1d917c446d2cfeb573`.
The developer renderer is `scripts/build_crystal_fina_cinematic.py`:

```sh
python scripts/build_crystal_fina_cinematic.py --output /tmp/fina-render
# Encode /tmp/fina-render/score.wav with VGAudio 2.2.1 HcaWriter:
# mono, Highest quality, LimitBitrate=false, unencrypted HCA 2, saved as score.hca.
python scripts/build_crystal_fina_cinematic.py --output /tmp/fina-render \
  --package assets/existing_visions/payload/fina_cinematic.zip
```

Rendering requires Pillow, NumPy, FFmpeg and [WannaCRI 0.3.3](https://github.com/donmai-me/WannaCRI) (MIT).
Players receive the completed media and need none of those developer tools. Rendering is deterministic for the
authored camera/particle/audio inputs; encoded bytes can vary with encoder versions. The shipped archive pins
every file by SHA-256 and is independent of the optional FFBE animation-library download.
