# FFR Vision Studio (Windows app)

This fork's additions and fixes are tracked in [CHANGELOG.md](CHANGELOG.md), separately from the original project's
release history. Use the `Sephira's-Update` test packages to try these changes; `master` stays the inherited baseline.
Keep demo-dependent work in the project's [full-game release checklist](#full-game-release-checklist), shared across task threads.

For the Crystal Fina cave trial, enable **Crystal Fina cave** on the main screen, build/install the mod, and restart
Resonance. Look north of the road between Earth Shrine and Mitra. The stone cave's crystal portal leads to her glowing
room. Both the overworld entrance and crystal portal require the interaction button; a blocking box prevents walking
through the cave entrance or portal crystal. Scene placement and interaction rules are recorded in
[SCENE_PLACEMENT.md](SCENE_PLACEMENT.md). Acquisition requests the native vision-obtain screen and returns outside the portal. Her ownership condition
hides her afterward. The Windows package is verified; placement and the acquisition presentation still need an in-game check.

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
After pushing, confirm its push run is visible in Actions before calling the helper; an immediate query can race
run discovery and dispatch a duplicate.

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

## Sephira’s Visions

The home page has an optional **Sephira’s Visions** section with 30 editable presets in the requested FFBE forms.
Revision 3 kits have 20–28 awakening abilities/bonuses, with learned MR skills additional, native stat/MR budgets
and balanced additions from the broader native/enemy catalog. Great Dragon is retired from this collection.
Existing edits are preserved; use **Reset all presets**
to apply expanded kits (backs up the roster and keeps acquisition), then build/install.
[Verified Windows test package / run 37554129020](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37554129020)
contains code `a4f82e8` and passed all required Windows checks on 2026-10-06. Live battle balance and appearance still
need in-game testing.
Enable it to prepare missing artwork and add the profiles, then build/install to make them available in the game.
Each required look resolves its own hosted unit, including Alice’s separately listed Brave Shift and base form.
Their specialties include attacks and secondary utility. Native stats, MR rewards and combat mechanics provide the
balance baseline; the collection covers the excluded original visions’ skills and passives. See
[the complete kits and unlock ranks](SEPHIRAS_VISIONS.md).

Turning the section off keeps your edits but omits the presets and their acquisition caves from the next build.
**Restore missing** replaces removed entries without resetting edited ones. **Reset all presets**, or right-click a
card and choose **Reset to preset**, restores the recipe and backs up the old roster while keeping IDs and acquisition
locations. An existing Crystal Fina is reused with her edits intact; explicitly reset her to apply the balanced kit.

**Use borrowed Sephira skill visuals** is a separate saved toggle on the home page,
enabled by default. Switch it off and rebuild/install to use original source visuals
for the 216 preset substitutions; switch it back on and rebuild/install to restore
their borrowed spell/attack effects. MP, power, effects, stats and MR stay as edited.
This works with existing saved presets without a reset, independently of the library
skill visibility/repair checkboxes. Missing demo animations may stay blank when off.
Explicitly edited visual donors and authored sequences remain as saved.

## Original vision testing

Drag a **Default vision** into **Added visions**, then install the mod. At the next battle start, a native game event
acquires one original vision item if it is not already owned. It uses the real vision ID, kit, portraits and MR rewards;
no replacement vision or custom skill slots are created. Equip it from the menu afterward. Drag it back into
**Default visions** and reinstall to stop acquisition, preserving other edits.

Enable **One-battle MR for testing** before installing to award 11,430 AP per reward-bearing victory, regardless of
opponent. This bound covers the largest total of the game's native MR rank costs and stays within 32,767; it does not
use an overflow-sized reward. Equip the visions first. Scripted battles that suppress rewards keep that behavior;
awakening ranks and their materials are unchanged. Both controls default off and persist across Studio restarts.

