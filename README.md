# FFR Vision Studio (Windows app)

This fork's additions and fixes are tracked in [CHANGELOG.md](CHANGELOG.md), separately from the original project's
release history. Use the `Sephira's-Update` test packages to try these changes; `master` stays the inherited baseline.
Keep demo-dependent work in the project's [full-game release checklist](#full-game-release-checklist), shared across task threads.

### Crystal Fina movie display and handoff test — 2026-10-23

[Verified Windows download / run 40024946811](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40024946811/Sephira-Studio-Test.zip)
(code `449fd0a`, extension **1.2.72**; **72.0 MB**).

The runtime trace confirms the selected movie opens and advances frames, while its display stays hidden.
This test update uses the native battle/movie UI transition and refreshes cached evaluation after shortening
movie/spawn timing. It targets the invisible movie and the unintended replay over Fina's sprite LB.
The exact selected **Crystal-Fina-Rotating-Lighter.mp4**, score, sprite animation, healing and cure sound remain.

Close Studio/game and update while keeping **Studio Test Data**. Include Crystal Fina, enable
**Test Crystal Fina cinematic**, rebuild/install and restart Resonance. Check for one **6.4-second movie**
followed by her existing sprite LB, then repeat in a second battle. No MR/acquisition update or kit reset is required.

