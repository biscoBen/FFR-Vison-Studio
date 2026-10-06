# Sephira’s Visions

30 optional, editable presets using the requested FFBE forms. Enable the section on the home page, then build/install. First enable downloads only the missing selected artwork and adds the profiles after all preparations succeed.

Turning the section off keeps edits and removed entries; its units and acquisition caves are omitted by the next build. **Restore missing** adds removed presets without resetting existing ones. **Reset all presets** or a card’s **Reset to preset** replaces its kit and appearance, preserves its IDs and acquisition location, and backs up the previous roster in Studio’s character-config backups.

An existing custom Crystal Fina is adopted with her current edits and acquisition intact. Reset her explicitly to use this balanced recipe. Other user-added copies and original vision/party edits are preserved.

## Balance and coverage

- Every preset copies a native level-one stat profile and its exact permanent MR stat rewards/ranks. AP remains the native +8 at MR 4 and +8 at MR 9. Native physical or magic growth curves are used.
- Existing native grants retain their mechanics. Supplemental skills come from the wider native/enemy catalog on private player copies: zero-MP enemy attacks receive MP costs; excessive accuracy, multipliers and hit counts are reduced. Group spells/healing cost more than comparable single-target spells. No FFBE multipliers or FFBE stat conversion are imported. LBs retain one native resonance’s total mechanics; selected elements/damage types follow the requested role.
- All 160 distinct active skills and 131 passives from the 15 excluded original visions are allocated. Within the pack, each exact active/passive appears once; permanent MR stats may repeat. Additional native skills provide thematic attacks and support. Each new vision has its own correctly bound Spirit mastery wrapper.
- Command/LB-specific bonuses use private rebound copies. Native originals remain unchanged. Minfilia’s Dual Jobs selects her own identity. Specific skill bonuses remain grouped with their required attacks.
- Each revised kit has 20–25 distinct abilities/passives, excluding permanent MR stats, its Spirit wrapper and LB. Reberta has 24 because Clive’s Eikon skills and associated fire passives stay together; Trance Terra has 25 with the full native fire spell line. They specialize without being restricted to one action type: healers and debuffers also have attacks. Added visions default to a 1,000-gil vendor price; acquisition can be edited normally.
- Great Dragon is retired from this collection and omitted from builds, including older tagged saved profiles. Reset all presets backs up and removes his old collection entry. His required original grants move to Reberta, Minfilia, Lila, Trance Terra and Primm. Untagged user-created Great Dragons are preserved.
- New enemy copies belong to the vision’s player command; enemy group-toggle partners are disabled so they cannot switch into unbalanced originals. New passives retain native magnitudes/equip costs and are learned through MR or their native ranks. No new permanent stat boosts are added. Alice’s three earth slams become ice slams with unchanged power/cost.
- Eiko uses the demo’s available Ifrit and Shiva summon commands; their native costs and mechanics are retained. Unreleased espers are not required.

The excluded originals are Tronn, Wilhelm, Warrior of Light, Firion, Onion Knight, Cecil, Bartz, Cloud, Squall, Zidane, Tidus, Shantotto, Vaan, Noctis and Clive. Their exact grants, native ranks, descriptions, mechanics and allocations are retained in `assets/sephira_visions/native_coverage.json`.

## Kit sizes

Revision 2 adds broader game skills rather than dividing only the excluded originals. Existing saved kits are preserved: use **Reset all presets** to apply this revision, then build/install. Individual reset is also available. Reset backs up edits and keeps allocated identity/acquisition.

| Vision | Previous | Active | Passive | Total |
|---|---:|---:|---:|---:|
| A2 | 13 | 11 | 9 | 20 |
| Christine | 13 | 11 | 9 | 20 |
| Crystal Fina | 15 | 14 | 8 | 22 |
| Barusa | 15 | 13 | 8 | 21 |
| Blue Sky Belle Fran | 15 | 12 | 8 | 20 |
| Oracle Maiden Lunafreya | 14 | 14 | 8 | 22 |
| Minfilia | 14 | 13 | 9 | 22 |
| Folka | 14 | 13 | 8 | 21 |
| Fryevia | 11 | 12 | 8 | 20 |
| Lenneth | 13 | 12 | 8 | 20 |
| Lila | 14 | 12 | 9 | 21 |
| Mystea | 12 | 12 | 9 | 21 |
| Reberta (JP) | 14 | 14 | 10 | 24 |
| Snow White | 13 | 12 | 8 | 20 |
| Aria | 14 | 14 | 8 | 22 |
| Eiko | 14 | 12 | 9 | 21 |
| Alice/Half Nightmare | 12 | 12 | 8 | 20 |
| Moogle of Narshe Mog | 14 | 13 | 8 | 21 |
| Lilith | 13 | 12 | 8 | 20 |
| Dragon Knight Freya | 12 | 12 | 8 | 20 |
| Trance Terra | 15 | 16 | 9 | 25 |
| Charming Kitty Ariana | 13 | 13 | 8 | 21 |
| Elephim | 12 | 14 | 8 | 22 |
| Jade | 14 | 12 | 8 | 20 |
| Spirited Heart Primm | 14 | 14 | 8 | 22 |
| Relm | 12 | 13 | 8 | 21 |
| Rikku (FFX-2) | 16 | 12 | 9 | 21 |
| Nalu | 14 | 12 | 8 | 20 |
| Elza | 15 | 13 | 8 | 21 |
| Lunera | 13 | 12 | 8 | 20 |

## Selected forms and kits

Awakening ranks below are numbered 1–4 for readability. MR ranks use the game’s 0–9 values. Native source names are retained for skills so their exact versions remain identifiable.

### A2 — 5

Physical combo attacker.

Sprite `310000505` (GL); stat/MR budget: Squall. Growth: Cloud.

- Awakening 1: Physical Attack +20% [1309]; Rend [485003]; Venom Skewer [485006]; Blade Volley [485015].
- Awakening 2: Rough Divide [446600]; Nullify Blind [1105]; HP +20% [1378]; Grand Slash [485009]; Perforate [485012].
- Awakening 3: Fated Circle [446610].
- Awakening 4: Lone Lion [1423]; Latent Potential [1424].
- MR 1: Mineuchi [400500]; Improvement [1421].
- MR 3: Gut Rip [400690]; Stagger Power +10% [1278].
- MR 5: Trigger [1422].
- MR 7: Fill LB on Attack [1478].
- MR 9: Barrage [400300]; Double Action [400710].

Supplemental player copies (native source ID; final MP/power):

- Rend ← Rend [501510, enemy]: MP 8, power 18. Non-elemental physical damage; power 18. Single enemies; MP 8; hits 1; accuracy 100; stagger 25.
- Venom Skewer ← Skewer [501790, enemy]: MP 12, power 18. Non-elemental physical damage; power 18. Apply Poison (50%). Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- Grand Slash ← Grand Slash [501310, enemy]: MP 18, power 18. Non-elemental physical damage; power 18. Group enemies; MP 18; hits 1; accuracy 100; stagger 12.
- Perforate ← Perforate [502220, enemy]: MP 24, power 30. Non-elemental physical damage; power 30. Apply Poison (50%). Single enemies; MP 24; hits 1; accuracy 100; stagger 25.
- Blade Volley ← Machine Gun [500150, enemy]: MP 10, power 12. Non-elemental physical damage; power 12. Single enemies; MP 10; hits 4; accuracy 100; stagger 25.

### Christine — 6

Ice magic and stagger.

Sprite `401002606` (GL); stat/MR budget: Tronn. Growth: Terra.

