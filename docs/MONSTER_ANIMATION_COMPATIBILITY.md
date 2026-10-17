# Monster skill animation compatibility

Evidence: Resonance demo, user tests and `Monster-Animation-Reference-20261016-161638-f6ee98-001.zip`,
collected 2026-10-16. The recipient vision was not recorded. This report distinguishes live observations from
asset inspection; serialization alone does not establish that an animation looks right in game.

| Skill | ID | User's live result |
| --- | --- | --- |
| Whip | 500120 | Visible animation |
| Tentacle | 500580 | Visible animation |
| Sonic Boom | 500440 | Visible animation |
| Bite | 500140 | Visible animation |
| Incisors | 500510 | Visible animation |
| Cling | 500910 | Original: damage without animation. Repaired version: user confirmed it works and looks better. |

The five successful entries are labeled **Verified; demo test** in Studio. The managed evidence file checks
their IDs, names, targeting, type, hit count and native sequence bindings before applying the label. A later
catalog change clears that evidence rather than approving a repurposed skill. Combat duplicate/hiding rules
retain their original verification predicate.

## Why Cling differs

The successful skills have both friendly-caster (`味方`, suffix 1) and enemy-caster (`敵`, suffix 2) asset
bindings. Cling has only **500912**, with no **500911** player route. These suffixes describe the caster side;
they do not mean single-target and multitarget. Native Fire and Curaga rows confirm the distinction.

Cling's native Cut timeline also disables its sole caster-motion track, `MovieSceneEventTrack_18`.
That track requests enemy `atk` at tick 0 and `idle` at tick 13600. Imported vision packs expose
`attack_A` instead of `atk`. Cling's effect timeline already uses `EffectSpawnNiagaraAtTarget`,
`Effect_SpawnTarget_bAllTarget = true`, and `NS_EF_SKL500240_Center` at the center socket. Its original
group target definition and hit event are present. Multitarget damage itself does not require replacement.

With **Show unverified skills** and either **Use our skill changes** or **Repair native skill bindings / motions** enabled, selected original Cling receives
a private **500911** copy of its own Master/Cut/Effect/Sound packages. Both native lookup tables gain the
ally route; every original row remains intact. Only the audited caster track is enabled, and `atk` becomes
`attack_A`. Hit timing, original all-target particles, sound and combat values are retained. Explicit custom
presentations take precedence. A future native 500911 binding wins; changed definitions or unexpected
caster tracks stop preparation with a clear error rather than enabling unknown events.

Generic audited same-name timeline reuse also now creates a player route for group skills. It prefers an
ally donor regardless of target count, then a shared or audited enemy donor. The receiving skill keeps its
own targeting and mechanics. Enemy-only timelines requiring specialized actors or unsupported motions still
need individual investigation; the Cling exception is not applied blindly to other monster skills.

The native probe used the actual engine clone functions, serializer and supplied mapping. Readback confirms
the new route in both tables, unchanged original rows, enabled supported caster motion, unchanged Master
hit constants, and preserved all-target Niagara reference. IoStore packing and verification pass.
The user confirmed the repaired Cling presentation works. The expanded batch is described below.

## Isolated native-repair mode

For testing, turn Show unverified skills on, Repair native skill bindings / motions on, and Use our skill changes off.
The isolated build route never creates the donor resolver, fallback schedules, Barrage trials or reviewed hides.
It includes the 22 audited native routes below and leaves other original bindings intact. An old three-field settings file
defaults the new boolean off without rewriting the file. Both repair flags are remembered while visibility is off;
the existing full-repair path wins when both are enabled. Explicit custom presentations and inherited native kits
retain their precedence. No new skills are marked verified merely by enabling this mode.

Sephira preset borrowed visuals are a separate saved setting: switch those off as well for a clean test.
Neither setting erases saved kits or user-authored presentation choices. The native-only build report records
`mode: native_repairs` and which selected skills actually received a native bridge.

