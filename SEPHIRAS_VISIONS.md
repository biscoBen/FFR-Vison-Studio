# Sephira’s Visions

30 optional, editable presets using the requested FFBE forms. Enable the section on the home page, then build/install. First enable downloads only the missing selected artwork and adds the profiles after all preparations succeed.

Turning the section off keeps edits and removed entries; its units and acquisition caves are omitted by the next build. **Restore missing** adds removed presets without resetting existing ones. **Reset all presets** or a card’s **Reset to preset** replaces its kit and appearance, preserves its IDs and acquisition location, and backs up the previous roster in Studio’s character-config backups.

An existing custom Crystal Fina is adopted with her current edits and acquisition intact. Reset her explicitly to use this balanced recipe. Other user-added copies and original vision/party edits are preserved.

## Balance and coverage

- Every preset copies a native level-one stat profile with five learned MR rewards at ranks 1, 3, 5, 7 and 9. MR 2/6/8 give three relevant permanent stats (normalized 5/10/15 points; HP ×6, MP ×2); MR 4 and 9 each give +8 AP. MR 9 also grants the Spirit mastery. MR 0 is the native empty starting rank; every rank from 1 to 9 has a reward. Native physical or magic growth curves are used.
- Existing native grants retain their mechanics. Supplemental skills come from the wider native/enemy catalog on private player copies: zero-MP enemy attacks receive MP costs; excessive accuracy, multipliers and hit counts are reduced. Group spells/healing cost more than comparable single-target spells. No FFBE multipliers or FFBE stat conversion are imported. LBs retain one native resonance’s total mechanics; selected elements/damage types follow the requested role.
- All 160 distinct active skills and 131 passives from the 15 excluded original visions are allocated. Each excluded active has one canonical allocation. All 75 original equipable MR rewards remain MR rewards, including 25 active skills at their original ranks and acquisition gates. All 131 original passives remain covered across the complete kits; supplementary awakening choices may repeat across visions. Additional native skills provide thematic attacks and support. Each new vision has its own correctly bound Spirit mastery wrapper.
- Command/LB-specific bonuses use private rebound copies. Native originals remain unchanged. Minfilia’s Dual Jobs selects her own identity. Specific skill bonuses remain grouped with their required attacks.
- Each odd MR rank has one learned ability, active or passive. The 150 slots contain 25 active rewards and 125 passive rewards. Supplemental passives move into awakening to make room for the original MR actives. Each complete kit retains its native counterpart’s passive count and a combined passive AP cost within 20%. Permanent MR stats, the Spirit wrapper and LB are excluded from these skill counts. Crystal Fina and Aria keep their reviewed kits unchanged. See [the MR restoration](docs/SEPHIRA_MR_RESTORATION.md) and [awakening balance report](docs/SEPHIRA_AWAKENING_BALANCE.md). Clive’s Eikon attacks and limit-break bonus remain on Reberta. Aria is sold in Mitra. Folka unlocks in Olderion’s item shop after its guardian story scene, at twice that shop’s highest other item price. The other 28 visions are challenge rewards at the matched original vision’s gate, with a separate Zoldaad cave for Barusa and Ariana. Acquisition remains editable.
- Great Dragon is retired from this collection and omitted from builds, including older tagged saved profiles. Reset all presets backs up and removes his old collection entry. His required original grants move to Reberta, Minfilia, Lila, Trance Terra and Primm. Untagged user-created Great Dragons are preserved.
- New enemy copies belong to the vision’s player command; enemy group-toggle partners are disabled so they cannot switch into unbalanced originals. Replacement bonuses retain native effects and equip costs, with a 20-AP floor for item bonuses that originally cost zero. Revision 5 replaces 52 reused rewards from kept visions with equipment/enemy bonuses and bounded enemy skills. Those protected MR rewards are absent from both awakening and MR; all excluded-vision grants remain allocated. The eight earlier low-tier alternatives remain available. Boss invulnerability and permanent attack buffs are replaced by finite native player effects; drain restores no more than damage dealt. Permanent MR rewards follow the same role-based three-stat budget for every preset. Alice’s three earth slams become ice slams with unchanged power/cost.
- Eiko uses the demo’s available Ifrit and Shiva summon commands; their native costs and mechanics are retained. Unreleased espers are not required.

The excluded originals are Tronn, Wilhelm, Warrior of Light, Firion, Onion Knight, Cecil, Bartz, Cloud, Squall, Zidane, Tidus, Shantotto, Vaan, Noctis and Clive. Their exact grants, native ranks, descriptions, mechanics and allocations are retained in `assets/sephira_visions/native_coverage.json`.

## Acquiring the visions

After obtaining the matched original, talk to its crystal again and select Challenge. The original replay remains available. Ownership or the original’s individual completion flag is checked before the menu, immediately before battle, and before rewards. Wilhelm uses his final quest step, not quest acceptance. Winning grants only missing team members; leaving, escaping or losing grants none. There are no farmable boss drops or XP. Each team shares one local-level boss budget, with staggered eight-action rotations and bounded healing. These are authored starting values; live balance still needs playtesting.

Tronn → Christine; Wilhelm → Barusa/Ariana; Warrior of Light → Lenneth/Crystal Fina; Firion → Lila/Fran; Onion Knight → Minfilia/Primm; Cecil → Snow White/Lilith/Mystea; Bartz → Fryevia/Lunera; Cloud → Nalu/Jade; Squall → A2/Alice; Zidane → Rikku/Eiko; Tidus → Elza/Mog; Shantotto → Trance Terra/Relm; Vaan → Lunafreya/Elephim; Noctis → Freya; Clive → Reberta.

Levels come from ordinary enemies in the encounter volume containing each shrine entrance (Earth Shrine’s inner floor for Tronn). See `assets/existing_visions/payload/sephira_challenges.json` for the native source tables, unlock evidence and local levels.

**Sephira visions: 1-gil Mitra shop** temporarily sells every enabled collection vision in Mitra’s item shop, without its normal story/challenge gate. Rebuild/install after switching. Turning it off restores the saved cave, crystal or shop assignments and prices; saved recipes and locations are never rewritten. Already purchased visions remain owned.

## Kit sizes

Untouched saved reward layouts migrate automatically once, with a roster backup. The update restores the original transferable MR actives and moves supplemental passives into awakening while preserving allocated IDs, artwork, permanent stat rewards, private combat recipes and acquisition choices. Deliberately edited affected MR slots and full awakening tiers report a conflict before building; use **Apply MR and acquisition update** after resolving it. Older recipes first receive their missing awakening bonuses. New presets include the current layout. Later edits remain yours. See [the complete MR allocation](docs/SEPHIRA_PASSIVE_MASTERY.md).

| Vision | Awakening abilities | Awakening bonuses | Awakening total | Additional MR abilities | Additional MR bonuses |
|---|---:|---:|---:|---:|---:|
| A2 | 17 | 7 | 24 | 2 | 3 |
| Christine | 15 | 6 | 21 | 1 | 4 |
| Crystal Fina | 20 | 5 | 25 | 0 | 5 |
| Barusa | 15 | 8 | 23 | 2 | 3 |
| Blue Sky Belle Fran | 17 | 4 | 21 | 0 | 5 |
| Oracle Maiden Lunafreya | 17 | 8 | 25 | 1 | 4 |
| Minfilia | 15 | 7 | 22 | 1 | 4 |
| Folka | 19 | 5 | 24 | 0 | 5 |
| Fryevia | 17 | 4 | 21 | 0 | 5 |
| Lenneth | 18 | 7 | 25 | 1 | 4 |
| Lila | 15 | 6 | 21 | 2 | 3 |
| Mystea | 15 | 5 | 20 | 0 | 5 |
| Reberta (JP) | 17 | 8 | 25 | 1 | 4 |
| Snow White | 18 | 6 | 24 | 1 | 4 |
| Aria | 20 | 5 | 25 | 0 | 5 |
| Eiko | 17 | 5 | 22 | 0 | 5 |
| Alice/Half Nightmare | 17 | 5 | 22 | 0 | 5 |
| Moogle of Narshe Mog | 16 | 6 | 22 | 1 | 4 |
| Lilith | 15 | 6 | 21 | 1 | 4 |
| Dragon Knight Freya | 18 | 10 | 28 | 1 | 4 |
| Trance Terra | 16 | 6 | 22 | 1 | 4 |
| Charming Kitty Ariana | 18 | 5 | 23 | 0 | 5 |
| Elephim | 17 | 6 | 23 | 1 | 4 |
| Jade | 18 | 7 | 25 | 1 | 4 |
| Spirited Heart Primm | 18 | 6 | 24 | 0 | 5 |
| Relm | 19 | 5 | 24 | 0 | 5 |
| Rikku (FFX-2) | 17 | 8 | 25 | 3 | 2 |
| Nalu | 18 | 7 | 25 | 1 | 4 |
| Elza | 18 | 6 | 24 | 1 | 4 |
| Lunera | 17 | 6 | 23 | 2 | 3 |

## Selected forms and kits

Awakening ranks below are numbered 1–4 for readability. MR ranks use the game’s 0–9 values. Native source names are retained for skills so their exact versions remain identifiable.

### A2 — 5

Physical combo attacker.

Sprite `310000505` (GL); base-stat budget: Squall. Growth: Cloud.

- Awakening 1: Rend [485003]; Venom Skewer [485006]; Blade Volley [485015]; Guard Mode [485045]; Charging Blade [485051]; Nullify Blind [1105]; Physical Attack +20% [1309]; HP +20% [1378].
- Awakening 2: Rough Divide [446600]; Grand Slash [485009]; Perforate [485012]; Colossal Cleave [485030]; Quad Blade [485033]; Binding Assault [485036]; Restore MP on Attack [1124].
- Awakening 3: Fated Circle [446610]; Rending Edge [485039]; Offensive Calibration [485042]; Relentless Blade [485048]; Critical Hit Rate +10% [1247].
- Awakening 4: Numbing Slash [485018]; Barrage [400300]; Stagger Power +30% [1376]; Latent Potential [1424].
- MR 1: Improvement [1421].
- MR 2: HP +30 (permanent).
- MR 3: Gut Rip [400690].
- MR 4: AP +8 (permanent).
- MR 5: Trigger [1422].
- MR 6: Agility +10 (permanent).
- MR 7: Lone Lion [1423].
- MR 8: Attack +15 (permanent).
- MR 9: Double Action [400710]; AP +8 (permanent); Spirit of A2.

Supplemental player copies (native source ID; final MP/power):