- Awakening 1: Blizzard [220050]; Silence [230030]; Dispel [210200]; Stagger Power +30% [1376]; Blizzard Beam [485109]; Frost Wave [485115].
- Awakening 2: Blizzara [220060]; Blizzaga [220070]; Resist Ice [1033]; Victor’s Respite [1407]; Absolute Zero [485106]; Slumber Mist [485112].
- Awakening 3: Deshell on Stagger [1285]; Freezing Spike [485103].
- Awakening 4: True Stagger [1406].
- MR 1: Restore MP on Stagger [1281].
- MR 3: Auto MP Restore (M) [1255].
- MR 5: Focus Magic [400630].
- MR 7: Nullify Doom [1115].
- MR 9: Half MP Cost [1045].

Supplemental player copies (native source ID; final MP/power):

- Freezing Spike ← Freezing Spike [220080, native]: MP 30, power 30. Ice magic damage; power 30. Group enemies; MP 30; hits 3; accuracy 100; stagger 21.
- Absolute Zero ← Absolute Zero [500230, enemy]: MP 22, power 24. Ice magic damage; power 24. Group enemies; MP 22; hits 1; accuracy 100; stagger 12.
- Blizzard Beam ← Blizzard Beam [500990, enemy]: MP 10, power 18. Ice magic damage; power 18. Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Slumber Mist ← Sleep Gas [500570, enemy]: MP 20, power 0. Apply Sleep (30%). Group enemies; MP 20; hits 1; accuracy 100; stagger 12.
- Frost Wave ← Blaze [500350, enemy]: MP 12, power 12. Ice magic damage; power 12. Group enemies; MP 12; hits 2; accuracy 100; stagger 12.

### Crystal Fina — Custom

Healing, cleansing and light magic.

Sprite `99887755552703` (CUSTOM); stat/MR budget: Ayaka. Growth: Terra.

- Awakening 1: Cure [210010]; Banish [210250]; Healing Magic +30% [1375]; Alabastrine Blessing [1455].
- Awakening 2: Cura [210020]; Banishra [210260]; Healing Magic +20% [1283]; Crystal Ray [485212]; Restore [485215].
- Awakening 3: Curaga [210030]; Banishga [210270]; Arise [210150].
- Awakening 4: Esunaga [210130]; Divine Tidings [1456]; Holy [485203]; Reraise [485206]; Radiant Restoration [485209].
- MR 3: Resist Light [1252].
- MR 5: Prepare Healing [400740].
- MR 7: The Hand That Heals [1393]; Auto-Potion [1043].
- MR 9: LB Charge on Heal [1397].

Supplemental player copies (native source ID; final MP/power):

- Holy ← Holy [210190, native]: MP 63, power 80. Light magic damage; power 80. Single enemies; MP 63; hits 1; accuracy 100; stagger 40.
- Reraise ← Reraise [210240, native]: MP 60, power 0. Grant Reraise to an ally. Single friendlies; MP 60; hits 1; accuracy 100; stagger 25.
- Radiant Restoration ← Curaga [215020, native]: MP 65, power 1500. Restore healing power 1500. Group friendlies; MP 65; hits 1; accuracy 100; stagger 60.
- Crystal Ray ← Array: Brilliance [503630, enemy]: MP 24, power 32. Light magic damage; power 32. Single enemies; MP 24; hits 1; accuracy 100; stagger 25.
- Restore ← Restore [501930, enemy]: MP 18, power 20. Restore 20% max HP. Single friendlies; MP 18; hits 1; accuracy 100; stagger 25.

### Barusa — 6

Earth physical bruiser and protection.

Sprite `401003006` (GL); stat/MR budget: Wilhelm. Growth: Cloud.

- Awakening 1: Stone Surge [421400]; Stone Slam [421340]; General’s Pride [1452]; Physical Defense +20% [1313]; Quicksand [485309]; Granite Claw [485312].
- Awakening 2: Stonera Surge [421410]; Stonera Slam [421350]; D Sword Breaker [414700]; Crust Driver [485303]; Resist Earth [1249].
- Awakening 3: Stonega Surge [421420]; Stonega Slam [421360]; Supreme Defense [414710]; HP +30% [1379]; Mantle Driver [485306].
- Awakening 4: Unmoving Bulwark [1453]; Bastion [1454].
- MR 1: Strategic Acumen [1336].
- MR 5: Guard [400640].
- MR 7: Stalwart Knight [1118].

Supplemental player copies (native source ID; final MP/power):

- Crust Driver ← Crust Driver [414800, native]: MP 20, power 23. Earth physical damage; power 23. Single enemies; MP 20; hits 1; accuracy 100; stagger 33.
- Mantle Driver ← Mantle Driver [414810, native]: MP 37, power 49. Earth physical damage; power 49. Single enemies; MP 37; hits 3; accuracy 100; stagger 36.
- Quicksand ← Quicksand [500330, enemy]: MP 12, power 12. Earth physical damage; power 12. Apply Slow (100%). Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- Granite Claw ← Pincer [500540, enemy]: MP 8, power 18. Non-elemental physical damage; power 18. Single enemies; MP 8; hits 1; accuracy 100; stagger 25.

### Blue Sky Belle Fran — 6

Ranged physical and disabling arrows.

Sprite `212001706` (GL); stat/MR budget: Firion. Growth: Cloud.

- Awakening 1: Aero Knife [421250]; Thunder Knife [421100]; Sleep Knife [422010]; Dual Guns [1443]; Poison Arrow [485403]; Binding Arrow [485406].
- Awakening 2: Aerora Knife [421260]; Thundara Knife [421110]; Blind Knife [422030]; Add Poison [1125]; Add Silence [1126]; Critical Hit Rate +5% [1321].
- Awakening 3: Aeroga Knife [421270]; Thundaga Knife [421120]; Add Blind [1128]; Arrow Tempest [485409].
- Awakening 4: Trigger-Happy [1444].
- MR 3: Aim [400450].
- MR 5: Decimating Attacks [1337].
- MR 7: Add Sleep [1127].

Supplemental player copies (native source ID; final MP/power):

- Poison Arrow ← Poison Slash [500210, enemy]: MP 8, power 12. Non-elemental physical damage; power 12. Apply Poison (100%). Single enemies; MP 8; hits 1; accuracy 100; stagger 25.
- Binding Arrow ← Stun Slash [501170, enemy]: MP 10, power 12. Non-elemental physical damage; power 12. Apply Paralyzation (100%). Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Arrow Tempest ← Frenzied Bombardment [503250, enemy]: MP 32, power 32. Non-elemental physical damage; power 32. Group enemies; MP 32; hits 4; accuracy 100; stagger 12.

### Oracle Maiden Lunafreya — NV Brave Shift

Debuff specialist with water/wind magic.

Sprite `215002417` (GL); stat/MR budget: Zidane. Growth: Terra.

- Awakening 1: Free Energy [446800]; Deprotect [230080]; Add Deprotect [1131]; Add Deshell [1132]; Slowing Tide [485509].
- Awakening 2: Meo Twister [446820]; Steal Vitality [446860]; Deshell [230090]; Confusega [485512]; Maelstrom [485515]; Blinding Light [485518].
- Awakening 3: Free Energy+ [446810]; Steal Magic [446870]; Sundering Wind [485503]; Graceful Deluge [485506]; Add Slow [1129].
- Awakening 4: Meo Twister+ [446830].
- MR 1: Skilled Disruptor [1326].
- MR 3: Insult to Injury [1425].
- MR 5: Stealth Specialist [1396].
- MR 7: Aggravation [1468]; Slow Opener [1298].

Supplemental player copies (native source ID; final MP/power):

