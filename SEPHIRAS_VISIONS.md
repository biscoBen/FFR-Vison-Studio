# Sephira’s Visions

30 optional, editable presets using the requested FFBE forms. Enable the section on the home page, then build/install. First enable downloads only the missing selected artwork and adds the profiles after all preparations succeed.

Turning the section off keeps edits and removed entries; its units and acquisition caves are omitted by the next build. **Restore missing** adds removed presets without resetting existing ones. **Reset all presets** or a card’s **Reset to preset** replaces its kit and appearance, preserves its IDs and acquisition location, and backs up the previous roster in Studio’s character-config backups.

An existing custom Crystal Fina is adopted with her current edits and acquisition intact. Reset her explicitly to use this balanced recipe. Other user-added copies and original vision/party edits are preserved.

## Balance and coverage

- Every preset copies a native level-one stat profile with five learned MR rewards at ranks 1, 3, 5, 7 and 9. MR 2/6/8 give three relevant permanent stats (normalized 5/10/15 points; HP ×6, MP ×2); MR 4 and 9 each give +8 AP. MR 9 also grants the Spirit mastery. MR 0 is the native empty starting rank; every rank from 1 to 9 has a reward. Native physical or magic growth curves are used.
- Existing native grants retain their mechanics. Supplemental skills come from the wider native/enemy catalog on private player copies: zero-MP enemy attacks receive MP costs; excessive accuracy, multipliers and hit counts are reduced. Group spells/healing cost more than comparable single-target spells. No FFBE multipliers or FFBE stat conversion are imported. LBs retain one native resonance’s total mechanics; selected elements/damage types follow the requested role.
- All 160 distinct active skills and 131 passives from the 15 excluded original visions are allocated. Within the pack, each exact active/passive appears once; permanent MR stats may repeat. Additional native skills provide thematic attacks and support. Each new vision has its own correctly bound Spirit mastery wrapper.
- Command/LB-specific bonuses use private rebound copies. Native originals remain unchanged. Minfilia’s Dual Jobs selects her own identity. Specific skill bonuses remain grouped with their required attacks.
- Revision 6 gives each vision 15–21 awakening active skills and exactly five MR passives, one at MR1/3/5/7/9. All 131 original passives are preserved once, with 19 additional bonuses; excessive extra passives are removed. Former MR active skills return to awakening. Permanent MR stats, the Spirit wrapper and LB are excluded from both skill counts. Clive’s Eikon attacks and limit-break bonus remain on Reberta. They specialize without being restricted to one action type: healers and debuffers also have attacks. Aria is sold in Mitra. Folka unlocks in Olderion’s item shop after its guardian story scene, at twice that shop’s highest other item price. The other 28 visions are challenge rewards at the matched original vision’s shrine, with a separate Zoldaad cave for Barusa and Ariana. Acquisition remains editable.
- Great Dragon is retired from this collection and omitted from builds, including older tagged saved profiles. Reset all presets backs up and removes his old collection entry. His required original grants move to Reberta, Minfilia, Lila, Trance Terra and Primm. Untagged user-created Great Dragons are preserved.
- New enemy copies belong to the vision’s player command; enemy group-toggle partners are disabled so they cannot switch into unbalanced originals. Replacement bonuses retain native effects and equip costs, with a 20-AP floor for item bonuses that originally cost zero. Revision 5 replaces 52 reused rewards from kept visions with equipment/enemy bonuses and bounded enemy skills. Those protected MR rewards are absent from both awakening and MR; all excluded-vision grants remain allocated. The eight earlier low-tier alternatives remain available. Boss invulnerability and permanent attack buffs are replaced by finite native player effects; drain restores no more than damage dealt. Permanent MR rewards follow the same role-based three-stat budget for every preset. Alice’s three earth slams become ice slams with unchanged power/cost.
- Eiko uses the demo’s available Ifrit and Shiva summon commands; their native costs and mechanics are retained. Unreleased espers are not required.

The excluded originals are Tronn, Wilhelm, Warrior of Light, Firion, Onion Knight, Cecil, Bartz, Cloud, Squall, Zidane, Tidus, Shantotto, Vaan, Noctis and Clive. Their exact grants, native ranks, descriptions, mechanics and allocations are retained in `assets/sephira_visions/native_coverage.json`.

## Acquiring the visions

After obtaining the matched original, talk to its crystal again and select Challenge. The original replay remains available. Ownership or the original’s individual completion flag is checked before the menu, immediately before battle, and before rewards. Wilhelm uses his final quest step, not quest acceptance. Winning grants only missing team members; leaving, escaping or losing grants none. There are no farmable boss drops or XP. Each team shares one local-level boss budget, with staggered eight-action rotations and bounded healing. These are authored starting values; live balance still needs playtesting.

Tronn → Christine; Wilhelm → Barusa/Ariana; Warrior of Light → Lenneth/Crystal Fina; Firion → Lila/Fran; Onion Knight → Minfilia/Primm; Cecil → Snow White/Lilith/Mystea; Bartz → Fryevia/Lunera; Cloud → Nalu/Jade; Squall → A2/Alice; Zidane → Lunafreya/Eiko; Tidus → Elza/Mog; Shantotto → Trance Terra/Relm; Vaan → Rikku/Elephim; Noctis → Freya; Clive → Reberta.

Levels come from ordinary enemies in the encounter volume containing each shrine entrance (Earth Shrine’s inner floor for Tronn). See `assets/existing_visions/payload/sephira_challenges.json` for the native source tables, unlock evidence and local levels.

**Sephira visions: 1-gil Mitra shop** temporarily sells every enabled collection vision in Mitra’s item shop, without its normal story/challenge gate. Rebuild/install after switching. Turning it off restores the saved cave, crystal or shop assignments and prices; saved recipes and locations are never rewritten. Already purchased visions remain owned.

## Kit sizes

Use **Apply MR and acquisition update** for existing saved presets, then build/install. It backs up the roster and preserves allocated IDs, artwork, permanent stat rewards, combat recipes and active learned abilities. It replaces the passive selection with five curated MR rewards and moves MR active skills to awakening. Saved acquisition choices are preserved. See [the complete passive allocation](docs/SEPHIRA_PASSIVE_MASTERY.md). Earlier recipes also receive the MR schedule and challenge/shop locations. New presets include the revision automatically. Later edits to updated presets remain yours.

| Vision | Awakening abilities | Awakening bonuses | Awakening total | Additional MR abilities | Additional MR bonuses |
|---|---:|---:|---:|---:|---:|
| A2 | 19 | 0 | 19 | 0 | 5 |
| Christine | 16 | 0 | 16 | 0 | 5 |
| Crystal Fina | 17 | 0 | 17 | 0 | 5 |
| Barusa | 16 | 0 | 16 | 0 | 5 |
| Blue Sky Belle Fran | 17 | 0 | 17 | 0 | 5 |
| Oracle Maiden Lunafreya | 17 | 0 | 17 | 0 | 5 |
| Minfilia | 16 | 0 | 16 | 0 | 5 |
| Folka | 19 | 0 | 19 | 0 | 5 |
| Fryevia | 17 | 0 | 17 | 0 | 5 |
| Lenneth | 19 | 0 | 19 | 0 | 5 |
| Lila | 16 | 0 | 16 | 0 | 5 |
| Mystea | 15 | 0 | 15 | 0 | 5 |
| Reberta (JP) | 18 | 0 | 18 | 0 | 5 |
| Snow White | 19 | 0 | 19 | 0 | 5 |
| Aria | 21 | 0 | 21 | 0 | 5 |
| Eiko | 17 | 0 | 17 | 0 | 5 |
| Alice/Half Nightmare | 17 | 0 | 17 | 0 | 5 |
| Moogle of Narshe Mog | 16 | 0 | 16 | 0 | 5 |
| Lilith | 16 | 0 | 16 | 0 | 5 |
| Dragon Knight Freya | 18 | 0 | 18 | 0 | 5 |
| Trance Terra | 17 | 0 | 17 | 0 | 5 |
| Charming Kitty Ariana | 18 | 0 | 18 | 0 | 5 |
| Elephim | 17 | 0 | 17 | 0 | 5 |
| Jade | 18 | 0 | 18 | 0 | 5 |
| Spirited Heart Primm | 18 | 0 | 18 | 0 | 5 |
| Relm | 19 | 0 | 19 | 0 | 5 |
| Rikku (FFX-2) | 20 | 0 | 20 | 0 | 5 |
| Nalu | 18 | 0 | 18 | 0 | 5 |
| Elza | 18 | 0 | 18 | 0 | 5 |
| Lunera | 17 | 0 | 17 | 0 | 5 |

## Selected forms and kits

Awakening ranks below are numbered 1–4 for readability. MR ranks use the game’s 0–9 values. Native source names are retained for skills so their exact versions remain identifiable.

### A2 — 5

Physical combo attacker.

Sprite `310000505` (GL); base-stat budget: Squall. Growth: Cloud.

- Awakening 1: Rend [485003]; Venom Skewer [485006]; Blade Volley [485015]; Guard Mode [485045]; Charging Blade [485051].
- Awakening 2: Rough Divide [446600]; Grand Slash [485009]; Perforate [485012]; Colossal Cleave [485030]; Quad Blade [485033]; Binding Assault [485036].
- Awakening 3: Fated Circle [446610]; Rending Edge [485039]; Offensive Calibration [485042]; Relentless Blade [485048].
- Awakening 4: Numbing Slash [485018]; Gut Rip [400690]; Barrage [400300]; Double Action [400710].
- MR 1: Physical Attack +20% [1309].
- MR 2: HP +30 (permanent).
- MR 3: Improvement [1421].
- MR 4: AP +8 (permanent).
- MR 5: Trigger [1422].
- MR 6: Agility +10 (permanent).
- MR 7: Lone Lion [1423].
- MR 8: Attack +15 (permanent).
- MR 9: Latent Potential [1424]; AP +8 (permanent); Spirit of A2.

Supplemental player copies (native source ID; final MP/power):

- Rend ← Rend [501510, enemy]: MP 8, power 18. Non-elemental physical damage; power 18. Single enemies; MP 8; hits 1; accuracy 100; stagger 25.
- Venom Skewer ← Skewer [501790, enemy]: MP 12, power 18. Non-elemental physical damage; power 18. Apply Poison (50%). Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- Grand Slash ← Grand Slash [501310, enemy]: MP 18, power 18. Non-elemental physical damage; power 18. Group enemies; MP 18; hits 1; accuracy 100; stagger 12.
- Perforate ← Perforate [502220, enemy]: MP 24, power 30. Non-elemental physical damage; power 30. Apply Poison (50%). Single enemies; MP 24; hits 1; accuracy 100; stagger 25.
- Blade Volley ← Machine Gun [500150, enemy]: MP 10, power 12. Non-elemental physical damage; power 12. Single enemies; MP 10; hits 4; accuracy 100; stagger 25.
- Colossal Cleave ← Colossus Cleave [501720, enemy]: MP 22, power 30. Non-elemental physical damage; power 30. Single enemies; MP 22; hits 1; accuracy 100; stagger 25.
- Quad Blade ← Barrage [503260, enemy]: MP 24, power 32. Non-elemental physical damage; power 32. Single enemies; MP 24; hits 4; accuracy 100; stagger 12.
- Binding Assault ← Boundless Void [505950, enemy]: MP 20, power 24. Non-elemental physical damage; power 24. Apply Paralyzation (50%). Single enemies; MP 20; hits 2; accuracy 100; stagger 33.
- Rending Edge ← Devil Claw [571330, enemy]: MP 18, power 20. Non-elemental physical damage; power 20. Also remove enemy buffs. Single enemies; MP 18; hits 1; accuracy 100; stagger 25.
- Offensive Calibration ← 猛攻の血を注入した！ [501780, enemy]: MP 20, power 0. Raise own attack and magic by 50% for 3 turns. Self friendlies; MP 20; hits 1; accuracy 100; stagger 25.
- Guard Mode ← Assaulting Warcry [505420, enemy]: MP 12, power 0. Reduce own physical damage taken by 30% for 3 turns. Self friendlies; MP 12; hits 1; accuracy 100; stagger 25.
- Relentless Blade ← Unrelenting Claw [503840, enemy]: MP 28, power 36. Non-elemental physical damage; power 36. Single enemies; MP 28; hits 1; accuracy 100; stagger 20.
- Charging Blade ← Trample [501050, enemy]: MP 10, power 18. Non-elemental physical damage; power 18. Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Numbing Slash ← Numbclaw [500890, enemy]: MP 10, power 12. Non-elemental physical damage; power 12. Apply Paralyzation (100%). Single enemies; MP 10; hits 1; accuracy 100; stagger 25.

### Christine — 6

Ice magic and stagger.

Sprite `401002606` (GL); base-stat budget: Tronn. Growth: Terra.

- Awakening 1: Blizzard [220050]; Silence [230030]; Dispel [210200]; Blizzard Beam [485109]; Frost Wave [485115]; Frozen Needle [485130].
- Awakening 2: Blizzara [220060]; Blizzaga [220070]; Absolute Zero [485106]; Slumber Mist [485112]; Frozen Needle II [485133]; Snowstorm [485139]; Focus Magic [400630].
- Awakening 3: Freezing Spike [485103]; Frozen Needle III [485136]; Frostspike [485142].
- MR 1: Restore MP on Stagger [1281].
- MR 2: Agility +5 (permanent).
- MR 3: Stagger Power +30% [1376].
- MR 4: AP +8 (permanent).
- MR 5: Victor’s Respite [1407].
- MR 6: MP +20 (permanent).
- MR 7: True Stagger [1406].
- MR 8: Magic +15 (permanent).
- MR 9: Half MP Cost [1045]; AP +8 (permanent); Spirit of Christine.