The full collector in `scripts/reference/native-skill-animations/` reads all `Sequencer/Battle/` packages,
both lookup tables, skill definitions/effects, reaction/load-unit/point-target tables, the mapping and asset inventory.
It copies only the four allowlisted ability mode fields, writes under Downloads/FFR Mod, and splits ordinary ZIPs
at 22 MiB before compression. It installs no loader and changes neither the game nor Studio files. Returning all
parts enables inspection of disabled caster tracks and monster-specific motions, including skills with existing
bindings; an enemy-only binding by itself is only a candidate, not proof of a player-compatible repair.

## Full native reference audit

The five-part `Native-Skill-Animation-Reference-20261016-171038-cabc96` collection contains 1,407 assets.
All 1,370 `SEQ_Battle_` packages were decoded (view and event dump), along with seven routing/definition tables:
2,747 native decode operations, with no failures. The raw catalog contains 1,167 entries, including internal and
hidden variants. 277 have direct bindings: 256 have a shared/player route and 21 only have an enemy route.
All directly bound packages are present. The remaining 890 have no direct binding; this does not establish
whether they are broken because some skills use other runtime routing. See [audit counts](native-skill-audit-summary.json).

Native-only mode covers all 21 enemy-only entries, plus the explicit Absolute Zero pointer described below. Each private route clones that skill's own native source;
no other skill's visual is substituted. Group targeting, particles, audio and hit timing remain original.

| Native skill entry | ID | Additional change to own timeline |
| --- | --- | --- |
| Cling | 500910 | Enable complete caster track; atk → attack_A; live-confirmed |
| Thwack | 505040 | Enable complete caster track; exact atk → attack_A |
| Throat Strike | 500250 | Enable complete caster track; exact atk → attack_A |
| Needle | 500260 | Enable complete caster track; exact atk → attack_A |
| Steal | 500530 | Enable complete caster track; exact atk → attack_A |
| Bioblaster | 500970 | Player binding; look-at point 2 → 18 (pending live confirmation) |
| Thunder Beam | 501000 | Enable complete caster track; exact atk → attack_A |
| Libra | 506090 | Enable complete caster track; exact atk → attack_A |
| Gimme an ether! | 580060 | Binding only |
| Steal | 580110 | Enable complete caster track; exact atk → attack_A |
| Flee | 580120 | Exact atk → attack_A |
| Cure | 245000 | Binding only |
| Fire | 255000 | Binding only |
| Blizzard | 255030 | Binding only |
| Thunder | 255060 | Binding only |
| Water | 255090 | Binding only |
| Aero | 255120 | Binding only |
| Stone | 255150 | Binding only |
| Bio | 255190 | Enable complete caster track |
| Banish | 245290 | Binding only |
| Banishra | 245300 | Binding only |

The additional routes require live testing. Import conversion already supplies the native weapon/magic attachment
points used by these effects. Thwack has an extra disabled attack-only template; only its complete attack/idle
track is enabled. Existing routes with `atk` events are recorded separately as investigation candidates, without
changing their original bindings. Disabled native tracks alone are not enough evidence to enable every track.

The managed policy fingerprints the original definition, each lookup binding and every source package byte.
A changed/missing source is reported as `native_repair_unresolved` and retained, while a future native player route
or an explicit custom presentation takes precedence. Only exact audited functions/tracks are edited on private copies.
Native build/readback confirms all 21 new rows in both tables with every original row unchanged, identical
hit/effect/audio event constants, and only approved motion names/track flags changed. IoStore verification passes.
No newly repaired entry is automatically labeled verified. Re-audit these rules against full-release assets.

## Native-only test batch on Agrias and Alaya Rundall

User reports from 2026-10-16/17: two added test visions, Agrias and Alaya Rundall, with no party replacements.
Show unverified and native repairs are on; Use our skill changes and borrowed Sephira visuals are off.
For usable skills, damage/status effects resolve. Most entries below have no visible presentation.
These are user observations plus static reference findings, not new verified-animation labels.