- Sundering Wind ← Sundering Wind [502470, enemy]: MP 28, power 0. Reduce enemy physical and magic defense by 30% for 3 turns. Group enemies; MP 28; hits 1; accuracy 100; stagger 12.
- Graceful Deluge ← Graceful Deluge [501420, enemy]: MP 40, power 30. Water magic damage; power 30. Also reduce enemy physical and magic defense. Group enemies; MP 40; hits 3; accuracy 100; stagger 12.
- Slowing Tide ← Mucus [500500, enemy]: MP 8, power 0. Apply Slow (100%). Single enemies; MP 8; hits 1; accuracy 100; stagger 25.
- Confusega ← Confusega [235070, native]: MP 24, power 0. Apply Confusion (50%). Group enemies; MP 24; hits 1; accuracy 100; stagger 25.
- Maelstrom ← Maelstrom [500760, enemy]: MP 22, power 24. Water magic damage; power 24. Group enemies; MP 22; hits 1; accuracy 100; stagger 12.
- Blinding Light ← Flash [500820, enemy]: MP 18, power 0. Apply Blind (100%). Group enemies; MP 18; hits 1; accuracy 100; stagger 12.

### Minfilia — 4

Mixed earth/wind offense and party protection.

Sprite `214000304` (GL); stat/MR budget: Onion Knight. Growth: Lightning.

- Awakening 1: Stone [220210]; Protect [230040]; Late Bloomer [1411]; Magic Attack +20% [1311]; Gale [485606]; Sandstorm [485609]; Quiet Recovery [485615].
- Awakening 2: Stonera [220220]; Protectga [230050]; Petrifying Gaze [485612].
- Awakening 3: Stonega [220230]; Blade Torrent [445200]; Chuck [1412]; Calamity [485603].
- Awakening 4: Dual Jobs [485690]; Job Change [1410]; Fire Immunity [1362].
- MR 1: Throw [400240].
- MR 3: Weakness Exploiter [1099].
- MR 5: Observe and Recover HP [1465].
- MR 7: Observe and Attack [1343]; Physical Defense +10% [1312].

Supplemental player copies (native source ID; final MP/power):

- Calamity ← Calamity [220240, native]: MP 35, power 30. Earth magic damage; power 30. Group enemies; MP 35; hits 3; accuracy 100; stagger 21.
- Gale ← Aero [225120, native]: MP 12, power 17. Wind magic damage; power 17. Group enemies; MP 12; hits 1; accuracy 100; stagger 17.
- Sandstorm ← Sandstorm [500320, enemy]: MP 12, power 12. Earth physical damage; power 12. Apply Blind (30%). Group enemies; MP 12; hits 2; accuracy 100; stagger 12.
- Petrifying Gaze ← Petrifying Gaze [500600, enemy]: MP 18, power 0. Apply Stoned (30%). Single enemies; MP 18; hits 1; accuracy 100; stagger 25.
- Quiet Recovery ← Groom [502610, enemy]: MP 5, power 100. Restore healing power 100. Self friendlies; MP 5; hits 1; accuracy 100; stagger 25.

### Folka — 6

Water magic with restorative utility.

Sprite `100018306` (GL); stat/MR budget: Tronn. Growth: Terra.

- Awakening 1: Water [220130]; Syphon [220310]; MP +10% [1380]; Bio [485712].
- Awakening 2: Watera [220140]; Resist Water [1251]; Aqua Breath [485703]; Poisonga [485715].
- Awakening 3: Waterga [220150]; Regen [210050]; Hi Regen [414510]; Tidal Wave [485706]; Watera Tide [485709].
- Awakening 4: Water Immunity [1367].
- MR 3: Mana Overload [1445]; Auto MP Restore (S) [1254].
- MR 5: Pass the Torch [400680]; MP Stroll [1307].
- MR 7: Nullify Paralysis [1108].
- MR 9: Magic Barrage [400360]; Water Eater [1348].

Supplemental player copies (native source ID; final MP/power):

- Aqua Breath ← Aqua Breath [500800, enemy]: MP 20, power 18. Water magic damage; power 18. Group enemies; MP 20; hits 3; accuracy 100; stagger 12.
- Tidal Wave ← Tidal Wave [505130, enemy]: MP 32, power 36. Water magic damage; power 36. Group enemies; MP 32; hits 2; accuracy 100; stagger 12.
- Watera Tide ← Watera [225100, native]: MP 30, power 33. Water magic damage; power 33. Group enemies; MP 30; hits 2; accuracy 100; stagger 19.
- Bio ← Bio [250260, enemy]: MP 10, power 12. Non-elemental magic damage; power 12. Apply Poison (100%). Single enemies; MP 10; hits 1; accuracy 100; stagger 20.
- Poisonga ← Poisonga [225180, native]: MP 20, power 0. Apply Poison (100%). Group enemies; MP 20; hits 1; accuracy 100; stagger 25.

### Fryevia — 5

Ice spellblade and precision physical.

Sprite `302001405` (GL); stat/MR budget: Bartz. Growth: Cloud.

- Awakening 1: Froststrike [421070]; Frozen Slumber Cut [485809]; Frostbind Cut [485812]; True Strike [485815]; Knight of the Sacred Frost [1463].
- Awakening 2: Froststrike II [421080]; Golden Thrust [485818]; Dark Edge [485821].
- Awakening 3: Froststrike III [421090]; Spellblade Wielder [1415]; Leaping Cleave [1357]; Glint of Verglas [485803]; Stormbound Smite [485806].
- Awakening 4: Flare Blade [420270]; Spellblade Mastery [1416]; Ice Immunity [1363].
- MR 5: Blade Dance [400350].
- MR 7: Dual Spellblade [1414]; Auto-Reflect [1071].
- MR 9: Ice Eater [1344].

Supplemental player copies (native source ID; final MP/power):

- Glint of Verglas ← Glint of Verglas [505380, enemy]: MP 35, power 40. Ice physical damage; power 40. Single enemies; MP 35; hits 2; accuracy 100; stagger 25.
- Stormbound Smite ← Stormbound Smite [505390, enemy]: MP 32, power 30. Ice physical damage; power 30. Group enemies; MP 32; hits 3; accuracy 100; stagger 12.
- Frozen Slumber Cut ← Sleep Slash [500630, enemy]: MP 10, power 18. Ice physical damage; power 18. Apply Sleep (50%). Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Frostbind Cut ← Paralysis Slash [500640, enemy]: MP 12, power 18. Ice physical damage; power 18. Apply Paralyzation (50%). Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- True Strike ← True Strike [500920, enemy]: MP 6, power 18. Non-elemental physical damage; power 18. Single enemies; MP 6; hits 1; accuracy 70; stagger 25.
- Golden Thrust ← Golden Lance [501600, enemy]: MP 14, power 24. Non-elemental physical damage; power 24. Single enemies; MP 14; hits 1; accuracy 100; stagger 25.
- Dark Edge ← Dark Edge [505260, enemy]: MP 20, power 24. Dark physical damage; power 24. Single enemies; MP 20; hits 1; accuracy 100; stagger 25.

### Lenneth — 6

Physical cover tank with light attacks.

Sprite `330000106` (GL); stat/MR budget: Warrior of Light. Growth: Cloud.

- Awakening 1: Vanguard Glaive [445010]; Banish Blade [420330]; Shield Crush [485903]; Repose [485915].
- Awakening 2: Banishra Blade [420340]; Protect Opener [1290]; Guarding Smite [485906]; Lance Breaker [485912].
- Awakening 3: Sacred Wave [445020]; Banishga Blade [420350]; Lustrous Shield [1408]; Sword Strike [485909].
- Awakening 4: Vanguard Glaive+ [445030].
- MR 1: Fill LB when Taking Damage [1331].
- MR 3: Multi-Cover [400390]; Auto-Protect [1072].
- MR 5: Physical Counter [1029].
- MR 7: Heroic Nature [1409]; Nullify Petrify [1110].
- MR 9: Grit [1042].

Supplemental player copies (native source ID; final MP/power):