Supplemental player copies (native source ID; final MP/power):

- Freezing Spike ← Freezing Spike [220080, native]: MP 30, power 30. Ice magic damage; power 30. Group enemies; MP 30; hits 3; accuracy 100; stagger 21.
- Absolute Zero ← Absolute Zero [500230, enemy]: MP 22, power 24. Ice magic damage; power 24. Group enemies; MP 22; hits 1; accuracy 100; stagger 12.
- Blizzard Beam ← Blizzard Beam [500990, enemy]: MP 10, power 18. Ice magic damage; power 18. Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Slumber Mist ← Sleep Gas [500570, enemy]: MP 20, power 0. Apply Sleep (30%). Group enemies; MP 20; hits 1; accuracy 100; stagger 12.
- Frost Wave ← Blaze [500350, enemy]: MP 12, power 12. Ice magic damage; power 12. Group enemies; MP 12; hits 2; accuracy 100; stagger 12.
- Frozen Needle ← Blizzard of the Seventh Dawn [220420, native]: MP 5, power 19. Ice magic damage; power 19. Single enemies; MP 5; hits 1; accuracy 100; stagger 17.
- Frozen Needle II ← Blizzard II of the Seventh Dawn [220430, native]: MP 17, power 36. Ice magic damage; power 36. Single enemies; MP 17; hits 2; accuracy 100; stagger 19.
- Frozen Needle III ← Blizzard III of the Seventh Dawn [220440, native]: MP 45, power 48. Ice magic damage; power 48. Group enemies; MP 45; hits 3; accuracy 100; stagger 25.
- Snowstorm ← Snowstorm [500470, enemy]: MP 20, power 18. Ice magic damage; power 18. Group enemies; MP 20; hits 1; accuracy 100; stagger 12.
- Frostspike ← Frostspike [506130, enemy]: MP 32, power 30. Ice magic damage; power 30. Apply Slow (100%). Group enemies; MP 32; hits 3; accuracy 100; stagger 21.

### Crystal Fina — Custom

Healing, cleansing and light magic.

Sprite `99887755552703` (CUSTOM); base-stat budget: Ayaka. Growth: Terra.

- Awakening 1: Cure [210010]; Banish [210250].
- Awakening 2: Cura [210020]; Banishra [210260]; Crystal Ray [485212]; Restore [485215]; Purify [485236]; Crystal Renewal [485218].
- Awakening 3: Curaga [210030]; Banishga [210270]; Arise [210150]; Crystal Renewal [485233].
- Awakening 4: Esunaga [210130]; Holy [485203]; Reraise [485206]; Radiant Restoration [485209]; Crystal Sanctification [485230].
- MR 1: Healing Magic +20% [1283].
- MR 2: HP +30 (permanent).
- MR 3: Magic Evasion +15% [1551].
- MR 4: AP +8 (permanent).
- MR 5: Auto-Regen [1077].
- MR 6: MP +20 (permanent).
- MR 7: LB Charge on Action [1552].
- MR 8: Mind +15 (permanent).
- MR 9: Grit [1042]; AP +8 (permanent); Spirit of Crystal Fina.

Supplemental player copies (native source ID; final MP/power):

- Holy ← Holy [210190, native]: MP 63, power 80. Light magic damage; power 80. Single enemies; MP 63; hits 1; accuracy 100; stagger 40.
- Reraise ← Reraise [210240, native]: MP 60, power 0. Grant Reraise to an ally. Single friendlies; MP 60; hits 1; accuracy 100; stagger 25.
- Radiant Restoration ← Curaga [215020, native]: MP 65, power 1500. Restore healing power 1500. Group friendlies; MP 65; hits 1; accuracy 100; stagger 60.
- Crystal Ray ← Array: Brilliance [503630, enemy]: MP 24, power 32. Light magic damage; power 32. Single enemies; MP 24; hits 1; accuracy 100; stagger 25.
- Restore ← Restore [501930, enemy]: MP 18, power 20. Restore 20% max HP. Single friendlies; MP 18; hits 1; accuracy 100; stagger 25.
- Crystal Sanctification ← Holy [240190, enemy]: MP 45, power 40. Light magic damage; power 40. Group enemies; MP 45; hits 1; accuracy 100; stagger 40.
- Crystal Renewal ← Repair [503210, enemy]: MP 35, power 10. Restore 10% max HP. Group friendlies; MP 35; hits 1; accuracy 100; stagger 25.
- Purify ← Regurgitate [570690, enemy]: MP 15, power 50. Remove an ally’s ailments. Single friendlies; MP 15; hits 1; accuracy 100; stagger 0.
- Crystal Renewal ← Curaga [506110, enemy]: MP 50, power 400. Restore healing power 400. Group friendlies; MP 50; hits 1; accuracy 100; stagger 50.

### Barusa — 6

Earth physical bruiser and protection.

Sprite `401003006` (GL); base-stat budget: Wilhelm. Growth: Cloud.

- Awakening 1: Stone Surge [421400]; Stone Slam [421340]; Quicksand [485309]; Granite Claw [485312]; Granite Slam [485333]; Stone Horn [485336]; Guard [400640].
- Awakening 2: Stonera Surge [421410]; Stonera Slam [421350]; D Sword Breaker [414700]; Crust Driver [485303]; Granite Shell Strike [485330].
- Awakening 3: Stonega Surge [421420]; Stonega Slam [421360]; Supreme Defense [414710]; Mantle Driver [485306].
- MR 1: Imbue Earth [1526].
- MR 2: HP +30 (permanent).
- MR 3: Strategic Acumen [1336].
- MR 4: AP +8 (permanent).
- MR 5: General’s Pride [1452].
- MR 6: Defence +10 (permanent).
- MR 7: Unmoving Bulwark [1453].
- MR 8: Attack +15 (permanent).
- MR 9: Bastion [1454]; AP +8 (permanent); Spirit of Barusa.

Supplemental player copies (native source ID; final MP/power):

- Crust Driver ← Crust Driver [414800, native]: MP 20, power 23. Earth physical damage; power 23. Single enemies; MP 20; hits 1; accuracy 100; stagger 33.
- Mantle Driver ← Mantle Driver [414810, native]: MP 37, power 49. Earth physical damage; power 49. Single enemies; MP 37; hits 3; accuracy 100; stagger 36.
- Quicksand ← Quicksand [500330, enemy]: MP 12, power 12. Earth physical damage; power 12. Apply Slow (100%). Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- Granite Claw ← Pincer [500540, enemy]: MP 8, power 18. Non-elemental physical damage; power 18. Single enemies; MP 8; hits 1; accuracy 100; stagger 25.
- Granite Shell Strike ← Turtle Shell [501340, enemy]: MP 18, power 24. Earth physical damage; power 24. Also reduce own physical damage taken by 30% for 3 turns. Single enemies; MP 18; hits 1; accuracy 100; stagger 25.
- Granite Slam ← Slam [500030, enemy]: MP 6, power 12. Earth physical damage; power 12. Single enemies; MP 6; hits 1; accuracy 100; stagger 25.
- Stone Horn ← Horn [500550, enemy]: MP 10, power 18. Earth physical damage; power 18. Single enemies; MP 10; hits 1; accuracy 100; stagger 25.

### Blue Sky Belle Fran — 6

Ranged physical and disabling arrows.

Sprite `212001706` (GL); base-stat budget: Firion. Growth: Cloud.

- Awakening 1: Aero Knife [421250]; Thunder Knife [421100]; Sleep Knife [422010]; Poison Arrow [485403]; Binding Arrow [485406]; Triple Arrow [485430]; Snipe [485439]; Focused Arrow [485412].
- Awakening 2: Aerora Knife [421260]; Thundara Knife [421110]; Blind Knife [422030]; Windfeather Volley [485436]; Flurry Arrow [485442].
- Awakening 3: Aeroga Knife [421270]; Thundaga Knife [421120]; Arrow Tempest [485409]; Roving Volley [485433].
- MR 1: Add Poison [1125].
- MR 2: Agility +5 (permanent).
- MR 3: Add Blind [1128].
- MR 4: AP +8 (permanent).
- MR 5: Add Silence [1126].
- MR 6: HP +60 (permanent).
- MR 7: Critical Hit Rate +5% [1321].
- MR 8: Attack +15 (permanent).
- MR 9: Decimating Attacks [1337]; AP +8 (permanent); Spirit of Blue Sky Belle Fran.

Supplemental player copies (native source ID; final MP/power):

- Poison Arrow ← Poison Slash [500210, enemy]: MP 8, power 12. Non-elemental physical damage; power 12. Apply Poison (100%). Single enemies; MP 8; hits 1; accuracy 100; stagger 25.
- Binding Arrow ← Stun Slash [501170, enemy]: MP 10, power 12. Non-elemental physical damage; power 12. Apply Paralyzation (100%). Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Arrow Tempest ← Frenzied Bombardment [503250, enemy]: MP 32, power 32. Non-elemental physical damage; power 32. Group enemies; MP 32; hits 4; accuracy 100; stagger 12.
- Triple Arrow ← Beak [500480, enemy]: MP 10, power 12. Non-elemental physical damage; power 12. Single enemies; MP 10; hits 3; accuracy 100; stagger 25.
- Roving Volley ← Strikes of the Duty Bound [503820, enemy]: MP 28, power 32. Non-elemental physical damage; power 32. Random enemies; MP 28; hits 4; accuracy 100; stagger 12.
- Windfeather Volley ← 羽ばたき_物理 [503880, enemy]: MP 20, power 20. Wind physical damage; power 20. Group enemies; MP 20; hits 3; accuracy 100; stagger 20.
- Snipe ← Snipe [500110, enemy]: MP 6, power 12. Non-elemental physical damage; power 12. Single enemies; MP 6; hits 1; accuracy 100; stagger 25.
- Flurry Arrow ← Flatten [500190, enemy]: MP 10, power 18. Non-elemental physical damage; power 18. Single enemies; MP 10; hits 2; accuracy 100; stagger 25.
- Focused Arrow ← Hack [500050, enemy]: MP 8, power 18. Non-elemental physical damage; power 18. Single enemies; MP 8; hits 1; accuracy 100; stagger 25.

### Oracle Maiden Lunafreya — NV Brave Shift

Debuff specialist with water/wind magic.

Sprite `215002417` (GL); base-stat budget: Zidane. Growth: Terra.

- Awakening 1: Free Energy [446800]; Deprotect [230080]; Slowing Tide [485509].
- Awakening 2: Meo Twister [446820]; Steal Vitality [446860]; Deshell [230090]; Confusega [485512]; Maelstrom [485515]; Blinding Light [485518]; Weakening Tide [485533]; Fading Tide [485536].
- Awakening 3: Free Energy+ [446810]; Steal Magic [446870]; Sundering Wind [485503]; Graceful Deluge [485506].
- Awakening 4: Meo Twister+ [446830]; Oracle’s Censure [485530].
- MR 1: Add Deprotect [1131].
- MR 2: Agility +5 (permanent).
- MR 3: Regen on Stagger [1286].
- MR 4: AP +8 (permanent).
- MR 5: Magic Attack +30% [1275].
- MR 6: MP +20 (permanent).
- MR 7: Insult to Injury [1425].
- MR 8: Magic +15 (permanent).
- MR 9: Aggravation [1468]; AP +8 (permanent); Spirit of Oracle Maiden Lunafreya.

Supplemental player copies (native source ID; final MP/power):

- Sundering Wind ← Sundering Wind [502470, enemy]: MP 28, power 0. Reduce enemy physical and magic defense by 30% for 3 turns. Group enemies; MP 28; hits 1; accuracy 100; stagger 12.
- Graceful Deluge ← Graceful Deluge [501420, enemy]: MP 40, power 30. Water magic damage; power 30. Also reduce enemy physical and magic defense. Group enemies; MP 40; hits 3; accuracy 100; stagger 12.
- Slowing Tide ← Mucus [500500, enemy]: MP 8, power 0. Apply Slow (100%). Single enemies; MP 8; hits 1; accuracy 100; stagger 25.
- Confusega ← Confusega [235070, native]: MP 24, power 0. Apply Confusion (50%). Group enemies; MP 24; hits 1; accuracy 100; stagger 25.
- Maelstrom ← Maelstrom [500760, enemy]: MP 22, power 24. Water magic damage; power 24. Group enemies; MP 22; hits 1; accuracy 100; stagger 12.
- Blinding Light ← Flash [500820, enemy]: MP 18, power 0. Apply Blind (100%). Group enemies; MP 18; hits 1; accuracy 100; stagger 12.
- Oracle’s Censure ← Biased Examination [503170, enemy]: MP 50, power 0. Attempt to lower enemy attack, magic, defenses and speed. Group enemies; MP 50; hits 1; accuracy 100; stagger 12.
- Weakening Tide ← Splattering Flesh [503670, enemy]: MP 24, power 10. Water magic damage; power 10. Also lower enemy physical attack and defense. Group enemies; MP 24; hits 1; accuracy 100; stagger 12.
- Fading Tide ← Splattering Fluid [503680, enemy]: MP 24, power 10. Water magic damage; power 10. Also lower enemy magic and magic defense. Group enemies; MP 24; hits 1; accuracy 100; stagger 12.

