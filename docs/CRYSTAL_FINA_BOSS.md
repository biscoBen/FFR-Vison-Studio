# Crystal Fina boss test

Enable **Home → Shop practice battle**, rebuild/install, restart Resonance, and talk to the Young Woman in
Mitra's item shop. Choose **More opponents** until **Crystal Fina (level 10): vision boss test** appears.
The final page also has More opponents and Cancel. Repeat fights use the same picker.

She loads her approved native Fina body and rotating glass crystal even with an empty vision roster or
Sephira's Visions switched off. If the vision is also included, both share its presentation. The enemy kit
and stats are independent of edits to the player vision. The usual Studio runtime/UE4SS prerequisite for
Crystal Fina's glass is still required; the build stages it automatically.

| Parameter | Value |
| --- | ---: |
| Level | 10 |
| HP / MP | 6,500 / 500 |
| Attack / Magic (Intelligence) | 100 / 105 |
| Defense / Spirit (Mind) | 70 / 80 |
| Speed (Agility) | 40 |
| Stagger gauge | 250 |

These are fixed enemy values, with no vision growth table, equipment, inherited boss passives or elemental
immunities. Light damage is halved, dark is a weakness, and other elements are neutral. Ailment/debuff
resistances use the native early-boss template. Her stats sit between native Belmodar (level 4, 2,000 HP)
and Liquid Thunder (level 13, 10,000 HP),
with lower defenses and offense than the latter. They are a starting balance target for an approximately
level-10 party; actual difficulty depends on equipment, visions, party size and action speed.

Her native AI repeats this eight-action cycle:

1. Attack — a weak, neutral single-target hit (power 12), with a small crystal-shot visual.
2. Banish — single-target light magic (power 17).
3. Crystal Ray — single-target light magic (power 32).
4. Crystal Sanctification — party-wide light magic (power 40).
5. Attack.
6. Restore — heal herself by 20% maximum HP **only at or below half HP**; otherwise Attack.
7. Banishra — single-target light magic (power 33).
8. Holy — stronger single-target light magic (power 80).

The native think counter determines the phase; all targeting goes through the original enemy scheduler.
Only one action is scheduled per decision. Healing is limited to one opportunity per cycle and consumes
that action. Silence falls back to the neutral attack through the native silence-fight setting.

Private enemy copies retain all 16 active abilities from the default Crystal Fina awakening kit, plus Attack.
Their effects and damage remain the preset versions; MP costs are zero for the enemy, as with the game's
ordinary enemy skills. The solo rotation uses the subset above: ally revival, Reraise and large unrestricted
heals stay outside it to avoid invalid solo targets or repeated resets. Passive/MR stat bonuses and the
vision's summon/resonance lifecycle are not attached to the enemy. Original skills and the obtainable
vision are unchanged. Native spell presentation variants and sound tracks are reused.

This test has no vision reward or acquisition requirement. It gives no XP, gil or item drops and keeps the
practice encounter's guaranteed escape. **Survive at 1 HP** remains available separately for animation testing;
turn it off when judging difficulty. Defeat-to-acquire progression can be added after the fight is tuned.

Validation checks the entire emitted rotation across many decisions, health thresholds, private IDs, native
table isolation, source-kit coverage, shared/standalone presentation, paged choices and real Kismet offsets.
Native package builds/readbacks exercise the supplied demo assets. A live fight and level-10 balance still
need an in-game test; file/serializer checks do not establish playability or difficulty.