- Shield Crush ← Crush [500020, enemy]: MP 10, power 18. Non-elemental physical damage; power 18. Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Guarding Smite ← Guarding Smite [505410, enemy]: MP 20, power 24. Non-elemental physical damage; power 24. Also defend after attacking. Single enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Sword Strike ← Sword Strike [503640, enemy]: MP 25, power 30. Non-elemental physical damage; power 30. Group enemies; MP 25; hits 1; accuracy 100; stagger 25.
- Lance Breaker ← Rib [500170, enemy]: MP 18, power 24. Non-elemental physical damage; power 24. Single enemies; MP 18; hits 1; accuracy 100; stagger 30.
- Repose ← Repose [502080, enemy]: MP 8, power 0. Raise own defenses while lowering attack and magic. Self friendlies; MP 8; hits 1; accuracy 100; stagger 0.

### Lila — 6

Martial physical damage and self recovery.

Sprite `100013806` (GL); stat/MR budget: Firion. Growth: Cloud.

- Awakening 1: Fire Slam [421010]; Fulminating Strike [445100]; Light of Rebellion [1353]; Physical Attack +30% [1273]; Fist of Vigor [486003].
- Awakening 2: Fira Slam [421020]; Bravery on Stagger [1288]; Nullify Instant Death [1325]; Fist of Fortification [486006]; Fist of Fury [486009]; Crushing Grasp [486012].
- Awakening 3: Firaga Slam [421030]; Saber of Adversity [445110]; Regen on Stagger [1286].
- Awakening 4: Fulminating Strike+ [445120]; Auto-Regen [1077].
- MR 1: Restore HP on Stagger [1284].
- MR 3: Chakra [400440]; Restore HP on Critical Hit [1322].
- MR 7: Vigilance [1048].
- MR 9: Arms Akimbo [400650].

Supplemental player copies (native source ID; final MP/power):

- Fist of Vigor ← Fist of Vigor [502230, enemy]: MP 12, power 14. Non-elemental physical damage; power 14. Also raise own attack by 50%. Single enemies; MP 12; hits 1; accuracy 100; stagger 17.
- Fist of Fortification ← Fist of Fortification [502370, enemy]: MP 20, power 18. Non-elemental physical damage; power 18. Also reduce own physical/magic damage taken by 30%. Single enemies; MP 20; hits 1; accuracy 100; stagger 17.
- Fist of Fury ← Fist of Fury [505060, enemy]: MP 14, power 24. Non-elemental physical damage; power 24. Single enemies; MP 14; hits 1; accuracy 100; stagger 25.
- Crushing Grasp ← Crushing Grasp [502240, enemy]: MP 22, power 28. Non-elemental physical damage; power 28. Apply Paralyzation (50%). Single enemies; MP 22; hits 1; accuracy 100; stagger 25.

### Mystea — 5

Magic tank, barriers and counter magic.

Sprite `100011005` (GL); stat/MR budget: Cecil. Growth: Terra.

- Awakening 1: Shell [230060]; Light Ray [486112]; Dazing Mist [486118].
- Awakening 2: Shellga [230070]; Manaward [220410]; Magic Defense +20% [1315]; Shell at Half HP [1299]; Magic Counter [1030]; Evasion Ward [486109]; Banishra Ray [486121].
- Awakening 3: Reflect [230120]; Auto-Shell [1073]; Shell Opener [1291]; Mighty Guard [486103]; Dystopia [486115].
- Awakening 4: Foul of the Seventh Dawn [220510].
- MR 1: Magic Barrier [1395].
- MR 3: Reflect at Half HP [1303].
- MR 7: Indomitable Spirit [1402]; Moiety Mirror [486106]; Magic Defense +10% [1314].

Supplemental player copies (native source ID; final MP/power):

- Mighty Guard ← Mighty Guard [500860, enemy]: MP 40, power 0. Reduce party physical and magic damage taken by 30%. Group friendlies; MP 40; hits 1; accuracy 100; stagger 25.
- Moiety Mirror ← Moiety’s Mirror [400790, native]: MP 30, power 0. Choose a physical and magic counter; reduce incoming damage this turn. Self friendlies; MP 30; hits 1; accuracy 100; stagger 0.
- Evasion Ward ← Scatter Feathers [500700, enemy]: MP 20, power 0. Raise own physical evasion by 50%. Self friendlies; MP 20; hits 1; accuracy 100; stagger 25.
- Light Ray ← Laser [500310, enemy]: MP 10, power 18. Light magic damage; power 18. Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Dystopia ← Dystopia [505860, enemy]: MP 26, power 26. Dark magic damage; power 26. Group enemies; MP 26; hits 1; accuracy 100; stagger 12.
- Dazing Mist ← Pollen [500690, enemy]: MP 12, power 0. Apply Confusion (100%). Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- Banishra Ray ← Banishra [240240, enemy]: MP 15, power 22. Light magic damage; power 22. Single enemies; MP 15; hits 2; accuracy 100; stagger 19.

### Reberta (JP) — 5

Dragoon with fire/wind spear attacks.

Sprite `100014405` (GL); stat/MR budget: Clive. Growth: Cloud.

- Awakening 1: Fire Surge [421040]; Aero Surge [421310]; Boundless Flames [1460]; Breath Wing [486203].
- Awakening 2: Fira Surge [421050]; Aerora Surge [421320]; Rising Flames [448000]; Flame Lance [486212].
- Awakening 3: Firaga Surge [421060]; Aeroga Surge [421330]; Heatwave [448010]; Clive’s Limit Break [1442]; Silver Lance [486206]; Branch Spear [486209].
- Awakening 4: Phase Echo [1360]; Quick Hit [1359].
- MR 1: Fill LB on Defeating Foes [1320].
- MR 3: Jump [400210]; Reflex [1257]; Overwhelm [1437]; HP +10% [1377].
- MR 7: Mirage [400670]; Bonus Damage [1335]; Fire Weapon [1010].

Supplemental player copies (native source ID; final MP/power):

- Breath Wing ← Breath Wing [500460, enemy]: MP 12, power 12. Wind physical damage; power 12. Group enemies; MP 12; hits 3; accuracy 100; stagger 12.
- Silver Lance ← Silver Lance [501260, enemy]: MP 25, power 36. Non-elemental physical damage; power 36. Single enemies; MP 25; hits 1; accuracy 100; stagger 25.
- Branch Spear ← Branch Spear [503780, enemy]: MP 25, power 36. Earth physical damage; power 36. Single enemies; MP 25; hits 1; accuracy 100; stagger 20.
- Flame Lance ← Spew Flames [502010, enemy]: MP 20, power 24. Fire physical damage; power 24. Single enemies; MP 20; hits 3; accuracy 100; stagger 25.

### Snow White — 7

Dark physical drain and risk/reward.

Sprite `336000207` (GL); stat/MR budget: Cecil. Growth: Cloud.

- Awakening 1: Dark Blade [420300]; Dark Sword [1457]; Leech [486303].
- Awakening 2: Darkra Blade [420310]; Sleep Slam [422020]; Drain [220300]; Predation [486306]; Revenge Strike [486312]; Binding Sweep [486315].
- Awakening 3: Drain Knife [422040]; Darkga Blade [420320]; Purging Blade [486309].
- Awakening 4: Regen Opener [1293].
- MR 1: Darkness [400490].
- MR 3: Dark Rite [1431]; Restore HP on Defeating Foes [1318]; Poison Powered [1067].
- MR 7: Staggeringly Risky [1405]; Vigorous Attacks [1358]; Regen at Half HP [1302].

Supplemental player copies (native source ID; final MP/power):