| Skill | Catalog ID | Live observation / test limit |
| --- | --- | --- |
| 1,000 Needles | 500270 | No visible animation |
| 10,000 Needles | 505110 | No visible animation |
| Absolute Zero | 500230 | Visible ice effect over the party |
| Absolving Hailstorm | 402050 / 505840 | Not tested: the selected version costs too much MP; exact version not collected |
| Abyss Graviton | 408040 | Not tested: Limit Burst restriction |
| Alluring Pollen | 503770 | No visible animation |
| Aqua Blast | 405050 | No visible animation |
| Aqua Breath | 500800 | Follow-up same-computer test: correctly aimed; user corrected the initial report |
| Aquatic Pulse | 405130 | No visible animation |
| Aquatic Synergy | 414410 | No visible animation |
| Array: Brilliance | 503630 | No visible animation |
| Array: Light of Destruction | 503620 | No visible animation |
| Array: Shock Shell | 503610 | No visible animation |
| Assassin's Needle | 501180 | No visible animation |
| Atomic Ray | 500380 | No visible animation |
| Bad Breath | 505020 | No visible animation |
| Bioblaster | 500970 | Reported separately: visible effect points toward the party |

IDs are matched by catalog names. The next collection includes installed skill definitions/grants to verify the
exact variants used. The only member of this batch covered by the initial 21-route repair was Bioblaster.
The repair switch does not promise an animation for every unverified entry.

Confirmed static findings from the complete native reference:

- Absolute Zero has no direct route, but its `playSequencerId` explicitly selects **225042**, whose asset is
  `Magic/225030/225032/SEQ_Battle_225032_Master`. Its effect spawns at fixed target **2**, the party-side point.
  The friendly counterpart 225041 uses target **18**, the enemy-side point. A repair must account for this
  explicit pointer and preserve enemy use of the skill; adding 500231 alone is insufficient.
- Bioblaster's native 500972 effect uses `NS_EF_SKL500970_Gas_001_Weapon_AtoB` and fixed look-at target **2**.
  The current private 500971 copy preserves that constant. This explains a concrete party-side aiming problem
  in the copied presentation; the correction still needs a live check of its placement/offset.
- Aqua Breath already has a native friendly route **500801** with look-at target **18**, while 500802 uses **2**.
  The user's follow-up test confirmed it already aims correctly. Its native player route remains unchanged.
- The twelve blank entries have no direct native sequence binding and no explicit `playSequencerId`.
  No same-ID effect folders appear in the supplied asset index. This does **not** prove the effects are absent:
  aliases or character-specific runtime paths may supply them. It does explain why a binding-only audit of the
  21 existing enemy routes did not restore these entries. Native-only mode deliberately leaves borrowed
  effects and generic fallback schedules off.

The focused read-only helper in [scripts/reference/skill-effects](../scripts/reference/skill-effects/) collects
matching native effect systems/meshes for the reported batch, fresh native tables, installed Studio lookup tables
and battle timelines, allowlisted mode flags/skill grants, and the latest build repair report. Output is split into
ordinary ZIPs under Downloads/FFR Mod. It does not install a runtime loader, modify game/Studio files or include
save files, sync settings, credentials, unrelated mods, or entire mod containers. This is a static collection and
cannot establish which sequence actually played live; a runtime trace may still be needed after asset inspection.

The returned `Skill-Effect-Reference-20261016-192530-573511` collection contains 63 native assets,
five installed assets and all required global/mapping data. All 80 table/view/event decode operations pass.
The 15 overlapping native reference files match the earlier collection byte-for-byte. Aqua Breath and
Bioblaster use local-space Niagara emitters; their particle references are intact. The report from this computer
is `original_game`, and its installed pack has no native Bioblaster player route. The user confirmed switching
computers, so this cannot establish which route the original Agrias/Alaya battle used.

Version 1.2.34 prepares two native presentation corrections, without borrowing other skills' visuals:

- Bioblaster's private 500971 timeline changes only its Niagara look-at target from 2 (party) to 18 (enemy).
- Absolute Zero keeps its original 500230 skill definition except `playSequencerId = -1`, allowing normal
  caster-side routing. New 500231 points at a private copy of the original 225032 sequence, with effect point
  18 and native player placement offsets from its existing 225031 counterpart. New 500232 points at the
  exact original 225032 package/sound, preserving enemy use. Every original lookup row remains intact.
