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
