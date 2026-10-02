# Changelog

Fork-specific changes for [biscoBen/FFR-Vison-Studio](https://github.com/biscoBen/FFR-Vison-Studio),
on `Sephira's-Update`, compared with the inherited `master` snapshot
[`d94c685`](https://github.com/biscoBen/FFR-Vison-Studio/commit/d94c685c9dd1b1502c8676e03e679f54a9a05086).
The original project's release notes are preserved below the fork history.

Windows test packages keep version **1.0.0, build 15** for host compatibility. Their commit and workflow run identify
which changes they contain. Dates below use America/Los_Angeles. Published entries describe tested branch packages;
**Unreleased** entries are work awaiting a successful package build.

## Unreleased

- Correct the shop practice battle's NPC binding. The observed "Potions, Phoenix Downs..." conversation belongs
  to Mitra's talk block 6, not the different woman's block 39 targeted in the first package. Match the original
  conversation event in both parent and combined tables; preserve the other woman and all existing testing options.
  Battle entry and return still require in-game confirmation after updating and rebuilding/installing the mod.
- Use the native level 7–8 encounter with one Evil Plant (300 HP) and two Wild Rats (320 HP each), preserving their
  normal stats and all other encounters. Retain guaranteed escape and the optional one-battle MR reward.

## Published Mitra shop practice battle — 2026-10-02

Changes in [`ce9d895`](https://github.com/biscoBen/FFR-Vison-Studio/commit/ce9d89517acebd168fb9d46d660266ff10b10d2f),
[test package 37076779355](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37076779355).

- Optional **Shop practice battle**: Young Woman in Mitra's item shop starts a repeatable fight with three level-1
  Steel Bats after her dialogue. Uses the current party and a native plains backdrop, with guaranteed escape and
  the existing one-battle MR setting when enabled. Disable and reinstall to restore her original interaction.
  Shop inventory, story flags, random encounters and pending ability-hiding decisions are preserved.
  Actual battle entry, return to the shop and repeat interaction require in-game confirmation.
- Passed local analysis, 19 focused Flutter tests and 188 Python tests. Windows passed the full Flutter/Python suites,
  real frozen-engine startup, launcher/updater/import checks and compilation. Verified the published ZIP's checksum,
  exact commit, all bundled extension files and retained party portraits. Master is unchanged.
- Actual engine serialization preserved every original row across all seven affected tables, including 26 original
  vision grants, 11,430 MR AP and the new private encounter. Patch both native parent and combined event/map tables.
- One code push and one reused push build. CI took 5m21s; summed job execution was 9m01s. First complete candidate:
  16:15:23 PDT; ZIP verified at 16:21:54 PDT (6m31s including final local checks, push, CI and download).
  Publication notes use the documentation-only path; the binary retains its tested code commit.

## Published original vision and MR testing — 2026-10-02

Changes in [`a718556`](https://github.com/biscoBen/FFR-Vison-Studio/commit/a718556823725f3d2f404663b6308215f5536aa8),
[test package 37045019928](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37045019928).

- Drag default visions into Added visions to acquire their original items at the next battle start, using the native
  ownership condition. Original vision IDs, kits and MR rewards remain intact. Dragging back stops acquisition after
  reinstalling and preserves edits. Both controls default off; use a clean save without saving.
- Enable one-battle MR testing for 11,430 AP per reward-bearing victory, bounded from native rank costs. Preserve
  scripted reward suppression and awakening requirements. Disable, reinstall and reload the clean save afterward.
- Real engine serialization verified all 26 original grants, preserving 100 parent-event rows, 828 combined-event rows,
  seven common events and 678 encounter groups. Patch both parent and combined tables so runtime recomposition
  retains acquisition. In-game acquisition and MR progression still need confirmation.
- Passed local analysis, 55 focused Flutter tests and 184 Python tests; Windows passed the full Flutter suite, all
  Python checks including real engine contracts, fresh engine startup, launcher/updater/import checks and compilation.
  Verified the authenticated ZIP checksum, exact commit, all extension files and eight retained party portraits.
  Pending ability-hiding decisions are excluded; master is unchanged.
- A runtime composite-table correction required a second code push. Cancelled the first automatic run before publication
  and an accidental duplicate manual run caused by querying Actions immediately after the first push. Reused the corrected
  push run; no further build was dispatched. Final CI took 5m15s, with 8m46s summed job execution; cancelled runs added
  13m39s of runner execution. The download helper's transient HTTP 401 recovered by rejoining the same successful run.
- First complete candidate: 10:57:54 PDT. ZIP verified at 11:10:31 PDT (12m37s from candidate, 33m02s from request,
  including checks, correction, superseded CI and waiting). Packaged-file checks followed the verified download.
  Documentation-only publication notes followed; the binary keeps its original tested commit.

## Published party battle paths and retired comparison skills — 2026-10-02

Changes in [`4348308`](https://github.com/biscoBen/FFR-Vison-Studio/commit/4348308fd3b13c4e79ee37cec1ff2980a56d1d14),
[test package 37030912870](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37030912870).

- Remove the four temporary comparison Copies. Migrate old roster/config grants to the regular skills, collapse only
  same-tier alias duplicates, and preserve other edits and saved config files. Keep the working Verified effects.
- Fix party replacements installing but retaining normal battle sprites: redirect the selected party rows' actual
  runtime soft paths in `DT_BtlUnitAsset`. Preserve existing/new vision operations in that same table, party identity,
  original resource names and field/cutscene assets. Verify sprite, all texture paths and Crystal Fina's material.
- Record user observations for future comparison-skill work: literal names display as **Name** in battle despite
  correct menu labels, and MP is consumed but insufficient MP does not block casting. Investigation is deferred;
  these temporary copies are removed rather than extended.
- Passed local analysis, 41 focused Flutter tests, 178 Python tests and bundle checks. The actual engine serialized
  all eight party redirects with correct soft paths, preserving 718 original rows, a modified vision and an added vision.
  Windows passed the full Flutter suite, real engine startup, all Python tests, 12 launcher/updater checks,
  10 import checks and compilation. Verified the authenticated ZIP checksum, exact commit and bundled files/portraits.
  In-game replacement appearance still needs testing on the user's installation after rebuilding/installing and restarting.
- One code push and one build: the helper found no automatic push run and dispatched the exact commit once.
  CI took 4m22s; summed job execution was 7m45s. First complete candidate: 08:53:16 PDT; ZIP verified at 09:04:42 PDT
  and packaged-file checks completed at 09:05:08 PDT (11m52s from candidate, 21m18s from request).
  Local corrections, checks and trigger waiting are included. The requested remaining-Unverified list was prepared
  during CI; documentation-only publication notes followed.

## Published party texture fix and comparison abilities — 2026-10-02

Changes in [`6c5161b`](https://github.com/biscoBen/FFR-Vison-Studio/commit/6c5161bd7a5baff1c5ed7401780ed9f46e0ca258),
[test package 37026312897](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37026312897).

- Fix party battle replacement textures failing because the sprite converter writes whole pixel sizes as floats and
  the engine requires integer arguments. Preserve the exact atlas dimensions for all three texture layers.
- Add independently selectable **Chakra (Copy)**, **Cheer (Copy)**, **Purify (Copy)** (Ayaka awakening 2), and
  **Seal of Conviction (Copy)** (ordinary Dark variant) for same-battle comparisons. Copies retain the original game
  mechanics/visual bindings and use the safe motion fallback when missing; they do not receive Studio's donor effects
  or use custom-move slots. Keep source labels and the working reaction-color cleanup. In-game appearance needs testing.
- The actual engine wrote all three 2048×2048 texture layers, preserved all 1,167 original skill rows, and wrote/decoded
  both versions of all four timelines. Passed local analysis, 28 focused Flutter tests, 179 Python tests and bundle checks.
  Windows passed the full Flutter suite, real engine startup, all Python tests, 12 launcher/updater checks,
  10 import checks and compilation. Verified the authenticated release ZIP checksum, exact commit, all bundled fixes
  and eight party portraits. One code push/build; CI took 4m38s, with 7m56s of summed job execution.
- First complete candidate: 08:17:47 PDT; authenticated ZIP verified at 08:26:08 PDT, then packaged-file checks passed
  at 08:26:32 PDT (8m45s from candidate through checks, push, CI and verification). The usable release was ready about
  17 minutes after the request; documentation-only publication notes followed. In-game visual comparisons remain
  on the user's installation.

## Published bulk ability effect profiles — 2026-10-02

Changes in [`34726e4`](https://github.com/biscoBen/FFR-Vison-Studio/commit/34726e4c86062411f3f53f309640178ef9c89746),
[test package 37022585529](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37022585529).

- Extend missing-sequence visual profiles with native FFR physical impact styles, healing strength tiers, and effects
  selected from actual buff/status mechanics. Keep existing sequences, skill mechanics, hiding/source rules and the
  working Steal/Barrage presentations. The batch report distinguishes mapped effects from remaining motion-only or
  specialized entries; mapping checks do not prove every skill's appearance in-game.
- Read the actual target-particle field, skip native empty/caster spawn events, retarget selected combatants, and keep
  cleanup only for borrowed target particles. Add a whole-catalog audit command that reports all failures together
  and caches decoded references by source, mapping and decoder checksums.
- Decode all 1,400 supplied reference packages and audit 482 active mappings without errors. The real engine authored
  a batch of timelines and verified 108 distinct donor/target contracts; original definitions and hit counts stayed
  intact. Windows passed analysis, the full Flutter suite, real engine startup, 175 Python tests, both bundles,
  12 launcher/updater checks, 10 import checks and compilation. Verified the authenticated published ZIP checksum,
  exact commit/provenance and all packaged extension/portrait files. One code push/build; CI took 4m04s.
- First complete animation candidate: 14:46:18 UTC; authenticated ZIP checksum/provenance verified at 14:55:27 UTC
  (9m09s including final local checks, report generation, push, CI and download verification). Packaged-file checks
  followed before delivery. The party package was delivered first in about 12½ minutes; the
  animation investigation also required 7m45s of reference decoding and 7m35s of actual engine authored-output checks,
  overlapping other work. In-game appearance still requires representative testing on the user’s installation.

## Published party install fix and portraits — 2026-10-02

Changes in [`8d6f0be`](https://github.com/biscoBen/FFR-Vison-Studio/commit/8d6f0be5347f90d880299fa2f0c973cf59e65cc7),
[test package 37017624549](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37017624549).

- Fix party replacements failing at install because the engine's vision loader added an empty abilities field.
  Keep party identity and appearance-only validation intact, and cover the actual saved-roster loader in regression tests.
- Show bundled classic FFBE portraits for all eight original party characters on the main page and character page.
  Replacement models retain their own previews. Portraits require no sprite downloads.
- Windows passed the full Flutter suite, real engine startup, 169 Python tests including the actual engine roster loader,
  both bundles, 12 launcher/updater checks, 10 vision-import checks and compilation. Verified exact-commit provenance,
  ZIP checksum, all eight packaged portraits and the loader fix. One code push/build; CI took 4m18s.

## Published battle-only party appearances — 2026-10-02

Changes in [`51184ab`](https://github.com/biscoBen/FFR-Vison-Studio/commit/51184ab8aa67aecdc347a195738d77c60a583ae2),
[test package 36979683126](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36979683126).

- Add a third home section for the eight original party characters. Choose and preview FFBE battle models, including
  Crystal Fina, save/load replacements with character configs, and revert each character independently. Keep original
  party abilities, equipment, progression, walking and cutscene assets. Generate private battle packages and verify
  every original battle-table row/reference; retain native animation-pack names and Nichol's mixture phases.
- Validate the party table with the real engine serializer. Battle appearance and special cinematics still need an
  in-game check on the user's Windows installation.
- Windows passed analysis, 146 Flutter tests, separate real engine startup, 166 Python tests including both actual engine
  contracts, both bundles, 12 launcher/updater checks, 10 vision-import checks and compilation. Verified the published
  ZIP checksum, exact commit/provenance and all nine packaged extension files. Final CI took 4m41s; earlier corrections
  to the material class, setup whitelist and real-engine test fixture required extra runs. Publication notes use the
  documentation-only path.

## Published native-kit and batch effect repair — 2026-10-01

Changes in [`dfb763c`](https://github.com/biscoBen/FFR-Vison-Studio/commit/dfb763cd71f47097c7a7dbd999c956d976420fa1),
[test package 36970064551](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36970064551).

- Keep inherited abilities out of custom-animation repair when opening original visions, including unchanged Aileen.
  Explicit additions and replaced FFBE models still receive repair. Preserve original visions' shared impact rows.
- Validate donor Niagara imports against their actual class/package instead of the filtered UI effects index, avoiding
  false rejection of valid common particles. Audit all selected mapped effects before staging repairs; report every
  failure together with its skill, donor and exact bad package. Decode each shared donor once per build.
- Add regressions for all 26 original vision IDs, new grants, model replacement, off-roster shared reactions, common
  particles and batch failures. Actual Crust Driver/Needles appearance still needs the user's extracted game references;
  keep the current tested Steal/Barrage/Needles presentations while collecting those references.
- Windows passed analysis, 142 Flutter tests, separate real engine startup, 158 Python tests including the actual
  particle patcher, both bundles, 12 launcher/updater checks, 10 vision-import checks and compilation. Reused the single
  push build and verified the published ZIP checksum, exact commit/provenance and packaged repair files. CI took 4m47s
  with 8m54s of summed job execution. Publication notes use the documentation-only path.

## Published borrowed-effect table verification fix — 2026-10-01

Changes in [`aaf1d97`](https://github.com/biscoBen/FFR-Vison-Studio/commit/aaf1d97a5441ba790c530e709d97b28679747aff),
[test package 36967960917](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36967960917).

- Fix roster builds rejected after packing when borrowed skill effects intentionally update existing reaction rows,
  including Zidane's Free Energy and Meal Twister. Record the audited donor row and reconstruct exact expected cosmetic
  fields from original game data. Keep checks for wrong effect values, changed IDs, unrelated fields, missing rows,
  incompatible reports and explicit custom animations. Full game installation still needs a local retry.
- Windows passed analysis, 142 Flutter tests, separate genuine engine startup, 151 Python tests including the real
  particle patcher and normal post-build verifier regression, both bundles, 12 launcher/updater checks, 10 vision-import
  checks and compilation. Reused the single push build and verified the published ZIP checksum, exact commit/provenance
  and all bundled extension files. CI took 4m57s with 8m35s of summed job execution; Flutter setup took 2m07s on validation
  and 1m40s on compilation, while compilation took 1m49s. Publication notes use the documentation-only path.

## Published visible Steal and monster Needle trials — 2026-10-01

Changes in [`0c47de3`](https://github.com/biscoBen/FFR-Vison-Studio/commit/0c47de34d93b1551f1f9845949627bc3087a1c8f),
[test package 36966862412](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36966862412).

- Make the Steal trial visible: the receiving vision approaches, uses its ready pose, resolves one original item theft,
  then returns to position/idle. Borrow ordinary monster Needle's shared Stab/Needle target effects for 1,000 and 10,000
  Needles, preserving their original one-hit fixed damage. Mark the two monster experiments as Verified FFR mob tests.
  Keep Barrage, skill mechanics, reaction colors, saved IDs and every selection/hiding rule intact.
- Add **MR=N** to all 128 exact-ID Bond reward assignments documented in the ability-source PDF, including Steal's
  **Source: Zidane; MR=1**. These labels describe reward sources, not animation donors or awakening tiers.
- Battle appearance, successful theft and monster-particle placement need in-game testing after rebuilding/installing
  the roster mod. Steal uses an explicit presentation rather than a recovered Zidane-specific timeline; Needles use
  the available ordinary monster Needle effects, not absent dedicated 1,000/10,000 sequences.
- Windows passed analysis, 142 Flutter tests, separate real engine startup, 148 Python tests including the actual
  particle patcher, both bundles, 12 launcher/updater checks, 10 vision-import checks and compilation. Reused the single
  push run and verified the published ZIP checksum, exact commit/provenance and all packaged extension files. CI took
  4m40s with 7m28s of summed job execution; compilation took 2m13s and Flutter setup 1m40s on the compile runner.

## Published particle-reference installation fix — 2026-10-01

Changes through [`a7862de`](https://github.com/biscoBen/FFR-Vison-Studio/commit/a7862de2d84fb733beb39da8c1b782fe57078000),
[test package 36963738087](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36963738087).

- Correct borrowed skill effects after the `$struct` fix: convert the engine's `import:name` dump labels into full
  particle asset paths with explicit Niagara classes, including secondary and friend/enemy particle references.
  Verify every reference against the written package and keep failed builds from reaching mod installation.
  Preserve skill mechanics, target selection, reaction colors and roster settings. Add reference-format regressions
  and a Windows check against the actual checksum-pinned engine patcher; full game installation needs a local retry.
- Windows passed analysis, 140 Flutter tests, genuine engine startup, 145 Python tests (including direct calls to the
  real engine's particle patcher/dump functions), both bundles, 12 launcher/updater and 10 vision-import checks, and
  compilation. Verified the published ZIP checksum, exact commit/provenance and packaged fix. Final CI took 5m43s
  with 9m04s of summed job execution; Flutter setup on the compile runner took 3m32s versus 1m12s compiling. A test-call
  correction superseded the first automatic run during setup; it published nothing. Reused the final push run.
  Close Studio, reopen the test shortcut to update, then retry the existing roster's build/install.

## Published skill-effect installation fix — 2026-10-01

Changes in [`fb7fb3d`](https://github.com/biscoBen/FFR-Vison-Studio/commit/fb7fb3d4bb4d822c62fd35dbbd279925a1bad658),
[test package 36962412907](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36962412907).

- Fix roster builds failing while writing borrowed skill effects (including Banishga) because `seqdump`'s `$struct`
  annotations were passed to the engine as real Niagara fields. Remove only those annotations from bytecode patches,
  including nested structs/arrays; preserve effect settings/imports, skill mechanics, reaction colors and saved rosters.
  Add a regression reproducing the rejected patch. Full installation and battle appearance need an in-game retry.
- Windows passed analysis, 140 Flutter tests, the separate real engine-startup test, 142 Python tests, both bundle
  checks, 12 launcher/updater and 10 vision-import checks, and compilation. Reused the automatic push build and verified
  the published ZIP checksum, exact commit/provenance and bundled fix. One code push produced one Windows build;
  CI took 4m51s with 8m47s of summed job execution. Close Studio, reopen the test shortcut to update, then retry the
  existing roster's build/install; the failed build stopped before replacing the installed mod.

## Published Steal and Barrage animation trials — 2026-10-01

Changes in [`62ede23`](https://github.com/biscoBen/FFR-Vison-Studio/commit/62ede23dae82a78d9d1d5066644c6b03c0847805),
[test package 36960649168](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36960649168).

- Add two animation experiments: player Steal keeps FFR's original routing instead of Studio's casting fallback;
  Barrage on FFBE-backed visions imports four cycles of that vision's own attack poses and FFBE impact timing.
  Preserve FFR's four hits, random targeting, skill mechanics, reaction colors and movement cleanup. Mark both as
  Verified FFR/FFBE tests to identify the touched entries. Exact resemblance to Zidane's Steal and battle appearance
  require in-game testing; the label tracks the implemented experiment, not a completed battle test.
- Windows passed analysis, 140 Flutter tests, the separate real engine-startup test, 141 Python tests, extension
  verification, 12 launcher/updater and 10 vision-import checks, and compilation. The helper reused the push run and
  verified the published ZIP checksum and exact commit/build provenance. One code push produced one Windows build.
  The workflow took 4m45s with 8m04s of summed job execution; Flutter setup took 86–87s per runner. A checksum-verified
  conversion of real A2 FFBE sprites also passed. Update Studio and rebuild/install the roster mod before testing.

## Published same-name and elemental target effects — 2026-10-01

Changes in [`b927015`](https://github.com/biscoBen/FFR-Vison-Studio/commit/b927015e7467270902130cf9d38a74c349ce019d),
[test package 36947606617](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36947606617).

- Reuse native target particle effects for missing same-name skills even when their mechanics differ, then select
  elemental/power-tier effects for remaining physical and magic attacks. Stone Slam/Surge's three tiers use Stone,
  Stonera and Stonega Blade. Preserve receiving skills' damage, targets, hit counts/ratios, costs and gameplay effects,
  with the vision's own attack/casting motion. Import actual Niagara references into the generated timeline; report an
  error if a mapped effect cannot be prepared instead of silently delivering a motion-only mod.
- Mark covered entries **(Verified)** while retaining source/awakening descriptions and every existing hiding rule.
  This label tracks the new visual mappings; in-game effect appearance still needs testing. Keep the white-state
  correction, which the user confirmed works, and existing/custom sequences and Resonance behavior.
- Windows passed analysis, 139 Flutter tests plus the separate genuine engine-startup test, 132 Python regressions,
  both extension checks, 12 launcher/updater checks, 10 vision-import checks and compilation. The helper joined the
  automatic run and verified the published ZIP's SHA-256 and exact commit/build provenance through authenticated
  downloads. One code push produced one build. The workflow took 6m33s, with 9m53s of summed job execution; Flutter
  setup took 216s in validation and 86s in compilation. These are measured timings; slower SDK setup was the bottleneck.
  The catalog mapping covers 113 of the original 175 entries and additional same-name variants such as Tronn's Fira.
  Rebuild/install the roster mod after updating Studio, then test the new target effects in-game.

## Published ability visual profiles and reaction-color correction — 2026-10-01

Changes through [`b275160`](https://github.com/biscoBen/FFR-Vison-Studio/commit/b27516073c7543ed1f627b9d5f4f2f7408315a06),
[test package 36942693908](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36942693908).

- Restore reaction color handling in generated ordinary-skill fallback timelines, which previously inherited the
  limit-burst scheduler's disabled color flag. Keep hit count, targets and mechanics intact. This is a candidate fix
  for friendly targets remaining white after unverified skills; persistence/recovery still needs an in-game test.

- Add visual-only animation profiles for Bladeblitz, Aero Blade, Aquatic Synergy and Arise when those abilities are
  selected and lack an existing or explicit custom sequence. Reuse audited native slash, wind, three-hit water and
  revival visuals with the receiving vision's preparation/release motions. Preserve original mechanics, hit ratios,
  consecutive-use bonuses and full revival strength. Keep donor assets separate, fit motions to the sequence's timing,
  and report a fallback when game assets cannot pass the audit. In-game appearance still requires testing.

- Windows passed analysis, 136 Flutter tests plus the separate genuine engine-startup test, 123 Python tests, both
  extension checks, 12 launcher/updater checks, 10 vision-import checks and compilation. The helper reused the push run
  and verified the published ZIP checksum and exact commit/build provenance. A first run caught Windows-specific paths
  in two new tests; the corrected final commit passed every required gate. The final workflow took 4m15s, with 6m49s
  of summed job execution; Flutter setup took 91s in validation and 73s in compilation. These are measured run timings.
- A separate 175-skill animation plan contains searchable HTML, CSV and Markdown proposals; only the four profiles above
  were implemented. Update Studio and rebuild/install the roster mod before testing; existing mods are not replaced by
  the app update. The plan was delivered separately because GitHub rejected its release upload with HTTP 400.

## Published on-demand sprites and restored character previews — 2026-10-01

Changes in [`bdc92b4`](https://github.com/biscoBen/FFR-Vison-Studio/commit/bdc92b4d335a0673699548b48f97ddb7bca5f1fa),
[test package 36938521499](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36938521499).

- Restore character sprite downloads on demand; startup, restart and game setup no longer download every hosted form.
- Restore the selected appearance and required base-form artwork when loading character configs, and prepare missing
  engine preview data when reopening the character. Keep saved settings, existing artwork and cached downloads.
  Config preparation failures preserve the roster and can be retried. Analysis and all 136 Flutter tests passed locally
  and on Windows. Windows also passed the separate genuine engine-startup test, 113 Python tests, both extension
  checks, 12 launcher/updater checks and 10 vision-import checks. One code push produced one Windows build; the helper
  reused that run and verified the published ZIP checksum and exact commit/build provenance.

## Published faster build and release workflow — 2026-10-01

Changes in [`f749adf`](https://github.com/biscoBen/FFR-Vison-Studio/commit/f749adfd32f6500ab3c5ae5cda9b83e131ea0e31),
[test package 36935925830](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36935925830).

- Avoid Windows rebuilds and extra releases for README/CHANGELOG-only updates while completing the existing check.
  Run full Windows validation and compilation concurrently, preserve every required check, and publish only after both
  succeed. Pin the verified Flutter version, keep safe SDK/Pub/engine caches, and avoid repeated package resolution.
  Protect manual builds and publication while cancelling superseded automatic validation/compilation jobs.
- Reuse the exact commit's running or successful build before dispatching, verifying workflow/build inputs and downloaded
  provenance. Keep explicit force rebuilds and authenticated downloads; reuse the verified test ZIP if artifact storage
  is blocked. Reject incompatible or missing build outputs without substituting another commit's binary.
  Windows CI passed analysis, 134 Flutter tests plus the separate real frozen-engine startup test, 113 Python tests,
  both bundled-extension checks, 12 launcher/updater checks, 10 official-vision import checks and compilation.
  The genuine startup test restored and checksum-verified the existing engine cache without another host download.
  The published ZIP's SHA-256, branch/commit/run/build metadata and embedded build provenance were verified through
  the authenticated release endpoint. The helper joined the push build and then reused its successful package in
  7.36 seconds, with only one workflow run for the code commit.
- Measured workflow wall time was 4m18s, compared with 6m00s for the previous final sprite build (1m42s less).
  Summed runner execution increased from 5m52s to 7m40s because the two Windows jobs each prepare Flutter.
  Flutter/Pub cache setup remained the largest cost: 91s for validation and 105s for compilation. These are observations
  from individual runs, not guaranteed savings. First complete candidate to verified release took 8m44s, including
  review corrections, local checks, CI waiting and download verification; final documentation verification is additional.

## Published startup character sprites — 2026-10-01

Changes through [`e71d92b`](https://github.com/biscoBen/FFR-Vison-Studio/commit/e71d92b8b1be2f25162057e8e4b5ec83b086dc7c),
[test package 36933213624](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36933213624).

- Download all hosted character sprite forms on startup, including units never selected in Add a unit. Check the full
  sprite-file inventory each launch, restore missing sheets, icons and animation files, and reuse complete packs and
  verified ZIPs. Keep existing artwork and roster edits. Prepare the engine's unit data before opening the roster;
  show progress during the first download, report failures, and retry missing forms on the next launch.
  Flutter analysis, 134 Flutter tests, 95 Python regressions and both bundled-extension checksum checks passed.
  Startup regressions cover all forms without picker interaction, persistent cache reuse, deleted files, retained artwork,
  incomplete markers, checksum errors, preparation/index failures, offline starts and retrying deferred downloads.
  Recheck deferred unit preparation after first-run game setup, before showing the roster.
  Windows CI passed analysis and the full suite, the frozen-engine fresh setup, Python tests, launcher/import checks
  and the release build. Both sprite builds reused the cached engine archive without downloading from its original host.
  The downloaded test ZIP's SHA-256, integrity and branch/commit/run metadata were verified. Live character rendering
  still needs verification on a tester's PC. The first full download takes longer and needs space for all hosted forms.

## Published cached Windows engine — 2026-10-01

Changes in [`61e4c7a`](https://github.com/biscoBen/FFR-Vison-Studio/commit/61e4c7aeb9b1ab183fa4c87c2761554ff9df5c88),
[test package 36928203827](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36928203827).

- Reuse the Windows startup test engine archive from a cache keyed by its pinned SHA-256, independent of app commits.
  Verify cached bytes on every build and keep extracting a fresh engine for the startup test. Fetch from the existing
  engine URL only when the archive is missing; failed downloads and checksum mismatches never become cached copies.
  Cache regressions passed locally in PowerShell, including reuse, corrupt copies and partial-download cleanup;
  all 95 Python regressions and both extension checksums passed. Windows CI passed Flutter analysis and the full suite,
  cache regressions, genuine frozen-engine fresh startup, Python tests, launcher/import checks and the release build,
  and saved the verified engine archive to the Actions cache.
  A subsequent [test package 36929060613](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36929060613)
  passed the same Windows checks and confirmed that real startup reused the checksum-verified cache without downloading
  from the engine host. The downloaded test ZIP's SHA-256 and branch/commit/run metadata were verified.
  GitHub may evict an unused cache, which restores the existing download path.

## Published complete ability sources and build diagnostics — 2026-10-01

Changes through [`b05e63c`](https://github.com/biscoBen/FFR-Vison-Studio/commit/b05e63c9672a1c40f1ff50c4233266db18d1a76f),
[test package 36926851597](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36926851597).

- Fix incomplete PDF source labels: include the additional game abilities and passives on pages 39–90, which were
  omitted from the first reference update. Add the missing 812 assigned ability sources and 61 passive sources;
  the complete reference now covers **1,141 ability IDs** and **343 passive IDs**. Preserve exact-ID matching,
  qualified internal labels, explicit awakening tiers, all picker hiding rules and saved/equipped grants. The full
  document leaves 61 original game definitions without a confirmed source; those remain unlabelled unless game
  tables establish an owner.
- Include fresh Windows engine setup errors in GitHub check annotations so cloud testing can diagnose failures
  when the separate log storage is unavailable. Keep the pinned checksum and required startup test.
- Validation: PDF mappings were checked against all tables, including late-page sources and unchanged filters/saved
  grants. Windows CI passed Flutter analysis and the full suite, genuine frozen-engine fresh startup, 95 Python tests,
  launcher/import checks and the release build. The downloaded test ZIP's SHA-256 and branch/commit/run metadata were
  verified. Previous engine downloads returned HTTP 403; the unchanged workflow's retry succeeded. Direct artifact
  downloading from this cloud workspace returned Forbidden; the existing published test ZIP was downloaded successfully.
  In-game rendering still requires a tester's PC.

## Published PDF sources and awakening tiers — 2026-10-01

Changes in [`867109e`](https://github.com/biscoBen/FFR-Vison-Studio/commit/867109eaceefbd1350af841daea81ae4820db020),
[test package 36911084005](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36911084005).

- Label visible abilities, passives and Resonance options from the October 1, 2026 ability-source PDF by exact ID,
  including verified entries and documented esper/equipment sources. Keep one sorted, deduplicated **Source: <unit names>**
  label alongside known game-table owners. The reference covers 611 owner labels across the Studio's 635 entries;
  shared abilities may have other sources. Qualify the six internal-owner-only labels and leave the 24 entries without
  assignments unlabelled unless the game tables establish a source.
- Add **awakening=N** for the 322 explicitly documented tiers, identifying the reference owner when several sources
  are shown. Bond rewards and linked variants do not imply a tier. Preserve all hiding rules, verification status,
  equipped/saved IDs, compact descriptions, click-to-open selectable details and drag-to-equip behavior.
- Validation: independently extracted all 635 Studio PDF rows and checked every bundled mapping. Flutter analysis
  passed with no issues; **118 Flutter tests** and **95 Python tests** passed, including hiding, click/drag and source-label
  regressions. Both bundled extensions passed checksum checks. The Windows-only fresh-engine test was skipped on Linux;
  Windows CI subsequently passed the release build, genuine frozen-engine fresh startup and launcher/import checks.
  The published ZIP checksum and commit metadata were verified; in-game rendering still needs a tester's PC.

## Published click descriptions and source labels — 2026-10-01

Changes in [`ce453b6`](https://github.com/biscoBen/FFR-Vison-Studio/commit/ce453b6f8ed562a2b7ba360b4395601dbf15a762),
[test package 36898247358](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36898247358).

- Open complete ability/passive descriptions by clicking their name/description area instead of hovering. Use a
  scrollable window with selectable text and a Close button across library, learned and MR entries. Keep dragging
  library entries to equip them; a drag does not open details or change the compact row descriptions.
- Standardize displayed owner names as **Source: <unit names>**. Combine default vision owners and confirmed enemy/party
  sources into one sorted label without duplicates, preserving existing verification status and ownership rules.

Windows validation passed: analysis, **112 Flutter tests**, a separate genuine frozen-engine fresh-start check,
**95 Python tests**, launcher/import checks and the release build. Mouse interaction checks verify no description
on hover, clicking equipped/unequipped entries without changing the roster, dragging abilities/passives to tiers
without opening details, and scrolling complete selectable descriptions. Source-label checks cover default vision
owners, confirmed non-vision sources and deduplication. The downloaded package's checksum, branch/commit metadata
and bundled library sources match the tested commit.

## Published default vision revert — 2026-10-01

Changes in [`f36e8cd`](https://github.com/biscoBen/FFR-Vison-Studio/commit/f36e8cd37477c7781b261223a4e48bdd61f873b2),
[test package 36893119483](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36893119483).

- Add **Revert to original** to the default vision popup beside **Edit vision** and **Change model**. Reuse the
  full reset action to restore the original model, abilities, passives, stats, Resonance and MR rewards by removing
  only that vision's overrides. Confirmation explains that the next build/install applies the reset to the game.
  Cancel keeps edits intact. The button is disabled for untouched visions and while a build is running.
- Share the reset confirmation between the popup and character-page reset, with a clearly labelled **Revert to original**
  confirmation button for default visions. Added units retain their existing Remove action.
- Keep build/install available after reverting the last edited vision when a Studio mod is already installed, so
  the original roster can replace that installed build without requiring a new custom vision.

Windows validation passed: analysis, **110 Flutter tests**, a separate genuine frozen-engine fresh-start check,
**95 Python tests**, launcher/import checks and the release build. Regression checks cover full reset, cancellation,
preserving other roster edits, disabled actions and removing stale model output during a clean rebuild. The
downloaded ZIP's checksum, branch/commit metadata and bundled native-vision sources were verified. Applying the
reset to an actual game installation still needs a build/install and in-game check on the tester's PC.

## Published compact ability library — 2026-10-01

Changes through [`703858c`](https://github.com/biscoBen/FFR-Vison-Studio/commit/703858cc7e7908bb60c0a85a191627168629855f),
[test package 36887346776](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36887346776).

- Reserve the 26 default vision Resonances and their alternate-target row for Resonance selection. Hide them from
  ordinary Abilities and MR ability pickers, together with untranslated names and entries named **Attack**. Keep
  existing equipped abilities, MR rewards, full catalog rows and saved configurations intact.
- Show ability rows as a short effect description followed by **Type; Target; Accuracy; Break; Power; MP; Hits;
  Crit Chance**. Wrap the stat line instead of cutting it off. Preserve real variant values and recorded zeroes;
  omit missing values. Generate missing damage/healing/effect summaries only from recorded mechanics.
- Keep the previous complete recorded descriptions, effects and variant details in scrollable hover text, including
  library and learned rows. Apply the same compact ability display to MR reward selection.
- Add **Source: <unit names>** labels for confirmed non-vision users, including enemies and base party members.
  Trace original command assignments, level grants, passives, explicit AI skill IDs and alternate-target references;
  resolve English unit names from the game's localization. Source ownership does not change **(Unverified)** status.
  Missing/ambiguous sources remain unlabelled; matching skill names alone never proves ownership.
- Validation: game source labels require the prepared game tables on the tester's PC. Cloud regression fixtures verify
  tracing/filtering, compact values and full hover behavior; a full game install and in-game rendering are unavailable here.

Windows validation passed: analysis, **106 Flutter tests**, a separate genuine frozen-engine fresh-start check,
**94 Python tests**, launcher/import checks and the release build. The downloaded package's SHA-256 and bundled
managed sources match the tested commit. Local Flutter/PowerShell execution remains limited by cloud workspace
process/thread exhaustion; fresh-start validation ran on the Windows runner.

## Published skill-library cleanup — 2026-09-30

Changes in [`b23d052`](https://github.com/biscoBen/FFR-Vison-Studio/commit/b23d0525eeeee24960bb3c491073636c12c5b7d8),
[test package 36821957800](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36821957800).

- Show the owning default vision names beside **(Unverified)** on abilities and passives, including MR reward pickers.
  Ownership comes from original awakening/MR grants, commands, level-up skills, base passives and alternate target modes.
- Hide an unused Unverified ability when a verified version has identical combat mechanics. Matching ignores internal
  IDs, icons, voices, debug/command lists, alternate-target menu settings and map/menu effects. Default-owned or
  roster-used IDs remain visible; different combat targets, power, costs, accuracy, hit data and effects remain distinct.
  Filtering affects Studio's pickers only; original game tables, saved configurations and equipped IDs remain intact.
- Standardize ability/passive descriptions with consistently ordered recorded stats and effects. Remove voice labels,
  internal IDs, debug fields and temporary placeholder descriptions. Missing values are omitted; undocumented effect
  parameters remain their recorded numbers. Full descriptions remain available on hover.
- Expand this changelog to cover all fork additions and fixes, link it from the README and document keeping it current.

## Published fork test updates — 2026-09-30

Changes through [`dcdab31`](https://github.com/biscoBen/FFR-Vison-Studio/commit/dcdab31ce2f2940530b728c0ee9549e2fbf84f94),
[test package 36817188628](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-36817188628).

### Vision roster and editing

- Expose previously hidden abilities and passives, including specialized moves, skills without dedicated sequences,
  unit-restricted moves and Japanese passives. Mark the exposed entries **(Unverified)**.
- Edit all **26 original visions**, including the nine original FFBE visions. Keep their original game identities,
  acquisition/progression data and existing Resonances while changing kits or models.
- Add **Change model**, **Use original model** and **Reset vision**. Replacement sprites can come from the normal
  FFBE picker or bundled Crystal Fina. Restoring a model preserves kit edits; resetting removes the original override.
- Add a per-vision **MR** tab for all ten ranks: edit stat rewards, abilities, passives and master rewards; move or remove
  rewards. Preserve original unlock-point requirements and untouched rewards, with up to five rewards per rank.
- Split the home roster into independently scrolling **Added visions** and **Default visions** boxes. Edited original
  visions appear once in the default box with their current edits.
- Bundle FFBE portrait PNGs for all 26 default visions in Studio's list and character page. Original portraits provide
  a fallback; replacement models show their selected model's portrait.

### Saving and migration

- Add **Save character config** and **Load character config**. Save the full kit, stats, passives, resistances, MR rewards,
  Resonance mechanics, animation settings and advanced configuration. Restore removed characters and resolve ID/name
  collisions; back up the roster before applying imports.
- Add **Save all character configs** and **Load all character configs** to the main page. Validate and restore a whole
  saved roster together while preserving other entries. Original-vision overrides and model selections are included.
- Copy official Studio visions once into an empty test profile, including imported artwork. Keep official and test
  profiles separate. Normalize migrated arrays correctly under Windows PowerShell 5.1.

### Crystal Fina

- Add **Crystal Fina** to the normal Add unit picker with the supplied profile, abilities, passives, stats and
  **Crystal Restoration Resonance**, and bundle all supplied sprite and animation assets.
- Install her engine integration automatically at startup and after compatible engine updates. Apply the supplied
  transparency material only to Crystal Fina in each fresh full-roster build; allocate free IDs and retarget texture
  references when needed. Preserve imported/user-edited profiles and artwork.
- Preserve binary material/sprite bytes across Windows checkouts and verify managed asset checksums.

### Animations, library and build fixes

- Prepare complete unit packs before Add unit previews, so animations appear before adding a character.
- Prepare original sprite assets before building model replacements, fixing Leah's missing-asset installation error
  and the same failure for other original visions.
- Remove the accidental ceiling imposed by 16 reserved command-icon tags. Extra added visions share a registered donor
  command icon. Automated checks cover 64 added entries; actual game capacity still needs in-game testing.
- Recover missing FFBE attack, magic and other sprite motions from matching, checksum-verified asset-dump files.
  Preserve existing and edited artwork; keep original assets if a repair is unavailable or incompatible.
- Generate basic attack/casting timelines for selected ordinary skills without a game sequence, including awakening
  and MR ActiveSkill grants. Basic fallbacks supply unit movement, not missing original particles or audio.
- Automatically reuse compatible same-name native game animations after auditing complete mechanics and actual
  timelines. Retarget hit/reaction references, preserve native effects/audio and recipient stats, and reject specialized
  or owner-specific timelines. Existing/custom sequences take precedence. Write a per-build animation repair report.
- Collapse proven unused exact skill/passive duplicates in Studio while keeping original-referenced and roster-used IDs.
  Explain actual same-name differences and show complete descriptions in scrollable hover text.
- Shorten managed Crystal Fina/native-extension staging paths, fixing fresh setup failures in long Windows paths such as
  Downloads/Sephira-Studio-Test. Verify compact staging folders against their full bundle checksums.
- Preserve engine-fixture line endings and wait for configuration file operations in tests, improving Windows validation.

### Test distribution and development

- Publish validated Windows prereleases automatically for `Sephira's-Update`, and build the branch on pushes and manual
  workflow runs. Run Flutter analysis/tests, Python checks, genuine frozen-engine setup tests and launcher/import tests.
- Add **Start Studio Test.cmd** and the **Sephira Studio Test** desktop shortcut. Check for the latest tested branch
  package, verify its SHA256 digest and launch it. Preserve settings and roster data across updates, and retain the
  installed app when updates fail or the network is unavailable.
- Give test packages a separate frontend update channel and local data folder. Keep `master` available as a clean
  inherited baseline. Keep the executable and workflow version stamp at compatible build 15.
- Add a cloud build helper that requests, tracks and downloads Windows artifacts, checking branch, commit and run.
  Support a temporary unpublished download when artifact storage is blocked. Compile when the host's version manifest
  is unavailable, while retaining runtime compatibility checks.

These are Windows test packages. Cloud checks cover app/engine startup and update preservation; game rendering,
combat behavior and full-roster mod installation still require testing against an installed game.

## Original project release history

## 1.0.0 build 7 — 2026-09-06

- The host answered with 429 (too many requests) and 404s once many people used the app at the same time. The add-unit
  dialog fetched one icon per row and one per look straight from the host, and the host only had one icon per unit.
  The icons are now one pack (every look, about 4 MB) downloaded once at setup and read from disk; the pickers make no
  host requests at all.
- Downloads back off on 429 and 5xx (honouring Retry-After) instead of failing at once; a missing file still fails fast.
- A pack that did not change between builds keeps its earlier version: this build reuses the build 6 engine (76 MB) and
  data, so updating downloads the app and the icons only.
- Update now: the helper is started through `cmd /c start`, the one route that outlives the closing app (the build 6
  helper never ran).

## 1.0.0 build 6 — 2026-09-06

- Limit-burst, magic and victory previews for Super Limit Break, Overdrive and every newer unit: the engine now finds
  `unit_limit_atk_cgs` next to `unit_limitatk_cgs` (both spellings of the archives).
- Brave Shift and Super Limit Break pairs are one unit with two looks ("7★ · Brave Shift", "7★ · Super Limit Break").
  A shifted look borrows its victory and down motions from the base form, in the viewer and in the mod.
- 53 units that exist only in the live JP client (Rain & Lasswell and others) are in the picker, with their sprites hosted.
- "Studio moves" in the Abilities library: Raegen Blast (staggers every enemy, no damage) can be granted like any ability.
- Unit page header: Back on the left, "Play like a vision the game has" and "Remove" on the right; the left column is
  the entry only.
- "Update now": the app downloads the new build, verifies it, stages it and restarts itself through a small PowerShell
  helper (started via `cmd /c start`, the one launch route that outlives the closing app); the download page remains the
  fallback, and read-only app folders are sent there.
- Developer environment (the script lives in the project repository): build a numbered pack, serve it locally, start the
  app from a scratch app-data folder.

## 1.0.0 build 5 — 2026-09-06

- Sprite packs downloaded after the engine started were invisible to it (cached folder scan): units lost their sprites and
  the build crashed on the missing sheet. The downloaded root is now checked live, the index rebuild rescans, and a build
  first heals units whose sprite copy is missing.
- Crashing tool scripts no longer show a message box: the traceback goes to `logs/engine-errors.log` and the process exits
  with code 1. Every build's console is saved as `logs/build-<stamp>.log`.
- Setup and build consoles are selectable and have a Copy button.

## 1.0.0 build 4 — 2026-09-05

- Release audit worked through: version and build number stamped into the exe and shown in the header, About page,
  offline start on installed packs, engine-exit watch with restart, close guard during builds, update notice, engine log
  files with "Logs folder" buttons, resumable downloads, sprite pack completion marker, single instance, safe unzip,
  minimum window 960×600, framed choices instead of radios, unit tests.
- Resonance step: the three animations that play the unit's limit burst come first with a description each; the owner
  cinematics are marked; a warning when the unit's motion is longer than the animation's window; caption-lines picker;
  Brave Exvius limit-burst hint; collapsible timeline. The auto-stretch measures from the first LB1 key.

## 1.0.3 (renumbered as build 3) — 2026-09-05

- All 3,800 Brave Exvius sprite forms hosted on sprite shards; every unit's face icon on the site; the add-unit dialog
  downloads a unit's pack when it is picked and shows its motions with arrows; rarity reads 1★..7★, NV, NV+.
- "Play like a vision the game has" copies a game vision's kit, stats, type, roles and Resonance numbers.
- Night edition toggle. Exe renamed `FFR Vision Studio.exe`.

## 1.0.1 (build 1) — 2026-09-05

- Install backups and "Restore the original game". Rain's face as the app icon and in the wordmark. Download page with the
  two game logos.

## 1.0.0 — 2026-09-05

- First native release: two-page spread, four Easy-mode steps with drag-and-drop tiers, build and install, first-run
  downloads of the engine and data packs, game folder detection.