- Rend ← Rend [501510, enemy]: MP 8, power 18. Deal physical damage to an enemy.
- Venom Skewer ← Skewer [501790, enemy]: MP 12, power 18. Deal physical damage to an enemy. Inflict Poison with a 50% chance.
- Grand Slash ← Grand Slash [501310, enemy]: MP 18, power 18. Deal physical damage to all enemies.
- Perforate ← Perforate [502220, enemy]: MP 24, power 30. Deal physical damage to an enemy. Inflict Poison with a 50% chance.
- Blade Volley ← Machine Gun [500150, enemy]: MP 10, power 12. Deal physical damage to an enemy 4 times.
- Colossal Cleave ← Colossus Cleave [501720, enemy]: MP 22, power 30. Deal physical damage to an enemy.
- Quad Blade ← Barrage [503260, enemy]: MP 24, power 32. Deal physical damage to an enemy 4 times.
- Binding Assault ← Boundless Void [505950, enemy]: MP 20, power 24. Deal physical damage to an enemy 2 times. Inflict Paralysis with a 50% chance.
- Rending Edge ← Devil Claw [571330, enemy]: MP 18, power 20. Deal physical damage to an enemy. remove enemy buffs.
- Offensive Calibration ← 猛攻の血を注入した！ [501780, enemy]: MP 20, power 0. Increase own attack and magic by 50% for 3 turns.
- Guard Mode ← Assaulting Warcry [505420, enemy]: MP 12, power 0. Reduce own physical damage taken by 30% for 3 turns.
- Relentless Blade ← Unrelenting Claw [503840, enemy]: MP 28, power 36. Deal physical damage to an enemy.
- Charging Blade ← Trample [501050, enemy]: MP 10, power 18. Deal physical damage to an enemy.
- Numbing Slash ← Numbclaw [500890, enemy]: MP 10, power 12. Deal physical damage to an enemy. Inflict Paralysis.

### Christine — 6

Ice magic and stagger.

Sprite `401002606` (GL); base-stat budget: Tronn. Growth: Terra.

- Awakening 1: Blizzard [220050]; Silence [230030]; Dispel [210200]; Blizzard Beam [485109]; Frost Wave [485115]; Frozen Needle [485130]; Resist Ice [1033]; MP +10% [1380].
- Awakening 2: Blizzara [220060]; Blizzaga [220070]; Absolute Zero [485106]; Slumber Mist [485112]; Frozen Needle II [485133]; Snowstorm [485139]; Speed +10% [1277]; Victor’s Respite [1407].
- Awakening 3: Freezing Spike [485103]; Frozen Needle III [485136]; Frostspike [485142]; Deshell on Stagger [1285].
- Awakening 4: True Stagger [1406].
- MR 1: Restore MP on Stagger [1281].
- MR 2: Agility +5 (permanent).
- MR 3: Stagger Power +30% [1376].
- MR 4: AP +8 (permanent).
- MR 5: Focus Magic [400630].
- MR 6: MP +20 (permanent).
- MR 7: Fill LB on Stagger [1280].
- MR 8: Magic +15 (permanent).
- MR 9: Half MP Cost [1045]; AP +8 (permanent); Spirit of Christine.

Supplemental player copies (native source ID; final MP/power):

- Freezing Spike ← Freezing Spike [220080, native]: MP 30, power 30. Deal Ice magic damage to all enemies 3 times.
- Absolute Zero ← Absolute Zero [500230, enemy]: MP 22, power 24. Deal Ice magic damage to all enemies.
- Blizzard Beam ← Blizzard Beam [500990, enemy]: MP 10, power 18. Deal Ice magic damage to an enemy.
- Slumber Mist ← Sleep Gas [500570, enemy]: MP 20, power 0. Inflict Sleep with a 30% chance.
- Frost Wave ← Blaze [500350, enemy]: MP 12, power 12. Deal Ice magic damage to all enemies 2 times.
- Frozen Needle ← Blizzard of the Seventh Dawn [220420, native]: MP 5, power 19. Deal Ice magic damage to an enemy.
- Frozen Needle II ← Blizzard II of the Seventh Dawn [220430, native]: MP 17, power 36. Deal Ice magic damage to an enemy 2 times.
- Frozen Needle III ← Blizzard III of the Seventh Dawn [220440, native]: MP 45, power 48. Deal Ice magic damage to all enemies 3 times.
- Snowstorm ← Snowstorm [500470, enemy]: MP 20, power 18. Deal Ice magic damage to all enemies.
- Frostspike ← Frostspike [506130, enemy]: MP 32, power 30. Deal Ice magic damage to all enemies 3 times. Inflict Slow.

### Crystal Fina — Custom

Healing, cleansing and light magic.

Sprite `99887755552703` (CUSTOM); base-stat budget: Ayaka. Growth: Terra.

- Awakening 1: Cure [210010]; Banish [210250]; Purify [485236]; Protect [230040]; Raise [210140]; MP +20% [1381]; Nullify Silence [1107].
- Awakening 2: Cura [210020]; Banishra [210260]; Crystal Ray [485212]; Restore [485215]; Crystal Renewal [485218]; Protectga [230050]; Esunaga [210130]; Speed +10% [1277].
- Awakening 3: Curaga [210030]; Banishga [210270]; Arise [210150]; Crystal Renewal [485233]; Radiant Restoration [485209]; Crystal Sanctification [485230]; Alabastrine Blessing [1455].
- Awakening 4: Holy [485203]; Reraise [210160]; Divine Tidings [1456].
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

- Holy ← Holy [210190, native]: MP 63, power 80. Deal Light magic damage to an enemy.
- Reraise ← Reraise [210240, native]: MP 60, power 0. Grant Reraise to an ally.
- Radiant Restoration ← Curaga [215020, native]: MP 65, power 1500. Restore all allies’ HP.
- Crystal Ray ← Array: Brilliance [503630, enemy]: MP 24, power 32. Deal Light magic damage to an enemy.
- Restore ← Restore [501930, enemy]: MP 18, power 20. Restore 20% of an ally’s max HP.
- Crystal Sanctification ← Holy [240190, enemy]: MP 45, power 40. Deal Light magic damage to all enemies.
- Crystal Renewal ← Repair [503210, enemy]: MP 35, power 10. Restore 10% of all allies’ max HP.
- Purify ← Regurgitate [570690, enemy]: MP 15, power 50. Remove an ally’s ailments.
- Crystal Renewal ← Curaga [506110, enemy]: MP 50, power 400. Restore all allies’ HP.

### Barusa — 6

Earth physical bruiser and protection.

Sprite `401003006` (GL); base-stat budget: Wilhelm. Growth: Cloud.

- Awakening 1: Stone Surge [421400]; Stone Slam [421340]; Quicksand [485309]; Granite Claw [485312]; Granite Slam [485333]; Stone Horn [485336]; Physical Defense +20% [1313]; General’s Pride [1452].
- Awakening 2: Stonera Surge [421410]; Stonera Slam [421350]; D Sword Breaker [414700]; Crust Driver [485303]; Granite Shell Strike [485330]; Nullify Sleep [1106]; Protect Opener [1290]; Strategic Acumen [1336].
- Awakening 3: Stonega Surge [421420]; Stonega Slam [421360]; Supreme Defense [414710]; Mantle Driver [485306]; Fill LB when Taking Damage [1331]; HP +30% [1379].
- Awakening 4: Bastion [1454].
- MR 1: Imbue Earth [1526].
- MR 2: HP +30 (permanent).
- MR 3: Chakra [400440].
- MR 4: AP +8 (permanent).
- MR 5: Guard [400640].
- MR 6: Defence +10 (permanent).
- MR 7: Unmoving Bulwark [1453].
- MR 8: Attack +15 (permanent).
- MR 9: Critical Counter [1333]; AP +8 (permanent); Spirit of Barusa.

Supplemental player copies (native source ID; final MP/power):

- Crust Driver ← Crust Driver [414800, native]: MP 20, power 23. Deal Earth physical damage to an enemy.
- Mantle Driver ← Mantle Driver [414810, native]: MP 37, power 49. Deal Earth physical damage to an enemy 3 times.
- Quicksand ← Quicksand [500330, enemy]: MP 12, power 12. Deal Earth physical damage to an enemy. Inflict Slow.
- Granite Claw ← Pincer [500540, enemy]: MP 8, power 18. Deal physical damage to an enemy.
- Granite Shell Strike ← Turtle Shell [501340, enemy]: MP 18, power 24. Deal Earth physical damage to an enemy. reduce own physical damage taken by 30% for 3 turns.
- Granite Slam ← Slam [500030, enemy]: MP 6, power 12. Deal Earth physical damage to an enemy.
- Stone Horn ← Horn [500550, enemy]: MP 10, power 18. Deal Earth physical damage to an enemy.

### Blue Sky Belle Fran — 6

Ranged physical and disabling arrows.

Sprite `212001706` (GL); base-stat budget: Firion. Growth: Cloud.

- Awakening 1: Aero Knife [421250]; Thunder Knife [421100]; Sleep Knife [422010]; Poison Arrow [485403]; Binding Arrow [485406]; Triple Arrow [485430]; Snipe [485439]; Focused Arrow [485412].
- Awakening 2: Aerora Knife [421260]; Thundara Knife [421110]; Blind Knife [422030]; Windfeather Volley [485436]; Flurry Arrow [485442]; Physical Attack +20% [1309]; Speed +10% [1277].
- Awakening 3: Aeroga Knife [421270]; Thundaga Knife [421120]; Arrow Tempest [485409]; Roving Volley [485433]; Recuperate LB [1338].
- Awakening 4: Stagger Power +30% [1376].
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

- Poison Arrow ← Poison Slash [500210, enemy]: MP 8, power 12. Deal physical damage to an enemy. Inflict Poison.
- Binding Arrow ← Stun Slash [501170, enemy]: MP 10, power 12. Deal physical damage to an enemy. Inflict Paralysis.
- Arrow Tempest ← Frenzied Bombardment [503250, enemy]: MP 32, power 32. Deal physical damage to all enemies 4 times.
- Triple Arrow ← Beak [500480, enemy]: MP 10, power 12. Deal physical damage to an enemy 3 times.
- Roving Volley ← Strikes of the Duty Bound [503820, enemy]: MP 28, power 32. Deal physical damage to random enemies 4 times.
- Windfeather Volley ← 羽ばたき_物理 [503880, enemy]: MP 20, power 20. Deal Wind physical damage to all enemies 3 times.
- Snipe ← Snipe [500110, enemy]: MP 6, power 12. Deal physical damage to an enemy.
- Flurry Arrow ← Flatten [500190, enemy]: MP 10, power 18. Deal physical damage to an enemy 2 times.
- Focused Arrow ← Hack [500050, enemy]: MP 8, power 18. Deal physical damage to an enemy.

### Oracle Maiden Lunafreya — NV Brave Shift

Debuff specialist with water/wind magic.

Sprite `215002417` (GL); base-stat budget: Zidane. Growth: Terra.

- Awakening 1: Free Energy [446800]; Deprotect [230080]; Slowing Tide [485509]; Nullify Silence [1107]; Magic Attack +30% [1275]; MP +10% [1380].
- Awakening 2: Meo Twister [446820]; Steal Vitality [446860]; Deshell [230090]; Confusega [485512]; Maelstrom [485515]; Blinding Light [485518]; Weakening Tide [485533]; Fading Tide [485536].
- Awakening 3: Free Energy+ [446810]; Steal Magic [446870]; Sundering Wind [485503]; Graceful Deluge [485506]; Resist Water [1251]; Restore MP on Stagger [1281]; Magic Defense +20% [1315]; Strategic Acumen [1336].
- Awakening 4: Meo Twister+ [446830]; Oracle’s Censure [485530]; Speed +10% [1277].
- MR 1: Add Deprotect [1131].
- MR 2: Agility +5 (permanent).
- MR 3: Regen on Stagger [1286].
- MR 4: AP +8 (permanent).
- MR 5: Gil Toss [400250].
- MR 6: MP +20 (permanent).
- MR 7: Insult to Injury [1425].
- MR 8: Magic +15 (permanent).
- MR 9: Aggravation [1468]; AP +8 (permanent); Spirit of Oracle Maiden Lunafreya.