### Minfilia — 4

Mixed earth/wind offense and party protection.

Sprite `214000304` (GL); base-stat budget: Onion Knight. Growth: Lightning.

- Awakening 1: Stone [220210]; Protect [230040]; Gale [485606]; Sandstorm [485609]; Quiet Recovery [485615]; Earthward [485630]; Throw [400240].
- Awakening 2: Stonera [220220]; Protectga [230050]; Petrifying Gaze [485612]; Warrior’s Blessing [485636].
- Awakening 3: Stonega [220230]; Blade Torrent [445200]; Calamity [485603]; Stonefall [485633].
- Awakening 4: Dual Jobs [485690].
- MR 1: Observe and Recover HP [1465].
- MR 2: Attack +5 (permanent).
- MR 3: Observe and Attack [1343].
- MR 4: AP +8 (permanent).
- MR 5: Job Change [1410].
- MR 6: MP +20 (permanent).
- MR 7: Late Bloomer [1411].
- MR 8: Magic +15 (permanent).
- MR 9: Chuck [1412]; AP +8 (permanent); Spirit of Minfilia.

Supplemental player copies (native source ID; final MP/power):

- Calamity ← Calamity [220240, native]: MP 35, power 30. Earth magic damage; power 30. Group enemies; MP 35; hits 3; accuracy 100; stagger 21.
- Gale ← Aero [225120, native]: MP 12, power 17. Wind magic damage; power 17. Group enemies; MP 12; hits 1; accuracy 100; stagger 17.
- Sandstorm ← Sandstorm [500320, enemy]: MP 12, power 12. Earth physical damage; power 12. Apply Blind (30%). Group enemies; MP 12; hits 2; accuracy 100; stagger 12.
- Petrifying Gaze ← Petrifying Gaze [500600, enemy]: MP 18, power 0. Apply Stoned (30%). Single enemies; MP 18; hits 1; accuracy 100; stagger 25.
- Quiet Recovery ← Groom [502610, enemy]: MP 5, power 100. Restore healing power 100. Self friendlies; MP 5; hits 1; accuracy 100; stagger 25.
- Earthward ← Stone [225150, native]: MP 12, power 17. Earth magic damage; power 17. Group enemies; MP 12; hits 1; accuracy 100; stagger 17.
- Stonefall ← Stonega [255170, enemy]: MP 28, power 24. Earth magic damage; power 24. Group enemies; MP 28; hits 3; accuracy 100; stagger 15.
- Warrior’s Blessing ← Red Wing Legacy [502730, enemy]: MP 14, power 0. Raise an ally’s attack by 50% for 3 turns. Single friendlies; MP 14; hits 1; accuracy 100; stagger 0.

### Folka — 6

Water magic with restorative utility.

Sprite `100018306` (GL); base-stat budget: Tronn. Growth: Terra.

- Awakening 1: Water [220130]; Syphon [220310]; Bio [485712]; Tidal Invocation [485718].
- Awakening 2: Watera [220140]; Aqua Breath [485703]; Poisonga [485715]; Rushing Tide [485739]; Oracle’s Blessing [485745].
- Awakening 3: Waterga [220150]; Regen [210050]; Hi Regen [414510]; Tidal Wave [485706]; Watera Tide [485709]; Sundering Deluge [485733]; Piercing Current [485736].
- Awakening 4: Waterga Tide [485730]; Restoring Mist [485742]; Waterga Surge [485721].
- MR 1: MP +10% [1380].
- MR 2: Mind +5 (permanent).
- MR 3: MP Stroll [1307].
- MR 4: AP +8 (permanent).
- MR 5: Imbue Water [1524].
- MR 6: MP +20 (permanent).
- MR 7: Water Eater [1348].
- MR 8: Magic +15 (permanent).
- MR 9: Water Immunity [1367]; AP +8 (permanent); Spirit of Folka.

Supplemental player copies (native source ID; final MP/power):

- Aqua Breath ← Aqua Breath [500800, enemy]: MP 20, power 18. Water magic damage; power 18. Group enemies; MP 20; hits 3; accuracy 100; stagger 12.
- Tidal Wave ← Tidal Wave [505130, enemy]: MP 32, power 36. Water magic damage; power 36. Group enemies; MP 32; hits 2; accuracy 100; stagger 12.
- Watera Tide ← Watera [225100, native]: MP 30, power 33. Water magic damage; power 33. Group enemies; MP 30; hits 2; accuracy 100; stagger 19.
- Bio ← Bio [250260, enemy]: MP 10, power 12. Non-elemental magic damage; power 12. Apply Poison (100%). Single enemies; MP 10; hits 1; accuracy 100; stagger 20.
- Poisonga ← Poisonga [225180, native]: MP 20, power 0. Apply Poison (100%). Group enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Waterga Tide ← Waterga [225110, native]: MP 60, power 55. Water magic damage; power 55. Group enemies; MP 60; hits 3; accuracy 100; stagger 21.
- Sundering Deluge ← Graceful Deluge [501410, enemy]: MP 28, power 26. Water magic damage; power 26. Apply DeffenceDown (100%), MindDown (100%). Group enemies; MP 28; hits 3; accuracy 100; stagger 12.
- Piercing Current ← Psycho Skewer [505320, enemy]: MP 36, power 40. Water magic damage; power 40. Single enemies; MP 36; hits 1; accuracy 100; stagger 25.
- Rushing Tide ← Watera [250140, enemy]: MP 22, power 22. Water magic damage; power 22. Random enemies; MP 22; hits 3; accuracy 100; stagger 19.
- Restoring Mist ← White Wind [500810, enemy]: MP 45, power 500. Restore healing power 500. Group friendlies; MP 45; hits 1; accuracy 100; stagger 50.
- Oracle’s Blessing ← Blue Wing Legacy [502710, enemy]: MP 14, power 0. Raise an ally’s magic by 50% for 3 turns. Single friendlies; MP 14; hits 1; accuracy 100; stagger 0.
- Tidal Invocation ← タイダルウェイブ(コロシアム) [571450, enemy]: MP 36, power 30. Water magic damage; power 30. Group enemies; MP 36; hits 4; accuracy 100; stagger 12.
- Waterga Surge ← Waterga [250150, enemy]: MP 30, power 30. Water magic damage; power 30. Group enemies; MP 30; hits 3; accuracy 100; stagger 21.

### Fryevia — 5

Ice spellblade and precision physical.

Sprite `302001405` (GL); base-stat budget: Bartz. Growth: Cloud.

- Awakening 1: Froststrike [421070]; Frozen Slumber Cut [485809]; Frostbind Cut [485812]; True Strike [485815]; Frozen Slash [485842].
- Awakening 2: Froststrike II [421080]; Golden Thrust [485818]; Dark Edge [485821]; Diamond Bind [485830]; Frozen Fang [485833]; Frost Pierce [485836]; Frost Sweep [485839]; Frost Dance [485824].
- Awakening 3: Froststrike III [421090]; Glint of Verglas [485803]; Stormbound Smite [485806].
- Awakening 4: Flare Blade [420270].
- MR 1: Knight of the Sacred Frost [1463].
- MR 2: Agility +5 (permanent).
- MR 3: Critical Focus [1539].
- MR 4: AP +8 (permanent).
- MR 5: Spellblade Wielder [1415].
- MR 6: HP +60 (permanent).
- MR 7: Spellblade Mastery [1416].
- MR 8: Attack +15 (permanent).
- MR 9: Dual Spellblade [1414]; AP +8 (permanent); Spirit of Fryevia.

Supplemental player copies (native source ID; final MP/power):

- Glint of Verglas ← Glint of Verglas [505380, enemy]: MP 35, power 40. Ice physical damage; power 40. Single enemies; MP 35; hits 2; accuracy 100; stagger 25.
- Stormbound Smite ← Stormbound Smite [505390, enemy]: MP 32, power 30. Ice physical damage; power 30. Group enemies; MP 32; hits 3; accuracy 100; stagger 12.
- Frozen Slumber Cut ← Sleep Slash [500630, enemy]: MP 10, power 18. Ice physical damage; power 18. Apply Sleep (50%). Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Frostbind Cut ← Paralysis Slash [500640, enemy]: MP 12, power 18. Ice physical damage; power 18. Apply Paralyzation (50%). Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- True Strike ← True Strike [500920, enemy]: MP 6, power 18. Non-elemental physical damage; power 18. Single enemies; MP 6; hits 1; accuracy 70; stagger 25.
- Golden Thrust ← Golden Lance [501600, enemy]: MP 14, power 24. Non-elemental physical damage; power 24. Single enemies; MP 14; hits 1; accuracy 100; stagger 25.
- Dark Edge ← Dark Edge [505260, enemy]: MP 20, power 24. Dark physical damage; power 24. Single enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Diamond Bind ← Petrifying Bite [502270, enemy]: MP 18, power 18. Ice physical damage; power 18. Apply Stoned (50%). Single enemies; MP 18; hits 1; accuracy 100; stagger 25.
- Frozen Fang ← Paralysis Fang [501670, enemy]: MP 20, power 24. Ice physical damage; power 24. Apply Paralyzation (100%). Single enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Frost Pierce ← Blizzara [250060, enemy]: MP 15, power 22. Ice physical damage; power 22. Single enemies; MP 15; hits 2; accuracy 100; stagger 19.
- Frost Sweep ← Blizzara [255040, enemy]: MP 20, power 18. Ice physical damage; power 18. Group enemies; MP 20; hits 2; accuracy 100; stagger 14.
- Frozen Slash ← Slash [500040, enemy]: MP 6, power 12. Ice physical damage; power 12. Single enemies; MP 6; hits 1; accuracy 100; stagger 25.
- Frost Dance ← Slash [501300, enemy]: MP 24, power 28. Ice physical damage; power 28. Single enemies; MP 24; hits 4; accuracy 100; stagger 25.

### Lenneth — 6

Physical cover tank with light attacks.

Sprite `330000106` (GL); base-stat budget: Warrior of Light. Growth: Cloud.

- Awakening 1: Vanguard Glaive [445010]; Banish Blade [420330]; Shield Crush [485903]; Repose [485915]; Guarding Bash [485936]; Shield Thrust [485939]; Multi-Cover [400390].
- Awakening 2: Banishra Blade [420340]; Guarding Smite [485906]; Lance Breaker [485912]; Valkyrie Ward [485948].
- Awakening 3: Sacred Wave [445020]; Banishga Blade [420350]; Sword Strike [485909]; Dawn Judgment [485930]; Luminant Purifier [485933]; Valkyrie Cleansing [485942]; Brave Lance [485945].
- Awakening 4: Vanguard Glaive+ [445030].
- MR 1: Protect Opener [1290].
- MR 2: Mind +5 (permanent).
- MR 3: Physical Counter [1029].
- MR 4: AP +8 (permanent).
- MR 5: Fill LB when Taking Damage [1331].
- MR 6: HP +60 (permanent).
- MR 7: Lustrous Shield [1408].
- MR 8: Defence +15 (permanent).
- MR 9: Heroic Nature [1409]; AP +8 (permanent); Spirit of Lenneth.

Supplemental player copies (native source ID; final MP/power):

- Shield Crush ← Crush [500020, enemy]: MP 10, power 18. Non-elemental physical damage; power 18. Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Guarding Smite ← Guarding Smite [505410, enemy]: MP 20, power 24. Non-elemental physical damage; power 24. Also defend after attacking. Single enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Sword Strike ← Sword Strike [503640, enemy]: MP 25, power 30. Non-elemental physical damage; power 30. Group enemies; MP 25; hits 1; accuracy 100; stagger 25.
- Lance Breaker ← Rib [500170, enemy]: MP 18, power 24. Non-elemental physical damage; power 24. Single enemies; MP 18; hits 1; accuracy 100; stagger 30.
- Repose ← Repose [502080, enemy]: MP 8, power 0. Raise own defenses while lowering attack and magic. Self friendlies; MP 8; hits 1; accuracy 100; stagger 0.
- Dawn Judgment ← Dawn of Judgment [505350, enemy]: MP 38, power 40. Light physical damage; power 40. Single enemies; MP 38; hits 1; accuracy 100; stagger 25.
- Luminant Purifier ← Luminant Purifier [505370, enemy]: MP 36, power 36. Light physical damage; power 36. Group enemies; MP 36; hits 1; accuracy 100; stagger 12.
- Guarding Bash ← Carapace [500930, enemy]: MP 12, power 18. Non-elemental physical damage; power 18. Also reduce own physical damage taken by 30% for 3 turns. Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- Shield Thrust ← Counter Horn [505100, enemy]: MP 10, power 18. Non-elemental physical damage; power 18. Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Valkyrie Cleansing ← Negation [505360, enemy]: MP 35, power 0. Remove party ailments and stat debuffs. Group friendlies; MP 35; hits 1; accuracy 100; stagger 12.
- Brave Lance ← Chomp [503810, enemy]: MP 32, power 40. Non-elemental physical damage; power 40. Single enemies; MP 32; hits 1; accuracy 100; stagger 20.
- Valkyrie Ward ← Show me majestic magic! [505530, enemy]: MP 20, power 0. Reduce own physical and magic damage taken by 30% for 3 turns. Self friendlies; MP 20; hits 1; accuracy 100; stagger 25.

