# Crystal Fina

Crystal Fina is available in **Add unit** in the Sephira test build. Reopen the
Sephira Studio Test shortcut to download the tested branch release. An imported
Fina is recognized as already in the mod; her saved settings are retained. Build
the mod again to include the rendering fix in its current complete roster.

The preset and all ten unit source files come from
`FFR-CrystalFina-Cloud-Handoff-v1.0.1.zip`. `assets/crystal_fina/profile.json` is the
unchanged `profile/crystal-fina-current.json`: it includes Crystal Restoration,
all awakening/passive grants, synchro bonuses, stats, owned skill definitions,
and custom animation fallback warnings. The supplied sprite sheet, icon,
parts CSV, three animation CSVs, metadata and resonance JSON are bundled locally.
Adding the preset does not fetch an official FFBE template or generate a new kit.

`BundledFeatures` verifies the manifests and stages source assets without
overwriting user-edited artwork. Before each engine start, including offline
startup and restart after a compatible update, the engine runs the bundled
installer itself. No Python installation or manual patch command is required
on the Windows PC. Engine 1.0.0.15 and later compatible 1.x layouts are accepted;
the installer validates the current builder's syntax and exact hook locations.
It maintains its own transactional state and original backups in
`engine/.ffr-crystalfina`, separate from the pack versions in `installed.json`.
An unsupported builder or unowned modification fails with a visible error.

Reference vision ID 13503 is used when its vision, command, master and owned skill
IDs are available. Otherwise the app allocates IDs using the current engine rules
and rewrites only owned definitions and their internal references. Borrowed game
IDs, source form 99887755552703 and the supplied settings remain intact.

The build extension changes only Fina's `isVisionCharacter` and `Material` fields
in the freshly generated `DT_BtlUnitAsset` recipe, after verifying all current
roster rows. After sprite generation and output cleanup, it copies her material
into the same full-roster build before packing. A different vision ID uses
`ffr-dt` JSON serialization to retarget the material package/object and texture
package/object imports. The cooked `.uexp` bytes and shader/export data must
remain identical. Other units retain their original materials. A conflicting
old `zzz_CrystalFina_AlphaFlagTest_999_P` overlay stops the build with an explanation
because it can override the fresh roster table.

Developer checks:

```sh
flutter analyze
flutter test
python -m unittest discover -s scripts -p 'test_*.py' -v
python scripts/verify_crystal_fina_bundle.py
```

After intentional, reviewed extension edits, refresh both hash manifests with
`python scripts/verify_crystal_fina_bundle.py --update`. CI runs the Flutter and
Python checks, native Windows shortcut/import checks, and compiles the Windows
release before publishing the test package from `Sephira's-Update`.

Fixtures in `scripts/fixtures/crystal_fina` are validation inputs; they never
replace the downloaded engine or supply a table to a user's mod. Offline tests
cover optional presence, full-roster preservation, collision retargeting,
checksums, transaction rollback, duplicate prevention, and concurrent user edits.
The cloud also runs the real engine installer and material serializer under
Wine. A complete game build, `verify_mod.py` against the packed game assets, and
in-game rendering still require a prepared FINAL FANTASY RESONANCE installation.