Enable **Shop practice battle**, then install and restart the game. Talk to **Young Woman** in Mitra's item shop
to fight one level-7 Evil Plant and two level-8 Wild Rats after her normal dialogue, using your current party and a native plains backdrop.
The shop uses a private instance-loaded stage so its backdrop does not depend on Mitra's preloaded battle levels.
Escape is guaranteed. The fight uses the one-battle MR reward when that setting is enabled. This switch defaults off;
disable and reinstall to restore her original interaction. Battle entry is confirmed; the updated backdrop, return and
repeat use still need in-game confirmation after rebuilding/installing the mod and restarting Resonance.
NPC event bindings are matched by the actual dialogue text key and talk block; display names and sprite IDs are insufficient.

Use a clean save, do not save with testing active, then disable the testing controls, reinstall and reload the clean save.
Disabling does not remove items or MR already acquired in the running session or a saved game. Table serialization
and automated checks are verified; acquisition timing and MR progression still need confirmation in a running game.

## Automatic animation repair

The main page has **Show unverified skills** and **Use our skill changes** controls. Both default off and are saved
with the engine's mod settings. The three modes are:

| Show unverified | Use our changes | Ability behavior |
| --- | --- | --- |
| Off | Inactive | Use master's original sequence/compatibility selection filter; automatic skill repairs are off. |
| On | Off | Show the expanded library with original game ability bindings; Studio's automatic timelines/effects and reviewed hides are off. |
| On | On | Enable Studio's skill repairs and the 304 reviewed picker hides for summons of monsters, duplicate monster skills, weaker Explodes, follow-ups, item effects, party skills, Ultima Weapon, dismiss commands and esper-owned skills. Ordinary summon commands remain available. |

Short descriptions, selected stats, full click descriptions, source/MR/awakening labels and all other Studio features
remain available in every mode. Existing language/Attack/Resonance and duplicate filters still apply. Equipped skill IDs,
original game rows and saved character configs are retained when their picker entries are hidden. The checkbox remembers
its value while the visibility switch is off; both controls must be enabled for repairs and reviewed hides to apply.
Rebuild/install after switching to replace the previous mod. Automatic repairs keep any existing game timeline first,
including timelines supplied by a later game version; full-game compatibility still needs validation when available.
The reviewed IDs, names and reasons are preserved in `assets/existing_visions/payload/ability_hiding_review.json`.

The four temporary comparison Copies are retired. Loading an older roster or config replaces their grants with
the regular skills, collapsing only duplicates within the same tier. Saved config files stay intact.

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
Right-click a card in **Added visions** and choose **Remove vision** to remove it with the usual confirmation.
Default portraits use bundled FFBE icons matched to all 26 original visions, with the original portrait as a fallback.
These portraits appear in Studio's list and character page; selecting a replacement model shows that model's portrait.

Missing-sequence abilities borrow native FFR target effects by name, element/power, physical impact style, or extracted
healing/status mechanics. Visions retain their own motions and the original skill mechanics. Existing timelines and
Steal/Barrage presentations are preserved. A `Verified` mapping identifies an applied visual profile; it does not mean
every skill has been observed in-game. Specialized actions and unmapped skills keep their existing behavior/fallback.
For a batch preflight against prepared game tables and timelines, run
`python scripts/audit_ability_animations.py --engine <engine-folder> --report <report-prefix>`.
The JSON/CSV inventory includes hidden/internal rows, lists every unsupported effect together, and changes no mod or
roster. Missing reference folders must be extracted first. Never infer animation ownership from learning sources alone.

The character page's **MR** tab uses the game's **MR 0–9** ranks. Select a rank, then add stat bonuses,
abilities, passives, or the vision's master reward. Rewards can be moved to another rank or removed, and stat amounts
can be edited directly. The engine supports five rewards per rank. Existing rewards and unlock-point requirements
are preserved until edited; character config files include these rewards. Build/install afterward to apply them in-game.
Flat rewards are marked **Permanent**, with **Speed**, **Magic** and **AP** matching the game terminology; passives
show their equip cost. Default visions retain the exact IDs from their native awakening/MR tables. Their inherited
entries show that vision's actual learning ranks, while library sources include other native learners of shared IDs.
An **Enemy version** label identifies rows explicitly marked for enemies in the game data. A PDF source label does
not mean that a default vision learns that version: Tronn learns shared Fire `220010`, not enemy Fire `250010`.
The **Native kit** filter on Abilities, Bonuses and MR selects a default vision's exact original awakening/MR IDs,
including entries removed from its current edit. Use it when re-adding a skill or assigning the same version to another
vision. Library entries show their game ID; all existing visibility filters still apply.