### Lila — 6

Martial physical damage and self recovery.

Sprite `100013806` (GL); base-stat budget: Firion. Growth: Cloud.

- Awakening 1: Fire Slam [421010]; Fulminating Strike [445100]; Fist of Vigor [486003]; Heavy Palm [486033].
- Awakening 2: Fira Slam [421020]; Fist of Fortification [486006]; Fist of Fury [486009]; Crushing Grasp [486012]; Martial Reprisal [486030]; Sweeping Fists [486036]; Chakra [400440].
- Awakening 3: Firaga Slam [421030]; Saber of Adversity [445110]; Binding Grapple [486039].
- Awakening 4: Fulminating Strike+ [445120]; Arms Akimbo [400650].
- MR 1: HP +30% [1379].
- MR 2: HP +30 (permanent).
- MR 3: Restore HP on Stagger [1284].
- MR 4: AP +8 (permanent).
- MR 5: Bravery on Stagger [1288].
- MR 6: Agility +10 (permanent).
- MR 7: Nullify Instant Death [1325].
- MR 8: Attack +15 (permanent).
- MR 9: Light of Rebellion [1353]; AP +8 (permanent); Spirit of Lila.

Supplemental player copies (native source ID; final MP/power):

- Fist of Vigor ← Fist of Vigor [502230, enemy]: MP 12, power 14. Non-elemental physical damage; power 14. Also raise own attack by 50%. Single enemies; MP 12; hits 1; accuracy 100; stagger 17.
- Fist of Fortification ← Fist of Fortification [502370, enemy]: MP 20, power 18. Non-elemental physical damage; power 18. Also reduce own physical/magic damage taken by 30%. Single enemies; MP 20; hits 1; accuracy 100; stagger 17.
- Fist of Fury ← Fist of Fury [505060, enemy]: MP 14, power 24. Non-elemental physical damage; power 24. Single enemies; MP 14; hits 1; accuracy 100; stagger 25.
- Crushing Grasp ← Crushing Grasp [502240, enemy]: MP 22, power 28. Non-elemental physical damage; power 28. Apply Paralyzation (50%). Single enemies; MP 22; hits 1; accuracy 100; stagger 25.
- Martial Reprisal ← That is no martial skill! [505600, enemy]: MP 22, power 30. Non-elemental physical damage; power 30. Single enemies; MP 22; hits 1; accuracy 100; stagger 25.
- Heavy Palm ← Clobber [501850, enemy]: MP 10, power 18. Non-elemental physical damage; power 18. Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Sweeping Fists ← Wild Rage [505030, enemy]: MP 16, power 12. Non-elemental physical damage; power 12. Group enemies; MP 16; hits 4; accuracy 100; stagger 12.
- Binding Grapple ← Stranglehold [501030, enemy]: MP 22, power 24. Non-elemental physical damage; power 24. Apply Paralyzation (20%). Single enemies; MP 22; hits 1; accuracy 100; stagger 25.

### Mystea — 5

Magic tank, barriers and counter magic.

Sprite `100011005` (GL); base-stat budget: Cecil. Growth: Terra.

- Awakening 1: Shell [230060]; Light Ray [486112]; Dazing Mist [486118]; Magic Ward [486130]; Dark Pulse [486136].
- Awakening 2: Shellga [230070]; Manaward [220410]; Evasion Ward [486109]; Banishra Ray [486121]; Focused Dark Pulse [486139].
- Awakening 3: Reflect [230120]; Mighty Guard [486103]; Dystopia [486115]; Barrier Burst [486133].
- Awakening 4: Foul of the Seventh Dawn [220510].
- MR 1: Physical Defense +20% [1313].
- MR 2: HP +30 (permanent).
- MR 3: Magic Defense +20% [1315].
- MR 4: AP +8 (permanent).
- MR 5: Shell at Half HP [1299].
- MR 6: Defence +10 (permanent).
- MR 7: Magic Evasion +20% [1530].
- MR 8: Mind +15 (permanent).
- MR 9: Magic Counter [1030]; AP +8 (permanent); Spirit of Mystea.

Supplemental player copies (native source ID; final MP/power):

- Mighty Guard ← Mighty Guard [500860, enemy]: MP 40, power 0. Reduce party physical and magic damage taken by 30%. Group friendlies; MP 40; hits 1; accuracy 100; stagger 25.
- Evasion Ward ← Scatter Feathers [500700, enemy]: MP 20, power 0. Raise own physical evasion by 50%. Self friendlies; MP 20; hits 1; accuracy 100; stagger 25.
- Light Ray ← Laser [500310, enemy]: MP 10, power 18. Light magic damage; power 18. Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Dystopia ← Dystopia [505860, enemy]: MP 26, power 26. Dark magic damage; power 26. Group enemies; MP 26; hits 1; accuracy 100; stagger 12.
- Dazing Mist ← Pollen [500690, enemy]: MP 12, power 0. Apply Confusion (100%). Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- Banishra Ray ← Banishra [240240, enemy]: MP 15, power 22. Light magic damage; power 22. Single enemies; MP 15; hits 2; accuracy 100; stagger 19.
- Magic Ward ← Magic Warcry [505430, enemy]: MP 12, power 0. Reduce own magic damage taken by 30% for 3 turns. Self friendlies; MP 12; hits 1; accuracy 100; stagger 25.
- Barrier Burst ← Heavy Countermeasure [503980, enemy]: MP 35, power 36. Non-elemental magic damage; power 36. Group enemies; MP 35; hits 1; accuracy 100; stagger 12.
- Dark Pulse ← Dark [255260, enemy]: MP 12, power 12. Dark magic damage; power 12. Group enemies; MP 12; hits 1; accuracy 100; stagger 17.
- Focused Dark Pulse ← Darkra [250520, enemy]: MP 18, power 22. Dark magic damage; power 22. Single enemies; MP 18; hits 2; accuracy 100; stagger 19.

### Reberta (JP) — 5

Dragoon with fire/wind spear attacks.

Sprite `100014405` (GL); base-stat budget: Clive. Growth: Cloud.

- Awakening 1: Fire Surge [421040]; Aero Surge [421310]; Breath Wing [486203]; Dragoon Cleave [486215].
- Awakening 2: Fira Surge [421050]; Aerora Surge [421320]; Rising Flames [448000]; Flame Lance [486212]; Flame Lance Volley [486230]; Carmine Lance [486236].
- Awakening 3: Firaga Surge [421060]; Aeroga Surge [421330]; Heatwave [448010]; Silver Lance [486206]; Branch Spear [486209]; Blistering Hellfire [486233]; Dragonfire Breath [486239].
- Awakening 4: Mirage [400670].
- MR 1: Opening Honed Senses [1507].
- MR 2: HP +30 (permanent).
- MR 3: Reflex [1257].
- MR 4: AP +8 (permanent).
- MR 5: Fill LB on Defeating Foes [1320].
- MR 6: Agility +10 (permanent).
- MR 7: Bonus Damage [1335].
- MR 8: Attack +15 (permanent).
- MR 9: Clive’s Limit Break [1442]; AP +8 (permanent); Spirit of Reberta (JP).

Supplemental player copies (native source ID; final MP/power):

- Breath Wing ← Breath Wing [500460, enemy]: MP 12, power 12. Wind physical damage; power 12. Group enemies; MP 12; hits 3; accuracy 100; stagger 12.
- Silver Lance ← Silver Lance [501260, enemy]: MP 25, power 36. Non-elemental physical damage; power 36. Single enemies; MP 25; hits 1; accuracy 100; stagger 25.
- Branch Spear ← Branch Spear [503780, enemy]: MP 25, power 36. Earth physical damage; power 36. Single enemies; MP 25; hits 1; accuracy 100; stagger 20.
- Flame Lance ← Spew Flames [502010, enemy]: MP 20, power 24. Fire physical damage; power 24. Single enemies; MP 20; hits 3; accuracy 100; stagger 25.
- Flame Lance Volley ← Flame Thrower [500370, enemy]: MP 16, power 18. Fire physical damage; power 18. Single enemies; MP 16; hits 3; accuracy 100; stagger 25.
- Blistering Hellfire ← Blistering Hellfire [505330, enemy]: MP 32, power 30. Fire physical damage; power 30. Group enemies; MP 32; hits 1; accuracy 100; stagger 12.
- Carmine Lance ← Carmine Inferno [505340, enemy]: MP 20, power 24. Fire physical damage; power 24. Single enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Dragonfire Breath ← Flame Breath [501880, enemy]: MP 40, power 40. Fire magic damage; power 40. Group enemies; MP 40; hits 1; accuracy 100; stagger 12.
- Dragoon Cleave ← Rake [500130, enemy]: MP 16, power 22. Non-elemental physical damage; power 22. Single enemies; MP 16; hits 1; accuracy 100; stagger 25.

### Snow White — 7

Dark physical drain and risk/reward.

Sprite `336000207` (GL); base-stat budget: Cecil. Growth: Cloud.

- Awakening 1: Dark Blade [420300]; Leech [486303]; Crimson Bite [486330]; Venom Gash [486333]; Nightcut [486336]; Slumber Gash [486339]; Darkness [400490].
- Awakening 2: Darkra Blade [420310]; Sleep Slam [422020]; Drain [220300]; Predation [486306]; Revenge Strike [486312]; Binding Sweep [486315]; Crimson Sweep [486345]; Blood Recovery [486348].
- Awakening 3: Drain Knife [422040]; Darkga Blade [420320]; Purging Blade [486309]; Hell Gate [486342].
- MR 1: Restore HP on Defeating Foes [1318].
- MR 2: HP +30 (permanent).
- MR 3: Vigorous Attacks [1358].
- MR 4: AP +8 (permanent).
- MR 5: Staggeringly Risky [1405].
- MR 6: Defence +10 (permanent).
- MR 7: Dark Rite [1431].
- MR 8: Attack +15 (permanent).
- MR 9: Dark Sword [1457]; AP +8 (permanent); Spirit of Snow White.

Supplemental player copies (native source ID; final MP/power):

- Leech ← Leech [500520, enemy]: MP 12, power 12. Non-elemental physical damage; power 12. Apply HP drain (100% of damage). Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- Predation ← Predation [570710, enemy]: MP 16, power 18. Non-elemental physical damage; power 18. Apply HP drain (100% of damage). Single enemies; MP 16; hits 1; accuracy 100; stagger 20.
- Purging Blade ← Purging Blade [505960, enemy]: MP 32, power 36. Dark physical damage; power 36. Also reduce enemy physical and magic defense. Single enemies; MP 32; hits 1; accuracy 100; stagger 16.
- Revenge Strike ← Revenge Blast [501630, enemy]: MP 16, power 24. Non-elemental physical damage; power 24. Single enemies; MP 16; hits 1; accuracy 100; stagger 25.
- Binding Sweep ← Cling [500910, enemy]: MP 14, power 12. Non-elemental physical damage; power 12. Apply Slow (30%). Group enemies; MP 14; hits 1; accuracy 100; stagger 12.
- Crimson Bite ← Incisors [500510, enemy]: MP 10, power 18. Dark physical damage; power 18. Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Venom Gash ← Regurgitate [570640, enemy]: MP 12, power 15. Dark physical damage; power 15. Apply Poison (100%). Single enemies; MP 12; hits 1; accuracy 100; stagger 0.
- Nightcut ← Regurgitate [570660, enemy]: MP 12, power 15. Dark physical damage; power 15. Apply Blind (100%). Single enemies; MP 12; hits 1; accuracy 100; stagger 0.
- Slumber Gash ← Regurgitate [570670, enemy]: MP 12, power 15. Dark physical damage; power 15. Apply Sleep (100%). Single enemies; MP 12; hits 1; accuracy 100; stagger 0.
- Hell Gate ← Hell’s Gate [505970, enemy]: MP 30, power 30. Dark physical damage; power 30. Group enemies; MP 30; hits 1; accuracy 100; stagger 12.
- Crimson Sweep ← Darkra [255280, enemy]: MP 20, power 18. Dark physical damage; power 18. Group enemies; MP 20; hits 2; accuracy 100; stagger 14.
- Blood Recovery ← 捕食(1000回復) [501530, enemy]: MP 18, power 400. Restore 400 HP. Self friendlies; MP 18; hits 1; accuracy 100; stagger 25.

### Aria — 5

Water support, healing and water blade.

Sprite `203000905` (GL); base-stat budget: Leah. Growth: Terra.

- Awakening 1: Water Blade [420100]; Cure of the Seventh Dawn [220480]; Healing Rain [486403]; Rejuvenate [486409]; Banish Ray [486418]; Water Chorus [486430]; Aether Current [486421].
- Awakening 2: Watera Blade [420110]; Cure II of the Seventh Dawn [220490]; Purify [414500]; Soothing Rain [486406]; Undertow [486412]; Bubble Breath [486415]; Cleansing Miasma [486436]; Mist Veil [486442].
- Awakening 3: Waterga Blade [420120]; Cure III of the Seventh Dawn [220500]; Ocean Requiem [486433]; Radiant Pulse [486439]; Waterdrop [486424].
- Awakening 4: Soothing Current [486427].
- MR 1: Nullify Poison [1104].
- MR 2: MP +10 (permanent).
- MR 3: Resist Water [1251].
- MR 4: AP +8 (permanent).
- MR 5: MP +20% [1381].
- MR 6: Magic +10 (permanent).
- MR 7: Magic Attack +20% [1311].
- MR 8: Mind +15 (permanent).
- MR 9: Imbue Light [1527]; AP +8 (permanent); Spirit of Aria.

