# Sephira vision challenge balance

This pass applies Christine’s tested approach to all 15 encounters (28 enemy visions). It changes private enemy copies; player abilities and mastery rewards keep their existing values. Live feedback is still needed for each fight.

- Preserve the existing encounter level, combined HP and shared break budget. Split attack power across partners, and stagger their signature turns.
- Increase physical and magic offensive stats by 50% over the original challenge curve, and speed by about 15%. Christine already had the magic/speed adjustment; her speed is unchanged in this pass.
- Apply the earlier bounded attack/spell increases (+50%, or +75% for a configured damaging signature), divide between partners, then apply the additional 50% used by the approved Christine fight. This affects physical and magical damage. Native integer rounding applies; healing remains capped at 15% and control effects keep their existing mechanics.
- Give caster roles spell basics. Apply explicit elemental resistance/weakness pairs where the vision has a clear theme. Other elements remain neutral.
- Christine remains level 5 with 2,750 HP and 162 break. Christine’s approved values stay at Blizzard 39, Blizzara 50 and Freezing Spike 78. The extra factor is not applied twice to her. Slumber Mist stays unchanged.
- Vision rewards use ordinary battle loot with the native guaranteed-drop value (1). No post-battle reward event or acquisition sequence runs. The user confirms Christine now grants her vision in the result screen and returns without a black screen. Other encounters use the same path. Escape/loss give no reward.

| Original unlock | Opponents | Level | Combined HP | Combined break | Speed | Basic actions |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Tronn | Christine | 5 | 2,750 | 162 | 24 | Christine: Blizzard |
| Wilhelm | Barusa + Charming Kitty Ariana | 26 | 48,000 | 1000 | 138 | Barusa: Attack; Charming Kitty Ariana: Wind Aria |
| Warrior of Light | Crystal Fina + Lenneth | 7 | 4,250 | 198 | 32 | Crystal Fina: Banish; Lenneth: Attack |
| Firion | Blue Sky Belle Fran + Lila | 18 | 34,000 | 750 | 123 | Blue Sky Belle Fran: Attack; Lila: Attack |
| Onion Knight | Minfilia + Spirited Heart Primm | 17 | 30,750 | 662 | 110 | Minfilia: Stone; Spirited Heart Primm: Attack |
| Cecil | Mystea + Snow White + Lilith | 26 | 48,000 | 999 | 138 | Mystea: Dark; Snow White: Attack; Lilith: Attack |
| Bartz | Fryevia + Lunera | 35 | 96,000 | 1200 | 241 | Fryevia: Attack; Lunera: Attack |
| Cloud | Jade + Nalu | 8 | 5,000 | 216 | 37 | Jade: Attack; Nalu: Attack |
| Squall | A2 + Alice/Half Nightmare | 18 | 34,000 | 750 | 123 | A2: Attack; Alice/Half Nightmare: Attack |
| Zidane | Eiko + Rikku (FFX-2) | 12 | 13,750 | 324 | 60 | Eiko: Banish; Rikku (FFX-2): Attack |
| Tidus | Moogle of Narshe Mog + Elza | 22 | 38,800 | 950 | 135 | Moogle of Narshe Mog: Aero; Elza: Attack |
| Shantotto | Trance Terra + Relm | 28 | 50,000 | 1000 | 190 | Trance Terra: Fire; Relm: Thunder |
| Vaan | Oracle Maiden Lunafreya + Aerith | 35 | 96,000 | 1200 | 241 | Oracle Maiden Lunafreya: Water; Aerith: Burning Notes |
| Noctis | Dragon Knight Freya | 14 | 21,000 | 400 | 72 | Dragon Knight Freya: Attack |
| Clive | Reberta (JP) | 4 | 2,000 | 145 | 20 | Reberta (JP): Attack |

The original vision prerequisite is checked both at the crystal and before battle. Existing shop overrides continue to remove the selected vision from its challenge. These are a common starting point for subsequent tuning at the player’s actual level; they do not establish an exact damage-per-turn prediction for every difficulty.