- Leech ← Leech [500520, enemy]: MP 12, power 12. Non-elemental physical damage; power 12. Apply HP drain (100% of damage). Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- Predation ← Predation [570710, enemy]: MP 16, power 18. Non-elemental physical damage; power 18. Apply HP drain (100% of damage). Single enemies; MP 16; hits 1; accuracy 100; stagger 20.
- Purging Blade ← Purging Blade [505960, enemy]: MP 32, power 36. Dark physical damage; power 36. Also reduce enemy physical and magic defense. Single enemies; MP 32; hits 1; accuracy 100; stagger 16.
- Revenge Strike ← Revenge Blast [501630, enemy]: MP 16, power 24. Non-elemental physical damage; power 24. Single enemies; MP 16; hits 1; accuracy 100; stagger 25.
- Binding Sweep ← Cling [500910, enemy]: MP 14, power 12. Non-elemental physical damage; power 12. Apply Slow (30%). Group enemies; MP 14; hits 1; accuracy 100; stagger 12.

### Aria — 5

Water support, healing and water blade.

Sprite `203000905` (GL); stat/MR budget: Leah. Growth: Terra.

- Awakening 1: Water Blade [420100]; Cure of the Seventh Dawn [220480]; Water’s Protection [1462]; Healing Rain [486403]; Rejuvenate [486409]; Banish Ray [486418].
- Awakening 2: Watera Blade [420110]; Cure II of the Seventh Dawn [220490]; Purify [414500]; Soothing Rain [486406]; Undertow [486412]; Bubble Breath [486415].
- Awakening 3: Waterga Blade [420120]; Cure III of the Seventh Dawn [220500].
- Awakening 4: Preventive Care [1352].
- MR 1: First Aid [400550]; Angelic Advocate [1401]; Restore MP when Taking Damage [1356].
- MR 3: Healing Magic +10% [1282]; Auto MP Restore (L) [1256].
- MR 7: Earth Immunity [1365].
- MR 9: Auto-Cure Ailments [1305].

Supplemental player copies (native source ID; final MP/power):

- Healing Rain ← Cure [245000, enemy]: MP 10, power 80. Restore healing power 80. Group friendlies; MP 10; hits 1; accuracy 100; stagger 20.
- Soothing Rain ← Cura [245010, enemy]: MP 18, power 200. Restore healing power 200. Group friendlies; MP 18; hits 1; accuracy 100; stagger 22.
- Rejuvenate ← Rejuvenate [502020, enemy]: MP 12, power 20. Restore 20% max HP. Self friendlies; MP 12; hits 1; accuracy 100; stagger 25.
- Undertow ← Graceful Deluge [501400, enemy]: MP 20, power 12. Water magic damage; power 12. Also reduce enemy physical and magic defense. Group enemies; MP 20; hits 3; accuracy 100; stagger 12.
- Bubble Breath ← Bubble Breath [501680, enemy]: MP 24, power 24. Water magic damage; power 24. Group enemies; MP 24; hits 3; accuracy 100; stagger 12.
- Banish Ray ← Banish [240230, enemy]: MP 5, power 14. Light magic damage; power 14. Single enemies; MP 5; hits 1; accuracy 100; stagger 17.

### Eiko — 7

Summoner with wind magic and revival.

Sprite `209000707` (GL); stat/MR budget: Ayaka. Growth: Terra.

- Awakening 1: Aero of the Seventh Dawn [220450]; Nullify Charm [1111].
- Awakening 2: Aero II of the Seventh Dawn [220460]; Raise [210140]; Nullify Silence [1107].
- Awakening 3: Ifrit [430990]; Shiva [431000]; Aero III of the Seventh Dawn [220470]; Banishga Ray [486509]; Aerora Gust [486512]; Healing Breeze [486515].
- Awakening 4: Reraise [210160]; Unlock Magic [1417]; Firaga Burst [486503]; Blizzaga Burst [486506].
- MR 3: Auto-LB Charge [1479].
- MR 5: LB Double Charge [1000].
- MR 7: Recuperate LB [1338]; Halve Encounters [1053].
- MR 9: LB Triple Charge [1031]; Break the Limit [1047].

Supplemental player copies (native source ID; final MP/power):

- Firaga Burst ← Firaga [225020, native]: MP 60, power 55. Fire magic damage; power 55. Group enemies; MP 60; hits 3; accuracy 100; stagger 21.
- Blizzaga Burst ← Blizzaga [225050, native]: MP 60, power 55. Ice magic damage; power 55. Group enemies; MP 60; hits 3; accuracy 100; stagger 21.
- Banishga Ray ← Banishga [240250, enemy]: MP 25, power 30. Light magic damage; power 30. Single enemies; MP 25; hits 3; accuracy 100; stagger 21.
- Aerora Gust ← Aerora [225130, native]: MP 30, power 33. Wind magic damage; power 33. Group enemies; MP 30; hits 2; accuracy 100; stagger 19.
- Healing Breeze ← Curaga [245020, enemy]: MP 35, power 600. Restore healing power 600. Group friendlies; MP 35; hits 1; accuracy 100; stagger 25.

### Alice/Half Nightmare — NV Brave Shift

Ice physical with burst and HP tradeoffs.

Sprite `336000127` (JP); stat/MR budget: Squall. Growth: Cloud.

- Awakening 1: Ice Slam [486660]; Boundless Void [446300]; Critical Hit Rate +10% [1247]; Rage [486606]; Throat Strike [486609]; Binding Cut [486618].
- Awakening 2: Icera Slam [486663]; Bravery Opener [1294]; Disorienting Cut [486615].
- Awakening 3: Icega Slam [486666]; Purging Blade [446310]; Nullify Sleep [1106]; Absolving Hail [486603]; Ruthless Rampage [486612]; Critical Hit Rate +20% [1480].
- MR 3: Deathblow [400530]; Hale and Hearty [1330].
- MR 7: Critical Stagger [1388]; Fill LB on Critical Hit [1324].
- MR 9: Critical Boost [1234].

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

### Moogle of Narshe Mog — 5

Wind magic, dance and speed support.

Sprite `206003005` (GL); stat/MR budget: Tidus. Growth: Terra.

- Awakening 1: Aero [220170]; Haste [230130]; Gust Dance [486703]; Mystery Waltz [486709].
- Awakening 2: Aerora [220180]; Resist Wind [1248]; Speed +10% [1277]; Cyclone [486706]; Mega Berserk [486715].
- Awakening 3: Aeroga [220190]; Slow [230150]; Haste Opener [1292]; Haste on Stagger [1287]; Alluring Dance [486712].
- Awakening 4: Hastega [230140]; Slowga [230160].
- MR 1: Wait [400760].
- MR 3: First Strike [1049]; No Encounters [1052].
- MR 5: Speed +5% [1316]; LB Charge Opener [1004].

Supplemental player copies (native source ID; final MP/power):

- Gust Dance ← Wind Slash [500430, enemy]: MP 12, power 12. Wind magic damage; power 12. Group enemies; MP 12; hits 1; accuracy 100; stagger 12.
- Cyclone ← Cyclone [500410, enemy]: MP 22, power 24. Wind magic damage; power 24. Group enemies; MP 22; hits 1; accuracy 100; stagger 12.
- Mystery Waltz ← Mystery Waltz [570450, enemy]: MP 12, power 10. Drain MP; power 10. Apply MP drain (100% of damage). Single enemies; MP 12; hits 1; accuracy 100; stagger 0.
- Alluring Dance ← Alluring Dance [570430, enemy]: MP 32, power 0. Apply Charme (100%). Group enemies; MP 32; hits 1; accuracy 100; stagger 0.
- Mega Berserk ← Mega Berserk [235080, native]: MP 22, power 0. Apply Berserk (100%). Group enemies; MP 22; hits 1; accuracy 100; stagger 25.

### Lilith — 5

Dark counter tank and protective magic.

Sprite `401005905` (GL); stat/MR budget: Cecil. Growth: Cloud.

- Awakening 1: Dark [220390].
- Awakening 2: Darkra [220520]; Power Stagger [414600]; Poison Mist [486812]; Shock Claw [486815].
- Awakening 3: Darkga [220400]; Shadowbringer [445310]; Royal Guard [414610]; Resist Dark [1253]; Protect at Half HP [1300]; Seal of Conviction [486803]; Dark Sunder [486806]; Dark Aegis [486809].
- Awakening 4: Paladin’s Code [1413]; Dark Immunity [1369].
- MR 3: Cover [400380]; Magic Counter [1036].
- MR 7: Critical Counter [1333]; Grit [1259].
- MR 9: Riposte [1339].

