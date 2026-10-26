# Eiko esper mastery and reviewed reward moves

The four new esper passives are equipable MR rewards. They follow the normal
native MR behavior: learned rewards are active through equipped Eiko, or can be
equipped individually on party Fina with any vision. Spirit of Eiko includes the
same MR effects. Vision/reward/Spirit sources apply each bonus once. Learning a
reward without equipping Eiko, that reward or Spirit does not activate it.
Summoning remains Fina's native command; Eiko no longer grants Ifrit or Shiva.

| Rank | Eiko | Equip cost |
| --- | --- | --- |
| MR1 | Nullify Silence | 10 |
| MR3 | Esper Power: esper damage +20% | 30 |
| MR5 | Esper Communion: recover 5% of the summoner's maximum MP per esper action | 20 |
| MR7 | Enduring Eidolons: one extra ordinary action before the finisher, esper max HP +20% | 40 |
| MR9 | Eidolon Revelry: 50% chance for each ordinary action to become a special; the final special stays guaranteed | 50 |

The native summon effects specify two ordinary actions before the final special.
Eight offensive espers check their remaining-action counter, then schedule their
special followed by dismissal. Their ordinary skills can include level-dependent
spells. Carbuncle instead uses a three-phase support rotation. The extra-action
reward repeats the opening phase before advancing the native rotation. Its early
special proc uses Glittering Ruby; its native support finale is retained.

Eiko also gains Healing Light (party Cure, 12 MP) in tier 1 and Eidolon's Reprieve
(party Regen, 25 MP) in tier 2. Raise is available in tier 1, and Shellga joins tier 2.
Her tier 3 bonus becomes Half MP Cost and tier 4
becomes Auto MP Restore (L). Her existing stats, acquisition, resonance, other
abilities and permanent MR rewards stay in place. Double EXP is removed from
her current rewards.

| Rank | Moogle of Narshe Mog |
| --- | --- |
| MR1 | Focus |
| MR3 | First Strike |
| MR5 | Recuperate LB |
| MR7 | Peaceful LB Engine |
| MR9 | LB Triple Charge |

Mystea swaps her MR5/MR9 abilities and MR1/MR2 rewards. AP and Spirit remain at
MR9. This is an explicit exception to the collection's ordinary odd/even layout.
All 131 original passive effects remain represented across the collection.
Rikku's resonance already uses Vaan's native eight-hit Fire attack against all
enemies, with guaranteed stealing; its mechanics and Rikku's presentation are
retained and checked against the generated rows.

Existing unedited default rewards migrate once, preserving vision and private
skill IDs, combat edits, artwork, acquisition and other settings. Edited MR slots
stay openable and report the conflict when applying the update. Previously
learned private equipment rewards retain their definitions for old saves.

## Implementation and validation limits

Custom passives 1960–1963 use private continuous markers on the equipping actor.
The owned UE4SS runtime checks the actual friendly native esper, Fina's active
effects/passives and her equipped vision's native effects/passives. It adds native damage/HP operations to that summon, restores
MP once per completed action, and adjusts native ordinary-action selection.
The final-special/dismissal stack is never replaced. Multi-hit callbacks and
dismissal do not create extra MP payments. No save or loadout mutation is used.
Native actor addresses preserve the same tracking across fresh Lua wrappers on
UE4SS 3.0.1, preventing repeated spawn bonuses or an indefinitely extended turn.

Validation includes native table serialization/readback, original-row preservation,
mastery/Spirit owner links, executable Lua ownership/lifecycle fixtures, and
Studio migration tests. These checks are not a live game test. In-game checks
are still needed for the four new runtime effects, Spirit activation, MP/HP
readback, Carbuncle's support rotation and higher-level esper variants.

The runtime logs concise `[FFR Esper]` entries to UE4SS.log for spawn bonuses,
extra actions, early specials, MP recovery and any unavailable native call.

On the user's UE4SS build `e3ba1016`, a UFunction-returned array is a Lua list
of `RemoteUnrealParam` elements. Unwrap each with `get()` before reading the
effect or passive ID. The native passive-list getter fills a caller-supplied
output table; it is not a zero-argument return-list getter. Each reward reader
is isolated so an unavailable optional read does not discard the other source.
The observer also records reflected function signatures for future diagnostics.
The loader contracts are documented in its
[array and UFunction pushers](https://github.com/UE4SS-RE/RE-UE4SS/blob/e3ba1016/UE4SS/src/LuaType/LuaUObject.cpp).
Fixtures model those wrapped lists, the output parameter, both failure cases
from the returned trace, and independent reader failure. In-game confirmation
is still required.