Supplemental player copies (native source ID; final MP/power):

- Sundering Wind ← Sundering Wind [502470, enemy]: MP 28, power 0. Reduce enemy physical and magic defense by 30% for 3 turns.
- Graceful Deluge ← Graceful Deluge [501420, enemy]: MP 40, power 30. Deal Water magic damage to all enemies 3 times. reduce enemy physical and magic defense.
- Slowing Tide ← Mucus [500500, enemy]: MP 8, power 0. Inflict Slow.
- Confusega ← Confusega [235070, native]: MP 24, power 0. Inflict Confusion with a 50% chance.
- Maelstrom ← Maelstrom [500760, enemy]: MP 22, power 24. Deal Water magic damage to all enemies.
- Blinding Light ← Flash [500820, enemy]: MP 18, power 0. Inflict Blind.
- Oracle’s Censure ← Biased Examination [503170, enemy]: MP 50, power 0. Attempt to lower enemy attack, magic, defenses and speed.
- Weakening Tide ← Splattering Flesh [503670, enemy]: MP 24, power 10. Deal Water magic damage to all enemies. lower enemy physical attack and defense.
- Fading Tide ← Splattering Fluid [503680, enemy]: MP 24, power 10. Deal Water magic damage to all enemies. lower enemy magic and magic defense.

### Minfilia — 4

Mixed earth/wind offense and party protection.

Sprite `214000304` (GL); base-stat budget: Onion Knight. Growth: Lightning.

- Awakening 1: Stone [220210]; Protect [230040]; Gale [485606]; Sandstorm [485609]; Quiet Recovery [485615]; Earthward [485630]; Magic Attack +20% [1311]; Physical Defense +20% [1313].
- Awakening 2: Stonera [220220]; Protectga [230050]; Petrifying Gaze [485612]; Warrior’s Blessing [485636]; Nullify Slow [1116]; MP +20% [1381].
- Awakening 3: Stonega [220230]; Blade Torrent [445200]; Calamity [485603]; Stonefall [485633]; Speed +10% [1277]; Job Change [1410].
- Awakening 4: Dual Jobs [485690]; Late Bloomer [1411].
- MR 1: Throw [400240].
- MR 2: Attack +5 (permanent).
- MR 3: Observe and Attack [1343].
- MR 4: AP +8 (permanent).
- MR 5: Observe and Recover HP [1465].
- MR 6: MP +20 (permanent).
- MR 7: Strategic Acumen [1336].
- MR 8: Magic +15 (permanent).
- MR 9: Chuck [1412]; AP +8 (permanent); Spirit of Minfilia.

Supplemental player copies (native source ID; final MP/power):

- Calamity ← Calamity [220240, native]: MP 35, power 30. Deal Earth magic damage to all enemies 3 times.
- Gale ← Aero [225120, native]: MP 12, power 17. Deal Wind magic damage to all enemies.
- Sandstorm ← Sandstorm [500320, enemy]: MP 12, power 12. Deal Earth physical damage to all enemies 2 times. Inflict Blind with a 30% chance.
- Petrifying Gaze ← Petrifying Gaze [500600, enemy]: MP 18, power 0. Inflict Stoned with a 30% chance.
- Quiet Recovery ← Groom [502610, enemy]: MP 5, power 100. Restore own HP.
- Earthward ← Stone [225150, native]: MP 12, power 17. Deal Earth magic damage to all enemies.
- Stonefall ← Stonega [255170, enemy]: MP 28, power 24. Deal Earth magic damage to all enemies 3 times.
- Warrior’s Blessing ← Red Wing Legacy [502730, enemy]: MP 14, power 0. Increase an ally’s attack by 50% for 3 turns.

### Folka — 6

Water magic with restorative utility.

Sprite `100018306` (GL); base-stat budget: Tronn. Growth: Terra.

- Awakening 1: Water [220130]; Syphon [220310]; Bio [485712]; Tidal Invocation [485718]; Magic Attack +30% [1275]; Nullify Silence [1107].
- Awakening 2: Watera [220140]; Aqua Breath [485703]; Poisonga [485715]; Rushing Tide [485739]; Oracle’s Blessing [485745]; Restore MP on Stagger [1281].
- Awakening 3: Waterga [220150]; Regen [210050]; Hi Regen [414510]; Tidal Wave [485706]; Watera Tide [485709]; Sundering Deluge [485733]; Piercing Current [485736]; Regen Opener [1293].
- Awakening 4: Waterga Tide [485730]; Restoring Mist [485742]; Waterga Surge [485721]; Magic Defense +20% [1315].
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

- Aqua Breath ← Aqua Breath [500800, enemy]: MP 20, power 18. Deal Water magic damage to all enemies 3 times.
- Tidal Wave ← Tidal Wave [505130, enemy]: MP 32, power 36. Deal Water magic damage to all enemies 2 times.
- Watera Tide ← Watera [225100, native]: MP 30, power 33. Deal Water magic damage to all enemies 2 times.
- Bio ← Bio [250260, enemy]: MP 10, power 12. Deal magic damage to an enemy. Inflict Poison.
- Poisonga ← Poisonga [225180, native]: MP 20, power 0. Inflict Poison.
- Waterga Tide ← Waterga [225110, native]: MP 60, power 55. Deal Water magic damage to all enemies 3 times.
- Sundering Deluge ← Graceful Deluge [501410, enemy]: MP 28, power 26. Deal Water magic damage to all enemies 3 times. Lower defense and spirit.
- Piercing Current ← Psycho Skewer [505320, enemy]: MP 36, power 40. Deal Water magic damage to an enemy.
- Rushing Tide ← Watera [250140, enemy]: MP 22, power 22. Deal Water magic damage to random enemies 3 times.
- Restoring Mist ← White Wind [500810, enemy]: MP 45, power 500. Restore all allies’ HP.
- Oracle’s Blessing ← Blue Wing Legacy [502710, enemy]: MP 14, power 0. Increase an ally’s magic by 50% for 3 turns.
- Tidal Invocation ← タイダルウェイブ(コロシアム) [571450, enemy]: MP 36, power 30. Deal Water magic damage to all enemies 4 times.
- Waterga Surge ← Waterga [250150, enemy]: MP 30, power 30. Deal Water magic damage to all enemies 3 times.

### Fryevia — 5

Ice spellblade and precision physical.

Sprite `302001405` (GL); base-stat budget: Bartz. Growth: Cloud.

- Awakening 1: Froststrike [421070]; Frozen Slumber Cut [485809]; Frostbind Cut [485812]; True Strike [485815]; Frozen Slash [485842]; Physical Attack +20% [1309].
- Awakening 2: Froststrike II [421080]; Golden Thrust [485818]; Dark Edge [485821]; Diamond Bind [485830]; Frozen Fang [485833]; Frost Pierce [485836]; Frost Sweep [485839]; Frost Dance [485824].
- Awakening 3: Froststrike III [421090]; Glint of Verglas [485803]; Stormbound Smite [485806]; Resist Ice [1033]; Speed +10% [1277].
- Awakening 4: Flare Blade [420270]; HP +20% [1378].
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

- Glint of Verglas ← Glint of Verglas [505380, enemy]: MP 35, power 40. Deal Ice physical damage to an enemy 2 times.
- Stormbound Smite ← Stormbound Smite [505390, enemy]: MP 32, power 30. Deal Ice physical damage to all enemies 3 times.
- Frozen Slumber Cut ← Sleep Slash [500630, enemy]: MP 10, power 18. Deal Ice physical damage to an enemy. Inflict Sleep with a 50% chance.
- Frostbind Cut ← Paralysis Slash [500640, enemy]: MP 12, power 18. Deal Ice physical damage to an enemy. Inflict Paralysis with a 50% chance.
- True Strike ← True Strike [500920, enemy]: MP 6, power 18. Deal physical damage to an enemy.
- Golden Thrust ← Golden Lance [501600, enemy]: MP 14, power 24. Deal physical damage to an enemy.
- Dark Edge ← Dark Edge [505260, enemy]: MP 20, power 24. Deal Dark physical damage to an enemy.
- Diamond Bind ← Petrifying Bite [502270, enemy]: MP 18, power 18. Deal Ice physical damage to an enemy. Inflict Stoned with a 50% chance.
- Frozen Fang ← Paralysis Fang [501670, enemy]: MP 20, power 24. Deal Ice physical damage to an enemy. Inflict Paralysis.
- Frost Pierce ← Blizzara [250060, enemy]: MP 15, power 22. Deal Ice physical damage to an enemy 2 times.
- Frost Sweep ← Blizzara [255040, enemy]: MP 20, power 18. Deal Ice physical damage to all enemies 2 times.
- Frozen Slash ← Slash [500040, enemy]: MP 6, power 12. Deal Ice physical damage to an enemy.
- Frost Dance ← Slash [501300, enemy]: MP 24, power 28. Deal Ice physical damage to an enemy 4 times.

### Lenneth — 6

Physical cover tank with light attacks.

Sprite `330000106` (GL); base-stat budget: Warrior of Light. Growth: Cloud.

- Awakening 1: Vanguard Glaive [445010]; Banish Blade [420330]; Shield Crush [485903]; Repose [485915]; Guarding Bash [485936]; Shield Thrust [485939]; Physical Defense +20% [1313].
- Awakening 2: Banishra Blade [420340]; Guarding Smite [485906]; Lance Breaker [485912]; Valkyrie Ward [485948]; Protect Opener [1290]; Shell at Half HP [1299]; HP +20% [1378].
- Awakening 3: Sacred Wave [445020]; Banishga Blade [420350]; Sword Strike [485909]; Dawn Judgment [485930]; Luminant Purifier [485933]; Valkyrie Cleansing [485942]; Brave Lance [485945]; Deprotect on Stagger [1235].
- Awakening 4: Vanguard Glaive+ [445030]; Grit [1042]; Resist Dark [1253].
- MR 1: Restore HP on Stagger [1284].
- MR 2: Mind +5 (permanent).
- MR 3: Multi-Cover [400390].
- MR 4: AP +8 (permanent).
- MR 5: Physical Counter [1029].
- MR 6: HP +60 (permanent).
- MR 7: Lustrous Shield [1408].
- MR 8: Defence +15 (permanent).
- MR 9: Heroic Nature [1409]; AP +8 (permanent); Spirit of Lenneth.

Supplemental player copies (native source ID; final MP/power):

