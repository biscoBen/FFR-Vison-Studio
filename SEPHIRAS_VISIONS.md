# Sephira’s Visions

31 optional, editable presets using the requested FFBE forms. Enable the section on the home page, then build/install. First enable downloads only the missing selected artwork and adds the profiles after all preparations succeed.

Turning the section off keeps edits and removed entries; its units and acquisition caves are omitted by the next build. **Restore missing** adds removed presets without resetting existing ones. **Reset all presets** or a card’s **Reset to preset** replaces its kit and appearance, preserves its IDs and acquisition location, and backs up the previous roster in Studio’s character-config backups.

An existing custom Crystal Fina is adopted with her current edits and acquisition intact. Reset her explicitly to use this balanced recipe. Other user-added copies and original vision/party edits are preserved.

## Balance and coverage

- Every preset copies a native level-one stat profile and its exact permanent MR stat rewards/ranks. AP remains the native +8 at MR 4 and +8 at MR 9. Native physical or magic growth curves are used.
- Native skills retain damage, MP cost, targeting, equip cost and effects. No FFBE multipliers or FFBE stat conversion are imported. LBs retain one native resonance’s total mechanics; selected elements/damage types follow the requested role, and their own FFBE sprite animations supply presentation.
- All 160 distinct active skills and 131 passives from the 15 excluded original visions are allocated. Within the pack, each exact active/passive appears once; permanent MR stats may repeat. Additional native skills provide thematic attacks and support. Each new vision has its own correctly bound Spirit mastery wrapper.
- Command/LB-specific bonuses use private rebound copies. Native originals remain unchanged. Minfilia’s Dual Jobs selects her own identity. Specific skill bonuses remain grouped with their required attacks.
- Most presets have fewer options than a complete original kit. They specialize without being restricted to one action type: healers and debuffers also have attacks. Added visions default to a 1,000-gil vendor price; acquisition can be edited normally.
- Eiko uses the demo’s available Ifrit and Shiva summon commands; their native costs and mechanics are retained. Unreleased espers are not required.

The excluded originals are Tronn, Wilhelm, Warrior of Light, Firion, Onion Knight, Cecil, Bartz, Cloud, Squall, Zidane, Tidus, Shantotto, Vaan, Noctis and Clive. Their exact grants, native ranks, descriptions, mechanics and allocations are retained in `assets/sephira_visions/native_coverage.json`.

## Selected forms and kits

Awakening ranks below are numbered 1–4 for readability. MR ranks use the game’s 0–9 values. Native source names are retained for skills so their exact versions remain identifiable.

### A2 — 5

Physical combo attacker.

Sprite `310000505` (GL); stat/MR budget: Squall. Growth: Cloud.

- Awakening 1: Physical Attack +20% [1309].
- Awakening 2: Rough Divide [446600]; Nullify Blind [1105]; HP +20% [1378].
- Awakening 3: Fated Circle [446610].
- Awakening 4: Lone Lion [1423]; Latent Potential [1424].
- MR 1: Mineuchi [400500]; Improvement [1421].
- MR 3: Gut Rip [400690].
- MR 5: Trigger [1422].
- MR 9: Barrage [400300]; Double Action [400710].

### Christine — 6

Ice magic and stagger.

Sprite `401002606` (GL); stat/MR budget: Tronn. Growth: Terra.

- Awakening 1: Blizzard [220050]; Silence [230030]; Dispel [210200]; Stagger Power +30% [1376].
- Awakening 2: Blizzara [220060]; Blizzaga [220070]; Resist Ice [1033]; Victor’s Respite [1407].
- Awakening 3: Deshell on Stagger [1285].
- Awakening 4: True Stagger [1406].
- MR 1: Restore MP on Stagger [1281].
- MR 5: Focus Magic [400630].
- MR 9: Half MP Cost [1045].

### Crystal Fina — Custom

Healing, cleansing and light magic.

Sprite `99887755552703` (CUSTOM); stat/MR budget: Ayaka. Growth: Terra.