The **Acquisition** tab assigns Added visions to saved locations. **Random** and **Hide for spoilers** start on.
Turn off Hide to reveal the selected location and its map marker; choices remain disabled until Random is off.
Random picks a category first: **75% caves / 25% vendors**, regardless of how many locations each list contains.
Changing Random in either direction rerolls; it prefers a different location within the selected category, but a sole
cave/vendor can repeat to preserve the odds. With no caves available, it uses vendors. Existing saved assignments stay
in place until rerolled. Choose **Shop** and a vendor, or **Cave** and one of our
custom caves. The vendor list retains all 105 native inventory and 20 combined-shop records, including chapter variants;
it uses readable translations of their source labels. Moving/later-game entries without identifiable native map coordinates
remain selectable with their pin unavailable. Zoom and drag the native world-map menu images, or use **Full map**.
Right-click the map, choose **Add cave here**, select an entrance image and click **Position cave**. Then name and place
it; use **Change** beside the selected entrance to choose another model. The shared cave list starts
with our Crystal Fina cave; you place the rest toward the 30-cave target. Selecting a cave centers its pin. Entrance
previews use native geometry with simplified lighting. Cave locations persist across Studio restarts. Right-click any
visible cave marker for **Remove cave**. Removal clears all current vision assignments
to that cave back to Mitra's shop, preserving their Random/Hide settings, and disables the legacy switch when removing
the original Crystal Fina cave. Rebuild/install and restart to remove it from the game. The selected cave is included
in character configs. Build/install the mod and restart Resonance to create **assigned** caves;
unassigned pool entries remain saved for later. Each is named **Resonance Cave** in-game and uses the existing stone
cave, button-operated crystal portal and glowing crystal room. It contains the assigned vision's idle sprite, grants
that vision's actual item through the native obtain screen, hides it once owned, and returns outside the portal in
the same stone cave. Multiple visions assigned to one cave have separate interactions and ownership conditions.
Cave-selected visions are not also sold in Mitra. Saved cave map IDs remain stable across rebuilds. The original
Crystal Fina cave switch still works; an explicit cave assignment for her takes precedence. Shop assignments now route
to the selected native inventory, including Mitra Weapons. Combined vendors use their item tab, or their first available
weapon/armor/accessory tab. Unassigned visions keep Mitra Items. Original visions
retain their native acquisition. Entrances default to 75% size and use decoded native landscape heights where available. Right-click a cave marker
for **Edit placement**: drag its entrance in the local 3D terrain preview, use X/Y/Z, ground snapping, rotation and
size controls, or right-click the map to move it. The pin marks the footprint center; saved edits update all assigned
visions without changing cave IDs. The 3D preview uses native terrain paint, shaded world meshes and tree/bush instances
with simplified lighting. It omits unavailable assets and Unreal's animated/transparent shaders. Native height/paint
coverage includes Grandshelt and Dirnado. Town/landmark models and bridge instances include inherited Blueprint components
and landscape levels. Native capture transparency defines the coast, so low towns remain on land; later-area models
now include the supplied Lanzelt towns/large bridges, Dirnado settlements and vision shrines (888 mesh instances).
Unsupported rock geometry and missing shader dependencies remain omitted/simplified. Elsewhere set Z manually.
Ordinary cave visions use 63% of their original scale (5% larger than the previous package); Crystal Fina's crystal stays at its tested size. Square native map
captures are displayed without stretching them to region bounds, keeping 2D pins aligned with saved world coordinates.
Cave exits travel to the world map and restore walking. While Resonance caves are installed, native world-map destination
banners use **World Map** rather than landmark names/recommended levels; this also affects native location exit previews.
Other destinations and native banner visibility settings are preserved. Returns are placed outside the entrance on
its opening side, at native terrain height with runtime collision snapping; the exact incoming player position is not saved.
The cave portal uses a white loading transition. Terrain/accessibility still need an in-game placement check. Automated asset checks do not execute gameplay.
The [verified acquisition package](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37267588481)
contains the entrance selector before placement and the native World Map banner policy, alongside expanded landmarks,
grounded cave exits and the vision-size adjustments (commit `da6c177`, run `37267588481`).
Update Studio, rebuild/install the mod
and restart Resonance to test cave behavior; the placement-preview additions are visible in Studio.

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