Full Windows validation, compilation, frozen-engine startup and downloaded-package checks passed.
The package matches the source files and selected movie hashes. **Visible game playback and the corrected
handoff remain an in-game test.** See [implementation/evidence](docs/CRYSTAL_FINA_CINEMATIC.md) and
[measured delivery/CI timings](CHANGELOG.md#published-crystal-fina-movie-display-and-handoff-test--2026-10-23).

### Crystal Fina lighter movie and playback correction — 2026-10-23

[Verified Windows download / run 40014034193](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-40014034193/Sephira-Studio-Test.zip)
(code `58dac32`, extension **1.2.71**; **72.0 MB**).

Use the selected **Crystal-Fina-Rotating-Lighter.mp4** for the cinematic test. Studio's preview is the exact
1080p file; the game copy uses the tested 720p VP9 format for the same 6.4 seconds, with the matching original
score. The crystal keeps rotating during the wide-to-close shot and Fina opens her red eyes at the end.
This also corrects the missing `Streams` component in the movie's pak path and the native container headers
identified from the returned game reference. The earlier blank-movie report still needs an in-game retest.

Close Studio/game and update while keeping **Studio Test Data**. Enable **Test Crystal Fina cinematic**,
rebuild/install, restart Resonance, and use her resonance. Check the movie, music, transition into her LB
and cure sound, then repeat in a second battle. **No MR/acquisition update or kit reset is required.**

Windows validation, compilation, package provenance and delivered movie checks passed. Actual game playback,
synchronization and Steam Deck playback remain user tests. Alternate artwork work is paused. See
[implementation and test limits](docs/CRYSTAL_FINA_CINEMATIC.md).

### Crystal Fina cinematic test — 2026-10-23

[Verified Windows download / run 39986827052](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39986827052/Sephira-Studio-Test.zip)
(code `aab0431`, extension **1.2.70**; **63.5 MB**).

An optional **6.4-second illustrated cinematic** now leads into Crystal Fina’s existing LB. It uses the approved
crystal refraction/light appearance and an original chime/glass score. Open **Preview Crystal Fina cinematic**
in Studio to watch it without entering a battle.

Update while keeping **Studio Test Data**. Include Crystal Fina, turn on **Test Crystal Fina cinematic**,
rebuild/install and restart the game, then use her resonance. Check the transition, sound and a second battle.
Turn the switch off and rebuild/install to remove it. **No MR/acquisition update or kit reset is required.**
Her healing, rewards, existing LB and accepted crystal material are retained.

Windows compilation/validation, media decoding and native timeline/package checks pass. Actual CRI playback,
synchronization, repeated battles and Steam Deck playback still need testing. See [the implementation and test
limits](docs/CRYSTAL_FINA_CINEMATIC.md). The large optional FFBE animation library remains a separate download.

### Sephira awakening bonuses and requested LB audio — 2026-10-23

[Verified Windows download / run 39921373217](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39921373217/Sephira-Studio-Test.zip)
(code `3d295a6`, extension **1.2.69**; **58.7 MB**).

All 30 Sephira visions gain a themed awakening bonus layer: **160 supplementary bonuses**, with complete
passive counts matching their native stat/Resonance counterparts. All **131 excluded-original passives** remain
in the MR allocation. Active skills, edited MR rewards, permanent stats, identities and acquisition choices
are retained. Native effects/AP costs stay intact; combined passive AP budgets stay within 20% of the original.
Christine now has 16 displayed bonuses like Tronn. See [the complete allocation and balance limits](docs/SEPHIRA_AWAKENING_BALANCE.md).

Close Studio/game and update while keeping **Studio Test Data**. Reopen Studio, click **Apply MR and acquisition
update** once, then rebuild/install and restart the game. The update backs up the roster and adds missing
awakening bonuses; no kit reset is needed. Independent bundled Fina receives the same additive repair where
there is room. A full edited kit is preserved instead of deleting abilities.

Audio includes the requested **Touch It** soundtrack for Ariana and **Accumulate + Cure** for both Fina versions.
Cure follows the existing healing marker. The other 23 original soundtracks remain; five exact Global LB
soundtracks are still unverified, as listed in [the audio report](docs/SEPHIRA_LB_AUDIO.md). Native readback,
Windows validation and package integrity checks pass. Final combat balance and audio synchronization still
need in-game testing. The optional animation library stays separate from Studio updates.

### Sephira LB audio and home-screen bonus counts — 2026-10-22

[Verified Windows download / run 39912426219](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39912426219/Sephira-Studio-Test.zip)
(code `fba79e6`, extension **1.2.68**; **58.6 MB**).

Original FFBE LB recordings now play at their source frame times for **23 Sephira visions**. All 30 have the
original charging cue. The seven exact forms/custom sequences without an original soundtrack are listed in
[LB audio coverage](docs/SEPHIRA_LB_AUDIO.md); unrelated LBs are not substituted. The selected recording pack
is about 1.5 MB and does not require the optional animation library. Home-screen cards now include MR rewards
in their ability/bonus totals, fixing the zero-bonuses display after passives moved into mastery.

Close Studio/game and update while keeping **Studio Test Data**. Reopen Studio, then rebuild/install and
restart the game for the sound changes. Old audio-off defaults upgrade once with a roster backup; later mutes
and custom banks stay intact. No kit reset or second MR update is needed for this change. Existing skill,
mastery, icon and Fina fixes remain. Native bank/timeline readback and Windows checks pass; volume, misses and
perceived synchronization still need in-game listening.

### Sephira MR rewards, elemental attacks and vision icons — 2026-10-22

[Verified Windows download / run 39907648685](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39907648685/Sephira-Studio-Test.zip)
(code `08a5195`, extension **1.2.67**; **57.1 MB**).

All **131 original passives** from the 15 excluded visions are preserved once, with 19 selected extras. Each
Sephira vision now has one passive at MR1/3/5/7/9; former MR active skills move to awakening. Permanent stat/AP
and Spirit rewards stay intact. See [all 150 MR choices](docs/SEPHIRA_PASSIVE_MASTERY.md).

39 custom elemental attacks get the correct elemental icon and a matching native impact at their existing
hit timing. Their original movement, sounds and damage events remain. Each added vision also has its own
battle-command and Spirit icon, fixing the Cloud/Terra donor fallback on later imports for Rain and Lasswell.
Original game icon rows are preserved.

Close Studio/game and update while keeping **Studio Test Data**. Reopen Studio, click **Apply MR and acquisition
update** once, then rebuild/install and restart the game. The migration backs up the roster and preserves
active skill edits, artwork, IDs, permanent rewards and acquisition settings. New/restored presets include it.
Windows checks, package integrity and native readback pass; final rendering and the revised passive balance
still need in-game testing. Existing individual source exceptions remain in the [runtime review](docs/SEPHIRA_RUNTIME_REVIEW.md).

### Crystal Fina battle recovery and MR repair — 2026-10-22

[Verified Windows download / run 39900403407](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39900403407/Sephira-Studio-Test.zip)
(code `aacedcc`, extension **1.2.66**; **57.1 MB**).

The independent Crystal Fina import now has the same MR reward schedule as the collection preset. Studio
recognizes and backs up the exact old stats-only layout, then repairs her rewards without resetting artwork,
identity, acquisition or combat edits. Explicitly edited reward layouts stay intact. Her private passive names,
learned Crystal Renewal and field healing also work when she is added independently of the collection.

The crystal uses a persistent game-thread loop where available, with a recoverable callback bridge on older
loaders. Invalid renderers and failed cleanup cannot block later Fina actors. The accepted glass and animation
speed are preserved. These failure paths pass regression checks; the user's intermittent trigger still needs
confirmation across consecutive battles in the actual game.

Close Studio and the game, update while keeping **Studio Test Data**, reopen Studio and use **Install into the
game**, then restart the game. The known MR layout repairs automatically; no kit reset or game preparation is
needed. Windows validation/compilation, local tests and native reward readback pass. See
[validation and measured timings](CHANGELOG.md#published-crystal-fina-battle-recovery-and-mr-repair--2026-10-22).

### Optional preparation and faster table refresh — 2026-10-22

[Verified Windows download / run 39894606827](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39894606827/Sephira-Studio-Test.zip)
(code `35c4f7b`, extension **1.2.65**; **57.1 MB**).

Build/install directly using the existing local data. Game preparation and patch review stay available under
**Game tools & snapshots**, but neither is required before a normal build. Existing first-run dependencies and
checks against installing a build made for different game data/settings remain.

Optional refresh skips localization string tables, gives each parallel reader a private mappings file, and
remembers unsupported optional table formats until their inputs change. Temporary I/O failures are tried again;
required tables are never silently cached as unsupported. No whole-game refresh or retry pass runs during an
ordinary build/install. Source assets, recipes, selected testing toggles and mod gameplay are preserved.

Close Studio, update while keeping **Studio Test Data**, reopen it and use **Install into the game** normally.
There is no preparation/review step for this update. Windows validation/compilation, Deck transfer checks and
native reader checks pass; actual install timing still needs confirmation on the user's PC. See
[validation and measured timings](CHANGELOG.md#published-optional-game-preparation-and-table-refresh--2026-10-22).

### Complete Sephira runtime pass and FFBE Blood Recovery test — 2026-10-22

[Verified Windows download / run 39889024440](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39889024440/Sephira-Studio-Test.zip)
(code `0b7a2c3`, extension **1.2.64**; **57.1 MB**).

Review all 30 visions across every awakening tier and MR rank. Correct blank private passive rewards, learned
abilities missing from character commands and field-healing availability. Give private skills their original player
presentations and sounds independently of borrowed visuals. Recover Fina's casing after battle visibility transitions
and transient attachment errors. Keep accepted glass, animation timing and gameplay budgets.

Add the explicitly selected **Scartio FFBE Blood Recovery** presentation to Snow White's existing private heal,
including separate front/back layers, red flash and original sound. Her healing strength and MP cost are retained.
Blood Recovery is on her second awakening tier. Its layering and scale remain an in-game test.

Keep **Studio Test Data**, update Studio, rebuild/install and restart the game. Existing prepared full-game data and
the current roster can be reused; corrections apply during building. **Use borrowed Sephira skill visuals** may stay
off. Native serialization, Windows validation/compilation and package checks pass. Every final visual still needs live
confirmation: Fina's boss/vision casing, the reported skills, and the three flagged original presentations in
[the complete roster audit](docs/SEPHIRA_RUNTIME_REVIEW.md). The full optional FFBE library stays separate.
See [validation and measured timings](CHANGELOG.md#published-complete-sephira-runtime-pass-and-ffbe-heal-test--2026-10-22).

### Shop check fix and earlier build errors — 2026-10-22

[Verified Windows download / run 39871672325](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39871672325/Sephira-Studio-Test.zip)
(code `bdc10cd`, extension **1.2.62**; **47.5 MB**).

Fix a separate shop check that still used saved acquisition locations while the temporary 1-gil Mitra override
was enabled. Normal acquisition also verifies Folka's story-gated Olderion stock together with other selected shops.
Acquisition/testing and shop tables are now checked immediately after writing, before skill effects, sprite conversion
and packing; the build stops on the first failing checked table. Final checks remain for later scene edits and generated assets.

Update while keeping **Studio Test Data**, then rebuild/install. Existing prepared data and saved vision settings
can be reused; this update does not need another MR/acquisition migration. Windows checks and cooked full-game table
checks pass. The user's live rebuild/install remains to be confirmed. See
[validation and measured timings](CHANGELOG.md#published-shop-verification-and-earlier-table-checks--2026-10-22).

### Protected MR rewards and temporary 1-gil shop — 2026-10-22

[Verified Windows download / run 39865892697](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39865892697/Sephira-Studio-Test.zip)
(code `19202e6`, extension **1.2.61**; **47.5 MB**).

Replace all 52 reused MR rewards from the original visions being kept, including eight grants that had moved to
awakening. Use equipment/enemy bonuses and bounded enemy skills while retaining kit counts, MR structure, permanent
stats and excluded-vision coverage. See [every replacement and its source](docs/SEPHIRA_REWARD_CHANGES.md).

Update while keeping **Studio Test Data**, use **Apply MR and acquisition update**, then rebuild/install. This backs
up the roster and preserves unrelated edits and saved revision-4 acquisition choices. Prepared game data can be reused.
Home’s **Sephira visions: 1-gil Mitra shop** toggle, off by default, temporarily sells enabled collection members in
Mitra for 1 gil each. Turn it off and rebuild/install to restore their saved locations and prices. Purchased visions stay owned.

Fix the reported final installation check expecting borrowed visual rows after a build using original visuals.
Verification now uses the build’s visual and acquisition modes. Full Windows validation/compilation and Deck checks
pass, and the downloaded package matches provenance, checksums and source. Native readback covers the new bonuses,
abilities, visual routing and shop prices. Gameplay balance and acquisition still need live testing. See
[validation and measured timings](CHANGELOG.md#published-protected-mr-rewards-and-temporary-mitra-shop--2026-10-22).

### Sephira MR rewards and vision challenges — 2026-10-22

[Verified Windows download / run 39857881255](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39857881255/Sephira-Studio-Test.zip)
(code `3fc7cdb`, extension **1.2.60**; **47.5 MB**).

Rework all 30 presets’ MR rewards to follow native progression, preserve their learned skills and awakening budgets,
and add guarded, locally scaled boss challenges for 28 visions. Each opposing team shares one boss budget.
Aria is sold in Mitra; Folka unlocks in Olderion after its guardian story scene. Barusa/Ariana have a separate
Zoldaad cave requiring Wilhelm’s completed quest. Original shrine rewards and repeat memories are preserved.
Crystal Fina also builds correctly after **Restore missing** allocates a new unit ID.

Close Studio, update while keeping **Studio Test Data**, then click **Apply MR and acquisition update** in
**Sephira’s visions** and rebuild/install. The update backs up the roster and retains identities, artwork, custom
skills and learned abilities. Successful preparation for the same game build can be reused. See
[the complete vision guide](SEPHIRAS_VISIONS.md) for locations, prerequisites, rewards and boss teams.

Full Windows validation and compilation pass; the downloaded package’s provenance, checksums and bundled recipes
match source. Native readback checks cover 29 full-game tables, all challenge AI/dialogues and the added Tronn
interaction. Actual battle difficulty, controller flow and every shrine encounter still need live playtesting.
See [validation and measured timings](CHANGELOG.md#published-sephira-mr-progression-and-guarded-vision-challenges--2026-10-22).

### Install after switching game folders — 2026-10-22

[Verified Windows download / run 39833304270](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39833304270/Sephira-Studio-Test.zip)
(code `3c0b1aa`, extension **1.2.59**; **47.5 MB**).

Fix installation stopping because the runtime record belongs to the demo. Keep separate package/runtime records and
backups for the full-game folder, preserving the demo's files and restore history. Carry over an existing managed
loader when the destination lacks one, without copying other mods or overwriting conflicting destination files.

Close Studio, update while keeping **Studio Test Data**, then use **Install the last build** with the full-game folder
selected if your settings/game have not changed. The supplied log confirms its mod built and passed verification;
no new preparation is needed for this installer fix. Windows validation/compilation and install/restore regression
checks pass, and the downloaded package matches source. The user's actual game installation still needs a retry.

### Full-game table support — 2026-10-22

[Verified Windows download / run 39825612562](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39825612562/Sephira-Studio-Test.zip)
(code `db66b58`, extension **1.2.58**; **47.5 MB**).

Use the full game's production composites and split parent tables for skills, sounds, practice battles, native-vision
grants and cave recipes. Prepared full-game catalogs now include production skill routes. Keep **Studio Test Data**,
update Studio, keep the full-game folder selected and retry **Install to game**. Your successful preparation can be
reused; saved recipes and testing preferences are preserved. The pre-upstream rollback kit below remains available.

Full Windows validation/compilation and Deck transfer checks pass; the downloaded package matches source. Native
patcher/readback tests preserve all original rows across sampled full-game skill and sound tables. Actual full-game
cave/menu rows were absent from the supplied reference, and live gameplay still needs testing on the user's PC.

### Native reference collection fix — 2026-10-22

[Verified Windows download / run 39815956581](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39815956581/Sephira-Studio-Test.zip)
(code `1a430dd`, extension 1.2.57; **47.5 MB**).

Fix parallel native-reference readers competing for an exclusive lock on the same mappings file. Each worker now
uses a private temporary copy of the original bytes. Collection logs decoded tables and preserves the actual leading
error plus table name on failure. No upstream engine or mappings update is included.

Close Studio, update its existing folder while keeping **Studio Test Data**, reopen it and retry **Collect current
game reference**. Your successful game preparation can be reused. Choose **Download latest reference** after collection
finishes. Windows native-reader, collection/download regression and full build checks pass; the downloaded files match
source. The subsequently returned full-game reference confirms collection succeeded; see the release checklist.

### Backup before upstream changes — 2026-10-22

[Download the rollback kit](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/pre-full-game-upstream-2026-10-22/Sephira-Studio-Pre-Upstream-2026-10-22.zip)
(**133.0 MB**). [Source checkpoint](https://github.com/biscoBen/FFR-Vison-Studio/tree/pre-full-game-upstream-2026-10-22):
`6c7c15e`, also saved in `backup/pre-full-game-upstream-2026-10-22`.

Preserve the tested app from run **39507226508** (extension **1.2.56**), exact engine **1.0.0.15**, matching core
packs, captured host manifest, checksums and rollback instructions. No upstream changes were integrated.
The published ZIP was downloaded again and verified. This reuses the existing tested binary; it is not a new app build.

Personal configurations and saves are not uploaded. Before updating your own installation, close Studio and copy
its entire folder, including **Studio Test Data**, to a separate location. A Studio backup preserves recorded settings
but does not include every downloaded source artwork pack. The kit is not a one-click offline restore of that private setup.

### Crystal Fina boss installation check — 2026-10-20

[Verified Windows download / run 39507226508](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39507226508/Sephira-Studio-Test.zip)
(code `9493d9b`, extension 1.2.56; **47.5 MB**).

Fix the final table check rejecting the resized Crystal Fina boss because of a numeric rounding difference.
Her boss size remains 130% of her normal vision size. This package supersedes the size update below.
Update Studio, keep **Studio Test Data**, and retry **Install to game**; existing prepared data can be reused.
The actual engine conversion regression and all Windows gates pass. The downloaded files match source;
the user's game installation still needs a retry.

### Crystal Fina boss size — 2026-10-20

[Verified Windows download / run 39504158761](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39504158761/Sephira-Studio-Test.zip)
(code `ddaaba6`, extension 1.2.55; **47.5 MB**).

The practice boss and her crystal now use 130% of her normal vision size, down from the oversized fallback.
Update Studio, keep **Studio Test Data**, and run **Install to game** again. This size change does not require
another game-data preparation. Windows checks pass and the downloaded package matches source; in-game framing
still needs a retry. The preparation fix and Crystal Fina boss fight below remain included.

### Build after preparing game data — 2026-10-20

[Verified Windows download / run 39500304695](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39500304695/Sephira-Studio-Test.zip)
(code `ee10c3d`, extension 1.2.54; **47.5 MB**).

Fix the missing `DA_UIUnitSsLayout.json` error after fresh preparation. Imported sprites skip that unnecessary
layout dump; native sprite clones read the current game's layout directly. The preparation prompt now distinguishes
untracked data, changed game files and interrupted preparation. Older setups can need one initial baseline;
the prompt alone does not prove Steam updated the demo.

Update your existing Studio folder, keep **Studio Test Data**, and retry **Install to game**. A successful
preparation for the same game build is reusable. Full Windows gates, missing-cache regression checks and
Linux/Windows transfer checks pass; the downloaded files match source. The Crystal Fina boss test below remains
included. The user's actual game installation still needs a retry.

### Crystal Fina level-10 boss test — 2026-10-20

[Verified Windows download / run 39495008542](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39495008542/Sephira-Studio-Test.zip)
(code `533749b`, extension 1.2.53; **47.5 MB**).

Enable **Home → Shop practice battle**, rebuild/install and restart the game. Talk to the Young Woman in
Mitra's item shop, then choose **More opponents** until the final page's **Crystal Fina (level 10)** appears.
She has **6,500 HP**, a neutral basic attack, light magic and a self-heal opportunity once per eight actions
when at or below half health. Light is resisted and dark is a weakness. Turn **Survive at 1 HP** off to judge
balance. See [the complete stats and rotation](docs/CRYSTAL_FINA_BOSS.md).

She uses her native body and rotating crystal even without an owned Fina or the Sephira collection enabled.
The fight is repeatable and awards no vision, XP, gil or items; acquisition progression stays unchanged.
Native table/AI/presentation/menu builds and full Windows gates pass, and the downloaded files match source.
Live combat behavior and level-10 difficulty still need an in-game test.

### Launch preparation and local Deck snapshots — 2026-10-19

[Verified Windows download / run 39370792784](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39370792784/Sephira-Studio-Test.zip)
(code `910aa18`, extension 1.2.52; **47.5 MB**).

Open **Home → Launch preparation & snapshots** for fresh native-data comparisons, an original-game test preset,
editable backups and a build-specific regression sheet. **Steam Deck snapshots** is the main transfer route:
build on PC, export **Resonance-Mod-Snapshot.zip**, copy/extract on the Deck and run **Install snapshot.sh**.
No private GitHub repository, token, Studio download or building on Deck is needed. Later snapshots update the
owned files and remove stale runtime; the installer supplies backups and restoration.

**Export Studio backup** separately preserves editable unit recipes and switches. Restore previews the roster,
backs up the current setup and prevents stale desktop saves from overwriting it. Native game fingerprints guard
preparation, installation and Deck transfer. Full Windows gates, Linux/Windows transfer checks and browser round
trips pass; full-game compatibility and real Deck/Proton playback still need testing. The existing optional
1.99 GB animation library is reused. See [the guide](docs/LAUNCH_PREPARATION.md) and
[validation/timings](CHANGELOG.md#published-launch-preparation-and-local-steam-deck-snapshots--2026-10-19).

### Portable fog edges and complete source choices — 2026-10-18

[Verified Windows download / run 39150580826](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39150580826/Sephira-Studio-Test.zip)
(code `bbf642f`, extension 1.2.48; **46.6 MB**). The optional **1.99 GB** library stays separate and is reused;
its 56 source packs have not changed. No source-library redownload or mod rebuild is needed for browsing.

Use **Home → FFBE animation library**, then **Find a source** and the grouped **Ability source** selector.
The full data audit adds **531 source choices**, bringing the selector to **3,901**, including Christine and
94 previously omitted named monsters. All **21 esper** ownership links are corrected. Every associated owner
can find a shared presentation, even when its first displayed source is someone else.

Christine has **seven matching library records**. Her Global-exclusive skills such as **Snow Burial** have no
matching record in this supplied Memorial archive; the selected source lists those unavailable skills by name.
Known sources remain selectable even when no matching skills or skill associations are recorded. No substitute
animations are guessed. **All sources** clears the filter.

**Soften exposed fog edges** is on by default. It feathers exposed fog/cloud/smoke outlines in the actual generated
texture alpha, including the background wall and slanted sheet in Unei's **Snowstorm**. Uncheck it to compare
original edges. Under **Effects and sound cues**, **Download visual-layer conversion** provides the prepared
textures, animation document and a helper for the existing SpriteStudio converter. The exported textures preserve
the correction through conversion; these files assign nothing to the game. Skill timing placement, anchors,
sound routing, asset capacity and game bindings still need integration.

Windows full validation, frozen-engine setup, launcher/updater checks and compilation pass for this exact code.
The downloaded package matches all **46** extension and **16** Crystal Fina file hashes and contains no large library
packs. Chromium checks cover source filtering, both edge modes, layering and a real conversion download. All **199**
fog-sheet cells retain exact RGBA through the existing converter's PNG and BGRA atlas output. This proves portable
visual data, not live-game playback or full FFBE camera/3D parity. Full validation, checksum and measured timings
are in [the changelog](CHANGELOG.md#published-portable-fog-edge-conversion-and-missing-source-coverage--2026-10-18).

Native missing-animation repair work is on hold until the full game launches on Thursday, as requested.
Retest the recorded original-enemy failures then before adding further demo-specific repairs.

Home's **FFBE animation library** button opens a local browser page. The optional
**1.99 GB** source download is separate from the Studio app: the page checks existing files, then asks **Download library / Not now**
if needed. Normal startup downloads nothing. Progress, pause/resume and checksum repair reuse completed files;
existing installations from the earlier bundled library are recognized automatically. App updates keep the data under
`engine/library/ffbe/`; previews are cached separately under `engine/build/ffbelib1/`.

Browse **45,478** distinct skill presentations backed by all **65,428** retained Memorial master records,
**15,674** effect groups, **8,779** effect definitions and **90** cinematics. Entries show an actual character,
monster or esper source name; ownership comes from original grant/skill-set records. Unlinked entries explicitly
say **Unattributed FFBE source**. Search finds skills and all associated source names. Matching presentations use
the first known source; monster/character versions and differences in animation files, timing, targeting, sound or
cinematics stay separate. Original IDs/aliases remain retained for future conversion.

Use animated **Christine 6★** and **Cactuar** as caster/target, swap the caster and choose one or three targets.
Christine uses her FFBE idle; Cactuar uses the supplied Resonance demo idle. Original hit times flash the target.
Filter magic, abilities, monster skills, limit bursts or summons. Enable **Include records without animation references**
to see passive and other records without visual timelines. Sound, speed, seeking, zoom and conditional controls remain
available; cinematics have their own controls and embedded sound. Browsing makes no changes to units, kits, mod inputs
or installed game files.

Use **Ability source**: type a name in **Find a source**, then choose the exact character/vision,
monster or esper from the grouped selector. Select **All sources** to clear it. Source filtering combines with skill
type and text search; **Include records without an animation reference** also shows that source's passive/unanimated
records. Shared animations remain included for every recorded owner, and the selected preview uses that owner's
actual skill record. Sources come from archived Memorial ownership links and checksum-pinned Global grants;
Global links require an exact typed skill ID and matching original name. Unattributed records stay in the full list.
Selected sources list known Global skills with no matching Memorial record, rather than hiding the source itself.

The preview corrects **Unei → Snowstorm** layering: rear effects draw behind the units, foreground effects draw
over them, and screen-wide backdrops use a separate viewport projection. Original effect files, sound and blend values
are retained. The library still approximates source camera motion/3D projection rather than reproducing FFBE's engine.
Mesh previews also retain their authored pivot through rotation/mirroring, and preview framing includes rotated corners.
Shared triangle edges follow GL's top-left fill rule so translucent triangles do not shade a common diagonal twice.
Separate soft/original caches include the portable fog-edge treatment described above. These common fixes apply
throughout the library; they do not establish that all 45,478 presentations match FFBE exactly. Camera motion,
mixed-axis 3D transforms and other unsupported source behavior still need native comparisons.

The APK and its delivery catalogs are SHA-pinned; original master rows, BMB/PNG/M3R/CGG/CGS dependencies,
source variants, USM cinematics and SE/System sound banks are retained. The page includes **1,011** cue records
and **990** distinct recordings, decoded losslessly and trimmed to their declared sample lengths. Original
cue variants, delays and play/stop instructions remain associated with the effects. The one unsupported System
block-sequence cue is retained in the bank; every referenced skill-group SE cue resolves.

Some master references have no matching file in this delivery: one BMB, 26 sprite dependencies, six group IDs
and 110 exact cinematic filenames. These remain visible and unavailable rather than receiving substitutes;
available regional cinematic variants can be browsed independently. These counts cover master-file references; some
archival BMBs also name editor/template resources absent from delivery or use unsupported preview formats. The **Source coverage** disclosure and entry
warnings explain gaps. Browser particle rendering is approximate, shows at most 30 seconds/256 particles per
emitter and does not prove exact FFBE rendering or later Resonance conversion. Original files are not truncated.

This includes the four standalone first/second-part limit-burst clips indexed separately from their full-film references.

The source packs are published independently under the stable `ffbe-library-memorial-en-v208-1` release.
Studio carries a small trusted manifest and browser metadata; future app updates reuse these immutable source packs.
The normal engine remains checksum-pinned. Library inspection uses a private renderer based on the
[pinned upstream effect tools](https://github.com/FFBE-JP-Translation/FFR-Vison-Studio/tree/990f2ccab25a6132b0bb3b217420899f6d0e38d9/mod-tools/tools/ffbe_effects),
with ordered placement/native UV support. No external converter is required for browsing.

To reproduce the source library as a developer (Python 3.12+, Pillow, NumPy, PyCryptodome and FFmpeg/FFprobe
with HCA/USM, VP9 alpha and Opus support), use the supplied APK and supported engine tools:

```sh
python scripts/prepare_ffbe_memorial_sources.py --apk <v208.apk> --output <source>
python scripts/prepare_ffbe_library_audio.py --source <source> --work <work> --engine-tools <engine/tools>
python scripts/prepare_ffbe_library_movies.py --source <source> --work <work>
python scripts/build_ffbe_animation_library.py --source <source> --work <work> --extract
python scripts/verify_ffbe_animation_library.py
python scripts/build_ffbe_library_browser.py --source <source> --actors <original-idle-sprites> --global-source <pinned-global-json-folder>
```

The browser overlay takes the original `christine.webp` (401002606) and native `cactuar-native.png` idle
sheet. Its metadata records their source hashes and the master-table hashes used for ownership. The optional
Global ownership folder uses the exact JSON inputs and commit pinned by
[`global-ownership-lock.json`](scripts/fixtures/ffbe_library/global-ownership-lock.json); mismatched hashes are rejected.

The APK is inspected rather than executed; source downloads use only its verified delivery URLs/ranges. Normal
Studio use needs none of these developer dependencies. Game assets retain their original ownership.

### Intermittent Mitra crash diagnostics — 2026-10-17

The user confirms that the in-game practice picker opens and the revised FFBE **1,000 Needles** visual and hit
sound play correctly. A separate generic **Fatal error!** occurs both while walking around Mitra and on a second
interaction with the practice woman. The first interaction worked. This report does not identify the failing
function or establish that the picker caused the walking crash; retain these observations separately from the
previous explicit name-index serialization failure. Misses reportedly have no sound; the imported timeline uses
`SoundPlayHitSound`, so this is not yet evidence of a missing source cue.

Use the [read-only crash collector](scripts/reference/game-crash/) after the crash, **before restarting the game**.
Extract its three files together and run **Collect Resonance Crash.cmd**. Accept or enter the game folder and
attach the **Resonance-Crash-Reference-*.zip** from **Downloads\FFR Mod**. It gathers recent Unreal crash contexts,
game/UE4SS log tails, runtime hashes, mod-file inventory and available testing/repair-version reports. It installs
nothing and needs no Studio update, tracer, mod rebuild or live game. The crash remains undiagnosed until that
report is available. Test coverage uses a fake installation; it does not reproduce the user's crash.
The standalone collector source passed [Windows run 39069211497](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/39069211497)
(code `31c2d35`): 445 Python checks (seven skipped), including the helper's real file-collection tests. The helper ZIP
is provided directly in chat because GitHub rejected the extra release-asset upload; source remains available above.
No Studio/game/runtime update is required for collection. Full validation and measured timings are in the changelog.

[Verified practice menu crash fix / run 39067343262](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39067343262/Sephira-Studio-Test.zip)
(code `b57a263`, published 2026-10-17; extension 1.2.42). Fix **Bad name index 79/36** while opening the practice
picker. Retain the full 80-name map on every menu page, preserving the appended choice tag at index 79 during
IoStore packing. Check the retained prefix after writing. Update Studio, rebuild/install your mod and restart.

Windows analysis, **263 Flutter tests** (one skipped), **439 Python checks** (six Windows/seven local skips), fresh
engine startup, launcher/updater checks and compilation pass. The actual engine serializer checks all six tag
indices. Packing/extracting the old page reproduces unresolved `79`; all six corrected packed pages retain their
menu tags, callbacks, unbound tracks and compiled timing after native readback. Container integrity alone missed
the original error. Downloaded provenance/checksum and **37** extension resources match source; **16** Crystal Fina
resources remain unchanged. The user subsequently confirms that the menu works; repeated interaction and walking
now expose a separate intermittent generic fatal error, tracked above. Paging/cancellation remain unconfirmed.
First complete candidate **20:33:57 UTC** to verified download **20:41:35 UTC**: **7m 38s**. One matching push run:
CI **6m 02s**, runner job time **9m 25s** (**9m 01s Windows**, **24s Linux**).

[Verified mixed-build testing verification fix / run 39065483449](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39065483449/Sephira-Studio-Test.zip)
(code `7e1f095`, published 2026-10-17; extension 1.2.41). Fix the final unit-table check when imported visions and
**Survive at 1 HP for testing** are enabled together. Check the complete build recipe alongside independently
recomputed testing requirements, retaining all imported rows and native edits. Missing/extra rows and wrong values
still fail, with affected row names reported. Update Studio, rebuild/install your mod and restart Resonance.

Windows analysis, **263 Flutter tests** (one skipped), **437 Python checks** (six skipped), fresh engine startup,
launcher/updater checks and compilation pass. Reproduce the old failure with native tables, then pass the actual
verifier with three imports, a native stat override, additional private passive/effect rows and survival together.
Native practice table/sequence readbacks and IoStore packing also pass. Downloaded provenance/checksum and **37**
extension resources match source; **16** Crystal Fina resources remain unchanged. Live behavior still needs user
confirmation. First complete candidate **20:06:25 UTC** to verified download **20:15:57 UTC**: **9m 32s**, including a
fixture correction and repeated local checks. One matching push run: CI **6m 34s**, runner job time **9m 57s**
(**9m 29s Windows**, **28s Linux**).

[Verified practice menu link fix / run 39063684610](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39063684610/Sephira-Studio-Test.zip)
(code `3e58dfa`, published 2026-10-17; extension 1.2.40). Fix the subsequent `ContinuousEventList` empty-struct-array
build failure. Use a populated native template while restoring the shop woman's original dialogue, arguments and
settings, then add only the menu link. Write her arguments as a native map. Update Studio, rebuild/install and restart.

Windows analysis, **263 Flutter tests** (one skipped), **431 Python checks** (six skipped), fresh engine startup,
launcher/updater checks and compilation pass. The actual-engine regression test reproduces the original error and
accepts all nineteen corrected dialogue edits. Both native talk tables, the map/encounter/stage tables and all six
choice sequences pass exact readback and IoStore packing. The supplied references omit the composite map and UI
choice table; those have logical/schema coverage, and the user's log confirms its choice-table write succeeded.
Downloaded provenance/checksum and **37** extension resources match source; **16** Crystal Fina resources remain
unchanged. Live menu operation still needs confirmation. First complete candidate **19:42:27 UTC** to verified
download **19:49:25 UTC**: **6m 58s**. One matching push run: CI **5m 28s**, runner job time **8m 53s**
(**8m 27s Windows**, **26s Linux**).

[Verified practice boss-category fix / run 39062414190](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39062414190/Sephira-Studio-Test.zip)
(code `c6e3acc`, published 2026-10-17; extension 1.2.39). Fix the table-preparation failure on Gigantuar (352):
it, Sheratan and Alpherg use the game's native `Boss` category. The practice picker now accepts these alongside
`Enemy` opponents, preserving their original stats and AI. Update Studio, rebuild/install and restart Resonance.
The optional `System.acb` LB-opening sound warnings are separate from this failure.

Windows analysis, **263 Flutter tests** (one skipped), **429 Python checks** (six skipped), fresh frozen-engine
startup, launcher/updater checks and compilation pass. All twelve encounters pass preparation with the supplied
native unit rows, native table readback and IoStore verification. Downloaded provenance/checksum and all **37**
extension resources match source; **16** Crystal Fina resources remain unchanged. Live menu interaction remains
pending confirmation. First complete candidate **19:23:16 UTC** to verified download **19:31:30 UTC**: **8m 14s**.
One matching push run: CI **5m 29s**, runner job time **9m 10s** (**8m 44s Windows**, **26s Linux**).

[Verified FFBE needle groups/audio and in-game practice picker / run 39059206346](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39059206346/Sephira-Studio-Test.zip)
(code `ba64cb5`, published 2026-10-17; extension 1.2.38). **Test FFBE 1,000 Needles visual** now retains
four separate source streaks and the original hit recording. **Survive at 1 HP for testing** allows normal damage
and healing with native unlimited reprieve/instant-death resistance. **Shop practice battle** opens an in-game
opponent picker at Mitra's item-shop Young Woman: twelve encounters across six pages, plus cancellation.
Enable the desired switches, rebuild/install and restart. Opponent choices then require no rebuild.
For an isolated FFBE comparison, leave **Use our skill changes** and **Use borrowed Sephira skill visuals** off;
the native binding/motion repair switch may remain on. Revised appearance/audio, survival damage/status cases,
and live menu interaction still need user confirmation; the first visual import itself has been confirmed playing.

Local analysis, **263 Flutter tests** (one Windows-only skip) and **428 Python checks** (five skipped) pass.
Windows analysis/tests, compilation, fresh frozen-engine setup and launcher/updater checks pass for the same
commit (428 Python checks, six skips). Actual cooked effect/audio/timeline/binding checks, all **8,917 animation
keys**, exact atlas pixels, native survival tables, six native choice pages and IoStore packing pass.
The downloaded provenance/checksum and all **37** managed extension resources match source; all **16** Crystal
Fina resources remain unchanged. Unsupported BMB generation shapes/alignment still require separate adapters;
this does not establish parity for every FFBE spell.
First complete candidate: **18:23:41 UTC**; downloaded package/source verification: **18:48:01 UTC** on 2026-10-17,
**24m 20s** elapsed including corrections, waits and verification. Successful CI: **5m 31s**. Measured runner job
time across both runs: **11m 34s** (**11m 04s Windows**, **30s Linux**). One redundant manual run was cancelled
when the matching push run became visible; the verified download uses the successful push run.

[Verified original Cactuar practice test / run 39011466161](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39011466161/Sephira-Studio-Test.zip)
(code `90ec6b2`, published 2026-10-16; extension 1.2.36). Enable **Shop practice battle** and choose
**Practice opponents → Cactuar (level 30, original AI)**, then rebuild/install. The Young Woman in Mitra's item
shop starts the private clone of its original solo encounter. Let Cactuar use **1,000 Needles**, bookmark with
**F8** in the existing runtime trace helper, and collect with option 2. Keep visual-substitution options off.
The follow-up visual test found no visible 1,000 Needles animation from the tested Cactuar either; no enemy trace
was collected. Its exact runtime route remains unconfirmed. The imported-vision fallback and the scope of this
observation are documented [below](#confirmed-runtime-fallbacks). No missing skill visual is marked repaired.

Local analysis, 262 Flutter tests (one Windows-only skip), 418 Python checks (five skipped), and both encounter
choices' actual native encounter/stage serialization, exact readback and IoStore verification pass. Windows
validation and compilation pass for the same commit, including fresh frozen-engine setup and launcher/updater.
Downloaded provenance/checksum and all 35 managed extension resources match source; all 16 Crystal Fina resources
remain unchanged. The first Windows attempt caught a mismatched Studio version check, corrected before publication.
Measured first-complete-candidate to verified download: **18m 54s**, including corrections and waiting. The successful
CI run took **5m 31s**; all three attempts used **22m 14s** of runner job time (**21m 27s Windows**, **47s Linux**).

[Verified native aiming and motion compatibility / run 39004444107](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39004444107/Sephira-Studio-Test.zip)
(code `56a9d39`, published 2026-10-16; extension 1.2.35). Correct the private player effect point for Thwack,
Bio and Banishra. Add El Niño's private player route with its original effect/timing, correct native aiming and
complete caster track; retain its original shared binding and enemy presentation. Imported battle models also expose
native `atk` as their own `attack_A` clip when a repair mode is enabled. Existing clips, atlas pixels and menus are
preserved; Crystal Fina's optional alias uses her accepted shot/mirroring without changing her existing presentation.

Local analysis, 260 Flutter tests (one Windows-only skip), 404 Python tests (four skipped), all 23 native player
routes (92 packages), both retained enemy routes and 25 additions per lookup pass serialization/readback and
IoStore verification. Native SS6 readback confirms the exact attack alias. Windows validation and compilation
pass for the same commit, including frozen-engine startup and updater/launcher checks. Downloaded provenance/checksum
and all 35 managed resources match source. The new changes need live tests; earlier Absolute Zero, Bioblaster,
Aqua Breath and repaired Cling have user confirmation.

For isolated animation testing, turn on **Show unverified skills** and **Repair native skill bindings / motions**,
and leave **Use our skill changes** and **Use borrowed Sephira skill visuals** off. Rebuild/install and restart
Resonance after updating. Saved kits and explicit custom presentations retain their precedence. The `atk` name
makes the recipient's attack available to native callers; it does not itself create a missing timeline/effect.

All 89 returned comprehensive reference ZIPs are valid: 7,130 assets, four restored large files, and no missing
packages. Windows console decoding caused 17 false missing-name reports; the [routing collector](scripts/reference/skill-routing/)
now forces UTF-8. The current collection needs no rerun. All 233 tables, two sequence-event blueprints, 258 AI
blueprints and ten original monster projects decode successfully. Secondary links do not resolve the twelve blank
skills in the test batch. Their AI assignments and matching-number files do not establish portable visual routes,
and no substitute visuals are silently assigned. See [findings and limits](docs/MONSTER_ANIMATION_COMPATIBILITY.md#returned-comprehensive-collection-and-extension-1235)
and the [machine-readable evidence](docs/native-skill-routing-findings.json). The collection already includes native
reflection data for further runtime investigation; there is no need to repeat the asset extraction at this stage.

The follow-up test still has eight blank entries, including newly reported Blighted Gloom, Bubble Breath and
Carmine Inferno. They are recorded in the [test findings](docs/MONSTER_ANIMATION_COMPATIBILITY.md#follow-up-blank-skills-and-sampled-runtime-trace).
The [verified Skill Runtime Trace helper source/instructions](scripts/reference/skill-runtime/)
(code `41ea510`, checked 2026-10-16 by [Windows run 39007387217](https://github.com/biscoBen/FFR-Vison-Studio/actions/runs/39007387217)). Compare one failed skill with a
working one and observe original enemy actions. It samples through the existing UE4SS loader and makes no playback
changes. Close the game, choose **1** to enable, relaunch/test, then choose **2** to collect the small ZIP in
Downloads\FFR Mod. Close the game and choose **3** to remove it. No Studio update or mod rebuild is required.
Missing sampled records do not prove an effect never played; short events can fall between samples.

### Confirmed runtime fallbacks

The returned `Skill-Runtime-Trace-20261016-231903-ce871e.zip` contains a successful observer capture:
2,421 log lines, 588 battle samples, three bookmarks and no collection errors. The user confirmed the cast order
as **1,000 Needles → Aqua Breath → Atomic Ray**. The collected engine is extension **1.2.35**; all recorded
resource hashes match the committed extension, and its build report selects **native repairs** with the `atk`
alias. This establishes the collected engine state; installed game containers were not part of this collection.

| Cast | Observed playing sequence | Result |
| --- | --- | --- |
| 1,000 Needles (500270), 23:17:42 | `Skill/900000/SEQ_Battle_900000_Master` | Generic fallback; no job-linked skill particles recorded; vision remained idle |
| Aqua Breath (500800), 23:17:55 | `EnemySkill/500800/500801/SEQ_Battle_500801_Master` | Original timeline, linked water effect and `magic_idle`/`magic_attack` motions recorded |
| Atomic Ray (500380), 23:18:11 | `Skill/900000/SEQ_Battle_900000_Master` | Generic fallback; no job-linked skill particles recorded; vision remained idle |

Times are the local timestamps in the supplied UE4SS log. Skill IDs for the two fallback casts are matched
from the user's bookmark order and catalog names: the optional runtime `GetSkillId` read was unavailable,
logged once and did not stop capture. Native enemy actions in this battle used other skills; original enemy
1,000 Needles/Atomic Ray playback was not observed.

The original binding's Japanese row name, **シーケンサー未設定用**, means **for an unset sequencer**. Its native
900000 package has exactly one event track, enabled, with one `OtherReaction` event at tick 4000. There are
no disabled motion tracks, caster-animation events, particle spawns, effect imports or child sequence imports
to restore in this fallback. The same package bytes are present in both complete reference collections. Its
event schedules combat reaction without supplying a skill presentation, explaining damage/status processing
while the imported vision stays idle. The working Aqua Breath cast provides a positive playback comparison.

This identifies the immediate cause for these **two tested casts**; it does not establish that every unbound
skill is broken or that the original effects cannot exist through another native enemy path. The other six
recently reported blank skills were not cast in this capture. There are no skill-specific tracks to restore inside
this fallback, but another original enemy path remains possible. Existing donor-based substitutes remain under
their existing options; this finding adds no substitute or verified label. No repeat of these two imported-vision
casts or comprehensive asset extraction is needed to establish the fallback behavior.

Cactuar's native unit (38) and AI do select the same **500270** ID, distinct from ordinary **Needle (500260)**.
Its collected AI blueprint hands scheduled actions to a native method. In the **2026-10-17 follow-up visual test**,
the user reports that the tested Cactuar also casts **1,000 Needles with no visible animation**. No tracer was run
for this test, so it establishes the reported enemy-side appearance, not its selected sequence or the absence of
all possible original assets. Together with the imported-vision trace and unset binding, this supports an unfinished
demo presentation as a possibility. It does not establish the cause of the other blank skills or other Cactuar variants.
This does not verify its original visuals. Its existing ordinary-Needle substitute remains confined to
**Use our skill changes**; native-only mode continues to preserve the original source presentation.

For that comparison, enable **Shop practice battle**, rebuild/install and restart, then talk to the Young Woman
in Mitra's item shop. Her native in-game picker offers two opponents per page, **More opponents** and **Cancel**.
Choose **Cactuar (level 30): 1,000 Needles**, defend and let it act. Its native AI may flee; repeat as needed.
Use the existing [runtime trace helper](scripts/reference/skill-runtime/) and F8 if you want to record the route.
Selecting another opponent requires no new build. The old Studio dropdown has been removed.
All twelve choices use private story-free encounters, original enemy units/AI, the native plains backdrop,
guaranteed escape and the usual practice reward (or the MR test override). Original encounter rewards are unchanged.
This picker supplies comparisons; it does not repair missing native skill animations.

### Consolidated original-enemy visual tests — 2026-10-17

The user reports that every skill targeted by the practice comparison list has no visible animation on its
original enemies, and adds the specific failures below. Carry the earlier Watcher/Malbodoom failures forward
when the exact same skill ID occurs on another tested unit. Other attacks the user actually received did show
animations; this does not mark every skill in each enemy's AI as tested. No new runtime trace accompanies this
report. These are visual observations, not proof that another source asset or native route cannot exist.

| Original enemy | Reported missing visuals, including the primary comparison target | Additional previously failed skills referenced by this enemy's AI |
| --- | --- | --- |
| Cactuar (38) | 1,000 Needles (500270), original demo version | — |
| Watcher (188) | Megavolt (500180), Atomic Ray (500380) | — |
| Ganymede (196) | Atomic Ray (500380) | — |
| Malbodoom (257) | Bad Breath (505020), Pollen (500690) | — |
| Malboro Marquis (258) | Bad Breath (505020), Flatten (500190) | Pollen (500690), previously blank on Malbodoom |
| Gigantuar (352) | 10,000 Needles (505110) | — |
| Sheratan (641) | Alluring Pollen (503770), Octostrike (501070), Branch Spear (503780), Stonega (255170), Aeroga (250190) | Pollen (500690), previously blank on Malbodoom |
| Alpherg (651) | Bubble Breath (501680), Reflectga (503800), Waterga (250150 or 255110), Flare (250330) | Aeroga (250190), same ID as Sheratan's failed cast |
| Bomb (24) | Self-Destruct (500720) | — |
| Wood Eyes (23) | Constrict (500590) | — |
| White Peak (283) | White Wind (500810) | — |

This tracks **19 distinct failed skill names**. Checking every practice enemy's collected
`DT_BtlUnitAIParameter` row finds **20 candidate skill IDs**, because Alpherg has both single-target Waterga
(250150) and group Waterga (255110); its reported cast does not identify which variant played. Sheratan's Stonega
is the enemy group version (255170), its Aeroga is enemy 250190, and Alpherg's Flare is enemy 250330. Do not
transfer these failures to working vision versions with the same display name. Pollen (500690) remains separate
from Alluring Pollen (503770). Additional shared AI references in the last column are investigation flags;
the report does not independently establish another observed cast for each of them.

Previously reported working original casts remain recorded: Watcher's **Missile, Laser, Machine Gun and Poison
Gas**, and Malbodoom's **Whip and Digestive Fluid**. Preserve those presentations. The native Cactuar baseline
also stays separate from the optional imported FFBE 1,000 Needles visual, which now has user-confirmed correct
playback and successful-hit sound. **Blighted Gloom** and **Carmine Inferno** remain earlier imported-vision
failures; no matching cast by these practice enemies has been established.

Enemy-side blanks show that imported-vision-only binding changes cannot explain all these failures. Investigate
each exact variant's own routing and source assets before adding an import or substitute. This record changes
no skills, visual substitutions, verification badges or game assets, and requires no Studio update or rebuild.

### Original-enemy comparisons for missing skills — 2026-10-17

The returned demo Skill-Routing reference includes the following native enemy candidates. Each pairing is
confirmed by its AI parameter's exact skill ID, its assigned native AI Blueprint and the actual collected cooked
SpriteStudio project, material, base-color/normal/material textures and their `.uexp` companions. This establishes
included assets and native skill usage, not natural story access or successful playback. Late-game rows alone
must never be treated as proof that the normal demo can reach the encounter.

| Missing skill | Included original enemies | Unit IDs |
| --- | --- | --- |
| Atomic Ray (500380) | Watcher; Ganymede | 188; 196 |
| Bad Breath (505020) | Malbodoom; Malboro Marquis | 257; 258 |
| 10,000 Needles (505110) | Gigantuar | 352 |
| Alluring Pollen (503770) | Sheratan, first form | 641 |
| Bubble Breath (501680) | Alpherg, first form | 651 |
| Self-Destruct (500720) | Bomb | 24 |
| Constrict (500590) | Wood Eyes | 23 |
| White Wind (500810) | White Peak | 283 |

All enemies in this table are now in the practice picker, and the user has reported the blank comparisons above;
no repeat of the same casts is needed just to reconfirm those observations. Sheratan and Alpherg use conditional
boss AI, so a skill listed in their AI is not automatically an observed cast. For further native comparisons, set
**Use our skill changes**, **Use borrowed Sephira skill visuals** and **Test FFBE 1,000 Needles visual** OFF. The native binding/track repair option may stay ON. Keep **Survive at 1 HP for testing** ON if needed.
These pairings establish AI usage, not that their native visuals work. Allow enemy turns and report the actual
skill name, visible effect, direction and sound; a skill it never casts is untested, not a failed visual.
Existing native-only fixes also permit comparisons against Belmodar's Thwack and Dark Skeleton's Throat Strike;
those two originally lacked player routes but already have native repair work.

The first reported blank 1,000 Needles vision cast was made with **Test FFBE 1,000 Needles visual OFF**, as the
user confirmed. It is not a failed enabled-import test. Subsequent enabled tests confirmed playback, and the latest
revised build now has user-confirmed line placement and hit sound. Its import is separate from the original Cactuar baseline.

### FFBE 1,000 Needles import investigation — 2026-10-17

The supplied [Memorial v208 APK](https://github.com/luminest-llc/ffbe-memorial-downloads/releases/tag/production-v208-9d21fc8b61c9900e)
resolved the missing art. Its SHA256 is `9d21fc8b61c9900eaacb1c2ddef2cabcad1e97d2dc720be16ac09b06fc0086b4`.
The APK was inspected statically, never executed. Its embedded delivery catalog points to public range-packed
files; each selected CPK/master download was verified against the catalog's SHA256.

Memorial magic **40050**, **1,000 Needles**, confirms `40:5002490:1:1:0` and source hit frame **92**.
Group **5002490**, `harisenbon1`, spawns effect **1002460** eleven times at frames 0, 4, …, 40,
with vertical offsets 40, 0, −40 repeatedly (last offset 0). These are 60-fps source frames.
Memorial monster skill **151400**, **1000 Needles**, independently confirms the same group and start frame;
its own damage cue is frame 80. The prototype consistently uses magic 40050's frame-92 single-hit cue on both sides.
The recovered `F_EFFECT_MST` maps that effect to type-5 **`atk_nail1_white.bmb`**, scale 100%.
`battleEffect1.cpk` supplies that 10,256-byte BMB; the `effectResource` packs supply its two PNG textures
and `position_model_circle12.m3r`. The exact source files, selected master rows, per-file checksums and
[provenance](scripts/fixtures/ffbe_needles/provenance.json) are retained in the project.
For another effect, the APK's `assets/base_delivery.tsv` indexes public CPK/master ranges and SHA256 values.
This source uses `HfRPdg65.dat` (effect definitions), `ZM06fUem.dat` (groups), `6J8jwSDW.dat` (magic),
`wJE09yxD.dat` (monster skills) and `TK61DudV.dat` (abilities). Static `libgame.so` master metadata identifies
the table decoder; CPK members use masked UTF directories and some CRILAYLA compression. Resolve the definition
before requesting its media: names alone do not establish the file type or dependencies.
The earlier published JP masters/public unit host did not contain this complete payload; no more Resonance
extraction is needed to recover this particular FFBE effect.

**Test FFBE 1,000 Needles visual** is a separate, default-off home switch. Enable it and rebuild/install to
add private ally/enemy routes **500271/500272** for Resonance skill **500270**. Keep **Use our skill changes**
and **Use borrowed Sephira skill visuals** off for an isolated comparison. The native bindings/motions repair
switch may remain on. This test takes priority over the ordinary-Needle substitute for this skill. It does not
teach the skill, edit kits, or change native MP, damage, targeting, AI or rewards. Turn it off and rebuild/install
to restore prior routing. Cactuar practice can exercise the enemy side; a vision equipped with the original
1,000 Needles can exercise the ally side.

The imported project retains all **1,760 particle-frame instances** (no drops/shrinks), eleven source spawns,
source-timed start at frame 40 and one native damage reaction at frame 92. The effect attaches to the selected
target's `Null_center`, rather than a hard-coded party-side point. Explicit destruction follows the visual tail;
hidden padding prevents looping before cleanup. The original FFBE hit sound now accompanies its twenty source
triggers. No camera, grading, game-speed or FFBE mechanics are imported. Its private sequence, project/texture and both binding tables pass actual cooked serialization,
readback and IoStore verification; the build checks event constants, project import, target, one hit, cleanup,
event-channel times and compiled playback times before packing.

The user confirmed the first import plays in Resonance, but its four simultaneous streaks were superimposed.
The source BMB selects **ordered-model emission** (mode 8): `position_model_circle12` supplies vertex positions,
scaled by the node's XYZ factors and inherited by its children. The development converter now preserves that
placement and per-node emission ordinal. Its four initial streak positions are distinct and all child trails follow.
This fixes a converter feature rather than adding arbitrary copies of one streak. Other nonzero shape/alignment
modes fail explicitly until implemented; this does not establish general parity for every FFBE effect.
The retained original cue **99 / se_special_needle_1** from checksum-verified `SE.acb` plays at group frames
0, 2, …, 38 (relative to visual start 40). Its complete mono HCA recording uses the existing host-format adapter
and installed-game routing/key. Twenty cosmetic sound pulses still produce just one native damage reaction.

This is a **visual-import prototype requiring live testing**, not a claim that all FFBE effects now work or
that its offline preview exactly matches FFBE's renderer. The converter simulates BMB particles; source random
placement jitter is omitted deterministically, and the build-15 writer uses its standard Mix/Add materials
instead of newer identity PartsColor keys. Revised spacing, sound level, target placement and repeated casts need in-game
confirmation. Other failed native skills remain a separate investigation.

Reproduce the shipped payload with `python scripts/build_ffbe_needles.py --converter <tools/ffbe_effects>
--work <temporary-directory>`, using the [pinned upstream converter](https://github.com/FFBE-JP-Translation/FFR-Vison-Studio/tree/990f2ccab25a6132b0bb3b217420899f6d0e38d9/mod-tools/tools/ffbe_effects)
and Pillow/NumPy. Studio uses the checked output ZIP and its existing asset writer; it does not download or
execute the APK or require the converter on the player's computer.

[Verified native-only mode and 21 native skill routes / run 38986188584](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-38986188584/Sephira-Studio-Test.zip)
(code `aa0452b`, published 2026-10-16; extension 1.2.33). Local analysis, 58 focused Flutter tests and
393 Python checks pass. All 21 native routes pass actual asset build/readback and IoStore verification;
only Cling has live confirmation. Windows validation and compilation pass for the same commit, including
full suites, frozen-engine startup and launcher/updater. Downloaded provenance/checksum and all
35 managed resources match source. Accepted Fina, cave, party knockout and native icon renderer bytes remain unchanged.

Cling's missing ally timeline is repaired when **Show unverified skills** and either repair checkbox are on.
Its original all-target effects, hit timing, sound and combat values are retained. The private copy enables only
its checked caster track and maps enemy `atk` to imported `attack_A`. Generic audited group-skill reuse now
creates a player route too; ally/enemy suffixes do not identify target count. The user confirmed repaired Cling works.
Whip, Tentacle, Sonic Boom, Bite and Incisors are labeled **Verified; demo test** based on the
user's successful tests, checked against their exact catalog definitions.

Imported vision portraits now use native face/timeline/ability frames without the blue backing or FFBE rarity
badge. Portrait layout controls remain available, and the advanced preview uses the same renderer.
Update Studio, rebuild/install the mod and restart Resonance to refresh the game icons and Cling timeline.
See [monster animation evidence and native icon details](docs/MONSTER_ANIMATION_COMPATIBILITY.md).

[Verified Cling and native icon update / run 38982081785](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-38982081785/Sephira-Studio-Test.zip)
(code `6aa315f`, published 2026-10-16; extension 1.2.31). Local analysis, 44 focused Flutter tests and
389 Python checks pass. Cling's real native clone/readback and IoStore verification pass; Windows validation,
compilation, frozen-engine startup and launcher/updater checks pass for the same commit. Downloaded
checksum/provenance and all 33 managed resources match source. Accepted Fina battle/cave and party
knockout assets remain byte-for-byte unchanged.

Crystal Fina's finished cave presentation is automatic. Add her normally (or enable Sephira's Visions), then open
**Edit → Acquisition**. To choose a specific cave, turn off **Hide for spoilers** and **Random**, select **Cave**
and choose your placement. Right-click the map to add a cave if needed. Build/install and restart Resonance;
use a save that has not acquired her to test the reward.

In any assigned cave, she uses her introductory floating pose inside the rotating transparent Sanctum crystal,
with the accepted size, glass and alignment. Acquisition grants her allocated vision, hides both her and the crystal,
and returns to that cave's stone room. The standalone **Crystal Fina cave** and **Crystal Fina Test** controls are removed.
Existing enabled switches migrate to an editable Acquisition assignment if she has no saved choice, then turn off.
Existing shop/cave choices, edits and disabled collection membership are preserved; removed profiles are not recreated.
See [scene placement and migration details](SCENE_PLACEMENT.md).

[Verified automatic Crystal Fina cave update / run 38978026068](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-38978026068/Sephira-Studio-Test.zip)
(code `2f9db41`, published 2026-10-16; extension 1.2.30). Update Studio, rebuild/install the mod and restart Resonance.
Windows validation and compilation pass for the same commit. Downloaded provenance/checksum and all
31 managed resources match source. Live confirmation of the new Acquisition route remains pending.

Party battle replacements now expose the native knockout motion names used by all eight party members,
including Lasswell's reverse stance. They use the selected sprite's fallen pose (or its base form's), preserving
its timing and offsets. Native death and revival remain in control. Cleome's four regular looks were checked
through native asset build/readback; the user confirmed the knockout fix looks good.
See [party knockout evidence](docs/PARTY_KNOCKOUT_INVESTIGATION.md).

[Verified party knockout update / run 38973264709](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-38973264709/Sephira-Studio-Test.zip)
(code `9275ab7`, published 2026-10-16; extension 1.2.29). Update Studio, rebuild/install the mod and restart Resonance.
Windows validation and compilation pass for the same commit; downloaded checksum/provenance and all
31 managed resources match source. Crystal Fina's accepted gameplay, crystal and preview bytes are unchanged.

Custom Crystal Fina uses the native introductory body and rotating private Sanctum glass in battle. The user
confirmed the body refraction and single resonance glow look right. Extension 1.2.28 slows her attack another
20% from the previous build, to 0.64× native speed. The body and linked hit/effect/sound clocks stay together;
Studio's preview shows the roughly **1.56-second** cast. Damage values, crystal settings, resonance and the
**1.25-second seated hold** are preserved. The user confirmed the pace and standalone Add behavior in game.

With Sephira's Visions off, Add can now move the saved Crystal Fina into Added Visions without enabling the
collection. It retains her identity, edited kit and cave/shop assignment; the preview shows her saved stats.
An initialized collection's subsequent toggles leave this independent entry included. Explicit collection restore
can still adopt her as before. An active Fina blocks a duplicate. Other FFBE units such as A2 keep their existing
multiple-entry support, with an active-only “in mod” badge and an explicit “Add another” button.

The rate controller still uses only the private Fina actor's linked action clocks, preserving native battle speed
as its base and restoring rates on recovery/cleanup. If no supported clock is available, it keeps native speed.
See [battle implementation evidence](docs/CRYSTAL_FINA_BATTLE.md).

Windows validation, compilation and frozen-engine startup pass. Downloaded checksum/provenance and all 31 managed
resources match source. The runtime uses the existing UE4SS loader independently of cycling; no new loader is
installed. Studio's updated preview (native-fina-10) remains a lighting approximation.
The [runtime diagnostics helper](scripts/reference/crystal-fina-battle/Collect%20Fina%20Runtime%20Diagnostics.cmd)
and [companion PowerShell file](scripts/reference/crystal-fina-battle/Collect%20Fina%20Runtime%20Diagnostics.ps1)
collect allowlisted runtime files/log under Downloads\FFR Mod without changing the game.
The [standalone full-game Fina diagnostics ZIP](scripts/reference/crystal-fina-battle/Crystal-Fina-Full-Game-Diagnostics.zip)
contains both files and instructions. It finds desktop Studio installations and full-game Steam libraries,
ignores saved demo paths, and includes the selected game's runtime install record. No Studio update is required.

[Verified standalone Crystal Fina / slower-attack update / run 38968721767](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-38968721767/Sephira-Studio-Test.zip)
(code `bde5f38`, published 2026-10-16; extension 1.2.28). Update Studio, rebuild/install the mod and restart Resonance.

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


## Steam Deck / SteamOS

### Local snapshots: build on PC, install on Deck (recommended)

Studio makes local snapshots the primary transfer route:

1. Set up your units on the PC and use **Build for Deck snapshot** (or build/install normally).
2. Open **Export / import snapshots → Export Deck snapshot**. Copy **Resonance-Mod-Snapshot.zip** to the Deck.
3. Extract the whole folder. Close Resonance and run `bash "Install snapshot.sh"` in Desktop Mode.
4. Repeat export/copy/import after PC changes. The Deck needs Python 3, with no Studio, engine build, repository
   or token. The installer detects Steam/SD-card libraries, verifies the native game build, backs up replaced files,
   removes stale owned runtime files and supplies a restore menu/shortcut.

Crystal Fina or cycling snapshots include the required runtime and document
`WINEDLLOVERRIDES="dwmapi=n,b" %command%` for the game's Steam launch options. Both computers need the same
native game build. **Export Studio backup** separately saves editable unit recipes and switches; the finished
Deck snapshot carries the actual compiled mod. See [the full guide](docs/LAUNCH_PREPARATION.md) for backup/import,
comparison and testing instructions. Real Deck/Proton playback remains to be tested.

### Optional: private GitHub publishing

The collapsed **Optional GitHub publishing** section publishes a finished mod to **your own private GitHub repository**.
The Deck downloads and installs that package without running Studio, downloading the engine or rebuilding assets.
Personal publishing starts **off**, with no destination or credentials shipped in the public fork. Ordinary builds
and installs never upload, even when personal publishing is enabled. Each person configures their own destination.

1. On your PC, open **Set up private sync**. Use its links to create a **private** repository in your GitHub account
   (for example, `Sephira-Deck-Mods`) and **initialize it with a README**. Create a fine-grained token for only that
   repository, granting **Contents: read and write**. Enter `owner/name` and the token, then **Verify & enable**.
   Studio rejects public repositories, the program fork and repositories owned by a different account.
2. Edit your setup as usual, then click **Build & publish to Deck**. Keep Studio open until it reports success.
   The package comes from that successful, verified build. It contains the three compiled mod files and the working
   character-cycling loader/scripts when cycling is enabled. Credentials, raw Studio settings, source sprite packs,
   game files and saves are excluded. Releases stay drafts until the uploaded checksum is verified.
3. On the Deck, download the small **Resonance-Deck-Sync.zip** from the latest tested release and extract it into
   **Downloads/FFR Mod/Installer**. In Desktop Mode, run:

   `bash "$HOME/Downloads/FFR Mod/Installer/Update my mod.sh"`

4. Enter the same private repository and a separate fine-grained token with **Contents: read**. Close Resonance.
   The installer detects Steam libraries, including SD cards; if multiple installs exist it asks which game folder
   to use. It downloads your most recently published complete package and creates an **Update my Resonance mod**
   desktop/menu shortcut. You can use that shortcut for later downloads while your PC is off.

PC tokens live in **Windows Credential Manager**, separate from the local destination/settings file. Deck tokens
can be remembered in **KWallet** or **Secret Service** if available; otherwise the installer prompts each time and
stores no token. Tokens never appear in a ZIP, public repository, command-line argument or saved settings file.
The setup dialog and Deck menu include a **Forget token** action. Nothing is uploaded on startup.

Deck helper, settings and backups are kept in **Downloads/FFR Mod/Deck Sync**. Only owned files are replaced;
unrelated mods are preserved. Turning cycling off in your PC build removes its previously synced runtime files.
The Deck menu can restore the files that existed before syncing, and an interrupted install is rolled back on the
next run. Changed files belonging to another runtime are preserved and reported rather than overwritten.
Checksums must match the game version used for the PC build. Update both games and rebuild after a game update.

When cycling is included, the installer prints the required Steam launch option:

`WINEDLLOVERRIDES="dwmapi=n,b" %command%`

Set it on **Resonance**, preserving any other launch options you use. The runtime comes from your working PC
installation; real UE4SS/Proton gameplay compatibility still needs a first Deck test. Package transfer does not
change saves. The connected GitHub integration cannot create personal repositories, so repository/token creation
is a one-time local setup through the dialog's GitHub links.

### Optional: run Studio itself on Deck

[Download the CI-checked launcher package / run 38457270486](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-38457270486/Sephira-Studio-Test.zip)
(code `8ce9507`, published 2026-10-13). Linux and Windows checks passed; the first real Deck test is pending.

Use the Windows test package through Proton. Its Windows command launcher does not run natively on SteamOS;
the package now includes **Start Studio Test.sh** and **Studio Deck Launcher.py** for Desktop Mode.

1. Switch to **Desktop Mode**. In Steam, enable the **Tools** library filter and install **Proton Experimental**.
2. Download the latest tested **Sephira-Studio-Test.zip** from this fork's test releases and extract its contents into
   **Downloads/Sephira-Studio-Test** (the scripts and **App** folder should be directly inside that folder).
3. Open **Konsole** and run:

   `bash "$HOME/Downloads/Sephira-Studio-Test/Start Studio Test.sh"`

The launcher creates a **Sephira Studio Test** desktop/menu shortcut. Use that shortcut afterward; it checks the
same validated test channel as Windows on each launch, verifies the package's SHA-256 and embedded identity,
and starts Studio through your installed Proton. An unavailable, interrupted or invalid update keeps the cached app.
Close Studio before reopening the shortcut for an update. Keep the installation folder in place.

Your units/settings/engine stay in **Studio Test Data/FFR Vision Studio**. Studio has its own **Proton** prefix beside
that folder; the launcher's updates do not replace either directory or touch the game's Proton prefix. Native Steam
and additional-library/SD-card Proton installations are detected. A saved selection is reused; an explicit
alternative can be chosen with `--proton "/path/to/Proton folder"`.

During first setup, if Studio does not find Resonance, use the game-folder path printed in Konsole. Windows sees
Linux files through drive **Z:**; the usual internal-storage path is
`Z:\home\deck\.local\share\Steam\steamapps\common\FINAL FANTASY RESONANCE DEMO`. SD-card paths start with
`Z:\run\media`. Close Resonance before installing mods. Studio's Windows process detection may not see a game
running in another Proton prefix.

The launcher uses the existing Windows app and engine. Live Steam Deck rendering, engine preparation and mod
installation need testing on the Deck; CI tests updater transactions, package layout and Proton launch arguments,
not actual Proton playback. If startup fails, collect **logs/proton-console.log** and **logs/steam-0.log** from the
installation folder. No sudo, SteamOS read-only changes, Proton download, or Steam shortcut-database edits are made.


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
[Verified Windows test package / run 37659730752](https://github.com/biscoBen/FFR-Vison-Studio/releases/tag/sephira-test-37659730752)
contains code `d35ceca` and passed all required Windows checks on 2026-10-07. It includes the reversible skill visual toggle.
Live battle balance and appearance still need in-game testing.
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

Enable **Shop practice battle**, install and restart, then talk to **Young Woman** in Mitra's item shop for an
in-game opponent dialog. Twelve encounters include the usual enemies, Cactuar and the ten enemy comparisons
listed above. **More opponents** cycles pages; **Cancel** returns without fighting. Each selection uses your current
party, the private native plains stage and guaranteed escape. The MR switch applies to every choice.

Enable **Survive at 1 HP for testing** before rebuilding/installing to test strong enemies and healing together.
Private battle-only native passives provide unlimited 1-HP reprieve and instant-death resistance on playable units.
Normal damage, maximum HP, healing, other passives and enemy stats/AI stay intact. It applies in all battles while
enabled; disable, reinstall and restart to remove it. Native table checks pass; lethal multi-hits, damage-over-time,
instant-death attacks and menu cancellation/repeat use still need live confirmation. Scripted battle endings are
not changed. The choices do not automatically heal or revive the party. Both testing switches default off.

Use a clean save, do not save with testing active, then disable the testing controls, reinstall and reload the clean save.
Disabling does not remove items or MR already acquired in the running session or a saved game. Table serialization
and automated checks are verified; acquisition timing and MR progression still need confirmation in a running game.

## Automatic animation repair

The main page has **Show unverified skills**, **Use our skill changes**, and **Repair native skill bindings / motions**
controls. All default off and are saved with the engine's mod settings. The modes are:

| Show unverified | Use our changes | Native repairs | Ability behavior |
| --- | --- | --- | --- |
| Off | Any | Any | Original picker filter; both library repair paths are inactive. |
| On | Off | Off | Expanded library with original game bindings; no automatic repairs or reviewed hides. |
| On | Off | On | Audited same-skill binding/aiming/motion repairs; original effects and timing. |
| On | On | Either | Full Studio skill repairs and 304 reviewed picker hides; includes native repairs. Ordinary summon commands remain available. |

With Show unverified on and Use our changes off, the native-repair checkbox selects a fourth mode: apply only audited
repairs to each skill's own timeline/binding/motion. It includes 22 audited demo entries. Bioblaster's copied effect aims at enemies, and Absolute Zero uses
separate caster routes with native player placement and the original enemy animation. Donor effects, generic fallback
timelines, Barrage trials and reviewed hides remain off. Both repair checkboxes remember their state while Show
unverified is off. If both are checked, the existing full-repair path applies, including its native repairs.
Borrowed Sephira preset visuals are controlled separately; turn that switch off for a clean native-only test.

Short descriptions, selected stats, full click descriptions, source/MR/awakening labels and all other Studio features
remain available in every mode. Existing language/Attack/Resonance and duplicate filters still apply. Equipped skill IDs,
original game rows and saved character configs are retained when their picker entries are hidden. The full-repair checkbox remembers
its value while the visibility switch is off; Show unverified and Use our changes must both be enabled for full repairs
and reviewed hides. The native-repair checkbox does not enable those features.
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
Turn the option off and rebuild/install to remove cycling; native Crystal Fina keeps its own battle runtime if present.
Removing her too, or restoring the original game, removes the owned runtime.
Previous-build restoration also restores the corresponding scripts. Live controller/scene behavior needs testing.

The original Resonance and its cinematic remain unchanged when replacing a model. Original visions can select another
existing game Resonance; creating a custom Resonance remains available for separately added units. Unsupported original
sprite layouts and incomplete placeholders are excluded. Engine integration runs automatically at startup and after
compatible updates, alongside Crystal Fina's transparency integration. No separate script is required.

## Full-game release checklist

The user's subsequent full-game install log confirms successful packing and table verification, including production
skill/sound tables, practice/grant/dialogue tables and the assigned Crystal Fina cave. Installation then stopped at the
legacy runtime's previous-folder guard. The **1.2.59** update scopes package/runtime ownership and backups per game,
preserving the demo records. It can copy an existing managed loader into a destination that lacks one, while preserving
unrelated mods and existing different loaders. The user's full-game installation and live gameplay still need a retry.

Full-game table support is available in the [verified package](https://github.com/biscoBen/FFR-Vison-Studio/releases/download/sephira-test-39825612562/Sephira-Studio-Test.zip), extension **1.2.58**. Studio resolves production composites and split
parent tables from the prepared official inventory, including custom skill donors and sound registration. It also
uses these physical paths for practice/grant/cave recipes and their verification. Existing full-game preparation
can be reused; the catalog refreshes its production routes when loaded. Saved roster edits and testing preferences
are retained. The optional FFBE Needles import defers to a native full-game route when one exists.
This is not a live compatibility pass: the supplied full-game reference lacks the actual map/menu table rows and
no full-game installation is running in this workspace. Keep the rollback backup and use the existing per-build
review/test sheet when installing. A native patcher/readback check preserves all original rows while adding 76
routes from 38 sampled bindings across the shared, production and composite skill tables.

This is the running project list for the full game's release, started **2026-10-04** from the `Sephira's-Update`
demo baseline `b15a4c0`. These are areas to review when the full game is available, not confirmed future bugs.
The October 22 full-game preparation finished **ready** after **2,618** tables, a quiet retry pass for **191** tables,
and **118** unread tables outside the setup's required set. It was not a confirmed hang. Starting preparation saves the selected game folder
globally before extraction; restarting is not required to change paths. Reference collection uses that saved path
and can run after preparation stops, even if preparation failed, but may encounter the same table-reader issue.
The [launch-preparation tools](docs/LAUNCH_PREPARATION.md) provide native comparisons, a reversible original-game
test preset, editable/compiled snapshots and a per-build test sheet; they do not mark the items below complete.

The returned **Resonance-Native-Reference.zip** collected with extension **1.2.57** successfully captures full-game
fingerprint `8ce7a0746d0cc1b2c9b97e44d186f8036212b156fc52b91571da94703168b5b4`.
Archive SHA-256: `4208fcecda16a7f88506d9fab2c353d0c96595bf7596386cd4f691ba47c14da1`.
The October 22 audit finds **106 scoped tables**, **58,035 inventory assets** and **7,087 timeline files**.
Of the 88 table names shared with the demo reference, 87 have identical schema/row metadata; the remaining shared
skill-asset table loses two Drain variants. Captured unit parameters, AI, skill/passive definitions, vision items,
awakening/MR and synchro mastery data match the demo. This is an offline comparison, not a full-game install or play pass.

The full game replaces the demo skill composite with **CDT_SkillAsset_Prod**: its 1,355 rows combine 428 generic
rows with 942 production rows, including 15 identical shared rows. Auditing that actual composite with definition
pointers and character links finds candidate routes for **1,074 of 1,167 skill definitions**, compared with **286**
in the demo: **788** definitions gain routes, none lose all routes, and **798** have changed distinct route sets.
These are candidate routes, not verified visual counts. The **1.2.57** collection omits production-only skill tables
from its skill-route summary; its **286 changed-skills** count is incomplete. Version **1.2.58** includes production
routes and compares distinct bindings, reproducing **798** changed skill records from the original captured rows.

All **21 named missing-visual test cases** now have native candidate routes with both visual and sound timeline
packages present, covering **22 candidate skill IDs** and **36 distinct routing rows**. Preserve the unresolved Waterga
variant and the earlier observations separately from this new asset evidence:

| Original comparison source | Newly available native test cases / exact skill IDs |
| --- | --- |
| Cactuar / Gigantuar | 1,000 Needles `500270`; 10,000 Needles `505110` |
| Watcher / Ganymede | Megavolt `500180`; Atomic Ray `500380` |
| Malbodoom / Malboro Marquis | Bad Breath `505020`; Pollen `500690`; Flatten `500190` |
| Sheratan | Alluring Pollen `503770`; Octo-Strike `501070`; Branch Spear `503780`; Stonega `255170`; Aeroga `250190` |
| Alpherg | Bubble Breath `501680`; Reflectga `503800`; Waterga `250150` or `255110`; Flare `250330` |
| Bomb / Wood Eyes / White Peak | Self-Destruct `500720`; Constrict `500590`; White Wind `500810` |
| Earlier imported-vision tests only | Blighted Gloom `407050`; Carmine Inferno `505340` |

The audit identified `_Demo` composite and generic-only donor assumptions addressed by **1.2.58**. The returned ZIP's
scopes omit map, shop, stage, dialogue and UI table rows, so it cannot establish cave, practice-menu or acquisition
compatibility. Future collection includes those feature tables. Source assets remain local, no native visuals are
marked verified by this audit, and the pre-upstream rollback checkpoint remains intact.

Keep user cave placements, character configs, concise descriptions and source labels. Add new demo-dependent
features here as work continues. Mark an item complete only with the tested game version, Studio commit and evidence;
retain unresolved cases and record the date/source fingerprints when refreshing catalogs.

- [ ] **Practice testing controls.** Recheck native unlimited reprieve/instant-death IDs, playable-unit attachment
  and the choice/branch/stage tables. Verify lethal multi-hits and damage-over-time at 1 HP, healing, cancellation
  and repeated fights. Update demo-only opponents and remove superseded animation comparisons.
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
  tracks an applied visual mapping, rather than observation of every skill in a running game. Recollect the 23 audited
  native player routes and caster tracks before retaining their bridges; refresh the exact source fingerprints
  and both aiming-point guards. Recheck the two retained enemy routes and shared bindings. Reassess the optional
  native `atk` motion alias against full-game requests without substituting other artwork or schedules. Refresh the five exact-definition
  **Verified; demo test** records after full-game live testing, including group skills and party replacements;
  see [monster compatibility evidence](docs/MONSTER_ANIMATION_COMPATIBILITY.md).
  Preserve the independent native-repair mode and audit all returned native battle tracks before expanding its rules.
  Revisit the [secondary-route findings](docs/native-skill-routing-findings.json), including normal-attack/character
  dispatch, the original twelve unresolved blank test cases and the three additional reports. Compare original
  enemy/runtime playback before inventing bindings; do not equate AI assignments with tested visuals. Recheck the
  optional observer's reflected fields against the new build and remove it after diagnosis.
  Re-audit the [confirmed runtime fallbacks](#confirmed-runtime-fallbacks): 1,000 Needles (500270) and Atomic Ray
  (500380) selected the native damage/reaction-only 900000 placeholder on imported visions in the demo. Find their
  own full-release presentation assets/routes and retest them, rather than treating a restored caster alias as
  recovery of their original visuals. The other six blank follow-up entries still lack this runtime attribution.
  Recheck the optional FFBE 1,000 Needles import against the full game's own effect route before retaining it.
  The Memorial source and isolated prototype are documented above; never enable the import automatically or
  treat its live appearance as verified from offline conversion alone.
  Retest 1,000 Needles on the original enemy too: the 2026-10-17 visual test reports no visible animation from
  the tested Cactuar, without a trace. Preserve this observation separately from proof of a missing asset or route.
- [ ] **World-map images, coordinates and cave placements.** Refresh native map captures, projection and landmarks.
  Validate saved positions before migration; preserve the user's cave locations and leave unknown vendor pins unavailable.
- [ ] **Default visions, party members and portraits.** Refresh identities, stats, abilities, MR rewards, Resonances,
  portraits and acquisition rules. Review new characters/placeholders and preserve original identities when replacing models.
  Recheck the native face/timeline/ability icon masks and frames used for imported portraits.
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
- [ ] **FFBE source library.** Recheck source delivery updates, missing dependencies, source IDs, conditional/audio routing, particle/camera fidelity and cinematic regional variants before assigning any imported visuals. The archival library currently assigns nothing. Native missing-animation repair is on hold until the full-game retest.
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
  For **Crystal Fina's assigned-cave presentation**, revalidate `M_Env_Glass_Single_Layer_Water`, its `MSM_SingleLayerWater` transmission model and scalar names,
  the reserved RefractionDepthBias override, cooked material-instance cached-data format, introductory pose/billboard transforms,
  and copied static visibility IDs/streaming metadata. Retest assignment to original, custom and shared caves with both
  retired switches off, including reward IDs and ownership visibility. Recheck the private casing sequence, Tick clock, explicit
  transform channels, unique cooked object identities, component soft-path binding and autoplay/input flags.
  Preserve the native crystal render data/material section and verify the mesh/bulk copies. The previous tip-only
  material partition produced dark end caps; do not revive it without a new visual test. Preserve the approved glass/rotation
  and retryable legacy-switch migration; keep the standalone diagnostic controls retired. Recheck shader serialization
  before carrying demo assets into another engine version.
- [ ] **Battle and overworld replacements.** Recheck native asset tables, sprite layouts, portraits, directions,
  restoration and special scenes. FFBE field sprites use separate source data; refresh that catalog when its source
  changes or additional suitable sheets become available. Recheck all eight native party knockout names (`death`, plus Lasswell's
  `reverse_death`/`reverse_dying`) against updated SS6 projects. Retest replacement knockout, held fallen poses,
  base-form borrowing and revival; a source look with no fallen artwork still needs a separate fallback decision.
  For native Crystal Fina battle presentation, revalidate the SS6 model names/parents, part sockets, UUPerPixel versus
  component-scale conversion, direct movable mesh attachment and native mesh/material/bulk data. Recheck the
  SpriteStudio playing-name out parameters, Play/SetPlayRate and Engine/Niagara component functions under UE4SS.
  Preserve native Niagara parameter names/offsets, renderer bindings and VM through native package cloning;
  JSON readback omits these fields. Verify byte-identical export data. Use SS6-supported Imgfliph and check its bool cache.
  Treat output-table field names as game reflection data; identify the private animation pack by value rather than
  assuming upstream parameter spelling. Normalize case as Unreal FName does; retest native `Idle` recovery and
  temporarily unavailable outputs without tearing down the casing.
  Preserve reflected bHidden access rather than calling the inline C++ IsHidden helper. Retest full-cast recovery,
  no idle glow, direct parameter-driven aura fades, the frame-134 fall and frame-258 reformation in real battles.
  Verify owned runtime staging/restoration and Deck transfer with cycling on and off. Keep the authorized seated
  fallback, native source bytes and saved kits. Refresh the labeled Studio preview and cache revision separately.
- [ ] **Field-character cycling and controller input.** Verify UE4SS compatibility, reflected function signatures,
  active-party lookup and input bindings. Check battle/cutscene/dialog guards and preservation of party order/save identity.
- [ ] **Engine, extraction and cooked assets.** Check executable/Pak paths, engine version, `Mappings.usmap`, table
  schemas, SpriteStudio serialization and IoStore roundtrips. Separate or invalidate prepared demo data. Review our engine
  extensions against upstream updates; change pinned checksums only for verified replacements. Preserve engine hosting.
- [ ] **Testing features.** Resolve the reported intermittent Mitra fatal error using Unreal/UE4SS crash logs;
  it occurs during walking and repeat practice interactions, separately from the fixed name-index error. Recheck the Young Woman binding, picker paging/cancellation, packed script names,
  practice enemies, backdrop and return; original-vision grants and toggle restoration. Test 1-HP survival with
  damage, status effects and healing. Recompute the one-battle MR reward within actual numeric bounds: 11,430 AP
  comes from the current demo's rank costs. Test with clean saves.
- [ ] **Custom IDs, capacity and configs.** Check reserved skill/unit/map/event/asset ranges against newly occupied IDs.
  Revalidate the 64-added-unit limit against engine/table constraints. Preserve old configs, separate appearance choices
  and selected cave snapshots.
- [ ] **Steam Deck / Proton launcher.** Recheck stock/GE Proton selection, first engine setup, native game-folder paths,
  Steam libraries/SD cards, update fallback, process detection across prefixes and mod installation. Test real Deck rendering
  and controller use; preserve the separate Studio data and Proton prefix. Confirm full-game Pak paths and runtime-loader
  compatibility on SteamOS independently of Windows CI.
- [ ] **Local PC-to-Deck snapshots and optional private sync.** Recheck local ZIP export/import, unchanged-game
  fingerprint, settings freshness, runtime-on → runtime-off cleanup and restore with real SteamOS/Proton.
  The normal transfer needs no repository/token or Deck-side build. Keep editable backups separate from compiled mod snapshots.
  **Optional GitHub path:** Recheck full-game Pak filenames and version fingerprint, private GitHub release
  APIs and digests, local credential managers, Steam library detection, owned backup/recovery and runtime dependencies.
  Test UE4SS under the game's Proton with the native `dwmapi` override. Keep destinations/credentials local and
  personal publishing opt-in; never bundle personal packages/configs into the public program release.
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