- Awakening 1: Cure [210010]; Banish [210250]; Healing Magic +30% [1375]; Alabastrine Blessing [1455].
- Awakening 2: Cura [210020]; Banishra [210260]; Healing Magic +20% [1283].
- Awakening 3: Curaga [210030]; Banishga [210270]; Arise [210150].
- Awakening 4: Esunaga [210130]; Divine Tidings [1456].
- MR 5: Prepare Healing [400740].
- MR 7: The Hand That Heals [1393].
- MR 9: LB Charge on Heal [1397].

### Barusa — 6

Earth physical bruiser and protection.

Sprite `401003006` (GL); stat/MR budget: Wilhelm. Growth: Cloud.

- Awakening 1: Stone Surge [421400]; Stone Slam [421340]; General’s Pride [1452]; Physical Defense +20% [1313].
- Awakening 2: Stonera Surge [421410]; Stonera Slam [421350]; D Sword Breaker [414700].
- Awakening 3: Stonega Surge [421420]; Stonega Slam [421360]; Supreme Defense [414710]; HP +30% [1379].
- Awakening 4: Unmoving Bulwark [1453]; Bastion [1454].
- MR 1: Strategic Acumen [1336].
- MR 5: Guard [400640].

### Blue Sky Belle Fran — 6

Ranged physical and disabling arrows.

Sprite `212001706` (GL); stat/MR budget: Firion. Growth: Cloud.

- Awakening 1: Aero Knife [421250]; Thunder Knife [421100]; Sleep Knife [422010]; Dual Guns [1443].
- Awakening 2: Aerora Knife [421260]; Thundara Knife [421110]; Blind Knife [422030]; Add Poison [1125]; Add Silence [1126]; Critical Hit Rate +5% [1321].
- Awakening 3: Aeroga Knife [421270]; Thundaga Knife [421120]; Add Blind [1128].
- MR 3: Aim [400450].
- MR 5: Decimating Attacks [1337].

### Oracle Maiden Lunafreya — NV Brave Shift

Debuff specialist with water/wind magic.

Sprite `215002417` (GL); stat/MR budget: Zidane. Growth: Terra.

- Awakening 1: Free Energy [446800]; Deprotect [230080]; Add Deprotect [1131]; Add Deshell [1132].
- Awakening 2: Meo Twister [446820]; Steal Vitality [446860]; Deshell [230090].
- Awakening 3: Free Energy+ [446810]; Steal Magic [446870].
- Awakening 4: Meo Twister+ [446830].
- MR 1: Skilled Disruptor [1326].
- MR 3: Insult to Injury [1425].
- MR 5: Stealth Specialist [1396].
- MR 7: Aggravation [1468].

### Minfilia — 4

Mixed earth/wind offense and party protection.

Sprite `214000304` (GL); stat/MR budget: Onion Knight. Growth: Lightning.

- Awakening 1: Stone [220210]; Protect [230040]; Late Bloomer [1411]; Magic Attack +20% [1311].
- Awakening 2: Stonera [220220]; Protectga [230050].
- Awakening 3: Stonega [220230]; Blade Torrent [445200]; Chuck [1412].
- Awakening 4: Dual Jobs [485690]; Job Change [1410].
- MR 1: Throw [400240].
- MR 5: Observe and Recover HP [1465].
- MR 7: Observe and Attack [1343].

### Folka — 6

Water magic with restorative utility.

Sprite `100018306` (GL); stat/MR budget: Tronn. Growth: Terra.

- Awakening 1: Water [220130]; Syphon [220310]; MP +10% [1380].
- Awakening 2: Watera [220140]; Resist Water [1251].
- Awakening 3: Waterga [220150]; Regen [210050]; Hi Regen [414510].
- Awakening 4: Water Immunity [1367].
- MR 3: Mana Overload [1445].
- MR 5: Pass the Torch [400680]; MP Stroll [1307].
- MR 9: Magic Barrage [400360]; Water Eater [1348].

### Fryevia — 5

Ice spellblade and precision physical.

Sprite `302001405` (GL); stat/MR budget: Bartz. Growth: Cloud.