The third home section, **Party characters**, lists Rain, Lasswell, Fina, Lid, Nichol, Dark Fina, Jake and Sakura.
Use **Change battle model** to select and preview an FFBE appearance, or **Manage appearances** to open previews and
config save/load. **Revert to original** offers **Revert battle only**, **Revert overworld only**, and **Revert both**.
Reverting one appearance keeps the other; build/install to apply it. Single/bulk character configs include
these choices. Party abilities, equipment and progression stay original; the builder writes private battle assets and
redirects the selected party rows in the runtime `DT_BtlUnitAsset` table, alongside existing vision changes.
**Change battle voice** independently selects any of the eight original party speakers. Standard battle events use the
selected character's native `BattleVoiceLabel`; story dialogue, character identity and progression stay original.
Authored normal-attack and party LB voice sections also use the selected speaker. LB openings, attack lines and
finishers use verified native generic LB cues; their wording may differ from the original skill. Non-voice effects,
animations and timeline timing stay original. Story dialogue and team victory conversations keep their authored voices.
The demo cue inventory covers all eight speakers in English and Japanese; live playback still needs in-game testing.
The choice survives single/bulk config saves. **Revert battle voice** restores only audio; appearance reverts keep it,
and **Revert all** restores appearances and voice. Rebuild/install and restart the game after changing voices.
Use **Edit overworld appearance** for an independent walking model. The picker includes every reviewed FFBE town
sheet with genuine directional running art: **Rain, Vagrant Knight Rain and Pyro Glacial Lasswell** are 8-way;
**Lasswell, Fina, Nichol, Lid and Jake** are 4-way. One additional 8-way sheet is listed as **Unidentified cloaked
character**, with its own standing image rather than an invented unit identity. Normal unit images and a **4-way/8-way**
label appear in the list. Preview **Idle**, **Walk** and **Run** in each available direction; standing frames are removed
from movement loops. Four-way models use their own front/back poses for diagonal movement. Separate missing walk
rows use that model's run art at walking speed. The assets are bundled; no sprite download is required.
Sakura's field running rows contain only shadows, and side-view battle movement does not qualify as 4-way art.
**Revert overworld
appearance** restores walking without removing your battle choice. Single/bulk configs preserve both selections.
Only the primary field animation and textures are redirected; special scene assets retain their paths. Scenes using
the ordinary walking model also show the replacement. Original skill effects
remain in use; special cinematics and replacement motions need an in-game check.
After selecting a model, rebuild/install the mod and restart Resonance. The catalog is pinned to the FFBE dump
snapshot recorded in `assets/existing_visions/payload/overworld_catalog.json`. `scripts/build_overworld_catalog.py`
audits complete source trees and sprite pixels, verifies Git blob hashes, removes rest/shadow frames and generates
the shared Dart/Python catalog and deterministic asset archive; new or changed sheets require review.

**Cycle walking character (LB / L1)** cycles the current active party's field appearances; F6 is an alternative.
Enable it and rebuild/install, using the UE4SS loader already prepared by the field-reference helper. Studio installs
only its owned `FFRStudioFieldLeader` Lua mod, with no further loader download. Right-stick click keeps its native
minimap function. Cycling changes the walking sprite, preserves party order/save identity and battle choices,
and restores the story appearance around events. All eight native party characters have movement sprites;
Dark Fina uses her own cardinal poses for diagonal idle. Independent overworld replacements participate too.
Turn the option off and rebuild/install, or restore the original game, to remove Studio's cycling scripts.
Previous-build restoration also restores the corresponding scripts. Live controller/scene behavior needs testing.