- Shield Crush ← Crush [500020, enemy]: MP 10, power 18. Deal physical damage to an enemy.
- Guarding Smite ← Guarding Smite [505410, enemy]: MP 20, power 24. Deal physical damage to an enemy. defend after attacking.
- Sword Strike ← Sword Strike [503640, enemy]: MP 25, power 30. Deal physical damage to all enemies.
- Lance Breaker ← Rib [500170, enemy]: MP 18, power 24. Deal physical damage to an enemy.
- Repose ← Repose [502080, enemy]: MP 8, power 0. Increase own defenses while lowering attack and magic.
- Dawn Judgment ← Dawn of Judgment [505350, enemy]: MP 38, power 40. Deal Light physical damage to an enemy.
- Luminant Purifier ← Luminant Purifier [505370, enemy]: MP 36, power 36. Deal Light physical damage to all enemies.
- Guarding Bash ← Carapace [500930, enemy]: MP 12, power 18. Deal physical damage to an enemy. reduce own physical damage taken by 30% for 3 turns.
- Shield Thrust ← Counter Horn [505100, enemy]: MP 10, power 18. Deal physical damage to an enemy.
- Valkyrie Cleansing ← Negation [505360, enemy]: MP 35, power 0. Remove party ailments and stat debuffs.
- Brave Lance ← Chomp [503810, enemy]: MP 32, power 40. Deal physical damage to an enemy.
- Valkyrie Ward ← Show me majestic magic! [505530, enemy]: MP 20, power 0. Reduce own physical and magic damage taken by 30% for 3 turns.

### Lila — 6

Martial physical damage and self recovery.

Sprite `100013806` (GL); base-stat budget: Firion. Growth: Cloud.

- Awakening 1: Fire Slam [421010]; Fulminating Strike [445100]; Fist of Vigor [486003]; Heavy Palm [486033]; Physical Attack +20% [1309]; Light of Rebellion [1353].
- Awakening 2: Fira Slam [421020]; Fist of Fortification [486006]; Fist of Fury [486009]; Crushing Grasp [486012]; Martial Reprisal [486030]; Sweeping Fists [486036]; Chakra [400440]; Critical Hit Rate +10% [1247].
- Awakening 3: Firaga Slam [421030]; Saber of Adversity [445110]; Binding Grapple [486039]; Speed +10% [1277]; Restore HP on Stagger [1284]; HP +30% [1379].
- Awakening 4: Fulminating Strike+ [445120].
- MR 1: Fill LB when Taking Damage [1331].
- MR 2: HP +30 (permanent).
- MR 3: Bladeblitz [400310].
- MR 4: AP +8 (permanent).
- MR 5: Bravery on Stagger [1288].
- MR 6: Agility +10 (permanent).
- MR 7: Nullify Instant Death [1325].
- MR 8: Attack +15 (permanent).
- MR 9: Arms Akimbo [400650]; AP +8 (permanent); Spirit of Lila.

Supplemental player copies (native source ID; final MP/power):

- Fist of Vigor ← Fist of Vigor [502230, enemy]: MP 12, power 14. Deal physical damage to an enemy. raise own attack by 50%.
- Fist of Fortification ← Fist of Fortification [502370, enemy]: MP 20, power 18. Deal physical damage to an enemy. reduce own physical/magic damage taken by 30%.
- Fist of Fury ← Fist of Fury [505060, enemy]: MP 14, power 24. Deal physical damage to an enemy.
- Crushing Grasp ← Crushing Grasp [502240, enemy]: MP 22, power 28. Deal physical damage to an enemy. Inflict Paralysis with a 50% chance.
- Martial Reprisal ← That is no martial skill! [505600, enemy]: MP 22, power 30. Deal physical damage to an enemy.
- Heavy Palm ← Clobber [501850, enemy]: MP 10, power 18. Deal physical damage to an enemy.
- Sweeping Fists ← Wild Rage [505030, enemy]: MP 16, power 12. Deal physical damage to all enemies 4 times.
- Binding Grapple ← Stranglehold [501030, enemy]: MP 22, power 24. Deal physical damage to an enemy. Inflict Paralysis with a 20% chance.

### Mystea — 5

Magic tank, barriers and counter magic.

Sprite `100011005` (GL); base-stat budget: Cecil. Growth: Terra.

- Awakening 1: Shell [230060]; Light Ray [486112]; Dazing Mist [486118]; Magic Ward [486130]; Dark Pulse [486136]; HP +30% [1379]; Resist Dark [1253].
- Awakening 2: Shellga [230070]; Manaward [220410]; Evasion Ward [486109]; Banishra Ray [486121]; Focused Dark Pulse [486139]; Grit [1042].
- Awakening 3: Reflect [230120]; Mighty Guard [486103]; Dystopia [486115]; Barrier Burst [486133]; Recuperate LB [1338].
- Awakening 4: Foul of the Seventh Dawn [220510]; Strategic Acumen [1336].
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

- Mighty Guard ← Mighty Guard [500860, enemy]: MP 40, power 0. Reduce party physical and magic damage taken by 30%.
- Evasion Ward ← Scatter Feathers [500700, enemy]: MP 20, power 0. Increase own physical evasion by 50%.
- Light Ray ← Laser [500310, enemy]: MP 10, power 18. Deal Light magic damage to an enemy.
- Dystopia ← Dystopia [505860, enemy]: MP 26, power 26. Deal Dark magic damage to all enemies.
- Dazing Mist ← Pollen [500690, enemy]: MP 12, power 0. Inflict Confusion.
- Banishra Ray ← Banishra [240240, enemy]: MP 15, power 22. Deal Light magic damage to an enemy 2 times.
- Magic Ward ← Magic Warcry [505430, enemy]: MP 12, power 0. Reduce own magic damage taken by 30% for 3 turns.
- Barrier Burst ← Heavy Countermeasure [503980, enemy]: MP 35, power 36. Deal magic damage to all enemies.
- Dark Pulse ← Dark [255260, enemy]: MP 12, power 12. Deal Dark magic damage to all enemies.
- Focused Dark Pulse ← Darkra [250520, enemy]: MP 18, power 22. Deal Dark magic damage to an enemy 2 times.

### Reberta (JP) — 5

Dragoon with fire/wind spear attacks.

Sprite `100014405` (GL); base-stat budget: Clive. Growth: Cloud.

- Awakening 1: Fire Surge [421040]; Aero Surge [421310]; Breath Wing [486203]; Dragoon Cleave [486215]; Resist Fire [1011]; Physical Attack +20% [1309].
- Awakening 2: Fira Surge [421050]; Aerora Surge [421320]; Rising Flames [448000]; Flame Lance [486212]; Flame Lance Volley [486230]; Carmine Lance [486236]; Regen on Stagger [1286]; HP +20% [1378].
- Awakening 3: Firaga Surge [421060]; Aeroga Surge [421330]; Heatwave [448010]; Silver Lance [486206]; Branch Spear [486209]; Blistering Hellfire [486233]; Dragonfire Breath [486239]; Regen Opener [1293].
- Awakening 4: Critical Hit Rate +10% [1247]; Bonus Damage [1335]; Stagger Power +30% [1376].
- MR 1: Opening Honed Senses [1507].
- MR 2: HP +30 (permanent).
- MR 3: Restore HP on Defeating Foes [1318].
- MR 4: AP +8 (permanent).
- MR 5: Power Stagger [1385].
- MR 6: Agility +10 (permanent).
- MR 7: Mirage [400670].
- MR 8: Attack +15 (permanent).
- MR 9: Clive’s Limit Break [1442]; AP +8 (permanent); Spirit of Reberta (JP).

Supplemental player copies (native source ID; final MP/power):

- Breath Wing ← Breath Wing [500460, enemy]: MP 12, power 12. Deal Wind physical damage to all enemies 3 times.
- Silver Lance ← Silver Lance [501260, enemy]: MP 25, power 36. Deal physical damage to an enemy.
- Branch Spear ← Branch Spear [503780, enemy]: MP 25, power 36. Deal Earth physical damage to an enemy.
- Flame Lance ← Spew Flames [502010, enemy]: MP 20, power 24. Deal Fire physical damage to an enemy 3 times.
- Flame Lance Volley ← Flame Thrower [500370, enemy]: MP 16, power 18. Deal Fire physical damage to an enemy 3 times.
- Blistering Hellfire ← Blistering Hellfire [505330, enemy]: MP 32, power 30. Deal Fire physical damage to all enemies.
- Carmine Lance ← Carmine Inferno [505340, enemy]: MP 20, power 24. Deal Fire physical damage to an enemy.
- Dragonfire Breath ← Flame Breath [501880, enemy]: MP 40, power 40. Deal Fire magic damage to all enemies.
- Dragoon Cleave ← Rake [500130, enemy]: MP 16, power 22. Deal physical damage to an enemy.

### Snow White — 7

Dark physical drain and risk/reward.

Sprite `336000207` (GL); base-stat budget: Cecil. Growth: Cloud.

- Awakening 1: Dark Blade [420300]; Leech [486303]; Crimson Bite [486330]; Venom Gash [486333]; Nightcut [486336]; Slumber Gash [486339]; Physical Attack +20% [1309]; Restore HP on Defeating Foes [1318].
- Awakening 2: Darkra Blade [420310]; Sleep Slam [422020]; Drain [220300]; Predation [486306]; Revenge Strike [486312]; Binding Sweep [486315]; Crimson Sweep [486345]; Blood Recovery [486348].
- Awakening 3: Drain Knife [422040]; Darkga Blade [420320]; Purging Blade [486309]; Hell Gate [486342]; Resist Dark [1253]; Physical Defense +20% [1313]; HP +20% [1378].
- Awakening 4: Auto-Regen [1077].
- MR 1: Darkness [400490].
- MR 2: HP +30 (permanent).
- MR 3: Vigorous Attacks [1358].
- MR 4: AP +8 (permanent).
- MR 5: Staggeringly Risky [1405].
- MR 6: Defence +10 (permanent).
- MR 7: Dark Rite [1431].
- MR 8: Attack +15 (permanent).
- MR 9: Dark Sword [1457]; AP +8 (permanent); Spirit of Snow White.

Supplemental player copies (native source ID; final MP/power):

- Leech ← Leech [500520, enemy]: MP 12, power 12. Deal physical damage to an enemy. Absorb damage dealt as HP.
- Predation ← Predation [570710, enemy]: MP 16, power 18. Deal physical damage to an enemy. Absorb damage dealt as HP.
- Purging Blade ← Purging Blade [505960, enemy]: MP 32, power 36. Deal Dark physical damage to an enemy. reduce enemy physical and magic defense.
- Revenge Strike ← Revenge Blast [501630, enemy]: MP 16, power 24. Deal physical damage to an enemy.
- Binding Sweep ← Cling [500910, enemy]: MP 14, power 12. Deal physical damage to all enemies. Inflict Slow with a 30% chance.
- Crimson Bite ← Incisors [500510, enemy]: MP 10, power 18. Deal Dark physical damage to an enemy.
- Venom Gash ← Regurgitate [570640, enemy]: MP 12, power 15. Deal Dark physical damage to an enemy. Inflict Poison.
- Nightcut ← Regurgitate [570660, enemy]: MP 12, power 15. Deal Dark physical damage to an enemy. Inflict Blind.
- Slumber Gash ← Regurgitate [570670, enemy]: MP 12, power 15. Deal Dark physical damage to an enemy. Inflict Sleep.
- Hell Gate ← Hell’s Gate [505970, enemy]: MP 30, power 30. Deal Dark physical damage to all enemies.
- Crimson Sweep ← Darkra [255280, enemy]: MP 20, power 18. Deal Dark physical damage to all enemies 2 times.
- Blood Recovery ← 捕食(1000回復) [501530, enemy]: MP 18, power 400. Restore 400 HP to self.