Supplemental player copies (native source ID; final MP/power):

- Seal of Conviction ← Seal of Conviction [505580, enemy]: MP 32, power 30. Dark physical damage; power 30. Group enemies; MP 32; hits 2; accuracy 100; stagger 12.
- Dark Sunder ← Darkness’s Dawn [505560, enemy]: MP 28, power 0. Reduce enemy physical and magic defense by 30% for 3 turns. Group enemies; MP 28; hits 1; accuracy 100; stagger 12.
- Dark Aegis ← Darkness’s Advance [505570, enemy]: MP 40, power 0. Reduce party physical and magic damage taken by 30%. Group friendlies; MP 40; hits 1; accuracy 100; stagger 25.
- Poison Mist ← Poison Gas [500560, enemy]: MP 18, power 0. Apply Poison (50%). Group enemies; MP 18; hits 1; accuracy 100; stagger 12.
- Shock Claw ← Shock Claw [503240, enemy]: MP 22, power 28. Non-elemental physical damage; power 28. Apply Paralyzation (100%). Single enemies; MP 22; hits 1; accuracy 100; stagger 25.

### Dragon Knight Freya — 5

Aerial light physical and water lance.

Sprite `209001805` (GL); stat/MR budget: Noctis. Growth: Cloud.

- Awakening 1: Water Surge [421190]; Flash Flood [486906]; Sonic Boom [486918].
- Awakening 2: Warp-Strike [447810]; Watera Surge [421200]; Nullify Slow [1116]; Crystal Lance [486903]; Venom Lance [486915].
- Awakening 3: Plunge [447800]; Waterga Surge [421210]; Deft Warp [1361]; Gungnir [486909]; Hydro Lance [486912].
- Awakening 4: Warp Crit [1466].
- MR 3: Preemptive Strike [1394].
- MR 5: Lance [400280].
- MR 7: Momentum Shift [1438]; Light Eater [1349].
- MR 9: Versatility [1340]; Hit and Run [1334].

Supplemental player copies (native source ID; final MP/power):

- Crystal Lance ← Crystal Lance [501610, enemy]: MP 20, power 30. Non-elemental physical damage; power 30. Single enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Flash Flood ← Flash Flood [500770, enemy]: MP 12, power 18. Water physical damage; power 18. Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- Gungnir ← Gungnir [505810, enemy]: MP 40, power 40. Non-elemental physical damage; power 40. Single enemies; MP 40; hits 1; accuracy 100; stagger 25.
- Hydro Lance ← Hydro Breath [503830, enemy]: MP 26, power 28. Water physical damage; power 28. Group enemies; MP 26; hits 1; accuracy 100; stagger 20.
- Venom Lance ← Poison Tail [500870, enemy]: MP 15, power 24. Non-elemental physical damage; power 24. Apply Poison (100%). Single enemies; MP 15; hits 1; accuracy 100; stagger 25.
- Sonic Boom ← Sonic Boom [500440, enemy]: MP 12, power 18. Wind physical damage; power 18. Single enemies; MP 12; hits 1; accuracy 100; stagger 25.

### Trance Terra — 5

Dark/fire magic, poison and costly finishers.

Sprite `206000125` (GL); stat/MR budget: Shantotto. Growth: Terra.

- Awakening 1: Poison [220250]; Fire [220010]; The Federation’s Fiend [1432]; Magic Attack +30% [1275].
- Awakening 2: Nightmare Scythe [447300]; Bio [220260]; Fira [220020]; Firaga [220030]; MP +20% [1381].
- Awakening 3: Salvation Scythe [447310]; Death [220320]; Meltdown [220380]; Spill [487103]; Trance Judgment [487106]; Judgment Shadow [487109]; Hell Pillar [487112].
- Awakening 4: Meteor [220350]; Ultima [220340]; Play Rough [1433].
- MR 1: Restore MP on Defeating Foes [1319]; Tenebrous Rites [1430].
- MR 7: Area Effect Adept [1351]; Piercing Magic [1065].
- MR 9: Dualcast [400730]; Fire Eater [1038].

Supplemental player copies (native source ID; final MP/power):

- Spill ← Spill [414300, native]: MP 46, power 45. Dark magic damage; power 45. Group enemies; MP 46; hits 2; accuracy 100; stagger 35.
- Trance Judgment ← Execution [505450, enemy]: MP 35, power 36. Dark magic damage; power 36. Group enemies; MP 35; hits 3; accuracy 100; stagger 12.
- Judgment Shadow ← Judgment of the Shadow [503120, enemy]: MP 30, power 30. Non-elemental magic damage; power 30. Group enemies; MP 30; hits 1; accuracy 100; stagger 25.
- Hell Pillar ← Hell’s Pillar [505470, enemy]: MP 26, power 24. Fire magic damage; power 24. Group enemies; MP 26; hits 3; accuracy 100; stagger 12.

### Charming Kitty Ariana — 5

Healing singer with control and arcane attacks.

Sprite `401002405` (GL); stat/MR budget: Ayaka. Growth: Terra.

- Awakening 1: Esuna [210120]; Bravery [230100]; Healing Refrain [487203]; Lullaby [487209].
- Awakening 2: Nullify Berserk [1114]; Nullify Confuse [1109]; Blindga [487212]; Silencega [487215]; Starlight Refrain [487218].
- Awakening 3: Gravity [220280]; Haste at Half HP [1301]; Restoring Refrain [487206].
- Awakening 4: Confuse [230180]; Graviga [220290].
- MR 1: Focus [400460]; Skill Flow [1464].
- MR 3: Recover [400540]; Light Immunity [1368].
- MR 7: Observe and Charge LB [1392]; Heal on Sweeping Stagger [1391]; Shell on Stagger [1476].

Supplemental player copies (native source ID; final MP/power):

- Healing Refrain ← Cure [215000, native]: MP 12, power 200. Restore healing power 200. Group friendlies; MP 12; hits 1; accuracy 100; stagger 50.
- Restoring Refrain ← Cura [215010, native]: MP 25, power 500. Restore healing power 500. Group friendlies; MP 25; hits 1; accuracy 100; stagger 55.
- Lullaby ← Lullaby [570440, enemy]: MP 8, power 0. Apply Sleep (100%). Single enemies; MP 8; hits 1; accuracy 100; stagger 0.
- Blindga ← Blindga [235010, native]: MP 20, power 0. Apply Blind (50%). Group enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Silencega ← Silencega [235020, native]: MP 20, power 0. Apply Silence (50%). Group enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Starlight Refrain ← Array: Light of Destruction [503620, enemy]: MP 24, power 28. Light magic damage; power 28. Group enemies; MP 24; hits 1; accuracy 100; stagger 12.

### Elephim — 7

Buff/debuff bard with ranged attacks.

Sprite `100017107` (GL); stat/MR budget: Vaan. Growth: Terra.

- Awakening 1: Debrave [230190]; Blind [230020]; Faith [230110]; Berserk [230170]; Faith Opener [1295]; Sleep [487303]; Defaith [487306].
- Awakening 2: Rapid Fire [414200]; Throw Down the Gauntlet [1451]; Victor’s Reprieve [1372]; Deprotect on Stagger [1235]; Debravega [487309]; Defaithga [487312]; Sleepga [487315].
- Awakening 3: Disorder [414210]; Deprotect Opener [1296]; Deshell Opener [1297]; Berserker Samba [487324]; Auto-Faith [1304]; Auto-Haste [1074].
- Awakening 4: Rallying Song [487318]; Inspire [487321].

