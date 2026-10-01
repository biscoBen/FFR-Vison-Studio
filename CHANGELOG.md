# Changelog

Fork-specific changes for [biscoBen/FFR-Vison-Studio](https://github.com/biscoBen/FFR-Vison-Studio),
on `Sephira's-Update`, compared with the inherited `master` snapshot
[`d94c685`](https://github.com/biscoBen/FFR-Vison-Studio/commit/d94c685c9dd1b1502c8676e03e679f54a9a05086).
The original project's release notes are preserved below the fork history.

Windows test packages keep version **1.0.0, build 15** for host compatibility. Their commit and workflow run identify
which changes they contain. Dates below use America/Los_Angeles. Published entries describe tested branch packages;
**Unreleased** entries are work awaiting a successful package build.

## Unreleased

No unpublished user-facing changes.

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