### Aria — 5

Water magic, water blades and healing.

Sprite `203000905` (GL); base-stat budget: Leah. Growth: Terra.

- Awakening 1: Water Blade [420100]; Cure of the Seventh Dawn [220480]; Healing Rain [486403]; Rejuvenate [486409]; Water Chorus [486430]; Aether Current [486421]; Esuna [210120]; Healing Magic +30% [1375].
- Awakening 2: Watera Blade [420110]; Cure II of the Seventh Dawn [220490]; Purify [414500]; Soothing Rain [486406]; Undertow [486412]; Bubble Breath [486415]; Raise [210140]; Nullify Charm [1111].
- Awakening 3: Waterga Blade [420120]; Cure III of the Seventh Dawn [220500]; Ocean Requiem [486433]; Waterdrop [486424]; Esunaga [210130]; Protect at Half HP [1300]; Haste at Half HP [1301].
- Awakening 4: Reraise [210160]; Preventive Care [1352].
- MR 1: Nullify Poison [1104].
- MR 2: MP +10 (permanent).
- MR 3: Resist Water [1251].
- MR 4: AP +8 (permanent).
- MR 5: MP +20% [1381].
- MR 6: Magic +10 (permanent).
- MR 7: Magic Attack +20% [1311].
- MR 8: Mind +15 (permanent).
- MR 9: Imbue Water [1524]; AP +8 (permanent); Spirit of Aria.

Supplemental player copies (native source ID; final MP/power):

- Healing Rain ← Cure [245000, enemy]: MP 10, power 80. Restore all allies’ HP.
- Soothing Rain ← Cura [245010, enemy]: MP 18, power 200. Restore all allies’ HP.
- Rejuvenate ← Rejuvenate [502020, enemy]: MP 12, power 20. Restore 20% of own max HP.
- Undertow ← Graceful Deluge [501400, enemy]: MP 20, power 12. Deal Water magic damage to all enemies 3 times. reduce enemy physical and magic defense.
- Bubble Breath ← Bubble Breath [501680, enemy]: MP 24, power 24. Deal Water magic damage to all enemies 3 times.
- Banish Ray ← Banish [240230, enemy]: MP 5, power 14. Deal Light magic damage to an enemy.
- Water Chorus ← Water [225090, native]: MP 12, power 17. Deal Water magic damage to all enemies.
- Ocean Requiem ← Graceful Deluge [501440, enemy]: MP 40, power 40. Deal Water magic damage to all enemies 3 times. Lower defense and spirit.
- Cleansing Miasma ← Bio [255190, enemy]: MP 20, power 12. Deal magic damage to all enemies. Inflict Poison.
- Radiant Pulse ← 連続ホーリー [503870, enemy]: MP 36, power 40. Deal Light magic damage to an enemy.
- Mist Veil ← Darkness Powder [570820, enemy]: MP 20, power 0. Inflict Blind.
- Aether Current ← (ボスカウンター用)アスピル [503970, enemy]: MP 8, power 6. Drain MP from an enemy.
- Waterdrop ← Water [250130, enemy]: MP 6, power 14. Deal Water magic damage to an enemy.
- Soothing Current ← Regurgitate [570620, enemy]: MP 14, power 200. Restore 200 HP to an ally.

### Eiko — 7

Summoner with wind magic and revival.

Sprite `209000707` (GL); base-stat budget: Ayaka. Growth: Terra.

- Awakening 1: Aero of the Seventh Dawn [220450]; Light of the Eidolons [486530]; Healing Magic +30% [1375]; Nullify Sleep [1106].
- Awakening 2: Aero II of the Seventh Dawn [220460]; Raise [210140]; MP +20% [1381].
- Awakening 3: Ifrit [430990]; Shiva [431000]; Aero III of the Seventh Dawn [220470]; Banishga Ray [486509]; Aerora Gust [486512]; Healing Breeze [486515]; Focused Gale [486539]; Speed +10% [1277].
- Awakening 4: Reraise [210160]; Firaga Burst [486503]; Blizzaga Burst [486506]; Eidolon Radiance [486533]; Guardian’s Earth [486536]; Guardian’s Lightning [486542]; Alabastrine Blessing [1455].
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

- Firaga Burst ← Firaga [225020, native]: MP 60, power 55. Deal Fire magic damage to all enemies 3 times.
- Blizzaga Burst ← Blizzaga [225050, native]: MP 60, power 55. Deal Ice magic damage to all enemies 3 times.
- Banishga Ray ← Banishga [240250, enemy]: MP 25, power 30. Deal Light magic damage to an enemy 3 times.
- Aerora Gust ← Aerora [225130, native]: MP 30, power 33. Deal Wind magic damage to all enemies 2 times.
- Healing Breeze ← Curaga [245020, enemy]: MP 35, power 600. Restore all allies’ HP.
- Light of the Eidolons ← Banish [225290, native]: MP 12, power 17. Deal Light magic damage to all enemies.
- Eidolon Radiance ← Banishga [225310, native]: MP 60, power 55. Deal Light magic damage to all enemies 3 times.
- Guardian’s Earth ← Stonega [225170, native]: MP 60, power 55. Deal Earth magic damage to all enemies 3 times.
- Focused Gale ← Aeroga [250190, enemy]: MP 25, power 30. Deal Wind magic damage to an enemy 3 times.
- Guardian’s Lightning ← Thundaga [225080, native]: MP 60, power 55. Deal Lightning magic damage to all enemies 3 times.

### Alice/Half Nightmare — NV Brave Shift

Ice physical with burst and HP tradeoffs.

Sprite `336000127` (JP); base-stat budget: Squall. Growth: Cloud.

- Awakening 1: Ice Slam [486660]; Boundless Void [446300]; Rage [486606]; Throat Strike [486609]; Binding Cut [486618]; Hail Cut [486639]; Twin Frost Blades [486642]; Deathblow [400530].
- Awakening 2: Icera Slam [486663]; Disorienting Cut [486615]; Frost Reprisal [486633]; Physical Attack +20% [1309]; Nullify Blind [1105]; HP +20% [1378].
- Awakening 3: Icega Slam [486666]; Purging Blade [446310]; Absolving Hail [486603]; Ruthless Rampage [486612]; Nightmare Flurry [486630]; Frozen Finale [486636]; Restore MP on Attack [1124].
- Awakening 4: Stagger Power +30% [1376].
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

- Absolving Hail ← Absolving Hailstorm [505840, enemy]: MP 32, power 30. Deal Ice physical damage to all enemies 3 times.
- Rage ← Rage [501700, enemy]: MP 10, power 0. Increase own attack and magic by 50%, lowering both defenses.
- Throat Strike ← Throat Strike [500250, enemy]: MP 10, power 18. Deal physical damage to an enemy. Inflict Silence with a 50% chance.
- Ruthless Rampage ← Ruthless Rampage [502030, enemy]: MP 30, power 18. Deal physical damage to all enemies 4 times. May inflict Paralysis, Blind and Silence.
- Disorienting Cut ← Slap [500620, enemy]: MP 18, power 24. Deal Ice physical damage to an enemy 2 times. Inflict Charm.
- Binding Cut ← Paralysis Needle [500290, enemy]: MP 8, power 12. Deal physical damage to an enemy. Inflict Paralysis.
- Ice Slam ← Blizzard Surge [421370, native]: MP 5, power 12. Deal Ice physical damage to an enemy.
- Icera Slam ← Blizzara Surge [421380, native]: MP 15, power 24. Deal Ice physical damage to an enemy.
- Icega Slam ← Blizzaga Surge [421390, native]: MP 44, power 39. Deal Ice physical damage to an enemy.
- Nightmare Flurry ← Whack and Smack [502200, enemy]: MP 36, power 28. Deal Ice physical damage to random enemies 4 times. May inflict Poison, Blind and Silence.
- Frost Reprisal ← That is no magic! [505610, enemy]: MP 22, power 30. Deal Ice physical damage to an enemy.
- Frozen Finale ← Regurgitate [570680, enemy]: MP 38, power 40. Deal Ice physical damage to an enemy.
- Hail Cut ← Blizzard [255030, enemy]: MP 12, power 12. Deal Ice physical damage to all enemies.
- Twin Frost Blades ← Tentacle [500580, enemy]: MP 12, power 18. Deal Ice physical damage to an enemy 2 times. Inflict Slow with a 50% chance.

### Moogle of Narshe Mog — 5

Wind magic, dance and speed support.

Sprite `206003005` (GL); base-stat budget: Tidus. Growth: Terra.

- Awakening 1: Aero [220170]; Haste [230130]; Gust Dance [486703]; Mystery Waltz [486709]; Berserker Step [486733]; Wait [400760]; Resist Water [1251]; Magic Attack +20% [1311].
- Awakening 2: Aerora [220180]; Cyclone [486706]; Mega Berserk [486715]; Gale Dance [486736]; HP +20% [1378].
- Awakening 3: Aeroga [220190]; Slow [230150]; Alluring Dance [486712]; Heavenly Wind [486730]; Regen on Stagger [1286]; Haste Opener [1292].
- Awakening 4: Slowga [230160]; Hastega [230140]; Fill LB on Defeating Foes [1320].
- MR 1: Focus [400460].
- MR 2: Magic +5 (permanent).
- MR 3: Haste on Stagger [1287].
- MR 4: AP +8 (permanent).
- MR 5: Speed +10% [1277].
- MR 6: MP +20 (permanent).
- MR 7: Opening Good Luck [1511].
- MR 8: Agility +15 (permanent).
- MR 9: First Strike [1049]; AP +8 (permanent); Spirit of Moogle of Narshe Mog.

Supplemental player copies (native source ID; final MP/power):

- Gust Dance ← Wind Slash [500430, enemy]: MP 12, power 12. Deal Wind magic damage to all enemies.
- Cyclone ← Cyclone [500410, enemy]: MP 22, power 24. Deal Wind magic damage to all enemies.
- Mystery Waltz ← Mystery Waltz [570450, enemy]: MP 12, power 10. Drain MP from an enemy.
- Alluring Dance ← Alluring Dance [570430, enemy]: MP 32, power 0. Inflict Charm.
- Mega Berserk ← Mega Berserk [235080, native]: MP 22, power 0. Inflict Berserk.
- Heavenly Wind ← Heavenly Wind [505280, enemy]: MP 40, power 40. Deal Wind magic damage to all enemies.
- Berserker Step ← Berserk [570410, enemy]: MP 6, power 0. Inflict Berserk.
- Gale Dance ← 大魔法マグヌム・オプス(風) [503920, enemy]: MP 22, power 20. Deal Wind magic damage to all enemies 3 times.

### Lilith — 5

Dark counter tank and protective magic.

Sprite `401005905` (GL); base-stat budget: Cecil. Growth: Cloud.