- Awakening 1: Froststrike [421070].
- Awakening 2: Froststrike II [421080].
- Awakening 3: Froststrike III [421090]; Spellblade Wielder [1415]; Leaping Cleave [1357].
- Awakening 4: Flare Blade [420270]; Spellblade Mastery [1416]; Ice Immunity [1363].
- MR 5: Blade Dance [400350].
- MR 7: Dual Spellblade [1414].
- MR 9: Ice Eater [1344].

### Lenneth — 6

Physical cover tank with light attacks.

Sprite `330000106` (GL); stat/MR budget: Warrior of Light. Growth: Cloud.

- Awakening 1: Vanguard Glaive [445010]; Banish Blade [420330].
- Awakening 2: Banishra Blade [420340]; Protect Opener [1290].
- Awakening 3: Sacred Wave [445020]; Banishga Blade [420350]; Lustrous Shield [1408].
- Awakening 4: Vanguard Glaive+ [445030].
- MR 1: Fill LB when Taking Damage [1331].
- MR 3: Multi-Cover [400390].
- MR 5: Physical Counter [1029].
- MR 7: Heroic Nature [1409].
- MR 9: Grit [1042].

### Lila — 6

Martial physical damage and self recovery.

Sprite `100013806` (GL); stat/MR budget: Firion. Growth: Cloud.

- Awakening 1: Fire Slam [421010]; Fulminating Strike [445100]; Light of Rebellion [1353]; Physical Attack +30% [1273].
- Awakening 2: Fira Slam [421020]; Bravery on Stagger [1288]; Nullify Instant Death [1325].
- Awakening 3: Firaga Slam [421030]; Saber of Adversity [445110].
- Awakening 4: Fulminating Strike+ [445120]; Auto-Regen [1077].
- MR 1: Restore HP on Stagger [1284].
- MR 3: Chakra [400440].
- MR 9: Arms Akimbo [400650].

### Mystea — 5

Magic tank, barriers and counter magic.

Sprite `100011005` (GL); stat/MR budget: Cecil. Growth: Terra.

- Awakening 1: Shell [230060].
- Awakening 2: Shellga [230070]; Manaward [220410]; Magic Defense +20% [1315]; Shell at Half HP [1299]; Magic Counter [1030].
- Awakening 3: Reflect [230120]; Auto-Shell [1073]; Shell Opener [1291].
- Awakening 4: Foul of the Seventh Dawn [220510].
- MR 1: Magic Barrier [1395].
- MR 7: Indomitable Spirit [1402].

### Reberta (JP) — 5

Dragoon with fire/wind spear attacks.

Sprite `100014405` (GL); stat/MR budget: Noctis. Growth: Cloud.

- Awakening 1: Fire Surge [421040]; Aero Surge [421310].
- Awakening 2: Fira Surge [421050]; Aerora Surge [421320].
- Awakening 3: Firaga Surge [421060]; Aeroga Surge [421330].
- Awakening 4: Phase Echo [1360]; Quick Hit [1359].
- MR 1: Fill LB on Defeating Foes [1320].
- MR 3: Jump [400210]; Reflex [1257]; Overwhelm [1437].
- MR 7: Mirage [400670]; Bonus Damage [1335].

### Snow White — 7

Dark physical drain and risk/reward.

Sprite `336000207` (GL); stat/MR budget: Cecil. Growth: Cloud.

- Awakening 1: Dark Blade [420300]; Dark Sword [1457].
- Awakening 2: Darkra Blade [420310]; Sleep Slam [422020]; Drain [220300].
- Awakening 3: Drain Knife [422040]; Darkga Blade [420320].
- Awakening 4: Regen Opener [1293].
- MR 1: Darkness [400490].
- MR 3: Dark Rite [1431]; Restore HP on Defeating Foes [1318].
- MR 7: Staggeringly Risky [1405]; Vigorous Attacks [1358].

### Aria — 5

Water support, healing and water blade.

Sprite `203000905` (GL); stat/MR budget: Leah. Growth: Terra.

