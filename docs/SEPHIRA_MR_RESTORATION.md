# Restore the original transferable MR rewards

The complete-kit audit previously counted 25 original MR active skills as covered because they were learned in awakening. Those skills were not transferable MR rewards. The revised layout restores all 25 as MR rewards without increasing the number of rewards at any rank. All 50 original passive MR rewards remain transferable. The [reproducible coverage report](SEPHIRA_MR_COVERAGE.md) now shows 75/75.

Each restored active has its stock native mechanics, equip cost, MP cost, general-command membership and animation. Acquisition families match the originals. Minfilia’s Throw is now MR3 instead of the original MR1, as explicitly requested alongside Libra at MR1. Saved acquisition overrides remain user choices. Rikku retains the Zidane gate.

| Original vision | Reward | MR | New MR teacher |
|---|---|---:|---|
| Tronn | Focus Magic (400630) | 5 | Christine |
| Wilhelm | Chakra (400440) | 3 | Barusa |
| Wilhelm | Guard (400640) | 5 | Barusa |
| Warrior of Light | Multi-Cover (400390) | 3 | Lenneth |
| Firion | Bladeblitz (400310) | 3 | Lila |
| Firion | Arms Akimbo (400650) | 9 | Lila |
| Onion Knight | Throw (400240) | 3 | Minfilia |
| Cecil | Darkness (400490) | 1 | Snow White |
| Cecil | Cover (400380) | 3 | Lilith |
| Bartz | Wait (400760) | 1 | Lunera |
| Bartz | Mimic (400330) | 9 | Lunera |
| Cloud | Deathblow (400530) | 3 | Nalu |
| Cloud | Fill Gauge (400770) | 5 | Jade |
| Squall | Gut Rip (400690) | 3 | A2 |
| Squall | Double Action (400710) | 9 | A2 |
| Zidane | Steal (400260) | 1 | Rikku (FFX-2) |
| Zidane | Mug (400270) | 5 | Rikku (FFX-2) |
| Zidane | Misfortune (400750) | 9 | Rikku (FFX-2) |
| Tidus | Focus (400460) | 1 | Moogle of Narshe Mog |
| Tidus | Reckless Abandonment (400700) | 5 | Elza |
| Shantotto | Dualcast (400730) | 9 | Trance Terra |
| Vaan | Gil Farmer (400400) | 1 | Aerith |
| Vaan | Gil Toss (400250) | 5 | Oracle Maiden Lunafreya |
| Noctis | Barrage (400300) | 9 | Dragon Knight Freya |
| Clive | Mirage (400670) | 7 | Reberta (JP) |

## Balance and migration

Twelve original MR passive placements move to another compatible slot, retaining their native MR rank and acquisition family. Every original MR passive stays an MR reward. 130 of 131 excluded-original passives remain learned across the kits after the approved Rikku replacement. The new swaps remove one passive each from Minfilia and Barusa and add one each to Primm and Trance Terra, preserving the collection total. Each remains within 20% of its native passive AP budget. The historical restoration plan and the later requested swaps are recorded separately in `scripts/fixtures/sephira_mr_restoration_plan.json` and `scripts/sephira_mr_layout.py`.

Trance Terra’s Fire Eater moves to awakening tier 3 and Primm MR9. Primm’s Boundless Flames moves to awakening tier 4, and Terra’s Trance Apocalypse moves from tier 3 to tier 4 to keep every tier within eight slots. Original MR rewards remain transferable. Crystal Fina and Aria are unchanged. Private recipes, artwork, stats, permanent rewards, allocated IDs and acquisition choices are preserved.

Studio backs up and migrates untouched saved reward layouts once on loading. The build also applies the same staged migration to older configs. Previously learned Barusa Earth-imbue IDs remain defined. Edited affected MR slots or full awakening tiers are left intact and reported before building; use **Apply MR and acquisition update** after resolving the conflict. Later edits to migrated units remain user edits.

Native table writing/readback checks verify all 30 collection kits plus an independent Fina, Spirit owner bindings and all 25 stock active rows. Live-game equipment and balance still need playtesting.