- Source definition/binding/package fingerprints remain mandatory. Both point-table entries are also checked;
  changed points skip the repair. Future player/enemy bindings or explicit custom presentation fields win.
  Verification derives only the intended presentation-pointer change from those inputs and requires the
  successful bridge record. Skipped repairs cannot authorize it; changing MP/damage or other fields still fails.
- All 22 player copies (88 packages) and 23 added routes per lookup table pass actual serialization/readback.
  Every original skill field except the one presentation pointer is unchanged, along with every original binding;
  the private copies change only approved motion flags/names and the two effect placements. IoStore verifies.
  These checks do not establish in-game appearance; both direction corrections still need live confirmation.

The follow-up `Skill-Effect-Reference-20261016-194051-70134c` confirms native-only flags on and a native-repair
report. Its installed Bioblaster player route 500971 still has look-at point 2, and Absolute Zero still has pointer
225042, confirming the targets of this patch. The user corrected the Aqua Breath report: it already aims correctly.
Aqua Breath is intentionally unchanged. The fresh native tables are byte-identical to the prior reference;
the prior matching mapping supports decoding the installed tables/timeline in uploaded part 001. The mod-only
extraction view may show `UnknownExport` for native particle imports absent from that view; this alone is not
evidence of a missing particle in game. Native source references and their fingerprints remain authoritative. Native-only
reports now label skills with no direct binding or explicit pointer `no_direct_native_route`, without calling
all such skills broken or substituting another visual. The twelve blank skills still need further evidence.
The collector now assigns JSON before enumerating it, handling PowerShell 5.1 empty/single/multiple rosters,
and records engine/game paths. Its readback smoke checks also cover copy fallback, temporary cleanup and
multipart ZIP integrity.

The diagnostic helper itself applies no aiming or blank-skill repairs. Keep the current test modes
unchanged when collecting. The helper's fixture checks cover quoted paths, exact installed-pack scope, flag/grant
allowlists, source immutability, missing installed packs, partial failures and output guards. Real retoc/PowerShell
collection of native tables and private installed timelines is also checked. Windows PowerShell 5.1 on the user's
PC remains the final environment check; local execution uses PowerShell 7 with 5.1-compatible syntax.

## Secondary routing investigation and confirmed facing retest

The user confirmed the version 1.2.34 Absolute Zero and Bioblaster corrections now aim correctly.
Aqua Breath was already correct and remains unchanged. Cling's repaired native route was previously
confirmed working. These observations apply to the tested native-repair mode; they do not verify every
skill or the original unrepaired routes.

The follow-up inventory audit found secondary assets outside the first collection's seven tables:

- `Datatable/Skill/Other/DT_SkillLinkSequencerData`, `DT_SkillGeneralData` and `DT_SkillTargetData`.
- `Datatable/Battle/Misc/DT_BtlSkillReactionParamDef`, unit asset/command/AI tables and demo table lists.
- `Sequencer/Skill/BP/BP_BtlSequenceEvent` and `BP_BtlLevelSequenceDirector`, plus native battle AI callers.

The matching mapping describes `BTL_LINK_SEQUENCER_PLAY_SKILL` with `SkillId` and separate sequence IDs
for Rain, Lasswell, Fina, Dark Fina, Lid, Nichol, Jake and Sakura. That is evidence of another supported link
structure, not evidence that it supplies the twelve blank skills: its native table contents have not yet been
collected. `Sequencer/Skill/` contains two event blueprints, rather than another set of attack timelines.
A skill definition can also describe content that the demo never uses. Presence in the catalog alone does
not prove a complete effect or original runtime caller is included.