- Awakening 1: Dark [220390]; Vampiric Lash [486836]; Resist Light [1252]; Physical Defense +20% [1313].
- Awakening 2: Darkra [220520]; Power Stagger [414600]; Poison Mist [486812]; Shock Claw [486815]; HP +20% [1378].
- Awakening 3: Darkga [220400]; Shadowbringer [445310]; Royal Guard [414610]; Seal of Conviction [486803]; Dark Sunder [486806]; Dark Aegis [486809]; Fill LB when Taking Damage [1331].
- Awakening 4: Nihilistic Solitude [486830]; Obsidian Vortex [486833]; Dark Feast [486839]; Grit [1042]; Paladin’s Code [1413].
- MR 1: Damage Reduction +20% [1513].
- MR 2: HP +30 (permanent).
- MR 3: Cover [400380].
- MR 4: AP +8 (permanent).
- MR 5: Riposte [1339].
- MR 6: Mind +10 (permanent).
- MR 7: Critical Counter [1333].
- MR 8: Defence +15 (permanent).
- MR 9: Dark Immunity [1369]; AP +8 (permanent); Spirit of Lilith.

Supplemental player copies (native source ID; final MP/power):

- Seal of Conviction ← Seal of Conviction [505580, enemy]: MP 32, power 30. Deal Dark physical damage to all enemies 2 times.
- Dark Sunder ← Darkness’s Dawn [505560, enemy]: MP 28, power 0. Reduce enemy physical and magic defense by 30% for 3 turns.
- Dark Aegis ← Darkness’s Advance [505570, enemy]: MP 40, power 0. Reduce party physical and magic damage taken by 30%.
- Poison Mist ← Poison Gas [500560, enemy]: MP 18, power 0. Inflict Poison with a 50% chance.
- Shock Claw ← Shock Claw [503240, enemy]: MP 22, power 28. Deal physical damage to an enemy. Inflict Paralysis.
- Nihilistic Solitude ← Nihilistic Solitude [506040, enemy]: MP 30, power 24. Deal Dark magic damage to all enemies. remove enemy buffs.
- Obsidian Vortex ← Obsidian Vortex [505550, enemy]: MP 30, power 0. Inflict Confusion.
- Vampiric Lash ← Vampiric Lash [571110, enemy]: MP 12, power 12. Deal Dark physical damage to an enemy 2 times. Absorb damage dealt as HP.
- Dark Feast ← Feed [503700, enemy]: MP 35, power 40. Deal Dark magic damage to an enemy. Absorb damage dealt as HP.

### Dragon Knight Freya — 5

Aerial light physical and water lance.

Sprite `209001805` (GL); base-stat budget: Noctis. Growth: Cloud.

- Awakening 1: Water Surge [421190]; Flash Flood [486906]; Sonic Boom [486918]; Lance Thrust [486930]; Splash Lance [486939]; Mana Lance [486921]; Physical Attack +20% [1309]; Magic Attack +20% [1311].
- Awakening 2: Warp-Strike [447810]; Watera Surge [421200]; Crystal Lance [486903]; Venom Lance [486915]; Lance Storm [486933]; Cleansing Lance [486936]; Tidal Lance [486942]; Critical Hit Rate +10% [1247].
- Awakening 3: Plunge [447800]; Waterga Surge [421210]; Gungnir [486909]; Hydro Lance [486912]; Ocean Lance [486945]; Speed +10% [1277]; Stagger Power +20% [1279]; HP +20% [1378].
- Awakening 4: Leaping Cleave [1357]; Phase Echo [1360]; Fire Immunity [1362]; Warp Crit [1466].
- MR 1: Fill LB on Defeating Foes [1320].
- MR 2: HP +30 (permanent).
- MR 3: Reflex [1257].
- MR 4: AP +8 (permanent).
- MR 5: Deft Warp [1361].
- MR 6: Agility +10 (permanent).
- MR 7: Bonus Damage [1335].
- MR 8: Attack +15 (permanent).
- MR 9: Barrage [400300]; AP +8 (permanent); Spirit of Dragon Knight Freya.

Supplemental player copies (native source ID; final MP/power):

- Crystal Lance ← Crystal Lance [501610, enemy]: MP 20, power 30. Deal physical damage to an enemy.
- Flash Flood ← Flash Flood [500770, enemy]: MP 12, power 18. Deal Water physical damage to an enemy.
- Gungnir ← Gungnir [505810, enemy]: MP 40, power 40. Deal physical damage to an enemy.
- Hydro Lance ← Hydro Breath [503830, enemy]: MP 26, power 28. Deal Water physical damage to all enemies.
- Venom Lance ← Poison Tail [500870, enemy]: MP 15, power 24. Deal physical damage to an enemy. Inflict Poison.
- Sonic Boom ← Sonic Boom [500440, enemy]: MP 12, power 18. Deal Wind physical damage to an enemy.
- Lance Thrust ← Stab [500090, enemy]: MP 10, power 18. Deal physical damage to an enemy.
- Lance Storm ← Stab [502600, enemy]: MP 24, power 34. Deal physical damage to an enemy.
- Cleansing Lance ← Clear Smog [571140, enemy]: MP 22, power 12. Deal Water physical damage to all enemies. remove enemy buffs.
- Splash Lance ← Water [255090, enemy]: MP 12, power 12. Deal Water physical damage to all enemies.
- Tidal Lance ← Watera [255100, enemy]: MP 20, power 18. Deal Water physical damage to all enemies 2 times.
- Ocean Lance ← Waterga [255110, enemy]: MP 28, power 24. Deal Water physical damage to all enemies 3 times.
- Mana Lance ← Giga-Syphon [503690, enemy]: MP 12, power 10. Drain MP from an enemy.

### Trance Terra — 5

Dark/fire magic, poison and costly finishers.

Sprite `206000125` (GL); base-stat budget: Shantotto. Growth: Terra.

- Awakening 1: Poison [220250]; Fire [220010]; Nullify Silence [1107]; Magic Attack +30% [1275].
- Awakening 2: Nightmare Scythe [447300]; Bio [220260]; Fira [220020]; Firaga [220030]; MP +20% [1381].
- Awakening 3: Salvation Scythe [447310]; Death [220320]; Meltdown [220380]; Spill [487103]; Trance Judgment [487106]; Judgment Shadow [487109]; Hell Pillar [487112]; Trance Apocalypse [487130].
- Awakening 4: Meteor [220350]; Ultima [220340]; MP Stroll [1307]; The Federation’s Fiend [1432]; Play Rough [1433].
- MR 1: Fire Eater [1038].
- MR 2: Agility +5 (permanent).
- MR 3: Restore MP on Defeating Foes [1319].
- MR 4: AP +8 (permanent).
- MR 5: Magic Defense +20% [1315].
- MR 6: MP +20 (permanent).
- MR 7: Area Effect Adept [1351].
- MR 8: Magic +15 (permanent).
- MR 9: Dualcast [400730]; AP +8 (permanent); Spirit of Trance Terra.

Supplemental player copies (native source ID; final MP/power):

- Spill ← Spill [414300, native]: MP 46, power 45. Deal Dark magic damage to all enemies 2 times.
- Trance Judgment ← Execution [505450, enemy]: MP 35, power 36. Deal Dark magic damage to all enemies 3 times.
- Judgment Shadow ← Judgment of the Shadow [503120, enemy]: MP 30, power 30. Deal magic damage to all enemies.
- Hell Pillar ← Hell’s Pillar [505470, enemy]: MP 26, power 24. Deal Fire magic damage to all enemies 3 times.
- Trance Apocalypse ← Ray of Apocalypse [505540, enemy]: MP 40, power 40. Deal magic damage to all enemies.

### Charming Kitty Ariana — 5

Healing singer with control and arcane attacks.

Sprite `401002405` (GL); base-stat budget: Ayaka. Growth: Terra.

- Awakening 1: Esuna [210120]; Bravery [230100]; Healing Refrain [487203]; Lullaby [487209]; Wind Aria [487233]; Focus [400460]; Healing Magic +30% [1375]; Nullify Silence [1107].
- Awakening 2: Blindga [487212]; Silencega [487215]; Starlight Refrain [487218]; Wind Refrain [487236]; Flame Refrain [487242]; MP +20% [1381].
- Awakening 3: Gravity [220280]; Restoring Refrain [487206]; Dimming Refrain [487230]; Winter Refrain [487239]; Dazzling Refrain [487221]; Speed +10% [1277].
- Awakening 4: Confuse [230180]; Graviga [220290]; Alabastrine Blessing [1455].
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

- Healing Refrain ← Cure [215000, native]: MP 12, power 200. Restore all allies’ HP.
- Restoring Refrain ← Cura [215010, native]: MP 25, power 500. Restore all allies’ HP.
- Lullaby ← Lullaby [570440, enemy]: MP 8, power 0. Inflict Sleep.
- Blindga ← Blindga [235010, native]: MP 20, power 0. Inflict Blind with a 50% chance.
- Silencega ← Silencega [235020, native]: MP 20, power 0. Inflict Silence with a 50% chance.
- Starlight Refrain ← Array: Light of Destruction [503620, enemy]: MP 24, power 28. Deal Light magic damage to all enemies.
- Dimming Refrain ← Flamewall [506120, enemy]: MP 34, power 30. Deal Fire magic damage to all enemies 3 times. Lower attack and magic.
- Wind Aria ← Aero [250170, enemy]: MP 5, power 14. Deal Wind magic damage to an enemy.
- Wind Refrain ← Aerora [250180, enemy]: MP 15, power 22. Deal Wind magic damage to an enemy 2 times.
- Winter Refrain ← Blizzaga [255050, enemy]: MP 28, power 24. Deal Ice magic damage to all enemies 3 times.
- Flame Refrain ← 大魔法マグヌム・オプス(火) [503910, enemy]: MP 22, power 20. Deal Fire magic damage to all enemies 3 times.
- Dazzling Refrain ← Alluring Pollen [503770, enemy]: MP 30, power 24. Deal magic damage to all enemies. May inflict Confusion, Charm, Silence and Blind.

### Elephim — 7

Buff/debuff bard with ranged attacks.

Sprite `100017107` (GL); base-stat budget: Vaan. Growth: Terra.

- Awakening 1: Debrave [230190]; Blind [230020]; Faith [230110]; Berserk [230170]; Sleep [487303]; Defaith [487306]; Resonant Notes [487327]; Magic Attack +20% [1311].
- Awakening 2: Rapid Fire [414200]; Debravega [487309]; Defaithga [487312]; Sleepga [487315]; Flame Chant [487330]; Nullify Silence [1107]; Resist Lightning [1250]; MP +20% [1381].
- Awakening 3: Disorder [414210]; Berserker Samba [487324]; Harp Volley [487333]; Strategic Acumen [1336].
- Awakening 4: Inspire [487321]; Rallying Song [487318]; Speed +10% [1277].
- MR 1: Gil Farmer [400400].
- MR 2: Mind +5 (permanent).
- MR 3: Deshell on Stagger [1285].
- MR 4: AP +8 (permanent).
- MR 5: Deprotect on Stagger [1235].
- MR 6: MP +20 (permanent).
- MR 7: Haste Opener [1292].
- MR 8: Agility +15 (permanent).
- MR 9: Gil Farmer on Stagger [1386]; AP +8 (permanent); Spirit of Elephim.

