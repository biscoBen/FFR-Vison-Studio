# Restore the original transferable MR rewards

The complete-kit audit previously counted 25 original MR active skills as covered because they were learned in awakening. Those skills were not transferable MR rewards. The revised layout restores all 25 as MR rewards without increasing the number of rewards at any rank. All 50 original passive MR rewards remain transferable. The [reproducible coverage report](SEPHIRA_MR_COVERAGE.md) now shows 75/75.

Each restored active has its stock native mechanics, equip cost, MP cost, general-command membership and animation. Its MR rank and acquisition family match the original. Saved custom acquisition overrides remain user choices. Rikku retains the Zidane acquisition gate.

| Original vision | Reward | MR | New MR teacher |
|---|---|---:|---|
| Tronn | Focus Magic (400630) | 5 | Christine |
| Wilhelm | Chakra (400440) | 3 | Barusa |
| Wilhelm | Guard (400640) | 5 | Barusa |
| Warrior of Light | Multi-Cover (400390) | 3 | Lenneth |
| Firion | Bladeblitz (400310) | 3 | Lila |
| Firion | Arms Akimbo (400650) | 9 | Lila |
| Onion Knight | Throw (400240) | 1 | Minfilia |
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
| Vaan | Gil Farmer (400400) | 1 | Elephim |
| Vaan | Gil Toss (400250) | 5 | Oracle Maiden Lunafreya |
| Noctis | Barrage (400300) | 9 | Dragon Knight Freya |
| Clive | Mirage (400670) | 7 | Reberta (JP) |

Current replacement: Rikku MR7 grants native **Pharmacology (1044)** instead of the Vaan-only **One for the Road (1435)**, at the same 30 AP cost. This user-approved exception retains the other 130 original passives and all 75 original equipable MR rewards.

## Balance and migration

Twelve original MR passive placements move to another compatible slot, retaining their native MR rank and acquisition family. Every original MR passive stays an MR reward. All 131 excluded-original passives remain learned across the kits. Each vision keeps its native counterpart’s total passive count and stays within 20% of its passive AP budget. No second percentage tier of the same main stat is added to a kit. The fixed allocation is recorded in `scripts/fixtures/sephira_mr_restoration_plan.json`; [the awakening report](SEPHIRA_AWAKENING_BALANCE.md) lists the final counts and costs.

An awakening active moves out only when that same vision now teaches it through MR. Other units retain signature awakening versions: Relm still has Mimic, for example, while Lunera teaches its MR version at Bartz’s gate. Canonical provenance identifies the MR teacher. Crystal Fina and Aria are unchanged. Private recipes, artwork, stats, permanent rewards, allocated IDs and acquisition choices are preserved.

Studio backs up and migrates untouched saved reward layouts once on loading. The build also applies the same declared migration to older configs. Deliberately edited affected MR slots or full awakening tiers are left intact and reported before building; use **Apply MR and acquisition update** after resolving the conflict. Later edits to migrated units remain user edits.

Native table writing/readback checks verify all 30 collection kits plus an independent Fina, Spirit owner bindings and all 25 stock active rows. Live-game equipment and balance still need playtesting.