Supplemental player copies (native source ID; final MP/power):

- Sleep ← Sleep [230010, native]: MP 5, power 0. Apply Sleep (80%). Single enemies; MP 5; hits 1; accuracy 100; stagger 25.
- Defaith ← Defaith [230200, native]: MP 6, power 0. Apply IntelligenceDown (100%). Single enemies; MP 6; hits 1; accuracy 100; stagger 25.
- Debravega ← Debravega [235050, native]: MP 24, power 0. Apply AttackDown (100%). Group enemies; MP 24; hits 1; accuracy 100; stagger 25.
- Defaithga ← Defaithga [235060, native]: MP 24, power 0. Apply IntelligenceDown (100%). Group enemies; MP 24; hits 1; accuracy 100; stagger 25.
- Sleepga ← Sleepga [235000, native]: MP 20, power 0. Apply Sleep (50%). Group enemies; MP 20; hits 1; accuracy 100; stagger 25.
- Rallying Song ← Get them! [501120, enemy]: MP 45, power 0. Raise party magic and speed by 50%. Group friendlies; MP 45; hits 0; accuracy 100; stagger 25.
- Inspire ← Inspire [570130, enemy]: MP 42, power 0. Raise an ally’s attack/magic by 50% and reduce incoming physical/magic damage by 30%. Single friendlies; MP 42; hits 1; accuracy 100; stagger 0.
- Berserker Samba ← Samba de Flan [570420, enemy]: MP 28, power 0. Apply Berserk (100%). Group enemies; MP 28; hits 1; accuracy 100; stagger 0.

### Jade — 5

Lightning martial attacker and crowd damage.

Sprite `337001205` (GL); stat/MR budget: Cloud. Growth: Cloud.

- Awakening 1: Thunder Blade [420070]; Sparkstrike [421160]; Rocket Punch [487409]; Charge [487412]; Radiant Knight [1459].
- Awakening 2: Thundara Blade [420080]; Sparkstrike II [421170]; Resist Lightning [1250]; Physical Attack +10% [1308]; Volt Palm [487403]; Gigavolt Strike [487406].
- Awakening 3: Thundaga Blade [420090]; Sparkstrike III [421180].
- Awakening 4: Lightning Immunity [1366].
- MR 1: Restore MP on Critical Hit [1323]; Vigorous Staggerer [1371].
- MR 3: Bladeblitz [400310].
- MR 5: Reckless Abandonment [400700]; Power Stagger [1385].
- MR 7: Physical Counter [1035].

Supplemental player copies (native source ID; final MP/power):

- Volt Palm ← Megavolt [500180, enemy]: MP 14, power 17. Thunder physical damage; power 17. Apply Paralyzation (100%). Single enemies; MP 14; hits 1; accuracy 100; stagger 25.
- Gigavolt Strike ← Gigavolt [500400, enemy]: MP 20, power 24. Thunder physical damage; power 24. Single enemies; MP 20; hits 2; accuracy 100; stagger 25.
- Rocket Punch ← Rocket Punch [500730, enemy]: MP 10, power 18. Non-elemental physical damage; power 18. Single enemies; MP 10; hits 1; accuracy 100; stagger 25.
- Charge ← Charge [501040, enemy]: MP 12, power 24. Non-elemental physical damage; power 24. Apply Paralyzation (50%). Single enemies; MP 12; hits 1; accuracy 70; stagger 25.

### Spirited Heart Primm — NV Super Limit Burst

Mixed elemental sabers and support.

Sprite `304000717` (GLW); stat/MR budget: Onion Knight. Growth: Lightning.

- Awakening 1: Slice & Dice - Wind [421280]; Stone Blade [420160]; Supercharged Driver [1461]; Cure [487503].
- Awakening 2: Slice & Dice - Wind II [421290]; Stonera Blade [420170]; Protect on Stagger [1390]; Resist Fire [1011]; Cura [487506]; Firestorm Saber [487512]; Atomic Saber [487515].
- Awakening 3: Slice & Dice - Wind III [421300]; Stonega Blade [420180]; Moonlightbringer [445300].
- Awakening 4: Ribbon [1355]; Curaga [487509].
- MR 3: Magic Boost [400660]; Staggering Spells [1370]; Weak Element Stagger Power +30% [1329].
- MR 5: Fill Gauge [400770]; Magic Attack +10% [1310].
- MR 7: MP +30% [1382].

Supplemental player copies (native source ID; final MP/power):

- Cure ← Cure [240010, enemy]: MP 6, power 200. Restore healing power 200. Single friendlies; MP 6; hits 1; accuracy 100; stagger 50.
- Cura ← Cura [240020, enemy]: MP 18, power 500. Restore healing power 500. Single friendlies; MP 18; hits 1; accuracy 100; stagger 55.
- Curaga ← Curaga [240030, enemy]: MP 50, power 1500. Restore healing power 1500. Single friendlies; MP 50; hits 1; accuracy 100; stagger 60.
- Firestorm Saber ← Firestorm [500360, enemy]: MP 20, power 18. Fire physical damage; power 18. Group enemies; MP 20; hits 1; accuracy 100; stagger 12.
- Atomic Saber ← Atomic Ray [500380, enemy]: MP 20, power 24. Fire physical damage; power 24. Single enemies; MP 20; hits 1; accuracy 100; stagger 25.

### Relm — 5

Painter with lightning magic and mimicry.

Sprite `206001005` (GL); stat/MR budget: Shantotto. Growth: Terra.

- Awakening 1: Thunder [220090]; Stagger Power +20% [1279]; Fire Beam [487606]; Drain [487615]; Fulminating Spells [1440].
- Awakening 2: Thundara [220100]; Thundaga [220110]; Nullify Poison [1104]; Bioblaster [487603]; El Nino [487609]; Banishra Canvas [487618].
- Awakening 3: Forbidden Ars Magna [487612].
- Awakening 4: Flare [220330]; Add Confuse [1237]; Mind Blast [487621].
- MR 1: Arcane Reclamation [1328].
- MR 3: Fill LB on Stagger [1280].
- MR 5: Spell Drinker [400720].
- MR 7: Sharp Mind [1332]; Wind Immunity [1364].
- MR 9: Mimic [400330].

Supplemental player copies (native source ID; final MP/power):

- Bioblaster ← Bioblaster [500970, enemy]: MP 18, power 12. Non-elemental magic damage; power 12. Apply Poison (70%). Group enemies; MP 18; hits 1; accuracy 100; stagger 12.
- Fire Beam ← Fire Beam [500980, enemy]: MP 12, power 18. Fire magic damage; power 18. Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- El Nino ← El Niño [501010, enemy]: MP 20, power 18. Water magic damage; power 18. Group enemies; MP 20; hits 1; accuracy 100; stagger 12.
- Forbidden Ars Magna ← 禁呪アルス・マグナ [503930, enemy]: MP 26, power 26. Non-elemental magic damage; power 26. Group enemies; MP 26; hits 1; accuracy 100; stagger 45.
- Drain ← Drain [250300, enemy]: MP 12, power 12. Non-elemental magic damage; power 12. Apply HP drain (100% of damage). Single enemies; MP 12; hits 1; accuracy 100; stagger 20.
- Banishra Canvas ← Banishra [245300, enemy]: MP 20, power 18. Light magic damage; power 18. Group enemies; MP 20; hits 2; accuracy 100; stagger 14.
- Mind Blast ← Mind Blast [500750, enemy]: MP 45, power 24. Thunder magic damage; power 24. Apply Paralyzation (100%), Silence (100%), Poison (100%). Single enemies; MP 45; hits 1; accuracy 100; stagger 25.

### Rikku (FFX-2) — 6

Thief, item utility and fire physical breaks.

Sprite `249000206` (GL); stat/MR budget: Vaan. Growth: Cloud.