Supplemental player copies (native source ID; final MP/power):

- Healing Rain ← Cure [245000, enemy]: MP 10, power 80. Restore healing power 80. Group friendlies; MP 10; hits 1; accuracy 100; stagger 20.
- Soothing Rain ← Cura [245010, enemy]: MP 18, power 200. Restore healing power 200. Group friendlies; MP 18; hits 1; accuracy 100; stagger 22.
- Rejuvenate ← Rejuvenate [502020, enemy]: MP 12, power 20. Restore 20% max HP. Self friendlies; MP 12; hits 1; accuracy 100; stagger 25.
- Undertow ← Graceful Deluge [501400, enemy]: MP 20, power 12. Water magic damage; power 12. Also reduce enemy physical and magic defense. Group enemies; MP 20; hits 3; accuracy 100; stagger 12.
- Bubble Breath ← Bubble Breath [501680, enemy]: MP 24, power 24. Water magic damage; power 24. Group enemies; MP 24; hits 3; accuracy 100; stagger 12.
- Banish Ray ← Banish [240230, enemy]: MP 5, power 14. Light magic damage; power 14. Single enemies; MP 5; hits 1; accuracy 100; stagger 17.
- Water Chorus ← Water [225090, native]: MP 12, power 17. Water magic damage; power 17. Group enemies; MP 12; hits 1; accuracy 100; stagger 17.
- Ocean Requiem ← Graceful Deluge [501440, enemy]: MP 40, power 40. Water magic damage; power 40. Apply DeffenceDown (100%), MindDown (100%). Group enemies; MP 40; hits 3; accuracy 100; stagger 12.
- Cleansing Miasma ← Bio [255190, enemy]: MP 20, power 12. Non-elemental magic damage; power 12. Apply Poison (100%). Group enemies; MP 20; hits 1; accuracy 100; stagger 12.
- Radiant Pulse ← 連続ホーリー [503870, enemy]: MP 36, power 40. Light magic damage; power 40. Single enemies; MP 36; hits 1; accuracy 100; stagger 40.
- Mist Veil ← Darkness Powder [570820, enemy]: MP 20, power 0. Apply Blind (100%). Group enemies; MP 20; hits 1; accuracy 100; stagger 12.
- Aether Current ← (ボスカウンター用)アスピル [503970, enemy]: MP 8, power 6. Drain MP; power 6. Apply MP drain (100% of damage). Single enemies; MP 8; hits 1; accuracy 100; stagger 20.
- Waterdrop ← Water [250130, enemy]: MP 6, power 14. Water magic damage; power 14. Single enemies; MP 6; hits 1; accuracy 100; stagger 17.
- Soothing Current ← Regurgitate [570620, enemy]: MP 14, power 200. Restore 200 HP. Single friendlies; MP 14; hits 1; accuracy 100; stagger 0.

### Eiko — 7

Summoner with wind magic and revival.

Sprite `209000707` (GL); base-stat budget: Ayaka. Growth: Terra.

- Awakening 1: Aero of the Seventh Dawn [220450]; Light of the Eidolons [486530].
- Awakening 2: Aero II of the Seventh Dawn [220460]; Raise [210140].
- Awakening 3: Ifrit [430990]; Shiva [431000]; Aero III of the Seventh Dawn [220470]; Banishga Ray [486509]; Aerora Gust [486512]; Healing Breeze [486515]; Focused Gale [486539].
- Awakening 4: Reraise [210160]; Firaga Burst [486503]; Blizzaga Burst [486506]; Eidolon Radiance [486533]; Guardian’s Earth [486536]; Guardian’s Lightning [486542].
- MR 1: Double EXP [1009].
- MR 2: Mind +5 (permanent).
- MR 3: Nullify Silence [1107].
- MR 4: AP +8 (permanent).
- MR 5: Recuperate LB [1338].
- MR 6: MP +20 (permanent).
- MR 7: Peaceful LB Engine [1498].
- MR 8: Magic +15 (permanent).
- MR 9: LB Triple Charge [1031]; AP +8 (permanent); Spirit of Eiko.

Supplemental player copies (native source ID; final MP/power):

- Firaga Burst ← Firaga [225020, native]: MP 60, power 55. Fire magic damage; power 55. Group enemies; MP 60; hits 3; accuracy 100; stagger 21.
- Blizzaga Burst ← Blizzaga [225050, native]: MP 60, power 55. Ice magic damage; power 55. Group enemies; MP 60; hits 3; accuracy 100; stagger 21.
- Banishga Ray ← Banishga [240250, enemy]: MP 25, power 30. Light magic damage; power 30. Single enemies; MP 25; hits 3; accuracy 100; stagger 21.
- Aerora Gust ← Aerora [225130, native]: MP 30, power 33. Wind magic damage; power 33. Group enemies; MP 30; hits 2; accuracy 100; stagger 19.
- Healing Breeze ← Curaga [245020, enemy]: MP 35, power 600. Restore healing power 600. Group friendlies; MP 35; hits 1; accuracy 100; stagger 25.
- Light of the Eidolons ← Banish [225290, native]: MP 12, power 17. Light magic damage; power 17. Group enemies; MP 12; hits 1; accuracy 100; stagger 17.
- Eidolon Radiance ← Banishga [225310, native]: MP 60, power 55. Light magic damage; power 55. Group enemies; MP 60; hits 3; accuracy 100; stagger 21.
- Guardian’s Earth ← Stonega [225170, native]: MP 60, power 55. Earth magic damage; power 55. Group enemies; MP 60; hits 3; accuracy 100; stagger 21.
- Focused Gale ← Aeroga [250190, enemy]: MP 25, power 30. Wind magic damage; power 30. Single enemies; MP 25; hits 3; accuracy 100; stagger 21.
- Guardian’s Lightning ← Thundaga [225080, native]: MP 60, power 55. Thunder magic damage; power 55. Group enemies; MP 60; hits 3; accuracy 100; stagger 21.

### Alice/Half Nightmare — NV Brave Shift

Ice physical with burst and HP tradeoffs.

Sprite `336000127` (JP); base-stat budget: Squall. Growth: Cloud.

- Awakening 1: Ice Slam [486660]; Boundless Void [446300]; Rage [486606]; Throat Strike [486609]; Binding Cut [486618]; Hail Cut [486639]; Twin Frost Blades [486642]; Deathblow [400530].
- Awakening 2: Icera Slam [486663]; Disorienting Cut [486615]; Frost Reprisal [486633].
- Awakening 3: Icega Slam [486666]; Purging Blade [446310]; Absolving Hail [486603]; Ruthless Rampage [486612]; Nightmare Flurry [486630]; Frozen Finale [486636].
- MR 1: Nullify Sleep [1106].
- MR 2: HP +30 (permanent).
- MR 3: Critical Hit Rate +10% [1247].
- MR 4: AP +8 (permanent).
- MR 5: Critical Boost [1234].
- MR 6: Agility +10 (permanent).
- MR 7: Bravery Opener [1294].
- MR 8: Attack +15 (permanent).
- MR 9: Critical Stagger [1388]; AP +8 (permanent); Spirit of Alice/Half Nightmare.

Supplemental player copies (native source ID; final MP/power):

- Absolving Hail ← Absolving Hailstorm [505840, enemy]: MP 32, power 30. Ice physical damage; power 30. Group enemies; MP 32; hits 3; accuracy 100; stagger 12.
- Rage ← Rage [501700, enemy]: MP 10, power 0. Raise own attack and magic by 50%, lowering both defenses. Self friendlies; MP 10; hits 1; accuracy 100; stagger 0.
- Throat Strike ← Throat Strike [500250, enemy]: MP 10, power 18. Non-elemental physical damage; power 18. Apply Silence (50%). Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Ruthless Rampage ← Ruthless Rampage [502030, enemy]: MP 30, power 18. Non-elemental physical damage; power 18. Apply Paralyzation (50%), Blind (50%), Silence (50%). Group enemies; MP 30; hits 4; accuracy 100; stagger 25.
- Disorienting Cut ← Slap [500620, enemy]: MP 18, power 24. Ice physical damage; power 24. Apply Charme (100%). Single enemies; MP 18; hits 2; accuracy 100; stagger 25.
- Binding Cut ← Paralysis Needle [500290, enemy]: MP 8, power 12. Non-elemental physical damage; power 12. Apply Paralyzation (100%). Single enemies; MP 8; hits 1; accuracy 100; stagger 25.
- Ice Slam ← Blizzard Surge [421370, native]: MP 5, power 12. Ice physical damage; power 12. Single enemies; MP 5; hits 1; accuracy 100; stagger 25.
- Icera Slam ← Blizzara Surge [421380, native]: MP 15, power 24. Ice physical damage; power 24. Single enemies; MP 15; hits 1; accuracy 100; stagger 28.
- Icega Slam ← Blizzaga Surge [421390, native]: MP 44, power 39. Ice physical damage; power 39. Single enemies; MP 44; hits 1; accuracy 100; stagger 30.
- Nightmare Flurry ← Whack and Smack [502200, enemy]: MP 36, power 28. Ice physical damage; power 28. Apply Poison (50%), Blind (50%), Silence (50%). Random enemies; MP 36; hits 4; accuracy 100; stagger 25.
- Frost Reprisal ← That is no magic! [505610, enemy]: MP 22, power 30. Ice physical damage; power 30. Single enemies; MP 22; hits 1; accuracy 100; stagger 25.
- Frozen Finale ← Regurgitate [570680, enemy]: MP 38, power 40. Ice physical damage; power 40. Single enemies; MP 38; hits 1; accuracy 100; stagger 0.
- Hail Cut ← Blizzard [255030, enemy]: MP 12, power 12. Ice physical damage; power 12. Group enemies; MP 12; hits 1; accuracy 100; stagger 12.
- Twin Frost Blades ← Tentacle [500580, enemy]: MP 12, power 18. Ice physical damage; power 18. Apply Slow (50%). Single enemies; MP 12; hits 2; accuracy 100; stagger 25.

### Moogle of Narshe Mog — 5

Wind magic, dance and speed support.

Sprite `206003005` (GL); base-stat budget: Tidus. Growth: Terra.

- Awakening 1: Aero [220170]; Haste [230130]; Gust Dance [486703]; Mystery Waltz [486709]; Berserker Step [486733]; Wait [400760].
- Awakening 2: Aerora [220180]; Cyclone [486706]; Mega Berserk [486715]; Gale Dance [486736].
- Awakening 3: Aeroga [220190]; Slow [230150]; Alluring Dance [486712]; Heavenly Wind [486730].
- Awakening 4: Slowga [230160]; Hastega [230140].
- MR 1: Speed +5% [1316].
- MR 2: Magic +5 (permanent).
- MR 3: Haste on Stagger [1287].
- MR 4: AP +8 (permanent).
- MR 5: Speed +10% [1277].
- MR 6: MP +20 (permanent).
- MR 7: Opening Good Luck [1511].
- MR 8: Agility +15 (permanent).
- MR 9: First Strike [1049]; AP +8 (permanent); Spirit of Moogle of Narshe Mog.

Supplemental player copies (native source ID; final MP/power):

- Gust Dance ← Wind Slash [500430, enemy]: MP 12, power 12. Wind magic damage; power 12. Group enemies; MP 12; hits 1; accuracy 100; stagger 12.
- Cyclone ← Cyclone [500410, enemy]: MP 22, power 24. Wind magic damage; power 24. Group enemies; MP 22; hits 1; accuracy 100; stagger 12.
- Mystery Waltz ← Mystery Waltz [570450, enemy]: MP 12, power 10. Drain MP; power 10. Apply MP drain (100% of damage). Single enemies; MP 12; hits 1; accuracy 100; stagger 0.
- Alluring Dance ← Alluring Dance [570430, enemy]: MP 32, power 0. Apply Charme (100%). Group enemies; MP 32; hits 1; accuracy 100; stagger 0.
- Mega Berserk ← Mega Berserk [235080, native]: MP 22, power 0. Apply Berserk (100%). Group enemies; MP 22; hits 1; accuracy 100; stagger 25.
- Heavenly Wind ← Heavenly Wind [505280, enemy]: MP 40, power 40. Wind magic damage; power 40. Group enemies; MP 40; hits 1; accuracy 100; stagger 12.
- Berserker Step ← Berserk [570410, enemy]: MP 6, power 0. Apply Berserk (100%). Single enemies; MP 6; hits 1; accuracy 100; stagger 0.
- Gale Dance ← 大魔法マグヌム・オプス(風) [503920, enemy]: MP 22, power 20. Wind magic damage; power 20. Group enemies; MP 22; hits 3; accuracy 100; stagger 21.

### Lilith — 5

Dark counter tank and protective magic.

Sprite `401005905` (GL); base-stat budget: Cecil. Growth: Cloud.

