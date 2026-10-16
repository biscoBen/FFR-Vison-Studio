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
| Cling | 500910 | Damage, no visible animation; repaired presentation awaits a live test |

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

With **Show unverified skills** and **Use our skill changes** enabled, selected original Cling receives
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
hit constants, and preserved all-target Niagara reference. IoStore packing and verification pass. A live
Cling test against multiple enemies is still required.

## Imported vision icon framing

Face, timeline and ability icons now use the game's existing Cloud frame and supplied portrait mask.
Only the portrait area is replaced with the selected FFBE artwork; native frame pixels remain unchanged.
The blue custom backing, drawn gem and FFBE rarity badge are omitted. Saved portrait scale/position
controls still apply. Both the build converter and advanced preview use the same renderer; rebuild/install
the mod to refresh existing in-game icons.

## Full-release follow-up

Recollect native bindings and caster tracks before carrying the Cling bridge to the full game. Retest all six
skills on imported visions, including multiple targets and a party replacement. Refresh the five live-test
records only after confirmation on that build. Recheck the native icon masks/templates and rendering.
The read-only collector lives in `scripts/reference/monster-animations/`; output goes to Downloads/FFR Mod.
