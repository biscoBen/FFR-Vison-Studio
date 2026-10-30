# Changelog

Fork-specific changes for [biscoBen/FFR-Vison-Studio](https://github.com/biscoBen/FFR-Vison-Studio),
on `Sephira's-Update`, compared with the inherited `master` snapshot
[`d94c685`](https://github.com/biscoBen/FFR-Vison-Studio/commit/d94c685c9dd1b1502c8676e03e679f54a9a05086).
The original project's release notes are preserved below the fork history.

Windows test packages keep version **1.0.0, build 15** for host compatibility. Studio now displays the managed
test-update version; the commit and workflow run identify the exact package. Dates below use America/Los_Angeles. Published entries describe tested branch packages;
**Unreleased** entries are work awaiting a successful package build.

## Unreleased

### Returned full-game reference audit — 2026-10-22

- Confirm successful collection after the private-mappings fix: 106 scoped tables, 58,035 inventory assets and
  7,087 timeline files from full-game fingerprint `8ce7a0746d0cc1b2c9b97e44d186f8036212b156fc52b91571da94703168b5b4`.
  Record archive provenance and the comparison in the README release checklist. Captured unit, AI, skill/passive,
  vision and mastery data match the demo; this does not establish runtime compatibility.
- Audit the actual production skill composite, including definition pointers and character links. Candidate route
  coverage grows from 286 to 1,074 of 1,167 definitions; 788 gain routes, none lose all routes, and 798 distinct route
  sets change. All 21 named missing-visual cases (22 candidate IDs) have visual and sound timeline packages present.
  Retain the Waterga variant uncertainty and require live direction, sound and timing tests.
- Identify remaining migration work: builder/extensions select demo composites and generic-only donors; the reference
  omits map, shop, stage, dialogue and UI table rows. The collector's skill-route report also overlooks production-only
  tables, so its 286 changed-skills count is incomplete; this audit uses the original captured rows instead.
  Documentation only: no code/engine update, gameplay changes, asset publication or new binary. Rollback checkpoint retained.

### Full-game preparation observation — 2026-10-22

- Record the user's full-game preparation: 2,618 tables, followed by retries for 191 unread tables. The follow-up
  screenshot finished **ready**, with 118 unread tables outside the setup's required set. No hang is confirmed.
  The existing preparation retry loop does not log each table individually. Preparation success is not a live mod pass.
- Verify that preparation writes the selected folder to global engine config before reading tables; collection
  reads that same saved path. Restarting is not needed to switch from the demo. Collection can start after the
  preparation worker stops without requiring a successful preparation, though the native reader may still fail.
  Documentation only; no compatibility pass, new extraction, parser fix or new Studio binary is claimed.

### Consolidated original-enemy missing visuals — 2026-10-17

- Record that all targeted practice-comparison skills show no animation on their original enemies. Add the
  user's eight new failed names: Malboro Marquis's Flatten; Sheratan's Octostrike, Branch Spear, Stonega and
  Aeroga; Alpherg's Reflectga, Waterga and Flare. Other attacks the user actually received showed animations;
  do not infer that every skill in the enemies' AI was tested.
- Consolidate 19 failed skill names across all eleven named practice opponents, carrying forward Watcher's
  Megavolt/Atomic Ray and Malbodoom's Bad Breath/Pollen where the exact IDs recur. Flag additional shared
  Pollen on Marquis/Sheratan and Aeroga on Alpherg as native-AI references without inventing separate cast
  observations. Preserve earlier successful Watcher/Malbodoom casts and the working optional FFBE Needles import.
- Match enemy-specific spell variants instead of names alone: Sheratan's Stonega 255170/Aeroga 250190,
  Alpherg's Flare 250330, and two possible Waterga IDs (250150 single-target, 255110 group). Pollen 500690
  and Alluring Pollen 503770 remain separate. Blighted Gloom/Carmine Inferno retain their earlier imported-vision
  failure status without a new original-enemy observation. No new trace, asset repair, substitute or package is
  implied. Verify the recorded ID associations against the collected native AI/skill tables; documentation only.

### Original Watcher and Malbodoom test results — 2026-10-17

- Record the user's original-enemy tests: Watcher's Missile, Laser, Machine Gun and Poison Gas show visuals;
  Megavolt and Atomic Ray do not. Malbodoom's Whip and Digestive Fluid show visuals; Bad Breath and Pollen do not.
- Match the four failed names to the tested units' native AI skill references. Keep Pollen (500690) separate
  from Alluring Pollen (503770). Atomic Ray/Bad Breath now have native enemy-side blank reports too; an
  imported-vision-only binding fix is insufficient to explain these observations. No new trace or visual fix
  is implied by this documentation update.

### Original-enemy animation comparison candidates — 2026-10-17

- Record ten included enemy/skill pairs covering eight missing-skill names, including Watcher/Ganymede for
  Atomic Ray and Malbodoom/Malboro Marquis for Bad Breath. Check exact native AI references, AI Blueprint and
  collected model/material/texture packages. Identify Watcher and Malbodoom as the simplest next practice tests.
- Distinguish included assets from natural demo story access and live playback. No new practice encounter or
  skill change is installed by this documentation update. Record that the first blank 1,000 Needles retest had
  its optional FFBE-import switch off; the user subsequently confirmed playback with it enabled, reporting
  superimposed streaks and missing sound (addressed in the published update below).

### Cactuar visual baseline — 2026-10-17

- Record the user's follow-up: the tested Cactuar's own **1,000 Needles** also shows no visible animation.
  No tracer was run. This adds an original-enemy visual observation, while its exact runtime route and whether
  another original presentation exists remain unconfirmed. Do not generalize it to other failed skills or Cactuar variants.
- Do not mark its original visuals verified; preserve native-only behavior. The existing ordinary-Needle substitute remains
  under **Use our skill changes**. Save the comparison in the shared full-release checklist. Documentation only;
  no new Studio package, substitute, gameplay change or repeated extraction is required for this observation.

## Published native-row bypass for the F7 crash — 2026-10-29

Code [`b73f538`](https://github.com/biscoBen/FFR-Vison-Studio/commit/b73f538bc3f485f0407569aeac1c3597b5d7ebc4) ·
[Studio test 1.2.137](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40974725661/Sephira-Studio-Test.zip)

- The user's capture matches 1.2.136 and shows two new F7 access violations.
  The pinned loader's binary/source maps the stack to Lua-table-to-struct
  conversion, with the next passive ID being interpreted as a table. The earlier
  scalar-wrapper fix exposed this second bug before the game's effect factory.
- Use the resident native skill-effect table and FindRow's UScriptStruct
  reference. Validate the table, schema, row type, ID/type/zero ratio, then let
  Unreal copy the original native struct through CopyCompleteValue. Never turn
  the effect row into a Lua table or write the source row. Missing data and
  unsupported getter signatures fail before reaching the factory. Preserve
  foreign effects, native restoration, all ground modes and session-only state.
- Record entry and successful completion of the first native factory/attachment.
  Auto-battle and its accepted right-side status placement are unchanged, as are
  all kits, balance, acquisition, audio/media and treasure assets. Subsequent
  live result on 2026-10-29: the user reports that 1.2.137 now seems to be working.
  Record this as a successful latest test; individual travel modes and extended
  session coverage were not specified.
- All 108 focused checks pass. The actual Windows payload passes 34 auto-battle,
  eight encounter-control and 10 counter checks. Factory fixtures require the
  original opaque native-row reference, reject Lua-table round-tripping and
  writes, preserve all 15 parameters and exercise missing-table/row/schema
  recovery and unsupported signatures. Native effect ownership, esper and
  combined game-thread fixtures pass. Full Windows Flutter, 878 Python tests
  (33 skips), fresh frozen-engine and launcher/updater checks pass. All 87
  extension and 16 Fina hashes match. Every public app file and launcher matches
  the verified artifact/source; every other payload file is unchanged.
  An earlier automatic attempt stopped on four Windows test-harness UTF-8
  decoding errors. Corrected the explicit file encoding; runtime bytes remained
  unchanged, and only the final successful attempt was published.
- If encounter control was disabled for recovery, re-enable it in Studio before
  rebuilding/installing and restarting to test F7 or the held-trigger control.
  The existing external session collector remains compatible.
- Public ZIP: 82,577,374 bytes; SHA-256
  `2082a1d1431a5540a219f33b2697c552733a68cc082aeeee969d7537a97808b4`.

First complete candidate **16:26:59 PDT** to verified
delivery **16:52:05 PDT**: **25m 05s**,
including focused checks, the held first attempt, its encoding correction,
waiting, both automatic Windows builds and actual
artifact/public-package verification. Combined CI run wall times: **19m 43s**;
summed runner job time including the failed attempt and publication: **27m 26s**.
Joined exact automatic runs 40973373962 (held) and 40974725661 (published);
no duplicate/manual dispatch. Publication notes use
only README/CHANGELOG and do not request another binary.

## Published native Dragon Seal parameter reading — 2026-10-29

Code [`e5462d1`](https://github.com/biscoBen/FFR-Vison-Studio/commit/e5462d1d09a7fd5be2e333cc5e0bb9255240f403) ·
[Studio test 1.2.136](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40968992216/Sephira-Studio-Test.zip)

- The user's capture matches the exact installed 1.2.135 runtime. It receives
  OFF, then fails native-effect validation before reaching the factory or
  displaying OFF. The same failure repeats 452 times in movement callbacks.
  The user confirms auto-battle works and accepts its right-side text placement.
- Pinned UE4SS cdbc0b66 converts returned struct arrays into Lua tables of
  RemoteUnrealParam entries. Comparing the first wrapper directly with zero
  rejects the expected Dragon Seal data. Snapshot and unwrap all 15 parameter
  values before validation and before passing numbers to native integer setters.
  Read existing effects and diagnostic snapshots the same way. Preserve the
  native ID/type/zero checks and report their actual values on mismatch.
- Deduplicate identical movement errors. Keep the native Dragon Seal mechanism,
  effect ownership/restoration, keyboard/controller controls, ground modes
  (foot/chocobo/magitek), context guards and session-only state. Auto-battle,
  status-widget code/assets, all kits, balance, acquisition, media and treasure
  assets are unchanged. Native encounter suppression still needs a live retest.
- The corrected regression fixture models the actual pinned loader's wrappers;
  the old runtime fails it. All 107 focused checks pass. The actual Windows
  payload passes 34 auto-battle, seven encounter-control and 10 counter tests,
  including full numeric factory parameters, existing native effects, cleanup,
  all three ground modes and bounded logging for 120 repeated failure callbacks.
  Full Windows Flutter, 877 Python tests (33 skips), fresh frozen-engine,
  launcher and updater checks pass. All 87 extension and 16 Fina hashes match;
  every public app file and launcher matches the verified artifact/source.
- Public ZIP: 82,576,876 bytes; SHA-256
  `150360319d80de7a2b96d03b2c5075bcdb890bc15b0f9c3fc8354942e5c5f1ec`.

First complete candidate **15:50:35 PDT** to verified
delivery **16:04:33 PDT**: **13m 57s**,
including focused checks, waiting, the single automatic build and actual
artifact/public-package verification. CI wall: **12m 35s**;
summed runner job time including publication: **16m 44s**.
Reused exact run 40968992216; no duplicate/manual dispatch. Publication notes use
only README/CHANGELOG and do not request another binary.

## Published confirmed commands, bottom anchors and ground travel — 2026-10-29

Code [`6d55bb7`](https://github.com/biscoBen/FFR-Vison-Studio/commit/6d55bb7c75563f507a004eff13a6b2bf9a09a390) ·
[Studio test 1.2.135](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40965164461/Sephira-Studio-Test.zip)

- The user's 1.2.134 report confirms partial replay and no visible indicators.
  Its exact runtime logs no captured-command messages and replays only native
  saved commands: Rain/Lasswell still use their attacks. Observe the native
  command manager's confirmed ExecuteDataList before the interactive input guard,
  so capture no longer depends on reflected hooks receiving direct native calls.
- Group decisions per character, retain the queue's latest record, deduplicate
  unchanged records and capture through hidden-input transitions. Unsubmitted
  menu choices never become memory. While auto-battle is ON, observe queue changes
  without overwriting remembered target preferences, including the frame before
  F9 switches OFF. Retain the native hook, Attack fallback, costs, legal targets,
  multicast, bonus-round and OFF/reentrancy/controller-latch safeguards.
- Correct the off-screen indicator placement: Unreal's size and position setters
  reset viewport anchors. Apply the intended bottom anchor/alignment afterward.
  Keep the corrected passive native widget, FText, cached layout and game-thread
  polling. The asset bytes and private package identity from 1.2.134 are unchanged.
- The encounter trace identifies a magitek-armour actor rejected by the old
  walking-only guard. At the user's explicit request, support native Walking,
  Chocobo and MagickArmor modes (1/3/5). Keep all input/menu/event/pause/battle
  guards and temporary native effects. Deduplicate movement-owner logs and update
  Studio help. The effect's live suppression result still needs confirmation.
- Local: 107 focused checks pass. Actual Windows payload tests pass 34 auto-battle,
  seven encounter-control and 10 counter cases, including native confirmations
  without reflected callbacks for all four tested characters, stale/unsubmitted
  records, retained auto preferences, real anchor-reset semantics and all three
  requested ground modes. Native effect ownership, esper and combined game-thread
  loop checks pass. All 87 extension and 16 Fina hashes match; every public app
  file and launcher matches the verified artifact and reviewed source. Full
  Windows Flutter, 877 Python tests (33 skips), fresh frozen-engine and launcher
  checks pass.
  Native memory capture, visible placement and encounter suppression need a live
  retest. Kits, balance, acquisition, audio/media and treasure assets are unchanged.
- Public ZIP: 82,576,600 bytes; SHA-256
  `60cfa835a12f8aa45fcc707baade500c8f7b79aa782060665fbca382ecef234e`.

First complete candidate **15:18:50 PDT** to verified
delivery **15:30:37 PDT**: **11m 46s**,
including focused checks, the single automatic Windows build, waiting and actual
artifact/public-package verification. CI wall: **8m 31s**;
summed runner job time including publication: **12m 19s**.
Reused exact run 40965164461; no duplicate/manual dispatch. Publication notes use
only README/CHANGELOG and do not request another binary.

## Published private package identity and walking-owner fallback — 2026-10-29

Code [`4e6ab7d`](https://github.com/biscoBen/FFR-Vison-Studio/commit/4e6ab7d400ee3e2f82bd33283646822000def4c4) ·
[Studio test 1.2.134](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40959972538/Sephira-Studio-Test.zip)

- The returned exact 1.2.133 runtime still cannot load the private status class.
  The actual IoStore manifest identifies its file as the original WBP_KeyGuide
  package: the author renamed the file/name map but retained the cooked summary's
  FolderName. The native loader correction alone did not resolve that mistake.
- Correct the summary to `/Game/UI/Studio/WBP_StudioStatus`, rebuild the small
  precompiled widget and refresh both pinned archive/file checksums. The actual
  packed manifest now has the correct private name, ID and matching filename;
  the original game's key-guide package is no longer overridden. Native legacy
  and IoStore round trips preserve the four exports, passive text and explicit
  font. Keep native loading/FText and all existing command/controller safeguards.
- The encounter key reports no ready map player. Cache the actual playable actor
  supplied by native InputMove, with the map getter as fallback before movement.
  Guard the whole callback, trace the chosen source and clear it at context and
  transition boundaries. Keep all walking/input/menu/event/pause/battle/vehicle
  guards. Encounter groups, actor ratios, movement thresholds, equipment and saves
  are unchanged. Live suppression remains unconfirmed; reuse the same collector.
- Local: 103 focused checks pass. The actual Windows payload passes 31 auto-battle,
  six encounter-control and 10 counter tests, including a missing map getter,
  native movement owner, transition cleanup and vehicle exclusion. Packaged native
  effect ownership, esper and combined game-thread-loop checks pass. All 87
  extension and 16 Fina hashes match. Every public app file and launcher matches
  the provenance-verified artifact and reviewed source. Full Windows Flutter,
  873 Python checks (33 skips), fresh frozen-engine and launcher checks pass. Rendering and both live
  controls need a retest. Kits, boss powers, acquisition, media, treasure radar
  and counter packages retain their values.
- Public ZIP: 82,576,118 bytes; SHA-256
  `88f807ac897645c2db1e6b196844587ff9cfa96b4300e5f7a1a4bcb88c79ca40`.

First complete candidate **14:39:30 PDT** to verified
delivery **14:53:42 PDT**: **14m 12s**,
including the local pinned-checksum correction, temporary build-cache cleanup,
focused checks, the single automatic Windows run, waiting and package verification.
CI wall: **11m 04s**; summed runner job time including
publication: **15m 53s**. Reused exact run 40959972538;
no duplicate/manual dispatch. Publication notes use only README/CHANGELOG.

## Published private status-widget loading correction — 2026-10-29

Code [`8e3c28c`](https://github.com/biscoBen/FFR-Vison-Studio/commit/8e3c28c9d6fe60018ac4d5e80af670ae3cb25f3a) ·
[Studio test 1.2.133](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40955684066/Sephira-Studio-Test.zip)

- The returned session verifies 1.2.132's installed runtime and 619 repeated
  `Battle guide unavailable` pauses. Our private status widget used UE4SS's
  registry-only asset loader, which cannot discover mounted mod-only assets.
  The HUD-dependent auto-battle control therefore stopped before replay.
- Load the private class through Unreal's native soft-object path, using the same
  working route as Fina's private presentation assets. Retain the passive widget,
  native FText, game-thread polling and all latest-command, Attack fallback,
  OFF/reentrancy, controller-latch, multicast and bonus-round safeguards.
  Show a specific class-load error and log repeated pause reasons only once.
- The capture's encounter request was rejected outside free walking; no OFF,
  effect-application or native battle-entry snapshot was recorded. Identify the
  exact rejecting gate on keypress without changing guards or suppression.
  Encounter suppression remains unresolved; the same no-install session collector
  works for the retest. No new F8 observer or collector is required.
- Local: 92 focused checks pass. The actual Windows payload passes 31 auto-battle
  fixtures, including a private class absent from both the loaded-object table and
  asset registry, native soft-object loading, FText, command replay and pause
  recovery. Field controls also exercise that loader. Packaged encounter ownership,
  esper and combined game-thread-loop checks and 10 counter checks pass.
  All 87 extension and 16 Fina hashes match; every public app file and launcher
  matches the provenance-verified Windows artifact and reviewed source.
  Windows CI passes full Flutter analysis/tests, 872 Python checks (33 skips),
  fresh frozen-engine setup and launcher/updater checks.
  Native rendering, controller operation and encounter suppression need retesting.
  Kits, boss powers, acquisition, media and treasure asset packages are unchanged.
- Public ZIP: 82,575,959 bytes; SHA-256
  `44ef3113191680f2d528c5dae91c892c99df08da168302bd00c2c0ffa44769a4`.

First complete candidate **14:11:45 PDT** to verified
delivery **14:22:25 PDT**: **10m 40s**,
including local verification, the single automatic Windows run, waiting and
artifact/public-package verification. CI wall: **9m 47s**;
summed runner job time, including publication: **14m 13s**.
Reused exact run 40955684066; no duplicate/manual dispatch. These publication notes
use only README/CHANGELOG and do not request another binary.

## Published dungeon counter and latest auto-battle memory — 2026-10-29

Code [`e5e5544`](https://github.com/biscoBen/FFR-Vison-Studio/commit/e5e5544faa28b2dcab1c68e6e9294f534f8d870e) ·
[Studio test 1.2.132](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40951100236/Sephira-Studio-Test.zip)

- Add **Items left: N** at the minimap's bottom-left with treasure radar enabled.
  Count unopened chests, glowing pickups and tablet fragments throughout grouped
  dungeon/shrine floors, including previously collected items. Native saved IDs
  deduplicate shared maps; decorative open chests are excluded. Scope: 108 maps,
  75 groups and 201 collectible locations. Unknown maps hide the label.
- Install a separate native counter companion; retain the original radar bytes.
  Existing users close Resonance and cycle Show treasure OFF/ON once. No vision
  rebuild or UE4SS is required for this counter. Ownership/rollback preserve
  edited or manual originals. Native minimap functions and layout are retained
  apart from the unrotated label, its reflected property and saved-state binding.
- Replace status key guides with a private passive text widget and explicit font,
  without input subscriptions, icons or script ticking. Runtime indicators still
  require a normal control rebuild/install and a live rendering check.
- Remember fresh manual commands independently for each party character, including
  submissions after native phase/UI changes or with empty/stale path history.
  Reconstruct the native command hierarchy and use each character's actual native
  Attack if no command memory exists. Keep native costs/availability and all OFF,
  controller latch, reentrancy and bonus-round guards. The user confirms 1.2.129
  fixed the single/all-target flicker; preserve those safeguards.
- Encounter suppression still fails in the user's test. Add event-driven read-only
  snapshots of map/playable parameters, owned encounter effects and their release
  reasons. The external control-session bundle installs no observer: run it,
  launch/test/close the game, then upload the automatic export. No F8 or cleanup.
- Local: 115 focused Python checks, 31 startup/UI Flutter checks and 15 source
  exporter checks pass. Both UI assets pass native legacy/IoStore round trips;
  execute the actual packed counter getter across every captured group and saved
  alias. The actual Windows payload passes 30 auto-battle fixtures, 10 counter
  checks, encounter ownership, esper and combined game-thread-loop checks.
  Windows CI also passes full Flutter analysis/tests, 871 Python checks (33 skips),
  fresh frozen-engine setup and launcher/updater checks.
  All 87 extension and 16 Fina hashes match. Every public app file and launcher
  matches the provenance-verified artifact and reviewed sources. Kits, boss powers,
  acquisition and media are unchanged. Native rendering, collection updates and
  live command refresh remain user tests; encounter suppression is unresolved.
- Public ZIP: 82,575,604 bytes; SHA-256
  `3e71802478f6fb2ed6eaed69c7bdc519820548964482776e769c875b178556de`.

First complete candidate **12:59:55 PDT** to verified
delivery **13:52:53 PDT**: **52m 57s**.
This includes local checks, the failed 1.2.130 resource allow-list correction,
the superseded 1.2.131 Attack-ID correction, all three automatic builds, waits and
artifact/public-package verification. CI wall time: 1.2.130 **4m 40s**,
1.2.131 **10m 49s**, 1.2.132 **10m 09s**.
Summed runner job time across all three, including publication: **38m 11s**.
No duplicate or manual dispatch; publication notes use the README/CHANGELOG-only path.

## Published bonus turns and controller cancellation safeguards — 2026-10-29

Code [`f7ddf9a`](https://github.com/biscoBen/FFR-Vison-Studio/commit/f7ddf9a3ce50d8e92338d1e86446971663856d5c) ·
[Studio test 1.2.129](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40938409829/Sephira-Studio-Test.zip)

- Continue remembered auto-battle actions through native Additional/bonus phases.
  Resolve the native current actor in a multi-character selection, retain native
  availability, costs and targeting checks, and leave Finish phases manual.
- Cancel replay immediately on F9 OFF even while a command transition blocks
  input. Retain the held-trigger latch across transitions and recheck enabled
  state/replay identity before every native command write. These checks also
  cover OFF dispatched reentrantly during an availability or target query.
- Reveal the owned status-widget content after viewport construction and preserve
  native FText. Stop rewriting unchanged positions, text, opacity and visibility;
  reject stale top-screen speed-guide geometry when positioning the footer.
- Replace the actor ratio/threshold writes confirmed ineffective by the user's log
  with transient native Dragon Seal effects on map parameters. Use the captured
  effect 71000/passive 1052 and reflected factory/arrays. Preserve equipped seals
  and foreign effects, and remove only Studio-owned instances. No equipment slots,
  learned skills, saves, encounter groups or forced-battle entry are changed.
- Local: 61 focused checks pass. Exact automatic Windows run 40938409829 passes
  full Flutter analysis/tests, 840 Python checks (19 skips), fresh frozen-engine
  verification and launcher/updater checks. The real packaged payload passes
  all 25 auto-battle fixtures, native effect ownership/lifecycle and combined-loop
  checks; 85 extension and 16 Fina hashes match. Every public app file and launcher
  matches the provenance-verified artifact and reviewed sources. Public ZIP:
  82,552,274 bytes; SHA-256
  `d2d6eae7629aab7e3fdf373d44d2fe8f9d3d4ab34e94ef833fa0d746b657ca61`.
- The user confirms controller single/all targeting flickers after switching OFF.
  Live targeting, bonus-round timing, footer visibility and encounter suppression
  still need a playtest; fixture passes do not establish those native outcomes.
  All vision kits, boss powers, acquisition and media retain their values.

First complete candidate **18:49:03.612 UTC** to verified delivery
**19:26:00.081 UTC**: **36m 56s**, including the controller follow-up correction,
local checks, both exact automatic builds, waiting and artifact/public verification.
The first run's CI wall time was **9m 55s**; final run **8m 40s** (combined active
CI wall **18m 35s**). Summed runner usage across both: **29m 48s**. Neither run was
manually dispatched. Publication notes use the README/CHANGELOG-only path.

## Published Primm resonance bonus correction — 2026-10-29

Code [`3084353`](https://github.com/biscoBen/FFR-Vison-Studio/commit/30843530fc3b7dba132f7a3a815d079eafe7fce6) ·
[Studio test 1.2.127](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40926189024/Sephira-Studio-Test.zip)

- Primm's resonance now increases Moonlightbringer's power by 20% until battle ends.
  Both she and Minfilia inherited Onion Knight's Blade Torrent bonus, but only
  Minfilia learns that skill. Primm learns Moonlightbringer at the same awakening
  tier (3). Correct both the private effect target and its description, preserving
  the resonance's damage, native level scaling, bonus amount and duration.
- Migrate both previously shipped descriptions without resetting saved presets.
  Follow one learned private Moonlightbringer copy; preserve custom descriptions,
  donors and effect lists, and skip a removed or ambiguous signature. Clone only
  Primm's effect. Minfilia, Onion Knight, other kits, rewards, acquisition, boss
  powers and media remain unchanged. No new runtime hooks or save writes.
- Local: 102 Sephira Python checks, 32 focused Flutter tests, targeted analysis and
  bundle manifests pass. Exact automatic Windows run
  [40926189024](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/40926189024)
  passes the full Flutter suite, fresh frozen-engine setup, 832 Python checks (19
  skips), payload/library verification and launcher/updater checks. Replay Primm's
  cloned-effect behavior from the actual packaged Python payload. Verify all 85
  extension and 16 Fina resource hashes and compare every published app/launcher
  file to the provenance-verified artifact and reviewed sources. Native battle
  verification remains pending; the treasure counter is not included.
- Public ZIP: 82,550,742 bytes, SHA-256
  `88b68f783f3bc2d6479d1f43c5b5bcdb765c4f734deac396a5560f433c268ff2`.
  First complete candidate 2026-10-29 10:54:48 PDT to verified public package
  11:22:42 PDT: **27m 54s**, including local checks, fixture/fingerprint corrections,
  temporary-checkout recovery, GitHub's checkout delay, waiting and verification.
  Required CI wall time: **22m 39s**. Summed successful code-run job usage,
  including publication: **32m 14s**. One automatic build; no duplicate dispatch.

## Published encounter and remembered-command corrections — 2026-10-29

Code [`8b23d6a`](https://github.com/biscoBen/FFR-Vison-Studio/commit/8b23d6af9d1c3e0b6726eea9bf315b24b2db5a91) ·
[Studio test 1.2.126](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40914045441/Sephira-Studio-Test.zip)

### Restore encounter control and reveal status content — 2026-10-29

- The returned 1.2.125 log records ratio writes to zero, but the user still receives
  ordinary overworld encounters. Treat this as an unresolved regression from their
  working 1.2.124 test, not proof of successful suppression. Suspend the native
  cached movement threshold as well as the ratio, refresh before native movement,
  and restore both only while their values are still owned. Retain later native
  zone changes and leave forced encounter transitions under native control.
- Explicitly reveal the stock key-guide content container and label and set their
  render opacity. Showing its outer UserWidget alone did not establish that its
  content was visible. Retain typed FText and game-thread scheduling.
- Auto-battle was not installed in the returned log; the user confirmed its Studio
  switch was OFF. Its first setup requires enabling the Studio switch, rebuilding/
  installing and restarting before F9 or the controller hold is available. A later
  log confirms successful initialization followed by false action-unavailable
  pauses. Fix the incorrect use of GetCommands (selected stack data) as a menu
  inventory; use the native CanActivateAction check. Capture manual decisions even
  after native input or command UI closes, and place the fallback guide at the
  bottom. Resolve nested speed guides through their world controller.
- Offline fixtures cover cached thresholds, zone changes between polling ticks,
  exact native-value restoration and hidden widget descendants. Native encounter
  suppression and indicator rendering require another live overworld test.
- Verification: 57 focused checks pass. Windows CI reports 333 Flutter passes /
  one skip, a separate fresh frozen-engine setup pass and 827 Python checks / 19
  skips; analysis, payload/library and launcher/updater checks pass. Through the
  unchanged build helper, verify exact workflow/input provenance and ZIP checksums.
  All 85 extension and 16 Fina resource hashes match; the actual packaged encounter
  fixture verifies hidden descendants, float32 ownership and movement refresh, and
  all 17 auto fixtures pass. A separate packaged replay clears native saved history
  and the command stack between battles while retaining session multicast/all-mode
  memory. Existing presets, boss powers and media match 1.2.125. Native overworld
  suppression, replay and bottom HUD placement still require the user’s live test.
- First complete candidate: 2026-10-29 09:34:34 PDT; verified public delivery:
  2026-10-29 09:53:17 PDT. Total 18m 43s includes local checks, additional
  user evidence, corrections, CI, waiting and download verification. Required CI
  wall time: 10m 0s; summed completed runner job time including publication:
  14m 48s. Reused the exact automatic push run; no duplicate dispatch.

## Published: Studio test 1.2.125 — 2026-10-28

Code [`3126974`](https://github.com/biscoBen/FFR-Vison-Studio/commit/31269749bf7fc1d8ab38b7be5118c1cd032b781f) ·
[Windows test package](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40792328266/Sephira-Studio-Test.zip)

### Repeat remembered battle commands

The user confirmed that 1.2.124 loads with encounter control enabled without
crashing. Use that release’s typed FText HUD handling and game-thread polling.
The supplied spell-target F8 capture provides the native command path; command
replay remains subject to live game testing.

- Add the optional **In-game auto-battle** switch. Rebuild/install once, then use
  **F9** or hold **LT+RT / L2+R2 for one real-time second** in ordinary battles.
  The mode starts OFF each game launch; an on-screen play indicator and ON/OFF
  guide follow the native battle-speed guide in viewport space. The guide has a
  temporary upper-right position until the speed widget has completed layout.
- Replay remembered command/skill paths through the native command view model and
  its availability, cost and target-selection rules. Retain actor-specific manual
  choices, multicasts and all-target mode across battles. Seed initial memory from
  native saved commands; resolve vision menus from the current native skill data.
  Choose fresh enemy targets each battle and resolve remembered party targets by
  stable party IDs. Filter all-target selections to the intended relation.
- Pause for unavailable commands, insufficient resources, no legal targets or
  unexpected command state. Manual selection takes over. Keep event, pause,
  cinematic, guest and extra-phase turns under native control. Do not mutate
  equipment, save data, action costs or native auto-battle options. Existing
  remembered-item commands use native inventory availability and consumption.
- Retain native callbacks through GC and stage/remove the runtime with the Studio
  switch; support an auto-only install and the optional UE4SS installer. Preserve
  other switches, vision presets, IDs, kits and media. Include the Lua helper in
  Python and Flutter setup allowlists and the fresh Windows startup resource check.
- Use the supplied target-selection capture (344 → 420070, target 8) as native
  protocol evidence. Offline replay/lifecycle fixtures pass. Native UI timing,
  all command types, controller conflicts and HUD positioning require live tests;
  the fixture is not proof that native command submission works in game. Verify
  the real shared HUD helper with typed text, primary native scheduling and the
  emitted combined encounter/esper runtime in addition to replay fixtures.

- Validation: 65 focused Python checks and targeted Flutter checks pass. Windows CI
  reports 333 Flutter passes / one skip, a separate fresh frozen-engine setup pass,
  and 825 Python checks / 19 skips; analysis, payload/library and launcher/updater
  checks pass. Verify the exact compiled and published ZIPs through the unchanged
  build helper’s workflow/input provenance and checksum checks. All 85 extension
  and 16 Fina file hashes match; actual packaged auto replay fixtures pass (15),
  combined native loops pass, and existing presets, boss powers and media match
  1.2.124. Native auto replay/controller timing still needs live confirmation.
- The original complete candidate was recorded at 2026-10-28 14:44:49 PDT; verified
  public delivery is 2026-10-28 17:21:21 PDT. Total 2h 36m 32s includes
  local checks, the startup-crash investigation and intervening fixes, release hold,
  user retest, CI and download verification. Required CI wall time: 9m 16s; summed
  completed runner job time including publication: 15m 11s. Reused the exact
  automatic push run; no duplicate build dispatched.

## Published native HUD text and esper polling correction — 2026-10-28

Code [`4432366`](https://github.com/biscoBen/FFR-Vison-Studio/commit/443236604af181d6b0ebf77ae1d806f940952102),
update **1.2.124**, [verified Windows test package / run 40789172083](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40789172083/Sephira-Studio-Test.zip)
(**82,543,085 bytes**; SHA-256 `e8c41a2035ab67b35f35d6c993cc1c56883c0891e5962bf11ef27d74aa4a95a5`).

- Correct the encounter indicator's `SetText` argument to native `FText`. The
  updated-loader crash maps exactly to `FText::ToFString` via the text-property
  setter; passing a raw Lua string was unsafe. The fixture now rejects that input.
- Prefer the native game-thread loop for Eiko's 200-ms esper scan. This removes
  background Lua entry alongside Fina's game-thread presentation. Retain one
  rooted, bounded-retry bridge for loaders without that scheduler. Preserve every
  esper modifier, native finale, player kit, boss power, Fina presentation and media.

**Evidence and limit:** the returned report verifies the newer cdbc0b66 loader
and an installed script containing Eiko/Fina with encounter code absent. Its
later crash is a distinct Lua userdata/table-lookup failure. The loader's actual
source shows its background scheduler entering the shared Lua VM separately
from game-thread callbacks. Removing that path addresses a concurrency risk; the
precise cause of that later crash remains unconfirmed. The user subsequently
reported one successful retry, so do not treat either the intermittent startup
failure or recovery as settled. Auto-battle remains held and is excluded here.

**Validation:** 40 focused checks pass against the exact clean commit, including
all esper mechanics under the native scheduler, no asynchronous polling entry,
rooted retry fallback and typed HUD input. Required Windows plan, validation,
compilation, final gate and publication succeed for the same commit. **333 Flutter
tests passed, 1 skipped**, a separate fresh frozen-engine setup test passed, and
**810 Python tests with 19 skips** completed. Analysis, engine archive/cache,
bundled-file, launcher and updater checks pass.

The actual package verifies all **84** extension and **16** standalone Fina
hashes, version 1.2.124 and emitted runtime with encounters both ON and OFF.
Execute the packaged HUD/controller/restoration fixture and complete esper
lifecycle/effect fixtures. Combined Eiko/Fina/encounter startup registers only
native game-thread loops, and OFF removes encounter code. All 30 presets, boss
power definitions, Fina presentation and other payload/media hashes match 1.2.123.
The public ZIP's digest, provenance, every app file and reviewed launchers match
the checked artifact. These checks do not replace an in-game startup retest.

**Measured time:** first complete implementation `2026-10-28T23:40:30.438396+00:00`
through verified public delivery `2026-10-28T23:54:03.434925+00:00`: **13m 33s**,
including local checks, staging, CI waits and package/publication verification.
Required CI wall: **9m 51s**; summed time of completed runner jobs,
including publication: **15m 16s**. Reused the matching automatic run;
no second workflow was dispatched.

## Published Minfilia/Primm tuning and loader-update installation — 2026-10-28

Code [`1bd54ae`](https://github.com/biscoBen/FFR-Vison-Studio/commit/1bd54ae9c0134a3e2cd70cb99e262901a17efb28),
update **1.2.123**, [verified Windows test package / run 40785014947](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40785014947/Sephira-Studio-Test.zip)
(**82,542,634 bytes**; SHA-256 `6caaeea6cff263ea41c41542cfc4118796ecc93bd2608e09f3f7a7420c056a19`).

- Set the paired boss skills to the requested powers: Moonlightbringer **52 → 33**,
  Calamity **39 → 33** and Blade Torrent **62 → 45**. Other boss skills, playable
  kits, levels, HP/break, speed, selected rotations and rewards stay unchanged.
- Accept a previously owned loader updated to Studio's exact checksum-pinned
  official binary pair. Status only checks files; a successful installation saves
  the new ownership hashes. Unknown or partial updates and settings edits retain
  their protections. Unowned loader files are not claimed.

**Validation:** 65 focused checks pass against the exact clean commit. Required
Windows plan, validation, compilation, final gate and publication succeed for that
same commit. Windows reports **333 Flutter tests passed, 1 skipped**, an additional
fresh frozen-engine setup test passed, and **808 Python tests with 19 skips**.
Analysis, engine archive/cache, bundled-file, launcher and updater checks pass.

The actual compiled package verifies all **84** extension and **16** standalone
Fina hashes and version 1.2.123. Generated boss-row comparisons find exactly the
three requested power changes. All 30 preset definitions, other boss stats and
selected actions, native Lua and media match 1.2.122. The packaged loader status
and install paths accept the reproduced stale-record upgrade without rewriting
the loader. The published ZIP's digest, provenance, every app file and reviewed
launchers match the checked Windows artifact. Auto-battle is excluded.

**Live limit:** the install preflight repair does not prove the encounter-control
native crash is resolved. The controlled newer-loader startup retest is still
pending; 1.2.122's HUD rewrite did not fix the reported crash. The requested native
spell-target capture has been received. Auto-battle remains held for that retest.

**Measured time:** first complete implementation `2026-10-28T23:04:41.931908+00:00`
through verified public delivery `2026-10-28T23:17:24.928184+00:00`: **12m 43s**,
including local checks, staging, CI waits and package/publication verification.
Required CI wall: **8m 49s**; summed time of completed runner jobs,
including publication: **13m 43s**. No second workflow was dispatched.

## Published encounter-control startup correction and diagnostic sessions — 2026-10-28

### External diagnostic sessions — 2026-10-28

- Add **Run Diagnostic Session.cmd**: run it, launch the selected full game
  normally, and close the game to export automatically. The external PowerShell
  watcher installs no game script, hooks, key bindings or input handler. There is
  no collect/disable sequence for new sessions and no Studio rebuild is needed.
- Follow only the selected installation's shipping process; attach to an existing
  session, wait if multiple matching instances are running, distinguish reused
  process IDs and tolerate a temporary inability to read process metadata. Export
  after actual process disappearance with session start/attach/exit timestamps.
  Cancellation and optional startup timeout leave the game untouched.
- Reuse the offline crash/log collector, bounded reads, own-runtime hash inventory
  and save/roster exclusions. Fix full-game G:/D: autodetection and skip stale demo
  roots. Keep **Collect Resonance Crash.cmd** for an immediate export of an existing
  crash. Share the watcher in `scripts/reference/common/DiagnosticSession.ps1` for
  future collectors. Preserve exact bundle source bytes on Windows.
- Correct the earlier mistaken attribution: the user's controlled test isolated
  the startup crash to **In-game encounter toggle**, just after the overworld
  appeared. The Battle Command observer works with encounter control off. Restore
  its installer and allow existing observers during external collection.
- Remove unnecessary confirmation when session mode already found a valid full-game
  folder. Recognize shortened Windows process names, then verify the full shipping
  executable path. Open the export folder and close the CMD on success; keep errors
  visible. These address the reported session that neither closed nor exported.
- Focused PowerShell/Lua/package checks cover export-after-exit, wrong-installation
  isolation, ambiguous processes, reused PIDs, temporary read failures, cancellation,
  existing-crash collection and preservation of existing observers/saves. Native
  process recognition still requires the user's Windows test.

### Encounter-control startup correction — 2026-10-28

- Replace raw UMG TextBlock construction, live Slate font copying and native field
  HUD canvas attachment with a separate UserWidget created by the game's widget
  library. Use the game's cooked key-guide text style and an owned viewport entry.
  No native HUD tree is traversed or modified. This removes the first-overworld
  badge code implicated by the user's encounter-toggle isolation test; no native
  crash stack is available to establish the exact failing call.
- Retain F7, the controller trigger chord, visible ON/OFF status and reversible
  walking-encounter overrides. Use real time for the full one-second controller
  hold. Keep title/menu/event/vehicle/battle guards and release only the owned badge.
- Native API/asset checks and runtime fixtures cover startup context guards,
  keyboard/controller use, new player/world instances, GC, own-widget removal,
  missing HUD refusal and restoration of native encounter overrides. Live startup
  safety, HUD positioning and controller input remain user checks.

- Stage the HUD helper through both Python and Flutter installer allowlists and
  the Windows fresh-setup resource check. The first Windows run caught Flutter's
  separate completeness list/count before any package was delivered; correct
  that bridge and run the full Flutter suite locally before the next candidate.
- Limit the planning and final-gate jobs to workflow/scripts checkouts so they
  avoid fetching the roughly 2 GiB tracked reference-asset tree. Compilation and
  validation retain full checkouts, all required checks, the pinned engine archive
  and fresh extraction. A real sparse checkout runs plan/gate and still rejects
  failed validation; **12** workflow/provenance tests pass. The build helper is unchanged.

Candidate **1.2.122** local validation: **804 Python tests** pass (18 platform
skips), including **51** focused encounter/field/collector checks; **333 Flutter tests** pass (one Windows-only skip),
including fresh engine setup; changed-Dart analysis passes. Verify all nine native widget/time methods,
the cooked key-guide class path and its member fields against the supplied SDK
and asset inventory. Vision presets, IDs, kits, acquisition and media are unchanged.
The final installer checks caught and corrected the new helper's resource-list
entry before packaging. Windows package verification passes; native startup/HUD behavior still requires the user's retest.

Published **2026-10-28**, code `ba739b5`, update **1.2.122**,
[Windows run 40769368591](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/40769368591),
[verified download](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40769368591/Sephira-Studio-Test.zip).
All required jobs pass: analysis, **333 Flutter tests** (one skip), real fresh
frozen-engine setup, **804 Python tests** (19 Windows/platform skips), extension
checksums and launcher/updater checks. Verify the artifact through the unchanged
build helper's matching-push, workflow/request provenance and SHA-256 checks.

The public **82,542,186-byte** ZIP SHA-256 is
`8b6f44997f81f8681188e73c8112e9a5b619b79f0d80767355d219dc7cc204bf`.
Every public app file matches the validated compiled artifact; launchers match
the reviewed packaging sources. Verify all **84** extension/**16** standalone
Fina checksums, the compiled 1.2.122 label and the actual emitted encounter Lua's
keyboard/controller, GC, context restoration and owned-widget cleanup cases.
All 30 vision presets, IDs, kits, acquisition and media remain unchanged.

Encounter HUD first complete candidate: **13:34:05 PDT**; public ZIP verified
**14:21:24 PDT**, **47m 20s** later. This includes local corrections,
the failed first Windows setup check, scratch-space cleanup, repeated checks,
both automatic candidates, waiting and final artifact/public-package comparison.
The external-session candidate began **12:55:22 PDT**, **86m 03s** before the same
verified package; its earlier prompt/process/attribution fixes are included.
Neither timer was restarted. Final required Windows wall time: **10m 31s**;
total runner usage across both attempts, including publication: **46m 28s**.
These measure development and CI, not the game's mod-install time.
The measured plan job falls from **15m 00s** in the failed first attempt to **6s**
with the sparse script checkout. Validation/compilation retain full inputs;
archive-cache checks confirm the pinned engine/fresh-extraction policy is intact.

## Published optional Fina cinematic and auto-battle investigation — 2026-10-28

**Attribution corrected:** the reported native startup crash persisted with the
Battle Command observer disabled and stopped with in-game encounter control off.
The user subsequently supplied successful F8 battle captures. The observer's
installer is restored; the external session collector also accepts existing F8
observers. Neither collector is installed automatically by Studio.

- Restore **Crystal Fina resonance cinematic** beside the main Studio switches,
  off by default. Rebuild/install and restart after changing it. Off skips movie
  template extraction, soundtrack preparation and the cinematic cache, excludes
  the movie runtime configuration, and removes the owned companion movie on the
  next install. Her ordinary sprite resonance, healing and cure sounds remain.
- Investigate repeat-last-command auto-battle with keyboard/controller controls
  and a prompt beside speed/unit information. The native game exposes auto-battle
  input and per-character saved command bundles, and the returned F8 capture now supplies function parameters and the live HUD
  hierarchy. Native repeat-command semantics still need verification. No auto-battle
  gameplay control or F6 binding is installed in this update.
- Initially provide a separate **Battle-Command-Diagnostics.zip**: F8-only snapshots of native
  function signatures, saved party command IDs, current command selection and
  the battle widget hierarchy. No polling, hooks, command submission, save or
  option writes. All native callbacks are retained. The installer preserves
  Studio and other mods and detects the full game on either PC, continuing past
  absent candidate drives. A PowerShell regression check covers that case. Preserve
  the diagnostic source line endings so the ZIP matches Windows checkouts exactly.
  The live capture confirms that it runs with encounter control disabled.

Candidate verification — 2026-10-28: update **1.2.121**, code
`6e3c3f9`, [Windows run 40750056461](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/40750056461).
All four required Windows jobs pass: analysis, the full Flutter suite, fresh frozen
engine setup, **795 Python tests** (19 platform skips), launcher/updater checks and
compilation. Local checks pass **795 Python tests** (48 environment/platform skips),
**43 focused Flutter tests**, changed-Dart analysis and **six** observer checks,
including PowerShell drive detection and install/collect/disable. An autocrlf-enabled
checkout reproduces the exact six diagnostic source bytes in the ZIP.

The connector-downloaded Windows artifact passes provenance and SHA-256
`52c99e239b69c5700fbce56219582ff6198dc050814d191d55a2f6f749982cf3`.
Its actual packaged modules pass movie **OFF → ON → OFF** runtime generation,
discard stale movie flags and skip movie-only extraction/tool work while off.
All **83** extension/**16** standalone Fina checksums match; all 30 vision presets,
IDs and acquisition choices, media and other runtime payloads match 1.2.120.
The direct installable test ZIP delivered in the task uses the unchanged packaging
helper and matches every app byte from that artifact plus the reviewed launchers.
Its **82,541,827-byte** ZIP SHA-256 is
`7f17b9fae28cc6f5e47343c4bc1168a1cf24bfa6f52bb2447a5f72d708a641b8`.

First complete candidate: **11:24:15 PDT**.
Direct ZIP verified: **12:34:59 PDT**,
**70m 44s** later. This includes all local checks,
corrections, three automatic code candidates, CI waits and package verification;
the timer was not reset. The first Windows attempt exposed diagnostic line-ending
conversion; the intermediate candidate fixed missing-drive handling before that
result arrived. The final candidate fixes both. Final required Windows checks
wall time: **19m 01s**; runner usage across
all three Windows workflows through direct-ZIP verification: **105m 30s**,
including elapsed time in the still-active publisher. These are development/CI
measurements, not game-install benchmarks. The pinned engine cache is unchanged;
each matching automatic run was joined through the unchanged build helper.

The public package subsequently published successfully and was verified at
**13:37:34 PDT**, **133m 19s** after the original first candidate. Its
82,541,827-byte ZIP SHA-256 is
`bfaded1bf9ca71d8a1642bf4fa7f42806c9341428d48f3dde113dad6d61704f7`.
Every published app file matches the provenance-verified Windows artifact and
its launchers match the reviewed packaging sources. Total measured runner usage
across all three Windows candidates, including completed publication: **120m 43s**.
The compiled commit remains `6e3c3f9`; later documentation does not relabel it.
The returned battle capture now supplies native command signatures and HUD layout.
Auto-battle command semantics still need verification; this candidate installs no
F6 or auto-battle gameplay control. Live Fina-toggle confirmation remains a user test.

## Published in-game encounter control — 2026-10-28

[Verified Windows ZIP / run 40737734046](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40737734046/Sephira-Studio-Test.zip), code `830fdab`, update **1.2.120** (82.5 MB).
SHA-256 `ff6af3fbc1ed7ff226d396f55ac12458fc4663d1f376c8713ffdd33703dea000`.

- Studio’s encounter switch now installs an in-game control. Press F7, or hold both
  controller triggers (LT+RT / L2+R2) for one second while freely walking. A persistent
  bottom-left ON/OFF badge shows the state. Encounters start ON each game launch.
- Apply a session-only native walking-encounter override; restore the prior value when
  switching back on or leaving field control. Preserve native zone changes, equipment,
  save data, map flags, bosses and scripted battles. No accessory or ability slot is used.
  Rebuild/install once to replace the earlier always-off map patch; subsequent toggles
  need no rebuild. The optional UE4SS installer also covers encounter-only setups.
- Use a real field-HUD text widget, restore native control during menus, battles,
  transitions and events, and refuse an invisible toggle if the HUD is unavailable.
  Automated Lua/API and installer checks do not establish live controller behavior or
  HUD placement; these need testing in the running game.
- The user reported an error while entering the vision menu with treasure markers enabled.
  A later screenshot shows a Lua nil-callback panic with the old FFRStudioMovieTrace
  diagnostic active. Root its timer, queued and F8 callbacks to prevent garbage collection
  from invalidating them, with an executable weak-registry regression test. Update both
  trace sources and the standalone movie-trace ZIP. Existing diagnostics need disabling
  and a game restart; Studio does not silently modify them. The treasure package is
  unchanged, and a crash-free live retest is still needed to establish the cause.

Validation: **788 Python tests** (45 platform/environment skips), **10 focused
Flutter tests**, changed-Dart analysis and executable Lua input/HUD/GC fixtures
pass locally. Full Windows analysis, Flutter/Python suites, fresh frozen-engine
startup, launcher/updater checks and compilation pass for this commit. The Steam
Deck launcher workflow also passes. Native schema/method evidence verifies the
field float override, FKey and UMG bindings; FieldWidgetManager is resolved as an
Object rather than queried as a WorldSubsystem. This evidence does not replace
a live playtest of suppression, controller recognition and HUD placement.

The downloaded ZIP passes provenance, checksum, compiled **1.2.120** labels and
**83** extension/**16** standalone Fina hash checks. Its exact encounter Lua passes
the controller/keyboard/HUD/restoration fixture. All 30 vision presets, IDs and acquisition match 1.2.119. Native skill/audio and
treasure package bytes are unchanged.
The old trace is not silently changed by an app update: disable its enabled.txt
and restart the game. Updated standalone trace helpers retain their callbacks;
treasure-related crash causation remains unconfirmed pending the user's retest.

First complete candidate: **10:18:14 PDT**.
ZIP verified: **11:09:43 PDT**,
**51m 29s** later. Delivery notes prepared:
**11:09:43 PDT**
(**51m 29s** from the same candidate).
This includes local checks and corrections, the additional trace investigation,
runner checkout/setup delays, the automatic Windows run, download and verification.
Measured Windows workflow wall time: **29m 19s**;
combined Windows-workflow runner usage: **37m 41s**. These are development/
package timings, not game-install benchmarks. The checksum-pinned engine cache
is unchanged; no second matching build was dispatched while this run was active.

## Published Sephira Libra and mastery swaps — 2026-10-27

[Verified Windows ZIP / run 40604529846](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40604529846/Sephira-Studio-Test.zip), code `ffdbecd`, update **1.2.119** (82.5 MB).
SHA-256 `e3b7ac0f69dda4259b45d6bf8564681202f6831540b829def89a704454b1e042`.

- Minfilia learns Libra at MR1 and Throw at MR3; her MR5/7/9 stay Observe and Recover HP,
  Observe and Attack, and Chuck. Barusa gets Strategic Acumen at MR1, Primm gets Imbue Earth
  at MR1, and Trance Terra gets Resist Fire at MR1.
- Fire Eater moves to Trance Terra awakening tier 3 and Primm MR9. Primm’s Boundless Flames
  moves to awakening tier 4. Terra’s Trance Apocalypse moves to tier 4 to fit the eight-slot cap.
  All 75 original equipable MR rewards stay covered. Minfilia/Barusa each lose one passive,
  Primm/Terra each gain one; all four stay within 20% of their native passive AP budgets.
- Migrate untouched saved reward layouts in stages, preserving IDs, Spirit ownership, private
  recipes, stats, acquisition choices and permanent rewards. Keep the old Barusa Earth imbue
  definition for existing learned saves, and give Primm a named 20-AP equipable copy.
  Conflicting edited rewards or full tiers stay intact and are reported. Live-game testing remains.

Validation: **785 Python tests** (45 platform/environment skips), **46 focused Flutter
tests** and clean changed-Dart analysis pass locally after correcting test fixtures.
Full Windows analysis, Flutter and Python suites, fresh frozen-engine startup,
launcher/updater checks and compilation pass for this commit. Real native writing
and readback verify **13 tables**, **31 vision/Spirit owners**, all **26 stock MR
active rows** including Libra, named 20-AP Primm Earth imbue and retained Barusa
reward 1938. All original skill/passive rows are unchanged. All 75 original MR
rewards stay MR rewards; other 26 presets and all 28 bosses’ combat behavior remain
unchanged. The actual downloaded ZIP passes provenance, checksum, compiled
**1.2.119** label and **82** extension/**16** standalone Fina hash checks. Its
catalogue and migration policy match the checked source. All other game-facing
payloads, including audio, acquisition, sprites/cache and treasure/encounter helpers,
match 1.2.118. Live-game equipment and progression confirmation remains.

First complete candidate: **16:43:20 PDT**.
ZIP verified: **17:00:46 PDT**,
**17m 26s** later. Delivery notes prepared:
**17:00:46 PDT**
(**17m 26s** from the same candidate).
This includes local checks, corrections, the automatic Windows run, waiting,
download and verification. Measured workflow wall time:
**12m 16s**; combined runner usage: **16m 34s**.
These are development/package timings, not game-install benchmarks.
The checksum-pinned engine cache is unchanged.

## Published treasure switch placement — 2026-10-27

[Verified Windows ZIP / run 40600073876](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40600073876/Sephira-Studio-Test.zip), code `f366a90`, update **1.2.118** (82.5 MB).
SHA-256 `defa3dc1dcc6d78e5eeddcec539f2a0056e25eedb58482a0d5986b368a3a88d3`.

- Move **Show treasure on the minimap** beside the other main switches, directly
  below **Disable random encounters**. Keep its immediate install/remove behavior
  and closed-game requirement. No game assets, saved settings or vision rewards change.

Validation: **31 focused Python installer tests**, the existing home-screen widget
test and clean changed-Dart analysis pass locally. Full Windows analysis, Flutter
and Python suites, fresh frozen-engine startup, launcher/updater checks and
compilation pass for this commit. The downloaded ZIP passes workflow provenance,
checksum, compiled **1.2.118** label and all **82** extension/**16** standalone Fina
hash checks. It has the single treasure control directly below the random-encounter
switch in the compiled source revision. All game-facing extension payloads,
including radar, encounter, audio and sprite/cache helpers, are byte-for-byte
identical to the verified 1.2.117 package; the complete 30-vision catalogue is unchanged.
The widget check passes; user confirmation of the new placement remains.

First complete candidate: **16:07:26 PDT**.
ZIP verified: **16:22:49 PDT**,
**15m 23s** later. Delivery notes prepared:
**16:23:04 PDT**
(**15m 38s** from the same candidate).
This includes local checks, the automatic Windows run, waiting, download and
verification. Measured workflow wall time: **13m 15s**;
combined runner usage: **17m 51s**. These are development/package timings,
not game-install benchmarks. The checksum-pinned engine cache is unchanged.

## Published treasure radar and encounter testing — 2026-10-27

[Verified Windows ZIP / run 40597050472](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40597050472/Sephira-Studio-Test.zip), code `2fbbcfd`, update **1.2.117** (82.5 MB).
SHA-256 `576d3aec4f5500dd17afb85767224c46cbc42dcdc4201f86baba84037e26221e`.

- Add **Show treasure on the minimap**, bundling the user's supplied
  `MinimapShowTreasure_FieldObjects 90` package unchanged. With the game closed,
  the switch directly installs/removes its three small files; no vision build
  or UE4SS loader is needed. Read the actual selected installation, recognize
  exact manual copies, preserve different/edited files, and roll back failed writes.
- Inspect its three UI assets and decode the 30-expression `SetDisplay` function:
  collected chest and field-pickup markers use native `IsOpen` state. Existing
  saves should be respected; respawning pickups follow the game. Every tablet
  variant and live marker refresh still need in-game testing.
- Add a separate **Disable random encounters** testing switch. Rebuild/install
  and restart to apply or remove it. Clear only native `doMovementEncount` flags,
  preserving encounter groups, boss/story events and Sephira challenges. Verify
  native patch/readback across 13 full-game tables: 64 flags change, and all other
  fields match the original rows. OFF produces no encounter edits.
- Preserve all vision recipes, permanent IDs, rewards, audio and sprite/icon caches.
  Include both new resources in the strict startup bundle count.
  [Package inspection and behavior](docs/MINIMAP_TREASURE.md).

**Show treasure on the minimap** is under **Your game files**. Close Resonance,
switch it on/off, then launch the game; it installs/removes just the supplied
24,658-byte package. **Disable random encounters** is a separate testing switch;
rebuild/install and restart after changing it. Both default to OFF. Neither
requires UE4SS or changes saves. Existing manual treasure-radar installs show
their actual installed state. An explicit OFF can remove the exact supplied
manual package; restoring the original game preserves copies Studio did not install.

Validation: **781 Python tests** locally (45 skipped), **62 focused Python tests**,
**331 Studio tests** locally (the Windows-only startup test is skipped),
and clean full-Dart analysis. Full Windows Flutter/Python validation, fresh
frozen-engine setup, launcher/updater checks and compilation pass for this commit.
The downloaded archive passes checksum/workflow checks, all **82** extension and
**16** standalone Fina hashes, and its compiled **1.2.117** label. Through the
actual packaged helpers, HTTP install/remove uses the original radar bytes,
blocks an open game, and restores Studio-owned files. The packaged encounter
recipe matches the successful native 13-table/64-flag patch/readback and emits
no encounter edits when OFF. All **30** vision kits, IDs, acquisition, rewards,
audio, game sprite/icon conversion and caches match 1.2.116. Live minimap updates,
tablet variants and encounter travel still need user testing.

First complete code candidate: **15:26:48 PDT**.
ZIP verified: **15:59:13 PDT**,
**32m 25s** later. Delivery notes prepared:
**15:59:29 PDT**
(**32m 41s** from the same candidate).
This includes local checks, the bundle-validation and startup-count corrections, waiting, both
automatic Windows runs, download and verification; the timer was not restarted.
Initial workflow wall time: **6m 21s**; final
workflow wall time: **13m 16s**. Combined runner usage:
**27m 26s**. The first candidate failed the strict startup count
when two resources were added; its release was skipped. Publication uses the
corrected, fully passing commit shown above. These are development/package timings,
not game-install benchmarks. The checksum-pinned engine cache is unchanged.

## Published Aerith Studio portrait refresh — 2026-10-27

[Verified Windows ZIP / run 40577047492](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40577047492/Sephira-Studio-Test.zip), code `04ecf56`, update **1.2.116** (82.5 MB).
SHA-256 `83888fae665ae703debfebbcc22887db6aa8b929f090c7857f8bcc8dfe8fa903`.

- Apply the reviewed Aerith appearance when Studio renders a saved Elephim
  portrait, including the brief interval before its deferred migration save
  finishes. This prevents the old portrait being cached under Aerith's new
  form URL. Face, timeline and ability previews use the same updated source.
- Include the completed appearance revision in Studio's portrait URL so a
  previously cached image refreshes and later deliberate model changes do not
  reuse a picture from before the swap.
- Bind the preview resolver at server startup, after the base engine defines its
  icon handler. Cover that actual registration order with a request-level test.
- Preserve deliberate later model edits and all kits, IDs, rewards and generated
  game assets. The sprite converter and its cache inputs are unchanged.

Reproduce the stale Studio portrait with the pinned engine's actual `spec_icon`
and `unit_icon_image` functions, the real Elephim/Aerith PNGs and native icon frames.
The extension is registered before the base handlers, then binds the resolver at
server startup. The pending saved row remains Elephim while face, timeline and ability previews all
render Aerith correctly. The saved row stays untouched. A later deliberate model
edit remains authoritative. The completed appearance revision also separates the
old and new cache keys, including a later deliberate switch back to an earlier form.

Validation: **768 Python tests** locally (45 skipped), **21 focused icon/migration/cache
tests**, **43 focused Studio tests**, and clean changed-Dart analysis. Full Windows
validation, fresh frozen-engine setup, compilation and publication pass for the final
commit. The downloaded ZIP passes workflow provenance/checksum checks, all **80**
extension and **16** standalone Fina hashes, its compiled **1.2.116** label and the
same real-portrait proof through the actual packaged preview helper. All **30** kits,
MR rewards, IDs, acquisitions and soundtracks match 1.2.114. Game sprite/icon converter
and cache sources, and the checksum-pinned engine cache, are unchanged. This fixes
Studio preview caching; no separate in-game icon defect is claimed. User confirmation
of the refreshed Studio portrait is still needed.

First complete candidate: **12:39:06 PDT**. Final ZIP verified:
**13:37:27 PDT**, **58m 22s** later.
Delivery notes prepared: **13:37:34 PDT**
(**58m 28s** from the same candidate). This includes
local checks, the cache-key correction, all three automatic Windows runs, waiting, download
and verification; the timer was not restarted. Initial workflow wall time:
**15m 32s**; cache-key candidate wall time:
**19m 12s**; final startup-order candidate wall time:
**16m 53s**. Combined runner usage:
**65m 47s**. These are development/package timings,
not game-install benchmarks. The initial candidate was superseded by the completed
cache-key and startup-order corrections; publication uses the final commit shown above.

Update Studio and restart it to refresh the portrait. No preset reset or game-artwork
reconversion is needed for this Studio preview fix.

## Published original 5★ Aerith replacement — 2026-10-27

[Verified Windows ZIP / run 40561006061](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40561006061/Sephira-Studio-Test.zip), code `f933c6b`, update **1.2.114** (82.5 MB).
SHA-256 `8a244f34bf69d98c6d00608b05c6abc33c6c6be537618e0cae9b3a673bc0289a`.

- Replace Elephim with original FFBE 5★ Aerith, including her sprites, icons,
  battle labels, Spirit name and Great Gospel animation with its original audio.
  Great Gospel uses the native party-heal-and-cleanse resonance and native power.
- Keep Elephim's complete regular kit, awakening bonuses, MR rewards, stats and
  acquisition. Retain permanent vision ID **13523**, command/Spirit IDs and the
  internal preset key for Steam Cloud save compatibility across PCs.
- Migrate the old default appearance once after preparing Aerith's artwork, with
  a roster backup; existing kit/acquisition edits and later appearance edits stay
  intact. A fresh setup and reset use Aerith at the same save slot. In-game playback
  and healing still need a test after packaging.

Validation: **766 Python tests** locally (45 skipped), **43 focused Studio tests**,
and clean analysis of the changed Dart code. The full Windows suite, fresh frozen-engine
setup, compilation and publication pass for this exact commit. The downloaded ZIP passes
workflow provenance/checksum verification, all **80** extension and **16** standalone Fina
hashes, and its compiled **1.2.114** label. The actual packaged migration keeps edited
abilities, MR rewards, stats and acquisition; repeated migration and later edits stay intact.
The other **29** presets and soundtracks are unchanged. All **75** original equipable MR
rewards remain covered. The sprite cache and checksum-pinned engine cache are unchanged.

The original hosted **207000405** pack is checked against SHA-256
`33548cfcae22899581dfa57341d8074f5c67b989618fe69e3009e825573d2495` and its 5★ sprite inspected.
Great Gospel uses the original clean Memorial cues **794** (frame 0) and **793** (frame 30),
with supported HCA v2 recordings. Native patch/readback checks three tables: vision **13523**,
resonance **444240** cloning native heal/cleanse **412510** at power **300**, and Spirit
**1352300**. Original rows, all **28** boss stat budgets/rotations and the regular kit remain
unchanged. In-game animation, sound and healing still need a live test.

First complete candidate: **11:24:26 PDT**. Final ZIP verified:
**11:50:21 PDT**, **25m 55s** later.
Delivery notes prepared: **11:50:53 PDT**
(**26m 27s** from the same candidate). This includes local
checks, corrections, native readback, waiting for one matching automatic Windows run,
download and verification; the timer was not restarted. Measured Windows CI wall time:
**15m 48s**; runner usage: **20m 47s**. These are development/package timings,
not game-install benchmarks.

Close the game, update Studio, rebuild/install and restart Resonance. Existing default
Elephim presets update with a roster backup; no preset reset is needed. The internal
`elephim` key and save ID intentionally remain permanent for cross-PC Steam Cloud saves.

## Published optional UE4SS installer — 2026-10-27

[Verified Windows ZIP / run 40549413156](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40549413156/Sephira-Studio-Test.zip), code `658c89a`, update **1.2.113** (82.4 MB).
SHA-256 `a57e8b769508aefd6f72887d508d60e4a6e9d886a79a2215e61fa171f06fa170`.

- Offer **Install UE4SS**, **Continue without it** and **Cancel** before building
  when selected runtime features need a missing loader. The last-build install
  uses the same prompt. Continuing installs the compiled visions and logs the
  unavailable overworld, Crystal Fina presentation/music and esper mastery features.
- Bundle the checksum-pinned official UE4SS production archive and license; copy
  only its core with the completed mod. Preserve existing complete loaders and
  other mods, reject conflicting partial loaders and include newly owned files
  in rollback/restore. No additional download or sprite rebuild is required.
- Automated fresh-install, skip, prompt, ownership and rollback checks; new loader
  revision still needs an in-game startup check on the friend's fresh PC.

Validation: **762 Python tests** locally (45 skipped), **10 focused Studio tests** (one
Windows-only check skipped locally), and clean analysis of the changed Dart code.
The full Windows suite, fresh frozen-engine setup, compilation and packaging pass for
this exact commit. The downloaded ZIP passes workflow provenance/checksum verification,
all **80** extension and **16** standalone Fina hashes, its compiled **1.2.113** label,
and execution of the actual packaged skip, later bootstrap, repeat install and restore
paths. The official archive's Windows x64 PE headers, license and default settings are
checked. Existing vision kits, MR assignments, boss tuning and esper Lua are unchanged;
the checksum-pinned engine cache remains unchanged. The newly bundled loader revision
still needs a fresh-PC Resonance startup and feature check.

First complete candidate: **10:15:12 PDT**. Final ZIP verified:
**10:43:24 PDT**, **28m 12s** later.
Delivery notes prepared: **10:43:38 PDT**
(**28m 26s** from the same candidate). This includes local
checks, the resource-validation correction, waiting for one matching automatic Windows
run, download and verification; the timer was not restarted. Measured Windows CI wall
time: **22m 51s**; runner usage: **29m 41s**. These are development/package
timings, not game-install benchmarks.

Close the game, update Studio and install. A fresh game installation with selected
runtime features offers **Install UE4SS** or **Continue without it** before building.
Existing complete loaders are reused. See [installation details](docs/UE4SS_INSTALLATION.md).

## Published Rikku MR7 Pharmacology — 2026-10-26

[Verified Windows ZIP / run 40449868455](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40449868455/Sephira-Studio-Test.zip), code `798a642`, update **1.2.112** (74.1 MB).
SHA-256 `01fea14b4b94e7429a17c680e0199cebbc16cb326ab335e3a8ec29b9ba38e6c8`.

- Replace Rikku's MR7 One for the Road with the native Pharmacology reward:
  items are 50% more effective in battle, at the same 30 AP equip cost. Existing
  default MR7 grants update once, without resetting awakening tiers or other edits.
  Spirit of Rikku follows the revised MR list. Deliberately edited MR7 slots remain
  openable and report a conflict when the update is explicitly applied.
- This explicitly replaces the Vaan-only awakening passive in the collection;
  the other 130 original passives and all 75 original equipable MR rewards remain.
  Original game passives, save identities, battle tuning and esper runtime are unchanged.

Validation: **755 Python tests** pass locally (45 skipped), plus **39 focused Studio tests**.
The default MR7 migration changes only the selected reward, preserving awakening edits, labels,
stats, private skill identities, acquisition and every other MR rank. Edited MR7 conflicts remain
atomic and later deliberate changes are retained. All 75 original equipable MR rewards remain
covered; the source audit explicitly records the approved One for the Road replacement instead
of claiming all 131 original passives are still in the collection. Pharmacology duplicates Leah's
native reward only in the explicitly approved Rikku MR7 slot.

Native patch/readback verifies Rikku MR7 passive **1044** and Spirit owner **13527**, with original
rows unchanged. Native Pharmacology retains its 30 AP cost and effect **1097**. All 28 boss rotations
and stat budgets, the other 29 presets and the esper Lua runtime are unchanged. Full Windows validation
and compilation pass for this exact commit. The downloaded ZIP passes provenance/checksum checks,
all **78** extension and **16** standalone Fina hashes, its compiled **1.2.112** label and checks against
the actual packaged migration. In-game learning/equipment still needs a check.

First complete candidate: **21:25:12 PDT**. Final ZIP verified:
**21:36:53 PDT**, **11m 40s** later.
Delivery notes prepared: **21:37:13 PDT**
(**12m 00s** from the same candidate).
This includes local checks, corrections, freeing temporary space for tests, waiting for one matching
automatic Windows run, download and verification; the timer was not restarted. Measured CI wall time:
**8m 04s**; runner usage: **12m 19s**. These are development/package timings, not game-install benchmarks.

Update Studio, rebuild/install and restart Resonance. No preset reset or Prepare Game is needed.

## Published Eiko early support spells — 2026-10-26

[Verified Windows ZIP / run 40419653308](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40419653308/Sephira-Studio-Test.zip), code `658242d`, update **1.2.111** (74.1 MB).
SHA-256 `8aedd9877d82fa776ced15b684140bfaf16b8c313490e01c0296e67c68d3ab6e`.

- Move Eiko's Raise to awakening tier 1 and add the native party Shellga to tier 2.
  Existing Eiko presets update automatically without a reset, preserving mastery rewards,
  private skill IDs and unrelated edits. Tier limits remain within eight grants.
- The user confirms the other esper modifiers work in game on 1.2.110; the HP increase
  remains unverified because the esper's HP is not displayed. This support-spell update
  leaves the working esper runtime unchanged.

Validation: **754 Python tests** pass locally (45 skipped), plus all four focused Studio kit tests.
The migration updates both the previous esper kit and older defaults exactly once while preserving custom
edits, private skill IDs, mastery and Spirit links. Native patch/readback verifies the awakening rows and
unchanged original rows. All 75 original equipable MR rewards remain covered; all 28 boss rotations and
stat budgets are unchanged. Eiko's tiers contain **6 / 4 / 6 / 7** grants, within the eight-grant limit.
Full Windows validation and compilation pass for the same commit. The downloaded ZIP passes provenance
and checksum checks, all **78** extension and **16** standalone Fina hashes, its compiled **1.2.111** label,
and migration checks using the actual packaged data. The other 29 presets, esper runtime, battle tuning
and pinned sprite cache are unchanged. The new tier placement still needs an in-game check.

First complete candidate: **16:23:19 PDT**. Final ZIP verified:
**16:37:18 PDT**, **13m 59s** later.
Delivery notes prepared: **16:37:23 PDT**
(**14m 05s** from the same candidate).
This includes local checks, corrections, waiting for one matching automatic Windows run, download and
verification; the timer was not restarted. Measured CI wall time: **10m 53s**; runner usage:
**14m 26s**. These are development/package timings, not game-install benchmarks.

Update Studio, rebuild/install and restart Resonance. No preset reset or Prepare Game is needed.

## Published native esper reward readers — 2026-10-26

[Verified Windows ZIP / run 40412719255](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40412719255/Sephira-Studio-Test.zip), code `babf5a2`, update **1.2.110** (74.1 MB).
SHA-256 `de8fcf18cc475eef9fee8d2c06c6756909bc1e3806d1b2dc0fe95c313663a80b`.

- Correct the remaining reward-detection failures in the returned Siren trace. UE4SS e3ba1016 returns
  a Lua list of `RemoteUnrealParam` values; unwrap each element before treating it as an effect or ID.
  Supply the native passive-list output table instead of calling its getter without arguments.
  A failed optional passive read no longer discards successfully read continuous-effect markers.
- Update runtime fixtures to model wrapped values and the required output argument, and add native
  function signatures to the standalone observer. Preserve native MR activation through equipped Eiko,
  individual rewards and Spirit, without duplicate bonuses or reward/kit/balance changes. In-game
  confirmation is still required; modeled runtime checks do not constitute a live-game pass.

Validation: **753 Python tests** pass locally (45 skipped). Native-shaped fixtures reproduce the unwrapped
`IsValid` failure and missing-output-argument failure, then check wrapped returned lists, output values,
property TArrays, all-nine-esper lifecycle behavior, equipped Eiko/individual/Spirit activation and isolated
reader failure. Complete generated-script startup remains covered across six feature combinations.
Full Windows validation and compilation pass for the same commit, including Flutter analysis/tests, fresh
engine setup and launcher/updater checks. The downloaded ZIP passes provenance/checksum verification,
all **78** extension and **16** standalone Fina hashes, its compiled **1.2.110** label, and execution of the
actual packaged runtime against those fixtures. Native reward tables, roster/catalog, battle tuning and
the pinned sprite cache are unchanged. The returned reader-only capture confirms the native `OutList` signature and all four passive/marker IDs
on Fina with only Eiko equipped after the MR unlock battle. The initial absence was before earning those
rewards; native MR activation needs no extra fallback. The modifiers themselves still need an in-game
retest with the fixed runtime; fixtures and reader snapshots are not a live modifier pass.

First complete candidate: **22:28:00 UTC**. Final ZIP verified: **22:46:13 UTC**,
**18m 13s** later. Delivery notes prepared: **22:46:42 UTC**
(**18m 41s** from the same candidate). This includes checks, waiting for the
single matching automatic Windows run, download and verification; the timer was not restarted.
Measured CI wall time: **11m 07s**; runner usage: **15m 48s**. These are development/package timings,
not game-install benchmarks.

Update Studio, rebuild/install and restart Resonance before retesting. No preset reset or Prepare Game is needed.
The [updated standalone observer](https://raw.githubusercontent.com/biscoBen/FFR-Vison-Studio/babf5a240da20b0fb083396942d8b9f1bdfc1454/scripts/reference/esper-mastery/Esper-Mastery-Diagnostics.zip)
also works on the current installation without a Studio rebuild; installing the observer requires a game restart.
It records native function signatures, correctly unwrapped effects and active passive IDs.

## Published esper runtime activation fixes — 2026-10-26

[Verified Windows ZIP / run 40408382806](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40408382806/Sephira-Studio-Test.zip), code `5810e1d`, update **1.2.109** (74.1 MB).
SHA-256 `d43b0fcbc6507cfbbb195200768a1701e49698df838f88b15c17536d6e0602d7`.

### Combined esper/Fina runtime startup — 2026-10-26

- Fix the exact `FFRStudioFieldLeader/Scripts/main.lua:213: attempt to call a nil value` reported
  with Eiko's esper mastery and Crystal Fina installed together. Explicitly terminate each isolated
  Lua block so the next block cannot call the first block's nil return value. Execute the complete
  generated script across six feature combinations, and reproduce the old line-213 failure as a
  regression control. No summon mechanics, reward IDs, kits or battle tuning change.
- The new esper modifiers still require a live-game retest after rebuilding/installing and restarting.
  The standalone observer can distinguish remaining activation or native-call failures.
- The returned Siren trace also identifies a second activation failure: `GetContEffectList()` returns
  a plain Lua table, so `ForEach` fails before any mastery marker can be read. Support both returned
  Lua lists and property TArrays. Use the AI's reflected skill selection in the MP callback instead
  of the unavailable `CPP_BtlSkill:GetSkillId` object method; retain one payment per completed action,
  final-stack recovery, and dismissal/multi-hit guards. Correct the observer and its quoted-config-key
  detection alongside these fixes. Actual in-game behavior still needs confirmation.
- Preserve normal native MR activation through equipped Eiko, individually equipped rewards with any
  vision, or Spirit of Eiko. Read the game's active passive lists on Fina and her equipped vision;
  do not grant unlearned rewards or stack the same bonus when both sources are present.

### Esper mastery diagnostic helper — 2026-10-26

- Add a standalone read-only observer and collector for Eiko's equipable esper rewards. Record Fina's
  actual mastery markers, native unit/owner IDs, HP/MP, action counts and selected skills alongside
  the installed runtime configuration and existing activation/error messages. Use F8 snapshots and
  an optional unequipped comparison to investigate live-game reports; 100 ms polling cannot prove
  the absence of short events. The helper uses the existing UE4SS and needs no Studio rebuild.

Validation: **752 Python tests** pass locally (45 skipped), including six complete generated-script startup
combinations, both native array formats, all-nine-esper lifecycle checks and learned vision/individual/Spirit
activation without duplicate bonuses. The original startup failure is reproduced as a regression control.
Full Windows validation and compilation pass for this exact commit, including Flutter analysis/tests, fresh
bundled-engine startup and launcher/updater checks. The downloaded ZIP passes provenance/checksum verification,
all **78** extension and **16** standalone Fina hashes, its compiled **1.2.109** label, and execution of its actual
packaged builder/runtime against those fixtures. Native reward tables, roster/catalog, battle tuning and the
pinned sprite cache are unchanged. An in-game retest is still required; fixture checks are not a live-game pass.

First complete candidate: **21:45:02 UTC**. Final ZIP verified: **22:09:59 UTC**,
**24m 56s** later. Delivery notes prepared: **22:10:24 UTC**
(**25m 22s** from the same candidate). This includes local checks, the returned
diagnostic corrections, both automatic Windows runs, waiting, download and verification; the timer was not restarted.
Final CI wall time: **12m 23s**; final runner usage: **17m 09s**.
Total runner usage across both runs: **32m 23s**. These are development/package timings,
not game-install benchmarks.

Update Studio, rebuild/install and restart Resonance before retesting. No preset reset or Prepare Game is needed.
Use the [updated standalone observer](https://raw.githubusercontent.com/biscoBen/FFR-Vison-Studio/5810e1db87258fe84206ecfc7f287f222358061b/scripts/reference/esper-mastery/Esper-Mastery-Diagnostics.zip)
for another capture if the modifiers still fail. [Reward behavior and limits](docs/EIKO_ESPER_MASTERY.md).

## Published Eiko esper mastery, Mog LB rewards and Mystea MR swaps — 2026-10-26

[Verified Windows ZIP / run 40399517353](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40399517353/Sephira-Studio-Test.zip), code `1716763`, update **1.2.107** (74.1 MB).
SHA-256 `32db28c5f228581e2985291c9709b355104a3bef5cafee0dd155302a4a24c9d5`.

- Rework Eiko's MR rewards into equipable esper damage +20%, 5% summoner MP recovery per esper action,
  one extra ordinary action plus esper HP +20%, and 50% early-special chances with a guaranteed native finale.
  Keep Nullify Silence at MR1, remove direct summon commands and Double EXP, add early party Cure/Regen,
  and set tier 3/4 bonuses to Half MP Cost / Auto MP Restore (L).
- Give Mog Focus / First Strike / Recuperate LB / Peaceful LB Engine / LB Triple Charge at MR1/3/5/7/9.
  Swap Mystea's MR1/2 and MR5/9 choices while keeping AP/Spirit at MR9. Preserve stable save IDs and migrate
  the default kits once with backups; retain definitions for previously learned private equipment rewards.
- Retain all 131 original passive effects across the collection. Verify Rikku already has Vaan's native
  eight-hit all-enemy Fire resonance and guaranteed stealing, with Rikku's own presentation.
- Add native table readback, migration and executable Lua lifecycle checks; the new esper effects still need
  in-game validation. Existing challenge rotations, tuned damage and shared stat budgets are preserved.
  See [Eiko esper mastery](docs/EIKO_ESPER_MASTERY.md) for the reward table, Carbuncle support behavior and limits.
- Use native immediate-recovery events and native actor addresses on UE4SS 3.0.1. Fresh Lua wrappers must
  not repeat HP/damage bonuses or reset the extra-action counter; the wrapper regression is reproduced and fixed.

Validation: **318 Flutter tests** pass (one skipped), **744 Python tests** pass (45 skipped locally),
analysis is clean, and focused native/runtime checks pass. The native patch/readback covers all new passive/effect
rows, Eiko/Mog/Mystea MR and Spirit owner links, both healing skills and Rikku's Vaan mechanics. All **28** boss
stat budgets/action rotations and the other **27** playable visions are preserved. The original **75** MR equipables
remain available through MR and all **131** original passive effects remain represented across the collection.
A fresh-wrapper fixture reproduces the earlier userdata-identity failure and confirms the native-address fix.

Full Windows validation, compilation, fresh-engine setup, Flutter/Python and launcher/updater gates pass for
this exact commit. The downloaded ZIP passes the unchanged build helper's provenance/checksum checks,
all **78** extension and **16** standalone Fina hashes, the compiled **1.2.107** label, packaged kit migrations,
native immediate-recovery settings and all-nine-esper Lua contracts. The pinned sprite-cache implementation is
unchanged. The new esper effects and Spirit behavior still require an in-game check; no live game pass is claimed.

First complete candidate: **20:10:10 UTC**; final ZIP verified: **21:04:53 UTC**,
**54m 43s** later. Delivery notes prepared at **21:06:20 UTC**
(**56m 09s** from that same candidate). This includes local checks/corrections,
three automatic Windows runs, waiting, download and verification; the timer was not restarted for either correction.
Final CI wall time: **10m 51s**; final runner usage: **14m 56s**.
Across all three successful runs, runner usage totals **45m 10s**.
These are measured development/package timings, not game-install benchmarks.

Update Studio, rebuild/install and restart Resonance. Keep Studio Test Data. Current default kits migrate once
with backups; edited MR conflicts remain visible for deliberate resolution. No preset reset or Prepare Game is needed.

## Published Eiko boss spell power tuning — 2026-10-26

[Verified Windows ZIP / run 40378174047](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40378174047/Sephira-Studio-Test.zip), code `6fd60ea`, update **1.2.104** (74.1 MB).
SHA-256 `ead9b1d058168f8b0d1b7f19239991cd58af95462fc185d854839b9d67043bec`.

- Set Eiko's boss **Firaga Burst to power 20** (from 25) and **Blizzaga Burst to power 25** (from 29) in the paired Eiko/Rikku encounter, following the latest in-game test.
- Preserve White Whorl, Light of the Eidolons, Flash Bomb, all other attacks, the shared HP/break budget, speed and rotation. Original and playable skills, all other encounters and the permanent vision-ID recovery remain unchanged.
- Apply on rebuild/install with existing rosters and caches. No preset reset, Prepare Game, save edit or new sprite/icon conversion is needed for these coefficients.

Validation: **32** focused encounter/cache tests pass. Native patch/readback checks all **528** generated boss
recipes and confirms exactly two changed rows: Eiko's private Firaga Burst **815130**, **25 → 20**, and Blizzaga
Burst **815140**, **29 → 25**. All **526** other recipes, all **28** boss stat budgets/action orders and every
original skill row are preserved. Full Windows validation, compilation, fresh-engine setup, Python/Flutter and
launcher/updater checks pass for this commit. The actual downloaded ZIP matches provenance/SHA-256, all **75**
extension and **16** standalone Fina hashes, the compiled **1.2.104** label and the packaged recipes' exact powers
**20 / 25**. The pinned sprite-cache implementation is unchanged. The next in-game test determines battle feel.

Update Studio, rebuild/install and restart Resonance. Keep the existing Studio Test Data.

Measured delivery: first complete candidate 11:27:50 to verified package
11:42:28 America/Los_Angeles, **14m 38s**, including local/native
checks, CI waiting and package verification. The timer was not reset. Measured CI wall time is **12m 05s**,
with **16m 26s** summed job runtime. The exact automatic push run was joined through the unchanged build
helper; no duplicate build was dispatched. Publication notes are a separate README/CHANGELOG-only commit.

## Published permanent Sephira vision IDs and roster recovery — 2026-10-26

[Verified Windows ZIP / run 40373555255](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40373555255/Sephira-Studio-Test.zip), code `5f75568`, update **1.2.103** (74.1 MB).
SHA-256 `76cec0d9d6fd9a71039b34b86a86bc4ed63f5520405eaaf49e8d6638922b4aed`.

- Fix an owned vision appearing locked after switching PCs: game saves retain numeric vision identities, while older Studio collections could allocate different IDs. Hard-code all **30** Sephira identities, including Crystal Fina **13503**. New collections, restores and resets use this scheme; occupied IDs stop instead of silently allocating another vision.
- Reduce boss **Blizzaga Burst** by approximately **45%**, power **52 → 29** after rounding. Firaga Burst and White Whorl keep their earlier reductions; Light of the Eidolons, Flash Bomb, all playable skills and the rest of the encounter are unchanged. Native readback checks all **528** boss recipes and confirms this is the only changed skill.
- Back up and correct older Sephira allocations on loading. Remap their private skills, commands, Spirits and cross-vision references together while preserving kits, stats, acquisition and artwork. Unrelated characters keep their identities. With this update on both PCs, the same Steam-synced save works without transferring Studio configuration files. This scheme follows the reviewed playthrough; a different historical save may need an ownership audit first.
- Add **Restore roster for same save**, using the two-arrow button beside **Load all character configs**, for users who can transfer configuration files. It restores the complete roster with exact saved IDs and a backup, rather than merging destination identities. Ordinary imports now reject renumbering a tagged Sephira vision. Keep the control within the existing footer height so the vision grids and drag targets remain usable.
- Add the read-only [Vision Save Check collector](scripts/reference/vision-save/Vision-Save-Check.zip). It copies saves and a detected roster for inspection, records hashes and the roster's source, and edits no save or installed mod. A returned save's checksum, structure and actual ownership/progression must be checked; catalog differences alone are not ownership evidence. Personal saves and rosters are not part of this release.

Validation: **315 Flutter tests** pass locally (one Windows-only test skipped), analysis is clean, and **739 Python
tests** pass locally (42 platform skips). Fixed-ID tests cover all 30 presets, reverse order, reset/missing entries,
legacy identity normalization, occupied native/private IDs and older kit migrations. Transfer checks cover swapped
identities, cross-vision references, backup/write failure and stale editor updates. The collector passes executable
PowerShell byte/hash preservation and source/output separation checks. A native round trip preserves every original
row and confirms Fina's unit SaveId **13503**, item **13503**, command **323** and Spirit **1350300**.
Full Windows validation, compilation, fresh-engine startup, launcher/updater checks and publication pass for this
commit. The actual downloaded ZIP matches provenance/SHA-256, all **75** extension and **16** standalone Fina
hashes, the compiled **1.2.103** label and the transfer/identity migration controls. Sprite-cache implementation
remains pinned and unchanged. The user has confirmed the corrected roster restores Fina; the automatic update and new Blizzaga tuning need the next live test.

Update both PCs, reopen Studio, rebuild/install and restart Resonance. The old roster is backed up automatically.
No preset reset, Prepare Game, game-save edit or between-PC Studio transfer is needed for this playthrough.
The user confirmed Fina's recovery with the corrected roster; automated recovery and Blizzaga tuning still need the next in-game test.

Measured delivery: first complete candidate 10:10:50 to verified package
11:11:53 America/Los_Angeles, **61m 03s**, including the footer fix,
returned-save audit, requested permanent-ID/automatic recovery work, local/native checks, four builds, waiting and
package verification. The timer was not reset. Final-run CI wall time is **12m 46s**, with **17m 29s** summed
job runtime; all four runs use **58m 10s** summed job runtime. Matching automatic push runs were joined
through the unchanged build helper; no duplicate build was dispatched. Publication notes are a separate
README/CHANGELOG-only commit.

## Published Rikku/Eiko boss burst reduction — 2026-10-25

[Verified Windows ZIP / run 40279755866](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40279755866/Sephira-Studio-Test.zip), code `0db2aeb`, update **1.2.100** (74.1 MB).
SHA-256 `a560c435a9bd73f0ba8dc321e4c485e29e5dea3d938963b5a88d188e680f9f9b`.

- Address the reported level-15 party wipe in the level-12 Rikku/Eiko encounter on the hardest difficulty. Reduce boss **White Whorl** and **Firaga Burst** by approximately **45%**: private skill power **45 → 25**, a **44.4%** reduction after integer rounding. Each per-skill coefficient is 55% of its former value.
- Keep their current HP, break gauges, speed, action order, other attacks and level. The original and playable versions of both skills, all other vision fights, Nalu's size/animation update, Fina's friendly Cure, walking replacements and crystal interactions are unchanged.
- Apply on the next rebuild with existing saved visions. Preserve the sprite-motion cache signature and pinned cache implementation; unchanged sprites/icons do not need converting for these coefficient changes.

Validation: **735 Python tests** pass locally (42 platform skips), including the existing encounter pressure and
cache checks. Native patch/readback checks all **528** generated boss skill recipes and confirms exactly **two**
changed rows: Eiko's private Firaga Burst **815130** and Rikku's private White Whorl **827090**, both power 25.
All other generated skills, all **28** boss stat budgets/action orders and every original skill-table row are
preserved. Full Windows validation, compilation, fresh engine and launcher/updater checks pass for this commit.
The actual downloaded ZIP matches provenance/SHA-256, all **75** extension and **16** standalone Fina hashes,
the compiled **1.2.100** label and the two intended coefficient overrides. The playable catalog is unchanged.
**Real damage and encounter difficulty still need the user's in-game retest.** Keep Studio Test Data, update,
rebuild/install and restart. No preset reset or Prepare Game is needed.

Measured delivery: first complete candidate 23:21:13 to verified package
23:39:25 America/Los_Angeles, **18m 12s**, including local/native
checks, CI waiting and package verification. The timer was not reset. Measured CI wall time is **10m 13s**,
with **14m 25s** summed job runtime. The exact automatic push run was joined through the unchanged build
helper; no duplicate build was dispatched. Publication notes are a separate README/CHANGELOG-only commit.

## Published smaller playable Nalu and Lance Launcher animation — 2026-10-25

[Verified Windows ZIP / run 40251214869](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40251214869/Sephira-Studio-Test.zip), code `1f38713`, update **1.2.99** (74.1 MB).
SHA-256 `f4748b3daf80deb367223a403adda651284b88e9889239dcdd0836ede951d473`.

- Make Nalu's playable battle sprite **35% smaller**: her native battle-design scale changes from **1.00 to 0.65**. Existing saved Nalu entries receive the change on their next build without a preset reset. Menu sprites/icons and the shared converted sprite assets are unchanged.
- Keep Nalu's boss scale at **1.30**, with the tested Nalu/Jade fight unchanged. The size adjustment targets only the playable vision's private design row, including allocated/imported identities. Other visions' sizes, stats, skills and acquisition routes are unchanged.
- Give playable **Lance Launcher** the **Thunder Spear** caster, effect and sound tracks. Preserve Lance Launcher's original two-hit master and cooked evaluator: swapping in Thunder Spear's one-hit master would lose a damage marker. Keep both original hit times, two 50% damage packets, physical Lightning damage, power 12 and MP cost 10.
- Apply the reviewed animation swap to existing default recipes with borrowed visuals on or off. Explicitly authored user animations retain precedence. The playable skill and all native/global and boss routes remain separate. Retain the sprite-motion cache signature and pinned cache implementation, so this adjustment reuses unchanged sprite/icon conversion.

Validation: **735 Python tests** pass locally (42 platform skips), focused presentation/cache/shrine checks pass,
and analysis is clean. The native design-table patch/readback verifies Nalu at 0.65, both Nalu/Jade bosses at 1.30,
Jade's playable size at 1.00 and every original design row intact. The actual builder's clone/patch/readback path
passes for Lance Launcher with borrowed visuals **off and on**: the cut/effect/sound children come from Thunder
Spear, the original two-hit master and opaque cooked evaluator are retained, and skill-table readback preserves
both hit ratios, power, cost, damage type and element. The same recipe generates and verifies the player scale.
Full Windows validation, compilation, fresh engine and launcher/updater checks pass for this commit. The downloaded
ZIP matches provenance/SHA-256, all **75** extension and **16** standalone Fina hashes and the compiled 1.2.99 label.
The catalog, working walking controller, shrine logic, Fina's friendly Cure and movie/audio remain intact.
**Live visual size and animation timing still need the user's retest.** Keep Studio Test Data, update,
rebuild/install and restart. No reset or Prepare Game is needed.

Measured delivery: first complete size candidate 17:33:19 to verified package
18:01:56 America/Los_Angeles, **28m 36s**, including the subsequent
animation request, native prototype/readback checks, local regression checks, CI waiting and package verification.
The timer was not reset. Measured CI wall time is **10m 05s**, with **15m 08s** summed job runtime.
The exact automatic push run was joined through the unchanged build helper; no duplicate build was dispatched.
Publication notes are a separate README/CHANGELOG-only commit.

## Published walking callback recovery and crystal interaction — 2026-10-25

[Verified Windows ZIP / run 40241100839](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40241100839/Sephira-Studio-Test.zip), code `59205a0`, update **1.2.98** (74.0 MB).
SHA-256 `9fc1bbdf79e7bf1725cff20ce60e03f1776d5830de2eb879f099e073b29f7ea4`.

- Address the 1.2.95 regression where Rain remains visible after saving Fina as an overworld appearance. The returned UE4SS log shows callback collection followed by `Ref was not function`. An executable weak-reference fixture reproduces that lost callback in the shipped controller. Use the persistent game-thread loop already working for Fina's presentation, retain loop/hook/key callbacks, and recover lost updates and transient loading errors.
- Keep the saved replacement for ordinary field idle, walking and running; restore original characters for cutscenes and reapply the saved choice when control returns. Retain input/menu/vehicle/encounter/story guards, optional party cycling and native Charlotte. Log state changes and the active map-unit/slot for any further runtime diagnosis.
- Require **A/Confirm** at all **13** native repeat crystals with enabled Sephira challenges, including Crystal Fina/Lenneth at Warrior of Light's sanctum. Selecting Leave no longer starts another challenge dialog merely from moving in the overlap area. Use the same button-operated native class for Christine's cave crystal.
- Replace only each selected repeat actor's class and component archetypes. Preserve native original-vision grants, replay targets, unlock conditions, event movement, placement and unrelated story actors. Groups moved to the shop or omitted from the build do not alter their shrine level. Validate native map serialization before sprite work and reuse those outputs later in the build.
- Give Crystal Fina a guarded Cure opportunity every **2–3 actions**, using the native lowest-HP friendly target helper so she can heal either herself or Lenneth. Recover **15%** of the target's maximum HP when the selected friendly unit is at or below **85%** HP; otherwise use her light attack. **Sacred Wave stays at its tested damage.** The player kit and the other 27 boss rotations are unchanged.
- Preserve the sprite-motion cache signature and the pinned cache implementation. Walking model generation, native field table recipes, sprites/icons, Fina movie/music, the approved Fina/Aria kits and all **75/75** equipable MR rewards are unchanged.

Validation: **735 Python tests** pass locally (42 platform skips), **78 focused Flutter tests** pass, and analysis is
clean. Executable Lua checks cover callback collection, failed scheduling, lost/late callbacks, scene transitions,
field idle/movement and transient actor errors. Native fromjson/readback checks pass for all **14** affected maps,
including the sanctum and Christine's cave, preserving actor references and original level data. A numbered-actor
FName serialization issue found in the first native proof was corrected before the final candidate; all 14 writes
then passed. The exact native clone/fromjson/readback pipeline also passes for both updated Fina AI functions. Native Kismet binary write/readback and real-engine jump-size checks pass, and an interpreter executes the collected base target helper to confirm Cure reaches either friendly boss while attacks retain native random routing. All 28 bosses keep their offensive skill rows and stats; only Fina's Cure changes from self to friendly single-target. Full Windows validation, compilation, fresh engine setup and launcher/updater checks pass for the final
commit. The actual ZIP matches provenance/SHA-256, all **75** extension and **16** standalone Fina hashes, the compiled
1.2.98 label, the retained controller and the delivered shrine module exercised against all 13 native repeat maps.
**The user's live controller and interaction retest remains necessary.** Keep Studio Test Data, update,
rebuild/install, restart and re-enter the room. No preset reset or Prepare Game is needed.

Measured delivery: first complete walking candidate 15:02:36
to verified combined package 15:50:05 America/Los_Angeles,
**47m 29s**, including local checks, the subsequent shrine and healing requests, their checks and corrections, all three builds,
waiting and package verification. The timer was not reset. The earlier walking-only 1.2.96 run **40238424891**
passed, as did the shrine update run **40239800056**. The subsequent friendly-healing request required the final 1.2.98 candidate. All three exact automatic push runs were joined
through the unchanged build helper; no duplicate dispatch was made. Final CI wall time is **10m 13s** and
summed job runtime **14m 39s**; the earlier CI wall times were **9m 42s** and **13m 21s**, with **45m 43s**
total summed job runtime across all three runs. Publication notes are a separate README/CHANGELOG-only commit.

## Published original cutscene appearances and native Charlotte walking — 2026-10-25

[Verified Windows ZIP / run 40235225775](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40235225775/Sephira-Studio-Test.zip), code `c981429`, update **1.2.95** (74.0 MB).
SHA-256 `fbf9249e6824c083f0738bc68b8b7eca30e8bcd58aaaaeaf43d5e2a42a516424`.

- Overworld replacements previously occupied the native primary slot, so cutscenes alternated the chosen model's idle with the original character's gestures. Preserve the complete original slot prefix and put the walking choice in a separate cosmetic slot. Rain remains Rain throughout scenes; the saved replacement returns when field control resumes, including while standing still.
- Keep the replacement for normal field idle, walking and running. Restore before native event entry or disabled player input, and respect story costume slots, menus, encounters and vehicles. Stage the existing cosmetic runtime automatically for a saved walking choice. It works with party cycling off and does not bind LB/L1 or F6 in that mode. Existing saved choices need no migration or reselection.
- Add **Charlotte (Resonance)** to **Edit overworld appearance**, using her original `npc0470` field project and textures. Preserve her NPC/story/vision assets and every original party animation slot. Private aliases supply player directional/idle names; an NPC walking clip supplies running when a distinct run family is absent. Use the existing bundled Charlotte portrait, with no FFBE pack download. Charlotte does not become an extra party identity or battle-voice option.
- Retain battle models, voices, progression, acquisition, mastery rewards, Fina movie/audio and all other character choices. Reuse the owned UE4SS deployment/rollback path. Saved field choices now require the same existing runtime loader used by cycling and native Fina effects; a missing loader is reported before game packages change.

Validation: **725 Python tests** pass locally (42 platform skips), **70 focused Flutter tests** pass, and analysis is
clean. Executable Lua checks cover field idle/movement, synchronous event restoration, gestures and idle inside a
scene, native story slots, post-scene idle, input/menu/battle/vehicle guards and actor recreation without enabling
cycling. Actual native table writing/readback covers eight saved choices with cycling off/on and Rain → Charlotte,
preserving every original primary/story slot and Charlotte's complete NPC row. Synthetic native SS6 checks cover the
NPC package rename and drawable walk-to-run/directional/field-idle aliases. The real Charlotte project is validated
against the selected game during build; its live walking appearance is not established by the synthetic fixture.
The existing sprite cache stays byte-identical to its pinned version and sprite reuse tests pass. Full Windows
validation, compilation, engine setup and launcher/updater checks pass for this same commit. The downloaded ZIP
matches provenance/SHA-256, all **75** extension and **16** standalone Fina hashes, the compiled 1.2.95 label,
cutscene guard, native Charlotte choice/portrait and unchanged Sephira kits.
**Live cutscene transitions and Charlotte walking still need in-game confirmation.** Keep Studio Test Data, update,
rebuild/install and restart. No preset reset, Prepare Game or Fina appearance reselection is required.

Measured delivery: first complete cutscene candidate 14:15:46
to verified package 14:33:52 America/Los_Angeles,
**18m 05s**, including the subsequent native Charlotte request, local checks, the picker-count fixture
correction, native serialization proof, waiting and package verification (including the Windows catalog line-ending
check correction); the timer was not reset. Measured Windows
CI wall time is **9m 41s**; summed job runtime is **13m 39s**. The matching automatic push run was reused;
no duplicate build was dispatched. Publication notes are a separate README/CHANGELOG-only commit.

## Published transferable MR rewards, native walking choices and automatic Fina cinematic — 2026-10-25

[Verified Windows ZIP / run 40227331721](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40227331721/Sephira-Studio-Test.zip), code `22f8bf9`, update **1.2.94** (74.0 MB).
SHA-256 `cf23e1a36b8972baecbc35c586d503c583b0ae0ac157e05f244fad3116c63f2f`.

- Restore all **75 individual equipable MR rewards** from the 15 excluded original visions as Sephira MR rewards. The 25 restored active rewards keep their original MR ranks and acquisition gates, stock mechanics, equip/MP costs and animation references. Keep all 50 original passive MR rewards transferable. Move supplemental passives into awakening to make room, retaining all **131 original passives** across the kits. Each odd MR rank still has one ability; MR9 retains its ability, permanent AP and Spirit.
- Match each vision's native counterpart passive count and keep passive AP totals within 20%. Keep themed awakening versions on other units where appropriate, such as Relm's Mimic, while the MR teacher matches the original gate. Preserve Crystal Fina and Aria's approved kits, Spirits, artwork, permanent stats, private combat recipes and acquisition choices. [Allocation and migration](docs/SEPHIRA_MR_RESTORATION.md); [75/75 MR audit](docs/SEPHIRA_MR_COVERAGE.md).
- Back up and migrate untouched saved layouts once. Deliberate edits to affected MR slots and full awakening tiers remain intact and report a conflict before building. Later edits remain user choices. Existing IDs, artwork and acquisition overrides stay intact; no preset reset is needed.
- Add all eight native Resonance party characters to **Edit overworld appearance**, alongside FFBE. Rain can walk as Dark Fina while retaining his battle identity and progression. Reuse native textures and animation clips through cached private walking projects; story costume slots and unrelated assets are preserved. Native choices require no sprite download or texture conversion.
- Remove **Test Crystal Fina cinematic**. Her cinematic is included automatically when she is in the build, even if the old saved toggle was off. Removing Fina removes the companion movie package. Preserve the chosen artwork, working HCA v3/ADX audio path, single playback, battle-music pause/resume and the 0.4s/0.8s fades from 1.2.92.

Validation: **720 Python tests** pass locally (42 platform skips), **92 focused Flutter tests** pass, and analysis is
clean. Native writing/readback checks cover all 30 kits plus an independent Fina, every Spirit owner and the complete
unchanged stock rows for all 25 restored MR actives. Native map tables preserve all eight walking swaps and unrelated
story rows. A real Fina build with the old toggle off passes stereo movie descriptor and picture-preservation checks;
its verified warm movie reuse takes about 0.060s. The existing sprite cache remains byte-identical to its pinned
version and MR/acquisition changes retain sprite reuse. Full Windows validation, compilation, engine setup and
launcher/updater checks pass for the same commit. The actual downloaded ZIP matches provenance/SHA-256, all **75**
extension and **16** standalone Fina hashes, the compiled 1.2.94 label, native choices, removed switch and 75/75 MR audit.
**Live native walking swaps, the new equipable reward placements and automatic cinematic playback still need in-game
confirmation.** Keep Studio Test Data, update, rebuild/install and restart; no Prepare Game or preset reset is required.

Measured delivery: first complete candidate 11:19:47
to verified package 12:51:50 America/Los_Angeles,
**92m 03s**. This includes the initial native/cinematic/audit candidate, the Windows report-encoding correction,
the subsequently requested MR restoration, local test/fixture/packaging/cache corrections, waiting and package
verification; the timer was not restarted. The final run's measured CI wall time is **8m 23s**, and summed
job runtime is **12m 40s**. Across the three automatic Windows runs, summed CI wall intervals are
**28m 30s** and summed job runtime is
**41m 10s**. The first run failed the new report's Windows text
encoding check; its corrected run passed. The final requested MR restoration was built at its own commit.
The matching automatic runs were reused; no duplicate build was dispatched. Publication notes are a separate
README/CHANGELOG-only commit and do not request another binary.

## Published gentle Fina movie music fades — 2026-10-25

[Verified Windows ZIP / run 40218872561](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40218872561/Sephira-Studio-Test.zip), code `4308e0e`, update **1.2.92** (74.0 MB).
SHA-256 `8591e24e958ab12120b261e3b88fae56dd4e55fc1db9b800cb60ec647015aeef`.

- The user confirms Crystal Fina's music now works in game. Soften its start and ending with a **0.4-second fade in** and **0.8-second fade out**, using a smooth volume envelope on both stereo channels before the existing ADX encoding step. Studio's preview uses the same faded samples.
- Preserve the working HCA v3 decoder, ADX encoder/muxer, movie pictures, 6.4-second duration, stereo format, single playback and battle-music pause/resume behavior. Replace only the cached scored movie automatically; the decoded source, sprite/icon and voice caches retain their inputs. Fades are prepared during the build and add no per-cast processing.

Validation: **713 Python tests** pass locally (42 platform skips), **31 focused Flutter tests** pass, and analysis is
clean. Synthetic stereo checks verify silent endpoints, smooth channel-matched fades, exact duration and an unchanged
middle. The actual cave recording passes the existing ADX encoder and independent ADX v4 decoding at **47.38 dB SNR**
against the faded samples. All 192 picture and opacity packets retain their timestamps and bytes. Cache checks replace
the old unfaded movie and reuse the verified faded copy on the next build. Full Windows validation, compilation,
fresh engine setup and launcher/updater checks pass for this commit. The downloaded ZIP matches provenance/SHA-256,
all **74** extension and **16** standalone Fina hashes, the compiled 1.2.92 label and unchanged codec/artwork assets.
No game recording or key is bundled. **The new fades still need an in-game listening check.** Keep Studio Test Data,
update, rebuild/install and restart; no preset reset or Prepare Game is required.

Measured delivery: first complete candidate 10:54:42
to verified package 11:07:49 America/Los_Angeles,
**13m 06s**, including local checks, encoding proof, waiting and package verification. This run's measured
CI wall time is **10m 01s**; summed runner usage is **14m 22s**. The matching automatic build was reused;
no duplicate build was dispatched.

## Published reviewed Crystal Fina and Aria kits — 2026-10-25

[Verified Windows ZIP / run 40216026078](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40216026078/Sephira-Studio-Test.zip), code `a729e0d`, update **1.2.91** (74.0 MB).
SHA-256 `a942c08edb95e27c942d97a2fed67b1703cbfc4fd563ae0d6915382bc973db7f`.

- Apply the user's four-tier ability/awakening layouts to Crystal Fina and Aria, including the independent Fina preset. Fina gains earlier protection and revival; Aria focuses on Water blades, Water magic and healing. Both use native 40-MP Reraise rather than the internal zero-MP revive event. Keep physical Water Blades physical.
- Aria's MR9 and Spirit now use Imbue Water. Retain the former private Light reward ID (1910), both Spirit IDs and their own vision references. Spirits follow their owner's current five MR passives; awakening bonuses and permanent MR stats are excluded. All 160 original active skills and 131 original passives remain represented across the collection.
- Back up existing rosters and apply this kit revision once, preserving skill definitions/private IDs, combat edits, MR stat grants, acquisition and artwork. Keep unrelated extra learned grants where they fit. Overfilled tiers remain intact, with a readable conflict from **Apply kit and MR updates**. Later deliberate edits remain yours. Give independent and collection Fina's copied skill rows distinct names so they can coexist.

Validation: **710 Python tests** pass locally (42 platform skips), **63 focused Flutter tests** pass, and analysis is clean.
Real native serialization/readback checks all four awakening tiers, ten MR ranks and Spirit ownership/descriptions for
both Fina versions and Aria; Aria's private reward retains ID 1910 and uses native Water effect 40207. Full Windows
validation, compilation, fresh engine setup and launcher/updater checks pass for the same commit. The downloaded ZIP
matches provenance, SHA-256, all **74** extension and **16** standalone Fina resource hashes, the catalog and compiled
1.2.91 label. Warm sprite/icon cache code and existing cinematic/audio bytes are unchanged. No game recording, key or
animation library is bundled. **The revised healer kits still need live gameplay confirmation.** Keep Studio Test Data,
update, rebuild/install and restart. No preset reset or Prepare Game is required.

Measured delivery: first complete candidate 10:17:02
to verified package 10:33:02 America/Los_Angeles,
**15m 59s**, including local checks, the independent row-name correction, waiting and package verification.
This run's measured CI wall time is **9m 51s**; summed runner usage is **13m 45s**. One matching automatic
run was reused; no duplicate build was dispatched.

## Published clear Fina movie sound and HCA v3 preview — 2026-10-25

[Verified Windows ZIP / run 40210925843](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40210925843/Sephira-Studio-Test.zip), code `0c9b92e`, update **1.2.90** (74.0 MB).
SHA-256 `a3e3f114e63716fad0e27f9ba7e433a0bae262f7cac67635f66a7759dd777bd8`.

- Fix the washed-out cave-music preview: the old decoder unpacked HCA v3 resolution-zero coefficients with HCA v2 rules. Add a small managed decoder for this recording's independent-channel layout, including v3 noise reconstruction, correct bit consumption and strict frame checks. Reuse the existing licensed VGAudio tables/IMDCT, with vgmstream algorithm attribution. The user confirms the independently decoded comparison sounds like clear cave music. Invalidate the old preview WAV automatically; no game recording or key is bundled.
- The private native cue in 1.2.89 stayed silent in game. Restore the embedded stereo ADX soundtrack that previously played, using the corrected samples. Match native movie audio metadata and preserve every picture/opacity packet, the once-only movie window, battle-music pause/resume and the existing sprite LB/cure sound. Cache the scored movie and restore it with sound on warm installs; fail visibly if it cannot be prepared. Existing sprite/icon and voice codec caches keep their inputs.

Validation: 706 Python tests pass locally (42 platform skips), 33 focused Flutter tests pass, and analysis reports no
issues. The managed preview matches independent clHCA v3 decoding within one PCM16 unit; independent ADX v4 decoding
retains the clear stereo waveform. Chromium passes sound, pause, seek and volume checks. Native readback confirms
both movie audio descriptors, inert spare tracks and identical cold/warm output. The cached movie stage measures
19.71 seconds cold and 0.061 seconds warm, with its recording already prepared; these are not full install timings.
Windows validation/compilation, the actual Windows HCA v3 fixture, fresh frozen-engine setup and launcher/updater
checks pass for this commit. The downloaded ZIP matches its checksum, provenance, all 74 managed-extension files,
16 standalone Fina files, compiled version and unchanged artwork. The animation library and game audio are excluded.
**The corrected embedded soundtrack still needs in-game listening confirmation.** Keep Studio Test Data, update,
rebuild/install and restart; no Prepare Game or preset reset is needed.

Measured delivery: first complete candidate 09:03:19
to verified package 09:26:51 America/Los_Angeles,
**23m 32s**, including local checks, corrections, waiting and ZIP verification. This run's measured CI wall time
is **8m 26s**; summed runner usage is **12m 31s**. A first validation attempt caught a stale startup-test
version expectation and was corrected before publication. Across both attempts, CI wall totals **14m 02s**
and runner usage totals **22m 02s**. The delivery interval includes that correction; earlier
completed releases are not included.

## Published native Fina music, preview sound and matching challenge damage — 2026-10-25

[Verified Windows ZIP / run 40176189690](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40176189690/Sephira-Studio-Test.zip), code `961a89d`, update **1.2.89** (74.0 MB).
SHA-256 `cd5bfd306e0b15c837229102ee9041ee179e55f04713d751d2ec9806f3f915de`.

- Apply the additional 50% attack-power increase from Christine’s approved fight to every other vision challenge, for physical and magical damage. Preserve team damage sharing, HP/break budgets, levels, speed, healing and control effects. Christine stays at her approved powers (39 Blizzard, 50 Blizzara, 78 Freezing Spike), with no second application of the factor. The user confirms her current difficulty, result-screen reward and normal field return work.
- Replace Fina’s distorted converted movie soundtrack with a private native sound cue containing the original cave recording’s compressed/encrypted frames. Trim it losslessly to 6.4 seconds from the beginning, remove looping, retain its AWB subkey, and stop at the movie endpoint. Embed the short recording in its own sound sheet so playback does not depend on the cave’s streaming BGM state. Mana carries the unchanged silent movie/opacity, so no converted second soundtrack competes. Keep battle music pause/resume and once-only movie timing.
- Add explicit Play with sound and separate audio controls to Studio’s preview. Unlock browser audio through the button, synchronize pause/seek/rate/volume, and show the actual audio endpoint error when loading fails. Normalize the short WAV header for browser playback. All original picture packets/artwork stay unchanged; no new game recording is bundled with Studio.

Includes the 1.2.88 default battle-name, result-screen vision reward and movie-voice conversion changes. Christine's
balance/reward/normal field return are confirmed by the user; the other fights and new Fina audio remain live tests.

Validation: 704 Python tests pass locally (41 platform skips), 31 targeted Flutter tests pass (one Windows-only local
skip), and analysis reports no issues. Native readback validates the combat rows, private music sheet/cue and original
encrypted HCA frames, with matching metadata and no competing Mana audio track. The same native movie stage took
22.43 seconds cold and 0.11 seconds warm with its recording already cached; outputs match. These are stage timings,
not complete install measurements. Chromium with user-gesture autoplay restrictions passes sound, pause, seek/resume
and volume checks. Windows validation/compilation both pass for this commit. The downloaded ZIP matches its checksum,
compiled version and all 72 managed extension / 16 standalone Fina manifest files. Original movie/artwork checksums
stay unchanged. No game music or animation-library download is added to Studio. Keep Studio Test Data, update,
rebuild/install and restart; no Prepare Game or preset reset is needed. Test Fina's music in game and use Play with
sound in Studio. Actual Windows audio output still needs the user's listening check.

First complete candidate 07:11:29 UTC to this verified ZIP 08:32:35 UTC:
**81m 06s**, including the intermediate 1.2.88 delivery, later audio reports and wider balance request, source
investigation, local corrections/proofs, Windows waiting, GitHub transport recovery and ZIP verification. This package's
CI wall time **9m 59s**; summed runner usage **14m 30s**. The earlier 1.2.88 run took 10m 20s wall and
14m 45s runner time. Two exact automatic runs joined across the task; no duplicate/manual dispatch. After public
GitHub API access expired, the unchanged build helper's selection, job, input-provenance and checksum checks used
GitHub connector metadata for the same runs. No stored credentials were read or altered.

## Published battle labels, Christine tuning, result rewards and voice format — 2026-10-25

[Verified Windows ZIP / run 40172348648](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40172348648/Sephira-Studio-Test.zip), code `93fba5d`, update **1.2.88** (74.0 MB).
SHA-256 `9717705b7e87d327c90e4343f8f90a1d27d3195da6a4857575510dc391243780`.

- Make automatic battle command labels follow default-vision model names, including existing saved replacements such as Tronn → 21O. Preserve native punctuation, command IDs, kit/voice settings and custom command labels/descriptions. Repeated model changes and Use original model update automatic labels consistently.
- Increase Christine’s enemy Blizzard, Blizzara and Freezing Spike by another 50% from 1.2.87 (Blizzard potency 26 → 39; Blizzara 33 → 50; Freezing Spike 52 → 78). Keep her tested speed, HP/break budget and Slumber Mist, and keep player skill values.
- Remove every post-battle challenge reward event after the user reported the black return again. Put each vision on its enemy’s normal result-screen loot using the native boss guaranteed-drop value **1**. The earlier value **100** was a reciprocal chance, rather than 100 percent. Results should list and grant the vision before returning normally; live confirmation is still needed. Escape/loss have no reward event and enemies cannot be stolen from.
- Convert movie-only voice selections to the proven native mono HCA v3 bank format, with matching waveform metadata and host encryption. Previously the private voice bank kept the encoder’s stereo v2 stream without native adaptation. Preserve voice timing, native voice-volume routing and original movie pictures/non-voice sections. Invalidate only prepared voice entries; retain sprite/icon reuse. Native bank readback/decode passes for Cloud’s movie voice routed onto Tronn; Lightning’s exact movie was not included in the supplied reference and still needs an in-game listen.

Validation: 703 Python tests pass locally (41 platform skips), 105 targeted Flutter tests pass (one Windows-only local
skip), and analysis reports no issues. Native readback passes for command labels, Christine's ice attacks, all 28 loot
entries and empty battle finish callbacks. All four native voice routing combinations pass; generated voice banks
contain encrypted mono HCA v3 with matching waveform metadata, and every clip decodes successfully. This proves the
converted bank path with supplied Cloud/Tronn samples, not live Lightning playback. Windows validation and compilation
both pass for this commit. The downloaded ZIP matches its checksum, compiled version and all 72 managed extension / 16
standalone Fina manifest files. No animation-library download is included. Keep Studio Test Data, update, rebuild/install
and restart. Existing default-model replacements get the command-label fix without reselecting them. No preset reset
or Prepare Game is required. Confirm the vision is listed/granted on the battle result screen, normal field return,
Christine's damage and Lightning's voice in game.

The user's new report of distorted Fina movie music remains active follow-up work; this intermediate package does not change that soundtrack.

First complete candidate 07:11:29 UTC to verified ZIP 07:34:53 UTC:
**23m 23s**, including focused/full local checks, native proofs, Windows waiting and downloaded-package
verification. CI wall time **10m 20s**; summed runner usage **14m 45s**. One exact automatic run joined;
no duplicate/manual dispatch.

## Published challenge balance, victory grants and movie audio — 2026-10-24

[Verified Windows ZIP / run 40146427534](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40146427534/Sephira-Studio-Test.zip), code `a10f83b`, update **1.2.87** (74.0 MB).
SHA-256 `1965895138f7a28efaa0fab51e4f59dba95b203df144049b97d603db3d0671e4`.

- Apply Christine’s boss approach to all 28 challenge enemies across 15 encounters: approximately 15% faster turns, stronger physical/magic offense, bounded attacks +50% and damaging signatures +75%, divided across partners. Give casters spell basics and add thematic elemental resistances/weaknesses. Keep encounter levels, original unlock gates and shared HP/break budgets. Christine keeps her tested speed, durability and Slumber Mist; Blizzard/Freezing Spike receive the requested extra potency. See [the balance table](docs/SEPHIRA_CHALLENGE_BALANCE.md).
- Replace unsupported vision enemy drops with a win-only native item event, using the ordinary item dispatcher without an acquisition sequence, fade, camera or map transition. Preserve ordinary field return and empty escape/loss rewards. The user confirms the prior return no longer goes black; the new item grant still needs a live retest.
- Restore Fina’s movie soundtrack as one stereo ADX stream, correcting metadata field types to match original movie headers and both native stereo descriptors. Keep the approved color/opacity packets unchanged, preserve once-only playback and battle-music pause/resume, and retain the same score on cached installs. Stop with an actionable error instead of silently building a muted movie if soundtrack preparation fails. Offline encoding/readback does not establish live playback; in-game audio still needs a listen.
- Retain all 1.2.86 default-model naming and Windows voice extraction fixes, and preserve the existing sprite/icon cache.

Validation: 700 Python tests pass locally (41 platform skips), 68 targeted Flutter tests pass (one Windows-only local
skip), and analysis reports no issues. Real native readback passes for the challenge tables, all 28 AI assets, 45 menus
and cave placement. Native stereo descriptors and ADX metadata match; every approved color/opacity packet is unchanged.
With the score already encoded, the native movie stage took 18.0 seconds cold and 0.05 seconds warm, with identical
output and the same score. This measures that stage only, not soundtrack preparation or a complete install. Windows validation and compilation both pass for this
commit; the downloaded ZIP matches all 72 managed extension and 16 standalone Fina manifest files and its checksum.
No animation-library download is included. Keep Studio Test Data, update, rebuild/install and restart. No preset reset
or Prepare Game is required. Live reward delivery, return-to-field behavior, fight difficulty and movie sound still
need testing in the game; serialized asset checks cannot establish those outcomes.

First complete candidate 23:46:35 UTC to this verified ZIP 00:32:46 UTC:
**46m 11s**, including the intermediate 1.2.86 delivery, user-requested follow-up scope, local corrections, native
proofs, Windows waiting and ZIP verification. This package's CI wall time **9m 56s**; summed runner usage
**14m 01s**. The earlier 1.2.86 run used 10m 02s wall and 13m 53s runner time. Two exact automatic runs joined
across the task; no duplicate/manual dispatch.

## Published default model naming and Windows voice extraction — 2026-10-24

[Verified Windows ZIP / run 40144253062](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40144253062/Sephira-Studio-Test.zip), code `45c4f64`, update **1.2.86** (74.0 MB).
SHA-256 `ba8cc457d0b80b5f00091feaa454f5520e35efda00b983d70ebc84a8b94e3fb6`.

- Fix the 1.2.85 regression that rejected ordinary default-vision model replacements with “The selected model has no name.” Pass the selected catalog name alongside the appearance-only model response, preserving automatic naming, the native kit and independently selected voice. Bundled Crystal Fina and ordinary Add unit keep their existing paths.
- Normalize native voice extraction filters to forward-slash package paths and remove the content prefix after normalization. Windows paths previously extracted zero sound tracks and caused the “Expected either native voice cues or one movie voice track” error. Fetch missing sound tracks when only a resonance master is cached.
- Add full-picker regressions for hosted and engine catalogs, plus Windows filter and uncached-track discovery checks. Keep existing sprite/icon reuse and voice/audio generation unchanged. Live voice playback still needs testing after a successful install.

Validation: 698 Python tests pass locally (41 platform skips), 97 targeted Flutter tests pass (one Windows-only local
skip), and analysis reports no issues. The exact commit passes full Windows validation and compilation, including fresh
frozen-engine setup, launcher/updater and extension checks. The downloaded ZIP matches all 72 managed extension and 16
standalone Fina manifest files. No animation-library download is included. Keep Studio Test Data, update, rebuild/install
and restart; no preset reset or Prepare Game is needed.

The user now confirms Christine returns without a black screen, but reports no vision reward and continued silence in
Fina's movie. Reward, battle balance and movie audio work continue in the next update; this package fixes model selection
and the Windows voice-build error.

First complete candidate 23:46:35 UTC to verified ZIP 00:04:04 UTC:
**17m 29s**, including local checks, Windows waiting and verification. CI wall time **10m 02s**; summed runner
usage **13m 53s**. One matching automatic run joined, with no manual dispatch.

## Published vision battle rewards, transferable MR and native voices — 2026-10-24

[Verified Windows test ZIP / run 40141095549](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40141095549/Sephira-Studio-Test.zip), code
[`5dfd847`](https://github.com/biscoBen/FFR-Vison-Studio/commit/5dfd847336617498e2fc8d2d246a88f83d6584a7), update **1.2.85**
(**74.0 MB**; host compatibility version/build unchanged). SHA-256
`68b97dfdd51ae4c10a9e9302d608273b763fbea82c4bbc02d2a33bcb00c489b0`.

- Default visions can use any other default vision’s resonance voice, including movie-only voices. Original effects and movie pictures stay intact; prepared voice data is cached using short filenames suitable for portable Windows paths. These routes require an in-game listening test; longer recordings can be cut short by the target resonance’s unchanged timing.
- Add a backed-up **Reset all visions** action to Default visions, restoring their original names/models and other overrides while keeping added visions, Sephira’s collection and party settings. Changing a default vision’s model now uses that model’s name; reverting its model restores the original name.
- Swap Rikku and Lunafreya’s normal acquisition groups: Rikku joins Eiko at Zidane’s crystal, and Lunafreya joins Elephim at Vaan’s crystal. Preserve both original-vision prerequisite gates, encounter levels and combined boss budgets. Migrate saved default locations once while retaining shop/custom overrides and later deliberate edits.
- Swap eight command/LB-bound MR passives on Christine, Barusa, Minfilia, Trance Terra and Nalu with their existing general awakening bonuses. Christine now learns transferable Fill LB on Stagger at MR7; True Stagger stays in her final awakening tier and names her own skills. Preserve every passive, all 131 excluded-original bonuses, native AP costs and kit power. Back up saved stock rosters before repairing them, retain deliberate MR edits, and apply the same rule during builds. Rebind the two named active-skill slots on Nalu’s Signature Moves and Trance Terra’s Play Rough to their private skills as well as their resonance; the original game’s rows remain unchanged.
- Keep Christine's level-5 HP (2,750) and break gauge (162), increase her magic stat by 50% and speed by 15% (rounded to the game's integer stat). Blizzard replaces her basic weapon attack. Ice damage is halved and Fire is a weakness; Slumber Mist's native 30% Sleep effect is unchanged.
- Give the simpler difficulty AI the same bounded offensive and utility choices as the scripted rotation, excluding heals that require the scripted low-HP guard. Other challenges keep their existing stats and skills.
- Play Fina's cave music directly through the original game's Atom cue from its beginning, with no embedded movie audio or re-encoding. Preserve the approved video, opacity, single playback and battle-music pause/resume. The returned ADX decodes cleanly offline, but the user heard garbling through Mana; native Atom playback still requires an in-game listening test.
- Make each challenge vision a guaranteed normal battle drop from its private boss. Remove the extra post-victory acquisition event/sequence, allowing the standard result and field-return flow to handle the reward. Quest/ownership checks still guard entry, and visions cannot be stolen. The new trace showed the field loaded, the camera targeting the player and the acquisition sequence finished during the black screen; the revised normal return still needs an in-game test. No camera or progression reset is applied.

- Preserve all 30 existing sprite/icon cache keys for mastery and acquisition-only changes. Motion or image changes
  still invalidate their dependent conversions. Native voice artifacts use separate content-verified reuse, flattened
  filenames and short cache keys, with recovery after a damaged cached file/manifest.
- Local validation: the 695-test Python suite passed (41 platform skips), followed by all eight focused native-voice/cache
  checks after the portable-path correction. All 93 targeted Flutter tests pass (one additional Windows-only local skip);
  Flutter analysis reports no issues. Final Windows validation and compilation both passed for this exact commit,
  including the full Flutter/Python suites, fresh frozen-engine setup, launcher/updater and extension checks.
- Native proofs read back all challenge reward/AI tables and the actual Mitra crystal placement, eight effect rows and
  26 private passive rows. The supplied voice reference verifies all four separate-cue/movie conversion routes,
  original ADX packet preservation, generated HCA cues and native asset readback. The small source export deliberately
  omits most movie pictures; full generated color/opacity packets are checked byte-for-byte during transplantation.
  The downloaded ZIP's 72 managed extension files and 16 standalone Fina files match their manifests; the optional
  animation library is excluded. Live battle exits, music playback and representative voice swaps still need testing.

Keep **Studio Test Data**, update, rebuild/install and restart the game. No Prepare Game or preset reset is required.
Stock MR/acquisition repairs save backups and preserve deliberate custom acquisition choices. Under **Default visions**,
click a vision and choose **Change voice**; **Original voice** restores its original audio. **Reset all visions** removes
all default overrides, including voices and models, while keeping added visions, Sephira's collection and party edits.

First complete candidate **21:07:56 UTC** to verified downloaded ZIP **23:14:21 UTC**:
**2h 06m 25s**, including local corrections, native source investigation, user-requested scope additions,
Windows waiting and actual ZIP verification. Final CI wall time **09m 52s**; final summed runner
usage **13m 58s**. Four automatic code runs were joined; none was manually dispatched.
Their total runner usage was **55m 54s**:
`40133219367` (success, 10m 25s wall / 13m 46s runner);
`40133998997` (success, 11m 13s wall / 15m 05s runner);
`40140616346` (cancelled, 08m 36s wall / 13m 05s runner);
`40141095549` (success, 09m 52s wall / 13m 58s runner).

## Published actual Mitra cave placement and native movie music — 2026-10-24

[Verified Windows test ZIP / run 40129779990](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40129779990/Sephira-Studio-Test.zip),
code [`57f558a`](https://github.com/biscoBen/FFR-Vison-Studio/commit/57f558ae60c0c404c79c54f89b09a4c01dded535),
update **1.2.82**; 73,975,170 bytes. SHA-256
`2876f6b0552a4415ad2f7aeb58030d9d330d1c571fb55a0242ed1695426af1dd`.

- Use the three returned F8 bookmarks to identify the cave behind Rain's house as part of Mitra's `Town_01Gra_20_PL`, rather than the separate `Dng_01Gra_44` cave. Place Christine's crystal at the native tutorial portal position (6610, 52639, -705.02), retaining original streams, story gates and the level-5 fight. Preserve the shop practice stage when enabled.
- Select the captured `BGM_PP_EVENT_VISIONS_INST` recording (stream 51), starting at its beginning. The earlier CAVE1/stream-56 choice was a different track. Include the cue/stream in the local preview cache identity so old audio is not reused.
- Pass the ADX encoder's DLL explicitly and resolve its optional default inside the script body. The returned Windows probe confirms the default parameter failed because `$PSScriptRoot` was empty; the explicit-DLL probe succeeds. Preserve readable encoder error details.
- Show update **1.2.82**. Keep all 30 sprite cache keys and the reviewed movie's video/alpha packets. The returned 1.2.81 install measured 136.3s, with all 30 sprite/icon sets reused in 6.1s; no complete sub-two-minute repeat-install result is claimed.



Evidence: F8 at cave entry places the player at (-1000, 52650, 102.15); the intended crystal spot at
(6388.09, 52650, -740.87). Both belong to Mitra's persistent world and play `BGM_PP_EVENT_VISIONS_INST`.
The original tutorial portal is `BP_MapGimmick_BlockObject012_C_1` at (6610, 52639, -705.02), visible only
at main progress 1080. The custom challenge retains its original-vision/progress-1090 prerequisite.
The third bookmark confirms battle BGM pauses during the CG and resumes before the sprite LB; the generated
movie had no audio track because Windows encoding failed. No further playback-state workaround is needed.

Validation: **684** Python tests pass locally (41 platform skips), plus **31** focused Flutter tests.
The full Windows suites, real frozen-engine setup, both Windows PowerShell ADX encoder cases, launcher/updater
and compilation pass for this commit. Actual Mitra map serialization/readback and IoStore packing pass;
native actors and streams remain unchanged. The user's successful Windows-encoded track muxes with all
192 color and 192 opacity packets unchanged. Native movie cold/reused outputs match (18.137s / 0.059s).
Verify the downloaded ZIP's **70** managed extension files, **16** standalone Fina files and compiled **1.2.82**
label against source; retain all 30 kits, 131-passive coverage, original LB audio and the approved movie pictures.
No full FFBE library or original cave recording is bundled; music is read locally from the selected game.

Keep **Studio Test Data**, update, rebuild/install and restart Resonance. Leave Christine on her normal route;
use the individual Mitra override for Fina if needed. No Prepare Game, new save, preset reset or new diagnostic
observer is required. The first corrected build changes the room/stage assets and fills the new audio cache.
Live crystal interaction, movie listening and a subsequent unchanged install still need the user's test.

First complete candidate **20:23:28 UTC** to verified downloaded ZIP **20:37:03 UTC**: **13m 35s**, including local
checks, native readback, publication transport correction, Windows waiting and actual ZIP verification.
One candidate / one reused automatic Windows run. CI wall time **9m 51s**; summed runner usage **13m 57s**.
Normal repository push and public read-only API/download transport completed publication; the unchanged build
helper still verifies exact workflow/commit/input provenance and the download checksum. No workflow was dispatched.

## Published warm-install reuse, persistent Christine unlock and visible update number — 2026-10-24

[Verified Windows test ZIP / run 40124402761](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40124402761/Sephira-Studio-Test.zip),
code [`8394aae`](https://github.com/biscoBen/FFR-Vison-Studio/commit/8394aae4fc139f34ccaf49314f87f88f18d927ca),
update **1.2.81**; 73,974,837 bytes. SHA-256
`0ba9cb222a8e796f631afb033e4bc78241180f178272b2c85d4aa6ba9d38f7f5`.

- Keep unchanged sprite/icon sets reusable across cave placement and balance edits, including existing 1.2.80 cache entries. Skip per-asset recipe writes and repeated indexing/copying on verified whole-table cache hits; changed packages and corrupted entries still rebuild.
- Use permanent story progress or original Tronn ownership for Christine's secret-cave crystal. The earlier flag is cleared by the following story event; visibility and interaction now use the same persistent condition. Keep the level-5 fight and original map actors.
- Explicitly resetting Sephira presets also restores their default acquisition locations, with previous edits retained in the reset backup. Normal updates continue to preserve custom acquisition choices.
- Show test update **1.2.81** in Studio's main window and About, and record the installed update version in build logs/profiles. Host compatibility remains version 1.0.0/build 15.
- Remove the unbundled `wave` import behind Fina's bare audio-preview server error. Cache a short original cave recording from the installed game and mux it locally into her unchanged movie using the previously working stereo ADX layout. Broaden private-movie detection for pausing/resuming the current battle BGM handle and log detector startup/source matching. Live cave visibility and soundtrack playback remain user tests.


The returned profile measured **225.5s**, including **115.9s** rebuilding raw sprite/icon sets despite native conversion
cache hits, **40.1s** for the first table patch, **10.0s** verification and **10.4s** installation/runtime work. The raw
sets were invalidated by a cave-only source edit. Audit the motion dependency and retain its existing 1.2.80 key when
unchanged. Whole-patch hits no longer write 1,343 throwaway recipes or restore/copy every package a second time.

Validation: **682** local Python tests pass (41 platform skips), **56** focused Flutter tests and analysis pass.
Windows full suites, actual frozen-engine import/PCM trimming, fresh setup, launcher/updater and compilation pass for
this commit. Native map readback and IoStore packing pass. A real 344-skill table/shop patch measures 7.129s cold /
0.010s unchanged / 0.886s shop-only; the scored movie wrapper measures 17.903s / 0.060s reused. Cold/reused native outputs
match; independent metadata parsing and companion-pak extraction preserve every color/alpha packet and the exact ADX
stream. These component measurements do not establish a complete sub-two-minute install on the user's PC.

Verify the actual downloaded ZIP: **70** managed extension files and **16** standalone Fina files match source,
the compiled app contains the **1.2.81** label, and all 30 kits, 131-passive coverage, elemental impacts and approved
movie artwork/audio archives remain intact. The optional full FFBE library and original cave recording are excluded.
The short cave recording is read and encoded locally only when the cinematic is enabled or previewed.

Keep **Studio Test Data**, update, rebuild/install and restart Resonance. No Prepare Game is required. Keep Christine
on her normal acquisition route and override only Fina to the shop when testing both. Explicit **Reset all presets**
now restores acquisition defaults too; it is optional and keeps a backup. Live crystal appearance/interaction, movie
sound and battle-music pause/resume and the next warm install timing still require the user's test.

Measured first complete candidate **19:12:41 UTC** to verified downloaded package **19:25:39 UTC**: **12m 58s**, including
local checks, Windows waiting and actual ZIP verification. One candidate and one reused automatic Windows run;
CI wall time **10m 37s**, summed runner usage **14m 48s**. No second build was dispatched.

## Published individual table reuse, Fina presentation caching and Christine crystal — 2026-10-24

[Verified Windows test ZIP / run 40120000643](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40120000643/Sephira-Studio-Test.zip),
code [`23dfd43`](https://github.com/biscoBen/FFR-Vison-Studio/commit/23dfd4381a15a6c46075df714fd69464c3be6147),
extension **1.2.80**; 73,965,605 bytes. SHA-256
`e0de0ee78608d2aa2efba98dcc4e1f42aa849317a0eea29cd98075f57257cce0`.

- Use the returned 405.2-second install profile to target repeated generation and reads: generation 335.0s,
  verification 54.6s, installation 14.3s; packing was only 2.3s. Preserve existing sprite/menu cache entries.
- Reuse unchanged native packages individually when the main patch changes; batch only dirty packages in one native
  invocation. Keep complete clean builds, input/corruption checks, verification and installation rollback.
- Cache Fina's complete verified body/crystal/glow/runtime presentation and movie wrapper, avoiding repeated large
  native-model JSON reads and signature churn. Build/verifier CLI processes share immutable decoded native tables;
  editor reads remain live and every new CLI invocation gets a fresh snapshot. Bind Fina's current table rows separately
  so an unrelated vision's challenge/stat changes do not recook her body or restore stale rows.
- Native component checks: Fina presentation 83.018s cold / 0.036s reused, movie wrapper 20.153s / 0.063s;
  the 344-skill table plus shop patch 6.556s cold / 0.014s unchanged / 0.844s for a shop-only change. Thirty-vision
  recipe/source reads 23.111s / 1.994s with identical recipes. These executor timings do not establish a complete
  sub-two-minute Windows install; the first build fills the new group caches.
- Place Christine's crystal and input interaction in the secret cave's persistent world at the original teleporter
  position (5260, -45, 75). Reuse native completion flag 147 for visibility/interaction, attach the mesh to its owner,
  and remove the old map's baked culling ID. Preserve native streams, actors, story gates and the level-5 fight.
- Optional Fina browser audio now reports its actual failure instead of an unhelpful internal-server-error page.
  During Fina's private movie only, pause the current native BGM playback handle and resume it when the movie
  ends or is interrupted. Preserve user/category volumes and other sounds. This runtime control needs live testing.
  Cave music is still reported silent in game; no successful soundtrack playback fix is claimed in this update.
  Crystal visibility/interaction on the user's save and full install time still require live testing.

Validation: 674 local Python tests (41 platform skips) and 282 local Flutter tests pass. Windows validation,
fresh frozen-engine setup, full Flutter/Python suites, launcher/updater checks and compilation pass for the same
commit. Native readback and IoStore packing pass for the persistent cave; cold/reused Fina and movie outputs match.
An unrelated native design-row edit preserves the body and takes 6.847s to rebind current tables. The downloaded
ZIP's 69 managed extension and 16 standalone Fina files match the source manifests; all 30 kits, mastery coverage,
approved movie and audio archives are preserved. The full optional FFBE library remains excluded.

Keep **Studio Test Data**, update, rebuild/install and restart Resonance. No Prepare Game or kit reset is required.
The original completed-story flag enables Christine on existing saves. Select only Fina in the optional shop override,
or leave Fina's existing Mitra acquisition choice; keep Christine on her normal acquisition route.

Measured first-complete-candidate to verified-package delivery: **30m 02.3s**, from 2026-10-24 17:57:59.634 UTC to
18:28:01.960 UTC, including checks, the installer-declaration correction, the final dependency split, extra builds,
waiting and actual ZIP verification. Final CI wall time **10m 08s**; final runner usage **13m 10s**. All three candidate
runs used **37m 07s** of runner time: `40118699183` failed (348s wall/546s runner), `40119362623` passed
(618s/891s), and final `40120000643` passed (608s/790s). The build helper reused the final automatic run and
its authenticated test-release download; it dispatched no duplicate workflow. This publication-note commit changes
only README/CHANGELOG and does not relabel the binary or request another build.

## Published timed builds, batched menus and Christine level-5 trial — 2026-10-24

- Address the user's **908.2-second failed install** without treating that duration as a cache benchmark. The pasted
  tail contains 54 menus built with four native operations each after sprites, while Studio still labels the stage
  “Lunera, 30 of 30.” There are no prior per-stage timestamps, so the full 15 minutes cannot be accurately apportioned.
- Timestamp every captured console/saved-log line with local time and elapsed build time. Stream verification output
  as it arrives; time verification and installation. Add accurate post-sprite stages, per-operation duration/status,
  cache hit/new/invalid lookup records, phase totals and slowest-operation summaries. Save unique `build-profile-*.json`
  and `build-events-*.jsonl` files in **Logs folder**, including failed builds. Keep completed cached work after a failure.
- Reproduce the exact Christine schema failure with native Blueprint packages available: the cave's existing actors
  decode normally but lose their schema context on JSON write. Collect all actual actor declarations into private
  mappings; preserve the installed mappings and original actors. Check the cave write before sprite conversion and
  reuse that verified result later in the same build.
- Batch native menu cloning from one authored template, assign consistent distinct signatures per menu, verify every
  cooked dialog and cache the whole group. Native 45-menu comparison: **149.386s / 180 tool launches before**, **44.433s /
  50 launches after**, **0.020s / zero launches on reuse**. These local component timings do not establish the Windows
  full-install two-minute target. Keep the existing asset-cache implementation/namespace so prior completed work remains usable.
- Tune Christine's fixed challenge to **level 5**, using the existing native boss curve (2,750 HP), her ice kit and
  generic attack. Review each later challenge against the user's party level and battle experience when they reach it.
  Native cave readback, menu bindings/signatures and fixed-level budget checks are included; live battle balance remains a user test.


- **Verified Windows test package:** code `c63c8e98f613a66646c2ca339e068c0593ea4e6a`, extension **1.2.79**,
  [run 40114191529](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/40114191529),
  [download](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40114191529/Sephira-Studio-Test.zip),
  **73,960,090 bytes**, SHA-256 `fda88d7cc31a43fae1933d3e7fa3baa76db5ec6000a7ad681838207bfb5a4fa9`.
  Full Windows analysis/Flutter tests, frozen-engine setup, Python checks, bundle checks, launcher/updater checks and
  compilation pass. Verify downloaded provenance and all **68** extension files plus **16** standalone Fina files.
  Confirm the delivered native asset-cache helper is byte-identical to 1.2.78, preserving completed cache entries.
- Windows validation caught open profile handles at normal builder return and a timestamp test using an unsupported
  epoch-era local date. Close profiles at normal return with an exit fallback; use a modern date in the clock test.
  Correct the follow-up test's indentation/module scope and explicitly check profiles are closed before temporary-file
  cleanup. Final validation passes; no failed candidate was published as this release.
- First complete candidate **16:38:08 UTC**, verified delivery **17:11:48 UTC**, 2026-10-24: **33m 40s**, including
  local checks, later level-5 request, Windows corrections, an extra retry, waiting, download and verification.
  Successful CI **9m 57s wall**, **13m 47s summed job time**. Earlier automatic run 40113152061 failed validation;
  the helper dispatched protected manual retry 40113776471 after that failure. Automatic 40114032519 was superseded
  and cancelled, and the corrected commit reused automatic run 40114191529. At delivery, measured job time across
  these attempts was **49m 13s**, including **16m 52s** elapsed on the still-running protected retry; this is a snapshot
  lower bound, not final/billed usage. Do not equate CI/delivery timing with PC installation time.

## Published faster repeat installs, selected shop visions and cave/movie corrections — 2026-10-24

- Reuse verified unchanged sprites/icons, authored timelines, audio banks and native serialization/decoding results;
  rebuild a clean asset folder so removed units cannot linger. Fingerprints track source art, motion/layout,
  mappings, relevant generator code, native writer and game identity. Corrupt entries regenerate; cache is bounded
  to 4 GiB. Skip unchanged installed package copies and identical-package backups, retaining complete rollback sets
  for changed packages. Keep all row verification and game/runtime ownership checks. Log total build/install time.
- Add a per-vision 1-gil shop selection. Fina can be sold in Mitra while Christine retains her normal cave battle;
  toggling off restores saved locations and retains the selection. Existing all-vision settings stay compatible.
- Respond to the confirmed missing crystal after restart/re-entry by placing Christine's crystal and interaction
  directly in the existing cave gimmick level; retain original story actors/import/name indices and exits.
- Fix the definite silent-music cause: the native movie master's Sound_001 parent track is disabled. Put the cave
  Atom soundtrack in its active Effect_000 subtree, retaining the working single-play compiled timing and sprite/cure
  handoff. Browser playback reads and locally caches the installed cave recording without adding game music to updates.
- Local 30-unit raw sprite conversion experiment: **36.073 s cold → 1.147 s warm**, all 30 reused. This excludes native
  cooking/icons, packing, verification and installation; it is not an end-to-end Windows sub-two-minute claim.
  Native cave/movie readback, parent-track regression, decoder/bounds and cache invalidation checks are included.
  Actual cave interaction, browser soundtrack extraction and in-battle music still require the user's live test.
  See [reuse details](docs/INCREMENTAL_BUILDS.md).


- **Verified Windows test package:** code `2047475e6facd0341278f2eb99a71a79c8fd32a4`, extension **1.2.78**,
  [run 40080356282](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/40080356282),
  [download](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40080356282/Sephira-Studio-Test.zip),
  **73,954,238 bytes**, SHA-256 `16884275a5d0ac2ff224905419622434f3db31e5eeb411de623dcb70e222e408`.
  Full Windows Flutter analysis/tests, frozen-engine startup, Python checks, bundle verification, launcher/updater
  checks and compilation pass for this commit. The actual downloaded ZIP's provenance and all **67** managed
  extension files plus **16** standalone Fina files match; the optional full animation library remains excluded.
- First complete candidate **08:58:56 UTC**, verified delivery **09:12:48 UTC** on 2026-10-24: **13m 52s**,
  including local checks/corrections, build waiting, download and verification. One automatic push run was reused;
  no duplicate manual build. Measured CI wall time (first job to final job) **9m 56s**; summed runner time **14m 15s**
  (plan 38s, compile 4m 25s, validation 7m 48s, Windows packaging 38s, test publication 46s).
  No prior task duration or end-to-end PC install time is inferred from these delivery measurements.

## Published cave soundtrack, Christine crystal and Sephira descriptions — 2026-10-23

Code [`0dd3c68`](https://github.com/biscoBen/FFR-Vison-Studio/commit/0dd3c680c4d5eaa60cb479a3fb7ed3fd9215ca8e),
extension **1.2.77**, [Windows test ZIP / run 40048368217](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40048368217/Sephira-Studio-Test.zip).
The verified ZIP is **73,827,639 bytes**, SHA-256
`aa23fc7956356c18c5b8cc2bef449ce07cad6e31e8bc192a8d86861d908d31bf`.

- Use the secret cave's original `BGM_PP_DUNGEON_CAVE1` recording from its
  beginning during Fina's 6.4-second intro. A private native Atom cue/track reads
  the installed `BGM_PP` sheet and streamed audio; no game music is copied or
  reencoded. Remove the discarded piano/organ score and all embedded Mana audio.
  Keep every approved video/opacity picture, single-play cooked movie timing,
  sprite animation, opening/build-up and healing/cure marker. The browser preview
  is picture-only because the original music stays in the installed game.
- Put a visible blue crystal in the wider end of the secret cave behind Rain's
  house, `01Gra_44`, using the returned cave geometry. Talking to it opens the
  guarded level-2 Christine challenge. Preserve the native cave's original story
  actors, navigation, lighting, exits and every existing stream; append one
  private always-loaded interaction/crystal stream. Remove the failed startup
  prompt. The crystal stays visible after acquisition and reports ownership.
  Tronn/the original story completion is still required, and only victory grants
  Christine once. The 1-gil shop override still suppresses the normal challenge.
- Shorten 313 authored ability descriptions across all 30 Sephira visions and
  rewrite all 30 resonances in native English style, describing effects instead
  of borrowed characters or animation sources. Remove repeated MP, accuracy,
  stagger and raw power listings while retaining useful effects and targets.
  Apply the same Crystal Renewal/resonance text to independent bundled Fina.
- Automatically back up and repair matching old generated text when Studio opens.
  Preserve custom descriptions and all combat, learned reward, artwork, identity,
  acquisition and audio settings. No MR/kit reset or Prepare Game run is needed.
- Extension 1.2.77. Native write/readback and IoStore packing pass for the movie,
  single native music cue, cave map and physical interaction. All 66 Sephira
  regressions, 29 existing-vision checks and 14 cinematic checks pass; Flutter
  analysis and 55 focused Flutter checks pass (one Windows-only local skip).
  Actual crystal visibility/interaction, cave music playback/mixing and movie
  handoff still require the user's in-game test. Windows/package verification
  passed for this exact commit, including frozen-engine startup and launcher/
  updater checks. The downloaded package matches all 64 extension files, all 16
  independent Fina files, the catalog and approved movie hashes.

### Measured delivery and CI

The first complete soundtrack candidate finished **2026-10-23 17:10:31 America/Los_Angeles**.
The final combined download was verified at **18:16:36**: **66 minutes 5 seconds** elapsed.
This includes the earlier soundtrack work, user steering/reference collection, corrections,
local checks, two stopped superseded runs, final CI and actual download verification; the clock
was not restarted. The final run reused the matching automatic push build, without a duplicate dispatch.

Final CI wall time was **7 minutes 56 seconds**. Measured Windows job time was **9 minutes
38 seconds** in parallel: compile **4:01**, validation **5:37**. Linux plan/aggregation/publication
used **2:10**. Across all three runs, including cancelled runs **40044171680** and **40044741999**,
the totals were **30:42 Windows** and **5:15 Linux** job time. These are elapsed job timestamps,
not billed or weighted runner minutes. Neither superseded piano run published a package.

## Published Fina movie timing/audio, install verification and Christine challenge — 2026-10-23

Code [`cc2b9ec`](https://github.com/biscoBen/FFR-Vison-Studio/commit/cc2b9ec632bcb188a782a88a29a5fa70f16dfb67),
extension **1.2.75**, [Windows test ZIP / run 40038819889](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40038819889/Sephira-Studio-Test.zip).
The verified ZIP is **74,251,661 bytes**, SHA-256
`b7313d5952801c86b0d106838fcdb8cb7b4b972febc754ddb86be447034e50aa`.

### Crystal Fina movie timing/audio, install verification and Christine challenge

- Fix the install-blocking Lasswell table error when a party voice override is
  combined with **Survive at 1 HP**. Merge authorized changes by field instead
  of replacing a row's expected voice edit with its survival edit. Verify the
  complete composed row while still requiring the exact saved voice and rejecting
  unrelated stat/identity changes or incorrect/missing survival passives.
- Check party voice parameters before sprite conversion and sequence generation,
  using the same expected edits as the final verifier. Errors name the character
  and mismatched fields. Keep the selected voice, survival mechanics and all
  appearances; no game reinstall or disabling those settings is needed after updating.
- Move Christine's normal challenge to the **secret cave behind Rain's house in
  Grandshelt**, on the path to Tronn/Leah, as requested. Entering it offers the
  level-2 challenge after obtaining Tronn (or the original completion flag),
  with a Leave/cancel option. Winning grants her once; the entry prompt stops
  after acquisition. Preserve original startup events, story grants and flags.
  Use an instance-loaded copy of the room's native battle stage. Stop changing
  the blocked Tronn crystal-room interaction. The 1-gil shop override and removed
  or moved profiles suppress the challenge as before; no MR/kit update is needed.
- Retain the now-visible 1080p Fina movie and its native opacity track. Shorten the
  cooked Mana/evaluation-tree endpoints as well as typed section/spawn ranges:
  fresh signatures alone had left the donor's longer playback window active.
  Preserve every other compiled byte and reject unknown templates by SHA-256.
  The target is one 6.4-second pass followed by the existing sprite LB.
- Put the exact matching original score directly in the movie as mono 48-kHz HCA,
  with sample-based packet timing and matching native movie descriptors. Remove
  the separate hit-sound score event so it cannot be gated during the cinematic
  or double the soundtrack. Keep the selected MP4/artwork unchanged, and retain
  sprite/heal/cure timing. The user confirms only movie sound is missing; the
  battle theme and sprite/healing sounds already work.
- Extension 1.2.75. Local regressions cover all eight party targets with survival
  on/off and both verifier paths; native readback reproduces the returned log's
  643-row table and 11 survival targets. Native write/readback verifies 19
  Christine challenge tables, preserving original startup/story/map fields.
  Fina's native sequence readback verifies cooked/typed bounds, opaque bindings,
  mono HCA descriptors, unchanged sprite/heal cues and successful retoc cooking;
  movie packets recover the exact score. All 96 focused Python checks and 41
  Flutter checks pass (one Windows-only local skip). Full Windows validation, compilation, frozen-engine setup, Python, launcher/updater
  and downloaded-package checks also pass. Live Christine entry/menu/battle and
  Fina's single-pass handoff/movie audio remain game tests.

Close Studio/game, update while keeping **Studio Test Data**, rebuild/install and
restart Resonance. Keep **Test Crystal Fina cinematic** enabled for this test.
Check one movie with its score followed by the sprite LB, then test another battle.
No MR/kit reset is needed. To use Christine's normal challenge, disable
**Sephira visions: 1-gil Mitra shop** and enter the secret cave behind Rain's house
after obtaining Tronn. Winning grants Christine once; Leave/cancel grants nothing.

The downloaded Windows app matches all **63 existing-vision** and **16 Fina** manifest
files, extension version, coupled installer hooks, exact selected MP4 and new movie
SHA-256 `60eb3c5866361c9eec901e80cb6213d22705183edf3eeb7de42721c7ef124581`.
It retains the prior 30-profile LB audio package, all 131 covered original MR passives,
150 distinct MR slots and 160 awakening balance grants. The optional full FFBE library
is excluded. Native sequence/descriptor/package checks and exact HCA/PCM recovery
pass; these do not establish the new handoff or audible score inside Resonance.

Measured delivery (America/Los_Angeles, PDT): first complete install-verifier candidate
**15:44:53**, combined movie candidate **16:17:12**, package verified **16:28:47**,
verified download link delivered **16:29:13**. Candidate to delivery is **44m 20s**
(**43m 54.9s** to package verification). The original clock includes Christine's requested
relocation, the later movie repeat/audio report, native serialization corrections,
local checks, both builds, waiting and downloaded-package verification.

Both automatic push runs passed and were reused; no duplicate workflow was dispatched.
Intermediate `910e4de` / run **40036836130** took **10m 32s** CI wall time,
**12m 04s Windows runner time** and **2m 35s Linux runner time**.
Final `cc2b9ec` / run **40038819889** took **10m 41s** CI wall time,
**12m 20s Windows runner time** and **2m 11s Linux runner time**.
Across the two code builds, measured runner usage is **24m 24s Windows** plus
**4m 46s Linux**; their summed CI wall time is **21m 13s**, separate from elapsed delivery.
Publication-note commits touch only README/CHANGELOG and request no new binary.

## Published Crystal Fina movie opacity test — 2026-10-23

Code: [`d37d3b8`](https://github.com/biscoBen/FFR-Vison-Studio/commit/d37d3b85fe859fe814303471e27c34491b63a01f), extension **1.2.73**.
Windows package: [run 40031404397](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40031404397/Sephira-Studio-Test.zip).
**74,090,982 bytes** (74.1 MB).
SHA-256: `f2fe99a8f5c7354b8781a977602ac78336d353fab5384f9aa70f494685ae47f8`.

- Address the returned test where battle UI hides but the movie remains invisible.
  The earlier runtime trace shows the correct movie decoding with the cinematic
  manager enabled. The native battle material samples a separate opacity texture;
  the previous private movie supplied no alpha channel.
- Add a native Sofdec full-opacity track to Fina's private VP9 movie, with one
  independently decodable opacity picture per color frame and matching timestamps
  and seek tables. Encode the selected movie at its original 1920×1080 resolution
  to match the native opacity pictures and battle texture. Keep the browser MP4
  byte-identical, and preserve its score, sprite LB, healing and cure-sound timing.
  Do not replace the shared movie player, texture, material or original movies.
- Extension 1.2.73. All 192 picture and opacity frames decode locally; opacity is
  full white throughout. Native readback confirms matching VP9/Sofdec track
  dimensions, frame rates and counts in both descriptors, the existing movie/spawn
  window and sprite/healing handoff, and the unchanged shared asset bindings.
  The companion pak survives retoc unchanged. All 53 focused Python checks and
  31 Flutter checks pass (one Windows-only local skip). This targets the likely
  opacity mismatch; visible playback still requires an in-game test.
- Full Windows validation, compilation, fresh frozen-engine startup, Python checks,
  bundled extension verification and shortcut/updater tests pass for this commit.
  The downloaded package matches all 63 managed-extension and 16 Fina files,
  executable provenance, selected preview and new color/opacity movie hashes.
  **Visible in-game playback and the live handoff remain unverified.**

Close Studio/game and update while keeping **Studio Test Data**. Include Crystal Fina,
enable **Test Crystal Fina cinematic**, rebuild/install and restart Resonance.
Expect one 6.4-second movie followed by her existing sprite LB; repeat in another battle.
No MR/acquisition update or kit reset is required.

First complete candidate: **15:04:56 PDT**.
The downloaded release was verified at **15:17:23 PDT**,
**12m 28s** later. Delivery was recorded at
**15:18:10 PDT**, **13m 15s** after the
candidate, including local checks, waiting, publication and download verification.
The matching automatic push run was reused; no duplicate build was dispatched.

| Workflow | Outcome | Measured CI wall time | Windows job time | Linux job time |
| --- | --- | --- | --- | --- |
| [40031404397](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/40031404397) | Passed | 10m 48s | 13m 59s | 2m 24s |

Job time sums overlapping jobs; it is separate from elapsed delivery time.

## Published Crystal Fina movie display and handoff test — 2026-10-23

Code: [`449fd0a`](https://github.com/biscoBen/FFR-Vison-Studio/commit/449fd0aab2e879ed83080701923ce8b260427220), extension **1.2.72**.
Windows package: [run 40024946811](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40024946811/Sephira-Studio-Test.zip).
**72,025,149 bytes** (72.0 MB).
SHA-256: `b70967454e968eb194b84a1e354f990015a2e8d5c98ee70dac4b175bb8e5b138`.

- Follow the native resonance movie's battle-UI transition, retaining movie visibility, then restore
  battle UI for Fina's existing sprite LB. The returned trace confirms her movie opens and advances
  frames with the cinematic manager enabled, despite staying invisible in the released test.
- Refresh the private movie/spawn evaluation signatures after shortening their ranges. The trace
  shows a second movie pass continuing during the sprite LB; the donor's longer evaluation cache
  survived the earlier range edits. Keep the exact selected movie/score and existing sprite LB,
  healing, reaction and cure-sound alignment. Align Studio's loader and startup checks with 1.2.72.
- Provide separate native-player reference and read-only runtime-observer downloads. The returned
  Windows collection successfully includes all nine requested native assets. The observer confirms
  decoding and distinguishes movie progress from the independent sprite animation. It is optional
  and does not automatically activate with the Studio update.
- Local checks: 52 focused Python checks and 31 Flutter checks pass (one Windows-only local skip).
  Native readback/package checks confirm all six refreshed signatures, the 2.0–8.4 second movie/spawn
  window, native UI transitions, preserved binding data and unchanged media. All Windows validation,
  compilation, frozen-engine startup, Python checks, shortcut/updater and publication checks pass.
- The downloaded package matches all 63 managed-extension files and 16 Fina files, executable
  provenance and the exact selected preview/USM hashes. **Visible playback and the corrected live
  handoff still need the user's game test.** No updated artwork or in-game success is claimed.

Close Studio/game and update while keeping **Studio Test Data**. Include Crystal Fina, enable
**Test Crystal Fina cinematic**, rebuild/install and restart Resonance. Expect one 6.4-second movie
followed by the existing sprite LB. No MR/acquisition update or kit reset is required.

First complete correction candidate: **14:01:10 PDT**. The downloaded release was verified at
**14:23:38 PDT**, **22m 29s** later, including local checks, the missed loader-version correction,
failed startup builds, waiting, publication and download verification. The helper automatically
retried the first failed commit before the corrected push; that protected manual run was retained
and also failed. The clock was not restarted after correcting the loader. These are separate from
the earlier artwork/selected-movie delivery timings recorded below.

| Workflow | Outcome | Measured CI wall time | Windows job time | Linux job time |
| --- | --- | ---: | ---: | ---: |
| 40023696526 | startup failure | 6m 23s | 8m 55s | 1m 16s |
| 40024507462 | automatic helper retry; startup failure | 6m 44s | 9m 32s | 1m 38s |
| 40024946811 | success | 9m 49s | 11m 39s | 2m 19s |

Summed measured job time: **35m 19s** (Windows **30m 06s**, Linux **5m 13s**), not billing.
Publication notes change README/CHANGELOG only; the verified binary remains commit `449fd0a`.

## Published selected Crystal Fina movie and playback correction — 2026-10-23

Code: [`58dac32`](https://github.com/biscoBen/FFR-Vison-Studio/commit/58dac32d01b7837aca53c67419262e7efeb59e77), extension **1.2.71**.
Windows package: [run 40014034193](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40014034193/Sephira-Studio-Test.zip).
**72,024,934 bytes** (72.0 MB).
SHA-256: `c7cfd38ead67cf41ba6f3f2745664eda5a8a271f2a4898d743980b4b75eaa073`.

- Use the user's selected `Crystal-Fina-Rotating-Lighter.mp4` for the optional cinematic test. Keep Studio's
  preview byte-identical to that 1080p file; encode the game copy at 720p/30 fps for the same 6.4 seconds.
  Retain its continuous crystal rotation, camera approach, red-eye ending and matching original score.
- Correct the companion-pak movie path to `Content/Streams/Movies/Studio`, matching the returned native
  game reference. Remove the obsolete owned staged movie on migration. Match native USM alignment,
  metadata byte counts, maximum chunk size, declared length and seek offsets without changing video packets.
- Preserve Fina's existing LB/heal behavior and audio offsets. Keep the test off by default; enabling it
  requires rebuilding/installing and restarting the game. Bump the managed extension to 1.2.71.
- Add a bounded, read-only movie diagnostic collector and developer import tool. Checksum-pin the exact
  selected preview and packaged stream. Alternate artwork remains local; no new frames are generated.
- Revision 1's blank movie is still awaiting an in-game retest. Native readback, package checks and full
  video decoding verify the candidate files; they do not prove playback inside Resonance.
- Local checks: 50 focused Python checks and 31 Flutter checks pass (one Windows-only local skip).
  Native readback, source-preview checksum, full VP9 decode and byte-identical USM/IVF roundtrip pass.

The delivered preview is byte-identical to the selected MP4 (SHA-256
`680e099c04a03f5e0e7206e2a2d5b8bb843613e218f7ee213d390b66a6b649c5`). Source name/hash, the normalized
VP9 movie, score and private movie path are verified in the downloaded package. All **63 managed extension
files / 16 Fina files**, existing 30 presets, optional-library exclusion and Windows executable provenance
match the approved commit. Full Windows app tests, analysis, frozen-engine startup, Python checks, shortcut,
updater, compilation and publication passed. Actual CRI playback remains unverified in Resonance.

First complete intact-crystal candidate: **2026-10-23 10:18 PDT** (minute precision). The exact selected-movie
candidate finished at **12:40:15 PDT**; the downloaded release was fully verified and shared at **12:57 PDT**
(verification completed **12:57:18 PDT**). This is approximately **2h 39m** from the first candidate, including
artwork review, corrections, local checks, the publication-approval pause, CI, waiting, download and verification;
the original clock is not restarted at the selected-movie import. Selected-candidate-to-verification time was
**17m 03s**. No in-game success is claimed.

The helper dispatched a manual build during a GitHub push-run discovery race. The duplicate automatic run
was cancelled before publication; the manual run was retained. Both runs' measured job times are included
below. The timing endpoint confirms wall durations but returns zero billable milliseconds, so runner usage
is reported as elapsed job time, not billing. Skipped/cancelled entries with inverted timestamps count as zero.
Publication notes change README/CHANGELOG only; they do not rebuild or relabel the verified binary.

| Workflow | Outcome | Measured CI wall time | Windows job time | Linux job time |
| --- | --- | ---: | ---: | ---: |
| 40014034193 | success | 10m 17s | 11m 44s | 2m 25s |
| 40014030142 | cancelled | 5m 59s | 2m 40s | 4m 30s |

Summed measured job time: **21m 19s** (Windows **14m 24s**, Linux **6m 55s**),
separate from the end-to-end verification time.

## Published Crystal Fina illustrated cinematic test — 2026-10-23

Code: [`aab0431`](https://github.com/biscoBen/FFR-Vison-Studio/commit/aab04319c58edb6ad4b6c6309fca38c0b06e4155), extension **1.2.70**.
Windows package: [run 39986827052](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39986827052/Sephira-Studio-Test.zip).
**63,464,413 bytes** (63.5 MB).
SHA-256: `b91a0e396143b573c6b005e64338868254dffaef2a71b1c39b6479289adb22a7`.

- Add an optional, default-off **Test Crystal Fina cinematic** switch and a read-only browser preview. The
  6.4-second illustrated intro uses the approved crystal refraction/light appearance, camera movement, healing
  glow and a glass release with an original synthesized score. It leads into her existing LB and cure sound.
- Keep Fina’s healing, reaction timing relative to her LB animation, kit, MR rewards and crystal presentation.
  Package the movie inside the normal three-file mod/snapshot; disabling and rebuilding removes the intro.
- Verify media decoding/demux, native movie/spawn descriptors, preserved compiled bindings, companion-pak
  transport and opt-out behavior. Native playback, synchronization, repeated battles and Steam Deck playback
  remain untested in game. See [the test instructions and limits](docs/CRYSTAL_FINA_CINEMATIC.md).

The approved source artwork is pinned by SHA-256 in the small media archive. The movie’s CRI container
recovers the exact fully decodable VP9 stream. Native writing/readback verifies 1280×720 / 30 fps / 192 frames,
the 2.0–8.4-second movie window, three sound banks, the existing cure/application alignment, private child
routes, inert donor battle events and byte-identical opaque compiled data. retoc packages the native assets
without changing the USM companion pak. The movie therefore uses the existing installer/snapshot transport.

Validation: **607 Python tests** (10 local platform/dependency skips), **279 Flutter passes** (one skip), clean
static analysis and all bundled manifests. Windows full validation, frozen-engine startup and compilation pass
for this exact commit. Download provenance, release SHA-256, **63 managed extension / 16 Fina files**, all
30 existing presets and the delivered movie/score archive are verified. The game itself has not been run here;
CRI decoder acceptance, UI restoration, synchronization and repeat playback remain user tests.

Close Studio/game, update while keeping **Studio Test Data**, enable **Test Crystal Fina cinematic**, then
rebuild/install and restart. The browser preview is included. No kit reset, mandatory game preparation or MR
update is introduced. Disabling the test and rebuilding returns to the normal LB. Other visions are unchanged.

First complete candidate: **2026-10-23 09:21:50 PDT**. Downloaded package fully verified at **09:35:55 PDT**:
**14m 05s** including local checks, corrections, CI, waiting, download and verification. The helper reused the
matching automatic push run and dispatched no additional build. Publication notes change only README/CHANGELOG;
they do not rebuild or relabel this binary. A separate preview upload was rejected by GitHub authentication;
the same MP4 remains included in Studio’s read-only preview.

| Workflow | Outcome | Measured CI wall time | Windows runner time | Linux runner time |
| --- | --- | ---: | ---: | ---: |
| 39986827052 | success | 8m 39s | 10m 30s | 2m 20s |

Summed runner usage: **12m 50s**, separate from elapsed verification/delivery time.

## Published Sephira awakening bonuses and requested LB audio — 2026-10-23

Code: [`3d295a6`](https://github.com/biscoBen/FFR-Vison-Studio/commit/3d295a6b2775874e8afe8d1a45e8d874957fbaac), extension **1.2.69**.
Windows package: [run 39921373217](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39921373217/Sephira-Studio-Test.zip). **58,671,798 bytes** (58.7 MB).
SHA-256: `46ce8c95207461b151d693be33365a2872135b91a54ee0af983bf6456828862e`.

- Restore 160 themed awakening bonuses across all 30 Sephira visions. Each complete passive kit now matches its original stat/Resonance counterpart's passive count; native effects and equip costs remain, with combined AP totals within 20% of that counterpart. Preserve all 131 excluded-original passives in MR, all active skills, permanent stats and acquisition settings. Avoid duplicate tiers of the same main stat bonus and kept originals' MR rewards.
- Saved-roster revision 7 adds missing bonuses through the backed-up progression update, preserving edited MR schedules and combat recipes. Full edited tiers fail before saving. Independent bundled Fina receives the same additive repair when there is room.
- Add the requested clean Touch It soundtrack for Ariana and Accumulate/Cure for both Fina versions. Cure follows the existing healing marker without adding an application event. The five unverified Global LB soundtracks remain flagged; a different Barusa LB and partial video matches are not presented as exact originals.
- Local validation: 601 Python tests (10 skips), 278 Flutter passes (one skip), clean analyzer; native writing/readback for all 30 kits and LB timelines, 26 private banks and 83 host recordings. Original table rows remain unchanged. Windows compilation and validation pass for the exact code commit. Live play is still needed to assess combined passive balance and perceived audio timing.

The balance pass retains 15–21 active skills and adds 4–9 awakening passives per vision, bringing complete
passive kits to 9–14 choices, equal to their native counterparts. Existing five-passive MR layouts and all
160 canonical excluded-original active grants remain. Shared awakening choices do not remove or relocate
the 131 canonical original MR passive allocations. They remain ordinary learned AP options; no free or
combined passive effects are introduced. Kept originals' MR rewards remain excluded. The original native
base stats, total Resonance mechanics, MP costs and permanent MR/AP budgets remain. This is a reasoned
starting balance, not a claim that equal passive counts or AP costs guarantee equal combat strength.

Revision 7 migrates revision 6 entries additively, preserving edited MR rewards, active skills, IDs, artwork,
locations and membership state. Earlier entries first receive their historical migrations, then the added
bonuses. Full edited awakening tiers fail before saving. Independent bundled Fina receives the additive
repair on load with a backup when it fits; full edited standalone kits remain openable and unchanged.
New/restored presets already include the added bonuses.

The two audio adaptations are explicitly requested. Ariana uses clean SE cue 617 from Touch It form
401000106 at LB1. Fina layers Accumulate (102) with the original common opening, then plays Cure (25) at
her existing reaction tick. The post-schedule alignment changes sound events only, leaving gameplay
application and cleanup events intact. The source recording pack remains about 1.6 MB and independent of
the optional animation library. Native writing/readback verifies 30 LB timelines, 258 sound events,
26 private banks and 83 host-format recordings with valid header/frame CRCs. Original rows remain
unchanged in seven physically read-back skill, sound, feedback and grading tables. All 30 complete kits,
314 private definitions, 26 private passive identities, 312 player presentation routes, 39 elemental
impacts and 30 command/Spirit icon pairs retain native readback coverage.

The exact Global LB audio routing remains unresolved for Christine, Barusa, Fryevia, Lilith and Elza.
Both the supplied Memorial master and the older JP master lack those exact identities. JP Barusa has a
different four-hit LB, while the selected Global form has two hits; partial matches in the narrated
Christine clip do not identify her full original soundtrack. Those are documented, not silently replaced
with unverified recordings. The existing original-skill review flags also remain in the runtime report.

Local validation: **601 Python tests** (10 platform/dependency skips), **278 Flutter passes** (one skip),
clean analyzer and bundle manifests. Windows compilation, complete validation, frozen engine startup and
launcher/updater checks pass for this exact commit. Package provenance, SHA-256, all **61 managed extension /
16 Fina files**, all 30 catalog profiles, 160 added bonuses and the embedded audio archive are verified.
Native serialized data and automated checks do not replace live-game balance and listening tests.

Measured delivery: first complete candidate **2026-10-23 00:54:41 PDT** → verified package
**01:10:42 PDT**, **16m 02s**, including local checks, CI, waiting, download and
verification. Earlier investigation precedes this candidate-to-verification timer. The helper joined the
matching automatic push run without dispatching another build. Publication changes only README/CHANGELOG
and does not rebuild or relabel the verified binary.

| Workflow | Outcome | Measured CI wall time | Windows runner time | Linux runner time |
| --- | --- | ---: | ---: | ---: |
| 39921373217 | success | 10m 30s | 14m 27s | 2m 15s |

Summed runner usage: **16m 42s**, separate from elapsed delivery time.

## Published Sephira LB audio and bonus-count correction — 2026-10-22

Code: [`fba79e6`](https://github.com/biscoBen/FFR-Vison-Studio/commit/fba79e69b702bdaffecd65e63801603f30f6c062), extension **1.2.68**.
Windows package: [run 39912426219](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39912426219/Sephira-Studio-Test.zip). **58,609,367 bytes** (58.6 MB).
SHA-256: `c9dc56bae3aabf4518900cca9e4e2bc162ec1dc0257543676e2f7a0deae99504`.

- Enable original FFBE LB recordings with source frame timing for 23 added visions, including the regional
  presentation metadata and layered Fran cue the previous audio adapter omitted. Supply the original charging
  recording for all 30. List the seven exact forms/custom sequences without an original soundtrack in
  `docs/SEPHIRA_LB_AUDIO.md`; no unrelated LB recording is substituted.
- Include only the small selected recording pack, independent of the optional animation library. Convert unsupported
  HFR/encrypted recordings for the installed game's audio adapter, retain complete sound tails, and use private banks.
- Back up and upgrade the old audio-off preset defaults once without resetting MR rewards, combat edits or artwork.
  Later explicit mutes and custom sound banks remain editable. Native bank/timeline checks and live listening results
  are reported separately; the game still needs a listening pass for volume, misses and synchronization.
- Include MR rewards in the home-screen bonus count, so visions whose passives moved into mastery no longer show
  zero bonuses. Their saved rewards and in-game behavior are unchanged.

The APK and decoded master/bank hashes, exact form IDs, selected variants and original cue frames are retained
in the small audio archive. Fran uses Shatterheart's second presentation and keeps both layers in each of its
three Ice Slash sound alternatives. Four recordings require offline conversion: three unsupported HFR attack
sounds and the encrypted charging cue. Cipher-aware VGAudio decoding preserves waveform polarity and sample
counts; an independent quality check caught the earlier encrypted-source decode before delivery. Converted
waveform readback is 35–71 dB SNR against the correctly decoded source, with matching sample counts. Layered
mixes retain headroom. The private host banks use the installed game's audio profile and original sound event
clock; combat data, hit timing and MR progression are not replaced.

The seven opening-only cases are Christine, Barusa, Fryevia, Lilith, Charming Kitty Ariana, Elza and the custom
Crystal Fina sequence. Different Japanese forms and Ariana's unrelated Touch It LB are not silently borrowed.
Standalone Fina also receives the charging cue. Existing native/party replacements and unrelated imported
visions retain their audio settings. Explicit sound-bank overrides and later mutes remain authoritative.

Validation: **599 Python tests** (10 platform/dependency skips), **276 Flutter passes** (one skip), clean static
analysis and manifest integrity. Focused correction checks rerun **33 Python tests / 55 Flutter passes**. Native
writing/readback verifies **30 real LB timelines**, **255 sound events**, **24 referenced private sound banks**,
**80 host-format recordings** with valid header/frame checksums, and unchanged original rows in seven skill,
sound, feedback and grading tables. Sound registration is checked in both generic and production composites.
Windows compilation and full validation pass for this exact commit. The downloaded package's provenance,
SHA-256, all **61 managed extension / 16 Fina files**, 30 presets and embedded audio archive are verified.
The optional full FFBE animation library remains excluded. In-game listening is still required for perceived
volume, misses/immunity behavior and synchronization; source-clock readback is not a live playback claim.

Old preset audio defaults upgrade once with a backup when Studio loads them. The MR revision and user edits
remain intact. Home cards count awakening and MR rewards, including permanent/stat/master rewards, rather than
showing zero when all passives are in MR. No reward or game-stat change accompanies that display fix.
Update while keeping **Studio Test Data**, then rebuild/install and restart the game. A kit reset is unnecessary.

Measured delivery: first complete candidate **2026-10-22 23:24:52 PDT** → verified package delivered
**23:48:54 PDT**, **24m 02s**, including local checks, the encrypted-source correction,
the additional bonus-count request, CI, waiting, download and verification. The timer was not restarted.
Both workflows were automatic push runs; helpers joined the matching runs without dispatching another build.
The first candidate passed CI but was superseded before a verified link was delivered. This download points
to the corrected candidate. Publication notes change only README/CHANGELOG and do not rebuild or relabel it.

| Workflow | Outcome | Measured CI wall time | Windows runner time | Linux runner time |
| --- | --- | ---: | ---: | ---: |
| Earlier audio candidate, superseded / 39911724021 | success | 8m 12s | 10m 16s | 2m 25s |
| Corrected audio and bonus-count package / 39912426219 | success | 12m 25s | 14m 31s | 2m 14s |

Summed runner usage: **29m 26s**, separate from elapsed delivery time.

## Published Sephira passive mastery and vision command icons — 2026-10-22

Code: [`08a5195`](https://github.com/biscoBen/FFR-Vison-Studio/commit/08a51958152721af53b2cefdb9d31b4b7fe81ca9), extension **1.2.67**.
Windows package: [run 39907648685](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39907648685/Sephira-Studio-Test.zip). **57,106,526 bytes** (57.1 MB).
SHA-256: `eb8c377a9b9ecf749512819767f218f582d46f93900c43f1e3c81c0a8d726539`.

- Preserve all 131 distinct passives from the 15 excluded original visions, once each, plus 19 curated extras. Each
  added vision has one passive at MR1/3/5/7/9; former MR active skills return to awakening. Keep permanent stat/AP
  and Spirit rewards. The backed-up MR update preserves active skill edits, IDs, artwork and acquisition choices.
- Correct all 39 neutral-source elemental skill icon mismatches. Give those custom attacks matching native hit
  particles at their original damage timing, preserving motion, sounds, hit counts and special-hit feedback.
  Native elemental borrowed presentations keep their effects; explicit user visual overrides remain intact.
- Give every added vision its own battle-command and Spirit icon. Remove the 16-slot donor fallback that showed
  Cloud/Terra icons on later imports, and preserve the original game's icon rows. Covers both Rain and Lasswell.
- Native asset writing/readback checks pass for all 30 kits, 39 elemental impacts and 30 command/master icon pairs.
  Live rendering and the revised passive balance still need playtesting; no missing original source is silently replaced.

The curated allocation contains **150 unique passives**: all 131 required originals and 19 extras, including
Knight of the Sacred Frost. Active grants and recipes remain; awakening has 15–21 active skills per vision and
no passive grants. Existing revision-3/4 source and acquisition migrations still run against their historical
layout before revision 6. Saved revision-5 profiles receive the curated MR rewards while retaining active
skills, permanent stat rewards, IDs, artwork, combat edits and acquisition settings. Standalone Fina keeps the
same MR allocation and Crystal Renewal in awakening; the known legacy reward repair remains backed up.
The level-10 practice Fina also retains the newly moved healing skill as a bounded 20%-HP boss copy.

The elemental effects use the original private reaction and native cosmetic hit-particle tables. No timeline
keys, damage hits, sounds, slowdown or flashes are added. Original critical/weakness/additional/miss/death
settings remain; three default-sentinel sources receive private generic feedback rows. Target body position
comes from the native reaction. With borrowed visuals off, all 39 get the new impact; with borrowed visuals on,
21 retain their existing elemental spell presentation and 18 use their recovered original attack plus impact.
Explicit user visual/icon edits remain authoritative. Command icons use separate per-vision serialized UI tags
and brush rows, avoiding the old 16-placeholder limit without replacing native tags or textures.

Validation: **595 local Python tests** (10 platform/dependency skips), **275 Flutter passes** (one skip), static
analysis and bundle integrity. Native writing/readback covers **30 kits**, **314 private skill definitions**,
**26 private passive identities**, **312 original player routes / 1,264 packages**, **39 elemental impacts** and
**30 command/master icon pairs** across 14 written tables. All original rows checked in ten definition, mastery,
feedback and UI tables are unchanged. Independent Fina reward and healing-route readback passes. Windows
validation, compilation, frozen-engine and release checks pass for the same code commit. Download verification
checks provenance, SHA-256, all **59** managed extension and **16** Fina file hashes, the actual catalog, all 150
passive selections and the shipped runtime helpers. The optional FFBE animation library remains separate.
These checks do not establish live appearance or balance; the three pre-existing original presentation reviews
remain flagged rather than silently substituted.

Update while keeping **Studio Test Data**, apply **MR and acquisition update**, rebuild/install and restart the
game. Preparation/review remains optional. Later edits to an already migrated recipe are preserved.

Measured timing: first complete candidate **2026-10-22 22:41:01 PDT** → verified package delivered
**22:58:14 PDT**, **17m 13s**, including local checks, the capacity-fixture and practice-boss
corrections, CI, waiting, download and verification. The timer was not restarted. The helper initially dispatched
before the automatic push run was visible; that duplicate was cancelled and the resumed helper joined the
matching push run. No second binary was delivered. README/CHANGELOG-only publication notes create no binary and
do not relabel the verified package.

| Workflow | Outcome | Measured CI wall time | Windows runner time | Linux runner time |
| --- | --- | ---: | ---: | ---: |
| Automatic Windows push / 39907648685 | success | 9m 44s | 12m 00s | 2m 05s |
| Raced duplicate dispatch / 39907651801 | cancelled | 3m 57s | 5m 11s | 1m 16s |

Summed runner usage: **20m 32s**, separate from elapsed delivery time.

## Published Crystal Fina battle recovery and MR repair — 2026-10-22

Code: [`aacedcc`](https://github.com/biscoBen/FFR-Vison-Studio/commit/aacedcccdc828262f0e22a0ca3799501e11e71ff), extension **1.2.66**.
Windows package: [run 39900403407](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39900403407/Sephira-Studio-Test.zip). **57,089,081 bytes** (57.1 MB).
SHA-256: `298f0cfdcaf3296f219f5bbc18de152bd1d4afc9689dbb39dd7108f1064a5881`.

- Prefer one persistent game-thread presentation loop on supporting loaders. Recover crystal updates after an
  older loader's native callback is lost; late callbacks cannot supersede the new request. Isolate invalid or unloading renderers, identify successive battle objects by their native addresses,
  and release stale action clocks/components independently so one failed cleanup cannot block later battles.
  Preserve the accepted glass, resonance glow and linked attack/damage speed.
- Correct the independent Crystal Fina preset's old stats-only MR layout to match her collection rewards. Detect
  that exact obsolete layout on opening Studio, importing, adopting or building; back up the previous roster and
  repair only her rewards and required learned healing skill. Preserve identities, artwork, acquisition, combat
  edits and deliberately edited reward layouts. Move an existing awakening grant to MR rather than duplicate it.
- Apply the private passive labels, learned-command availability, field healing and original animation handling
  to independent bundled Fina without enrolling her in Sephira's collection or its shop override. Verify standalone
  MR parity against the collection during bundle validation, and remap the learned skill's command on allocation.
- Local Flutter/Python regression checks and native table readback pass; Windows checks pass. The exact
  intermittent game-session trigger has not been captured; successive-battle testing in the game is still needed
  to confirm the disappearance is resolved.

The returned screenshot exactly matches the obsolete standalone layout: HP at MR1, Attack at MR2, Defence at
MR3, MP at MR4, Magic at MR5, Mind at MR6, Speed at MR7, HP at MR8, then Attack/AP/Spirit at MR9. Repair replaces
that known layout with Resist Light; HP+30; Magic Evasion +15%; AP+8; Crystal Renewal; MP+20; LB Charge on Action;
Spirit+15; then Divine Tidings/AP+8/Spirit of Crystal Fina. Existing grants move between awakening and MR rather
than duplicate. Custom skill slots are allocated without replacing edited skills, and native/party overrides
are excluded. Raw legacy imports with renamed keys and independent presets with edited artwork retain the
runtime reward handling, without being enrolled in collection acquisition overrides.

Validation: **591 local Python tests** (10 dependency/platform skips), **274 Flutter passes** (one skip), static
analysis and both bundle integrity checks. Executable Lua regression covers native repeating-loop selection,
older-loader fallback, lost/late callbacks, unloading unrelated renderers, stale action clocks, reused component
names, recreation, scope, glass, resonance and linked timing. The native asset tool writes and reads back **9**
actual full-game tables, including two correctly named private passives, the exact MR schedule and Crystal
Renewal's common command/field-healing flags. Its own original skill route clones four packages and applies the
guarded native motion/reaction edits. The old unused Raegen Blast definition is preserved; no repair or runtime
validation of that ungranted test definition is claimed. No fallback visual was added.

Full Windows validation and compilation pass for the same final commit. Download verification checks provenance,
SHA-256, all **59** managed extension and **16** Fina file hashes, the corrected standalone profile and actual new
runtime script. The optional FFBE animation library stays separate. The exact in-game disappearance trigger was
not captured: no live Unreal session, driver behavior or full sequence of other-unit actions is claimed as
reproduced. Test several battles in one game session after updating; collect diagnostics before restarting if
the crystal disappears again.

Close Studio/game, update while retaining **Studio Test Data**, reopen Studio, rebuild/install and restart the
game. The automatic migration backs up the prior roster and does not reset the kit. Preparation and patch review
remain optional. A deliberately edited reward layout is preserved rather than replaced.

Measured timing: first complete candidate **2026-10-22 21:16:13 PDT** → verified package
**21:38:19 PDT**, **22m 06s**, including local checks, corrections, the added independent
import identity case, both automatic Windows runs, waiting and verification. The timer was not restarted. Each
helper joined its matching automatic push workflow; no duplicate manual build was dispatched. The first run was
superseded before delivery. README/CHANGELOG-only publication notes create no binary and do not relabel this one.

| Workflow | Outcome | Measured CI wall time | Windows runner time | Linux runner time |
| --- | --- | ---: | ---: | ---: |
| Windows, superseded candidate / 39900076343 | cancelled | 5m 18s | 7m 39s | 1m 24s |
| Windows, final candidate / 39900403407 | success | 10m 11s | 12m 37s | 2m 07s |

Summed runner usage: **23m 47s**, separate from elapsed delivery time.

## Published optional game preparation and table refresh — 2026-10-22

Code: [`35c4f7b`](https://github.com/biscoBen/FFR-Vison-Studio/commit/35c4f7b5e29c2f501c3074e7b50c9a91aae56b6a), extension **1.2.65**.
Windows package: [run 39894606827](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39894606827/Sephira-Studio-Test.zip). **57,080,556 bytes** (57.1 MB).
SHA-256: `de6acc764f447c884d6eeb0766bc04292d4dabaadf45f3f1f7cbb48b6b4d5b32`.

- Make game-data preparation and patch review optional. Build/install using existing local data without a
  preparation record or review approval. Keep the tools, backups, references and Deck snapshots available under
  **Game tools & snapshots**. Remove the preparation requirement from Home; first-run dependencies are still needed.
- Keep the inexpensive checks for a changed game/settings during a build and installing an outdated build.
  Do not run preparation or consult its ledger in the ordinary build/install path.
- Optional refresh skips localization string tables used through the text catalog. Give parallel readers private
  mappings files to avoid exclusive-file conflicts. Cache unsupported optional reads against the game, mappings,
  reader and source bytes; retry required tables once and report actual required-table failures by name.
- Local/native and Windows validation pass; live install timing needs confirmation on the user's PC.

Update while retaining **Studio Test Data**, then build/install normally. The optional baseline and patch-review
records are not consulted by the normal build gate. Missing actual first-run data still needs setup; running a
manual refresh/collection blocks competing writes until that requested operation finishes. Game/input changes
during a build or before installing an old result still require a new build. This does not add an automatic refresh.
The optional read cache contains only known unsupported format failures, keyed by the game, reader, mappings and
source bytes. Temporary I/O/read errors are logged and tried on the next refresh; required table failures are
retried once and reported to the existing setup completeness check.

Validation: **583 local Python tests** (10 dependency/platform skips), **28 focused Flutter passes** (one skip),
static analysis and extension integrity pass. Regression covers builds with no/unreadable optional baseline,
review before preparation, stale-install rejection, changes during a build, private parallel mappings, localization
skips, unchanged failure reuse, source/mapping/reader invalidation, required failures and recovery after temporary
I/O errors. Native-reader proof decodes two actual full-game table packages, records one real non-table source as
unsupported, preserves every source byte and launches **zero readers** on the unchanged second refresh. The measured
small-fixture times are not a benchmark of a full refresh or the user's normal install.

Full Windows validation and compilation pass for the same final commit, together with the automatic Deck launcher
workflow. Download verification checks provenance, SHA-256, all **59** managed extension and **16** Fina file hashes,
the optional flow/helper version and unchanged vision catalog/art payloads. The optional FFBE library stays
separate. Gameplay and the previously reported animation review cases are unchanged by this install-flow update.

Measured timing: first complete candidate **2026-10-22 20:12:49 PDT** → verified package
**20:35:21 PDT**, **22m 31s**, including local checks, the correction to avoid caching
transient I/O failures, both automatic Windows candidates, their Deck checks, waiting and package verification.
The timer was not restarted. Each build helper joined the matching automatic push workflow; no duplicate manual
build was dispatched. The first candidate was superseded before delivery. Publication notes only change
README/CHANGELOG and do not create or relabel a binary.

| Workflow | Outcome | Measured CI wall time | Windows runner time | Linux runner time |
| --- | --- | ---: | ---: | ---: |
| Windows, superseded candidate / 39894022150 | cancelled | 9m 00s | 12m 17s | 1m 21s |
| Deck launcher, first candidate / 39894022158 | success | 1m 15s | 1m 14s | 0m 54s |
| Windows, final candidate / 39894606827 | success | 11m 51s | 12m 47s | 2m 05s |
| Deck launcher, final candidate / 39894606803 | success | 1m 18s | 1m 18s | 0m 56s |

Summed runner usage: **32m 52s**, separate from elapsed delivery time.

## Published complete Sephira runtime pass and FFBE heal test — 2026-10-22

Code: [`0b7a2c3`](https://github.com/biscoBen/FFR-Vison-Studio/commit/0b7a2c33f364793067f083ccfe66982349214a3c), extension **1.2.64**.
Windows package: [run 39889024440](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39889024440/Sephira-Studio-Test.zip). **57,079,338 bytes** (57.1 MB).
SHA-256: `bd472ba78ec76db36047ea9016467e0d4d431f876a434235eb455bc6e0d62068`.

### Sephira roster runtime corrections — 2026-10-22

- Review all 30 visions, every awakening tier and MR rank. Move 47 private passives into stable native passive
  IDs to fix blank rewards. Make all 15 private learned MR abilities available as character commands, including
  Crystal Renewal and Folka's Tidal Invocation/Waterga Surge. Give pure HP healing copies field-recovery metadata.
  Preserve saved recipes, explicit availability edits, power, costs, target grouping and permanent stat budgets.
- Give 312 private skills their own original player routes and sounds. Prefer 190 complete native player variants,
  restore 81 checked caster-motion tracks, resolve aliased impact rows, and teach imported models the native motion names their skills request using their
  own FFBE clips. Run independently of borrowed visuals. Keep original/global rows and enemy routes unchanged.
- Check all written reward names, passive IDs, ranks and learned-command availability before converting sprites.
  Stop early on changed audited source files. Record three original presentations still needing individual review
  in [the roster audit](docs/SEPHIRA_RUNTIME_REVIEW.md); do not silently substitute other skill visuals.
- Restore both of Fina's casing visibility flags after battle transitions. Retain the queued runtime callback and
  recover from removed attachments or transient actor errors per instance. Preserve the accepted glass and timing.
  Native serialization and fixture checks do not replace a live retest of the vision and boss.

### Snow White's approved FFBE Blood Recovery test — 2026-10-22

- Assign Scartio's FFBE Blood Recovery to Snow White's private heal, as requested, including its front/back layers,
  red flash and original healing sound. Retain one native heal and existing power, MP cost and targets. Works with
  borrowed visuals off; no new toggle or full-library download is needed. Keep explicit user presentation edits.
- Retain all 3,037 source sprite frames without cropping/dropping. Resample mesh texture cells while keeping world
  sizes. Check the native projects, atlases, audio and exact event/cleanup schedule. Layering, scale and the
  target-anchored source flash remain an in-game experiment, rather than a claim of exact FFBE render parity.

### Crystal Fina full-game diagnostics — 2026-10-22

- Update the standalone Fina runtime collector to select the full game, ignore demo paths, find Steam libraries
  and desktop Studio installations, and include the selected game's runtime install record. Show the resolved
  folders before collection. Keep the existing read-only file allowlist; no game assets or saves are collected.
- Supply only the Fina collector, launcher and instructions as a small standalone ZIP. It does not require
  rebuilding or updating Studio. Collection checks use fixture installations; live Fina rendering remains unverified.

Keep **Studio Test Data**, update Studio, rebuild/install and restart the game. The current roster and successful
preparation for the same full-game build can be reused. Borrowed visuals can stay off. Existing saved recipes are
not rewritten by the runtime normalization. Final rendering, already-earned reward behavior and gameplay still
need live testing; no save edits or rank resets are performed.

Validation: **579 local Python tests** (10 platform/dependency skips), **46 focused Flutter passes** (one skip),
static analysis and bundle integrity pass. Native tools write/read all 30 visions' reward and ability tables,
clone **1,264 original timeline packages**, apply **339 private object edits / 1,303 bytecode edits**, and reparse
them. Deliberately wrong Folka learned-command metadata and a blank Fina passive name fail the early table check;
restored tables pass. Blood Recovery additionally passes native writing/readback of all three SS6 projects,
textures, the original HCA bank, private player/enemy routes, exact healing/sound/cleanup events and original-row
preservation. The audio/SS6 donor-shell checks use the earlier compatible capture; the live full-game bank and
rendering still need confirmation. Its separate 9.6 MB payload retains every drawable source frame; source screen flash placement and
world scale remain unverified in-game. Three original presentations remain flagged in the roster audit.

Full Windows analysis/tests, frozen-engine setup, Python checks, extension integrity, launcher/updater checks and
compilation pass for the same final commit. Package verification checks provenance, SHA-256, all **59** managed
extension and **16** Crystal Fina file hashes, version **1.2.64**, the approved art payload and unchanged 30-preset
catalog. The complete optional animation library is not included. The previous passing **1.2.63** candidate was
superseded after the user explicitly requested the FFBE heal import; it was not delivered as the final update.

Measured timing: first complete roster candidate **2026-10-22 18:07:03 PDT** → verified package
**19:32:27 PDT**, **85m 24s**. This includes local/native checks and corrections,
the approved FFBE addition, CI waiting, both roster builds and package verification. The timer was not restarted.
The earlier standalone collector candidate was **2026-10-22 17:28:09 PDT**; including that work, elapsed
time to the verified package was **124m 18s**. Its two earlier Windows
runs failed path-related collector checks; the final Windows run includes their corrected tests. Each helper joined
the exact matching automatic push run; no duplicate manual workflow was dispatched. Publication notes change
README/CHANGELOG only and do not produce or relabel another binary.

| Workflow | Outcome | Measured CI wall time | Windows runner time | Linux runner time |
| --- | --- | ---: | ---: | ---: |
| 39878309861 (collector: short/long Windows path guard) | failure | 8m 08s | 10m 30s | 1m 35s |
| 39879508254 (collector: test path comparison) | failure | 8m 44s | 12m 05s | 1m 22s |
| 39886839777 (base runtime pass; superseded after approved import) | success | 16m 51s | 18m 50s | 2m 13s |
| 39889024440 (final, including approved FFBE heal) | success | 10m 36s | 12m 19s | 2m 02s |

Summed runner usage: **60m 56s**, separate from elapsed delivery time.

## Published shop verification and earlier table checks — 2026-10-22

Code: [`bdc10cd`](https://github.com/biscoBen/FFR-Vison-Studio/commit/bdc10cd841f691bbd26a49d17ef55ac56717f51a), extension **1.2.62**.
Windows package: [run 39871672325](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39871672325/Sephira-Studio-Test.zip). **47,530,217 bytes** (47.5 MB).
SHA-256: `8b5603da53620d6ab851b2dc6a7ca0884d173e419a5f4930ba0747553298eb45`.

- Fix the final Mitra inventory check when the temporary 1-gil Sephira shop override is enabled. Verify the
  effective build locations and include Folka's story-gated Olderion inventory when normal acquisition is selected.
  Keep checks for unrelated stock, purchase limits, conditions and missing entries.
- Run the existing acquisition/testing table checks and independently check shop routing immediately after writing tables,
  before building skill effects, converting unit sprites or packing. Stop at the first failed checked table with its name;
  retain final verification for later scene edits and generated assets. Sprite/packing failures can still occur later.
- Native serialization and Windows package validation pass; live installation requires a new test.

Update while retaining **Studio Test Data**, then rebuild/install. Prepared game data and the saved roster/settings
remain usable. No additional MR/acquisition update is required for this verification-only change.

Validation: **551 local Python checks** with 22 platform/dependency skips, **28 focused Flutter passes** and static
analysis pass. Regression covers both borrowed-visual modes, the shop override on/off, disabled members, normal Folka
story stock, stale entries and altered unrelated stock. The installed builder hook stops before effect/sprite/pack
work on a failed table. Signed zero is accepted, AI class references use the established verifier, and later
presentation edits remain checked at the final stage.
The pinned native patcher and row exporter pass **29 full-game tables / 2,822 operations** for normal routes and
**one inventory operation** for the shop override. Deliberately corrupted stock fails in both native cases.
Full Windows analysis/tests, frozen-engine setup, Python checks, bundle integrity, launcher/updater checks and
compilation pass for the same code commit. Download verification checks provenance, SHA-256, all **55** extension
and **16** Crystal Fina file hashes, the new hook/helper version and the unchanged 30-preset catalog. The optional
FFBE animation library remains separate. Live rebuilding and installation on the user's PC still need confirmation.

Measured timing: first complete candidate **2026-10-22 16:06:55 PDT** → verified package
**16:39:42 PDT**, **32m 47s**, including local checks, native export-format corrections, the correction to reuse existing
staged validators, both CI runs and download verification. The timer was not restarted after that correction. Reused
two matching automatic Windows runs for two distinct code commits; no manual/duplicate build was dispatched.
The first package was withdrawn to draft before delivery after final review found that broad recipe replay could
misread native hard-reference/vector export notation. The corrected version stages the existing independent validators.
Deck workflow files and transfer helpers were unchanged, so no separate Deck workflow was triggered. Publication notes only change README/CHANGELOG and
produce no new binary or relabelled package.

| Workflow | Outcome | Measured CI wall time | Windows runner time | Linux runner time |
| --- | --- | ---: | ---: | ---: |
| Windows 39870174199 (superseded) | success; package withdrawn | 10m 13s | 11m 44s | 3m 14s |
| Windows 39871672325 | success | 13m 25s | 14m 09s | 5m 18s |

Summed runner usage: **34m 25s** (**25m 53s Windows**, **8m 32s Linux**), separate from elapsed delivery time.

## Published protected MR rewards and temporary Mitra shop — 2026-10-22

Code: [`19202e6`](https://github.com/biscoBen/FFR-Vison-Studio/commit/19202e6367a084758ab822605e47caed6f0001d9), extension **1.2.61**.
Windows package: [run 39865892697](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39865892697/Sephira-Studio-Test.zip). **47,529,655 bytes** (47.5 MB).
SHA-256: `e3ce1001ca777bf6095e4a5d0ee6d8241d267929d7d513140017e0a6ef67df78`.

- Remove all 52 reused MR rewards belonging to the 11 original visions the user is keeping: 44 MR grants and
  eight awakening grants. Use 37 equipment/enemy bonuses and 15 bounded private enemy skills. Preserve the
  excluded originals’ full grant coverage, awakening counts, five MR abilities, permanent stats and boss budgets.
  Check all 55 protected original rewards by source ID, including private copies, so moving a reward cannot evade it.
- Apply this as recipe revision 5 through **Apply MR and acquisition update**. Back up the roster and replace
  affected learned rewards in place while retaining allocated identities, artwork, stats, unrelated skills and
  revision-4 custom acquisition choices. Keep native bonus mechanics; use private English text and a 20-AP floor
  for originally zero-cost item bonuses. See [the full replacement list](docs/SEPHIRA_REWARD_CHANGES.md).
- Add **Sephira visions: 1-gil Mitra shop**, off by default. Override only enabled collection members in the build,
  without rewriting saved locations/prices. While enabled, omit their challenge/cave/story-shop acquisition and
  sell them once each in Mitra. Turning it off and rebuilding restores saved acquisition. Purchased visions stay owned.
  Preserve the switch across settings saves, backups and Deck snapshots, independently of visual modes.
- Fix the reported final installation check expecting borrowed visual rows after building with original visuals.
  Recompute the same ephemeral visual/acquisition choices in verification. Preserve strict checks for unrelated rows.
  The supplied log reached final validation and did not confirm installation.
- Offline source, migration, shop-routing and native serialization checks cover these changes. Full Windows packaging
  checks pass; live full-game acquisition, visuals and battle difficulty still require playtesting.

Keep **Studio Test Data**, use **Apply MR and acquisition update** and rebuild/install. The existing game preparation
can be reused. Home’s new shop override applies after a rebuild/install; switching it off restores saved routes and
prices. See [the vision guide](SEPHIRAS_VISIONS.md) and [all 52 source replacements](docs/SEPHIRA_REWARD_CHANGES.md).

Validation: **547 local Python checks** with 22 platform/dependency skips, **271 Flutter passes** plus one platform
skip, and static analysis pass. A local suite run stalled at API tests with restricted networking and was interrupted;
the diagnostic rerun with network access passed all checks. Regression covers every protected MR source in both
progression fields and active-copy recipes, native bonus conditions/costs, reassigned IDs, custom slot collisions,
legacy migration, edited acquisition preservation, settings round trips and reversible shop routing. The actual
installed verifier reproduces the original-mode mismatch and checks the corrected mode without weakening unrelated-row checks.
The pinned native patcher/readback verifies **165 operations across eight full-game tables**, including **37** named
private bonuses, **15** new active recipes and visual/hit bindings, plus **30** one-gil vision prices and Mitra stock.
Native bonus effect parameters and unrelated rows are preserved; formerly zero-cost bonuses use a 20-AP equip cost.
Full Windows analysis/tests, fresh frozen-engine setup, Python suite, bundle checks, launcher/updater checks and
compilation pass for the same code commit. Deck launcher and Windows transfer checks also pass. The downloaded
release matches provenance/SHA-256, all **55** extension and **16** Crystal Fina file hashes, all 30 revision-5 presets,
all 55 protected source exclusions and the standalone Deck installer. The optional FFBE library remains separate.
Live gameplay, balance and acquisition behavior still need testing on the user's installation.

Measured timing: first complete candidate **2026-10-22 22:28:15.670 UTC** → verified package
**22:44:53.302 UTC**, **16m 38s**, including local checks, the interrupted API-test run and diagnostic rerun,
CI waits, metadata access fallback and download verification. Timer not restarted. One matching automatic Windows
run and its companion Deck workflow were reused; no manual or duplicate build was dispatched. Publication notes
are a README/CHANGELOG-only commit and do not rebuild or relabel the verified binary.

| Workflow | Outcome | Measured CI wall time | Windows runner time | Linux runner time |
| --- | --- | ---: | ---: | ---: |
| Windows 39865892697 | success | 10m 17s | 13m 05s | 2m 13s |
| Deck 39865892852 | success | 1m 18s | 1m 18s | 0m 37s |

Summed runner usage: **17m 13s** (**14m 23s Windows**, **2m 50s Linux**), separate from elapsed delivery time.

## Published Sephira MR progression and guarded vision challenges — 2026-10-22

Code: [`3fc7cdb`](https://github.com/biscoBen/FFR-Vison-Studio/commit/3fc7cdb313ba2419673133c321307c8986c487f6), extension **1.2.60**.
Windows package: [run 39857881255](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39857881255/Sephira-Studio-Test.zip). **47,513,201 bytes** (47.5 MB).
SHA-256: `73fa2d10de15878f48b2e87ca6d4557cb28bdf494eb365d24d5ea7c4addfa503`.

- Give all 30 presets five learned MR rewards at 1/3/5/7/9, one permanent role stat at 2/6/8,
  AP at 4, and Spirit mastery plus AP alongside the MR9 ability. Keep MR0 as the native starting rank.
  Preserve all earlier learned abilities and the 20–28 awakening quota; eight low-tier attacks fill the short kits.
- Add **Apply MR and acquisition update** for saved presets. Back up the roster before saving and retain identities,
  sprites, stats, custom skill mechanics and learned abilities. Already-updated presets keep later edits.
- Add the requested 28 challenge rewards at the matched originals’ crystals; Barusa/Ariana use a separate Zoldaad
  cave. Check each original’s ownership or actual completion state before the menu, before battle and before rewards.
  Tronn uses his story grant; Wilhelm uses final quest progress 48/50. Keep original shrine memories available.
- Share one local-level boss budget across each opposing team, including Cecil’s three visions. Add private enemy
  copies of learned active skills, generic attacks, staggered eight-action AI, bounded recovery and native visuals/sounds.
  Winning grants missing visions only; cancel/escape/loss never grant them. Add no farmable experience, gil or drops.
- Place Aria in Mitra’s shop and Folka in Olderion’s item shop after its guardian story scene. Folka costs twice
  the highest other inventory price. Locations and gates come from the supplied full-game maps, quests and tables.
- Fix Crystal Fina’s material verification after Restore missing assigns a new ID: verify the intended texture-name
  rename while still requiring the original cooked shader/export bytes. No extra extraction is needed for this fix.
- Keep standalone sprite conversion independent of challenge helpers when no saved roster is present.
- Validation covers portable migration, original event preservation, all unlocks, native table serialization and AI
  execution. Gameplay balance, controller interaction and all shrine fights still require live full-game testing.

Close Studio, update while keeping **Studio Test Data**, then use **Apply MR and acquisition update** in
**Sephira’s visions** before rebuilding/installing. Keep the full-game folder selected. Preparation for the same
build is reusable. See [the complete vision guide](SEPHIRAS_VISIONS.md) for the final kits, MR rewards, all original
acquisition gates, encounter levels and teams. This package includes the Restore missing Crystal Fina fix.

Validation: local static analysis, **268 Flutter passes** plus one skip, and **542 Python checks** with 22 skips
pass. Native patch/readback verifies **3,071 operations across 29 full-game tables**, preserves unrelated rows and
original vision grants, and roundtrips all **28 AI classes**, **45 choice sequences**, the reward sequence and Tronn’s
private interaction/streaming assets. Actual pinned material serialization passes with reassigned Fina IDs 13500 and
13514 while retaining identical cooked export bytes. Migration checks preserve earlier learned abilities and edits.
The initial Windows build compiled but found three standalone converter tests loading a challenge dependency without
a roster. The import is now conditional, and those tests pass with an isolated subprocess environment.
Final full Windows analysis/tests, fresh frozen-engine setup, Python suite, bundle checks, launcher/updater checks
and compilation all pass for the same code commit. The companion Deck workflow passes; its files are unchanged by
the converter correction. The downloaded release matches provenance/SHA-256, all **55** extension and **16** Crystal
Fina file hashes, the 30 preset recipes and the standalone Deck installer. The optional FFBE library remains separate.
Offline checks do not establish live battle balance, controller interaction or every shrine encounter.

Measured timing: first complete candidate **2026-10-22 21:12:10.885 UTC** → verified package
**21:45:34.312 UTC**, **33m 23s**, including local checks, the Windows converter correction, user approval wait,
both builds, CI waits and download verification. Timer not restarted. The helper reused each exact-commit automatic
push run; no manual or duplicate build was dispatched. The README/CHANGELOG publication commit uses the cheap
checks and does not rebuild or relabel this binary.

| Workflow | Outcome | Measured CI wall time | Windows runner time | Linux runner time |
| --- | --- | ---: | ---: | ---: |
| Windows 39856415003 | failure | 10m 02s | 12m 47s | 3m 05s |
| Deck 39856414858 | success | 2m 10s | 2m 10s | 1m 50s |
| Windows 39857881255 | success | 13m 23s | 13m 45s | 4m 27s |

Summed runner usage: **38m 04s** (**28m 42s Windows**, **9m 22s Linux**), separate from elapsed delivery time.

## Published installation records for separate game folders — 2026-10-22

Code: [`3c0b1aa`](https://github.com/biscoBen/FFR-Vison-Studio/commit/3c0b1aa4345ff4c37b42d68de80b0bed0a4dc91f), extension **1.2.59**.
Windows package: [run 39833304270](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39833304270/Sephira-Studio-Test.zip). **47,479,720 bytes** (47.5 MB).
SHA-256: `bb430d4ee5ae1fd3e2b98e11d0284a958f71bc65c85aeab891c153ff0ed4e7af`.

- Fix installation stopping at “Restore the field leader runtime in the previous game folder first.”
  Keep the legacy runtime/package ownership records and backups with their original game. Later game folders
  use separate records under `game-installs/`, so full-game installs and restores cannot reuse the demo's backups.
- When runtime effects are needed and the destination lacks a loader, copy only the loader DLLs/settings/layouts
  and allowlisted signature files from an existing Studio-managed installation. Preserve the source game and
  unrelated mods; refuse conflicting destination files. Track newly copied files and remove only unchanged owned
  copies on restore. Existing destination loaders remain unowned and are preserved.
- Check runtime/loader ownership again before deployment and roll back added files if a runtime write fails.
  Bind package records/backups to the folder captured by the operation, even if the selected folder changes mid-copy.
  Keep native prepared data and saved recipes. The supplied full-game log confirms its mod packed and passed
  table verification, then stopped before installation; it does not establish live gameplay behavior.
- Regression covers both folders through the actual pinned installer source, including legacy records, identical
  backup timestamps, independent restores, loader conflicts, edited files, races and failed state writes.

Update Studio while keeping **Studio Test Data** and the full-game folder selected. The returned log shows a
successfully built and verified mod; use **Install the last build** if the game/settings are still the same.
No new game preparation is required solely for this fix. The user's actual installation and runtime playback still
need a retry; copying an existing loader does not establish live full-game compatibility.

Validation: **107 focused local Python checks** (one platform skip) and **28 Flutter passes** plus one Windows-only
skip; static analysis passes. After binding the operation to its captured folder, **50 focused Python checks** pass.
All **nine migration cases** also pass after making their filesystem snapshot comparison portable on Windows.
Exercise the actual pinned server's install/restore functions using independent temporary game folders, legacy
ledgers, equal backup timestamps, mid-copy selection changes and unrelated files. Check runtime loader copy,
conflict refusal, edited-file preservation and rollback after failed state writes. Full Windows analysis/tests,
fresh frozen-engine setup, Python suite, bundle checks, launcher/updater checks and compilation pass for the same
final commit. Downloaded provenance/SHA-256, all **53** extension and **16** Crystal Fina file hashes, and the unchanged
standalone Deck installer match source. No native assets or personal installation records are published.

Measured timing: first complete candidate **2026-10-22 18:23:32.763 UTC** → verified package
**18:53:21.275 UTC**, **29m 48s**, including local checks, the folder-binding correction,
a Windows test-path correction, superseded builds, queue waits and download verification. Timer not restarted.
Three automatic push runs were used; the first two were superseded and cancellation was requested. The helper reused
the final exact-commit run; no manual or duplicate workflow was dispatched. No separate Deck workflow was triggered
by these paths; the standalone installer source is unchanged.

| Workflow | Outcome | Measured CI wall time | Windows runner time | Linux runner time |
| --- | --- | ---: | ---: | ---: |
| 39831313547 | cancelled | 7m 20s | 7m 44s | 3m 21s |
| 39831972601 | cancelled | 11m 39s | 12m 47s | 3m 19s |
| 39833304270 | success | 13m 19s | 14m 19s | 4m 51s |

Summed runner usage: **46m 21s** (**34m 50s Windows**, **11m 31s Linux**), separate from elapsed delivery time.

## Published full-game table support — 2026-10-22

Code: [`db66b58`](https://github.com/biscoBen/FFR-Vison-Studio/commit/db66b583f3774596cc24f27e799564718f931df7), extension **1.2.58**.
Windows package: [run 39825612562](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39825612562/Sephira-Studio-Test.zip). **47,477,843 bytes** (47.5 MB).
SHA-256: `11dbb300153b8c2333e7e745c8b43eddb04f22f5ef025b0c97b34cf971d97a3d`.

- Resolve demo composite names to the selected game's production packages using its official asset inventory.
  Read shared and production parents together; write custom clones into the parent that actually owns the donor
  and update the production composite. Preserve prepared source dumps and saved units/settings.
- Apply the same resolution to practice battles, native-vision grants, caves, skill visuals and sound registration.
  Verification recomputes physical table operations and still rejects unrelated changes. Refresh production skill
  routes when loading an already-prepared catalog, without requiring another full preparation.
- Include production bindings in native-reference reports, deduplicate parent/composite copies and expand future
  collection to the map, shop, stage, dialogue and UI tables used by these features. If the optional FFBE Needles
  test remains enabled, retain the full game's native timeline when present without changing the saved switch.
- Offline validation uses the supplied full-game skill assets and the pinned native patcher: 38 sampled bindings,
  76 added routing rows, exact readback of all three physical tables, and every original row preserved. Production
  fixture tests cover practice/grants, split donors, conflicting parent rows, stale demo caches and strict verification.
  The supplied ZIP omits actual full-game cave/menu table rows; live installation and gameplay still need testing.

Update Studio while preserving **Studio Test Data**, retain the full-game folder selected and retry **Install to game**.
The successful full-game preparation can be reused. Existing per-build review and source-specific guards remain active;
this update does not certify untested full-game visuals, direction, timing, caves or menus.

Validation: **109 focused local Python tests**, **55 passing Flutter tests** plus one Windows-only skip, and static
analysis pass. The pinned native patcher/readback also registers a private bank in both full-game sound tables,
preserving every native row. All **30** preset unit IDs and **292** custom skill sources have no full-game definition/
route-ID conflicts. Full Windows analysis/tests, fresh frozen-engine setup, Python suite, bundle checks, launcher/updater
checks and compilation pass for the same commit. The separate Linux launcher and Windows snapshot-transfer checks
pass. Downloaded provenance/SHA-256, all **53** extension and **16** Crystal Fina file hashes, and the standalone Deck
installer match source. Native source files remain local; the archived FFBE library is not included in the update.

Measured timing: first complete candidate **2026-10-22 17:44:26.540 UTC** → verified package
**18:01:33.907 UTC**, **17m 07s**, including focused checks, a corrected local test-import invocation,
additional native audio verification, CI waits and download verification. Timer not restarted. One matching automatic
Windows build was reused, plus the expected Deck workflow; no manual or duplicate build was dispatched.

| Workflow | Measured CI wall time | Windows runner time | Linux runner time |
| --- | ---: | ---: | ---: |
| Windows 39825612562 | 13m 45s | 16m 57s | 4m 46s |
| Deck 39825612576 | 2m 11s | 2m 11s | 1m 43s |

Summed runner usage: **25m 37s** (**19m 08s Windows**, **6m 29s Linux**), separate from elapsed delivery time.

## Published native reference collection fix — 2026-10-22

Code: [`1a430dd`](https://github.com/biscoBen/FFR-Vison-Studio/commit/1a430dd18fd3c651073cd8940dfa32b638c3a494), extension **1.2.57**.
Windows package: [run 39815956581](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39815956581/Sephira-Studio-Test.zip). **47,474,944 bytes** (47.5 MB).
SHA-256: `af239b060eefc50e07382201c675227b7cb271c59eff9cc12e77e6a8089a075c`.

- Give each parallel reference reader a private temporary copy of the mappings file. The pinned reader opens
  mappings with exclusive sharing; the previous workers competed for one file and could abort collection.
  Preserve the original mapping bytes and prepared game data. No upstream engine or mapping replacement is applied.
- Check the mapping path before extraction, log decoded tables, and retain the leading error cause plus the table
  name if a native read fails. A failed collection stops and cannot publish a complete reference.
- Update Studio and retry **Collect current game reference**. The successful preparation can be reused;
  **Download latest reference** becomes available after a successful collection.

Validation: **49 focused local Python checks** (two platform skips), **28 passing local Flutter tests** plus
one Windows-only skip, and the actual pinned mappings reader exercised locally. Native regression uses a valid
minimal usmap: opening the locked shared path fails with IOException, while identical private copies parse successfully.
Windows CI repeats that contract using its checksum-verified engine. A concurrent collection fixture forces all four
workers to overlap, checks private mapping bytes/cleanup, and downloads a complete reference through the real API.
Also check a failed job stops without enabling download, missing mappings stop before extraction, and long errors retain
their leading cause. Full Windows analysis/tests, fresh frozen-engine setup, Python suite, bundle checks, launcher/updater
checks and compilation pass. Separate Linux launcher and Windows transfer checks pass. Downloaded provenance/SHA-256,
all **52** extension and **16** Crystal Fina hashes, and standalone Deck helper match source. Native game files from the
user's full-game installation were not collected here; that live collection still needs a retry.

Measured timing: first complete candidate **2026-10-22 16:38:53.996 UTC** → verified release download
**16:53:49.853 UTC**, **14m 56s**, including local checks, queue/CI waits and verification. One automatic Windows
run was reused plus the expected Deck workflow; no duplicate or manual build was dispatched. Timer not restarted.

| Workflow | Measured CI wall time | Windows runner time | Linux runner time |
| --- | ---: | ---: | ---: |
| Windows 39815956581 | 12m 19s | 13m 28s | 4m 10s |
| Deck 39815956546 | 3m 11s | 1m 51s | 1m 27s |

Summed runner usage: **20m 56s** (**15m 19s Windows**, **5m 37s Linux**), separate from elapsed delivery time.

## Published backup before upstream changes — 2026-10-22

Source checkpoint: [`6c7c15e`](https://github.com/biscoBen/FFR-Vison-Studio/tree/pre-full-game-upstream-2026-10-22),
preserved in annotated tag **pre-full-game-upstream-2026-10-22** and branch **backup/pre-full-game-upstream-2026-10-22**.
[Rollback kit](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/pre-full-game-upstream-2026-10-22/Sephira-Studio-Pre-Upstream-2026-10-22.zip):
**132,962,159 bytes** (133.0 MB). SHA-256: `352e2fdcf15e7fffe9344797df29e5c58b1571a152a3815983a7178171c2fa31`.

- Preserve the existing verified Windows package (code `9493d9b`, run **39507226508**, extension **1.2.56**),
  exact frozen engine **1.0.0.15**, matching base/icons/common/catalog packs, captured host manifest and rollback notes.
  Source/history remain available through the remote checkpoint; the optional archival library is not duplicated in the kit.
- No upstream code was integrated. The checked original repository's default branch is `990f2cc`, five commits
  beyond the inherited `d94c685` baseline; the currently hosted manifest still advertises **1.0.0.15** with the same
  pinned engine SHA-256. This does not establish full-game compatibility or rule out updates elsewhere.
- Personal configurations, saves and optional downloaded artwork are not uploaded. Keep a closed local copy of
  the whole Studio folder, including **Studio Test Data**, for the user's complete working setup. The kit preserves
  published components but is not an automatic offline reconstruction of private files.

Validation: remote tag and backup branch both resolve to `6c7c15e`; app, engine and core-pack hashes match their
published values. Download the newly published kit again, check its whole-file SHA-256 and ZIP CRCs, then verify all
eight recorded input-file hashes and source identity. No new Windows app was compiled; its prior validation is retained.
Direct asset upload authentication failed, so isolated Actions run **39813336244** published the same deterministic
archive. A redundant helper revision/run **39813529373** stopped at the already-existing release; its temporary branch
was removed. The saved checkpoint refs were not changed.

Measured archive-candidate timing: **2026-10-22 16:16:39.133 UTC** → downloaded/verified backup
**16:24:06.736 UTC**, **7m 28s**, including upload recovery, extra helper attempt and verification; timer not restarted.
Archive helper CI wall times: **24s** successful publication and **16s** redundant attempt. Total Linux runner usage:
**34s** (**22s + 12s**); no Windows runner usage for this backup. These are separate from elapsed delivery time.

## Published Crystal Fina boss scale verification — 2026-10-20

Code: [`9493d9b`](https://github.com/biscoBen/FFR-Vison-Studio/commit/9493d9be0b16a6021d8cf5004ee55baaed8bb4ca), extension **1.2.56**.
Windows package: [run 39507226508](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39507226508/Sephira-Studio-Test.zip). **47,474,464 bytes** (47.5 MB).
SHA-256: `74ff8c38afe46c4bf1cee56b2f7e85027d97985224dc6e4b5c3471abc0c3e388`.

- Fix the final table check rejecting the resized boss. Python's `0.9 * 1.3` produced
  `1.1700000000000002`; the actual native FloatProperty row exporter writes `1.17`.
  Round the intended scale before writing the recipe so exact verification succeeds.
- Keep the requested 130% vision size and strict table checks. Existing prepared data can be reused;
  update Studio and retry **Install to game**. This supersedes the earlier size package for installation.

Validation: **22 focused Python tests**, **28 passing local Flutter tests** plus one Windows-only skip,
and a local run through the actual engine patcher/row exporter. Add the same native conversion regression
to Windows CI using its checksum-verified engine archive. The old failing value changes during conversion;
the corrected recipe verifies exactly, and a genuinely changed scale is still rejected. Replace approximate
size assertions with exact comparisons. Full Windows analysis/tests, fresh frozen-engine setup, Python suite,
bundle verification, launcher/updater checks and compilation pass. Downloaded provenance/SHA-256, all **52**
extension and **16** Crystal Fina hashes, and standalone Deck helper match source. No live game installation
was performed; the user's install still needs a retry.

Measured timing: first complete candidate **2026-10-20 22:18:15.958 UTC** → verified release download
**22:32:18.017 UTC**, **14m 02s**, including local checks, CI waits and package verification. One automatic
Windows run was reused; no duplicate or manual build was dispatched. CI wall time: **12m 30s**.
Summed runner usage: **17m 59s** (**13m 06s Windows**, **4m 53s Linux**), separate from elapsed delivery time.

## Published Crystal Fina boss size — 2026-10-20

Code: [`ddaaba6`](https://github.com/biscoBen/FFR-Vison-Studio/commit/ddaaba6559de919a63832e8f7fe0645cf4559123), extension **1.2.55**.
Windows package: [run 39504158761](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39504158761/Sephira-Studio-Test.zip). **47,474,444 bytes** (47.5 MB).
SHA-256: `57f94e7abe5ac396d4d1c5e7c179220159ff3b197bb3359a51ff8c2ffec292bf`.

- Reduce the practice boss and her attached crystal to 130% of her normal vision size.
  Use her native donor's scale rather than the much larger fallback for unset scales.
  The demo boss scale is now 1.17 instead of 2.7. Her vision and cave presentation stay as configured.
- Update Studio and reinstall the mod to apply the size change. Existing prepared game data can be reused.

Validation: **72 focused Python tests** and **28 passing local Flutter tests** plus one Windows-only skip.
Check both the standalone boss and shared vision presentation. Full Windows analysis/tests, fresh frozen-engine
setup, Python suite, bundle verification, launcher/updater checks and compilation pass. Downloaded provenance,
SHA-256, all **52** extension and **16** Crystal Fina hashes, and standalone Deck helper match source.
No live game installation was performed; in-game framing still needs a retry.

Measured timing: first complete candidate **2026-10-20 21:54:03.503 UTC** → verified release download
**22:08:35.697 UTC**, **14m 32s**, including local checks, CI waits and package verification. One automatic
Windows run was reused; no duplicate or manual build was dispatched. CI wall time: **12m 33s**.
Summed runner usage: **16m 55s** (**12m 23s Windows**, **4m 32s Linux**), separate from elapsed delivery time.

## Published fresh-preparation layout fix — 2026-10-20

Code: [`ee10c3d`](https://github.com/biscoBen/FFR-Vison-Studio/commit/ee10c3d88b82ba0bbc2ca47322b3fa9d6eeb20ab), extension **1.2.54**.
Windows package: [run 39500304695](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39500304695/Sephira-Studio-Test.zip). **47,474,317 bytes** (47.5 MB).
SHA-256: `66496df0adf5e6f818753422cfa0c5661a0403a3c51270c0b8adcd546ef8696c`.

- Fix the missing `build/visions_mod/check/da/DA_UIUnitSsLayout.json` failure after preparing game data.
  Imported sprites and empty/native-only rosters no longer read an unnecessary donor-layout dump. Cloned
  native sprites read the current extracted UI layout directly, recovering missing packages from official
  containers when needed, instead of relying on shipped or prior-build JSON.
- Explain whether preparation is needed because the setup has no recorded baseline, the selected game
  files differ, or a preparation was interrupted. An untracked baseline does not prove a Steam game update.
  Keep native fingerprint and patch-review guards. An already successful preparation can be reused.
- Regression checks cover builds with the old layout cache absent, fresh native donor layouts, stale cache
  exclusion, official-container extraction and the distinct preparation states. Windows gates pass;
  the user's actual game install still needs a retry.

Validation: **512 Python checks** (20 local platform/tool skips), **266 passing local Flutter tests** plus
one Windows-only skip, and analysis pass. Execute the actual patched builder's layout block with Fina,
Agrias and Alaya without the old `check` directory, plus a native donor clone with fresh layout fixtures.
The existing native-only and fully reverted build tests also run without pre-seeding the old layout file.
Verify that a stale shipped cache is ignored and missing-source extraction excludes `~mods`. Preserve
changed-game and interrupted-preparation guards. Full Windows tests, fresh frozen-engine setup,
launcher/updater checks and compilation pass. Separate Linux launcher and Windows transfer checks pass.
Downloaded provenance/SHA-256, all **52** extension and **16** Crystal Fina hashes, and the standalone Deck
helper match source. No live installation into the user's game or new game-reference collection was performed.

Measured timing: first complete candidate **2026-10-20 21:23:44.065 UTC** → verified release download
**21:40:52.572 UTC**, **17m 09s**, including regression corrections, local checks, CI waits and package verification.
One automatic Windows build and the separately triggered Deck workflow ran; no duplicate or manual build
was dispatched. The timer was not restarted.

| Workflow | Measured CI wall time | Windows runner time | Linux runner time |
| --- | ---: | ---: | ---: |
| Windows 39500304695 | 13m 00s | 13m 49s | 4m 53s |
| Deck 39500304702 | 2m 20s | 2m 16s | 1m 27s |

Summed runner usage: **22m 25s** (**16m 05s Windows**, **6m 20s Linux**), separate from elapsed delivery time.

## Published Crystal Fina level-10 boss test — 2026-10-20

Code: [`533749b`](https://github.com/biscoBen/FFR-Vison-Studio/commit/533749b798f348a160176fbe907d0d5f5130dc0c), extension **1.2.53**.
Windows package: [run 39495008542](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39495008542/Sephira-Studio-Test.zip). **47,473,092 bytes** (47.5 MB).
SHA-256: `f831a1f4edba15bd716862e01a1fba62e10a3f508b08ef3e618b8096661dd2b2`.

- Add Crystal Fina to the item-shop practice picker: level 10, 6,500 HP, fixed early-boss stats, a weak
  neutral attack, light spells and a bounded self-heal. Her eight-action native AI schedules one action
  at a time, with Holy as its stronger single-target move. Retain private copies of her full active kit.
- Load her approved native body and rotating crystal without requiring her in the roster. Share the
  presentation when she is included; keep the enemy independent of player vision edits. Add a seventh
  choice page with working More/Cancel. No acquisition gating, vision reward, XP, gil or item farming.
- See [the stats, rotation and test steps](docs/CRYSTAL_FINA_BOSS.md). Native builds and automated checks
  pass as described below; live encounter behavior and level-10 difficulty still need testing.

Validation: **506 Python checks** (20 local platform/tool skips), **266 passing local Flutter tests** plus
one Windows-only skip, and analysis pass. Full Windows validation, fresh frozen-engine setup, native Kismet
size/jump contracts, dialogue patching, launcher/updater checks and compilation pass for the published commit.
Build/read back all **10** affected native boss tables (**93** private rows), both standalone and shared Fina
presentations (**27** clips each), the crystal/material/texture/runtime payload and all **seven** choice sequences.
The standalone case requires no saved/imported Fina. Download provenance/SHA-256 and all **52** extension and
**16** Crystal Fina source hashes match; the standalone Deck helper also matches. No live fight was run.

Measured timing: first complete candidate **2026-10-20 20:30:13.039 UTC** → verified release download
**21:03:26.009 UTC**, **33m 13s**, including local/native checks, correction, both automatic CI runs, waits and
package verification. The first run exposed an obsolete 19-row expectation in the Windows-only dialogue
contract; update it to the 21 rows required by thirteen opponents and seven pages, and verify it with the real
engine serializer before the second push. No encounter code changed in that correction. The timer was not
restarted and no duplicate/manual workflow was dispatched.

| Automatic run | Result | Measured CI wall time | Windows runner time | Linux runner time |
| --- | --- | ---: | ---: | ---: |
| 39493478585 | Failed stale dialogue test | 11m 24s | 12m 48s | 3m 19s |
| 39495008542 | Passed and published | 13m 55s | 13m 03s | 5m 52s |

Summed runner usage: **35m 02s** (**25m 51s Windows**, **9m 11s Linux**), separate from elapsed delivery time.

## Published launch preparation and local Steam Deck snapshots — 2026-10-19

Code: [`910aa18`](https://github.com/biscoBen/FFR-Vison-Studio/commit/910aa185ec5c653f424182b714f7d49a12cd74cd), extension **1.2.52**.
Windows package: [run 39370792784](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39370792784/Sephira-Studio-Test.zip). **47,465,970 bytes** (47.5 MB).
SHA-256: `82e40408a3fd3cd1431cbd7bc9bba1920139a124410a5f185830d01b03cde313`.

- Add **Launch preparation & snapshots** on Home. Collect fresh official native skill/unit/MR/routing tables,
  timeline packages, sound references and inventory in an isolated view that excludes installed mods. Compare
  exact definitions, schema fields, routing and asset/timeline changes against the supplied demo metadata;
  retain raw evidence in a downloadable reference. Localized labels alone do not count as route changes.
- Identify game builds by every top-level native container name/size and every `.utoc` hash. Preserve older
  prepared directories when the build changes; rebuild native rows/listing/catalog instead of reusing shipped
  demo caches. Reject builds/installs against untracked or changed preparation and stale last builds. Invalidate
  preparation before moving data so failed attempts and switching back cannot reuse partial files. Flag enabled patches on unreviewed builds with an explicit, fingerprint-specific review or original-game preset.
  Detect full-game folders by the actual container marker without inventing an app ID/name.
- Add a reversible **original-game test preset**. Back up settings first, disable the visual/repair/test controls
  and original-vision test grants, retain edited kits/appearances and explicit custom animations. Individual
  switches remain available. A completely unmodified comparison still requires removing the mod.
- Add a 31-entry editable launch sheet: 19 original-enemy failed skill names / 20 candidate IDs, two separately
  reported imported-vision failures and ten regression groups. Preserve Waterga's unresolved exact variant and
  AI-only shared references. Save visuals, direction, sound, hit timing and notes separately per native build;
  export CSV without converting old observations into new-build passes.
- Make local finished-mod snapshots the main Deck route. Build once on PC, export **Resonance-Mod-Snapshot.zip**,
  copy/extract on Deck and run **Install snapshot.sh**. Include a standalone Python installer, exact compiled
  files and required Crystal Fina/cycling runtime. No GitHub, credentials, Studio download or building on Deck.
  Stream large exports through the browser; verify game/input/output freshness and package checksums.
- Reuse the owned-file installer transaction, automatic backups, interruption recovery and restore shortcut.
  Use native Windows/Linux file locks and process checks; expose Windows regression traces directly in CI annotations.
  Later snapshots remove stale runtime files. Keep optional private GitHub publishing collapsed and opt-in;
  normal builds and local snapshots never upload.
- Add a separate **Studio backup** for the recorded roster, appearance/acquisition choices, icon layout and
  visual/testing settings. Preview before restoring, reject a stale preview and make an automatic prior backup.
  Restore atomically with rollback; notify Studio to reload saved setups and invalidate prior builds. Reject
  stale desktop saves; preserve pending edits in a local backup before reloading a restored roster. Preserve
  machine paths, credentials, source downloads and saves separately.

Validation: analysis, **266 passing local Flutter tests** plus one Windows-only skip, **501 Python checks**
(19 local platform/tool skips), and real Chromium round trips pass. Check Studio backup export/preview/restore,
stale saves and previews, pending-edit backup/reload including engine reconnection, per-build observations/CSV,
unchanged-demo comparison and a streamed Deck download without JavaScript errors. The exported ZIP's own Bash
wrapper installs all **nine** fixture mod/runtime files, verifies their hashes, creates the shortcut and restores
cleanly in an isolated Linux handoff. Native Windows/Linux locking, local imports, stale runtime removal and
owned-file rollback pass; separate Windows transfer checks pass too.

Full Windows analysis/tests, fresh frozen-engine setup, launcher/updater checks and compilation pass for this
exact code. The downloaded package's provenance and SHA-256 match the published asset; all **50** extension and
**16** Crystal Fina hashes match source, and the standalone installer matches its managed payload. No large FFBE
source packs are bundled. Their trusted manifest, original engine pin, personal rosters and game skill assignments
are unchanged. Full-game mappings/asset compatibility and actual Deck/Proton gameplay, graphics, controller input
and runtime behavior remain to be tested; these tools do not turn source presence into a live visual pass.

Measured timing: first complete candidate **2026-10-20 04:08:31.758 UTC** → verified release download
**04:55:29.813 UTC**, **46m 58s**, including corrections, local checks,
Windows diagnosis, failed/superseded builds, waits and package verification. The timer was not restarted.
One early helper call raced automatic-run registration and dispatched an unnecessary manual Windows run;
subsequent delivery joins the existing automatic run. Intermediate failures exposed the Linux-only installer lock
and the CI command-contract update; both are resolved in the delivered package. Measured workflow wall times:

| Workflow run | Result | Wall time |
| --- | --- | --- |
| [39368599062](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/39368599062) (Windows) | cancelled | 6m 45s |
| [39368602423](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/39368602423) (Windows) | failure | 9m 04s |
| [39368884298](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/39368884298) (Windows) | failure | 10m 19s |
| [39369694565](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/39369694565) (Windows) | cancelled | 6m 46s |
| [39370003885](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/39370003885) (Windows) | cancelled | 4m 41s |
| [39370152167](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/39370152167) (Windows) | success | 17m 58s |
| [39370792784](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/39370792784) (Windows) | success | 12m 16s |
| [39368599049](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/39368599049) (Deck checks) | success | 1m 28s |
| [39369694534](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/39369694534) (Deck checks) | failure | 1m 48s |
| [39370003695](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/39370003695) (Deck checks) | success | 2m 18s |

Sum of started-to-completed runner job time across these runs: **103m 17s**
(**70m 07s Windows**, **33m 10s Ubuntu**). This is measured job duration,
not billed/rounded usage, and is separate from end-to-end elapsed time and overlapping workflow wall times.

## Published portable fog-edge conversion and missing source coverage — 2026-10-18

Code: [`bbf642f`](https://github.com/biscoBen/FFR-Vison-Studio/commit/bbf642f53220cfb583599826cb5d19a12cdbc465), extension **1.2.48**.
Windows package: [run 39150580826](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39150580826/Sephira-Studio-Test.zip). **46,602,319 bytes** (46.6 MB).
SHA-256: `b241b9a2327986fff25621abc4d238eab4c4b7c481f23b0d14a63379c581ec7b`.

- Correct shared triangle-edge ownership to match GL's top-left fill rule. Translucent mesh triangles no longer shade their common diagonal twice.
- Add **Soften exposed fog edges**, on by default, with an original-edge comparison. Recognize normal-blended source fog/cloud/smoke surfaces; feather their exposed geometry outlines in generated PNG alpha. Preserve the interior, source RGB, timing and raw archive files. Already feathered mesh outlines, additive flashes and non-fog materials keep their existing treatment. The correction addresses the circled background wall and slanted fog sheet in Unei's Snowstorm and applies to the same material classes throughout the library.
- Bake the treatment into conversion textures rather than clipping the browser viewport. Add **Download visual-layer conversion** under **Effects and sound cues**: prepared PNGs, a normalized animation document and a helper for the existing SpriteStudio converter. Optional emitter selection can split large effects. These are visual-layer source files, not an installed skill; timing placement, anchors, sound routing, asset capacity and game bindings still need integration. No game assignment or table changes are made.
- Refresh derived particle previews once for corrected triangle rasterization and separate soft/original profiles. Keep all 56 optional library packs unchanged; no source-library redownload is needed.
- Audit the source index across the full available unit data. Supplement missing Memorial character records with checksum-pinned Global unit grants, passives, limit bursts and enhancements from `aEnigmatic/ffbe` at `95727376e82d27acc1290b6dc8ad27ce3c89ea71`. Require an exact typed skill ID and matching original name before linking Global grants to an existing Memorial record. Keep original first-source labels while retaining every associated owner for filtering.
- Add **531 selectable sources**, bringing the selector to **3,901**. Christine now shows her seven matching library records, including Blizzaga despite its first source being Lasswell. Also retain all 94 previously omitted named monsters whose available records have no skill-set associations. Keep known units with no matching archive skills selectable; explain their missing Global records by name instead of silently omitting them. Christine's Snow Burial and other exclusive Global skills have no matching record in this supplied Memorial archive; no substitute animations are guessed.
- Correct all **21 esper** source links using the original esper/rank status table. The skill table's boolean field was previously mistaken for an identity. Preserve every existing character/monster variant and all 65,428 original Memorial records.

Validation: local analysis, **28 focused Flutter checks** (one Windows-only skip), **485 Python checks**
(19 local platform/tool skips) and real Chromium checks pass. Cover the complete 3,901-name source index,
actual Christine/shared Blizzaga, other missing Global units, no-association monsters, all esper joins,
source checksums, triangle fill, alpha at multiple aspect ratios, independent edge profiles, pagination/reset,
rotated framing and rear → actor → foreground compositing. At Snowstorm's exposed fog outline the prepared
texture's maximum border alpha changes from 180 (original) to 0 (soft), independently of the viewport.
A real UI conversion download is processed by the existing SpriteStudio converter: all **199** fog-sheet cells
retain exact RGBA in both PNG and BGRA atlas data. This verifies portable visual data, not live-game playback
or automatic skill integration. Source camera/motion and other particle behavior remain approximate; soft edges
are a reversible conversion treatment, not a claim of native FFBE parity.

Full Windows validation, fresh frozen-engine setup, launcher/updater checks and compilation pass for the exact
code. The downloaded package's provenance and SHA-256 match its published release asset. All **46** extension
and **16** Crystal Fina file hashes match source; no large library packs are bundled. The separate release's
**56** source-pack digests stay unchanged. Engine pin, personal rosters and game skill assignments are unchanged.

Measured timing: first complete candidate **2026-10-18 17:09:57.750 UTC** → verified release download
**17:56:07.371 UTC**, **46m 10s**, including local checks, corrections, the final monster-registry audit, both
builds, waits and verification. The timer was not restarted after corrections. Actual CI wall times were
**10m 10s** (run 39149811241) and **11m 57s** (final run 39150580826). Both matching automatic code runs
succeeded; no duplicate manual workflow was dispatched. Sum of started-to-completed runner job time across
both runs: **31m 35s** (**23m 34s Windows**, **8m 01s Ubuntu**), separate from the overlapping CI wall times
and end-to-end elapsed time. These are measured job durations, not billed/rounded usage.

## Published animation source filters and mesh alignment — 2026-10-17

Code: [`645270a`](https://github.com/biscoBen/FFR-Vison-Studio/commit/645270adff9be984c5b1e6b2f47d1caf6df79201), extension **1.2.46**.
Windows package: [run 39085967496](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39085967496/Sephira-Studio-Test.zip). **46,353,319 bytes** (46.4 MB).
SHA-256: `77cf2768ef6f9df74ff87c89a24a412ca82cbfe72619a08dae791faf89537319`.

- Add a searchable **Ability source** selector, grouped into **Characters / visions**, **Monsters** and **Espers**. Select an exact source to show its recorded abilities; **All sources** clears the filter. Combine source selection with skill type, text search, pagination and the existing option to include records without animation references.
- Follow every recorded owner of a shared presentation. Selecting a source returns that source's exact original skill ID and labels its preview with the selected owner, even when the unfiltered library lists the shared animation under another unit. Preserve distinct character/monster sources and separately named unit versions.
- Keep the same optional library download and existing archive bytes. Unattributed records remain in **All sources** and are not guessed into a unit's kit. Filtering and previewing change no game skills or saved roster data.
- Correct Unei’s **Snowstorm** preview and the common composition path: draw rear groups behind the actors and front groups over them, preserving source order within each pass. Screen-anchored effects use their authored flat backdrop as a separate viewport reference instead of being fitted into the unit scene. This prevents large fog walls from shrinking the actors and exposes fewer rectangular plate borders; source camera motion and 3D projection still remain approximate.
- Preserve each mesh’s authored pivot after projecting it into a centred bitmap, including signed scale, rotation and mirroring. Apply this to every mesh-based library preview rather than patching a named spell. The source audit finds 529 off-centre meshes among 875 original mesh files; this is a structural audit, not visual verification of every skill. Include rotated sprite corners in the preview bounds so diagonal effects are not cropped by unrotated framing.
- Upgrade existing v15 particle draw positions without regenerating texture PNGs when sprite counts, texture indices and every non-position field still match. Re-render if that compatibility check fails. Original shader values, timelines, sounds, archives and game assignments stay intact.
- Keep the remaining rendering limit explicit: these shared corrections do **not** certify every skill as visually identical to FFBE. Source camera motion, mixed-axis 3D transforms and other unsupported particle behavior still need native comparisons; the apparent Snowstorm wind edge is not a verified one-for-one match.

Validation: local analysis and 28 focused Flutter checks (one Windows-only skip), 477 Python checks (seven skipped),
exact source filtering/pagination/reset, real canvas compositing, rotated-corner framing and all four Unei Snowstorm
components pass. Firaga, Cure, Tornado, Holy and Blizzaga load and produce particles in Chromium without warnings.
A numerical audit checks 2,843,667 projected vertices across all 875 source meshes at three tilts, signed scales,
rotation and mirroring; maximum coordinate error is below 5e-13. This proves coordinate consistency, not visual parity.
The full Windows validation/compilation, frozen-engine startup and launcher/updater checks pass for this exact code.
Package hashes match all 46 extension files and 16 Crystal Fina files; no large library packs are bundled. The optional
library's 56 existing pack digests stay unchanged. Some camera-dependent 3D behavior still needs native comparison;
the remaining Snowstorm wind outline is not certified to match FFBE.

Measured timing: first complete candidate **2026-10-18 00:53:33 UTC** → verified release download
**01:29:09 UTC**, **35m 36s**, including the mesh correction, both builds, local checks, waits and verification.
The timer was not restarted after the correction. Actual CI wall times were **11m 27s** (run 39084512021) and
**10m 57s** (final run 39085967496). Sum of started-to-completed runner job time across both runs: **31m 38s**
(**24m 00s Windows**, **7m 38s Ubuntu**); this is measured job time, not billed/rounded usage. The end-to-end
elapsed time is separate from the overlapping CI durations and runner usage.

## Published optional animation library, named sources and preview units — 2026-10-17

Code: [`1a32262`](https://github.com/biscoBen/FFR-Vison-Studio/commit/1a322621825313798daaedb57f896651b78e4e36), extension **1.2.44**.
[Verified Windows download / run 39081843723](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39081843723/Sephira-Studio-Test.zip), **46,350,787 bytes** (46.4 MB).
[Independent source data release](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/ffbe-library-memorial-en-v208-1).

- Keep the 1.99 GB Memorial library out of Studio app packages. Opening **FFBE animation library** checks for existing verified packs; missing data prompts **Download library / Not now**. Nothing downloads at normal startup. Show progress and allow pause/resume; check every pack's SHA256 and publish the installed manifest only when all files pass. Reuse prior installed library data across Studio updates and repair only missing or damaged packs.
- Publish the unchanged source packs once as an independent, immutable data release. Ship only the small trusted manifest and browser metadata with app updates. Keep all original source records, sound banks and files available for later conversion; browsing still assigns nothing to the game.
- Show actual FFBE unit, monster or esper source names derived from level grants, enhancement recipes, limit-burst links, bestiary names and enemy skill sets. Search also finds alternate owners. Unlinked records say **Unattributed FFBE source** rather than guessing a character or showing a numeric ID as the source.
- Combine identical same-named skill presentations under their first known source: **45,478** browsing entries represent **65,428** retained master records. Preserve character/monster versions, differing sprite sequences, particle files, cue timing, hit timing, placement flags and cinematics. Original IDs and aliases remain available internally for later imports.
- Preview with animated **Christine 6★** and **Cactuar** sprites instead of dots. Choose either caster, show one or three actual targets and mark original hit times. Christine uses her FFBE idle; Cactuar uses the supplied Resonance demo idle. These are preview actors only; source caller motion/camera commands and every FFBE emitter remain subject to the existing renderer limits.
- Correct Cactuar’s unevenly packed native cells using their original coordinates and pivots. Verify every idle frame against its original pixel hash to catch head/arm clipping or neighboring-frame bleed.

Validation: local analysis, **28 focused Flutter checks** (one Windows-only check skipped), **469 Python checks**
(seven skipped), source-archive verification and Chromium previews pass. Cover consent/decline, progress, pause/resume,
checksum failures, existing-library reuse, corrupted-pack repair, source-name search, distinct timing/target/audio/sprite
variants, Christine/Cactuar rendering, original Needles audio, seeking and cinematics. The full Windows Flutter suite, analysis, **469 Python checks** (seven skipped), fresh frozen-engine installation, original particle/sprite/audio/cinematic reads, launcher/updater checks and compilation pass.

The downloaded app's provenance and SHA256 match the selected workflow. All **46** packaged extension files
(**43** managed runtime resources) and **16** Crystal Fina files match source hashes. The app contains no
`assets/ffbe_library/` packs. All 56 independent data-release digests match the existing immutable archives.
A real public download through the shipped installer fetches one missing pack, reuses 55 existing verified packs
and commits a ready manifest successfully. Windows' fresh-install fixture installs all 56 packs through a local
transport; the public test separately confirms the real download endpoint. Archive bytes, engine pin, game
assignments, personal rosters and Crystal Fina assets remain unchanged. No mod rebuild is needed for browsing.

Package SHA256: `e618d9548ee7bc3fc1d509101da166a2908d5e969bdce1ae3d85fb1dfc710909`.

First complete code candidate **00:03:59.187 UTC** to verified download **00:25:49.545 UTC** on October 18:
**21m 50s**, including local checks, the reported Cactuar clipping correction, build waits, separate-data publication
and package/public-download verification. The final matching push run took **13m 39s** of CI elapsed time.
Two automatic code workflows ran: the first was superseded/cancelled and the corrected candidate passed; no manual
duplicate was dispatched. Summed runner job time: **31m 37s** (**24m 29s Windows**, **7m 08s Linux**), separate
from local elapsed time. Required step outcomes are confirmed through the Jobs API; package download used the
helper's authenticated, checksum-verified test-release fallback.

## Published FFBE animation and sound library — 2026-10-17

Code: [`a8bec63`](https://github.com/biscoBen/FFR-Vison-Studio/commit/a8bec63f8840ac44089e20018a5e057f84595968), extension **1.2.43**.
[Verified Windows download / run 39076528651](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39076528651/Sephira-Studio-Test.zip).

- Preload all **65,428** skill records from the supplied, SHA-pinned Memorial EN Global Events v208 APK delivery: 486 magic, 43,536 abilities, 17,926 monster skills, 3,417 limit bursts and 63 summons. Preserve distinct IDs, conditional timelines, raw master rows, 15,674 effect groups, 8,779 effect definitions, original particle/texture/model/sprite files and differing source-file variants.
- Add **FFBE animation library** on Home. Search/filter by name, ID or filename; browse source groups, individual effects and 90 cinematics. Preview particles/sprites with original cue timing, play/stop, seeking, sound, speed, zoom, target count and conditional variants. Cinematics retain transparency and embedded sound in browser previews, alongside their original USM sources.
- Preserve the original SE/System sound banks, all 1,011 cue records and 990 distinct lossless preview recordings. Preserve random cue alternatives and play/stop instructions; trim decoded HCA padding to the source's declared sample length. Keep the original bank for the one unsupported System block-sequence cue; no skill-group SE cue is missing.
- Keep the entire library separate from mod inputs and personal rosters: browsing assigns nothing, edits no skills and requires no mod rebuild. Bundle 56 independently verified packs (1.99 GB); stage locally in bounded memory and reuse verified copies. No library download, APK, FFmpeg or developer Python is required on the user's PC.
- Include four standalone first/second-part limit-burst clips found in the base delivery catalog. Preserve their original filenames independently of complete-film references; incremental archival updates retain all existing source bytes and skill identities.
- Preserve references absent from the supplied delivery and label unavailable previews: one particle filename, 26 sprite dependencies, six effect-group IDs and 110 exact cinematic filenames. Available regional cinematic variants remain independently browsable, without silently equating different filenames. These counts cover master-file links; archival BMB editor/template dependencies and unsupported formats can cause further per-entry preview warnings. Particle rendering approximates FFBE's engine, caps previews at 30 seconds/256 particles per emitter and does not establish exact playback parity or Resonance compatibility. Full original files remain available for later conversion.
- Defer further missing-native-animation investigation until the full game launches on Thursday, as requested. Preserve the reported failures for comparison and leave all existing game skill assignments and visual-testing toggles unchanged.

Validation: local analysis, 31 focused Flutter checks, **454 Python checks** (seven skipped), complete source-table/cue/member integrity checks and browser playback pass. Chromium checks cover Needles' four ordered streaks and 20 sound pulses, Fire, Cure, Bad Breath, Flame Sword, cinematic playback, all four supplemental clips, search/pagination, mute, speed and first-seek rendering. The archived library contains **13,634** verified files. This does not establish rendering parity for every FFBE emitter, caller motion or camera command.

Windows analysis, the full Flutter suite, **454 Python checks** (seven skipped), fresh frozen-engine installation, actual particle/sprite rendering, sound/cinematic reads, launcher/updater checks and compilation pass. The downloaded ZIP's provenance and SHA256 match the selected workflow. All **56** library pack digests and **43** extension/**16** Crystal Fina resource hashes match source. The library manifest is identical after Windows newline normalization. Crystal Fina assets, original engine checksum, personal rosters and game skill assignments remain unchanged. No mod rebuild is required to browse.

First complete code candidate **22:25:37.707 UTC** to verified download **23:08:01.813 UTC**: **42m 24s**, including local checks, the first-seek correction, the final base-delivery audit/four additional clips, uploads, build waits and verification. The final matching push run took **18m 07s** of CI elapsed time. Three automatic code workflows ran: one superseded/cancelled run, one successful 86-clip candidate and the final 90-clip package; no manual duplicate was dispatched. Summed runner job time across them: **43m 04s** (**28m 15s Windows**, **14m 49s Linux**), separate from local elapsed time. GitHub's log-storage download was unavailable; required step outcomes are confirmed through the Jobs API. Package/artifact storage used the helper's authenticated, checksum-verified test-release fallback.

## Published read-only intermittent crash collector — 2026-10-17

Code: [`31c2d35`](https://github.com/biscoBen/FFR-Vison-Studio/commit/31c2d35dd2bc7dee12f1fa8c240d3eb6ffe6119a).
[Successful Windows validation / run 39069211497](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/39069211497).
[Collector source and instructions](scripts/reference/game-crash/).

- Add a standalone Windows helper that collects recent Unreal crash contexts, bounded game/UE4SS logs,
  runtime hashes, installed-mod inventory and available testing/repair-version reports. Run after the crash
  before restarting. No game mutation, installation, tracer or Studio rebuild is needed; saves, assets,
  DLL contents, rosters and memory dumps are excluded.
- Record live confirmation: the practice picker works, revised FFBE 1,000 Needles placement and successful-hit
  sound work. A separate generic fatal error occurs while walking in Mitra and on a repeat practice interaction.
  This helper collects evidence; it does not claim a fix or identify the crash's cause without the report.
- Update the original-enemy test instructions to match the twelve installed practice choices. Keep native
  baseline tests separate from borrowed skill visuals and the optional FFBE Needles import.

Validation: 445 Python checks pass locally and on Windows (seven skips on each platform), including actual
helper execution against fake game/Saved trees. Windows analysis, 263 Flutter tests (one skipped), fresh frozen-engine
startup, launcher/updater checks and compilation pass. All 37 extension and 16 Crystal Fina packaged resource hashes
match source; no game/runtime code is changed. The helper ZIP's contents and SHA256 are verified locally; GitHub's
standalone extra-asset upload returned HTTP 401, so the ZIP is supplied directly in chat alongside the committed
source. The crash itself remains undiagnosed pending the user's report.
First complete candidate **21:00:54.779 UTC** to verified collector ZIP **21:11:54.398 UTC**: **11m 00s** (rounded),
including checks, waiting and the failed extra-asset upload. One matching push run: CI **6m 53s**; summed runner job
time **10m 18s** (**9m 50s Windows**, **28s Linux**). No duplicate workflow was dispatched.

## Published practice menu name-retention crash fix — 2026-10-17

Code: [`b57a263`](https://github.com/biscoBen/FFR-Vison-Studio/commit/b57a263a080c46a80896de8456cb1d70da1d9eec).
[Verified Windows test release / run 39067343262](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-39067343262).

- Fix the runtime crash while opening the practice picker: its choice tag used name index 79, but the
  inherited shell's `NamesReferencedFromExportDataCount` retained only the first 36 names in IoStore.
  Preserve the full 80-name map in its existing order on all six authored menu pages.
- Check that every menu tag falls inside the retained prefix after writing. Regression tests reproduce
  the old 79/36 mismatch on all six pages, and the pinned engine's serializer checks their actual FName indices.
- Reproduce the failure by packing/extracting the old page: its tag becomes unresolved `79`. Pack/extract all
  six corrected pages and verify their retained names, native calls, bindings and compiled timing. Container
  integrity verification alone did not detect this error. Extension 1.2.42 aligns startup/install checks.
- The packed assets pass these checks; opening, navigating and cancelling the menu in-game still need user confirmation.

Validation: 439 Python checks (seven local/six Windows skips), 28 focused local Flutter tests, full Windows
analysis and 263 Flutter tests (one skipped), fresh frozen-engine startup, updater/launcher checks and compilation
pass. The pinned engine's FName-index contract passes for all six pages. Actual IoStore packing/extraction and
native readback retain the complete original name prefix, menu tag, native callbacks, unbound tracks and compiled
timing on all six pages; the old packed page reproduces the unresolved index 79. Downloaded provenance/checksum
and 37 extension resources match source; 16 Crystal Fina resources remain unchanged. Live interaction is pending.
First complete candidate **20:33:57 UTC** to verified download **20:41:35 UTC**: **7m 38s**, including checks,
waiting and verification. One matching push run: CI **6m 02s**; runner job time **9m 25s** (**9m 01s Windows**, **24s Linux**).

## Published mixed-build testing verification fix — 2026-10-17

Code: [`7e1f095`](https://github.com/biscoBen/FFR-Vison-Studio/commit/7e1f095abf1670d3c0e50f8157faa466bf42124f).
[Verified Windows test release / run 39065483449](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-39065483449).

- Fix the final `Unit/DT_UnitParameter` check when **Survive at 1 HP for testing** is used with imported visions.
  The previous check expected only original rows plus testing edits, rejecting the three added visions after
  the normal verifier had already passed. Compare shared tables with the complete build recipe, then impose
  independently recomputed testing requirements. Keep the normal original-row verifier and full row checks.
- Replay native partial map/struct updates, first-element struct-array templates and indexed values when
  computing expected rows. Verify imported units, native stat edits and additional private passive/effect rows
  together with survival. Missing/extra rows, incorrect values and missing survival effects still fail, including
  when a faulty build recipe contains the same survival error. Report the affected row names in future errors.
- Extension 1.2.41 aligns startup/install checks. Reproduce the reported failure with native cooked tables,
  then verify the corrected mixed build and IoStore packing. This fixes build verification; live practice-menu,
  survival and revised FFBE visual/audio behavior still need in-game confirmation.

Validation: 437 Python checks (six skips locally and on Windows), 28 focused local Flutter tests, full Windows
analysis and 263 Flutter tests (one skipped), fresh frozen-engine startup, updater/launcher checks and compilation
pass. Native table write/readback and the actual testing verifier pass with three imports, a native stat override,
additional private passive/effect rows and survival enabled. Repeat native practice talk/composite/map/encounter/stage
readbacks, six choice sequences and IoStore packing pass. Downloaded provenance/checksum and all 37 extension
resources match source; 16 Crystal Fina resources remain unchanged. Live behavior remains pending confirmation.
First complete candidate **20:06:25 UTC** to verified download **20:15:57 UTC**: **9m 32s**, including a test-fixture
correction, repeated local checks, waiting and verification. One matching push run: CI **6m 34s**; runner job time
**9m 57s** (**9m 29s Windows**, **28s Linux**).

## Published practice menu link serialization fix — 2026-10-17

Code: [`3e58dfa`](https://github.com/biscoBen/FFR-Vison-Studio/commit/3e58dfa48c8731350f3ede08aa8c6c0da06a655e).
[Verified Windows test release / run 39063684610](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-39063684610).

- Fix the next build failure when writing the shop woman's empty `ContinuousEventList`. Replace her row
  using a populated native continuous-event template, restoring every original field except the menu link.
  Clear the template's quest flags, progress and request changes; retain the original dialogue and arguments.
- Write `ArgList` as its native map property rather than an unsupported dotted struct path. Use independently
  retained native talk rows in regression tests, and exercise all nineteen dialogue edits with the pinned
  engine patcher in Windows CI, including a negative control that reproduces the reported empty-array error.
- Extension 1.2.40 aligns startup/install checks. Native talk/composite/map/encounter/stage table serialization,
  exact readback, six choice-sequence readbacks and IoStore verification pass. The reference omits the map
  composite and UI choice table; those remain covered by logical/schema checks and the user's successful
  choice-table write. Live menu operation still needs confirmation after installing this fix.

Validation: 431 Python checks (six skips locally and on Windows), 28 focused local Flutter tests, full Windows
analysis and 263 Flutter tests (one skipped), fresh frozen-engine startup, updater/launcher checks and compilation
pass. The new actual-engine dialogue contract passes on Windows. Downloaded provenance/checksum and all 37
extension resources match source; all 16 Crystal Fina resources remain unchanged. Live menu operation is pending.
First complete candidate **19:42:27 UTC** to verified download **19:49:25 UTC**: **6m 58s**, including local checks,
waiting and verification. One matching push run: CI **5m 28s**; runner time **8m 53s** (**8m 27s Windows**, **26s Linux**).

## Published practice boss-category fix — 2026-10-17

Code: [`c6e3acc`](https://github.com/biscoBen/FFR-Vison-Studio/commit/c6e3acc7907e1da6345ee7cc705f64a98535cf75).
[Verified Windows test release / run 39062414190](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-39062414190).

- Fix the preparation failure on Gigantuar (352): the game classifies it, Sheratan (641) and Alpherg (651)
  as `Boss`, while the new practice validator only accepted `Enemy`. Accept both native hostile categories,
  retain expected levels, and continue rejecting playable/vision rows. Leave opponent categories, stats and AI intact.
- Replace the generated enemy-category test assumptions with independently retained fields from all thirteen
  supplied demo unit rows used by the twelve practice choices. Exercise every choice and the three boss rows,
  including rejection of playable/vision substitutions. Extension 1.2.39 keeps startup/install checks aligned.
- The supplied error occurred before any practice tables were written. Common `System.acb` LB-opening warnings
  are separate from this failure. Live practice-menu interaction still needs confirmation after rebuilding.

Validation: 429 Python checks (five local/six Windows skips), 28 focused local Flutter tests, full Windows analysis
and 263 Flutter tests (one skipped), fresh frozen-engine startup, updater/launcher checks and compilation pass.
All twelve encounters pass preparation against the supplied full native unit table; native encounter/stage
serialization, exact readback and IoStore verification pass with the original rows retained. Downloaded
provenance/checksum and 37 extension resources match source; 16 Crystal Fina resources remain unchanged.
First complete candidate **19:23:16 UTC** to verified download **19:31:30 UTC**: **8m 14s**, including local checks,
waiting and verification. One matching push run: CI **5m 29s**; runner time **9m 10s** (**8m 44s Windows**, **26s Linux**).

## Published FFBE needle groups/audio and in-game practice picker — 2026-10-17

Code: [`ba64cb5`](https://github.com/biscoBen/FFR-Vison-Studio/commit/ba64cb5db4bc7cffb15a86d3096c5ccabab3b0c7).
[Verified Windows test release / run 39059206346](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-39059206346).

- Correct the FFBE converter's missing ordered-model emission placement: four particles were retained but
  superimposed at one position. Preserve the positioning mesh's vertex order/scale and per-node instance identity,
  including shared child trails. Reject unsupported shape/alignment modes. Keep every source particle/frame and
  the original eleven group starts; the skill still deals one native fixed-damage hit.
- Import the original `se_special_needle_1` recording and all twenty source sound triggers through the existing
  host-format HCA/routing adapter. Keep the entire recording and allow its final tail to finish.
- Add default-off **Survive at 1 HP for testing**. Attach private battle-only unlimited reprieve and instant-death
  resistance to playable units, preserving damage, healing, existing passives and enemy stats/AI. Disable and
  rebuild/install to remove it; runtime behavior across damage/status cases still needs live testing.
- Replace Studio's opponent dropdown with a native in-game choice dialog at Mitra's item-shop Young Woman.
  Six pages cover the usual encounter, Cactuar and all ten comparison candidates. Choose an opponent per fight
  without rebuilding, or cancel without a fight. Private groups use the usual practice rewards (or MR override),
  guaranteed escape, native enemy units/AI, an instance-loaded plains stage and no story/recovery/save changes.
  Preserve the old saved opponent field for compatibility; it no longer selects the fight.
- Extension 1.2.38; cooked needle/audio/timeline and survival-table readbacks pass. Native choice functions,
  unbound event tracks and compiled timing are checked after writing. Menu interaction, 1-HP survival, revised
  appearance and audible levels remain pending in-game confirmation.

Validation: 263 Flutter tests (one local Windows-only skip), 428 Python checks (five local/six Windows skips),
analysis, frozen-engine startup, updater/launcher and Windows compilation pass. Read back all 8,917 converted
animation keys and atlas pixels, original audio/timeline/binding assets, survival tables and six private native
choice pages; IoStore verification passes. Downloaded provenance/checksum and 37 managed resources match;
16 Crystal Fina resources are unchanged. Live confirmation of the new changes remains pending.
First complete candidate to verified download: **24m 20s**, including corrections and waiting. Successful CI:
**5m 31s**; both runs used **11m 34s** runner time (**11m 04s Windows**, **30s Linux**). A redundant manual
run was cancelled after the matching automatic push run became visible; no second package was used.

## Published FFBE 1,000 Needles visual-import prototype — 2026-10-17

Code: [`deb8139`](https://github.com/biscoBen/FFR-Vison-Studio/commit/deb8139972651c3bc32502c030aeaf3c1b24d8ca).
[Verified Windows test release / run 39016148168](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-39016148168).

- Recover the original `atk_nail1_white.bmb`, both textures and its mesh from the supplied Memorial APK's
  checksum-verified delivery packs. Retain source rows/checksums and a reproducible conversion script.
- Add default-off **Test FFBE 1,000 Needles visual**, independent of the other visual switches. Rebuild/install
  to give skill 500270 private ally/enemy routes with its eleven source-timed needle flashes and one native
  damage reaction. Preserve MP, mechanics, kits, AI and rewards; disabling/rebuilding restores prior behavior.
- Attach the effect to the selected target, destroy it after its tail and pad its clip to prevent loops. Check
  cooked references, event constants and compiled timing before packing. Persist the test setting across other
  switches and old clients; permit an empty-roster test build. Extension 1.2.37 keeps host/install checks aligned.
- Local effect/project/texture/timeline serialization, binding readback and IoStore validation pass. Live
  appearance, placement and repeated casts remain unverified. BMB simulation, deterministic placement without
  native jitter and build-15 Mix/Add materials may differ from FFBE; no replacement is claimed pixel-perfect.

Validation: local analysis, 263 Flutter tests (one Windows-only skip), 423 Python checks (five skips), actual
cooked project/texture/timeline/binding readback, all 8,540 keys/atlas pixels and IoStore verification pass. Windows
validation, compilation, fresh frozen-engine startup and updater/launcher checks pass (423 Python checks, six skips).
Downloaded provenance/checksum and 37 extension resources match; 16 Crystal Fina resources are unchanged.
Preserve extracted source bytes on Windows after its checksum test exposed Git line-ending conversion.
First complete candidate to verified package/source download: **17m 15s**, including corrections and waiting;
successful CI **5m 27s**; all three runs **24m 22s** runner time (23m 33s Windows, 49s Linux), including one stopped retry.

## Published original Cactuar practice encounter — 2026-10-16

Code: [`90ec6b2`](https://github.com/biscoBen/FFR-Vison-Studio/commit/90ec6b277e1c9586c3af778255251d33c8b5c50e).
[Verified Windows test release / run 39011466161](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-39011466161).

- Add a **Practice opponents** dropdown below the enabled **Shop practice battle** switch: the existing three
  level 7–8 enemies or the game's solo level-30 Cactuar encounter. Rebuild/install after selecting. This makes
  the original 1,000 Needles dispatch reachable for runtime comparison without finding Cactuar in the story.
- Clone the native encounter into the existing private practice group/stage, retain Cactuar's own unit/AI/skills
  and preserve normal encounters. Keep guaranteed player escape, native encounter rewards (or the existing MR
  override), no story transition/autosave, and the previous shop dialogue/party. Persist opponents across other
  testing switches, disable/re-enable and older clients' updates. Default to the existing opponents for old configs.
- Cactuar's AI uses the same 500270 ID tested on imported visions; its original enemy presentation was
  unobserved at publication. This adds a diagnostic encounter, not a new effect or verified animation claim.
- Local analysis, 262 Flutter tests (one Windows-only skip), 418 Python checks (five skipped), and both encounter
  choices' native encounter/stage serialization, exact readback and IoStore verification pass. Windows validation,
  compilation, full suites, frozen-engine setup and launcher/updater checks pass for the same commit. Downloaded
  provenance/checksum and all 35 managed extension resources match source; all 16 Crystal Fina resources and the
  existing trace helper remain unchanged.
- Correct Studio's required extension version and fresh-engine test to 1.2.36 after the first Windows startup
  check rejected the newly installed extension. No failed package was published.
- Measured first-complete-candidate to verified download: 18m 54s, including local checks, corrections, the failed
  attempt, cancelled automatic retry and waiting. Successful CI wall time: 5m 31s. Runner job time across all three
  attempts: 22m 14s (Windows 21m 27s; Linux 47s), measured separately from elapsed time.

### Native-only runtime findings — 2026-10-16

- Analyze the returned three-bookmark battle capture, with the user confirming 1,000 Needles, Aqua Breath,
  then Atomic Ray. Both blank casts actually play the game's 900000 "sequencer not set" fallback. Native package
  inspection finds one active `OtherReaction` event, no caster-motion/particle events, no disabled motion tracks
  and no child sequence/effect imports. This explains working combat resolution while the vision stays idle.
- Aqua Breath plays its original 500801 sequence, links its water particle system and runs the imported vision's
  magic motions. The collector captured extension 1.2.35 with matching resource hashes and a native-only build
  report. Its optional skill-ID getter was unavailable, handled once; the user-provided order supplies attribution.
  Installed game containers and original enemy use of the two failed skills were not captured.
- Save the [runtime evidence and limits](README.md#confirmed-runtime-fallbacks) and add both IDs to the shared
  full-release checklist. The other six blank follow-up skills remain unconfirmed by this capture. No new
  presentation is recoverable from the placeholder itself; no donor visual, gameplay change or verified label is
  added by the fallback analysis itself. The package above adds the original-enemy practice comparison.

## Published skill animation runtime trace — 2026-10-16

Code: [`41ea510`](https://github.com/biscoBen/FFR-Vison-Studio/commit/41ea510a6ad9e67a815205392f4647549e5c183b).
[Verified Windows test release / run 39007387217](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-39007387217).
[Standalone helper source/instructions](scripts/reference/skill-runtime/). No Studio update is required.

- Record the follow-up failures for 1,000 Needles, 10,000 Needles, Alluring Pollen, Atomic Ray, Bad Breath,
  Blighted Gloom, Bubble Breath and Carmine Inferno. Audit the three new IDs against the complete returned tables;
  no direct/secondary route is recovered. The native `atk` alias has not resolved this reported batch. Static AI
  assignments do not prove demo availability or portable visuals. No new animation substitute or verified label is added.
- Add the optional Skill Runtime Trace `.cmd`/PowerShell/Lua helper. Through the existing UE4SS installation, sample
  working/waiting jobs, sprite motions, original sequences and active effects on the game thread. Keep job-linked
  effects distinct from global components, record unavailable fields once, support F8 bookmarks/F9 stop, and cap
  the capture. No hooks, native offsets, setters, asset loads or playback changes. Missing samples cannot establish
  absence of playback. Actual Unreal/UE4SS observation still needs the user's live capture.
- Enable/remove only the helper's owned files and reject edited/unknown/linked content. Preserve the loader,
  other mods and Studio runtime. Collect only tagged trace/own-mod startup lines, observer files, DLL hashes and optional engine
  presentation/version hashes into Downloads\FFR Mod. No Studio update or mod rebuild is needed for this helper.
  Existing application/engine resources, settings and accepted gameplay fixes are unchanged.
- Focused observer/lifecycle checks cover missing runtime fields, game-thread queueing, capture limits,
  ownership/path guards, private-log filtering and repeat enable/collect/remove. Normalize Windows short/long
  folder spellings consistently before rejecting capture destinations inside the game; test both alias directions.
  The full local Python suite completes 416 tests (five skipped), and both managed resource manifests verify
  without changes. Lua fixtures and PowerShell lifecycle tests do not verify live UE4SS startup, original enemy
  playback or Unreal rendering.

- Windows validation and compilation pass for the same commit, including the short/long-path regression,
  full Flutter/Python suites, frozen-engine startup and launcher/updater checks. Downloaded provenance/checksum
  matches the commit/run. All 35 existing-vision resources and all 16 Crystal Fina resources match source and
  remain byte-identical to extension 1.2.35. The four-file helper ZIP matches its committed sources and its local
  SHA256. These checks do not establish live UE4SS/game playback; the eight reported skills remain unresolved.
  The standalone ZIP is delivered with the task. GitHub rejected its separate asset upload (HTTP 401); the helper
  source/instructions are committed in the project, and no helper ZIP is attached to the test release.
- First complete candidate to verified helper delivery: **20m47s**, including
  local checks, the Windows path correction, waiting, cancelled retry and verification. Final successful Windows CI:
  **5m34s**; its runner usage: **9m10s**. Total runner usage across all three
  runs: **21m57s**. The initial push run failed its output-path check; the helper's automatic
  retry of that old commit was cancelled. The corrected commit reused its matching automatic run without dispatching
  another build.

## Published native skill routing audit and motion compatibility — 2026-10-16

Code: [`56a9d39`](https://github.com/biscoBen/FFR-Vison-Studio/commit/56a9d39be53f4400a9df88c9adfa50ab0e985286).
[Verified Windows test release / run 39004444107](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-39004444107).

- Extension 1.2.35 corrects the private player effect point for Thwack, Bio and Banishra. El Niño receives a
  private player route using its original shared effect/timing with native friendly aiming/height, and only
  its complete caster track enabled with the supported motion name. Its new enemy route retains the exact
  original shared package/sound; all original shared/native bindings stay intact. Definition, binding,
  package-byte and target-point fingerprints remain mandatory. Combat values and hit/sound schedules are unchanged.
- With Show unverified and either repair mode enabled, generated battle models expose native `atk` as a deep
  copy of that character's own `attack_A`. Escape's existing friendly timeline requests this name. This supplies
  motion compatibility and adds no timeline or substitute effect; it does not establish that unbound skills play.
  Existing clips, atlas/cell/menu data and explicit aliases stay intact. Crystal Fina's optional alias uses her
  accepted shot/mirroring; her existing clips, crystal, glow, seated hold and action timing stay unchanged.
- Add the comprehensive read-only routing collector: timelines, secondary links/callers, battle/skill/unit/encounter
  tables, complete effect libraries and shared materials/textures, battle character projects, camera/postprocess,
  cue metadata and relevant engine/plugin assets. Compare inventory coverage and record native container header
  hashes. Write ordinary upload ZIPs to Downloads/FFR Mod; stream oversized individual files into chunks with
  original length/SHA256 and a restoration ledger. No Studio update or runtime loader is needed for collection.
- All 89 returned ZIPs validate, with all 7,130 expected assets and four exactly restored large files. Every one
  of the 2,819 overlapping native files and the mapping matches the prior reference. Decode 233 tables, two
  sequence-event blueprints, 258 AI blueprints and ten original monster projects with no failures. Correct UTF-8
  native-output decoding in the collector: 17 Unicode names had been misreported missing; all files were present.
  No rerun is required. Record the [routing evidence](docs/native-skill-routing-findings.json) and full-game follow-ups.
- Secondary links do not supply visual routes for the twelve blank skills in the Agrias/Alaya test batch.
  Some are assigned to native enemies, but assignment is not proof of demo availability or portable presentation.
  All twelve matching-number master candidates are already bound to other current skills and are not blindly
  reclaimed. Record the user's successful Absolute Zero/Bioblaster retest and unchanged correct Aqua Breath.
  No new skill is automatically labeled verified, and borrowed visuals remain a separate option.
- Local analysis and the full Flutter suite pass (260 passed, one Windows-only skip); the Python suite completes
  404 tests (four skipped). Real converter tests preserve existing clips, atlas pixels and menus. Native SS6
  serialization/readback confirms the exact recipient attack alias. All 23 private player routes (92 packages),
  both retained enemy routes, 25 added bindings per lookup, and exact event/track edits pass actual native
  serialization/readback and IoStore verification. New in-game appearance still needs live tests.
- Windows validation and compilation pass for the same commit, including full suites, frozen-engine startup
  and launcher/updater checks. Downloaded provenance/checksum and all 35 managed resources match source.
  Accepted Fina runtime/material/preview, cave, party knockout and icon renderer bytes are unchanged; the
  Fina motion adapter only recognizes the optional new alias, with all prior clips preserved by regression checks.
- First complete candidate to verified download: **10m48s**, including local
  verification, converter-fixture corrections, waiting and package verification. Windows CI: **5m24s**;
  runner usage: **9m42s**. One matching automatic run was reused; no duplicate build was dispatched.

## Published native skill facing and diagnostics — 2026-10-16

Code: [`e3f73bf`](https://github.com/biscoBen/FFR-Vison-Studio/commit/e3f73bf1e667f3ef66732d4877bd897b0e4a8675).
[Verified Windows test release / run 38996274544](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38996274544).

- Correct native Bioblaster's private player timeline to aim at the enemy-side point. Give Absolute Zero
  player/enemy routes and remove its forced enemy-sequence pointer; correct only the private player effect's
  location, using native player placement. Its enemy route retains the original enemy package and sound.
  The same native effects and timings are used; MP, damage, status effects, targeting and hit counts are unchanged.
  These repairs run with either repair checkbox, when Show unverified is on and the skill is selected.
  Existing custom presentations and future native routes take precedence. Extension 1.2.34.
- Fingerprint both native battle target points as well as definitions, bindings and package bytes. The normal
  verifier accepts only the exact audited presentation-pointer edit after a successful repair; changed source
  data, skipped repairs and unrelated mechanical changes remain rejected. All 22 player routes and the retained
  enemy route pass actual native serialization/readback and IoStore verification; both facing fixes need live tests.
- Native-only reports distinguish entries with no direct binding or explicit sequence pointer from existing
  routes. They add no substitute effects. Record the alphabetical test batch on Agrias/Alaya Rundall, including
  MP/LB skips and direction problems, in the [animation compatibility report](docs/MONSTER_ANIMATION_COMPATIBILITY.md).
  Aqua Breath is user-confirmed correctly aimed and stays unchanged; the remaining blank skills need investigation.
- Add the standalone read-only skill-effect collector. It gathers native particle/mesh assets and installed
  Studio routes, allowlisted flags/grants and the latest repair report under Downloads/FFR Mod. Temporary
  container links/copies supply the native global index and are removed before upload ZIP creation. Fix
  PowerShell 5.1 array enumeration for empty/single/multiple rosters; record the selected engine/game paths.
  The returned two-part collection has 63 native assets and no extraction failures. The installed mod is from
  a different computer than the original test and cannot identify the route used in that battle.

- Cancel the notice-expiry timer when Studio's state is disposed, fixing the delayed callback caught by
  Windows validation. Repeating the same notice now gives it a fresh six-second duration. Add focused
  disposal/expiry regression checks. The same-computer follow-up confirms native-only flags, Bioblaster's
  player route still aimed at the party and Absolute Zero's forced enemy pointer.
- Local analysis, 58 focused Flutter tests and the full Flutter suite (260 passed, one Windows-only skip) pass.
  The full Python suite completes 395 checks (four skipped).
  Checks cover exact pointer authorization, mechanical-field rejection, future/custom/changed-source guards,
  native-only report distinctions and existing mode isolation. Collector fixture checks include PowerShell 5.1
  array behavior, temporary-copy fallback, partial failures, ZIP splitting, output guards and source immutability.

- Windows validation and compilation pass for the same commit, including all Flutter/Python tests,
  frozen-engine setup and launcher/updater checks. Downloaded provenance/checksum and all 35 managed resources
  match source. Accepted Fina, cave, party knockout, sprite converter and icon renderer bytes are unchanged.
- First complete candidate to verified download: **21m24s**, including
  native asset checks, the Windows-discovered notice timer fix, extra/cancelled runs, waiting and verification.
  Final Windows CI: **5m38s**; final runner usage: **8m15s**.
  Total runner usage across all attempts: **26m05s**. The build helper briefly
  dispatched a duplicate before the automatic run became visible; that run was cancelled. Its automatic retry
  of the validation failure was cancelled after the corrected commit superseded it. The final matching
  automatic run was reused and its original package identity retained.

## Published native-only testing and audited skill bindings — 2026-10-16

Code: [`aa0452b`](https://github.com/biscoBen/FFR-Vison-Studio/commit/aa0452bae51eaf2e757f6e8c180f2a95e238ad16).
[Verified Windows test release / run 38986188584](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38986188584).

- Add an independent **Repair native skill bindings / motions** testing checkbox. With Show unverified skills
  on and Use our skill changes off, apply only audited same-skill repairs: Cling plus 20 additional demo entries.
  Keep donor effects, generic fallback timelines, Barrage trials and reviewed hiding rules off in this mode.
  Remember all three flags across restarts; old settings default the new checkbox off. Extension 1.2.33.
- Include a read-only collector for all native battle timelines, skill routing tables, game mapping and asset
  inventory. Separate upload ZIPs go to Downloads/FFR Mod; no runtime loader or installation changes.
  The returned five-part reference contains 1,407 assets. Borrowed Sephira preset visuals remain a separate
  switch and should also be off for a clean native-only test; saved kits and explicit custom presentations stay intact.
- Audit 1,370 sequence packages and 277 directly bound raw catalog entries. Add 20 own-source player routes
  alongside Cling, including native monster abilities and group spells. Nine of the new entries need motion/track
  repairs; enable only their audited complete caster tracks and translate exact `atk` events to `attack_A`.
  Preserve unused tracks, all effect/audio/hit constants and every original table row. Fingerprint the skill definition,
  both source bindings and all package bytes; changed inputs skip the repair and report why. Future native routes
  and explicit custom presentations take precedence. Existing routes and entries without direct bindings stay intact.
  Only Cling has live confirmation; the additional 20 entries need game testing.
- Local analysis, 58 focused Flutter tests and 393 Python checks pass. Tests cover native-only isolation,
  settings migration/persistence, independent UI flags, build guards, exact motion exports/track selection,
  future native/custom precedence and changed definition/binding/package rejection. All 21 routes pass
  real native serialization/readback and IoStore verification, retaining original lookup rows and hit/effect/audio
  constants. The collector's quoted-path, output-guard, partial-failure and source-immutability smoke checks pass.
  Independently extracted references match across all 87 overlapping files. Windows validation and compilation
  pass for the same commit, including full suites, frozen-engine startup and launcher/updater. Downloaded
  provenance/checksum and all 35 managed resources match source. Accepted Fina, cave, party knockout,
  sprite converter and icon renderer bytes remain unchanged.
- First complete candidate to verified final download: **21m22s**, including the
  full reference upload/audit, expanded repairs, checks, both builds, waiting and verification. The initial isolated-mode
  run took **5m11s**; final Windows CI took **5m42s**.
  Combined runner usage: **17m52s** across the two runs. Joined each matching automatic
  run; no duplicate workflows dispatched. The final package adds the audited batch to the initial toggle build.

## Published Cling ally animation and native vision icons — 2026-10-16

Code: [`6aa315f`](https://github.com/biscoBen/FFR-Vison-Studio/commit/6aa315f93b773d7cc5dbb22e7b5792b270c1a1c1).
[Verified Windows test release / run 38982081785](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38982081785).

- Add a missing ally timeline for Cling using its original all-target effects, hit timing and audio.
  Enable only its audited caster track and map enemy `atk` to imported `attack_A`; keep original game
  bindings and combat values. Requires Show unverified skills and Use our skill changes. Generic audited
  group-skill reuse now creates a player route rather than confusing caster-side suffixes with target count.
  Native roundtrip/readback and IoStore pass; the repaired Cling presentation needs a live multitarget test.
- Mark the five user-confirmed monster animations (Whip, Tentacle, Sonic Boom, Bite and Incisors) as
  **Verified; demo test**, tied to their exact catalog definitions. Cling remains unverified pending testing.
- Give imported vision face/timeline/ability icons native game frames without the blue backing or FFBE
  rarity badge. Preserve portrait layout controls and use the same renderer in the advanced preview.
  Rebuild/install to update existing game icons. Extension 1.2.31.
- Include the read-only monster-animation reference collector, writing only under Downloads/FFR Mod.
- Local analysis, 44 focused Flutter tests and 389 Python checks pass. Tests cover ally-only additions,
  future-native/custom precedence, changed-track rejection, group caster routes, exact live-test labels,
  native icon frame preservation, clipping, converter output and startup resource staging. Native Cling
  Master/Cut/Effect/Sound cloning, table readback and IoStore verification pass. Windows validation and
  compilation pass for the same commit, including full suites, frozen-engine startup and launcher/updater.
  Downloaded checksum/provenance and all 33 managed resources match source. Accepted Fina battle/cave
  presentation and party replacement knockout assets remain unchanged. Cling's new presentation and native
  icon appearance still need live confirmation.
- First complete candidate to verified download: **8m22s**, including startup
  resource-allowlist corrections, checks, waiting and verification. Windows CI took **5m55s**,
  using **9m23s** of runner time. Joined the matching automatic run; no extra build dispatched.

## Published automatic Crystal Fina cave presentation — 2026-10-16

Code: [`2f9db41`](https://github.com/biscoBen/FFR-Vison-Studio/commit/2f9db41b5418b5c577e08893175084b908b010b5).
[Verified Windows test release / run 38978026068](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38978026068).

- Remove the standalone Crystal Fina cave/Test switches from Studio. Assigning her to any cave through
  Acquisition now automatically includes the finished introductory sprite, rotating transparent crystal,
  approved size/material and normal cave acquisition/return flow. Other cave visions keep their appearance.
- Migrate an enabled old switch to an explicit original-cave assignment when Fina has no saved choice,
  then retire the switch. Preserve existing shops/caves, edited kits and disabled collections; do not
  recreate removed profiles. Save failures keep a retryable state and stop the build. Extension 1.2.30.
  The new assignment route needs a live game test.
- Local analysis, 75 focused Flutter tests and 381 Python checks pass. Coverage includes shared caves,
  allocated reward IDs, original/shop/custom choices, disabled collections, removal, migration retries and save
  failures that block builds. Native casing mesh/material, component binding and rotation sequence roundtrips
  and IoStore verification pass. Full native NPC reconstruction is not exercised by that probe because the reference
  omits its Blueprint parents; table routing is covered by regressions. Windows validation and compilation pass
  for the same commit, including full Flutter/Python suites, frozen-engine startup and launcher/updater checks.
  Downloaded checksum/provenance and all 31 managed resources match source. Battle appearance/timing bytes match
  the accepted release. The user also confirmed the previous party-knockout update looks good.
- First complete candidate to verified download: **8m53s**, including a migration
  edit-preservation guard, checks, waiting and verification. Windows CI took **5m28s**, using
  **9m00s** of runner time. Joined the matching automatic run; no extra build dispatched.

## Published party replacement knockout motions — 2026-10-16

Code: [`9275ab7`](https://github.com/biscoBen/FFR-Vison-Studio/commit/9275ab78afd923afb3259bb2ac1b40e031637fb4).
[Verified Windows test release / run 38973264709](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38973264709).

- Fix party battle replacements staying upright after knockout: map the selected sprite's `dead` clip
  to the native `death` name used by all eight party members, including Lasswell's reverse stance.
  Keep the selected/base-form artwork, frame timing and offsets; native death/revival logic stays in control.
  Extension 1.2.29. Live knockout/revival testing remains pending.
- Include the read-only party-knockout reference collector under Downloads/FFR Mod. The returned references
  confirmed the motion-name mismatch; no runtime loader is needed for this fix.
- Local analysis, 41 focused Flutter tests and 380 Python checks pass. Native generation/readback covers all
  eight party packs across four regular Cleome rarities, with separate standing/knockout cells and verified IoStore.
  Regression checks cover complete fall/held clips, base-form cells/offsets and unchanged idle recovery. Windows
  validation and compilation pass for the same commit, including full Flutter/Python suites, frozen-engine startup
  and launcher/updater checks. Downloaded checksum/provenance and all 31 managed resources match source.
  Accepted Crystal Fina gameplay, runtime and preview bytes match the previous release.
- First complete candidate to verified download: **8m08s**, including checks,
  waiting and verification. Windows CI took **6m02s**, using **10m32s** of runner
  time. Joined the matching automatic run; no extra build dispatched.

## Published standalone Crystal Fina and gentler attacks — 2026-10-16

Code: [`bde5f38`](https://github.com/biscoBen/FFR-Vison-Studio/commit/bde5f3848bfa40d6720ed55ab3b813acab5c82a4).
[Verified Windows test release / run 38968721767](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38968721767).

- Slow Crystal Fina's normal attack another 20% from the accepted build (0.64× native speed). Keep the
  owning hit/effect/sound clocks aligned and preserve the approved crystal, resonance and seated hold.
  Render the 1.5625-second Studio cast with fractional timing rather than rounding the native SS6 frame rate.
- Disabled Sephira entries no longer count as active duplicates in the Add picker. Add can move saved Crystal
  Fina into Added Visions, preserving her identity, edited kit and acquisition, without enabling the collection.
  Re-enabling an initialized collection retains that independent entry. An already active Fina remains blocked;
  other active FFBE units use an explicit “Add another” button. Save failure retains the original entry and
  concurrent edits survive the transfer. The Add preview shows the saved stats it will retain.
  Extension 1.2.28, preview native-fina-10.
- Local analysis, 66 focused Flutter tests, 377 Python checks and native build/readback/IoStore verification pass.
  Tests cover active/off duplicate badges, standalone transfer, later collection toggles, cave activation, saved
  stats, save failure and concurrent edits. Idle/resonance preview bytes match the accepted build. Windows
  validation and compilation pass for the same commit, including full Flutter/Python suites and frozen-engine
  startup. Downloaded checksum/provenance and all 31 managed resources match source. Live pace testing is pending.
- First complete candidate to verified download: **11m06s**, including a saved-stat
  preview correction, checks, waiting and verification. Windows CI took **7m05s**, using
  **11m12s** of runner time. Joined the matching automatic run; no extra build dispatched.

## Published Crystal Fina gentler attack and matching clocks — 2026-10-16

Code: [`7a97ee0`](https://github.com/biscoBen/FFR-Vison-Studio/commit/7a97ee07d7bfc3f1078d150be7f777b3c902f5f9).
[Verified Windows test release / run 38964077148](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38964077148).

- Slow Crystal Fina's normal attack phases to 80% speed (25% more time) together with the linked native
  action timelines, hit/effect sequence and sound player. Preserve damage values, accepted glass/refraction,
  resonance, and the 1.25-second seated hold. Restore original rates on recovery, missing jobs or cleanup;
  preserve native speed when no linked clock is available. Extension 1.2.27, preview native-fina-9.
- Reflected job/owner fields are checked against the supplied game mapping. Executable runtime fixtures cover
  matching event/body clocks, unrelated targets, linked owners, game speed, noncompounding updates, recovery,
  missing clocks and API failure. Live native clock association and perceived timing still need an in-game test.
- Local static analysis, 20 focused Flutter tests, 377 Python checks and native asset/readback/IoStore verification
  pass. Windows validation and compilation pass for the same commit, including full Flutter/Python suites and
  frozen-engine startup. Downloaded checksum, commit/run provenance and all 31 managed resources match source.
- First complete candidate to verified download: **8m54s**, including a pause-clock
  guard correction, checks, waiting and verification. Windows CI took **5m26s**, using
  **8m57s** of runner time. Joined the matching automatic run; no extra build dispatched.

## Published Crystal Fina body refraction and single resonance glow — 2026-10-16

Code: [`eba9b3c`](https://github.com/biscoBen/FFR-Vison-Studio/commit/eba9b3c93457d1b7b709694505d8ae319f1366a1).
[Verified Windows test release / run 38955704470](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38955704470).

- Remove Crystal Fina's authored second resonance glow (frames 210–282), which lit the socket while she was seated.
  Keep only the early pulse through frame 164, then hide/destroy it. Preserve attack timing, mirroring, rotation and
  the accepted 1.25-second seated hold. Refresh Studio previews/cache (native-fina-8), extension 1.2.26.
- Replace ineffective depth-scale normalization with camera-to-native-mesh ray measurements at five head-to-feet
  probes. Target 20% refraction at the deepest probe using the shader's actual depth-gate equation, retaining
  background refraction and the accepted surface settings. Record applied/read-back bias, view depth and camera FOV.
  The supplied 12:13 trace confirms the old update ran but changed bias only to 12.08664 because world depth scale
  was nearly the cave's. That disproves the prior large-scale explanation. Actual body clarity still needs live testing;
  CPU probe geometry is not a GPU depth-buffer readback or an exact cave-camera match.
- Local static analysis, 20 focused Flutter tests, 371 Python tests and the real native build/readback/IoStore
  checks pass. Tests cover original LOD0 decoding, rotated/nonuniform transforms, overlapping shells, the deeper
  lower body, camera fallback, range caps and no seated/reformation pulse. Windows validation and compilation pass
  for the same commit, including full Flutter/Python suites and frozen-engine startup. Downloaded checksum,
  commit/run provenance and all 31 managed resources match source.
- First complete candidate to verified download: **9m09s**, including a front-hit
  correction, checks, waiting and verification. Windows CI took **5m18s**, using
  **9m14s** of runner time. Joined the matching automatic run; no extra build dispatched.

## Published Crystal Fina scaled glass and final glow cleanup — 2026-10-16

Code: [`4e871bc`](https://github.com/biscoBen/FFR-Vison-Studio/commit/4e871bc9efd4709f35674527b201ef8347e16006).
[Verified Windows test release / run 38950607802](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38950607802).

- Match Crystal Fina's battle refraction depth gate to the crystal's actual inherited world scale. Use an owned
  dynamic material instance and the accepted cave's depth/scale reference; retain its surface settings and rotation.
  Log the measured depth scale and calculated bias instead of selecting another fixed battle-only value.
- Destroy the resonance aura as soon as its final fade finishes, and latch completion through native frame resets
  and temporary animation-name gaps. A later genuine resonance can light normally. Preserve the accepted attack,
  early glow, facing and 1.25-second seated hold. Extension 1.2.25; live battle clarity/flash confirmation is pending.
- Windows validation and compilation pass for the same commit, including full Flutter/Python suites and real
  frozen-engine startup. Local analysis, 20 focused Flutter tests, 367 Python tests and native build/readback/IoStore
  checks pass. Regression fixtures cover scaled depth gating/range caps, late frame resets, animation-name gaps,
  expired seated emitters and a later resonance. Downloaded checksum/provenance and all 31 managed resources match.
- First complete candidate to verified download: **8m37s**, including checks,
  waiting and verification. Windows CI took **5m55s**, using **9m47s** of
  runner time. Joined the matching automatic push run; no extra build dispatched.

## Published Crystal Fina short attack and early resonance glow — 2026-10-16

Code: [`1e679ba`](https://github.com/biscoBen/FFR-Vison-Studio/commit/1e679baeca155bdd131852154f04f9017f18980c).
[Verified Windows test release / run 38946295996](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38946295996).

- Fit Crystal Fina's eye-opening, turn and charge into native attack preparation; start her shot with native
  release and return to idle on the game's existing schedule. Remove the long independent runtime cast, preserving
  damage/effect timing. Refresh the Studio preview (native-fina-7) and extension 1.2.24.
- Start her brighter, body-centered resonance glow immediately during preparation. Fix the preparation attachment
  being parked offscreen; keep the native particles warm through the seated interval and glow before reformation.
  Preserve the accepted **1.25-second** seated hold, facing and cave presentation.
- Use the accepted cave glass parameters for battle too, removing the battle-only refraction depth override that
  made the casing appear behind her. Native/API and regression checks cover authored timing and resource integrity;
  battle lighting/refraction and the exact perceived impact still require an in-game test.
- Windows validation and compilation pass on the same commit, including full Flutter/Python checks and real
  frozen-engine startup. Local analysis, 20 focused Flutter tests, 365 Python tests and native asset/readback/IoStore
  checks pass. Confirmed 30-frame preparation/release, supported mirrored cells, the accepted seated hold and every
  cave glass scalar in the native battle material. Downloaded checksum/provenance and all 31 managed resources match.
- First complete candidate to verified download: **7m58s**, including a preview
  version-check correction, checks, waiting and verification. Windows CI took **5m22s**, using
  **9m11s** of runner time. Joined the matching automatic push run; no extra build dispatched.

## Published Crystal Fina battle presentation fixes — 2026-10-16

Code: [`d764d9b`](https://github.com/biscoBen/FFR-Vison-Studio/commit/d764d9baad0e2993c6ad77d5ddb0f417a53efb1c).
[Verified Windows test release / run 38938932251](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38938932251).

- Fix Crystal Fina's full cast being canceled by native `Idle` recovery after roughly half a second. Normalize
  animation/pack names with Unreal's case-insensitive FName semantics; preserve the approved 229-frame turn/shot.
- Replace ignored SS6 `Fliph` tracks with supported `Imgfliph` tracks for attack and resonance. Verify the native
  attribute and boolean fallback cache, and refresh the Studio preview/cache revision (extension 1.2.23).
- Preserve the real intro glow through native package cloning. The former JSON rebuild discarded Niagara variable
  names/offsets and renderer bindings despite passing JSON readback. Require byte-identical source/cloned export
  data. Fade `NiagaraAlpha` as the native intro does, center the effect without its +80 UU intro offset, and suppress
  its native lights with the owned component's `LightPower` override.
- Reduce distortion of the body inside the private battle glass by increasing its refraction depth bias from 12 to 24.
  Preserve the accepted cave material, surface/facet settings and **1.25-second** seated hold. Source/API checks,
  native readbacks and regression fixtures do not replace an in-game visual test.
- Windows validation and compilation pass on the same code, including the full Flutter/Python suites and frozen-engine
  startup. Local analysis, 20 focused Flutter tests, 365 Python tests and real native build/readback/IoStore checks pass.
  Verified the private glow's 117,357 export bytes against the original, supported mirror keys/bool caches and battle
  material depth bias. The downloaded ZIP checksum, commit/run provenance and all 31 managed resources match source.
- First complete candidate to verified download: **7m28s**, including checks, waiting and verification. Windows CI took
  **5m01s**, using **8m34s** of runner time. Joined the matching automatic push run; no extra build dispatched.

## Published Crystal Fina animation-output crash fix — 2026-10-16

Code: [`8fd2cb1`](https://github.com/biscoBen/FFR-Vison-Studio/commit/8fd2cb195b56d571fcd6b59a028a21fc01215831).
[Verified Windows test release / run 38933124386](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38933124386).

- Set Crystal Fina's seated resonance hold to exactly **1.25 seconds** (75 native frames), with reformation/glow
  timing and Studio previews moved together. Preserve the accepted cave presentation. Bundled extension 1.2.22.
- Fix the battle-runtime failure identified by the supplied UE4SS log: the real crystal attached successfully,
  then reading a hardcoded animation-output field returned nil and cleanup removed the crystal and disabled the
  glow/full cast. Read both reflected output names in one table and identify the verified private pack by its value,
  independently of parameter spelling/order. Keep the casing and retry when names are temporarily unavailable.
  Log the actual output fields once to make future runtime differences diagnosable.
- Add a read-only **Collect Fina Runtime Diagnostics.cmd** helper. It collects only the allowlisted loader log/settings,
  installed Studio Lua scripts and built runtime metadata, hashing DLLs without uploading them. Output stays in
  **Downloads\FFR Mod**. Regression checks cover renamed/reordered outputs, startup gaps, full-cast recovery,
  glow/casing timing and cleanup. Live rendering after the correction still needs the user's in-game test.
- Windows validation and compilation pass on the same code, including the full Flutter/Python suites and frozen-engine
  startup. Local analysis, 20 focused Flutter tests, 362 Python tests, real native readback/IoStore checks and the
  read-only collector fixture pass. The downloaded ZIP checksum, exact commit/run provenance and all 31 managed
  resources were verified against source. The supplied installed script exactly matches the preceding release,
  ruling out a stale install as the cause.
- First complete candidate to verified download: **8m13s**, including corrections, checks, waiting and verification.
  Windows CI took **5m48s**, using **9m21s** of runner time. Joined the matching automatic push run; no extra build dispatched.

## Published direct Crystal Fina battle runtime — 2026-10-15

Code: [`ff2cedd`](https://github.com/biscoBen/FFR-Vison-Studio/commit/ff2cedd52cc4aca99db87fb25739fa89401a7f3a).
[Verified Windows test release / run 38861705226](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38861705226).

- Replace Crystal Fina's non-rendering battle casing/sequence-glow route with direct, battle-only mesh and Niagara
  attachments through the existing UE4SS loader. Reuse Studio's owned runtime deployment/restore and Deck transfer;
  walking-character cycling can stay off. Require the working loader before installing. Preserve the accepted cave.
- Observe actual SpriteStudio clips and keep the approved full 229-frame cast through native early recovery calls.
  Preparation only opens her eyes, eliminating the duplicated curled-up turn. Mirror attack/resonance body tracks;
  reduce the seated hold from 125 to 100 frames. Drive crystal visibility and body-centered glow alpha from LB1 frames.
- Resolve private mesh/material/glow packages through Unreal soft-path loading rather than the original asset registry,
  and reload collected glow assets before reuse.
- Refresh native Studio previews/cache revision and bundled extension 1.2.21. Native asset and executable Lua fixture
  checks cover serialization, scope, interruption, pulse timing, private package loading, asset collection and cleanup.
  Both Windows validation and compilation pass on the final commit, including the full suite and frozen-engine startup.
  Download checksum, exact commit/run provenance and all 31 managed resources were checked against source. Live Unreal
  rendering still needs an in-game test; binary and simulated runtime checks do not establish visual correctness.
- First complete candidate to verified download: **26m47s**, including the loading correction, checks, both builds,
  waiting and verification. Final Windows CI took **7m41s** and **11m25s** of runner time; both automatic runs combined
  took **12m53s**, using **20m09s** of runner time. Joined matching push runs; no duplicate build dispatched.

## Published Crystal Fina cave and battle corrections — 2026-10-15

Code: [`2976d53`](https://github.com/biscoBen/FFR-Vison-Studio/commit/2976d53b01edcd3809e0139903125fe25effdac0).
[Verified Windows test release / run 38855894137](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38855894137).

- Remove the old side-by-side Crystal Fina cave comparison and enlarge the native Fina/glass pair by 15%, retaining
  the approved material and slow rotation. Update the cave toggle's description.
- Fix missing battle attachment model parts and inherited body offsets. Author and verify the SS6 model hierarchy;
  append the casing component renderer while retaining the native MeshRendererInfo dependency's original class/data.
  Disable other casing-system renderers explicitly. Idle has only the crystal, with no persistent golden aura.
- Complete normal casting/release motion in a shorter presentation window. Use the replacement duration in animation
  repair, preserving native gameplay event timing. Resonance spawns/fades/destroys native body-centered glow pulses
  around crystal disappearance and reappearance; restore the floating crystal after a seated hold about half as long.
- Refresh native Studio previews/cache revision and bundled extension 1.2.19. Native model/renderer/VM readbacks, cooked glow-event checks and
  IoStore packing/verification pass. Local Python checks, Flutter analysis and focused UI tests pass. Windows validation and compilation
  passed on the same commit, including the full Flutter suite, real frozen-engine startup/import, Python and launcher
  checks. Verified the downloaded ZIP checksum, commit/run provenance and all 30 managed resources against source.
  Live battle rendering still needs an in-game test.
- First complete candidate to verified download: **13m17s**, including corrections, checks, waiting and verification.
  Windows CI took **4m13s**, using **7m22s** of runner time. Joined the automatic push run; no extra build dispatched.

## Published Crystal Fina scale fix and Studio previews — 2026-10-15

Code: [`b3e9d0a`](https://github.com/biscoBen/FFR-Vison-Studio/commit/b3e9d0a30ca2a8b3d47ef439c3b4fe4f105e5bb7).
[Verified Windows test release / run 38847946131](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38847946131).

- Fix Crystal Fina builds failing with "The native sprite/effect battle scales are invalid." Read her fresh built
  design row instead of requiring positive donor values. Fill only nonpositive scale fields with explicit native-presentation
  values, preserve positive scales and other rows, and size the casing from the same values written to the game.
  Reject nonfinite/unsupported data with field/value details; canonicalize authored floats for native readback checks.
- Update Studio's Crystal Fina animation viewer and selector to show the native sprite inside crystal geometry, the
  eye-opening/turn/cast attack and the glowing fall/seated resonance. Include verified previews offline, bypass old
  FFBE preview files and revise Flutter's image-cache identity. Label the software preview's lighting difference.
  Bundled extension 1.2.18; existing kits, menu portraits and the cave comparison remain intact.

- Validation: clean analysis, 246 Flutter tests (one skip), the separate fresh frozen-engine startup check,
  358 Python checks (Windows: five skips; Linux: four), managed bundles, 12 launcher and 10 import checks passed.
  The frozen runtime opens the bundled animated WebP and verifies its native-preview API/header. Regressions cover
  nonpositive scales, preservation of unrelated rows/fields, invalid values, stale preview bypass, party-model fallback,
  image cache revision, navigation, decoded durations and disappearance of the crystal before the seated ending.
  Native integration builds and strictly reads back a zero-scale design-table fixture with the private battle assets;
  IoStore packing/container verification also pass. The original user game data is not replaced by test fixtures.
  Verified the package SHA-256, commit/run provenance and all 30 managed manifest entries against source. The software
  Studio preview is labeled; actual battle rendering/rotation and glass lighting still need an in-game test.
- First complete candidate to verified download: **10m29s**, including corrections, checks, waiting and verification.
  Windows CI took **5m40s**, using **9m19s** of runner time. Joined the automatic push run; no extra build dispatched.

## Published native Crystal Fina battle test — 2026-10-15

Code: [`bb2a737`](https://github.com/biscoBen/FFR-Vison-Studio/commit/bb2a7372d24c62c2e15deadc5aa27deaf9c3a673).
[Verified Windows test release / run 38843855920](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38843855920).

- Replace custom Crystal Fina's battle body with the native introductory sprite inside a private copy of the approved
  Sanctum glass. Attack opens her eyes, turns and casts; resonance uses the native intro aura, hides the casing at
  frame 134, descends and holds the original jacket-free seated pose. Fit ordinary action bodies to their existing
  clip durations; preserve skills, hit/healing events, stats, vision identity, menu assets and saved edits.
- Attach the casing/aura through the actual per-unit battle effect table. A CPU Niagara component renderer owns one
  non-colliding static-mesh casing and retains the approved cooked glass shader. SS6 attachment tracks carry turning
  and resonance visibility. The original cave comparison and its approved glass/turn sequence remain unchanged.
  Bundled extension 1.2.17. Native asset generation/readbacks pass; battle rendering, attachment rotation inheritance,
  effect cleanup and perceived timing still need an in-game check.
- Keep read-only battle-reference collectors and a shared native SsValue decoder/body-preview tool in the project.
  Collectors write to Downloads\FFR Mod. Evidence and runtime limits are recorded in `docs/CRYSTAL_FINA_BATTLE.md`;
  the full-game checklist includes the new per-unit attachments, shader/scale dependencies and seated fallback.

- Validation: clean analysis, 244 Flutter tests (one skip), the separate fresh frozen-engine Windows startup check,
  354 Python checks (Windows: five skips; Linux: four), managed bundles, 12 launcher and 10 import checks passed.
  Native integration generated the private SS6 project/textures, component-renderer system, glass/mesh and battle tables;
  strict readbacks and custom-value decoding confirm their contents. The supplied original assets remain untouched.
  A checksum-verified upstream retoc 0.1.5 also packed the generated assets as UE5.6 IoStore and verified the container,
  including its streamed mesh bulk data. This is an asset/build check, not a live battle-rendering test.
  Verified the published ZIP's SHA-256, exact commit/run provenance and all 28 managed manifest entries against source.
- First complete candidate to verified download: **10m08s**, including local checks, corrections, waiting and package
  verification. Windows CI took **6m34s**, using **10m06s** of runner time. Joined the automatic push run; no extra build.

## Published Crystal Fina side-by-side comparison — 2026-10-15

Code: [`aee9e8c`](https://github.com/biscoBen/FFR-Vison-Studio/commit/aee9e8c6411a5516b11a31a93406bc64aeb4b0a8).
[Verified Windows test release / run 38829455821](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38829455821).

- Crystal Fina Test now shows the original imported Crystal Fina beside the native introductory Fina in rotating
  Sanctum glass, using the old sprite's original material, size and floating offset. The comparison has a separate
  streamed NPC level and asset identity, follows the same ownership condition and has no acquisition prompt or reward.
  The existing vision, acquisition and cave return remain shared; the new crystal stays at its approved location.
- Remove Solid casing check and Animate crystal casing from the home screen and saved settings. Test mode always
  uses the approved transparent glass and working rotation; accept/discard those old settings during migration.
  Keep the original cave and Test switches mutually exclusive. Bundled extension 1.2.16. Comparison spacing needs a
  live check; the current glass and rotation are user-approved and their asset generators are unchanged.
- Validation: clean analysis, 244 Flutter checks (one skip), the separate fresh frozen-engine Windows startup check,
  347 Python checks (Windows: five skips; Linux: four), bundle verification, 12 launcher checks and 10 import checks
  passed. Tests cover distinct old/new sprite identities, original scale/pose/material, ownership visibility, a single
  grant, fixed rotation and migration from the removed switches. Strict native roundtrips pass for the glass, mesh,
  turn sequence and both casing attachment graphs; their asset binaries match the previous approved version exactly.
  Verified the ZIP's SHA-256, commit/run provenance and all 26 manifest entries plus the manifest against source.
  Side-by-side spacing still needs an in-game check.
- First complete candidate to verified download: **7m18s**, including local checks, waiting and
  verification. Windows CI took **5m37s**, using **9m12s** of runner time.
  Reused the automatic push run; no extra build dispatched.

## Published uniform Crystal Fina glass restoration — 2026-10-15

Code: [`9e70734`](https://github.com/biscoBen/FFR-Vison-Studio/commit/9e70734080492100c04657afd97e633300ed4d5b).
[Verified Windows test release / run 38826297629](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38826297629).

- Restore the approved Crystal Fina glass across the whole casing after the tip-only material experiment produced
  dark end caps. Use the native single-section mesh with every original opaque render byte and bulk companion intact.
  Generate only the main glass/solid material; remove the extra tip normal texture and material regions. Preserve
  the approved .22 opacity, .80 Fresnel, .10 roughness and refraction bias 12.
- Keep the unique rotation track/section names, fixed size and grounded attachment: live testing now confirms the
  crystal spins correctly. The old tip codec remains unused for managed-file compatibility and format reference.
  Rebuild/install with Solid casing check off and Animate crystal casing on. The restored tips need an in-game check.
  Bundled extension 1.2.15.
- Validation: clean analysis, 244 Flutter checks (one skip), the separate fresh frozen-engine Windows startup check,
  346 Python checks (Windows: five skips; Linux: four), bundle verification, 12 launcher checks and 10 import checks
  passed. Native material/mesh/sequence and both component graphs passed strict roundtrips. The glass material and
  turn sequence (both .uasset/.uexp) are byte-identical to the respective live-approved references; the mesh's opaque
  render data matches the native source exactly and has one material slot. Verified the ZIP's SHA-256, commit/run
  provenance and all 26 manifest entries plus the manifest against source. Final appearance still needs a live check.
- First complete candidate to verified download: **7m14s**, including local checks, waiting and verification.
  Windows CI took **5m18s**, using **9m06s** of runner time. Reused the automatic push run; no extra build dispatched.

## Published Crystal Fina turn and tip detail correction — 2026-10-15

Live follow-up: the user confirms spinning works, but the tip-only regions render dark. The correction above removes
that visual experiment and preserves the working turn. Native geometry/serialization checks did not predict this
material/rendering failure.

Code: [`dc5a01d`](https://github.com/biscoBen/FFR-Vison-Studio/commit/dc5a01de36365d95f314a3404d3a43036a44146a).
[Verified Windows test release / run 38823829616](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38823829616).

- Correct Crystal Fina Test's rotation package: the appended turn track reused an existing cutscene track's object
  name under the same MovieScene. Give the new track and section unique names, revise signatures and reject duplicate
  cooked object identities before writing/after readback. The retained donor contains off-stage/zero-scale transforms;
  a property roundtrip alone did not detect that ambiguous runtime path. Live rotation still needs confirmation.
- Preserve the approved central glass and add subtle native crystal normal detail (.04) only at the outer tips.
  Partition all three native LODs into central/tip material sections, retaining every triangle, vertex, tangent, UV,
  winding, bound, physics body and bulk companion. Align the depth-only triangles by oriented geometry and retain GPU
  buffer sizes. Reject unrecognized layouts; record this dependency in the full-game checklist. The circled patch has
  no open mesh edge; leave its central glass unchanged while assessing it in motion.
- Keep Solid casing check off and enable Animate crystal casing for the next test; rebuild/install and restart.
  Actual movement and the small tip refraction change require an in-game check. Bundled extension 1.2.14.
- Validation: clean analysis, 244 Flutter checks (one skip), the separate fresh frozen-engine Windows startup check,
  346 Python checks (Windows: five skips; Linux: four), bundle verification, 12 launcher checks and 10 import checks
  passed. Strict native roundtrips passed for both component graphs, the corrected sequence, mesh and both glass
  instances. Independent native LOD comparisons retain every vertex byte, triangle/winding, GPU buffer size and opaque
  tail, with central/tip triangle counts 1696/188, 856/86 and 432/38. All 364 sequence export identities are unique.
  Verified the downloaded ZIP's SHA-256, commit/run provenance and all 26 manifest entries plus the manifest against
  source. Native structure/package verification does not establish the live turn or optical appearance.
- First complete candidate to verified download: **8m08s**, including focused/full checks, waiting and verification.
  Windows CI took **5m01s**, using **8m58s** of runner time. Reused the automatic push run; no extra build dispatched.

## Published Crystal Fina glass refraction — 2026-10-15

Live follow-up: the user approves the transparency and requests only slightly stronger refraction above/below Fina.
Enabling the optional turn makes the casing disappear; the duplicate track identity correction above addresses a
concrete error in that generated sequence while preserving the approved central material.

Code: [`68615bf`](https://github.com/biscoBen/FFR-Vison-Studio/commit/68615bf44f3523d7bf8872fb1abc001e2de336ee).
[Verified Windows test release / run 38819768798](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38819768798).

- Strengthen Crystal Fina Test's glass after live testing confirmed the casing and Fina are visible with added
  rotation off. Raise surface opacity from .12 to .22 and Fresnel from .65 to .80, and sharpen reflections with
  roughness .10 instead of .14. Reduce RefractionDepthBias from 1000 to 12 to admit depth-gated refraction rather
  than suppress it across the casing. Keep water ripples off. This uses the shipped glass shader and scalar overrides.
- Keep the confirmed grounded attachment, fitted pose and independent solid/rotation switches. Test with Solid
  casing check off and Animate crystal casing off, then rebuild/install and restart. Actual refraction and Fina's
  readability still need an in-game check. Bundled extension 1.2.13.
- Validation: clean analysis, 244 Flutter checks (one skip), the separate fresh frozen-engine Windows startup check,
  342 Python checks (Windows: five skips; Linux: four), bundle verification, 12 launcher checks and 10 import checks
  passed. Glass material and mesh passed strict native roundtrips. Verified the downloaded ZIP's SHA-256, exact
  commit/run provenance and all 25 manifest entries plus the manifest against source. These checks establish the
  packaged parameters, not the final in-game refraction or readability.
- First complete candidate to verified download: **7m23s**, including local checks, waiting and verification.
  Windows CI took **5m23s**, using **8m53s** of runner time. Reused the automatic push run; no extra build dispatched.

## Published grounded Crystal Fina casing comparison — 2026-10-15

Live follow-up: the solid casing renders and its own material makes it turn. Switching Solid casing check off with
added rotation off also renders the glass and readable Fina. The user requests stronger glass presence and refraction.

Code: [`29c5e6b`](https://github.com/biscoBen/FFR-Vison-Studio/commit/29c5e6bbc84ec9cca236be1856c106eddce5e6af).
[Verified Windows test release / run 38815120120](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38815120120).

- Restore the Crystal Fina Test casing's grounded FootComponent attachment from the first visible solid version.
  Add **Animate crystal casing**, off by default for new and legacy settings, independently of Solid casing check.
  Off removes the added LevelSequenceActor and turn-sequence asset entirely; the original solid material retains
  its own effects. On enables the existing slow transform turn. Preserve both preferences when other switches
  change; neither preference alone enables a mod or creates a roster. Log the attachment and rotation mode.
- Keep the fitted Fina sprite, casing size, material choices, acquisition and collision. The disappearance was first
  reported after adding the turn sequence, but its cause remains unconfirmed. Start with Solid casing check on and
  Animate crystal casing off, rebuild/install and restart Resonance. Native serialization and settings checks cannot
  establish actual in-game visibility. Bundled extension 1.2.12.
- Validation: clean analysis, 244 Flutter checks (one skip), the separate fresh frozen-engine Windows startup check,
  342 Python checks (Windows: five skips; Linux: four), bundle verification, 12 launcher checks and 10 import checks
  passed. Native readbacks passed for the static and rotating component graphs, turn sequence, solid material and
  mesh. Verified the downloaded ZIP's SHA-256, exact commit/run provenance and all 25 manifest entries plus the
  manifest against source. Game visibility remains unverified; the complete user log for the preceding build
  confirmed SOLID CHECK, its turning sequence and successful installation of all three mod files.
- First complete candidate to verified download: **7m19s**, including local checks, waiting and verification.
  Windows CI took **4m57s**, using **9m00s** of runner time. Reused the automatic push run; no extra build dispatched.

## Published Crystal Fina solid casing comparison — 2026-10-15

Live follow-up: the casing was still missing. The complete install log confirms this was the solid material with
its added turning sequence and a successful install. The grounded/static comparison above isolates that setup.

Code: [`ff32f8a`](https://github.com/biscoBen/FFR-Vison-Studio/commit/ff32f8ae1c9224af6aa7815ef7d730ae94d0f3cb).
[Verified Windows test release / run 38808095289](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38808095289).

- Add **Solid casing check** below Crystal Fina Test, enabled by default for existing and new settings. It switches
  the private material between the original solid Sanctum material and the current experimental glass. Both modes
  use the same mesh, placement, size, turning sequence and acquisition. The solid copy retains its native opaque
  parent, parameters and 121,103 bytes of original shader/cache data; it does not require the glass shader.
- Save the choice independently and preserve it when other switches change. A saved diagnostic preference alone
  does not activate a mod feature or create a roster. Print SOLID CHECK or GLASS during installation. Rebuild/install
  and restart between modes. A visible solid casing would point to the experimental material/render path; a missing
  solid casing would leave runtime object presence/installation to investigate. Fina may be hidden by the solid shell.
  This comparison follows another live report of the missing casing; it does not establish a rendering fix yet.
- Validation: clean analysis, 244 Flutter checks, the separate fresh frozen-engine Windows startup check and all
  341 Python checks passed (Windows: five skips; Linux: four), with bundle verification, 12 launcher checks and
  10 import checks. Solid mesh/material native roundtrips passed; material data and native shader/cache bytes match
  the source. Verified the downloaded ZIP's SHA-256, commit/run provenance and all 25 manifest entries plus the
  manifest against source. Bundled extension 1.2.11. Actual casing visibility still needs an in-game test.
- First complete candidate to verified download: **6m50s**, including checks, waiting and verification. Windows CI
  took **5m02s**, with **9m18s** runner time. Reused the automatic push run without dispatching an additional build.

## Published Crystal Fina casing setup correction — 2026-10-15

Live follow-up: the user still reported the same missing casing. The solid-versus-glass comparison above separates
material behavior from runtime object presence; the earlier setup corrections have not established the live cause.

Code: [`741e486`](https://github.com/biscoBen/FFR-Vison-Studio/commit/741e48609b46e5512b6402e132b8cc95daebfd84).
[Verified Windows test release / run 38804043413](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38804043413).

- Correct **Crystal Fina Test** casing setup after surface-only adjustments left it invisible: reset the copied
  VisibilityId from 1 to -1 and invalidate donor texture-streaming build data. A nonnegative visibility ID can subject
  a relocated mesh to the donor level's precomputed culling. Restore direct attachment to the sprite and bind the
  turning sequence to the casing itself; remove the added intermediate pivot.
- Use ClockSource=Tick and clear the acquisition donor's CustomClock. Explicitly author all nine transform channels
  with the casing's position, .12 scale and zero roll/pitch; only yaw changes over time. No unrelated donor translation
  or scale survives. Retain the current glass settings, fitted Fina pose, acquisition flow and collision. Record these
  rules in `SCENE_PLACEMENT.md` and the full-game checklist. The live cause remains unconfirmed; visibility and turning
  still require an in-game check.
- Validation: clean analysis, 243 Flutter checks and the separate fresh frozen-engine Windows startup check passed.
  All 340 Python checks passed on Windows (five skips) and Linux (four skips), alongside bundle verification,
  12 launcher checks and 10 import checks. Native sequence and actor/component roundtrips retained Tick, the cleared
  culling ID, direct attachment and explicit transforms. Verified the downloaded ZIP's SHA-256, commit/run provenance
  and all 25 manifest entries plus the manifest against source. Bundled extension 1.2.10. These checks do not prove
  runtime visibility or animation playback.
- First complete candidate to verified download: **10m16s**, including checks, waiting and verification. Windows CI
  took **8m19s**, with **12m42s** runner time. Reused the automatic push run without dispatching an additional build.

## Published Crystal Fina glass surface visibility test — 2026-10-15

Live follow-up: the user reported the same appearance after the surface adjustment. Superseded by the casing setup
correction above; surface parameters alone did not resolve the missing casing.

Code: [`3097d47`](https://github.com/biscoBen/FFR-Vison-Studio/commit/3097d4767711bb96d4c174a7de87d5333de155e3).
[Verified Windows test release / run 38800014400](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38800014400).

- Restore surface cues in **Crystal Fina Test**: raise opacity to .12, Fresnel intensity to .65 and metallic response
  to .08, with roughness .14. Keep refraction depth bias 1000 and zero normal/wave distortion. The previous live test
  showed Fina clearly but no perceptible casing. Native assets still contain the mesh and private material with ordinary
  visibility settings; restoring moderate highlights and coverage addresses the overly faint surface settings.
  Retain the fitted pose, display center, casing-only rotation and acquisition flow. Final casing visibility and turning
  still require an in-game test.
- Validation: clean analysis, 243 Flutter checks, the separate fresh frozen-engine Windows startup check, and all
  340 Python checks passed (Windows: five skips; Linux: four). Bundle checks, 12 launcher checks and 10 import checks
  passed. The updated native material roundtrip retained the surface settings and distortion suppression. Downloaded
  the published ZIP, verified SHA-256 and commit/run provenance, and matched all 25 manifest entries plus the manifest
  against source. Bundled extension 1.2.9. Automated checks do not verify runtime rendering.
- First complete candidate to verified download: **7m11s**, including checks, waiting and verification. Windows CI
  took **5m25s**, with **9m51s** runner time. Reused the automatic push run without dispatching an extra build.

## Published Crystal Fina clarity, fit and turning test — 2026-10-15

Live follow-up: Fina is clearly visible, but the casing has no perceptible surface. Rotation cannot be assessed from
that screenshot. Superseded by the surface visibility candidate above.

Code: [`20d27fc`](https://github.com/biscoBen/FFR-Vison-Studio/commit/20d27fc0557b18849efc42670a920d499f54f688).
[Verified Windows test release / run 38795958251](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38795958251).

- Refine **Crystal Fina Test** after the glass trial: reduce image warping with the engine's refraction depth bias,
  lower surface opacity and reduce the introductory pose by about 23%. Check all three idle frames against the
  casing's projected silhouette through a full turn. Preserve the display center and casing size.
- Restore a slow casing-only turn with a private looping native sequence, bound to an owned pivot. Keep Fina,
  interaction and collision steady, without camera cuts or movement-input restrictions. Preserve the original cave
  option and acquisition route. Record engine controls, binding paths and native component serialization requirements
  in `SCENE_PLACEMENT.md` and the full-game checklist. Final clarity, fit and turning still need an in-game comparison.
- Validation: clean analysis, 243 Flutter checks and the separate fresh frozen-engine Windows startup check passed.
  All 340 Python checks passed on Windows (five skips) and Linux (four skips), plus bundle verification, 12 launcher
  checks and 10 import checks. Native mesh, material, rotation sequence and actor/component roundtrips passed.
  Downloaded the published ZIP, matched SHA-256 and commit/run provenance, and compared all 25 manifest entries plus
  the manifest with source. Bundled extension 1.2.8. These checks do not verify game rendering or runtime playback.
- First complete candidate to verified download: **7m38s**, including checks, waiting and verification. Windows CI
  took **5m46s**, with **9m59s** runner time. Reused the automatic push run; no additional build was dispatched.

## Published Crystal Fina glass material test — 2026-10-15

Live follow-up: the glass revealed Fina, but strongly refracted her image and lost the original material-driven turn.
Superseded by the clarity, fit and turning candidate above.

Code: [`1d2ad70`](https://github.com/biscoBen/FFR-Vison-Studio/commit/1d2ad70c286264f931c374c33d819c595ad93844).
[Verified Windows test release / run 38785441302](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38785441302).

- Replace the unsuccessful masked material in **Crystal Fina Test** with the game's native glass transmission
  shader (`MSM_SingleLayerWater`). Use low opacity/reflection and no normal-map/wave distortion; inherit the glass
  shader's defaults instead of the opaque crystal's color, glow and texture overrides. Validate the actual shading
  model and its parameter names. Retain the current casing placement, Fina's introductory pose and acquisition route.
  The earlier masked shader's static dithering switch was disabled, and live testing showed that candidate remained
  solid. Final transmission, sprite visibility and glass appearance of this candidate still need an in-game test.
- Validation: clean analysis, 243 Flutter checks and the real frozen-engine Windows startup check passed.
  All 338 Python checks passed on Windows (five skips) and Linux (four skips), with the required bundle checks,
  12 launcher checks and 10 import checks. Native mesh/material roundtrips retained the new glass parent and scalar
  settings. Downloaded the published ZIP, matched SHA-256 and commit/run provenance, and compared all 25 manifest
  entries plus the manifest with the source. The bundled extension is 1.2.7. These checks do not verify game rendering.
- First complete candidate to verified download: **8m20s**, including checks, waiting and verification. Windows CI
  took **5m34s** with **8m14s** runner time. Reused the automatic push run without dispatching an extra build.

## Published Crystal Fina test visibility fix — 2026-10-15

Live follow-up: this candidate still appeared solid. The shipped masked shader's dithering switch was disabled;
its scalar settings did not reveal Fina. Superseded by the glass transmission candidate above.

Code: [`d31c5b6`](https://github.com/biscoBen/FFR-Vison-Studio/commit/d31c5b606462d7901898cd048589c9576a5a92a6).
[Verified Windows test release / run 38779778666](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38779778666).

- Correct **Crystal Fina Test** visibility: the native Sanctum material is opaque. The private test instance now
  inherits the game's cooked masked crystal shader, discards the incompatible opaque shader resources and reduces
  surface glare. Center the casing in the sprite's own coordinates so billboard transforms keep it around her.
  Retain the acquisition route and original cave option. This uses masked coverage rather than optical glass
  transmission; final coverage and framing still need an in-game test. Record the native shader and sprite-space
  placement rules in `SCENE_PLACEMENT.md` and the full-game release checklist.
- Validation: clean analysis, 243 Flutter checks and the separate real frozen-engine Windows startup check passed.
  All 338 Python checks passed on Windows (five skips) and Linux (four skips), along with the required bundle,
  launcher and import checks. Native material/mesh/component binary roundtrips passed. Downloaded the published
  archive, matched its SHA-256 and commit/run provenance, and verified all 25 manifest entries plus the manifest
  against the source. The engine extension is 1.2.6. Gameplay appearance remains pending.
- First complete candidate to verified download: **8m18s**, including checks, corrections, waiting and verification.
  Windows CI took **5m26s** with **10m05s** runner time. Reused the matching automatic push run; no extra build
  was dispatched. Master stays unchanged.

## Published Crystal Fina Sanctum crystal test — 2026-10-15

Code: [`fe46921`](https://github.com/biscoBen/FFR-Vison-Studio/commit/fe4692168fc7916c3a3efec59df35ad1ac78c070).
[Verified Windows test release / run 38771871918](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38771871918).

- Add **Crystal Fina Test** beside the original cave switch. It uses the same entrance, portal, acquisition reward,
  ownership condition and stone-cave return, with Fina's native introductory `openarmidle2` pose inside private copies
  of the Sanctum crystal mesh and material. Retain the crystal's original glow/material parameters for this experiment;
  omit Fina's separate yellow introductory aura. The switches are mutually exclusive and reuse the same editable vision.
  Register the decorative shell on the acquisition actor, preserve its streamed mesh data and keep the existing NPC
  collision/interaction. Serializer checks use the supplied native assets; visibility through the unchanged material,
  component hiding and final framing still need an in-game test.
- Validation: clean analysis; 243 Flutter checks and the separate real frozen-engine Windows startup check passed.
  All 337 Python checks passed on Windows (five platform skips) and locally on Linux (four skips), along with the
  bundle checks, 12 Windows launcher checks and 10 import checks. Native mesh/material/component serializer roundtrips
  retained references, opaque data and effect parameters. Downloaded the published package, matched its commit/run
  provenance and SHA-256, and compared all 25 managed extension files with the source candidate. Gameplay remains pending.
- First complete candidate to verified download: **14m26s**, including dependency setup, corrections, checks, build
  waiting and download verification. Windows CI took **7m49s** with **12m16s** runner time. The build helper reused the
  automatic push run and its verified test-release download; no extra build was dispatched. Master stays unchanged.

## Published private PC-to-Deck mod sync — 2026-10-13

Code: [`8ce9507`](https://github.com/biscoBen/FFR-Vison-Studio/commit/8ce9507e6c3ce29e2820078ab9d43a23094abc71).
[Verified Windows test release / run 38457270486](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38457270486).
[Small Deck installer ZIP](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-38457270486/Resonance-Deck-Sync.zip).
[Linux checks / run 38457270515](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/38457270515).

- Add **Steam Deck sync** with local, opt-in private-repository setup and **Build & publish to Deck**.
  Ordinary installs/builds never upload. PC tokens use Windows Credential Manager; the Deck uses KWallet/Secret
  Service or prompts without saving. Validate that the destination is private and belongs to the publishing account.
  Package the verified compiled mod plus its working cycling runtime; exclude credentials, raw Studio config, game
  files and saves. Publish a release only after its uploaded checksum matches.
- Publish a small **Resonance-Deck-Sync.zip** containing the standalone **Update my mod.sh / Deck Mod Sync.py** installer,
  also included in the full Studio test ZIP. Download private packages on
  SteamOS without Studio, Proton for the app or engine/build setup; detect game libraries/SD cards and create a persistent
  shortcut in Downloads/FFR Mod. Match the PC game version, check package paths/checksums, back up owned files, preserve
  other mods/runtime conflicts, remove stale cycling files and recover interrupted installs. Print the cycling Proton
  launch option. Repository creation remains a one-time local step because the connected GitHub integration lacks it.
- Add transfer/privacy, checksum/channel, credential, rollback/recovery, runtime ownership and UI/API checks; exercise
  the managed extension and credential store in the genuine frozen Windows engine. Live private publishing with the
  user's token and actual Deck/UE4SS gameplay remain unverified. Add the workflow to the full-game checklist.

- Validation: clean analysis; 241 Flutter tests plus the real frozen-engine Windows startup/credential check passed.
  All 333 Python checks passed on Windows (five platform skips) and Linux (four platform skips). Windows passed
  bundle checks, 12 launcher checks and 10 import checks; Linux also passed the launcher, package and transfer jobs.
  Downloaded both published ZIPs and checked SHA-256, commit/run metadata, embedded helper bytes and executable LF
  wrappers. The standalone downloaded helper passed launch/help and restore smoke checks. Master remains unchanged.
- Final fixes include the bundle allowlist/material background found by the full suite and changing game folders only
  after restoring the previous install. First recorded complete candidate to verified downloads: **18m38s**, including
  local checks, dependency setup, corrections, waiting, both Windows push builds and download verification. Final Windows
  CI took **5m08s** with **8m42s** runner time; the first Windows build used **10m18s** runner time. Both Linux jobs
  used **6s** each. An early helper call raced push-run visibility and dispatched a duplicate, which was cancelled;
  it used **2m54s** runner time and published nothing. The final helper reused the matching push run and verified its
  download through the authenticated test-release fallback. Publication notes use the cheap docs-only checks.

## Published Steam Deck launcher (CI checked) — 2026-10-13

Code: [`b520392`](https://github.com/biscoBen/FFR-Vison-Studio/commit/b520392bdb8a5df71f0b950669e3f66c7c862d48).
[Windows test release / run 38446853083](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-38446853083).
[Linux launcher checks / run 38446853147](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/38446853147).

- Add **Start Studio Test.sh** and a Python Steam Deck updater/launcher to test ZIPs.
  Run in Desktop Mode using an installed Proton, with separate persistent Studio data
  and Proton prefix. The desktop/menu shortcut checks the same tested branch releases
  as Windows, verifies SHA-256 and embedded metadata, and retains the cached app after
  failed/offline updates. Detect additional Steam libraries/SD cards and support a saved
  or explicit Proton choice; log Proton startup and show the game's Windows Z: path.
  Preserve native Windows launchers and keep their CRLF formatting; Deck scripts use LF.
- Add automated coverage for channel selection, package layout, checksum/metadata failures,
  interrupted updates, atomic state recovery, saved-data/prefix preservation, offline
  startup, ZIP traversal/symlinks, Steam/Proton detection and Windows launch arguments.
  A Linux CI job also checks real file locking, shell syntax and startup with a mock
  Proton process. Live Deck rendering, engine preparation and game installation remain unverified.

- Windows CI passed full Flutter analysis/tests, frozen-engine startup, bundle
  verification, 304 Python tests (three Linux integration skips), 12 Windows launcher
  checks, compilation and publication. Linux CI passed all 14 launcher tests and two
  package tests, including shell syntax, real file locking and startup with a mock
  Proton process. Test ZIPs include executable LF Deck scripts alongside CRLF Windows
  launchers. Master remains unchanged.
- Release commit/run, channel, asset URL and published SHA-256 metadata were checked.
  The connected workspace failed to provision, so local checks and the usual download
  helper could not run; CI supplied validation. No local ZIP checksum verification,
  real Proton rendering, engine preparation or game installation is claimed. Use the
  Deck logs for the first device test.
- First recorded complete candidate to CI/release-identity verification: **16m00s**,
  including the failed selector check, correction, Linux coverage and both automatic
  Windows builds. Final Windows CI took **5m12s**, with **9m30s**
  runner time; the earlier failed candidate used **7m35s** runner time.
  Linux checks used **9s** runner time. Two code pushes, two automatic Windows
  builds and one Linux run; no manual dispatch. Publication notes use the docs-only path.

## Published reversible Sephira skill visuals — 2026-10-07

Code: [`d35ceca`](https://github.com/biscoBen/FFR-Vison-Studio/commit/d35ceca1dfdfc0982d8aad76462d3cdb9c453877).
[Verified Windows test release / run 37659730752](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37659730752).

- Add a separate saved **Use borrowed Sephira skill visuals** toggle, on by default.
  Turn it off and rebuild/install to use the original source visuals for the 216
  preset substitutions, while retaining MP, power, effects, stats, MR and saved edits.
  Turn it on and rebuild/install to restore the borrowed visuals. Works with existing
  saved kits without resetting them and independently of library visibility/repair
  controls. Missing source animations stay missing in the demo; full-game visuals
  still need testing. Explicitly edited donors and authored sequences are preserved.
  Original mode also retains native shared-sequence pointers such as Absolute Zero's.
- Validation: 237 Flutter tests passed (one platform skip), 290 Python tests passed
  (three platform skips), clean analysis and verified bundles. Checks cover all 216
  substitutions, mode independence, unchanged combat settings and saved kits,
  persistence/failure handling, and native source timelines supplied by a later game.
  An audit against the extracted game tables confirmed all 216 substitutions and
  retained Absolute Zero's shared native sequence without changing combat settings.

- All required Windows gates passed: full validation, frozen-engine startup,
  launcher/updater checks, compilation and publication. Authenticated download
  verified the exact commit/run, ZIP checksum and all 60 bundled resources.
  The downloaded helper switched all 216 substitutions off/on with unchanged
  saved kits and combat fields; master remains unchanged. Live-game visuals
  and the full game's future source assets still require in-game testing.
- First recorded complete candidate to verified package: **22m31s**,
  including local checks, final review, waiting and package verification.
  Two code pushes and two reused automatic builds; the second includes the native
  shared-sequence correction. No manual dispatch. CI took **5m23s**, with **8m56s**
  runner time; combined runner time including the earlier candidate was **20m27s**.
  Verification after CI took **1m11s**.
  Publication notes use the documentation-only path.

## Published awakening and MR count correction — 2026-10-06

Code: [`a4f82e8`](https://github.com/biscoBen/FFR-Vison-Studio/commit/a4f82e81e054ba029346b5936c809bb7f5cd8d87).
[Verified Windows test release / run 37554129020](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37554129020).

- Correct Sephira kit counts to **20–28 awakening abilities/bonuses**, with learned
  MR abilities/bonuses additional. Add 139 awakening grants from the wider catalog;
  current recipes contain 20 awakening grants each, except Elephim with 22. Preserve
  every existing MR reward, native stat budget and required original-skill allocation.
  Separate awakening and MR counts in the kit document. New support copies replace
  permanent boss buffs/invulnerability with timed player effects and cap drain at
  damage dealt. Keep skill-dependent bonuses with their required skills.
- Saved kits stay intact until the backed-up **Reset all presets** or individual
  reset applies revision 3. Build/install afterwards. Live-game balance and demo
  animation availability still need testing.

- Local checks passed: 234 Flutter tests (one existing platform skip), 282 Python
  tests (three existing platform skips), clean analysis and verified bundles.
  Native SDK readback checked 312 private rows and unchanged originals; the pinned
  engine accepted all 29 hosted LB timelines. Focused Flutter checks, Python checks
  and native readback were repeated after the cleansing correction. Regression
  checks count the actual awakening grants independently of MR, preserve every MR
  reward exactly, verify bonus dependencies, and ensure cleansing keeps friendly buffs.
- All required Windows gates passed, including full validation, frozen-engine
  startup, launcher/updater checks, compilation and publication. Authenticated
  download verified the exact commit/run, ZIP checksum and all 59 bundled resources:
  30 presets, 602 awakening grants and 168 additional learned MR grants. Master is unchanged.
- Measured audit start to verified package: **24m49s**.
  First recorded complete candidate to verified package: **12m59s**,
  including local checks, the cleansing correction, superseded build, waiting and verification.
  Two code pushes and two reused automatic builds; the earlier run was superseded.
  Final CI took **7m26s** and **9m44s** runner time;
  combined runner time including the superseded run was **17m37s**.
  Verification after CI took **0m23s**. Publication notes use the documentation-only path.

## Published expanded Sephira kits — 2026-10-06

Code: [`fa81e40`](https://github.com/biscoBen/FFR-Vison-Studio/commit/fa81e402e05b5d86eec2a8580ac0b74d1486c09c).
[Verified Windows test release / run 37546814857](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37546814857).

- Expand the Sephira collection from 11–16 to 20–25 distinct abilities/passives
  (including learned MR rewards in these earlier totals) using the wider native and enemy catalog. Keep exact native stat/MR budgets
  and all 291 excluded-vision grants covered once. Supplemental player copies
  receive appropriate MP costs, capped boss accuracy/power and safe drain values;
  original game skills remain intact. Alice's slam line now uses ice.
- Retire Great Dragon, leaving 30 presets. Keep his required original rewards
  covered by suitable remaining visions; Reberta's Eikon/fire bundle stays together.
  Older tagged Great Dragons are omitted from builds; Reset all presets backs up
  and removes the retired entry. Independent user-added copies are preserved.
- Show when saved kits have a newer recipe available. Apply it with the existing
  backed-up **Reset all presets** (or individual reset), then build/install;
  saved edits and acquisition placements remain intact until reset. Keep copied
  skills' player command bindings correct when allocating another vision ID.
- Kit counts, sources, costs, unlocks and balance limits are documented in
  `SEPHIRAS_VISIONS.md`. Live-game balance and demo animation availability still
  require testing.
- Local checks passed: 234 Flutter tests (one existing platform skip), 280 Python
  tests (three existing platform skips), clean analysis and bundle verification.
  Native SDK readback verified 177 private skill/passive/effect rows and unchanged
  originals; the pinned engine accepted all 29 hosted LB timelines. Regression
  checks cover kit bounds, unique sources, safe costs/drain/hit ratios, command
  remapping, update notices, backed-up resets and retired-entry filtering.
- All required Windows gates passed: full validation, frozen-engine startup,
  launcher/updater checks, compilation and publication. Authenticated download
  verified the exact commit/run, ZIP checksum and all 59 bundled resources,
  including the 30 presets and 631 distinct grants. Master remains unchanged.
- Measured audit start to verified package: **40m59s**. First recorded complete
  candidate to verified package: **11m49s**, including local checks, damage-ratio
  precision correction and final command-binding correction. One code push and
  one reused automatic build. CI took **5m09s** and **8m48s** runner time;
  verification after CI took **1m20s**. Publication notes use the documentation-only path.

## Published preset appearance preparation fix — 2026-10-06

Code: [`a5ace73`](https://github.com/biscoBen/FFR-Vison-Studio/commit/a5ace736273bc3b707dc1ffe82c6f3dd556b8ad9).
[Verified Windows test release / run 37541028882](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37541028882).

- Fix enabling Sephira’s Visions when a Brave Shift's base appearance belongs
  to a separate hosted unit. Resolve each appearance's download owner independently,
  including Alice/Half Nightmare and original Alice, without changing the selected
  look or kit. Preparation failures name the preset and preserve the saved roster.
- Validate preparation of all 31 bundled presets against catalog ownership rules,
  including shared-owner and separate-owner shifted forms. The pinned engine accepts
  all 33 required hosted form requests. Local checks: 232 Flutter tests (one existing
  Windows-only skip), 278 Python tests (three existing Windows-only skips), clean
  analysis and verified bundles.
- All required Windows gates passed, including full suites, analysis, frozen-engine
  startup, launcher/updater checks, compilation and publication. Authenticated
  download verified the exact commit/run, package checksum and all 59 bundled
  resources. Saved kits, selected looks, engine payloads and master are unchanged.
- Measured first inspection to verified package: **9m04s**. First recorded complete candidate
  to verified package: **7m41s**, including local checks and the correction to retain
  API error types. One code push and one reused automatic build. CI took **5m10s**
  and **8m30s** runner time; verification after CI took **18s**. Publication notes
  use the documentation-only path.

## Published Sephira’s Visions collection — 2026-10-06

Code: [`5886393`](https://github.com/biscoBen/FFR-Vison-Studio/commit/5886393d22f7b3d89c283aa33e4c659e28402fd0).
[Verified Windows test release / run 37535223224](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37535223224).

- Add 31 balanced, optional Sephira’s Visions presets using the requested FFBE
  rarities, Brave Shift/Super Limit Burst forms and custom Crystal Fina. Their
  native stat/MR budgets and unique skills cover all 160 active skills and 131
  passives of the 15 excluded originals. Specialists also have attacks and
  secondary utility; no FFBE stat or LB multiplier conversion is used.
- Add a home-page section with
  edit-preserving enable/disable, restore-missing and backed-up preset resets.
  Disabled entries are filtered before sprites, animations, acquisition and
  verification without deleting their saved configs or reusing their IDs.
- Rebind command/LB bonuses on private copies and make Minfilia’s Dual Jobs
  select her allocated vision identity. Preserve native originals. Adopt an
  existing Crystal Fina without changing her kit or cave assignment; reset her
  explicitly to apply the balanced recipe.
- Reserve the native skill catalog during preset ID allocation and recheck at
  build time. Keep new LB IDs in the custom namespace; reset backups can be
  imported directly through Studio’s character-config controls.
- Document every selected form, kit and unlock rank in `SEPHIRAS_VISIONS.md`,
  with machine-readable coverage and native balance budgets. Local native-SDK
  read-back confirms 21 private rows and unchanged originals; the pinned engine
  accepts all 30 hosted LB timelines. Live-game balance and visual checks remain
  an in-game testing task; the presets use native budgets as their starting point.
- Local checks: 230 Flutter tests (one Windows-only skip), 278 Python tests
  (three existing Windows-only skips), clean analysis and verified bundles.
- All required Windows gates passed: full Flutter/Python suites, analysis,
  fresh frozen-engine startup, launcher/updater checks, compilation and
  publication. Authenticated release download verified the exact commit/run,
  package checksum and all 59 packaged resources, including the 31 presets and
  their complete native coverage audit. Master remains unchanged.
- Measured first inspection to verified package: **1h12m11s**, including form
  selection, research, implementation, checks, corrections and build waiting.
  First complete candidate to verified package: **22m32s**. Three code pushes:
  the first run was cancelled, the second completed but its superseded release
  was withdrawn into draft after the native-ID correction, and the final exact
  automatic run was reused for delivery. Final CI took **5m34s** and **9m07s**
  runner time; all three runs used **27m01s** runner time. Package verification
  after CI completion took **1m38s**. Publication notes use the documentation-only path.

## Published exact native kits and MR labels — 2026-10-06

Code: [`0f45572`](https://github.com/biscoBen/FFR-Vison-Studio/commit/0f45572ecef4bf4120a3875eb7ed5a2eedc353bb).
[Verified Windows test release / run 37524217402](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37524217402).

- Correct the default-vision editor's MR numbering to the game's 0–9 ranks. Label permanent stat rewards and
  passive equip costs, using Speed/Magic/AP for the matching native stats.
- Show each default vision's actual learning ranks for its inherited abilities/passives, including shared IDs.
  Include verified native learners in library source labels and identify explicitly marked enemy versions.
  Preserve exact game IDs, reward amounts, unlock points, hiding rules and descriptions. All 26 prepared default
  kits were audited against native tables; Tronn learns shared Fire 220010, not enemy Fire 250010.
- Add a Native kit filter to Abilities, Bonuses and MR, with visible game IDs. Browse any default vision's original
  awakening/MR abilities and passives even after removing them from an edit, and assign that exact version elsewhere.
- Local validation: 219 Flutter tests (one existing skip), clean analysis, 271 Python tests (three existing Windows-only
  skips), and bundle verification. Re-add/transfer tests distinguish same-named IDs and retain native rewards unchanged.
- All required Windows gates passed: full Flutter/Python suites, analysis, fresh frozen-engine startup,
  launcher/updater checks, compilation and publication. Authenticated release download verified the exact commit/run,
  package checksum and all 56 packaged resources. The default game recipes, engine payloads and master are unchanged.
- Measured first inspection to verified package: **20m35s** — inspection/implementation and focused checks **12m38s**,
  final local checks/review/push **1m36s**, CI **5m30s**, package verification **50s**. First complete candidate to
  verified package: **13m08s**, including the additional exact-kit filter work. One code push and one reused automatic
  Windows build; CI used **8m08s** runner time. Publication notes use the documentation-only path.

## Published party attack and LB voice replacements — 2026-10-05

Code: [`c60b37a`](https://github.com/biscoBen/FFR-Vison-Studio/commit/c60b37a400490e23980dbcc1428dbff2ffcf8e1a).
[Verified Windows test release / run 37361816629](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37361816629).

- Replace fixed normal-attack grunts and party LB voice sections for every native party-to-party voice override.
  Use the selected speaker's native attack and generic LB cues, confirmed in base/English/Japanese demo banks.
  Keep original effects, section timing, animations and skill mechanics; original-voice selection restores authored audio.
  Story dialogue and team victory conversations stay original. LB wording and live playback require an in-game trial.
  Rebuild/install and restart Resonance after updating Studio.
- Local validation: 16 focused Flutter tests, clean analysis, and 270 Python tests (three existing Windows-only skips).
  Cover all 64 voice-selection pairs, duplicate export names and unchanged effect/timing properties. Native SDK
  read-back verifies 30 available authored sections and 15 cue assets; the new voice references survive IoStore packing
  and extraction. Frozen Windows startup also checks installation and all eight speaker profiles. Live playback remains
  an in-game user check.

- All required Windows gates passed: full Flutter/Python suites, analysis, fresh frozen-engine startup,
  launcher/updater tests, compilation and publication. Authenticated release download verifies exact commit/run,
  checksum and all 56 packaged resources. No audio recordings or engine archives were uploaded or rehosted.
- Measured original inspection to verified package: **52m25s**, including **3m55s** awaiting the native cue reference.
  From that upload: **29m11s** — implementation **13m39s**, local checks/corrections/push **8m03s**,
  CI **6m22s**, package verification **1m06s**. First complete candidate to verified package: **15m32s**.
  The main CI run used **9m20s** runner time. One code push and one completed automatic Windows build;
  an initial helper discovery race dispatched an unintended duplicate, cancelled before compilation/publication.
  Publication notes use the documentation-only path.

## Published native party battle voice selector — 2026-10-05

Code: [`c5024e8`](https://github.com/biscoBen/FFR-Vison-Studio/commit/c5024e8193bce9efe69d4447a674df586efb75ea).
[Verified Windows test release / run 37354335281](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37354335281).

- Add **Change battle voice** for all eight party characters, with independent save/load and voice-only revert.
  Use the game's native battle voice labels; preserve story dialogue, identities, models, stats and progression.
  This first pass covers standard battle routing. Fixed cinematic voices and team victory conversations remain authored;
  available recordings for demo-unavailable characters still require live testing. Rebuild/install and restart the game.
- Validation: 29 focused Flutter tests, clean analysis and 265 Python tests (three local Windows CI-only skips).
  Cover all 64 voice-selection pairs. Native serialization and IoStore read-back preserve the selected labels and other
  properties of all 643 character rows. All required Windows gates passed, including the full Flutter/Python suites,
  fresh frozen-engine startup, launcher/updater checks, compilation and publication. Authenticated release download
  verified the exact commit/run, checksum and all 54 packaged resources.
- Measured first recorded inspection timestamp to verified package: **17m51s** — inspection/implementation **6m45s**,
  local validation/review/push **4m31s**, CI **5m54s**, package verification **40s**. Initial skill/setup work preceded
  that first timestamp, so this is a lower bound on the full request time. First complete candidate to verified package:
  **11m06s**. One code push and one reused automatic Windows build; CI used **9m40s** runner time.
  Publication notes use the documentation-only path.

## Published weighted random acquisition — 2026-10-05

Code: [`4a37020`](https://github.com/biscoBen/FFR-Vison-Studio/commit/4a370208401451b6b84ce27c24fa7a77a5de69d6).
[Verified Windows test release / run 37345207748](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37345207748).

- Random acquisition chooses caves 75% of the time and vendors 25%, independent of their list sizes. Apply the same
  weighting to initial selections and both Random-toggle rerolls. Prefer another location in the selected category when
  available; a sole cave can repeat to preserve the odds. With no caves, use vendors. Preserve saved/manual choices.
- Show the odds beside Random and record the final-quarter story-access filter in the shared full-game release checklist.
  That exclusion remains pending reliable progression/cutoff data for vendors and custom cave positions.
- Validation: 23 focused acquisition tests and clean Flutter analysis. Cover unequal pool sizes, all category outcomes,
  within-category choice, both toggle directions, a sole cave, missing categories, saved/manual choices, config persistence
  and UI behavior. All required Windows gates passed, including the full Flutter/Python suites, fresh frozen-engine startup,
  launcher/updater checks and compilation. Authenticated release download verified the exact commit/run, checksum and all
  54 packaged resources. Engine assets and native cave generation are unchanged.
- Measured request to verified package: **16m06s** — inspection/implementation **5m34s**, local validation/review/push
  **3m53s**, CI **6m14s**, package verification **24s**. First complete candidate to verified package: **10m31s**.
  One code push and one reused automatic Windows build; CI used **9m58s** runner time. Publication notes use the
  documentation-only path. The first local test invocation was blocked from opening its loopback socket; rerunning with
  network permission resolved that setup issue before tests executed.

## Published cave exit object identities — 2026-10-04

Code: [`808e515`](https://github.com/biscoBen/FFR-Vison-Studio/commit/808e515d9782b7db849bfffb00b756fa0939b186).
[Verified Windows test release / run 37270830560](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37270830560).

- Give every Resonance Cave world-map exit its own stable reserved object ID instead of inheriting `0`, which is also
  used by Earth Shrine's world entrance. Keep the existing travel target, grounded return, interaction and collision.
  The previous banner-policy change still showed Earth Shrine in live testing. This update tests the object-identity
  explanation; live confirmation remains necessary. Rebuild/install the mod after updating Studio to regenerate exits.
- Validation: 15 focused cave tests and the full 262-test Python suite (three existing skips). Native SDK read-back and
  IoStore round-trip preserve all 45 generated packages for four entrances/five visions, including nonzero exit IDs
  distinct from the portals and unchanged routes/collision/grants. All required Windows gates passed, including the full
  Flutter suite, analysis, fresh frozen-engine startup and launcher/updater checks. Authenticated release download verified
  the exact commit/run, checksum and all 54 packaged resources. No new runtime diagnostic is included.
- Measured request to verified package: **10m00s** — implementation **1m27s**, local checks/push **2m57s**,
  CI **5m20s**, package verification **16s**. First complete candidate to verified package: **8m33s**.
  One code push and one reused automatic Windows build; CI used **8m46s** runner time. Publication notes use the
  documentation-only path.

## Published cave entrance selector and World Map banners — 2026-10-04

Code: [`da6c177`](https://github.com/biscoBen/FFR-Vison-Studio/commit/da6c177585fafd924b8a6c92802a65e6247ffb84).
[Verified Windows test release / run 37267588481](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37267588481).

- New caves require an explicit entrance-image selection before opening the placement map. The placement editor shows the
  chosen model and offers **Change** to revisit the selector. Cancelling either step preserves saved caves and assignments.
- Correct the native destination-banner policy for map 1000 to use **World Map** rather than a landmark's name and
  recommended level. This applies while Resonance caves are installed, including world-map exit previews from native
  locations. Preserve native display timing/visibility, all other map entries, translations, and cave travel/collision.
  The previous region-ID change was insufficient in live testing; the supplied native place-name data exposed the
  separate `bUseLandName` setting. Native gameplay still needs the user's in-game test.
- Local validation: 14 focused Flutter tests, clean analysis, and the 262-test Python suite (three existing skips). Native
  SDK read-back and IoStore pack/extract checks preserve all 45 generated packages for four entrances/five visions,
  including the banner policy and unchanged other UI entries. All required Windows gates passed: analysis, the full Flutter suite, fresh frozen-engine startup, launcher/updater checks,
  compilation and release publication. Authenticated download verified exact commit/run provenance, checksum and all 54
  packaged resources. The banner's live display remains an in-game user check.
- Measured original request to verified package: **2h27m03s**, including **2h09m16s**
  awaiting the missing native reference. Work resumed with the upload: **11m25s** to verified package;
  active work across both turns **17m47s**. Implementation **7m57s**, local checks/push
  **4m04s**, CI **5m20s**, package verification **0m25s**. First complete candidate to verified
  package: **8m41s**. One code push and one reused automatic Windows build; CI used **9m02s**
  runner time. Publication notes use the documentation-only path.

## Published cave exit display identity — 2026-10-04

Code: [`97dc8e2`](https://github.com/biscoBen/FFR-Vison-Studio/commit/97dc8e23d1ab1b8af0a8360f18f09373a4fa6085).
[Verified Windows test release / run 37241624765](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37241624765).

- Set cave exits' native region/display ID explicitly to the world map, alongside their existing world-map travel target.
  This addresses the inherited Earth Shrine name/recommended-level banner while preserving grounded return locations.
- Validation: 14 focused cave checks and the full 261-test Python suite (three existing skips). Native SDK read-back and
  IoStore pack/extract verification preserve all 44 generated packages for four entrances/five visions; every tested exit
  has explicit travel and region IDs of 1000, with unchanged return coordinates, facing and collision snapping. All required
  Windows gates passed, including analysis, the full Flutter suite, fresh frozen-engine startup and launcher/updater tests.
  Authenticated download verified exact commit/run provenance, release checksum and all 54 packaged resources. The native
  banner's live display still requires the user's Resonance test; this workspace cannot execute the game.
- Measured request start to verified package: **14m53s** — inspection/implementation **4m27s**, local checks/native asset
  validation/push **4m20s**, CI **5m16s**, package verification **50s**. First complete candidate to verified package:
  **10m26s**. One code push and one reused automatic Windows build; CI used **8m33s** runner time. Publication notes use
  the documentation-only path.

## Published additional world-map landmarks — 2026-10-04

Code: [`250e7bc`](https://github.com/biscoBen/FFR-Vison-Studio/commit/250e7bce252a8c2a72ce389e60eb687ef347d68a).
[Verified Windows test release / run 37238843504](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37238843504).

- Restore 164 additional native scenery objects from the new reference files: Lanzelt's large bridges and towns,
  Dirnado settlements and industrial landmarks, and vision shrines. Preserve existing paint, foliage and landmark coverage.
- Decode textures whose highest source mip was stripped by cooking, retaining payload-size/dimension checks. Large bridges
  now use their available native diffuse colors. Shader effects and unsupported rock geometry remain simplified/omitted.
- Validation: all four reference archives passed integrity checks (279 native packages with companion exports). All previous
  scenery model types, terrain paint, foliage and shared native source fingerprints remain intact. Focused Flutter checks
  and a rendered preview passed; 261 Python tests passed with three existing skips. All required Windows gates passed,
  including the full Flutter suite, analysis, fresh frozen-engine startup and launcher/updater checks. Authenticated release
  download verified exact commit/run provenance, checksum, all 54 packaged resources and the 888-instance scenery archive.
- Measured request start to verified package: **13m27s** — reference inspection/implementation **6m22s**, local checks/push
  **1m19s**, CI **5m18s**, verification **27s**. First complete candidate to verified package: **7m06s**. The build helper raced
  push-run registration and dispatched an accidental duplicate; it was cancelled before publication and the push build was
  reused. Successful CI used **8m08s** runner time; the cancelled duplicate used **2m57s** (total **11m05s**).
  Publication notes use the documentation-only path. Live game rendering remains a user check.

## Published grounded cave exits and map details — 2026-10-04

Code: [`d94d02e`](https://github.com/biscoBen/FFR-Vison-Studio/commit/d94d02e2139612ac8de7204b9a7d052b7f123bc9).
[Verified Windows test release / run 37237225179](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37237225179).

- Increase ordinary cave visions by 5% from the previous package; preserve Crystal Fina's tested crystal scale.
- Return outside each cave on its rotated opening side, using native landscape height and runtime collision snapping
  instead of a fixed westward point 200 units above ground. Restore walking and use the native world-map exit/name route.
- Use native capture transparency to distinguish coast/ocean from low ground; Mitra no longer appears in water in the
  3D preview. Restore inherited town/landmark meshes and cooked bridge instances, including components
  in landscape levels. Cull distant meshes before expanding their geometry. Later-region assets absent from the supplied
  references and unsupported/translucent meshes still need additional reference coverage; rendering remains simplified.
- Validation: clean Flutter analysis, 205 Flutter tests (one existing platform skip), 260 Python tests (three existing
  platform/reference skips), and all required Windows gates, including fresh frozen-engine startup and launcher/updater
  tests. Native read-back and IoStore round-trip passed for four rotated entrances/five visions (44 packages), including
  grounded returns, facing, collision snapping and the unconditional world-map exit. Authenticated download verified the
  exact commit/run, release checksum, all 54 packaged resources and scenery members. Live Resonance gameplay remains a
  user check; automated checks cannot execute its native transition functions.
- Measured request start to verified package: **32m53s** — investigation/implementation and preview correction **19m25s**,
  local checks/pushes **3m46s**, CI/waiting **8m57s**, release verification **45s**. First complete candidate to verified
  package: **17m13s**, including both builds and the correction. A visual check during the first build caught low ground
  being colored as ocean; the second code push fixes that. Both exact-commit push builds were reused, without duplicate
  dispatch. Their CI durations were **5m25s** and **6m06s**, overlapping the correction; summed runner time **17m48s**.
  Publication notes use the documentation-only path.

## Published acquisition fixes and scenery — 2026-10-04

Code: [`1951934`](https://github.com/biscoBen/FFR-Vison-Studio/commit/1951934b84a49fe975e3524ff8e42db10b4ae430).
[Verified Windows test release / run 37233295971](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37233295971).

- Reduce ordinary cave visions to 60% of their previous sprite scale, preserving Crystal Fina's tested crystal size.
- Wire saved vendor choices into native shop inventories; Mitra Weapons no longer falls back to Mitra Items. Preserve
  original contents, purchase limits and native vision acquisition. Combined vendors use an existing inventory tab.
- Correct 2D coastal marker alignment by displaying native captures as squares instead of stretching them to region
  bounds. Retain saved cave coordinates and the reversible map projection.
- Replace the placement preview's wireframe with native painted terrain, paths, shaded scenery and tree/bush instances.
  Lighting is simplified, transparent shaders are omitted, and coverage is limited to available native reference regions.

- Verification: Flutter analysis, 205 local Flutter tests (one existing platform skip) and 258 Python tests (three
  existing platform/reference skips). All Windows gates passed, including fresh frozen-engine startup and shortcut/updater
  tests. All 125 vendor choices resolve to native inventories, with each assigned vision present exactly once and the
  Mitra Weapons assignment absent from Mitra Items. Native asset read-back and IoStore round-trip preserve all 44 cave
  map/timeline packages, including exact float32 sprite scales, collision, grants and returns. The authenticated release
  download matches the code commit and checksum; all 54 packaged resources and the scenery archive's members are verified.
  These checks do not execute Resonance gameplay; lighting/shader parity and later-game vendor accessibility need live tests.
- Measured request start to verified package: **26m39s** — implementation/investigation **18m05s**, local checks/corrections/push
  **3m00s**, CI **5m13s**, verification **0m21s**. First complete candidate to verified package: **8m34s**;
  native read-back caught a non-binary float32 scale and it was corrected before pushing. CI used **9m04s** of runner time.
  One code push and one reused Windows build. Publication notes use the documentation-only path.

## Published precise cave placement — 2026-10-04

Code: [`011d0e2`](https://github.com/biscoBen/FFR-Vison-Studio/commit/011d0e287548b2a69cf918d857e1ffac4cfe224f).
[Test package / run 37229153450](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37229153450).

- Add/edit cave placements with local 3D terrain dragging, precise X/Y/Z, ground snapping, rotation and size controls.
  Entrances default to 75% of the previous size. Ground their footprint centers using native terrain instead of a
  shared fixed height; preserve cave identities and update every assigned vision when editing a shared placement.
- Give assigned cave visions Crystal Fina's tested sprite scale and make the cave-to-crystal-room transition white.
  Keep the existing shrine model and its native glow. The preview uses simplified prop outlines and omits game
  shaders/instanced foliage; terrain references cover Grandshelt and Dirnado, with manual height elsewhere.
- Validation: Flutter analysis, full Flutter/Python suites, Windows frozen-engine startup and launcher/updater gates
  passed. Native SDK/IoStore checks cover 44 level/timeline packages; four mesh bounds match their saved centers,
  terrain bases and 75% size. The exact-commit release ZIP and 52 packaged resources/data files were verified.
  Live placement, the new white portal transition and sprite sizing still need an in-game check.
- Timing: 29m 06s from request to verified package, including investigation/development checks. Final candidate to
  verification took 7m 29s; CI elapsed 5m 09s and used 8m 44s of runner time. One code push, one reused push build.

## Published cave-marker removal — 2026-10-04

Code: [`86600ac`](https://github.com/biscoBen/FFR-Vison-Studio/commit/86600ac8c33c324eabbe0268dbcdd8e53ddfcf64).
[Verified Windows test release](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37227168310).

- Right-click a visible Acquisition cave marker to remove that saved placement. Clear every current vision assigned
  to it back to Mitra's shop while preserving other edits and Random/Hide settings; disable the legacy Crystal Fina
  switch when removing its cave. Hidden markers cannot be removed, overlapping markers list their cave names, and
  removal is blocked during a mod build. Rebuild/install and restart Resonance to apply the removal in-game.
- Validation: Flutter analysis, full Flutter/Python suites, Windows frozen-engine startup and launcher/updater checks
  passed. Focused tests cover zoom/pan, overlapping and hidden markers, cancellation, shared assignments, persistence
  and blocked/failed writes. Verified the downloaded package's commit, checksum and 50 bundled resources.

## Published assigned Resonance Caves — 2026-10-04

Code: [`203f976`](https://github.com/biscoBen/FFR-Vison-Studio/commit/203f976f70e684de6fa77be424a2b2d5f99c3e16).
[Verified Windows test release](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37225348474).

- Build saved cave assignments as **Resonance Caves**, with each selected vision's sprite, native item grant and
  once-owned disappearance. Reuse the Crystal Fina stone cave, button-operated portal, blockers, crystal room,
  controller-compatible obtain flow and return point. Group shared cave assignments with independent vision grants.
  Preserve stable map identities across rebuilds, append entrances/collision to the same world without replacing
  previous caves, and use the chosen native entrance mesh. Remove cave-selected visions from Mitra's shop; original
  vision acquisition and the legacy Crystal Fina switch remain compatible. Vendor routing is still a planning feature.
  Native tables and all four entrance types pass asset serialization with independent shared-cave grants. Live terrain,
  appearance and acquisition checks remain necessary; automated asset checks do not execute gameplay.
- Validation: Flutter analysis and the full Flutter/Python suites, Windows frozen-engine startup, launcher/updater
  checks and publication gates passed. All 44 generated native map/timeline packages survived IoStore packing and
  extraction; the downloaded release's provenance, checksum and 50 bundled resources were verified.

## Published native vendors and user-placed caves — 2026-10-04

Code: [`37f42ba`](https://github.com/biscoBen/FFR-Vison-Studio/commit/37f42ba2ebf41dc4b8fbe3f9da66c26b7f3085b5).
[Test package](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37222696350),
[Windows run 37222696350](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/37222696350).

- Replace specific acquisition checkboxes with **Shop**/**Cave** and dropdowns. Include all native shop inventory and
  combined-shop records, preserving IDs/chapter variants; later-game/moving shops without known coordinates have no pin.
- Right-click the map to save a named cave at the clicked location and choose from four native entrance model previews.
  Keep a shared persistent pool beginning with our Crystal Fina cave; the user places the remaining caves toward 30.
  Selecting a cave centers its marker. Preserve spoiler hiding, random rerolls and saved character configs; include a
  selected custom cave snapshot so configs can restore it. These are Studio placements; game acquisition is still unchanged.
- Verification: Flutter analysis, 197 passing local Flutter tests and 241 Python tests (existing local platform/reference
  skips). Cover pan/zoom placement, cancellation, selecting and centering caves, thirty user-chosen saved locations,
  config restoration and preservation of corrupt files. All Windows gates passed, including genuine frozen-engine
  startup and launcher/updater checks. Verify authenticated release checksum, exact-commit provenance and all 50
  packaged resource files. No new live game behavior is introduced.
- Measured request clock to verified package: **40m58s** — **24m28s investigation/implementation** (including reference
  gathering), **6m40s local checks, correction and pushes**, **9m30s CI/waiting**, **20s release verification**.
  First complete candidate to verified package: **16m30s**. The final CI run took **4m36s**, using **7m58s runner time**.
  The first build failed because Windows read UTF-8 source labels as cp1252; fix explicit encoding and verify native
  regeneration under that default. Two code pushes, two push builds and one cancelled helper-generated retry consumed
  **23m03s total runner time**. Publication notes use the documentation-only path.

## Published acquisition planning UI and native map — 2026-10-04

Code: [`0e9ad33`](https://github.com/biscoBen/FFR-Vison-Studio/commit/0e9ad33595202f23b73977b5d1e59dc9d1f64ca8).
[Test package](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37217313830),
[Windows run 37217313830](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/37217313830).

- Add an **Acquisition** tab with Random and Hide for spoilers enabled by default. Save each vision's
  preview selection in its character configuration; either Random transition chooses a different site.
  Reveal the selected, disabled option while Random is on, or choose manually with it off. Hide both
  choices and marker for spoilers. Start with Mitra shop, Earth Shrine and the crystal cave.
- Use the game's own world-map menu captures and native coordinates, with zoom, mouse dragging and
  a full-map view. Bundle the images for offline use. These preferences only plan future acquisition;
  installing still uses the existing shop/cave behavior. No game acquisition logic changes in this update.
- Verification: Flutter analysis, 190 local Flutter tests and 237 Python tests (existing local platform/reference
  skips). Test spoiler hiding, rerolling, manual selection, config persistence, zoom/pan and minimum-width layout;
  verify native texture decoding, map projection and image checksums. All Windows gates passed, including genuine
  frozen-engine startup and launcher/updater checks. Authenticated release checksum, exact-commit provenance and
  all 45 packaged resource files verified. No new live game behavior is introduced.
- Measured from the initial request clock to verified package: **35m16s** — **20m47s investigation/implementation**,
  including extraction and reference gathering, **9m22s local checks, test corrections and push**, **4m46s CI**,
  **21s release verification**. First complete candidate to verified package: **14m29s**. CI used **8m08s runner time**.
  One code push and one reused build; publication notes use the documentation-only path.

## Published complete directional FFBE field selector — 2026-10-03

Code: [`378436a`](https://github.com/biscoBen/FFR-Vison-Studio/commit/378436a084e635d792a177b4419bc76305e29c8b).
[Test package](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37174463870),
[Windows run 37174463870](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/37174463870).

- Expand overworld appearances to all nine reviewed directional FFBE running sheets: five 4-way and four 8-way,
  with normal unit images and direction labels. Preview idle/walk/run; exclude inserted standing frames and
  shadow-only rows. Keep four-way models visible diagonally using their own cardinal poses. Bundle checksum-verified
  assets for offline use and preserve saved Vagrant Rain choices, independent battle appearances and cycling.
  One cloaked sheet is explicitly unidentified; Sakura lacks a usable run. The complete town-sheet and unit motion-name
  inventories were inspected at the pinned FFBE dump revision; side-view battle runners are excluded by request.
- Verification: Flutter analysis and 183 local Flutter tests; 234 Python tests (3 local reference/platform skips).
  All nine models' 468 clips, frame references, lengths, texture dimensions and pixel payloads survived UE5.6 IoStore
  readback using the actual generator with a genuine field-class donor. All Windows gates passed, including the
  real frozen-engine startup, launcher/updater tests and release publication. Authenticated release checksum,
  exact-commit provenance and all 35 packaged files verified. Live game/controller behavior still needs retesting.
- Measured from the first clock reading during initial setup to verified package: **28m14s** — **17m12s audit/implementation**,
  **4m35s local checks, integration correction and push**, **5m48s CI**, **39s release verification**. Earlier setup
  before that clock reading is unrecorded. First complete candidate to verified package: **11m03s**.
  CI used **8m47s runner time**. One code push and one reused build; publication notes use the documentation-only path.

## Published cycled party diagonal visibility repair — 2026-10-03

Code: [`81ca68f`](https://github.com/biscoBen/FFR-Vison-Studio/commit/81ca68fc44d66c73ea2718c619d00a9fd4281a59).
[Test package](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37169692104),
[Windows run 37169692104](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/37169692104).

- Repair disappearing cycled party sprites: Lasswell and several other native projects contain named diagonal
  clips pointing to zero-sized cells. Private field copies replace unusable diagonal idle/walk/run clips with
  visible front/back cardinal clips, keeping genuine diagonal frames, textures and original game assets intact.
  Preserve diagonal movement and LB/L1 controls. Supply Rain's overworld idle aliases for all cycling models and
  Vagrant Rain. Update Studio, rebuild/install the mod and restart Resonance to apply the repaired models.
- Verification: 230 local Python tests (3 reference/platform skips), actual feature-builder readback of seven native
  private projects and the field bank, plus all 52 Vagrant Rain clips through UE5.6 IoStore. All 256 required
  direction/motion combinations have usable geometry. All Windows gates passed, including Flutter, genuine
  frozen-engine startup and launcher/updater tests. Authenticated release checksum, exact-commit provenance and
  all 33 packaged files verified. Live controller behavior still needs retesting; missing diagonal art uses cardinal poses.
- Measured from the first recorded clock reading during initial inspection to verified package: **17m55s** —
  **9m47s investigation/implementation, including clarification**, **3m01s local checks/push**, **4m34s CI**,
  **32s package verification**. First complete candidate to verified package: **8m08s**. CI used **7m58s runner time**.
  One code push and one reused build; publication notes use the documentation-only path.

## Published field-leader launch serialization repair — 2026-10-03

Code: [`8d17073`](https://github.com/biscoBen/FFR-Vison-Studio/commit/8d17073f5af8fa835fdb68ff5073c60396d24082).
[Test package](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37168358782),
[Windows run 37168358782](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/37168358782).

- Fix the launch serialization fault with **Cycle walking character (LB / L1)** enabled. Dark Fina's four private
  diagonal idle aliases now include their native binary keyframes as well as reflected animation properties.
  Preserve all original clips and keyframes; reject incomplete or unsupported payloads during generation.
  After updating Studio, rebuild/install the mod to replace the broken asset.
- Verification: 228 Python tests (3 local reference/platform skips), missing-tail regression, actual feature-builder
  readback and all 29 clips/6,064 keyframe bytes through UE5.6 IoStore. All required Windows gates passed, including
  Flutter, real frozen-engine startup and launcher/updater checks. Reused the one push run; authenticated checksum,
  exact-commit provenance and all 33 packaged files verified. Resonance launch/controller behavior needs live retesting.
- Measured from the first recorded clock reading to verified package: **10m46s** — **4m01s remaining implementation**,
  **47s local checks/push**, **5m28s CI**, **30s package verification**. Earlier initial inspection took a few minutes
  before that clock reading and is excluded from this measured window. First complete candidate to verified package:
  **6m45s**. CI used **7m52s runner time**. Publication notes use the documentation-only path.

## Published field-leader cycling and window controls — 2026-10-03

Code: [`4c93c15`](https://github.com/biscoBen/FFR-Vison-Studio/commit/4c93c15b9662b2826cbf54c0790b8badbbd94561).
[Test package](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37167054120),
[Windows run 37167054120](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/37167054120).

- Add opt-in **Cycle walking character (LB / L1)**, also available on F6, using the active party's native field
  sprites and independent overworld selections. Preserve original actor identity and story asset indices; suspend
  the cosmetic replacement around events, battle, menus and vehicles. Add private diagonal idle aliases for Dark
  Fina's four-direction idle poses. Install/remove only Studio's owned Lua mod using the already working UE4SS
  loader. No loader download, save writes or battle model changes. The uploaded native SDK verifies signatures;
  controller behavior and scene transitions require an in-game trial after package verification.
- Give Studio explicit light/dark title-bar controls so minimize, maximize/restore and close remain visible.
  Preserve window dragging and the existing close-during-build confirmation. Included in the cycling build.
- Verification: 180 local Flutter tests, analysis, 226 Python tests (3 local reference/platform skips), executable
  Lua callback/guard tests, native field-bank and Dark Fina project readback through UE5.6 IoStore. All final Windows
  gates passed, including the genuine frozen-engine startup and launcher/updater checks. Reused the final push run;
  authenticated release checksum, exact-commit provenance and all 33 bundled files verified. Native gameplay and
  controller behavior still require the user's live trial; the runtime dump verifies loader startup and signatures.
- Measured from receiving the usable native reference to verified package: **30m29s** — **15m57s implementation**,
  **4m44s checks/correction/push**, **8m56s across two CI runs**, **52s release verification**. The first run compiled
  successfully but an existing settings-map expectation omitted the new cycling flag; its gate prevented publication.
  Updated that test, ran the full local Flutter suite, then verified the second run. CI used **16m05s runner time**.
  First complete candidate to verified package: **14m32s**. The original movement/cycling request to this verified
  package spans **1h32m04s**, including the earlier movement/revert releases and collecting/testing runtime references.
  These publication notes use the documentation-only path; they do not trigger another app build.

## Published independent party appearance reversion — 2026-10-03

Code: [`b34af8b`](https://github.com/biscoBen/FFR-Vison-Studio/commit/b34af8bb3d649194f87f4f811cc492e6fbc63377).
[Test package](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37164080230),
[Windows run 37164080230](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/37164080230).

- Party characters' **Revert to original** offers **Revert battle only**, **Revert overworld only** and **Revert both**
  from home or their management page. Reverting one keeps the other appearance and unrelated pending roster edits.
  Rename **Edit battle appearance** to **Manage appearances** for previews and config save/load;
  **Change battle model** still opens the FFBE picker. Build/install to apply appearance reverts to the game.
- Verification: focused party, native-vision and picker tests, Flutter analysis, failed-save/cancel/build guards,
  all required Windows Flutter/Python checks (218 Python tests, 3 reference/platform skips), real frozen-engine startup,
  launcher/updater checks and publication. Exact push build reused; authenticated release checksum/provenance and all
  31 bundled files verified. Includes the already published Vagrant Rain movement repair; no cycling handler yet.
- Measured from this additional revert request to verified package: **14m11s** — **5m16s implementation/investigation**,
  **1m17s local checks/corrections/push**, **6m21s CI** and **1m17s release verification**. CI used **10m17s runner time**.
  First complete candidate to verified package: **8m55s**. One code push/build for this request; notes use the
  documentation-only path. The earlier movement task's builds and timings are recorded below.

## Published Vagrant Rain movement loops and directions — 2026-10-03

Code: [`c26b650`](https://github.com/biscoBen/FFR-Vison-Studio/commit/c26b650fb3c2756f59af289e9a8edee06850b401).
[Test package](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37163210493),
[Windows run 37163210493](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/37163210493).

- Remove the identical standing pose from Vagrant Knight Rain's movement loops and use the six moving cells.
  Correct swapped northwest/northeast rows for idle, walk and run; match the Studio preview's rows and cycle.
  Keep native movement modes: ordinary full-stick jogging and B-held running share `dash` at different rates.
  Rebuild/install after updating to regenerate field assets. In-game smoothness and directions need retesting.
- Verification: 218 final local Python tests (3 reference/platform skips), Flutter analysis, bundle checks,
  genuine native table/project/texture generation and readback, 44 decoded clip timings and 31 packaged files.
  All required Windows checks and release gates passed for the final commit; exact-commit reuse and authenticated
  release download verified. Original party walk/run coverage and field input mappings inspected from the new archive.
- Measured to verified package: **18m20s from request**, including **4m16s initial investigation/implementation**,
  **2m37s local checks/revision/push**, **10m36s across two CI runs** and **51s release verification**.
  The direction correction arrived during the first build; both builds passed and the final one was reused.
  CI used **16m51s runner time**. First complete candidate to verified package: **14m04s**; overlapping correction
  work is included in the elapsed clock. Publication notes use the documentation-only path.

## Published cave navigation and controller repair — 2026-10-03

Code: [`1a53b30`](https://github.com/biscoBen/FFR-Vison-Studio/commit/1a53b301e44b2e143b6c4d6fa0f58bbedeb51aed).
[Test package](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37159561491),
[Windows run 37159561491](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/37159561491).

- Both glowing-room exit routes still returned outside the cave. Replace the stone cave's inherited navigation
  reference with private exit/portal links; register return point 1 in its persistent level and bind its navigation
  area. Require a button to leave the stone cave, preventing automatic re-exit on arrival. Restore the earlier
  event-only acquisition/talk flow after the transition pre-event regressed controller confirmation. Preserve
  Fina's confirmed grant, size and collision. Cave return and controller confirmation require a live-game retest.
- Verification: 218 local Python tests (3 reference/platform-dependent skips), Flutter analysis, bundle checks,
  native table/scene readback, all 12 generated assets through IoStore and all 31 packaged files. All required
  Windows Flutter, Python, frozen-engine startup, launcher/updater and publication gates passed for the exact commit.
- Measured to verified package: **12m09s from request** — **4m59s investigation/implementation**, **1m54s local
  checks and push**, **4m38s CI**, **38s release verification**. First complete candidate to verified package:
  **7m10s**. CI used **8m07s runner time**. One code push/build, reused through authenticated release download;
  publication notes use the documentation-only path.

## Published cave transition ownership — 2026-10-03

Code: [`0dd312a`](https://github.com/biscoBen/FFR-Vison-Studio/commit/0dd312a809a1c8fe93b5ce6209233592262e800a).
[Test package](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37157852608),
[Windows run 37157852608](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/37157852608).

- Give Crystal Fina's button one regular transition to stone cave 29990, portal point 1, with acquisition as its
  pre-event. Clear the NPC's competing talk binding and the grant event's separate map change. Preserve her confirmed
  grant, white flash, size and collision. Run 37156080907 still returned to the overworld after reinstall; this revised
  event flow needs a live-game retest. Correct the earlier fallback hypothesis in `SCENE_PLACEMENT.md`.
- Verification: 216 local Python tests (3 reference/platform-dependent skips), Flutter analysis, bundle checks,
  native table/scene readback, all 11 scene assets through IoStore, and all 31 packaged files. All required Windows
  Flutter, Python, frozen-engine startup, launcher/updater and publication gates passed for the exact code commit.
- Measured to verified package: **16m59s from investigation start** — **9m54s investigation/implementation**,
  **1m28s local checks and push**, **5m10s CI**, **27s release verification**. First complete candidate to verified
  package: **7m05s**. CI used **9m02s runner time**. One code push/build, reused through authenticated release download;
  publication notes use the documentation-only path.

## Published cave acquisition return — 2026-10-03

Code: [`4a5707a`](https://github.com/biscoBen/FFR-Vison-Studio/commit/4a5707a088b265288dbb1dc022620f8c3cc12e87).
[Test package](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37156080907),
[Windows run 37156080907](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/37156080907).

- Give Fina's acquisition button the same explicit stone-cave/portal return destination as its event, including both
  default and conditional routes. Preserve the working grant, white flash, size, input and collision. Nudge Fina
  another 16 units right toward the floor glow. Live return and final alignment still require retesting.
- Verification: 215 local Python tests (3 reference/platform-dependent skips), Flutter analysis, bundle checks,
  native readback and all 11 scene assets through IoStore, including the serialized return routes and portal point.
  All required Windows checks/publication passed; authenticated download and all 31 packaged files verified.
- Measured to verified release: **11m18s from task start** — **3m44s investigation/implementation**, **2m01s local
  checks/corrections and push**, **4m46s CI**, **47s release verification**. First complete candidate to verified
  release: **7m34s**. CI used **8m31s runner time**. One code push/build; no duplicate dispatch.

## Published native cave acquisition and blockers — 2026-10-03

Code: [`38b30bf`](https://github.com/biscoBen/FFR-Vison-Studio/commit/38b30bf15b47d0ca14ff4c110e6afb34b1931060).
[Test package](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37154705737),
[Windows run 37154705737](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/37154705737).

- Crystal Fina's acquisition now executes the native event header/footer timeline with her actual allocated vision ID,
  obtain screen and return to the stone cave. Keep her confirmed size and input; move her slightly right toward the glow.
- Replace ineffective generic entrance/portal boxes with native cooked BlockingVolumes in private collision levels.
  Keep button interaction, original world streams and story data. Record the live-test failures and native mechanisms in
  `SCENE_PLACEMENT.md`.
- Verification: 215 local Python tests (3 reference/platform-dependent skips), Flutter analysis, bundle checks, native
  grant-table readback, all 11 scene assets through SDK/IoStore, and all 31 packaged files. Required Windows Flutter,
  frozen-engine startup, Python, launcher/updater and publication gates passed. Inventory acquisition, hiding on return,
  blocking and precise glow alignment still require a live-game retest.
- Measured to verified release: **24m49s from task start**, including **12m52s investigation/implementation**, **5m56s
  local checks/corrections and push**, **5m09s CI** and **52s release verification**. First complete candidate to verified
  release: **11m57s**. CI used **8m17s runner time**. One code push/build; exact-commit reuse and authenticated download.

## Published grounded cave interaction and collision — 2026-10-03

Changes in [`5b8197e`](https://github.com/biscoBen/FFR-Vison-Studio/commit/5b8197ed89c562972f826bfe9aa7f93f40185d07),
[test package 37150366752](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37150366752).

- Reduce cave Crystal Fina's sprite by 15% and center her between the room's native acquisition lights.
  Add a manual acquisition trigger attached to her grounded capsule, independent of sprite size/lift.
- Register separate world-static blockers for the overworld entrance and cave portal; remove inherited
  transition archetypes and extend portal collision below the native floor plane. Document scene placement rules.
  Serialized assets and Windows packaging are checked; final visual alignment and gameplay input need an in-game test.
- Passed analysis, 212 local Python tests (three frozen-engine contracts deferred to Windows), bundle checks,
  native SDK generation/readback and actual IoStore packing/extraction for all seven maps. Windows passed its full
  suites, fresh engine startup, launcher/updater checks and compilation before publication. Authenticated download
  verified the ZIP checksum, exact commit/run and all 31 bundled files; the packaged generator reproduces the checked maps.
- One code push and one reused automatic build. Request to verified package: **27m14s**; investigation/implementation
  **16m56s**, final local validation/corrections **2m32s**, push/CI **7m22s**, release verification **24s**.
  First completed candidate to verified package: **10m18s**, including later local corrections. CI itself took
  **7m18s**, with **11m08s** summed job execution; validation (**6m47s**) was the longest job. These are measured
  intervals; publication-note bookkeeping follows package verification and creates no additional app build.
  Rebuild/install the mod and restart Resonance. Live collision/input and the brightest rendered glow still need
  an in-game smoke test; the workspace has native reference assets but no running game or native C++ source.

## Published combined cave/overworld installation and direction fixes — 2026-10-03

Changes in [`a98414f`](https://github.com/biscoBen/FFR-Vison-Studio/commit/a98414ffebd4236be926bec3b0e3c27655545a0a),
with the Windows test correction in [`2a3c53b`](https://github.com/biscoBen/FFR-Vison-Studio/commit/2a3c53b8dad94883ceceee0db3f46f93e5a2eeab),
[test package 37147289426](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37147289426).

- Fix installation with both Crystal Fina's cave and a party overworld replacement enabled: verify their combined
  shared map-unit table, retaining exact checks for unrelated edits, missing rows and incorrect acquisition data.
  Include the failing table in future testing-verification errors.
- Correct Vagrant Knight Rain's swapped east/southeast sheet rows in both the walking viewer and generated
  idle/walk/run animations. Rebuild/install the mod to regenerate the field assets.
- Passed analysis, the affected viewer test, 211 local Python tests (three engine contracts deferred to Windows),
  bundle checks and both actual install-verification entrypoints against the SDK-built combined native table.
  The corrected directional project also generated/read back through the real SDK. Windows passed full suites,
  fresh frozen-engine startup, launcher/updater checks and compilation before publication. Verified the authenticated
  ZIP checksum, exact commit/run and all 31 bundled extension/preset files. Update Studio, rebuild/install the mod and
  restart Resonance. Full in-game walking and installation still require a user retest; no game runtime is available here.
- The first CI run blocked publication on a Windows-only path assumption in the new regression test. Corrected the
  fixture, added an explicit backslash-path check and reused the second push's build. Cancelled the helper's redundant
  retry of the failed commit. Master is unchanged; publication notes use the documentation-only path.
- Published at 12:21:20 PDT; final CI took 5m01s (9m06s summed job execution). Across the failed run, cancelled retry and
  successful run, runner execution totaled 21m43s. First complete candidate: 12:09:20 PDT; verification finished at
  12:22:25 PDT (13m05s including local checks, failed CI, correction, new CI and package verification).
  From task start at 12:06:01 PDT, the verified package took 16m24s: implementation 3m19s, initial local checks/push
  1m10s, CI including the Windows test correction 10m52s and release verification 1m03s.

## Published party overworld appearances and cave interactions — 2026-10-03

Changes in [`fe8ed80`](https://github.com/biscoBen/FFR-Vison-Studio/commit/fe8ed800a0e7eb628e8c016e4c4f795aca1361e6),
[test package 37145810773](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37145810773).

- Double cave Crystal Fina's sprite scale and shift her right toward the floor glow, keeping collision-based settling
  and once-only acquisition. Require input at the overworld entrance and add an invisible blocking box at the crystal
  portal while preserving its larger interaction area.
- Add independent **Edit overworld appearance** choices for party characters, initially limited to Vagrant Knight
  Rain. Bundle its eight-direction idle/walk/run sheet, preview the walking frames, and preserve battle choices and
  both appearances in saved configs. Redirect primary field assets only; ordinary scenes using them also show the
  new look. Placement, walking direction and scene compatibility still require an in-game check.
- Passed analysis, affected Flutter checks, 210 Python checks (three engine contracts deferred locally to Windows),
  bundle verification and native table/map/field asset SDK and actual IoStore pack/extract readbacks. Windows passed
  the full suites, fresh frozen-engine startup including the new field importer, launcher/updater tests and
  compilation before publication. Verified the authenticated ZIP checksum, exact commit/run, all 31 bundled
  extension/preset files and compiled picker controls. One code push and one reused automatic build; master is
  unchanged. This workspace has no Resonance runtime. Update Studio, rebuild/install the mod and restart the game;
  choose **Party characters → Edit overworld appearance → Vagrant Knight Rain → Use this model** to test walking.
- Published at 11:57:20 PDT. CI took 5m16s, with 8m37s summed job execution. First complete candidate: 11:48:25 PDT;
  verification finished at 11:58:05 PDT (9m40s including local corrections/checks, push, CI and verification).
  From task start at 11:34:51 PDT, the verified package took 23m14s: implementation 13m34s, local corrections/checks/push
  3m40s, CI 5m16s and release verification 44s. Publication notes use the documentation-only path without another app build.

## Published Crystal Fina floor collision fix — 2026-10-03

Changes in [`b7446b1`](https://github.com/biscoBen/FFR-Vison-Studio/commit/b7446b14ce7462eb0315f24683747f2dfda1411d),
[test package 37143490113](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37143490113).

- Fix cave Crystal Fina spawning below the visible platform: the ground mesh's origin was not its surface.
  Spawn her above the platform at the clear crystal's light and enable native gravity/floor collision for the
  stationary NPC, including physics without a controller. Her capsule and interaction volumes settle together;
  retain the enlarged floating sprite, manual portal and once-only acquisition. In-game settling still needs a
  retest because this workspace has no Resonance runtime. Update Studio, rebuild/install the mod and restart the game.
- Passed 205 local Python checks with three engine contracts deferred to Windows, bundle verification, native table
  preservation and all seven maps' SDK and actual IoStore pack/extract readbacks. Confirmed the floor-physics settings,
  capsule, attached interaction, sprite scale and manual portal survive packing. Windows passed the full suites,
  frozen-engine startup, launcher/updater tests and compilation before publication. Verified the authenticated ZIP
  checksum, exact commit/run and all 29 bundled extension/preset files. One code push and one reused automatic build;
  master is unchanged. Vagrant Knight Rain's field-sprite investigation made no app changes.
- Published at 11:19:13 PDT. CI took 4m05s, with 7m23s summed job execution. First complete candidate: 11:13:41 PDT;
  package verification finished at 11:19:43 PDT (6m02s, including local checks, push, CI and verification).
  From task start at 11:08:06 PDT, verification took 11m37s: implementation 5m35s, local checks/push 1m30s,
  CI 4m05s and release verification 27s. Publication notes use the documentation-only path without another app build.

## Published reachable Crystal Fina and crystal interaction — 2026-10-03

Changes in [`37f71d0`](https://github.com/biscoBen/FFR-Vison-Studio/commit/37f71d025309d17fcf4772bbcabda5da78fa59fd),
[test package 37141486449](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37141486449).

- Enlarge cave Crystal Fina to 2.5 times the previous sprite scale and center her above the clear crystal's ground
  glow. Put her foot and interaction volume directly on the native floor, with a 40-unit sprite-only float offset;
  the stationary NPC did not settle from the previous raised spawn. Require interaction with the stone cave's
  crystal to enter the glowing room, using the native manual-transition setting. In-game size, reach and interaction
  still need a retest; the workspace has no Resonance runtime.
- Passed 204 local Python checks with three engine contracts deferred to Windows, bundle verification and all seven
  generated maps' SDK and actual IoStore pack/extract readbacks. Confirmed the floor-level foot, enlarged sprite,
  manual inner portal and automatic cave exits survive packing. Windows passed the full Flutter/Python suites,
  frozen-engine startup, launcher/updater tests and compilation before publication. Verified the authenticated ZIP
  checksum, exact commit/run and all 29 bundled extension/preset files. One code push and one reused automatic build;
  master is unchanged. Update Studio, rebuild/install the mod and restart Resonance to test the change.
- Published at 10:48:08 PDT. CI took 5m56s, with 9m35s summed job execution. Flutter setup on the validation runner
  took 2m57s. First complete candidate: 10:39:26 PDT; package verification finished at 10:48:53 PDT (9m27s, including
  local corrections/checks, push, CI and verification). From task start at 10:34:24 PDT, verification took 14m29s:
  implementation 5m02s, local corrections/checks/push 2m48s, CI 5m56s and release verification 43s.
  Publication notes use the documentation-only path without another app build.

## Published Crystal Fina cave placement and glow cleanup — 2026-10-03

Changes in [`1243a6f`](https://github.com/biscoBen/FFR-Vison-Studio/commit/1243a6fb29ba84ba876438893118237d09941a53),
[test package 37139668745](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37139668745).

- Lower the world-map Crystal Fina cave entrance by 80 units and reduce its model to 80% scale. Keep the existing
  stone cave and crystal portal marker. Place Fina above the native clear crystal's elevated pedestal instead of
  below the room floor, retaining her floating sprite, once-only acquisition and return to the stone cave.
  Remove the two leftover green crystal glows while preserving the room's fog and lighting. Visual placement and
  acquisition still require an in-game retest; this workspace has no Resonance runtime.
- Passed 202 local Python checks with three engine contracts deferred to Windows, bundle verification, native table
  safeguards and all seven maps' SDK readbacks and actual IoStore packing/extraction. Windows passed full Flutter
  and Python checks, frozen-engine startup, launcher/updater tests and compilation before publication. Verified the
  authenticated release ZIP checksum, exact commit/run and all 29 bundled extension/preset files. One code push and
  one reused automatic build; master is unchanged. Rebuild/install the mod to apply the map changes.
- Published at 10:16:50 PDT. CI took 4m16s, with 7m26s summed job execution. First complete candidate: 10:10:13 PDT;
  package verification finished at 10:17:27 PDT (7m14s, including final local checks/push, CI and download verification).
  From task start at 10:03:47 PDT, verification took 13m40s: implementation 6m26s, local checks/push 2m24s, CI 4m16s
  and release verification 34s. Publication notes use the documentation-only path without another app build.

## Published cave packing fix and roster removal menu — 2026-10-03

Changes in [`f52bbb6`](https://github.com/biscoBen/FFR-Vison-Studio/commit/f52bbb656086daed7d467fa8a1fa9ad33e9fd49a),
[test package 37137462441](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37137462441).

- Fix the cave entrance's reported `Bad name index 127/62` crash: retain added overlap/delegate names in the
  packed map header without reordering original names. Reproduced the discarded callbacks through actual IoStore
  conversion, then verified all seven generated maps retain their authored delegate/animation names after packing
  and extraction. Reject a truncated name header during building. In-game cave travel still needs a Resonance retest.
- Right-click an Added vision and choose **Remove vision**, with the existing confirmation, cancellation and
  removal safeguards. Original visions return to Defaults when their overrides are removed. Builds and the
  cave-required Crystal Fina profile remain protected. Rebuild/install the mod after updating Studio to apply the map fix.
- Passed local analysis and 201 Python checks with three engine contracts deferred to Windows, and focused mouse
  removal tests. Windows passed the full Flutter/Python suites, real frozen-engine startup, bundle and launcher/updater
  checks and compilation before publication. Verified the authenticated ZIP checksum, exact commit, all 29 bundled
  extension/preset files and compiled removal menu. One code push and one reused automatic build; master is unchanged.
- CI took 4m38s, with 8m06s summed job execution. First complete candidate: 09:35:42 PDT; package verification finished
  at 09:41:39 PDT (5m57s, including final local checks/push, CI and verification). From the first recorded investigation
  time at 09:24:20 PDT, verification took 17m19s, plus the initial branch/instruction reads before that timestamp.
  Publication notes follow through the documentation-only path without another app build.

## Published Crystal Fina cave — 2026-10-03

Changes in [`3c4f415`](https://github.com/biscoBen/FFR-Vison-Studio/commit/3c4f415c951f5aa32d5feb177536a11627074a1b),
[test package 37135304953](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37135304953).

- Add an opt-in Crystal Fina cave north of the Earth Shrine–Mitra road, using private copies of the native stone cave
  and glowing Leah/Tronn room. A crystal portal leads to the floating bundled Crystal Fina. Request the native
  vision-obtain dialog and a white transition back to the stone cave. Ownership prevents repeat grants and hides
  her on subsequent visits. Enabling adds her bundled profile if needed, using its allocated ID and preserving edits.
- Verified the native tables and all seven cooked maps through engine SDK writes/readbacks, preserving original
  world actors and story rows. Passed analysis, 200 Python and 41 focused Flutter tests; Windows passed the full
  suites, real frozen-engine startup, bundle and launcher/updater/import checks and compilation before publication.
  Verified the authenticated ZIP checksum, exact commit, compiled cave switch and all packaged extension files.
  Cave placement, movement, white flash and acquisition-screen presentation still require an in-game check;
  there is no game runtime in this workspace. Master and engine hosting are unchanged.
- Two code pushes/builds: the first correctly blocked publication on a stale Windows startup assertion expecting
  extension 1.2.0 instead of 1.2.1. Corrected it and checked the installed cave module. Reused both push runs;
  successful CI took 4m48s, with 8m48s total CI elapsed and 15m21s summed job execution across both attempts.
  First complete candidate: 08:51:55 PDT; package verification finished at 09:08:12 PDT (16m17s, including corrections,
  local checks, both builds and download verification). From the original cave request at 22:32:15 PDT the previous
  evening, verification took 10h35m57s, including the 9h36m55s interval awaiting split reference uploads. Active work
  totaled 59m02s: implementation/investigation and development checks 42m45s, final local checks/revision/push 5m12s,
  CI 8m48s, package verification 2m17s. Publication notes follow through the documentation-only path.

## Published repeated-model portrait refresh — 2026-10-02

Changes in [`85b9f0c`](https://github.com/biscoBen/FFR-Vison-Studio/commit/85b9f0ccc8eb73b17a10efaf75003513ef43b543),
[test package 37095880954](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37095880954).

- Refresh Studio's roster portrait when changing a party character's replacement model again. Include the selected
  FFBE form in its image-cache URL so the same party slot can show successive models without reverting first.
- Passed analysis and all five party-character tests, including consecutive replacement saves, changed image providers
  in the retained card, reuse of a previous form's own portrait and restoration of the original portrait. Windows passed
  the full Flutter/Python suites, real frozen-engine startup, bundle, launcher/updater/import checks and compilation.
  Verified the authenticated ZIP checksum, exact commit and all bundled extension files. Retain the complete unit-picker
  fix and previous features; master is unchanged.
- One portrait code push and one reused build after the separate picker release. CI took 4m22s, with 7m38s summed job
  execution. First portrait candidate: 21:13:56 PDT; ZIP verified at 21:19:27 PDT and packaged checks finished at
  21:19:49 PDT (5m53s from candidate; 8m18s from the recorded portrait report). This includes finishing/verifying the
  earlier picker package while investigating the new report. Across both reports, release verification took 14m59s
  from 21:04:50 PDT, with two code pushes/two builds, 9m01s total CI time and 15m38s total runner execution. Implementation
  and local checks took roughly four minutes combined; publication/download verification and waiting account for the
  remaining time, with portrait investigation overlapping picker verification. Publication notes use the documentation-only path.

## Published complete unit-picker browsing — 2026-10-02

Changes in [`3069a46`](https://github.com/biscoBen/FFR-Vison-Studio/commit/3069a467e1fc6649d4caa606fd62f59479b27977),
[test package 37095455577](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37095455577).

- Remove the unit picker's first-200-results cutoff so browsing reaches the full character roster when adding a unit
  or replacing a default vision/party model. Keep search uncapped and rows built as they scroll into view; browsing
  still leaves character sprite downloads on demand.
- Passed local analysis and 11 focused tests, covering late-alphabet browsing, more than 200 search matches, both
  replacement pickers, engine-catalog fallback and existing sprite preparation. Windows passed the full Flutter/Python
  suites, genuine engine startup, bundle, launcher/updater/import checks and compilation before publication. Verified the
  authenticated ZIP's checksum, exact commit and all bundled extension files. Master is unchanged.
- One code push and one reused build. CI took 4m39s, with 8m00s summed job execution. First complete candidate:
  21:05:45 PDT; ZIP verified at 21:12:22 PDT and packaged-file checks finished at 21:12:32 PDT (6m47s from candidate,
  7m42s from the recorded request). Implementation took about one minute, local checks/push about one minute, and
  waiting/download/package verification about one minute beyond CI. Publication notes use the documentation-only path.

## Published private shop battle stage — 2026-10-02

Changes in [`67a6fea`](https://github.com/biscoBen/FFR-Vison-Studio/commit/67a6feaa86f68aef3968ac2fbccc866afe14f61e),
[test package 37083235664](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37083235664).

- Give the shop practice battle a private, instance-loaded plains stage instead of selecting a preloaded stage that
  Mitra does not contain. Retain the native background/lighting, level 7–8 enemies, dialogue, escape and normal return
  settings without altering shared stages or other encounters. This targets the black backdrop and possible stage-loading
  stall after combat; backdrop rendering and return still require confirmation in the actual game.
- Local checks passed all 195 Python tests (three Windows engine contracts deferred to CI), the managed bundle check
  and actual engine serialization across all nine affected tables with all 26 original vision grants and max MR enabled.
  Windows passed full Flutter/Python checks, real frozen-engine startup, launcher/updater/import checks and compilation.
  Verified the authenticated published ZIP's checksum, exact commit and all 28 bundled extension files. Ability modes,
  descriptions and other features are retained; master is unchanged.
- One code push and one reused push build. CI took 4m38s, with 8m06s summed job execution. First complete candidate:
  17:42:34 PDT; ZIP verified at 17:48:33 PDT and packaged-file checks finished at 17:48:46 PDT (6m12s from candidate).
  From the queued shop report at 17:19:49 PDT, verification took 28m57s, including 17m05s finishing the requested prior
  ability-mode build. Investigation/implementation took about five minutes, local checks/push about one minute, and
  final publication/download verification about one minute. Publication notes use the documentation-only path.

## Published optional ability visibility and repairs — 2026-10-02

Changes through [`4bad931`](https://github.com/biscoBen/FFR-Vison-Studio/commit/4bad9316818fd0b678df7b20f283a9fa183cee54),
[test package 37082390772](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37082390772).

- Add main-page **Show unverified skills** and adjacent **Use our skill changes** controls, both defaulting off.
  Off uses master's original sequence/compatibility selection filter; showing skills without repairs retains original
  game ability bindings; enabling both restores Studio's animation work and applies all 304 reviewed picker hides.
  Keep ordinary summon commands, equipped IDs, configs, concise descriptions/stats, full click details and source labels.
- Persist the settings without changing other testing controls or roster data. Disable automatic skill timelines/effects
  outside enhanced mode and clear stale Barrage/coverage records. Existing native timelines take precedence, including
  future game versions; full-game behavior remains untested until the game is available. Rebuild/install after switching.
- Preserve a complete pre-change source/history snapshot and the original hiding/animation reports separately.
- Match the engine readiness check to the updated extension version; retain rejection of outdated installer responses.
- Preserve descriptions/stats across all three modes. The prepared catalog has 127 ordinary selectable skills with
  visibility off, 1,009 with visibility on and repairs off, and 705 with both enabled; the enhanced mode retains 198
  Unverified entries. Existing native timelines win over repairs, and reviewed hides require matching IDs and names.
- Windows passed the full Flutter suite, genuine frozen-engine startup, all 195 Python tests including real engine
  contracts, launcher/updater/import checks, both bundles and compilation. Verified the authenticated published ZIP
  checksum, exact commit and all 12 native-extension/16 Crystal Fina files. Master remains unchanged.
- Two Windows failures were corrected before publication: a readiness version mismatch and a regression test reading
  UTF-8 review metadata with Windows' default encoding. Cancelled the helper's automatic retry of the first failed
  commit; used three code pushes and reused the final push build. Final CI took 5m18s, with 9m10s summed job execution.
  All runs together used 31m00s of runner execution, including the cancelled retry; no failed run published a release.
- First complete candidate: 17:14:27 PDT; authenticated ZIP verified at 17:36:48 PDT, 22m21s from candidate and 29m13s
  from the recorded request, including local checks, corrections, failed builds, cancellation and waiting. Packaged-file
  checks finished at 17:36:54 PDT. Publication notes use the documentation-only path. The reported shop backdrop/return
  issue is a separate follow-up; this package preserves its existing shop behavior.

## Published shop dialogue correction and level 7–8 battle — 2026-10-02

Changes in [`d614dda`](https://github.com/biscoBen/FFR-Vison-Studio/commit/d614dda918b517987d6d43eedfe31a0cf91c4d73),
[test package 37079690571](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37079690571).

- Correct the shop practice battle's NPC binding. The observed "Potions, Phoenix Downs..." conversation belongs
  to Mitra's talk block 6, not the different woman's block 39 targeted in the first package. Match the original
  conversation event in both parent and combined tables; preserve the other woman and all existing testing options.
  Battle entry and return still require in-game confirmation after updating and rebuilding/installing the mod.
- Use the native level 7–8 encounter with one Evil Plant (300 HP) and two Wild Rats (320 HP each), preserving their
  normal stats and all other encounters. Retain guaranteed escape and the optional one-battle MR reward.
- Passed local analysis, 19 focused Flutter tests, 188 Python tests and both bundle checks. Windows passed the full
  Flutter/Python suites, real frozen-engine startup, launcher/updater/import checks and compilation before publication.
  Actual engine serialization preserved every original row across all seven affected tables with all 26 original
  vision grants and both testing options enabled. Verified the published ZIP checksum, exact code commit and all
  packaged extension files. Pending ability-hiding decisions are excluded; master is unchanged.
- One correction push and one reused push build: CI took 4m36s; summed job execution was 8m11s. Final corrected
  candidate: 16:52:53 PDT; ZIP verified at 16:58:27 PDT (5m34s including final local checks, push, CI and download).
  From the first feature candidate at 16:15:23 PDT, verification took 43m04s; from the recorded original request at
  16:09:05 PDT, 49m22s. These totals include the initial release, the roughly 25-minute user-testing gap, correction
  and second build. Packaged-file checks finished at 16:58:54 PDT; requested ability lists and documentation followed.
  Publication notes use the documentation-only path and retain the binary's tested code commit.

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