- Awakening 1: Dark [220390]; Vampiric Lash [486836]; Cover [400380].
- Awakening 2: Darkra [220520]; Power Stagger [414600]; Poison Mist [486812]; Shock Claw [486815].
- Awakening 3: Darkga [220400]; Shadowbringer [445310]; Royal Guard [414610]; Seal of Conviction [486803]; Dark Sunder [486806]; Dark Aegis [486809].
- Awakening 4: Nihilistic Solitude [486830]; Obsidian Vortex [486833]; Dark Feast [486839].
- MR 1: Damage Reduction +20% [1513].
- MR 2: HP +30 (permanent).
- MR 3: Dark Immunity [1369].
- MR 4: AP +8 (permanent).
- MR 5: Riposte [1339].
- MR 6: Mind +10 (permanent).
- MR 7: Critical Counter [1333].
- MR 8: Defence +15 (permanent).
- MR 9: Paladin’s Code [1413]; AP +8 (permanent); Spirit of Lilith.

Supplemental player copies (native source ID; final MP/power):

- Seal of Conviction ← Seal of Conviction [505580, enemy]: MP 32, power 30. Dark physical damage; power 30. Group enemies; MP 32; hits 2; accuracy 100; stagger 12.
- Dark Sunder ← Darkness’s Dawn [505560, enemy]: MP 28, power 0. Reduce enemy physical and magic defense by 30% for 3 turns. Group enemies; MP 28; hits 1; accuracy 100; stagger 12.
- Dark Aegis ← Darkness’s Advance [505570, enemy]: MP 40, power 0. Reduce party physical and magic damage taken by 30%. Group friendlies; MP 40; hits 1; accuracy 100; stagger 25.
- Poison Mist ← Poison Gas [500560, enemy]: MP 18, power 0. Apply Poison (50%). Group enemies; MP 18; hits 1; accuracy 100; stagger 12.
- Shock Claw ← Shock Claw [503240, enemy]: MP 22, power 28. Non-elemental physical damage; power 28. Apply Paralyzation (100%). Single enemies; MP 22; hits 1; accuracy 100; stagger 25.
- Nihilistic Solitude ← Nihilistic Solitude [506040, enemy]: MP 30, power 24. Dark magic damage; power 24. Also remove enemy buffs. Group enemies; MP 30; hits 1; accuracy 100; stagger 12.
- Obsidian Vortex ← Obsidian Vortex [505550, enemy]: MP 30, power 0. Apply Confusion (100%). Group enemies; MP 30; hits 1; accuracy 100; stagger 12.
- Vampiric Lash ← Vampiric Lash [571110, enemy]: MP 12, power 12. Dark physical damage; power 12. Apply HP drain (100% of damage). Single enemies; MP 12; hits 2; accuracy 100; stagger 25.
- Dark Feast ← Feed [503700, enemy]: MP 35, power 40. Dark magic damage; power 40. Apply HP drain (100% of damage). Single enemies; MP 35; hits 1; accuracy 100; stagger 20.

### Dragon Knight Freya — 5

Aerial light physical and water lance.

Sprite `209001805` (GL); base-stat budget: Noctis. Growth: Cloud.

- Awakening 1: Water Surge [421190]; Flash Flood [486906]; Sonic Boom [486918]; Lance Thrust [486930]; Splash Lance [486939]; Mana Lance [486921].
- Awakening 2: Warp-Strike [447810]; Watera Surge [421200]; Crystal Lance [486903]; Venom Lance [486915]; Lance Storm [486933]; Cleansing Lance [486936]; Tidal Lance [486942].
- Awakening 3: Plunge [447800]; Waterga Surge [421210]; Gungnir [486909]; Hydro Lance [486912]; Ocean Lance [486945].
- MR 1: Nullify Slow [1116].
- MR 2: HP +30 (permanent).
- MR 3: Fire Immunity [1362].
- MR 4: AP +8 (permanent).
- MR 5: Deft Warp [1361].
- MR 6: Agility +10 (permanent).
- MR 7: Warp Crit [1466].
- MR 8: Attack +15 (permanent).
- MR 9: Leaping Cleave [1357]; AP +8 (permanent); Spirit of Dragon Knight Freya.

Supplemental player copies (native source ID; final MP/power):

- Crystal Lance ← Crystal Lance [501610, enemy]: MP 20, power 30. Non-elemental physical damage; power 30. Single enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Flash Flood ← Flash Flood [500770, enemy]: MP 12, power 18. Water physical damage; power 18. Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- Gungnir ← Gungnir [505810, enemy]: MP 40, power 40. Non-elemental physical damage; power 40. Single enemies; MP 40; hits 1; accuracy 100; stagger 25.
- Hydro Lance ← Hydro Breath [503830, enemy]: MP 26, power 28. Water physical damage; power 28. Group enemies; MP 26; hits 1; accuracy 100; stagger 20.
- Venom Lance ← Poison Tail [500870, enemy]: MP 15, power 24. Non-elemental physical damage; power 24. Apply Poison (100%). Single enemies; MP 15; hits 1; accuracy 100; stagger 25.
- Sonic Boom ← Sonic Boom [500440, enemy]: MP 12, power 18. Wind physical damage; power 18. Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- Lance Thrust ← Stab [500090, enemy]: MP 10, power 18. Non-elemental physical damage; power 18. Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Lance Storm ← Stab [502600, enemy]: MP 24, power 34. Non-elemental physical damage; power 34. Single enemies; MP 24; hits 1; accuracy 100; stagger 25.
- Cleansing Lance ← Clear Smog [571140, enemy]: MP 22, power 12. Water physical damage; power 12. Also remove enemy buffs. Group enemies; MP 22; hits 1; accuracy 100; stagger 25.
- Splash Lance ← Water [255090, enemy]: MP 12, power 12. Water physical damage; power 12. Group enemies; MP 12; hits 1; accuracy 100; stagger 12.
- Tidal Lance ← Watera [255100, enemy]: MP 20, power 18. Water physical damage; power 18. Group enemies; MP 20; hits 2; accuracy 100; stagger 14.
- Ocean Lance ← Waterga [255110, enemy]: MP 28, power 24. Water physical damage; power 24. Group enemies; MP 28; hits 3; accuracy 100; stagger 15.
- Mana Lance ← Giga-Syphon [503690, enemy]: MP 12, power 10. Drain MP; power 10. Apply MP drain (100% of damage). Single enemies; MP 12; hits 1; accuracy 100; stagger 20.

### Trance Terra — 5

Dark/fire magic, poison and costly finishers.

Sprite `206000125` (GL); base-stat budget: Shantotto. Growth: Terra.

- Awakening 1: Poison [220250]; Fire [220010].
- Awakening 2: Nightmare Scythe [447300]; Bio [220260]; Fira [220020]; Firaga [220030].
- Awakening 3: Salvation Scythe [447310]; Death [220320]; Meltdown [220380]; Spill [487103]; Trance Judgment [487106]; Judgment Shadow [487109]; Hell Pillar [487112]; Trance Apocalypse [487130].
- Awakening 4: Meteor [220350]; Ultima [220340]; Dualcast [400730].
- MR 1: Fire Eater [1038].
- MR 2: Agility +5 (permanent).
- MR 3: Restore MP on Defeating Foes [1319].
- MR 4: AP +8 (permanent).
- MR 5: The Federation’s Fiend [1432].
- MR 6: MP +20 (permanent).
- MR 7: Area Effect Adept [1351].
- MR 8: Magic +15 (permanent).
- MR 9: Play Rough [1433]; AP +8 (permanent); Spirit of Trance Terra.

Supplemental player copies (native source ID; final MP/power):

- Spill ← Spill [414300, native]: MP 46, power 45. Dark magic damage; power 45. Group enemies; MP 46; hits 2; accuracy 100; stagger 35.
- Trance Judgment ← Execution [505450, enemy]: MP 35, power 36. Dark magic damage; power 36. Group enemies; MP 35; hits 3; accuracy 100; stagger 12.
- Judgment Shadow ← Judgment of the Shadow [503120, enemy]: MP 30, power 30. Non-elemental magic damage; power 30. Group enemies; MP 30; hits 1; accuracy 100; stagger 25.
- Hell Pillar ← Hell’s Pillar [505470, enemy]: MP 26, power 24. Fire magic damage; power 24. Group enemies; MP 26; hits 3; accuracy 100; stagger 12.
- Trance Apocalypse ← Ray of Apocalypse [505540, enemy]: MP 40, power 40. Non-elemental magic damage; power 40. Group enemies; MP 40; hits 1; accuracy 100; stagger 12.

### Charming Kitty Ariana — 5

Healing singer with control and arcane attacks.

Sprite `401002405` (GL); base-stat budget: Ayaka. Growth: Terra.

- Awakening 1: Esuna [210120]; Bravery [230100]; Healing Refrain [487203]; Lullaby [487209]; Wind Aria [487233]; Focus [400460].
- Awakening 2: Blindga [487212]; Silencega [487215]; Starlight Refrain [487218]; Wind Refrain [487236]; Flame Refrain [487242].
- Awakening 3: Gravity [220280]; Restoring Refrain [487206]; Dimming Refrain [487230]; Winter Refrain [487239]; Dazzling Refrain [487221].
- Awakening 4: Confuse [230180]; Graviga [220290].
- MR 1: Nullify Blind [1105].
- MR 2: Magic +5 (permanent).
- MR 3: Nullify Berserk [1114].
- MR 4: AP +8 (permanent).
- MR 5: Regen Opener [1293].
- MR 6: MP +20 (permanent).
- MR 7: Growing Good Luck [1499].
- MR 8: Mind +15 (permanent).
- MR 9: Double Gil [1050]; AP +8 (permanent); Spirit of Charming Kitty Ariana.

Supplemental player copies (native source ID; final MP/power):

- Healing Refrain ← Cure [215000, native]: MP 12, power 200. Restore healing power 200. Group friendlies; MP 12; hits 1; accuracy 100; stagger 50.
- Restoring Refrain ← Cura [215010, native]: MP 25, power 500. Restore healing power 500. Group friendlies; MP 25; hits 1; accuracy 100; stagger 55.
- Lullaby ← Lullaby [570440, enemy]: MP 8, power 0. Apply Sleep (100%). Single enemies; MP 8; hits 1; accuracy 100; stagger 0.
- Blindga ← Blindga [235010, native]: MP 20, power 0. Apply Blind (50%). Group enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Silencega ← Silencega [235020, native]: MP 20, power 0. Apply Silence (50%). Group enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Starlight Refrain ← Array: Light of Destruction [503620, enemy]: MP 24, power 28. Light magic damage; power 28. Group enemies; MP 24; hits 1; accuracy 100; stagger 12.
- Dimming Refrain ← Flamewall [506120, enemy]: MP 34, power 30. Fire magic damage; power 30. Apply AttackDown (100%), IntelligenceDown (100%). Group enemies; MP 34; hits 3; accuracy 100; stagger 21.
- Wind Aria ← Aero [250170, enemy]: MP 5, power 14. Wind magic damage; power 14. Single enemies; MP 5; hits 1; accuracy 100; stagger 17.
- Wind Refrain ← Aerora [250180, enemy]: MP 15, power 22. Wind magic damage; power 22. Single enemies; MP 15; hits 2; accuracy 100; stagger 19.
- Winter Refrain ← Blizzaga [255050, enemy]: MP 28, power 24. Ice magic damage; power 24. Group enemies; MP 28; hits 3; accuracy 100; stagger 15.
- Flame Refrain ← 大魔法マグヌム・オプス(火) [503910, enemy]: MP 22, power 20. Fire magic damage; power 20. Group enemies; MP 22; hits 3; accuracy 100; stagger 21.
- Dazzling Refrain ← Alluring Pollen [503770, enemy]: MP 30, power 24. Non-elemental magic damage; power 24. Apply Confusion (50%), Charme (50%), Silence (50%), Blind (50%). Group enemies; MP 30; hits 1; accuracy 100; stagger 20.

### Elephim — 7

Buff/debuff bard with ranged attacks.

Sprite `100017107` (GL); base-stat budget: Vaan. Growth: Terra.

- Awakening 1: Debrave [230190]; Blind [230020]; Faith [230110]; Berserk [230170]; Sleep [487303]; Defaith [487306]; Resonant Notes [487327].
- Awakening 2: Rapid Fire [414200]; Debravega [487309]; Defaithga [487312]; Sleepga [487315]; Flame Chant [487330].
- Awakening 3: Disorder [414210]; Berserker Samba [487324]; Harp Volley [487333].
- Awakening 4: Inspire [487321]; Rallying Song [487318].
- MR 1: Resist Lightning [1250].
- MR 2: Mind +5 (permanent).
- MR 3: Deshell on Stagger [1285].
- MR 4: AP +8 (permanent).
- MR 5: Deprotect on Stagger [1235].
- MR 6: MP +20 (permanent).
- MR 7: Haste Opener [1292].
- MR 8: Agility +15 (permanent).
- MR 9: Gil Farmer on Stagger [1386]; AP +8 (permanent); Spirit of Elephim.

Supplemental player copies (native source ID; final MP/power):

