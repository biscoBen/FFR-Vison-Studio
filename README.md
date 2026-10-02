# FFR Vision Studio (Windows app)

This fork's additions and fixes are tracked in [CHANGELOG.md](CHANGELOG.md), separately from the original project's
release history. Use the `Sephira's-Update` test packages to try these changes; `master` stays the inherited baseline.

The native front of the studio: a Flutter desktop app that downloads and supervises the Python/.NET engine
(`FFR Vision Studio Engine.exe`, fetched from the project's host on first start) and drives its Easy mode natively.
This repository is the app on its own: it needs nothing else on disk to build, and at runtime it talks only to the
engine over localhost and to the host over HTTPS. Design: `DESIGN.md` and `lib/design/DIRECTION.md`. The engine's
source, the pack builder and the project notes live in a separate project repository, which is not published yet.

## Build

```
flutter pub get
flutter analyze
flutter test
flutter build windows --release            # defaults to version 1.0.0, build 15
```

A build talks to the live host, which can require a minimum app version in its manifest. This branch defaults to build 15
in both the executable metadata and the app's version check. To use another compatible build number:

```
flutter build windows --release --build-name 1.0.0 --build-number <n> \
  --dart-define=APP_VERSION=1.0.0 --dart-define=APP_BUILD=<n>
```

`.github/workflows/windows.yml` on this fork's development branch runs analyze, test and the Windows build on pushes to
`Sephira's-Update`, `main`, and `master`, as well as pull requests. It attaches the Release folder as the
`FFR-Vision-Studio-windows` artifact. Automatic builds default to build 15 and check the host's minimum-version requirement
when its manifest is reachable. A blocked or unavailable updater host does not prevent compilation; the app still checks
compatibility at startup.
README/CHANGELOG-only changes complete the inexpensive `plan` and `windows` checks, without a Windows build or release.
All other paths retain full coverage. Manual builds always run. Validation and compilation run concurrently on Windows;
the `windows` check requires both to succeed before either download publication job can run. Superseded automatic
validation/compilation jobs on `Sephira's-Update` can be cancelled; manual builds and release publication are protected.
CI pins the verified Flutter 3.47.6 toolchain, retains Flutter/Pub caches, enforces `pubspec.lock`, and resolves packages
once per runner. It extracts a fresh engine for its real startup test and does not reuse generated build directories.
A manual run ("Run workflow") can supply a different compatible build number.
If GitHub Actions is disabled on the fork, enable it from the repository's Actions page first. The zips people
download are assembled by the packaging run in the project repository, which passes the same flags and ships the
exe next to the engine and the data packs.

## Cloud builds

Windows users can install the separate test copy from a `Sephira-Studio-Test.zip` package. Extract it and run
`Start Studio Test.cmd` once; it creates a **Sephira Studio Test** desktop shortcut. Opening the shortcut checks for
the latest validated `Sephira's-Update` prerelease, verifies its SHA256 digest, and launches it. Settings and units
remain in `Studio Test Data` beside the launcher. Failed/offline updates retain the installed app. Close the test app
before reopening the shortcut to check again. Use a copied game folder to keep installed test mods separate too.

Successful builds on this development branch automatically publish those test packages. The test app uses its own
shortcut for frontend updates and continues to fetch engine/data packs from the original host. It does not offer the
original project's frontend updater. The release label remains build 15; the shortcut identifies updates by their
workflow run and commit. These packages are prereleases and do not replace the fork's stable release or change master.

From this checkout, use the helper to build the development branch and download the resulting Windows app:

```
python3 scripts/cloud_windows_build.py
```

Enable repository Actions from its Actions page first. The helper can also do this with `--enable-actions` if its credential
has Administration permission.
The helper defaults to `Sephira's-Update` and build 15. It checks the remote commit and searches for a successful or
running build with that exact commit, workflow and build/download inputs. It reuses a verified build or waits for the
matching running build; otherwise it dispatches one run. `--force-rebuild` deliberately requests a new run.
Missing, expired or incompatible artifacts cause a new build unless the same run has a verified published test ZIP.
Downloads validate the SHA-256 and embedded commit, workflow, pinned Flutter version and build inputs before delivery.
The helper writes `build-record.json` alongside the executable under `/workspace/.runtime/ffr/builds`. Existing output
is preserved; choose a different `--output` directory for another download. Commit and push code before building it.
After publication, updating README/CHANGELOG release notes needs no further application build; the published package
continues to identify its original tested commit.

The verified [workflow 36935925830](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/36935925830) took 4m18s
from creation through publication, compared with 6m00s for the previous final sprite build. Parallel execution used
7m40s of runner time versus 5m52s; SDK/Pub cache setup still took 91–105s per Windows runner. A subsequent helper call
reused the verified package in 7.36s without dispatching another workflow. These single-run measurements show the
elapsed-time/runner-usage tradeoff; cache restoration, Windows compilation and queue time still vary.

Windows CI reuses its startup-test engine ZIP through an Actions cache keyed by the pinned SHA-256, so app commits
do not require another download from the engine host after the cache is populated. Every build verifies that checksum
and extracts a fresh engine for startup testing. A cache miss uses the existing `ffr.luminest.io` URL; partial downloads
and corrupt archives are rejected. GitHub can evict unused caches. For repeated local Windows startup tests, set
`FFR_STUDIO_ENGINE_CACHE` to a persistent directory; a verified archive is retained there under its SHA-256 filename.

For the Steal/Barrage animation comparison, give **Steal (Verified; FFR test)** to Zidane and an FFBE-backed vision
such as A2, and **Barrage (Verified; FFBE test)** to the FFBE-backed vision. After updating Studio, rebuild/install
the roster mod. Steal now approaches the target in the recipient's ready pose, resolves one original item theft,
then returns to idle and position. This is an explicit presentation, not a recovered Zidane-specific sequence.
Barrage retains the recipient's four FFBE attack cycles and FFR's four-hit mechanics. **1,000 Needles** and
**10,000 Needles (Verified; FFR mob test)** borrow ordinary monster Needle's shared Stab/Needle target particles;
they retain one hit for their original fixed damage, without importing a monster body or extra hits. Compare theft,
movement, target effects and battle completion. Windows checks cannot verify appearance in a running battle.

If the cloud proxy blocks GitHub's artifact storage, the helper first reuses the exact run's authenticated published
test ZIP when available, verifying both its release metadata and embedded build identity. No second build is needed.
For runs without a usable published test ZIP, use `python3 scripts/cloud_windows_build.py --cloud-download`
on the development branch. The workflow creates a temporary **unpublished draft** download through GitHub's release-asset
endpoint. The helper verifies its branch, commit, run and SHA256 digest, downloads it, and deletes the draft. This requires
Contents read/write in addition to Actions access. Normal push builds do not create temporary drafts; successful
development-branch builds publish the separate test prerelease described above.

The platform's GitHub integration may allow code pushes while denying Actions administration. In that case, supply a
fine-grained GitHub token securely as `FFR_GITHUB_ACTIONS_TOKEN` in the cloud environment's secret settings, scoped only
to `biscoBen/FFR-Vison-Studio`. It needs **Actions: read and write** to enable workflows, request builds, watch runs, and
download artifacts; **Contents: read** to verify the selected commit; and **Administration: read and write** for the
one-time repository Actions activation. Administration permission can be removed after activation.
The helper uses the existing injected GitHub authentication when this additional binding is absent. Never put token
values in the repository or chat.

Older baseline workflows without the build-input/provenance contract can still be built manually in Actions; the helper
rejects unprovable workflow inputs rather than attributing their binaries to a requested build. This does not change master.
Run the downloaded executable through the prepared Wine runtime with separate scratch application data.
Full mod tests still need the game's installation and extracted data.

## Character sprites

Character sprites download on demand when you choose a character in **Add a unit**, load its saved config, or open
an existing character whose preview data is missing. Startup does not download the whole hosted roster.
Config loading restores only the selected appearance and its required base form, keeps existing artwork and reuses
cached files. Single-character and **Load all character configs** saves retain their appearances when reopened.
A failed preparation reports its error and keeps the roster unchanged; retry loading the config after the host recovers.

## Automatic animation repair

Fresh roster builds give missing ordinary skills native target effects from a regular same-name skill, even when damage,
targets or hit counts differ. Remaining elemental attacks use three power tiers: physical Earth/Thunder skills use the
corresponding Blade effects; other families use matching elemental spell effects with the vision's physical or magic
motion. Named II/III and ra/ga variants select their tier before the power fallback. Light's third tier uses Banishra;
Dark uses Dystopia's portable effects because ordinary Dark/Banishga timelines are absent.

The builder imports only particle events and their game asset references into its own attack/casting schedule. Original
damage, targets, hit counts/ratios, costs and gameplay effects remain intact. Donor caster motions, voices and gameplay
hit events are excluded. Bladeblitz, Aero Blade, Aquatic Synergy and Arise retain explicit Grand Slash/Aero/Waterga/Raise
donors. Existing sequences and custom animations take precedence. The working ordinary-skill reaction-color correction
is retained, and original Resonance scheduling is preserved.

**(Verified)** identifies entries covered by the new visual mapping. It tracks visual coverage; duplicate hiding still
uses the original combat verification rules. Source and awakening labels remain intact. Documented Bond rewards
also show **MR=N**, such as Steal's **Source: Zidane; MR=1**, identifying its MR tab assignment. Unmapped entries retain
**(Unverified)** and the existing motion fallback. A mapped effect that cannot be extracted/imported stops the build
with its skill/donor error instead of silently producing a motion-only mod. Each build records selected skills and donors
in `engine/build/animation-repair-report.json`. All selected donor failures are reported together before staging repairs,
with the exact invalid particle package when available; repeated uses of the same donor are decoded once per build.

Opening an original vision or editing its stats/passive rewards preserves its inherited ability presentation. Animation
repair covers added visions, explicitly added abilities and original visions with replaced FFBE models. Shared impact
rows used by original visions remain unchanged even when another vision borrows that ability's target effects.

Rebuild/install the roster mod after updating Studio. Installing the app alone does not replace a previously built mod.
Effect appearance and battle completion still require in-game testing.

## Ability and passive libraries

Unverified entries used by default visions show **Source: <unit names>** beside **(Unverified)**. Ownership includes
awakening and MR rewards, command/level-up skills, base passives and alternate target modes. An unused Unverified ability
is hidden when a verified same-name version has matching complete combat data, even if presentation, menu/map effects
or internal IDs differ. Real differences in targets, power, MP cost, accuracy, hit data and effects remain selectable.
Default-owned and roster-used IDs are retained. This filters Studio's pickers; it does not delete or remap game rows.

The default visions' Resonance moves are reserved for Resonance selection and hidden from Abilities and MR ability
pickers. Untranslated names and entries named **Attack** are also hidden from ordinary selection. Existing learned
abilities and MR rewards keep their IDs and remain editable. Ability rows show short prose and recorded
**Type; Target; Accuracy; Break; Power; MP; Hits; Crit Chance**, with the full stat line wrapping as needed.

The same **Source: <unit names>** label identifies confirmed non-vision users, including enemies and base party members.
When both kinds of ownership are known, their names share one sorted label without duplicates. The engine
traces original commands, level grants, passives, explicit AI skill IDs and alternate target rows, using the prepared
game's English unit names. Missing or ambiguous sources stay unlabelled. Source labels do not verify compatibility
on added visions or change **(Unverified)** status.

The bundled October 1, 2026 ability-source reference covers all 91 pages, including the additional game abilities
and passives. It labels 1,141 assigned ability IDs and 343 passive IDs, including enemy, party, esper, consumable
and equipment sources. All hiding rules still apply; this also covers already-equipped hidden IDs. Its owner is
representative; known game-table sources still join the same sorted, deduplicated **Source: <unit names>** label. Explicit awakening tiers
appear as **awakening=N** (with the reference owner named when multiple sources are listed). Bond rewards and linked
variants do not imply an awakening tier. Six internal owner labels are marked **(internal label only)** without claiming
an unlock; entries without an assignment remain unlabelled unless the game tables establish a source. This reference
changes display metadata only and preserves all selection filters, verification status and saved grants.

Click a skill or passive's name/description area to open its full description in a scrollable, selectable window.
Dragging a library entry still equips it; dragging does not open its description. Details are also available on learned
entries and MR rewards. The descriptions show recorded stats and effects in a consistent order, with internal
voice/debug metadata removed.
Extracted values take precedence; absent values are omitted, and undocumented effect parameters are shown as recorded
numbers. Duplicate matching requires the prepared game's full extracted tables.

## Saved character configurations

The home screen separates **Added visions** from **Default visions**. Edited original visions remain in the default box
and appear once with their current edits. Each box scrolls independently; adding units and saving/loading all configs
remain available from the home screen.
Default portraits use bundled FFBE icons matched to all 26 original visions, with the original portrait as a fallback.
These portraits appear in Studio's list and character page; selecting a replacement model shows that model's portrait.

The character page's **MR** tab edits the rewards at each of the ten ranks. Select a rank, then add stat bonuses,
abilities, passives, or the vision's master reward. Rewards can be moved to another rank or removed, and stat amounts
can be edited directly. The engine supports five rewards per rank. Existing rewards and unlock-point requirements
are preserved until edited; character config files include these rewards. Build/install afterward to apply them in-game.

Open a vision and use **Save character config** at the bottom left to save a `.vision.json` file. It contains the full
character spec: abilities and passives by tier, custom moves, stats, resistances, roles, Resonance mechanics and animation
settings, and advanced fields. Studio suggests its persistent `Character Configs` folder, or you can choose another folder.

Use **Load character config** from a character page or **Your visions**. A removed character is restored directly;
an existing matching character requires confirmation before replacing its setup. An unrelated selected character is
never overwritten. Studio keeps a full roster backup under `config-backups` before loading and allocates free IDs and
internal table row names when necessary. Re-added characters keep their current ID whenever it is available.

These files save configuration, not artwork. Removing a vision keeps its cached artwork, and Crystal Fina's bundled
artwork is repaired automatically. On another installation, first add/import the character to obtain its artwork,
then load the saved file. Build or install the mod afterward to apply the restored setup to the game.

The **Your visions** page also has **Save all character configs** and **Load all character configs**. Save all writes
every current unit to one `.visions.json` file. Load all restores missing units and replaces matching setups after
confirmation, while keeping other units in the current roster. Every saved entry and its artwork are checked before
the roster is written once; a missing asset or invalid entry prevents the entire import. IDs and references between
saved units are adjusted together if necessary. A full roster backup is kept before applying the import.

## Editing original game visions

After game preparation, **Your visions** also lists the original game visions, including the nine original FFBE visions
(Amelia, Tronn, Victoria, Camille, Leah, Ayaka, Wilhelm, Aileen and Charlotte). Click one and choose
**Edit vision** to adjust its kit or **Change model** to select replacement artwork from the normal unit picker,
including Crystal Fina. Changing artwork keeps the original vision's game ID, stats, abilities, passives, MR rewards,
Resonance and acquisition/progression data. Original visions are updated in place, rather than added as duplicate units.
Only original visions you choose to edit are stored in your mod roster or included in saved configs.

The character page has **Change model** and **Use original model**. Restoring the model keeps your kit edits.
**Reset vision** removes the entire override; build/install afterward to restore that vision's game defaults.
If no overrides or added units remain, use **Restore original game** to remove the installed mod.
Single and bulk config saves include original-vision edits and replacement-model selections.

The original Resonance and its cinematic remain unchanged when replacing a model. Original visions can select another
existing game Resonance; creating a custom Resonance remains available for separately added units. Unsupported original
sprite layouts and incomplete placeholders are excluded. Engine integration runs automatically at startup and after
compatible updates, alongside Crystal Fina's transparency integration. No separate script is required.

## Layout

- `lib/main.dart` window, single-instance lock, header, engine-down banner
- `lib/state/app_state.dart` boot (downloads, offline start, update notice), engine supervision, units, build, restore
- `lib/services/` engine process, downloader (resume + checksum), engine API client, game folder detection, paths
- `lib/design/` the guide's tokens (`Guide`, day and night editions), parts, wordmark, motion viewer, choice
- `lib/screens/` setup, home (spread), unit page and its five tabs, add-unit, copy-a-vision, about, build status
- `windows/runner/Runner.rc` exe metadata; `windows/runner/resources/app_icon.ico` Rain's face

## Developing without touching your real install

Update the fork section of [CHANGELOG.md](CHANGELOG.md) with each user-facing change. Keep work under **Unreleased**
until its Windows package passes the required checks; then record its date, commit and test-release link. Preserve the
original project's release notes below the fork history.

Start the built exe with `LOCALAPPDATA` pointed at a scratch folder: the app keeps everything (engine, packs, units, logs)
under `<LOCALAPPDATA>\FFR Vision Studio`. `FFR_STUDIO_HOST` points it at another host tree (a local copy served on
127.0.0.1, for instance); it defaults to the live host, which is all a developer build needs.

To compare `Sephira's-Update` with a clean `master` build, keep the executables in separate folders and give each its own
scratch `LOCALAPPDATA` directory. This separates settings, engine files, and units. On Linux, run the Windows build
through Wine or Proton; compiling the Windows executable still requires Windows. Keep `master` unchanged when testing
the development branch.

## Files

`CHANGELOG.md` (by build), `LICENSE` (MIT for the code; the game's art and data are Square Enix's and excluded),
`CONTRIBUTING.md`, `.github/workflows/windows.yml` (analyze, test, build, artifact on every push).