Supplemental player copies (native source ID; final MP/power):

- Sleep ← Sleep [230010, native]: MP 5, power 0. Inflict Sleep with a 80% chance.
- Defaith ← Defaith [230200, native]: MP 6, power 0. Lower magic.
- Debravega ← Debravega [235050, native]: MP 24, power 0. Lower attack.
- Defaithga ← Defaithga [235060, native]: MP 24, power 0. Lower magic.
- Sleepga ← Sleepga [235000, native]: MP 20, power 0. Inflict Sleep with a 50% chance.
- Rallying Song ← Get them! [501120, enemy]: MP 45, power 0. Increase party magic and speed by 50%.
- Inspire ← Inspire [570130, enemy]: MP 42, power 0. Increase an ally’s attack/magic by 50% and reduce incoming physical/magic damage by 30%.
- Berserker Samba ← Samba de Flan [570420, enemy]: MP 28, power 0. Inflict Berserk.
- Resonant Notes ← Cut [500060, enemy]: MP 6, power 12. Deal magic damage to an enemy.
- Flame Chant ← Flame [500340, enemy]: MP 6, power 12. Deal Fire magic damage to all enemies.
- Harp Volley ← Swing [500070, enemy]: MP 6, power 12. Deal Wind physical damage to an enemy 2 times.

### Jade — 5

Lightning martial attacker and crowd damage.

Sprite `337001205` (GL); base-stat budget: Cloud. Growth: Cloud.

- Awakening 1: Thunder Blade [420070]; Sparkstrike [421160]; Rocket Punch [487409]; Charge [487412]; Volt Kick [487430]; Thunder Palm [487433]; Resist Lightning [1250]; Physical Attack +20% [1309].
- Awakening 2: Thundara Blade [420080]; Sparkstrike II [421170]; Volt Palm [487403]; Gigavolt Strike [487406]; Thunder Palm II [487436]; Bladeblitz [400310]; Critical Hit Rate +10% [1247].
- Awakening 3: Thundaga Blade [420090]; Sparkstrike III [421180]; Thunder Palm III [487439]; Storm Flurry [487442]; Fist of the Storm [487445]; Speed +10% [1277]; HP +20% [1378]; Power Stagger [1385].
- Awakening 4: Reckless Abandonment [400700]; Critical Boost [1234].
- MR 1: Restore MP on Critical Hit [1323].
- MR 2: HP +30 (permanent).
- MR 3: Lightning Immunity [1366].
- MR 4: AP +8 (permanent).
- MR 5: Fill Gauge [400770].
- MR 6: Agility +10 (permanent).
- MR 7: Vigorous Staggerer [1371].
- MR 8: Attack +15 (permanent).
- MR 9: Quick Hit [1359]; AP +8 (permanent); Spirit of Jade.

Supplemental player copies (native source ID; final MP/power):

- Volt Palm ← Megavolt [500180, enemy]: MP 14, power 17. Deal Lightning physical damage to an enemy. Inflict Paralysis.
- Gigavolt Strike ← Gigavolt [500400, enemy]: MP 20, power 24. Deal Lightning physical damage to an enemy 2 times.
- Rocket Punch ← Rocket Punch [500730, enemy]: MP 10, power 18. Deal physical damage to an enemy.
- Charge ← Charge [501040, enemy]: MP 12, power 24. Deal physical damage to an enemy. Inflict Paralysis with a 50% chance.
- Volt Kick ← Lightning Bolt [500220, enemy]: MP 12, power 18. Deal Lightning physical damage to an enemy.
- Thunder Palm ← Thunder [255060, enemy]: MP 12, power 12. Deal Lightning physical damage to all enemies.
- Thunder Palm II ← Thundara [255070, enemy]: MP 20, power 18. Deal Lightning physical damage to all enemies 2 times.
- Thunder Palm III ← Thundaga [255080, enemy]: MP 28, power 24. Deal Lightning physical damage to all enemies 3 times.
- Storm Flurry ← Octo-Strike [501070, enemy]: MP 28, power 32. Deal Lightning physical damage to random enemies 4 times.
- Fist of the Storm ← Fist of Ferocity [502380, enemy]: MP 35, power 40. Deal Lightning physical damage to an enemy.

### Spirited Heart Primm — NV Super Limit Burst

Mixed elemental sabers and support.

Sprite `304000717` (GLW); base-stat budget: Onion Knight. Growth: Lightning.

- Awakening 1: Slice & Dice - Wind [421280]; Stone Blade [420160]; Cure [487503]; Magic Attack +20% [1311]; Nullify Slow [1116].
- Awakening 2: Slice & Dice - Wind II [421290]; Stonera Blade [420170]; Cura [487506]; Firestorm Saber [487512]; Atomic Saber [487515]; Flame Saber [487530]; Blazing Saber [487518]; MP +20% [1381].
- Awakening 3: Slice & Dice - Wind III [421300]; Stonega Blade [420180]; Moonlightbringer [445300]; Gale Saber [487533]; Spiritlight Saber [487536]; Mana Burst [487539]; Speed +10% [1277]; Regen Opener [1293].
- Awakening 4: Curaga [487509]; Fill Gauge [400770]; Restore HP on Stagger [1284].
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

- Cure ← Cure [240010, enemy]: MP 6, power 200. Restore an ally’s HP.
- Cura ← Cura [240020, enemy]: MP 18, power 500. Restore an ally’s HP.
- Curaga ← Curaga [240030, enemy]: MP 50, power 1500. Restore an ally’s HP.
- Firestorm Saber ← Firestorm [500360, enemy]: MP 20, power 18. Deal Fire physical damage to all enemies.
- Atomic Saber ← Atomic Ray [500380, enemy]: MP 20, power 24. Deal Fire physical damage to an enemy.
- Flame Saber ← Fira [255010, enemy]: MP 20, power 18. Deal Fire physical damage to all enemies 2 times.
- Gale Saber ← Aerora [255130, enemy]: MP 20, power 18. Deal Wind physical damage to all enemies 2 times.
- Spiritlight Saber ← Banishra [225300, native]: MP 35, power 33. Deal Light physical damage to all enemies 2 times.
- Mana Burst ← Countermeasure [503190, enemy]: MP 26, power 27. Deal magic damage to all enemies.
- Blazing Saber ← Fire [255000, enemy]: MP 14, power 18. Deal Fire physical damage to all enemies.

### Relm — 5

Painter with lightning magic and mimicry.

Sprite `206001005` (GL); base-stat budget: Shantotto. Growth: Terra.

- Awakening 1: Thunder [220090]; Fire Beam [487606]; Drain [487615]; Earth Canvas [487630]; Frost Canvas [487636]; Aether Palette [487624]; Magic Attack +30% [1275]; Nullify Silence [1107].
- Awakening 2: Thundara [220100]; Thundaga [220110]; Bioblaster [487603]; El Nino [487609]; Banishra Canvas [487618]; Earth Canvas II [487633]; Stone Stroke [487642]; Storm Canvas [487627].
- Awakening 3: Forbidden Ars Magna [487612]; Erase Canvas [487639]; MP +20% [1381]; Magic Defense +20% [1315].
- Awakening 4: Flare [220330]; Mind Blast [487621]; Mimic [400330]; MP Stroll [1307].
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

- Bioblaster ← Bioblaster [500970, enemy]: MP 18, power 12. Deal magic damage to all enemies. Inflict Poison with a 70% chance.
- Fire Beam ← Fire Beam [500980, enemy]: MP 12, power 18. Deal Fire magic damage to an enemy.
- El Nino ← El Niño [501010, enemy]: MP 20, power 18. Deal Water magic damage to all enemies.
- Forbidden Ars Magna ← 禁呪アルス・マグナ [503930, enemy]: MP 26, power 26. Deal magic damage to all enemies.
- Drain ← Drain [250300, enemy]: MP 12, power 12. Deal magic damage to an enemy. Absorb damage dealt as HP.
- Banishra Canvas ← Banishra [245300, enemy]: MP 20, power 18. Deal Light magic damage to all enemies 2 times.
- Mind Blast ← Mind Blast [500750, enemy]: MP 45, power 24. Deal Lightning magic damage to an enemy. Inflict Paralysis, Silence and Poison.
- Earth Canvas ← Stone [255150, enemy]: MP 12, power 12. Deal Earth magic damage to all enemies.
- Earth Canvas II ← Stonera [255160, enemy]: MP 20, power 18. Deal Earth magic damage to all enemies 2 times.
- Frost Canvas ← Blizzard [225030, native]: MP 12, power 17. Deal Ice magic damage to all enemies.
- Erase Canvas ← Liquidate [503200, enemy]: MP 40, power 40. Deal magic damage to all enemies.
- Stone Stroke ← Stonera [250220, enemy]: MP 15, power 22. Deal Earth magic damage to an enemy 2 times.
- Aether Palette ← Regurgitate [570630, enemy]: MP 18, power 30. Restore 30 MP to an ally.
- Storm Canvas ← Thundaga [250110, enemy]: MP 30, power 30. Deal Lightning magic damage to an enemy 3 times.

### Rikku (FFX-2) — 6

Thief, item utility and fire physical breaks.

Sprite `249000206` (GL); base-stat budget: Vaan. Growth: Cloud.

- Awakening 1: Steal Strength [446840]; Steal Speed [446850]; Flash Bomb [487703]; Sleep Needle [487706]; Poison Needle [487709]; Nullify Berserk [1114]; Speed +20% [1317]; Thievery [1426].
- Awakening 2: Red Spiral [447400]; Acid Grenade [487736]; Incendiary Sphere [487739]; Discerning Eye [1056]; HP +20% [1378].
- Awakening 3: White Whorl [447410]; Blinding Flash [487730]; Mustard Bomb [487733]; Wave Cannon [487742]; Trickshot [487745]; Emergency Protocol [487748]; Quick Repair [487751]; Haste on Stagger [1287].
- Awakening 4: Gil Farmer [400400]; Gil Toss [400250]; Restore MP on Attack [1124]; Wings of Freedom [1436].
- MR 1: Steal [400260].
- MR 2: HP +30 (permanent).
- MR 3: Treasure Hunter [1387].
- MR 4: AP +8 (permanent).
- MR 5: Mug [400270].
- MR 6: Attack +10 (permanent).
- MR 7: One for the Road [1435].
- MR 8: Agility +15 (permanent).
- MR 9: Misfortune [400750]; AP +8 (permanent); Spirit of Rikku (FFX-2).

Supplemental player copies (native source ID; final MP/power):

