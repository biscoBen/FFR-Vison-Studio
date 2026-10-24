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