- Sleep ← Sleep [230010, native]: MP 5, power 0. Apply Sleep (80%). Single enemies; MP 5; hits 1; accuracy 100; stagger 25.
- Defaith ← Defaith [230200, native]: MP 6, power 0. Apply IntelligenceDown (100%). Single enemies; MP 6; hits 1; accuracy 100; stagger 25.
- Debravega ← Debravega [235050, native]: MP 24, power 0. Apply AttackDown (100%). Group enemies; MP 24; hits 1; accuracy 100; stagger 25.
- Defaithga ← Defaithga [235060, native]: MP 24, power 0. Apply IntelligenceDown (100%). Group enemies; MP 24; hits 1; accuracy 100; stagger 25.
- Sleepga ← Sleepga [235000, native]: MP 20, power 0. Apply Sleep (50%). Group enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Rallying Song ← Get them! [501120, enemy]: MP 45, power 0. Raise party magic and speed by 50%. Group friendlies; MP 45; hits 0; accuracy 100; stagger 25.
- Inspire ← Inspire [570130, enemy]: MP 42, power 0. Raise an ally’s attack/magic by 50% and reduce incoming physical/magic damage by 30%. Single friendlies; MP 42; hits 1; accuracy 100; stagger 0.
- Berserker Samba ← Samba de Flan [570420, enemy]: MP 28, power 0. Apply Berserk (100%). Group enemies; MP 28; hits 1; accuracy 100; stagger 0.
- Resonant Notes ← Cut [500060, enemy]: MP 6, power 12. Non-elemental magic damage; power 12. Single enemies; MP 6; hits 1; accuracy 100; stagger 25.
- Flame Chant ← Flame [500340, enemy]: MP 6, power 12. Fire magic damage; power 12. Group enemies; MP 6; hits 1; accuracy 100; stagger 12.
- Harp Volley ← Swing [500070, enemy]: MP 6, power 12. Wind physical damage; power 12. Single enemies; MP 6; hits 2; accuracy 100; stagger 25.

### Jade — 5

Lightning martial attacker and crowd damage.

Sprite `337001205` (GL); base-stat budget: Cloud. Growth: Cloud.

- Awakening 1: Thunder Blade [420070]; Sparkstrike [421160]; Rocket Punch [487409]; Charge [487412]; Volt Kick [487430]; Thunder Palm [487433].
- Awakening 2: Thundara Blade [420080]; Sparkstrike II [421170]; Volt Palm [487403]; Gigavolt Strike [487406]; Thunder Palm II [487436]; Bladeblitz [400310].
- Awakening 3: Thundaga Blade [420090]; Sparkstrike III [421180]; Thunder Palm III [487439]; Storm Flurry [487442]; Fist of the Storm [487445].
- Awakening 4: Reckless Abandonment [400700].
- MR 1: Restore MP on Critical Hit [1323].
- MR 2: HP +30 (permanent).
- MR 3: Lightning Immunity [1366].
- MR 4: AP +8 (permanent).
- MR 5: Power Stagger [1385].
- MR 6: Agility +10 (permanent).
- MR 7: Vigorous Staggerer [1371].
- MR 8: Attack +15 (permanent).
- MR 9: Quick Hit [1359]; AP +8 (permanent); Spirit of Jade.

Supplemental player copies (native source ID; final MP/power):

- Volt Palm ← Megavolt [500180, enemy]: MP 14, power 17. Thunder physical damage; power 17. Apply Paralyzation (100%). Single enemies; MP 14; hits 1; accuracy 100; stagger 25.
- Gigavolt Strike ← Gigavolt [500400, enemy]: MP 20, power 24. Thunder physical damage; power 24. Single enemies; MP 20; hits 2; accuracy 100; stagger 25.
- Rocket Punch ← Rocket Punch [500730, enemy]: MP 10, power 18. Non-elemental physical damage; power 18. Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Charge ← Charge [501040, enemy]: MP 12, power 24. Non-elemental physical damage; power 24. Apply Paralyzation (50%). Single enemies; MP 12; hits 1; accuracy 70; stagger 25.
- Volt Kick ← Lightning Bolt [500220, enemy]: MP 12, power 18. Thunder physical damage; power 18. Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- Thunder Palm ← Thunder [255060, enemy]: MP 12, power 12. Thunder physical damage; power 12. Group enemies; MP 12; hits 1; accuracy 100; stagger 12.
- Thunder Palm II ← Thundara [255070, enemy]: MP 20, power 18. Thunder physical damage; power 18. Group enemies; MP 20; hits 2; accuracy 100; stagger 14.
- Thunder Palm III ← Thundaga [255080, enemy]: MP 28, power 24. Thunder physical damage; power 24. Group enemies; MP 28; hits 3; accuracy 100; stagger 15.
- Storm Flurry ← Octo-Strike [501070, enemy]: MP 28, power 32. Thunder physical damage; power 32. Random enemies; MP 28; hits 4; accuracy 100; stagger 12.
- Fist of the Storm ← Fist of Ferocity [502380, enemy]: MP 35, power 40. Thunder physical damage; power 40. Single enemies; MP 35; hits 1; accuracy 100; stagger 17.

### Spirited Heart Primm — NV Super Limit Burst

Mixed elemental sabers and support.

Sprite `304000717` (GLW); base-stat budget: Onion Knight. Growth: Lightning.

- Awakening 1: Slice & Dice - Wind [421280]; Stone Blade [420160]; Cure [487503].
- Awakening 2: Slice & Dice - Wind II [421290]; Stonera Blade [420170]; Cura [487506]; Firestorm Saber [487512]; Atomic Saber [487515]; Flame Saber [487530]; Blazing Saber [487518].
- Awakening 3: Slice & Dice - Wind III [421300]; Stonega Blade [420180]; Moonlightbringer [445300]; Gale Saber [487533]; Spiritlight Saber [487536]; Mana Burst [487539].
- Awakening 4: Curaga [487509]; Fill Gauge [400770].
- MR 1: Resist Fire [1011].
- MR 2: Attack +5 (permanent).
- MR 3: HP +20% [1378].
- MR 4: AP +8 (permanent).
- MR 5: Physical Attack +30% [1273].
- MR 6: MP +20 (permanent).
- MR 7: Physical Evasion +15% [1531].
- MR 8: Magic +15 (permanent).
- MR 9: Boundless Flames [1460]; AP +8 (permanent); Spirit of Spirited Heart Primm.

Supplemental player copies (native source ID; final MP/power):

- Cure ← Cure [240010, enemy]: MP 6, power 200. Restore healing power 200. Single friendlies; MP 6; hits 1; accuracy 100; stagger 50.
- Cura ← Cura [240020, enemy]: MP 18, power 500. Restore healing power 500. Single friendlies; MP 18; hits 1; accuracy 100; stagger 55.
- Curaga ← Curaga [240030, enemy]: MP 50, power 1500. Restore healing power 1500. Single friendlies; MP 50; hits 1; accuracy 100; stagger 60.
- Firestorm Saber ← Firestorm [500360, enemy]: MP 20, power 18. Fire physical damage; power 18. Group enemies; MP 20; hits 1; accuracy 100; stagger 12.
- Atomic Saber ← Atomic Ray [500380, enemy]: MP 20, power 24. Fire physical damage; power 24. Single enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Flame Saber ← Fira [255010, enemy]: MP 20, power 18. Fire physical damage; power 18. Group enemies; MP 20; hits 2; accuracy 100; stagger 14.
- Gale Saber ← Aerora [255130, enemy]: MP 20, power 18. Wind physical damage; power 18. Group enemies; MP 20; hits 2; accuracy 100; stagger 14.
- Spiritlight Saber ← Banishra [225300, native]: MP 35, power 33. Light physical damage; power 33. Group enemies; MP 35; hits 2; accuracy 100; stagger 19.
- Mana Burst ← Countermeasure [503190, enemy]: MP 26, power 27. Non-elemental magic damage; power 27. Group enemies; MP 26; hits 1; accuracy 100; stagger 12.
- Blazing Saber ← Fire [255000, enemy]: MP 14, power 18. Fire physical damage; power 18. Group enemies; MP 14; hits 1; accuracy 100; stagger 12.

### Relm — 5

Painter with lightning magic and mimicry.

Sprite `206001005` (GL); base-stat budget: Shantotto. Growth: Terra.

- Awakening 1: Thunder [220090]; Fire Beam [487606]; Drain [487615]; Earth Canvas [487630]; Frost Canvas [487636]; Aether Palette [487624].
- Awakening 2: Thundara [220100]; Thundaga [220110]; Bioblaster [487603]; El Nino [487609]; Banishra Canvas [487618]; Earth Canvas II [487633]; Stone Stroke [487642]; Storm Canvas [487627].
- Awakening 3: Forbidden Ars Magna [487612]; Erase Canvas [487639].
- Awakening 4: Flare [220330]; Mind Blast [487621]; Mimic [400330].
- MR 1: HP Stroll [1066].
- MR 2: Agility +5 (permanent).
- MR 3: Add Confuse [1237].
- MR 4: AP +8 (permanent).
- MR 5: Stagger Power +20% [1279].
- MR 6: MP +20 (permanent).
- MR 7: Phase Echo [1360].
- MR 8: Magic +15 (permanent).
- MR 9: Fill LB on Stagger [1280]; AP +8 (permanent); Spirit of Relm.

Supplemental player copies (native source ID; final MP/power):

- Bioblaster ← Bioblaster [500970, enemy]: MP 18, power 12. Non-elemental magic damage; power 12. Apply Poison (70%). Group enemies; MP 18; hits 1; accuracy 100; stagger 12.
- Fire Beam ← Fire Beam [500980, enemy]: MP 12, power 18. Fire magic damage; power 18. Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- El Nino ← El Niño [501010, enemy]: MP 20, power 18. Water magic damage; power 18. Group enemies; MP 20; hits 1; accuracy 100; stagger 12.
- Forbidden Ars Magna ← 禁呪アルス・マグナ [503930, enemy]: MP 26, power 26. Non-elemental magic damage; power 26. Group enemies; MP 26; hits 1; accuracy 100; stagger 45.
- Drain ← Drain [250300, enemy]: MP 12, power 12. Non-elemental magic damage; power 12. Apply HP drain (100% of damage). Single enemies; MP 12; hits 1; accuracy 100; stagger 20.
- Banishra Canvas ← Banishra [245300, enemy]: MP 20, power 18. Light magic damage; power 18. Group enemies; MP 20; hits 2; accuracy 100; stagger 14.
- Mind Blast ← Mind Blast [500750, enemy]: MP 45, power 24. Thunder magic damage; power 24. Apply Paralyzation (100%), Silence (100%), Poison (100%). Single enemies; MP 45; hits 1; accuracy 100; stagger 25.
- Earth Canvas ← Stone [255150, enemy]: MP 12, power 12. Earth magic damage; power 12. Group enemies; MP 12; hits 1; accuracy 100; stagger 12.
- Earth Canvas II ← Stonera [255160, enemy]: MP 20, power 18. Earth magic damage; power 18. Group enemies; MP 20; hits 2; accuracy 100; stagger 14.
- Frost Canvas ← Blizzard [225030, native]: MP 12, power 17. Ice magic damage; power 17. Group enemies; MP 12; hits 1; accuracy 100; stagger 17.
- Erase Canvas ← Liquidate [503200, enemy]: MP 40, power 40. Non-elemental magic damage; power 40. Group enemies; MP 40; hits 1; accuracy 100; stagger 12.
- Stone Stroke ← Stonera [250220, enemy]: MP 15, power 22. Earth magic damage; power 22. Single enemies; MP 15; hits 2; accuracy 100; stagger 19.
- Aether Palette ← Regurgitate [570630, enemy]: MP 18, power 30. Restore 30 MP. Single friendlies; MP 18; hits 1; accuracy 100; stagger 0.
- Storm Canvas ← Thundaga [250110, enemy]: MP 30, power 30. Thunder magic damage; power 30. Single enemies; MP 30; hits 3; accuracy 100; stagger 21.

### Rikku (FFX-2) — 6

Thief, item utility and fire physical breaks.

Sprite `249000206` (GL); base-stat budget: Vaan. Growth: Cloud.

- Awakening 1: Steal Strength [446840]; Steal Speed [446850]; Flash Bomb [487703]; Sleep Needle [487706]; Poison Needle [487709]; Steal [400260].
- Awakening 2: Red Spiral [447400]; Acid Grenade [487736]; Incendiary Sphere [487739]; Mug [400270].
- Awakening 3: White Whorl [447410]; Blinding Flash [487730]; Mustard Bomb [487733]; Wave Cannon [487742]; Trickshot [487745]; Emergency Protocol [487748]; Quick Repair [487751].
- Awakening 4: Gil Farmer [400400]; Gil Toss [400250]; Misfortune [400750].
- MR 1: Discerning Eye [1056].
- MR 2: HP +30 (permanent).
- MR 3: Treasure Hunter [1387].
- MR 4: AP +8 (permanent).
- MR 5: Thievery [1426].
- MR 6: Attack +10 (permanent).
- MR 7: One for the Road [1435].
- MR 8: Agility +15 (permanent).
- MR 9: Wings of Freedom [1436]; AP +8 (permanent); Spirit of Rikku (FFX-2).

Supplemental player copies (native source ID; final MP/power):