- Flash Bomb ← Flash Bomb [501020, enemy]: MP 10, power 6. Deal physical damage to all enemies. Inflict Blind with a 30% chance.
- Sleep Needle ← Sleep Needle [500300, enemy]: MP 8, power 12. Deal physical damage to an enemy. Inflict Sleep.
- Poison Needle ← Poison Needle [500280, enemy]: MP 8, power 12. Deal physical damage to an enemy. Inflict Poison.
- Blinding Flash ← Blinding Flash [571540, enemy]: MP 28, power 24. Deal physical damage to all enemies. Inflict Blind.
- Mustard Bomb ← Mustard Bomb [571550, enemy]: MP 40, power 40. Deal physical damage to all enemies. Inflict Paralysis with a 50% chance.
- Acid Grenade ← Secrete Acid [501650, enemy]: MP 24, power 18. Deal physical damage to all enemies. Inflict Poison with a 50% chance.
- Incendiary Sphere ← Incineration Sphere [571530, enemy]: MP 22, power 18. Deal Fire physical damage to all enemies. May lower attack and magic.
- Wave Cannon ← Wave Cannon [505120, enemy]: MP 35, power 36. Deal magic damage to all enemies.
- Trickshot ← Triple Threat [505940, enemy]: MP 30, power 36. Deal physical damage to random enemies 3 times.
- Emergency Protocol ← Analyze Movement Pattern [571520, enemy]: MP 30, power 0. Remove own ailments/debuffs and gain 30% physical/magic protection for 3 turns.
- Quick Repair ← Cannibalize [501290, enemy]: MP 30, power 200. Restore 200 HP to all allies.

### Nalu — 5

Lightning physical, criticals and analysis.

Sprite `100015405` (GL); base-stat budget: Cloud. Growth: Cloud.

- Awakening 1: Thunder Surge [421130]; Libra [210220]; Thunder Spear [487803]; Lightning Sweep [487806]; Needle [487812]; Lance Launcher [487836]; Resist Lightning [1250]; Physical Attack +20% [1309].
- Awakening 2: Braver [446000]; Thundara Surge [421140]; Lightning Strike [447500]; Lightning Lance Sweep [487830]; Shock Lance [487839]; Critical Hit Rate +10% [1247]; Imbue Lightning [1523].
- Awakening 3: Cross-Slash [446010]; Thundaga Surge [421150]; Thunderfall [447510]; Chain Lance [487809]; Thunderstorm Lance [487833]; Numbing Spark [487842]; Thunder Javelin [487845]; HP +20% [1378].
- Awakening 4: Signature Moves [1418]; Broadsword Mastery [1420].
- MR 1: Restore MP on Attack [1124].
- MR 2: Agility +5 (permanent).
- MR 3: Deathblow [400530].
- MR 4: AP +8 (permanent).
- MR 5: Scan and Strike [1399].
- MR 6: HP +60 (permanent).
- MR 7: Stagger Power +20% [1279].
- MR 8: Attack +15 (permanent).
- MR 9: Critical Boost [1234]; AP +8 (permanent); Spirit of Nalu.

Supplemental player copies (native source ID; final MP/power):

- Thunder Spear ← Thunder Beam [501000, enemy]: MP 12, power 18. Deal Lightning physical damage to an enemy.
- Lightning Sweep ← Lightning [500390, enemy]: MP 12, power 12. Deal Lightning physical damage to all enemies 2 times.
- Chain Lance ← Chain Spark [220120, native]: MP 30, power 30. Deal Lightning physical damage to all enemies 3 times.
- Needle ← Needle [500260, enemy]: MP 8, power 18. Deal physical damage to an enemy.
- Lightning Lance Sweep ← Thunder [225060, native]: MP 15, power 17. Deal Lightning physical damage to all enemies.
- Thunderstorm Lance ← Thunderstorm [506140, enemy]: MP 36, power 30. Deal Lightning physical damage to all enemies 3 times. Inflict Paralysis.
- Lance Launcher ← Launcher [500880, enemy]: MP 10, power 12. Deal Lightning physical damage to an enemy 2 times.
- Shock Lance ← Array: Shock Shell [503610, enemy]: MP 20, power 26. Deal Lightning physical damage to an enemy.
- Numbing Spark ← Thunderspark [250360, enemy]: MP 32, power 30. Deal Lightning physical damage to an enemy. Inflict Paralysis with a 50% chance.
- Thunder Javelin ← Regurgitate [570650, enemy]: MP 28, power 36. Deal Lightning physical damage to an enemy.

### Elza — 5

Dark/water physical and sustained pressure.

Sprite `302000605` (GL); base-stat budget: Tidus. Growth: Cloud.

- Awakening 1: Dark Surge [422050]; Spiral Cut [447000]; Slice & Dice - Water [421220]; Resist Water [1251]; Physical Attack +20% [1309].
- Awakening 2: Darkra Surge [422060]; Slice & Dice - Water II [421230]; Queenly Rend [487903]; Venom Sweep [487909]; HP +20% [1378].
- Awakening 3: Darkga Surge [422070]; Energy Rain [447010]; Spiral Cut+ [447020]; Slice & Dice - Water III [421240]; Shred [487906]; Black Tide [487912]; Rabid Claw [487930]; Abyssal Rend [487933].
- Awakening 4: Ferocious Strike [487936]; Crushing Tide [487939]; Judgment Claw [487942]; Restore MP on Attack [1124]; Fill LB on Defeating Foes [1320]; Imbue Dark [1528].
- MR 1: Resist Dark [1253].
- MR 2: HP +30 (permanent).
- MR 3: Speed +20% [1317].
- MR 4: AP +8 (permanent).
- MR 5: Reckless Abandonment [400700].
- MR 6: Agility +10 (permanent).
- MR 7: Skyward Dreams [1434].
- MR 8: Attack +15 (permanent).
- MR 9: Tip-Top Shape [1428]; AP +8 (permanent); Spirit of Elza.

Supplemental player copies (native source ID; final MP/power):

- Queenly Rend ← Queenly Whip [505910, enemy]: MP 16, power 16. Deal Dark physical damage to an enemy 2 times. reduce enemy attack and magic.
- Shred ← Shred [503580, enemy]: MP 25, power 35. Deal physical damage to an enemy.
- Venom Sweep ← Digestive Fluid [500490, enemy]: MP 15, power 12. Deal physical damage to all enemies. Inflict Poison with a 50% chance.
- Black Tide ← Sludge [503660, enemy]: MP 26, power 28. Deal Water physical damage to all enemies.
- Rabid Claw ← Rabid Claw [502040, enemy]: MP 26, power 30. Deal Dark physical damage to an enemy. May inflict Confusion and Berserk.
- Abyssal Rend ← Regurgitate [570610, enemy]: MP 32, power 40. Deal Dark physical damage to an enemy. May inflict Poison, Paralysis and Slow.
- Ferocious Strike ← Ferocious Strike [503650, enemy]: MP 32, power 30. Deal Dark physical damage to all enemies. Inflict Paralysis with a 50% chance.
- Crushing Tide ← Crushing Breath [505400, enemy]: MP 26, power 28. Deal Water physical damage to all enemies.
- Judgment Claw ← Judgment of the Claw [503130, enemy]: MP 28, power 30. Deal Dark physical damage to all enemies.

### Lunera — 6

Wind physical and stagger support.

Sprite `100007506` (GL); base-stat budget: Bartz. Growth: Cloud.

- Awakening 1: Aero Blade [420130]; Gale Sweep [488033]; Twin Gale Shot [488042]; Physical Attack +20% [1309].
- Awakening 2: Aerora Blade [420140]; Crushing Blade [445500]; Torrential Hew [414400]; Shamshir [488003]; Gale Volley [488006]; Venom Gale [488015]; Gale Reprisal [488039]; Resist Wind [1248].
- Awakening 3: Aeroga Blade [420150]; Wind Cutter Blade [445510]; Aquatic Synergy [414410]; Merciless Gale [488009]; Star Volley [488012]; Silencing Gale [488036]; Restore MP on Stagger [1281]; Lingering Debuffs [1510].
- Awakening 4: Tempest Volley [488030]; Double MRP [1051]; Stagger Power +30% [1376].
- MR 1: Wait [400760].
- MR 2: Agility +5 (permanent).
- MR 3: Spry Steps [1258].
- MR 4: AP +8 (permanent).
- MR 5: Speed +5% [1316].
- MR 6: HP +60 (permanent).
- MR 7: Guiding Wind [1458].
- MR 8: Attack +15 (permanent).
- MR 9: Mimic [400330]; AP +8 (permanent); Spirit of Lunera.

Supplemental player copies (native source ID; final MP/power):

- Shamshir ← Shamshir [500450, enemy]: MP 16, power 24. Deal Wind physical damage to an enemy.
- Gale Volley ← Wing Flap [503720, enemy]: MP 20, power 20. Deal Wind magic damage to all enemies 3 times.
- Merciless Gale ← Merciless Judgment [505270, enemy]: MP 38, power 40. Deal Wind physical damage to an enemy 3 times.
- Star Volley ← Flare Star [500900, enemy]: MP 32, power 30. Deal physical damage to all enemies.
- Venom Gale ← Venom Breath [501900, enemy]: MP 24, power 18. Deal Wind physical damage to all enemies. Inflict Poison with a 30% chance.
- Tempest Volley ← Aeroga [225140, native]: MP 42, power 40. Deal Wind physical damage to all enemies 3 times.
- Gale Sweep ← Aero [255120, enemy]: MP 12, power 12. Deal Wind physical damage to all enemies.
- Silencing Gale ← Windwail [506150, enemy]: MP 34, power 30. Deal Wind physical damage to all enemies 3 times. Inflict Silence.
- Gale Reprisal ← Counter Vines [502620, enemy]: MP 20, power 26. Deal Wind physical damage to an enemy 2 times.
- Twin Gale Shot ← Whip [500120, enemy]: MP 8, power 12. Deal Wind physical damage to an enemy 2 times.

## Research and validation limits

Selected hosted packs were checked against their published SHA-256 values, including base packs for shifted forms. Unit records, selected-form sprite motions and LB profiles were inspected. FFBE themes are references, not imported combat numbers. The archived Global datamine is `aEnigmatic/ffbe` at `95727376e82d27acc1290b6dc8ad27ce3c89ea71`; hosted merged records also cover Japanese and post-archive forms. Reberta’s Japanese hosted record has no translated skill list; her requested physical dragoon role and the original Reberta elemental/jump theme guide that kit.

Automated checks cover portable configs, unique allocation, native base stats, MR scheduling and role budgets, mastery caps, owner-condition rebinding, native table patch serialization, and optional-pack lifecycle. They do not establish live-game balance or prove every animation exists in the demo. Library repairs use the existing unverified-skill controls. The separate **Use borrowed Sephira skill visuals** toggle defaults on; turn it off and rebuild/install to restore the 226 preset source visual mappings without changing mechanics or saved kits. Turn it on and rebuild/install to restore borrowed visuals. Explicit visual donor edits and authored sequences are preserved. The 39 custom elemental attacks based on neutral sources receive a native elemental impact at their original hit; no damage keys, sounds or battle-speed effects are added. If an optional borrowed visual is already elemental, its native effect supplies that presentation. Skill icons follow actual damage elements. Every added vision has its own command and Spirit icon, without consuming another original vision’s icon slot. Original full-game source exceptions are recorded in [the runtime review](docs/SEPHIRA_RUNTIME_REVIEW.md).

## Full-game release review

Re-audit native stats, level curves, skill mechanics and unlock ranks; private command/LB conditions and IDs; summon availability; selected form/LB presentation; and vendor/acquisition availability. Preserve user edits; apply MR/acquisition revisions through the backed-up progression update. See README’s running full-release checklist.