- Awakening 1: Water Blade [420100]; Cure of the Seventh Dawn [220480]; Water’s Protection [1462].
- Awakening 2: Watera Blade [420110]; Cure II of the Seventh Dawn [220490]; Purify [414500].
- Awakening 3: Waterga Blade [420120]; Cure III of the Seventh Dawn [220500].
- Awakening 4: Preventive Care [1352].
- MR 1: First Aid [400550]; Angelic Advocate [1401]; Restore MP when Taking Damage [1356].
- MR 3: Healing Magic +10% [1282].
- MR 9: Auto-Cure Ailments [1305].

### Eiko — 7

Summoner with wind magic and revival.

Sprite `209000707` (GL); stat/MR budget: Ayaka. Growth: Terra.

- Awakening 1: Aero of the Seventh Dawn [220450]; Nullify Charm [1111].
- Awakening 2: Aero II of the Seventh Dawn [220460]; Raise [210140]; Nullify Silence [1107].
- Awakening 3: Ifrit [430990]; Shiva [431000]; Aero III of the Seventh Dawn [220470].
- Awakening 4: Reraise [210160]; Unlock Magic [1417].
- MR 5: LB Double Charge [1000].
- MR 7: Recuperate LB [1338].
- MR 9: LB Triple Charge [1031]; Break the Limit [1047].

### Alice/Half Nightmare — NV Brave Shift

Ice physical with burst and HP tradeoffs.

Sprite `336000127` (JP); stat/MR budget: Squall. Growth: Cloud.

- Awakening 1: Blizzard Surge [421370]; Boundless Void [446300]; Critical Hit Rate +10% [1247].
- Awakening 2: Blizzara Surge [421380]; Bravery Opener [1294].
- Awakening 3: Blizzaga Surge [421390]; Purging Blade [446310]; Nullify Sleep [1106].
- MR 3: Deathblow [400530]; Hale and Hearty [1330].
- MR 7: Critical Stagger [1388].
- MR 9: Critical Boost [1234].

### Moogle of Narshe Mog — 5

Wind magic, dance and speed support.

Sprite `206003005` (GL); stat/MR budget: Tidus. Growth: Terra.

- Awakening 1: Aero [220170]; Haste [230130].
- Awakening 2: Aerora [220180]; Resist Wind [1248]; Speed +10% [1277].
- Awakening 3: Aeroga [220190]; Slow [230150]; Haste Opener [1292]; Haste on Stagger [1287].
- Awakening 4: Hastega [230140]; Slowga [230160].
- MR 1: Wait [400760].
- MR 3: First Strike [1049].
- MR 5: Speed +5% [1316].

### Lilith — 5

Dark counter tank and protective magic.

Sprite `401005905` (GL); stat/MR budget: Cecil. Growth: Cloud.

- Awakening 1: Dark [220390].
- Awakening 2: Darkra [220520]; Power Stagger [414600].
- Awakening 3: Darkga [220400]; Shadowbringer [445310]; Royal Guard [414610]; Resist Dark [1253]; Protect at Half HP [1300].
- Awakening 4: Paladin’s Code [1413]; Dark Immunity [1369].
- MR 3: Cover [400380].
- MR 7: Critical Counter [1333].
- MR 9: Riposte [1339].

### Dragon Knight Freya — 5

Aerial light physical and water lance.

Sprite `209001805` (GL); stat/MR budget: Noctis. Growth: Cloud.

- Awakening 1: Water Surge [421190].
- Awakening 2: Warp-Strike [447810]; Watera Surge [421200]; Nullify Slow [1116].
- Awakening 3: Plunge [447800]; Waterga Surge [421210]; Deft Warp [1361].
- Awakening 4: Warp Crit [1466].
- MR 3: Preemptive Strike [1394].
- MR 5: Lance [400280].
- MR 7: Momentum Shift [1438].
- MR 9: Versatility [1340].

### Great Dragon — 4

Fire breath and physical dragon assault.

Sprite `337000704` (GL); stat/MR budget: Clive. Growth: Cloud.

- Awakening 1: Fire [220010]; Boundless Flames [1460].
- Awakening 2: Rising Flames [448000]; Fira [220020]; Firaga [220030]; Resist Fire [1011].
- Awakening 3: Heatwave [448010]; Clive’s Limit Break [1442]; Regen on Stagger [1286].
- Awakening 4: Fire Immunity [1362].
- MR 9: Fire Eater [1038].

