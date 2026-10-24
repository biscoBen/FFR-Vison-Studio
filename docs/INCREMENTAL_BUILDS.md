# Reusing unchanged build work

Studio extension 1.2.78 keeps verified generated assets under `engine/build/reuse`.
The first build fills this local cache. Later builds assemble a clean asset folder
and restore matching sprite/icon assets, authored timelines, sound banks and native
read/write results instead of rerunning those conversions. Removed units are not
restored. Changed game containers, mappings, artwork, motions, layout, generator
code or native writer invalidate the affected results; corrupt entries regenerate.
The optional cache is bounded to 4 GiB and can be deleted while Studio is closed.

This does not modify an installed UCAS file in place. A changed mod still needs
packing and verification. Installation compares the actual three installed files:
unchanged files are not recopied, and an identical owned package skips its package
backup. Changed packages keep the prior complete set for rollback. Runtime scripts
still go through their existing ownership and deployment checks.

The console prints stage reuse counts and a final **Total build/install time**.
`engine/build/reuse-report.json` records generation-stage reuse and timing; it does
not include subsequent packing, verification and installation.

A local Linux experiment converted the actual raw FFBE sheets/CSV files for all
30 shipped presets: 36.073 seconds cold, 1.147 seconds warm, with all 30 conversions
reused. This experiment restores the six required spec/texture outputs per unit;
it excludes native cooking, icons, packing, verification and copying to the game.
It does **not** establish a sub-two-minute Windows installation. That target needs
the user's full 30-unit build on their PC. The first post-update build populates
the new cache; compare subsequent setting changes using the final console timing.

## Testing different acquisition routes

Under **Sephira visions: 1-gil Mitra shop**, choose the visions to override. Select
only Crystal Fina and leave Christine unselected to test both in one installation.
The switch must be on to apply the selection. Turning it off restores normal
routes and retains the selection for later; the saved vision recipes are unchanged.
Old settings with no selection continue to override every enabled Sephira vision.

## Timestamped timing reports

Every captured build-log line has local wall time and elapsed time since the
build started. Verification output streams immediately. Explicit stages cover
practice fights, imported effects, acquisition caves, challenge AI/menus/rewards,
Fina's presentation/movie/music and walking-character controls; the final sprite
label no longer covers these later jobs.

**Logs folder** contains the full saved build log, `build-profile-<run>.json`,
and `build-events-<run>.jsonl`. These remain available after a failed native
operation. The JSON profile records stage/phase durations, operation durations
and statuses, cache counts and cache context. Events distinguish hits, absent
entries and invalid entries. Nested operations are included in their parent's
duration, so do not add parent and child times together. Console summaries list
phase totals and slowest operations; verification and install duration follow.

The user's 908.2-second failed first attempt provides a total, not a timed phase
breakdown. Its tail shows 54 separately generated menus during the misleading
last-sprite stage. A native 45-menu comparison measured 149.386s/180 launches with
the old code, 44.433s/50 launches with batching, and 0.020s/zero launches with reuse.
These are menu-component measurements on this executor. The full Windows install
still needs the new timed report from the user's PC.

## The returned seven-minute profile

The 2026-10-24 report records **405.2 seconds** total: 335.0s generating, 54.6s
verifying and 14.3s installing. Sprite/icon sets took 116.1s, but all 270 native
sprite/texture cooks were already reused: the updated generator had rebuilt its
30 raw sets once. Menus took 39.6s on their first group-cache population. Packing
was just 2.3s. Preserve the existing cache when updating.

Extension 1.2.80 adds reuse for individual packages within the initial table/clone
patch, and for Fina's entire presentation and movie wrapper. A changed shop setting
can reuse unchanged skills, icons and other tables. Dirty packages share one native
invocation; in-place timeline edits keep the existing guarded command path.
Fina's runtime data is restored together with her body, glass, glow and textures.
Her current table bindings are generated/cached separately: another vision's
challenge or stat edit does not recook her body, and unrelated table rows stay current.
Native input hashes and complete sidecars still control reuse; a corrupt entry
regenerates. Both builder and verifier take their own immutable table snapshot at
the start of each CLI invocation, avoiding repeated parsing without freezing the
long-running editor's data.

Native component measurements on this executor (not a complete Windows install):

| Work | Cold | Reused / edited |
| --- | ---: | ---: |
| Fina body, crystal, glow and runtime | 83.018s | 0.036s, zero native launches |
| Fina movie wrapper | 20.153s | 0.063s, companion-pak packing only |
| 344 skills plus shop table | 6.556s | 0.014s unchanged; 0.844s shop-only edit |
| 30-vision recipe/source reads | 23.111s | 1.994s using the snapshot |

Readbacks/recipes are identical between the relevant cold and reused paths.
The first build after this update populates the new group entries. Measure the
next unchanged or acquisition-only install against the two-minute goal using the
same profile/log files. No Prepare Game step or recipe reset is needed.