- Awakening 1: Steal Strength [446840]; Steal Speed [446850]; Thievery [1426]; Flash Bomb [487703]; Sleep Needle [487706]; Poison Needle [487709].
- Awakening 2: Red Spiral [447400]; Discerning Eye [1056].
- Awakening 3: White Whorl [447410].
- Awakening 4: Treasure Hunter [1387]; One for the Road [1435]; Wings of Freedom [1436].
- MR 1: Steal [400260]; Gil Farmer [400400].
- MR 3: Gil Farmer on Stagger [1386]; Pickpocket’s Prowess [1055].
- MR 5: Mug [400270]; Gil Toss [400250].
- MR 7: Pharmacology [1044].
- MR 9: Misfortune [400750]; Double Gil [1050].

Supplemental player copies (native source ID; final MP/power):

- Flash Bomb ← Flash Bomb [501020, enemy]: MP 10, power 6. Non-elemental physical damage; power 6. Apply Blind (30%). Group enemies; MP 10; hits 1; accuracy 100; stagger 12.
- Sleep Needle ← Sleep Needle [500300, enemy]: MP 8, power 12. Non-elemental physical damage; power 12. Apply Sleep (100%). Single enemies; MP 8; hits 1; accuracy 100; stagger 25.
- Poison Needle ← Poison Needle [500280, enemy]: MP 8, power 12. Non-elemental physical damage; power 12. Apply Poison (100%). Single enemies; MP 8; hits 1; accuracy 100; stagger 25.

### Nalu — 5

Lightning physical, criticals and analysis.

Sprite `100015405` (GL); stat/MR budget: Cloud. Growth: Cloud.

- Awakening 1: Thunder Surge [421130]; Libra [210220]; Broadsword Mastery [1420]; Thunder Spear [487803]; Lightning Sweep [487806]; Needle [487812].
- Awakening 2: Braver [446000]; Thundara Surge [421140]; Lightning Strike [447500].
- Awakening 3: Cross-Slash [446010]; Thundaga Surge [421150]; Thunderfall [447510]; Chain Lance [487809].
- Awakening 4: Signature Moves [1418].
- MR 5: Scan and Strike [1399]; Bonus Phase Stagger Boost [1400].
- MR 7: Restore MP on Attack [1124]; Thunder Weapon [1028].
- MR 9: Lightning Eater [1347]; Pilebunker [1404].

Supplemental player copies (native source ID; final MP/power):

- Thunder Spear ← Thunder Beam [501000, enemy]: MP 12, power 18. Thunder physical damage; power 18. Single enemies; MP 12; hits 1; accuracy 100; stagger 25.
- Lightning Sweep ← Lightning [500390, enemy]: MP 12, power 12. Thunder physical damage; power 12. Group enemies; MP 12; hits 2; accuracy 100; stagger 12.
- Chain Lance ← Chain Spark [220120, native]: MP 30, power 30. Thunder physical damage; power 30. Group enemies; MP 30; hits 3; accuracy 100; stagger 21.
- Needle ← Needle [500260, enemy]: MP 8, power 18. Non-elemental physical damage; power 18. Single enemies; MP 8; hits 1; accuracy 100; stagger 25.

### Elza — 5

Dark/water physical and sustained pressure.

Sprite `302000605` (GL); stat/MR budget: Tidus. Growth: Cloud.

- Awakening 1: Dark Surge [422050]; Spiral Cut [447000]; Slice & Dice - Water [421220]; Skyward Dreams [1434].
- Awakening 2: Darkra Surge [422060]; Slice & Dice - Water II [421230]; Speed +20% [1317]; Queenly Rend [487903]; Venom Sweep [487909].
- Awakening 3: Darkga Surge [422070]; Energy Rain [447010]; Spiral Cut+ [447020]; Slice & Dice - Water III [421240]; Shred [487906]; Black Tide [487912].
- MR 1: Rearguard [1383].
- MR 7: Tip-Top Shape [1428]; LB Shield [1403]; Essence of Mundanity [1389]; Vital Strike [1398].
- MR 9: Dark Eater [1350].

Supplemental player copies (native source ID; final MP/power):

- Queenly Rend ← Queenly Whip [505910, enemy]: MP 16, power 16. Dark physical damage; power 16. Also reduce enemy attack and magic. Single enemies; MP 16; hits 2; accuracy 100; stagger 25.
- Shred ← Shred [503580, enemy]: MP 25, power 35. Non-elemental physical damage; power 35. Single enemies; MP 25; hits 1; accuracy 100; stagger 25.
- Venom Sweep ← Digestive Fluid [500490, enemy]: MP 15, power 12. Non-elemental physical damage; power 12. Apply Poison (50%). Group enemies; MP 15; hits 1; accuracy 100; stagger 12.
- Black Tide ← Sludge [503660, enemy]: MP 26, power 28. Water physical damage; power 28. Group enemies; MP 26; hits 1; accuracy 100; stagger 12.

### Lunera — 6

Wind physical and stagger support.

Sprite `100007506` (GL); stat/MR budget: Bartz. Growth: Cloud.

- Awakening 1: Aero Blade [420130]; Guiding Wind [1458].
- Awakening 2: Aerora Blade [420140]; Crushing Blade [445500]; Torrential Hew [414400]; Shamshir [488003]; Gale Volley [488006]; Venom Gale [488015].
- Awakening 3: Aeroga Blade [420150]; Wind Cutter Blade [445510]; Aquatic Synergy [414410]; Merciless Gale [488009]; Star Volley [488012].
- Awakening 4: Alluvial Edge [1448]; Alluvial Flourish [1449].
- MR 3: HP Stroll [1066]; Spry Steps [1258]; Wind Eater [1345].
- MR 7: Enemy Lure [1054].
- MR 9: Drop Rate Up [1341].

Supplemental player copies (native source ID; final MP/power):

- Shamshir ← Shamshir [500450, enemy]: MP 16, power 24. Wind physical damage; power 24. Single enemies; MP 16; hits 1; accuracy 100; stagger 25.
- Gale Volley ← Wing Flap [503720, enemy]: MP 20, power 20. Wind magic damage; power 20. Group enemies; MP 20; hits 3; accuracy 100; stagger 20.
- Merciless Gale ← Merciless Judgment [505270, enemy]: MP 38, power 40. Wind physical damage; power 40. Single enemies; MP 38; hits 3; accuracy 100; stagger 25.
- Star Volley ← Flare Star [500900, enemy]: MP 32, power 30. Non-elemental physical damage; power 30. Group enemies; MP 32; hits 1; accuracy 100; stagger 12.
- Venom Gale ← Venom Breath [501900, enemy]: MP 24, power 18. Wind physical damage; power 18. Apply Poison (30%). Group enemies; MP 24; hits 1; accuracy 100; stagger 12.

## Research and validation limits

Selected hosted packs were checked against their published SHA-256 values, including base packs for shifted forms. Unit records, selected-form sprite motions and LB profiles were inspected. FFBE themes are references, not imported combat numbers. The archived Global datamine is `aEnigmatic/ffbe` at `95727376e82d27acc1290b6dc8ad27ce3c89ea71`; hosted merged records also cover Japanese and post-archive forms. Reberta’s Japanese hosted record has no translated skill list; her requested physical dragoon role and the original Reberta elemental/jump theme guide that kit.

Automated checks cover portable configs, unique allocation, native stat/MR budgets, mastery caps, owner-condition rebinding, native table patch serialization, and optional-pack lifecycle. They do not establish live-game balance or prove every animation exists in the demo. The existing unverified-skill visibility/animation toggles continue to govern demo animation repairs.

## Full-game release review

Re-audit native stats, level curves, skill mechanics and unlock ranks; private command/LB conditions and IDs; summon availability; selected form/LB presentation; and vendor/acquisition availability. Preserve user edits and require an explicit reset to apply revised recipes. See README’s running full-release checklist.