### Trance Terra — 5

Dark/fire magic, poison and costly finishers.

Sprite `206000125` (GL); stat/MR budget: Shantotto. Growth: Terra.

- Awakening 1: Poison [220250]; The Federation’s Fiend [1432]; Magic Attack +30% [1275].
- Awakening 2: Nightmare Scythe [447300]; Bio [220260]; MP +20% [1381].
- Awakening 3: Salvation Scythe [447310]; Death [220320]; Meltdown [220380].
- Awakening 4: Meteor [220350]; Ultima [220340]; Play Rough [1433].
- MR 1: Restore MP on Defeating Foes [1319].
- MR 7: Area Effect Adept [1351].
- MR 9: Dualcast [400730].

### Charming Kitty Ariana — 5

Healing singer with control and arcane attacks.

Sprite `401002405` (GL); stat/MR budget: Ayaka. Growth: Terra.

- Awakening 1: Esuna [210120]; Bravery [230100].
- Awakening 2: Nullify Berserk [1114]; Nullify Confuse [1109].
- Awakening 3: Gravity [220280]; Haste at Half HP [1301].
- Awakening 4: Confuse [230180]; Graviga [220290].
- MR 1: Focus [400460]; Skill Flow [1464].
- MR 3: Recover [400540].
- MR 7: Observe and Charge LB [1392]; Heal on Sweeping Stagger [1391].

### Elephim — 7

Buff/debuff bard with ranged attacks.

Sprite `100017107` (GL); stat/MR budget: Vaan. Growth: Terra.

- Awakening 1: Debrave [230190]; Blind [230020]; Faith [230110]; Berserk [230170]; Faith Opener [1295].
- Awakening 2: Rapid Fire [414200]; Throw Down the Gauntlet [1451]; Victor’s Reprieve [1372]; Deprotect on Stagger [1235].
- Awakening 3: Disorder [414210]; Deprotect Opener [1296]; Deshell Opener [1297].

### Jade — 5

Lightning martial attacker and crowd damage.

Sprite `337001205` (GL); stat/MR budget: Cloud. Growth: Cloud.

- Awakening 1: Thunder Blade [420070]; Sparkstrike [421160].
- Awakening 2: Thundara Blade [420080]; Sparkstrike II [421170]; Resist Lightning [1250]; Physical Attack +10% [1308].
- Awakening 3: Thundaga Blade [420090]; Sparkstrike III [421180].
- Awakening 4: Lightning Immunity [1366].
- MR 1: Restore MP on Critical Hit [1323]; Vigorous Staggerer [1371].
- MR 3: Bladeblitz [400310].
- MR 5: Reckless Abandonment [400700]; Power Stagger [1385].

### Spirited Heart Primm — NV Super Limit Burst

Mixed elemental sabers and support.

Sprite `304000717` (GLW); stat/MR budget: Onion Knight. Growth: Lightning.

- Awakening 1: Slice & Dice - Wind [421280]; Stone Blade [420160]; Supercharged Driver [1461].
- Awakening 2: Slice & Dice - Wind II [421290]; Stonera Blade [420170]; Protect on Stagger [1390].
- Awakening 3: Slice & Dice - Wind III [421300]; Stonega Blade [420180]; Moonlightbringer [445300].
- Awakening 4: Ribbon [1355].
- MR 3: Magic Boost [400660]; Staggering Spells [1370].
- MR 5: Fill Gauge [400770]; Magic Attack +10% [1310].

### Relm — 5

Painter with lightning magic and mimicry.

Sprite `206001005` (GL); stat/MR budget: Shantotto. Growth: Terra.

- Awakening 1: Thunder [220090]; Stagger Power +20% [1279].
- Awakening 2: Thundara [220100]; Thundaga [220110]; Nullify Poison [1104].
- Awakening 4: Flare [220330]; Add Confuse [1237].
- MR 1: Arcane Reclamation [1328].
- MR 3: Fill LB on Stagger [1280].
- MR 5: Spell Drinker [400720].
- MR 7: Sharp Mind [1332].
- MR 9: Mimic [400330].

