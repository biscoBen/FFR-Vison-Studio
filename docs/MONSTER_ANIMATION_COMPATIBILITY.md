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
It includes the 21 audited native routes below and leaves other original bindings intact. An old three-field settings file
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

Native-only mode now covers all 21 enemy-only entries. Each private route clones that skill's own native source;
no other skill's visual is substituted. Group targeting, particles, audio and hit timing remain original.

| Native skill entry | ID | Additional change to own timeline |
| --- | --- | --- |
| Cling | 500910 | Enable complete caster track; atk → attack_A; live-confirmed |
| Thwack | 505040 | Enable complete caster track; exact atk → attack_A |
| Throat Strike | 500250 | Enable complete caster track; exact atk → attack_A |
| Needle | 500260 | Enable complete caster track; exact atk → attack_A |
| Steal | 500530 | Enable complete caster track; exact atk → attack_A |
| Bioblaster | 500970 | Binding only |
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

The 20 new routes require live testing. Import conversion already supplies the native weapon/magic attachment
points used by these effects. Thwack has an extra disabled attack-only template; only its complete attack/idle
track is enabled. Existing routes with `atk` events are recorded separately as investigation candidates, without
changing their original bindings. Disabled native tracks alone are not enough evidence to enable every track.

The managed policy fingerprints the original definition, each lookup binding and every source package byte.
A changed/missing source is reported as `native_repair_unresolved` and retained, while a future native player route
or an explicit custom presentation takes precedence. Only exact audited functions/tracks are edited on private copies.
Native build/readback confirms all 21 new rows in both tables with every original row unchanged, identical
hit/effect/audio event constants, and only approved motion names/track flags changed. IoStore verification passes.
No newly repaired entry is automatically labeled verified. Re-audit these rules against full-release assets.

## Imported vision icon framing

Face, timeline and ability icons now use the game's existing Cloud frame and supplied portrait mask.
Only the portrait area is replaced with the selected FFBE artwork; native frame pixels remain unchanged.
The blue custom backing, drawn gem and FFBE rarity badge are omitted. Saved portrait scale/position
controls still apply. Both the build converter and advanced preview use the same renderer; rebuild/install
the mod to refresh existing in-game icons.

## Full-release follow-up

Recollect native bindings and caster tracks before carrying any of these 21 bridges to the full game. Retest all six
skills on imported visions, including multiple targets and a party replacement. Refresh the five live-test
records only after confirmation on that build. Recheck the native icon masks/templates and rendering.
The read-only collector lives in `scripts/reference/monster-animations/`; output goes to Downloads/FFR Mod.