The standalone [skill-routing collector](../scripts/reference/skill-routing/) gathers these missing scopes
alongside the complete native battle timelines and visual libraries: all skill/battle/unit/encounter/asset tables,
demo table lists, battle AI/event callers, full effect assets and shared materials/textures, battle character
animation projects, camera/postprocess support, movie/cue metadata and relevant engine/SpriteStudio/Niagara
support. The current inventory predicts **7,130 packages**, including every one of the **2,048 game-package
references** found in the earlier sequence views. See [scope counts and candidate evidence](native-skill-routing-scope.json).
All native asset bytes, including extracted bulk data, are retained. Map levels, shader libraries and full
game/video/audio containers are outside the requested scope.

The report compares extraction against the inventory and required key files, preserving partial collections.
It records selected source paths and native container header hashes; it reads the saved game path but copies
no config, saved kits, saves, executable, runtime logs or installed mod containers. Outputs go to Downloads/FFR Mod.
No loader, in-game test or new Studio build is required. Ordinary ZIPs stay below 22 MiB before compression.
Individual larger files are streamed into numbered chunks without a second on-disk copy, with original
length/SHA256 and ordered parts recorded in `split-files.json`. After all ZIPs have been extracted together,
maintainers run `python3 scripts/restore_reference_chunks.py <collection-folder>` before decoding.
The restoration tool checks lengths/hashes and rejects missing chunks, conflicting files and escaping paths.

Fixture checks run the actual PowerShell collector with an extractor driven by all 7,130 matching inventory
entries, including multiple 36 MiB assets whose restored bytes match exactly. Tests also cover partial/missing
assets, inventory failure, no assets, missing mapping, quoted paths, config-based discovery, source immutability,
private-data exclusion, default output, output guards and ordinary ZIP integrity. Real retoc/PowerShell collection
of 91 native-derived packages passes, with missing native scopes correctly reported as partial. Six focused
Python restoration tests pass. Actual Windows PowerShell 5.1 execution and newly requested native table contents
still require the user's returned collection.

Further static leads support tracing existing assets before authoring replacements. Twenty-three unbound skill
definitions have same-ID effect folders referenced by existing sequence packages. Twelve have matching-number
master timelines on disk, including Bladeblitz, Water/Watera/Waterga Blade, Scorch, Cyclone and six magic entries.
These are candidates, not recovered bindings: the native lookups already reuse packages under different IDs,
and package imports can belong to disabled/template tracks. Current skill ownership and active playback must
be established from the secondary tables/callers and keyed events, rather than from file numbers alone.

The next audit will join skill IDs through those tables and callers, follow sequence imports to their native
effects, and compare original player/enemy placement and supported caster motions. Only when no usable
native timeline can be recovered should a private timeline be authored around the skill's own available
effects. Finding only combat data cannot reconstruct missing original art. Borrowed visuals remain a separate
optional mode.

The active-event scan of the already collected battle timelines also found additional repair candidates:
Thwack, Bio and Banishra still use the fixed party-side effect point in their copied player timelines;
El Niño's shared route selects an enemy Aqua Breath timeline. Escape has an active friendly `atk` request.
Seal of Conviction combines party-side placement with specialized monster motions and game-speed events,
so changing its target point alone is insufficient. Friendly Light Veil intentionally uses the party point.
These are static findings awaiting implementation and live tests, not new repairs in this helper.
The aiming audit must consider the selected effect function and target relation; a global rotation or a global
replacement of positive-Y points would also change correctly placed friendly effects.

## Returned comprehensive collection and extension 1.2.35

All **89** `Skill-Routing-Reference-20261016-213210-7ca510` ZIP parts pass extraction/CRC checks.
The four split large files restore with their original lengths and SHA256. All **7,130** expected packages
are present. The 17 reported missing names are Windows console decoding artifacts: CP437-decoded UTF-8
turned degree signs and a zero-width space into other characters. Each original Unicode path is present.
The collector now selects UTF-8 before invoking retoc. This collection does not need to be repeated.
All 2,819 overlapping files from the earlier full native reference, plus the mapping, match byte-for-byte.