### Rikku (FFX-2) — 6

Thief, item utility and fire physical breaks.

Sprite `249000206` (GL); stat/MR budget: Vaan. Growth: Cloud.

- Awakening 1: Steal Strength [446840]; Steal Speed [446850]; Thievery [1426].
- Awakening 2: Red Spiral [447400]; Discerning Eye [1056].
- Awakening 3: White Whorl [447410].
- Awakening 4: Treasure Hunter [1387]; One for the Road [1435]; Wings of Freedom [1436].
- MR 1: Steal [400260]; Gil Farmer [400400].
- MR 3: Gil Farmer on Stagger [1386].
- MR 5: Mug [400270]; Gil Toss [400250].
- MR 9: Misfortune [400750]; Double Gil [1050].

### Nalu — 5

Lightning physical, criticals and analysis.

Sprite `100015405` (GL); stat/MR budget: Cloud. Growth: Cloud.

- Awakening 1: Thunder Surge [421130]; Libra [210220]; Broadsword Mastery [1420].
- Awakening 2: Braver [446000]; Thundara Surge [421140]; Lightning Strike [447500].
- Awakening 3: Cross-Slash [446010]; Thundaga Surge [421150]; Thunderfall [447510].
- Awakening 4: Signature Moves [1418].
- MR 5: Scan and Strike [1399]; Bonus Phase Stagger Boost [1400].
- MR 7: Restore MP on Attack [1124].
- MR 9: Lightning Eater [1347].

### Elza — 5

Dark/water physical and sustained pressure.

Sprite `302000605` (GL); stat/MR budget: Tidus. Growth: Cloud.

- Awakening 1: Dark Surge [422050]; Spiral Cut [447000]; Slice & Dice - Water [421220]; Skyward Dreams [1434].
- Awakening 2: Darkra Surge [422060]; Slice & Dice - Water II [421230]; Speed +20% [1317].
- Awakening 3: Darkga Surge [422070]; Energy Rain [447010]; Spiral Cut+ [447020]; Slice & Dice - Water III [421240].
- MR 7: Tip-Top Shape [1428]; LB Shield [1403]; Essence of Mundanity [1389].
- MR 9: Dark Eater [1350].

### Lunera — 6

Wind physical and stagger support.

Sprite `100007506` (GL); stat/MR budget: Bartz. Growth: Cloud.

- Awakening 1: Aero Blade [420130]; Guiding Wind [1458].
- Awakening 2: Aerora Blade [420140]; Crushing Blade [445500]; Torrential Hew [414400].
- Awakening 3: Aeroga Blade [420150]; Wind Cutter Blade [445510]; Aquatic Synergy [414410].
- Awakening 4: Alluvial Edge [1448]; Alluvial Flourish [1449].
- MR 3: HP Stroll [1066]; Spry Steps [1258].
- MR 9: Drop Rate Up [1341].

## Research and validation limits

Selected hosted packs were checked against their published SHA-256 values, including base packs for shifted forms. Unit records, selected-form sprite motions and LB profiles were inspected. FFBE themes are references, not imported combat numbers. The archived Global datamine is `aEnigmatic/ffbe` at `95727376e82d27acc1290b6dc8ad27ce3c89ea71`; hosted merged records also cover Japanese and post-archive forms. Reberta’s Japanese hosted record has no translated skill list; her requested physical dragoon role and the original Reberta elemental/jump theme guide that kit.

Automated checks cover portable configs, unique allocation, native stat/MR budgets, mastery caps, owner-condition rebinding, native table patch serialization, and optional-pack lifecycle. They do not establish live-game balance or prove every animation exists in the demo. The existing unverified-skill visibility/animation toggles continue to govern demo animation repairs.

## Full-game release review

Re-audit native stats, level curves, skill mechanics and unlock ranks; private command/LB conditions and IDs; summon availability; selected form/LB presentation; and vendor/acquisition availability. Preserve user edits and require an explicit reset to apply revised recipes. See README’s running full-release checklist.