- Flash Bomb ← Flash Bomb [501020, enemy]: MP 10, power 6. Non-elemental physical damage; power 6. Apply Blind (30%). Group enemies; MP 10; hits 1; accuracy 100; stagger 12.
- Sleep Needle ← Sleep Needle [500300, enemy]: MP 8, power 12. Non-elemental physical damage; power 12. Apply Sleep (100%). Single enemies; MP 8; hits 1; accuracy 100; stagger 25.
- Poison Needle ← Poison Needle [500280, enemy]: MP 8, power 12. Non-elemental physical damage; power 12. Apply Poison (100%). Single enemies; MP 8; hits 1; accuracy 100; stagger 25.
- Blinding Flash ← Blinding Flash [571540, enemy]: MP 28, power 24. Non-elemental physical damage; power 24. Apply Blind (100%). Group enemies; MP 28; hits 1; accuracy 100; stagger 50.
- Mustard Bomb ← Mustard Bomb [571550, enemy]: MP 40, power 40. Non-elemental physical damage; power 40. Apply Paralyzation (50%). Group enemies; MP 40; hits 1; accuracy 100; stagger 25.
- Acid Grenade ← Secrete Acid [501650, enemy]: MP 24, power 18. Non-elemental physical damage; power 18. Apply Poison (50%). Group enemies; MP 24; hits 1; accuracy 100; stagger 12.
- Incendiary Sphere ← Incineration Sphere [571530, enemy]: MP 22, power 18. Fire physical damage; power 18. Apply AttackDown (65%), IntelligenceDown (65%). Group enemies; MP 22; hits 1; accuracy 100; stagger 25.
- Wave Cannon ← Wave Cannon [505120, enemy]: MP 35, power 36. Non-elemental magic damage; power 36. Group enemies; MP 35; hits 1; accuracy 100; stagger 12.
- Trickshot ← Triple Threat [505940, enemy]: MP 30, power 36. Non-elemental physical damage; power 36. Random enemies; MP 30; hits 3; accuracy 100; stagger 12.
- Emergency Protocol ← Analyze Movement Pattern [571520, enemy]: MP 30, power 0. Remove own ailments/debuffs and gain 30% physical/magic protection for 3 turns. Self friendlies; MP 30; hits 1; accuracy 100; stagger 12.
- Quick Repair ← Cannibalize [501290, enemy]: MP 30, power 200. Restore 200 HP. Group friendlies; MP 30; hits 1; accuracy 100; stagger 25.

### Nalu — 5

Lightning physical, criticals and analysis.

Sprite `100015405` (GL); base-stat budget: Cloud. Growth: Cloud.

- Awakening 1: Thunder Surge [421130]; Libra [210220]; Thunder Spear [487803]; Lightning Sweep [487806]; Needle [487812]; Lance Launcher [487836].
- Awakening 2: Braver [446000]; Thundara Surge [421140]; Lightning Strike [447500]; Lightning Lance Sweep [487830]; Shock Lance [487839].
- Awakening 3: Cross-Slash [446010]; Thundaga Surge [421150]; Thunderfall [447510]; Chain Lance [487809]; Thunderstorm Lance [487833]; Numbing Spark [487842]; Thunder Javelin [487845].
- MR 1: Restore MP on Attack [1124].
- MR 2: Agility +5 (permanent).
- MR 3: Imbue Lightning [1523].
- MR 4: AP +8 (permanent).
- MR 5: Scan and Strike [1399].
- MR 6: HP +60 (permanent).
- MR 7: Broadsword Mastery [1420].
- MR 8: Attack +15 (permanent).
- MR 9: Signature Moves [1418]; AP +8 (permanent); Spirit of Nalu.

Supplemental player copies (native source ID; final MP/power):

- Thunder Spear ← Thunder Beam [501000, enemy]: MP 12, power 18. Thunder physical damage; power 18. Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- Lightning Sweep ← Lightning [500390, enemy]: MP 12, power 12. Thunder physical damage; power 12. Group enemies; MP 12; hits 2; accuracy 100; stagger 12.
- Chain Lance ← Chain Spark [220120, native]: MP 30, power 30. Thunder physical damage; power 30. Group enemies; MP 30; hits 3; accuracy 100; stagger 21.
- Needle ← Needle [500260, enemy]: MP 8, power 18. Non-elemental physical damage; power 18. Single enemies; MP 8; hits 1; accuracy 100; stagger 25.
- Lightning Lance Sweep ← Thunder [225060, native]: MP 15, power 17. Thunder physical damage; power 17. Group enemies; MP 15; hits 1; accuracy 100; stagger 17.
- Thunderstorm Lance ← Thunderstorm [506140, enemy]: MP 36, power 30. Thunder physical damage; power 30. Apply Paralyzation (100%). Group enemies; MP 36; hits 3; accuracy 100; stagger 21.
- Lance Launcher ← Launcher [500880, enemy]: MP 10, power 12. Thunder physical damage; power 12. Single enemies; MP 10; hits 2; accuracy 100; stagger 25.
- Shock Lance ← Array: Shock Shell [503610, enemy]: MP 20, power 26. Thunder physical damage; power 26. Single enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Numbing Spark ← Thunderspark [250360, enemy]: MP 32, power 30. Thunder physical damage; power 30. Apply Paralyzation (50%). Single enemies; MP 32; hits 1; accuracy 100; stagger 28.
- Thunder Javelin ← Regurgitate [570650, enemy]: MP 28, power 36. Thunder physical damage; power 36. Single enemies; MP 28; hits 1; accuracy 100; stagger 0.

### Elza — 5

Dark/water physical and sustained pressure.

Sprite `302000605` (GL); base-stat budget: Tidus. Growth: Cloud.

- Awakening 1: Dark Surge [422050]; Spiral Cut [447000]; Slice & Dice - Water [421220].
- Awakening 2: Darkra Surge [422060]; Slice & Dice - Water II [421230]; Queenly Rend [487903]; Venom Sweep [487909].
- Awakening 3: Darkga Surge [422070]; Energy Rain [447010]; Spiral Cut+ [447020]; Slice & Dice - Water III [421240]; Shred [487906]; Black Tide [487912]; Rabid Claw [487930]; Abyssal Rend [487933].
- Awakening 4: Ferocious Strike [487936]; Crushing Tide [487939]; Judgment Claw [487942].
- MR 1: Resist Dark [1253].
- MR 2: HP +30 (permanent).
- MR 3: Speed +20% [1317].
- MR 4: AP +8 (permanent).
- MR 5: Imbue Dark [1528].
- MR 6: Agility +10 (permanent).
- MR 7: Skyward Dreams [1434].
- MR 8: Attack +15 (permanent).
- MR 9: Tip-Top Shape [1428]; AP +8 (permanent); Spirit of Elza.

Supplemental player copies (native source ID; final MP/power):

- Queenly Rend ← Queenly Whip [505910, enemy]: MP 16, power 16. Dark physical damage; power 16. Also reduce enemy attack and magic. Single enemies; MP 16; hits 2; accuracy 100; stagger 25.
- Shred ← Shred [503580, enemy]: MP 25, power 35. Non-elemental physical damage; power 35. Single enemies; MP 25; hits 1; accuracy 100; stagger 25.
- Venom Sweep ← Digestive Fluid [500490, enemy]: MP 15, power 12. Non-elemental physical damage; power 12. Apply Poison (50%). Group enemies; MP 15; hits 1; accuracy 100; stagger 12.
- Black Tide ← Sludge [503660, enemy]: MP 26, power 28. Water physical damage; power 28. Group enemies; MP 26; hits 1; accuracy 100; stagger 12.
- Rabid Claw ← Rabid Claw [502040, enemy]: MP 26, power 30. Dark physical damage; power 30. Apply Confusion (50%), Berserk (50%). Single enemies; MP 26; hits 1; accuracy 100; stagger 25.
- Abyssal Rend ← Regurgitate [570610, enemy]: MP 32, power 40. Dark physical damage; power 40. Apply Poison (50%), Paralyzation (50%), Slow (30%). Single enemies; MP 32; hits 1; accuracy 100; stagger 25.
- Ferocious Strike ← Ferocious Strike [503650, enemy]: MP 32, power 30. Dark physical damage; power 30. Apply Paralyzation (50%). Group enemies; MP 32; hits 1; accuracy 100; stagger 25.
- Crushing Tide ← Crushing Breath [505400, enemy]: MP 26, power 28. Water physical damage; power 28. Group enemies; MP 26; hits 1; accuracy 100; stagger 12.
- Judgment Claw ← Judgment of the Claw [503130, enemy]: MP 28, power 30. Dark physical damage; power 30. Group enemies; MP 28; hits 1; accuracy 100; stagger 25.

### Lunera — 6

Wind physical and stagger support.

Sprite `100007506` (GL); base-stat budget: Bartz. Growth: Cloud.

- Awakening 1: Aero Blade [420130]; Gale Sweep [488033]; Twin Gale Shot [488042].
- Awakening 2: Aerora Blade [420140]; Crushing Blade [445500]; Torrential Hew [414400]; Shamshir [488003]; Gale Volley [488006]; Venom Gale [488015]; Gale Reprisal [488039].
- Awakening 3: Aeroga Blade [420150]; Wind Cutter Blade [445510]; Aquatic Synergy [414410]; Merciless Gale [488009]; Star Volley [488012]; Silencing Gale [488036].
- Awakening 4: Tempest Volley [488030].
- MR 1: Resist Wind [1248].
- MR 2: Agility +5 (permanent).
- MR 3: Spry Steps [1258].
- MR 4: AP +8 (permanent).
- MR 5: Lingering Debuffs [1510].
- MR 6: HP +60 (permanent).
- MR 7: Guiding Wind [1458].
- MR 8: Attack +15 (permanent).
- MR 9: Double MRP [1051]; AP +8 (permanent); Spirit of Lunera.

Supplemental player copies (native source ID; final MP/power):

- Shamshir ← Shamshir [500450, enemy]: MP 16, power 24. Wind physical damage; power 24. Single enemies; MP 16; hits 1; accuracy 100; stagger 25.
- Gale Volley ← Wing Flap [503720, enemy]: MP 20, power 20. Wind magic damage; power 20. Group enemies; MP 20; hits 3; accuracy 100; stagger 20.
- Merciless Gale ← Merciless Judgment [505270, enemy]: MP 38, power 40. Wind physical damage; power 40. Single enemies; MP 38; hits 3; accuracy 100; stagger 25.
- Star Volley ← Flare Star [500900, enemy]: MP 32, power 30. Non-elemental physical damage; power 30. Group enemies; MP 32; hits 1; accuracy 100; stagger 12.
- Venom Gale ← Venom Breath [501900, enemy]: MP 24, power 18. Wind physical damage; power 18. Apply Poison (30%). Group enemies; MP 24; hits 1; accuracy 100; stagger 12.
- Tempest Volley ← Aeroga [225140, native]: MP 42, power 40. Wind physical damage; power 40. Group enemies; MP 42; hits 3; accuracy 100; stagger 21.
- Gale Sweep ← Aero [255120, enemy]: MP 12, power 12. Wind physical damage; power 12. Group enemies; MP 12; hits 1; accuracy 100; stagger 12.
- Silencing Gale ← Windwail [506150, enemy]: MP 34, power 30. Wind physical damage; power 30. Apply Silence (100%). Group enemies; MP 34; hits 3; accuracy 100; stagger 21.
- Gale Reprisal ← Counter Vines [502620, enemy]: MP 20, power 26. Wind physical damage; power 26. Single enemies; MP 20; hits 2; accuracy 100; stagger 25.
- Twin Gale Shot ← Whip [500120, enemy]: MP 8, power 12. Wind physical damage; power 12. Single enemies; MP 8; hits 2; accuracy 100; stagger 25.

## Research and validation limits

Selected hosted packs were checked against their published SHA-256 values, including base packs for shifted forms. Unit records, selected-form sprite motions and LB profiles were inspected. FFBE themes are references, not imported combat numbers. The archived Global datamine is `aEnigmatic/ffbe` at `95727376e82d27acc1290b6dc8ad27ce3c89ea71`; hosted merged records also cover Japanese and post-archive forms. Reberta’s Japanese hosted record has no translated skill list; her requested physical dragoon role and the original Reberta elemental/jump theme guide that kit.

Automated checks cover portable configs, unique allocation, native base stats, MR scheduling and role budgets, mastery caps, owner-condition rebinding, native table patch serialization, and optional-pack lifecycle. They do not establish live-game balance or prove every animation exists in the demo. Library repairs use the existing unverified-skill controls. The separate **Use borrowed Sephira skill visuals** toggle defaults on; turn it off and rebuild/install to restore the 226 preset source visual mappings without changing mechanics or saved kits. Turn it on and rebuild/install to restore borrowed visuals. Explicit visual donor edits and authored sequences are preserved. The 39 custom elemental attacks based on neutral sources receive a native elemental impact at their original hit; no damage keys, sounds or battle-speed effects are added. If an optional borrowed visual is already elemental, its native effect supplies that presentation. Skill icons follow actual damage elements. Every added vision has its own command and Spirit icon, without consuming another original vision’s icon slot. Original full-game source exceptions are recorded in [the runtime review](docs/SEPHIRA_RUNTIME_REVIEW.md).

## Full-game release review

Re-audit native stats, level curves, skill mechanics and unlock ranks; private command/LB conditions and IDs; summon availability; selected form/LB presentation; and vendor/acquisition availability. Preserve user edits; apply MR/acquisition revisions through the backed-up progression update. See README’s running full-release checklist.