Decode/readback succeeds for **233 tables, two sequence-event blueprints, 258 AI blueprints and ten
original monster projects**. The sequence-event blueprints contain no additional attack schedules.
`DT_SkillLinkSequencerData` has seven rows: five reference skill IDs absent from current skill definitions;
the two current rows are Physical Counter and Magic Counter, selecting party-specific attack sequences.
The twelve blank tested skills have no entry in this table. The ordinary-skill audit distinguishes 218
directly bound entries, 21 with explicit presentation pointers, two with character links, thirteen with
normal-attack dispatch, and 771 with none of those direct/secondary routes. Pointer presence alone does
not establish that its referenced binding exists. These counts do not classify every unbound skill as broken.
See the [returned-reference evidence](native-skill-routing-findings.json).

The AI tables do assign 1,000 Needles, 10,000 Needles, Atomic Ray, Bad Breath and several other blank
skills to native enemies. Some assignments have zero random weight or belong to later encounters, so
assignment alone does not establish demo availability or live playback. Inspected AI blueprints schedule
skills and targets; they expose no separate animation/sequence/effect dispatch for this batch. Ten original
enemy projects mainly contain `Setup`, `idle` and `atk`, rather than an independent named animation for
each assigned skill. This static inspection cannot exclude behavior implemented in compiled native code.

Every matching-number master candidate is already bound to a different current skill ID. For example,
the 400311/400312 files serve Grand Slash; 500241/500242 serve Poison Gas; and 220041/220042 serve Fire.
They are not automatically reclaimed for Bladeblitz, Scorch or Inferno Sphere. Nor do same-ID effect folders
prove current ownership when packages are reused. No recovered secondary link currently resolves the
twelve blank test entries, and no new donor visuals or generic hit schedules are enabled for them.

The supported repairs added in extension 1.2.35 are:

- Thwack, Bio and Banishra: change only the audited private player effect's fixed target point 2 to 18.
  Their native particles, event keys, sound and combat definitions stay intact.
- El Niño: its shared binding 501010 selects native 500802. Add private player 501011 with enemy-side
  look-at point 18 and native friendly look-at height 200, and enable only its complete `atk`/`idle` caster
  track with the supported `attack_A` name. New enemy 501012 retains the original shared package/sound.
  Original shared/native rows are preserved. Future explicit routes, custom presentations, changed source
  bytes/definitions/bindings/target points still prevent the repair.
- Native `atk` compatibility: generated imported battle models expose a deep copy of their own `attack_A`
  clip under `atk` when Show unverified and either repair flag are on. Escape's existing friendly timeline
  explicitly requests this name. This is motion compatibility only; it creates no skill route or substitute
  effect, and does not claim that the twelve blank skills are fixed. Existing aliases win. Atlas/cell/menu
  data and existing animations are preserved. Crystal Fina maps the optional name to her accepted shot and
  mirroring without changing any of her existing clips, glow, crystal, impact timing or seated hold.

All **23** private player routes (92 packages), plus both retained enemy routes and **25** new bindings
per lookup table, pass actual native serialization/readback. Every original binding remains identical;
every skill field remains original except the previously accepted Absolute Zero presentation pointer.
Only the exact audited events/tracks change, including intact Niagara import references. IoStore packing
and verification pass. These asset checks do not establish in-game appearance; the new changes need live tests.

## Imported vision icon framing

Face, timeline and ability icons now use the game's existing Cloud frame and supplied portrait mask.
Only the portrait area is replaced with the selected FFBE artwork; native frame pixels remain unchanged.
The blue custom backing, drawn gem and FFBE rarity badge are omitted. Saved portrait scale/position
controls still apply. Both the build converter and advanced preview use the same renderer; rebuild/install
the mod to refresh existing in-game icons.

## Full-release follow-up

Recollect native bindings, caster tracks and target-point coordinates before carrying any of these 22 repairs to the full game. Re-audit Absolute Zero's explicit pointer and enemy-route preservation. Retest all six
skills on imported visions, including multiple targets and a party replacement. Refresh the five live-test
records only after confirmation on that build. Recheck the native icon masks/templates and rendering.
The read-only collector lives in `scripts/reference/monster-animations/`; output goes to Downloads/FFR Mod.