The original Resonance and its cinematic remain unchanged when replacing a model. Original visions can select another
existing game Resonance; creating a custom Resonance remains available for separately added units. Unsupported original
sprite layouts and incomplete placeholders are excluded. Engine integration runs automatically at startup and after
compatible updates, alongside Crystal Fina's transparency integration. No separate script is required.

## Full-game release checklist

This is the running project list for the full game's release, started **2026-10-04** from the `Sephira's-Update`
demo baseline `b15a4c0`. These are areas to review when the full game is available, not confirmed future bugs.
Keep user cave placements, character configs, concise descriptions and source labels. Add new demo-dependent
features here as work continues. Mark an item complete only with the tested game version, Studio commit and evidence;
retain unresolved cases and record the date/source fingerprints when refreshing catalogs.

- [ ] **Vendors and cave entrance images/models.** Regenerate from full-game shop tables and entrance assets.
  Retain native IDs/chapter variants, review unused entries, locate currently unmapped vendors where data permits,
  and recheck all four entrance previews.
- [ ] **Random acquisition progression limits.** Exclude the final quarter of story access from both random vendor and
  cave pools before applying the 75% cave / 25% vendor weighting. Establish the full game's ordered story milestones
  and cutoff; tag each vendor/chapter variant and cave position with its earliest reachable milestone, including transport
  requirements. Keep unknown, unused and no-longer-accessible locations out of that filtered random pool; keep manual
  choices available. Do not infer progression from vendor IDs, alphabetical order or map distance. Only 28 of the current
  125 vendor records have mapped locations, and custom caves have no story-access tags, so this exclusion is not active
  yet. Confirm whether chapters 7–8 are actually the final quarter rather than assuming the demo's labels cover the full
  story. Preserve existing saved assignments until explicitly rerolled and validate that both eligible categories remain.
- [ ] **Skills: verified, unverified and hide/show modes.** Audit the updated catalog, including newly available
  native timelines/effects, MR/awakening assignments and source ownership. Native timelines take precedence over our
  fallback repairs. Reassess the 304 reviewed hides and original picker filters while retaining the three modes and
  descriptions/source labels. Do not assume every missing demo skill will be implemented. `Verified` currently
  tracks an applied visual mapping, rather than observation of every skill in a running game.
- [ ] **World-map images, coordinates and cave placements.** Refresh native map captures, projection and landmarks.
  Validate saved positions before migration; preserve the user's cave locations and leave unknown vendor pins unavailable.
- [ ] **Default visions, party members and portraits.** Refresh identities, stats, abilities, MR rewards, Resonances,
  portraits and acquisition rules. Review new characters/placeholders and preserve original identities when replacing models.
- [ ] **Sephira’s Visions presets.** Re-audit the excluded-vision coverage, exact
  skill/passive IDs, command-specific bonus bindings, native power budgets,
  MR stat rewards and unlock ranks. Check recipes against the full game's
  mechanics and ID reservations; preserve edited and disabled presets instead
  of silently resetting them. See `SEPHIRAS_VISIONS.md` for the agreed design.
  Turn off **Use borrowed Sephira skill visuals** and rebuild/install to evaluate
  newly available source animations. This restores the 216 preset visual substitutions
  independently of library repairs without removing MP, power or other kit edits.
  Explicit custom donor edits and authored sequences remain as saved; compare both
  modes and retain the toggle for sources still missing or unsuitable in the full game.
- [ ] **Espers and summons.** Inspect full-game sprites, effects and timelines. Reassess esper-owned hiding separately
  from ordinary summon commands; check whether assets absent from the demo are now available.
- [ ] **Crystal Fina cave and acquisition locations.** Refresh donor interiors, entry actors, navigation, collision,
  return points, event timelines and ownership conditions. Retest granting the vision, disappearance, white flash,
  return to the stone cave and controller dialogs. Assigned user-placed Resonance Caves now use this flow; recheck
  their stable map identities, shared-cave grants, entrance models, terrain heights and full-game regions. Refresh the
  checked landscape mip decoder, source height data and placement preview geometry; expand terrain coverage and
  validate existing saved X/Y/Z, rotation and scale without moving caves silently. Refresh painted terrain, native foliage
  instance transforms, visible mesh/material dependencies and square capture sizing; extend scenery coverage. Retest
  inherited Blueprint transforms, cooked bridge instances, capture-alpha coastline masks, door-side returns and runtime
  collision snapping with restored walking, including placements on low ground and elevated entrances. Retest
  exit banners' region/name and recommended-level metadata independently of their travel destinations. Refresh
  `DA_UI_PlaceNameProperty` and review map 1000's `bUseLandName` policy, preserving other destinations/visibility settings.
  Retest selected vendor inventories and combined-shop tabs, preserving native item conditions and purchase limits.
- [ ] **Battle and overworld replacements.** Recheck native asset tables, sprite layouts, portraits, directions,
  restoration and special scenes. FFBE field sprites use separate source data; refresh that catalog when its source
  changes or additional suitable sheets become available.
- [ ] **Field-character cycling and controller input.** Verify UE4SS compatibility, reflected function signatures,
  active-party lookup and input bindings. Check battle/cutscene/dialog guards and preservation of party order/save identity.
- [ ] **Engine, extraction and cooked assets.** Check executable/Pak paths, engine version, `Mappings.usmap`, table
  schemas, SpriteStudio serialization and IoStore roundtrips. Separate or invalidate prepared demo data. Review our engine
  extensions against upstream updates; change pinned checksums only for verified replacements. Preserve engine hosting.
- [ ] **Testing features.** Recheck the Young Woman binding, practice enemies, backdrop and return; original-vision
  grants and toggle restoration. Recompute the one-battle MR reward within actual numeric bounds: 11,430 AP comes from
  the current demo's rank costs. Test with clean saves.
- [ ] **Custom IDs, capacity and configs.** Check reserved skill/unit/map/event/asset ranges against newly occupied IDs.
  Revalidate the 64-added-unit limit against engine/table constraints. Preserve old configs, separate appearance choices
  and selected cave snapshots.
- [ ] **Installation, updater and release validation.** Verify full-game detection, engine/host compatibility,
  rebuild/install, restore and config migration with a separate test profile. Decide whether demo support remains and
  identify supported game builds. Run the batch animation audit and required Windows release gates, followed by
  representative live-game checks; package validation alone does not establish gameplay compatibility.

Deferred feature: **FFBE battle voices** remain on hold. Resume source/audio-bank investigation when requested;
review available full-game voice routing and preserve story dialogue. This is not an implemented compatibility feature.
Native party voice overrides must also be checked against full-game bank contents, fixed cinematic cues and team
victory exchanges before claiming complete battle voice coverage.

## Layout

- `lib/main.dart` window, single-instance lock, header, engine-down banner
- `lib/state/app_state.dart` boot (downloads, offline start, update notice), engine supervision, units, build, restore
- `lib/services/` engine process, downloader (resume + checksum), engine API client, game folder detection, paths
- `lib/design/` the guide's tokens (`Guide`, day and night editions), parts, wordmark, motion viewer, choice
- `lib/screens/` setup, home (spread), unit page and its five tabs, add-unit, copy-a-vision, about, build status
- `windows/runner/Runner.rc` exe metadata; `windows/runner/resources/app_icon.ico` Rain's face

## Developing without touching your real install

When creating Windows reference-extraction scripts, default their output to `%USERPROFILE%\Downloads\FFR Mod`,
with a separate named or timestamped collection folder. Keep extracted files and upload ZIPs there, off the Desktop.

When adding or changing a demo-dependent feature, update the [full-game release checklist](#full-game-release-checklist)
in this README so future task threads can continue from the same list.

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
