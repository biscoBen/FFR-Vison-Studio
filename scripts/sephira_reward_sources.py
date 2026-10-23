"""Replace kept visions' learned MR rewards with audited equipment/enemy sources.

Run after MR scheduling, before publishing a catalog. Both awakening and MR are
checked by native source ID, so cloning or moving a protected reward cannot hide it.
"""
import copy

from sephira_kit_expansion import skill

# (old kind, native source) -> native passive or bounded private active recipe.
# Passive donors below belong to equipment or enemies, rather than kept visions' MR.
PASSIVES = {
    400790: 1274, 1393: 1551, 1397: 1552, 1326: 1510, 1396: 1517, 1445: 1535,
    1344: 1522, 1395: 1530, 1402: 1513, 1437: 1507,
    1401: 1527, 1282: 1519, 1000: 1498, 1047: 1373,
    1480: 1481, 1330: 1531, 1004: 1511, 1334: 1529,
    1394: 1516, 1438: 1497, 1340: 1539, 1430: 1532,
    1391: 1515, 1392: 1499, 1464: 1518, 1310: 1521,
    1370: 1525, 1332: 1500, 1044: 1009, 1347: 1523,
    1400: 1537, 1404: 1496, 1350: 1528, 1383: 1495,
    1389: 1506, 1403: 1276, 1341: 1051,
}
ACTIVES = {
    ('ActiveSkill', 400500): skill(500890, 'Numbing Slash', 10),
    ('ActiveSkill', 400740): skill(506110, 'Crystal Renewal', 50, magnification=400, defaultTargetRelation='Friendlies'),
    ('ActiveSkill', 400450): skill(500050, 'Focused Arrow', 8, magnification=18),
    ('ActiveSkill', 400680): skill(571450, 'Tidal Invocation', 36, magnification=30, hitCount=4),
    ('ActiveSkill', 400360): skill(250150, 'Waterga Surge', 30, TargetType='Group'),
    ('ActiveSkill', 400350): skill(501300, 'Frost Dance', 24, element='Ice', TargetType='Single', hitCount=4, magnification=28),
    ('ActiveSkill', 400210): skill(500130, 'Dragoon Cleave', 16, magnification=22),
    ('ActiveSkill', 400550): skill(250130, 'Waterdrop', 6, element='Water'),
    ('ActiveSkill', 400280): skill(503690, 'Mana Lance', 12, magnification=10),
    ('ActiveSkill', 400540): skill(503770, 'Dazzling Refrain', 30),
    ('ActiveSkill', 400660): skill(255000, 'Blazing Saber', 14, DamageType='Physic', damageCalcType='Physic', magnification=18),
    ('ActiveSkill', 400720): skill(250110, 'Storm Canvas', 30),
    ('PassiveSkill', 1356): skill(503970, 'Aether Current', 8),
    ('PassiveSkill', 1305): skill(570620, 'Soothing Current', 14, TargetType='Single', defaultTargetRelation='Friendlies'),
    ('PassiveSkill', 1328): skill(570630, 'Aether Palette', 18, magnification=30, TargetType='Single', defaultTargetRelation='Friendlies'),
}

# Checked against native effect rows, including cases whose Japanese placeholder
# descriptions disagree with their actual mechanics. These labels affect private
# Sephira copies; the original equipment and its parameters stay unchanged.
LABELS = {
    1274: ('Physical Defense +30%', 'Reduce physical damage taken by 30%.'),
    1551: ('Magic Evasion +15%', 'Evade magic attacks with a 15% chance.'),
    1552: ('LB Charge on Action', 'Fill the LB gauge by 10% at the start of each action.'),
    1510: ('Lingering Debuffs', 'Increase the duration of inflicted ailments and debuffs by 2 turns.'),
    1517: ('Healthy Focus', 'Increase damage and stagger power by 8% while HP is at least 75%.'),
    1535: ('Water Damage +30%', 'Increase water damage by 30%.'),
    1522: ('Imbue Ice', 'Add ice to non-elemental standard attacks and battle skills.'),
    1530: ('Magic Evasion +20%', 'Evade magic attacks with a 20% chance.'),
    1513: ('Damage Reduction +20%', 'Reduce physical and magic damage taken by 20%.'),
    1507: ('Opening Honed Senses', 'Begin battle with Honed Senses for 5 turns.'),
    1527: ('Imbue Light', 'Add light to non-elemental standard attacks and battle skills.'),
    1519: ('Steady Focus', 'Increase damage and stagger power by 8% while HP is at least 25%.'),
    1498: ('Peaceful LB Engine', 'Fill the LB gauge by 10% when acting without dealing damage.'),
    1373: ('Weakness Stagger +40%', 'Increase stagger power by 40% when exploiting an elemental weakness.'),
    1481: ('Critical Rate +30%', 'Increase critical hit rate by 30%.'),
    1531: ('Physical Evasion +15%', 'Evade physical attacks with a 15% chance.'),
    1511: ('Opening Good Luck', 'Begin battle with 8 stacks of Good Luck.'),
    1529: ('Physical Evasion +20%', 'Evade physical attacks with a 20% chance.'),
    1516: ('Full-HP Focus', 'Increase damage and stagger power by 8% while HP is full.'),
    1497: ('Critical Stagger +30%', 'Increase stagger power by 30% on critical hits.'),
    1539: ('Critical Focus', 'Increase critical damage and stagger power by 15%.'),
    1532: ('Fire Damage +20%', 'Increase fire damage by 20%.'),
    1515: ('Opening Sage Eye', 'Increase elemental-weakness stagger power by 50% for the first 4 turns.'),
    1499: ('Growing Good Luck', 'Gain 1 stack of Good Luck when acting.'),
    1518: ('Resilient Focus', 'Increase damage and stagger power by 8% while HP is at least 50%.'),
    1521: ('Imbue Fire', 'Add fire to non-elemental standard attacks and battle skills.'),
    1525: ('Imbue Wind', 'Add wind to non-elemental standard attacks and battle skills.'),
    1500: ('Damage +30%', 'Increase damage dealt by 30%.'),
    1009: ('Double EXP', 'Double EXP gained.'),
    1523: ('Imbue Lightning', 'Add lightning to non-elemental standard attacks and battle skills.'),
    1537: ('Lightning Damage +30%', 'Increase lightning damage by 30%.'),
    1496: ('Critical Damage +30%', 'Increase critical damage by 30%.'),
    1528: ('Imbue Dark', 'Add dark to non-elemental standard attacks and battle skills.'),
    1495: ('Damage +20%', 'Increase damage dealt by 20%.'),
    1506: ('Critical Rate +50%', 'Increase critical hit rate by 50%.'),
    1276: ('Magic Defense +30%', 'Reduce magic damage taken by 30%.'),
    1051: ('Double MRP', 'Double MRP gained.'),
    1524: ('Imbue Water', 'Add water to non-elemental standard attacks and battle skills.'),
    1526: ('Imbue Earth', 'Add earth to non-elemental standard attacks and battle skills.'),
}


# Display names checked against the supplied English equipment localization.
EQUIPMENT_NAMES = {1009: 'Adept’s Armlet',
 1051: 'Mastery Pendant',
 1276: 'Malice Breaker',
 1373: 'Pilebunker',
 1481: 'Sniper’s Eye',
 1495: 'Tatenashi Armor+',
 1496: 'Thor’s Hammer',
 1497: 'Thor’s Hammer',
 1498: 'Last Resort',
 1499: 'Arcturus',
 1500: 'Lorica Apocalyptica',
 1506: 'Genji Gloves',
 1507: 'Shisui',
 1510: 'Abyss',
 1511: 'Caelum Renatum',
 1513: 'Save the Vermillion',
 1515: 'Roselia',
 1516: 'Ultima Reactor',
 1517: 'Ultima Reactor',
 1518: 'Ultima Reactor',
 1519: 'Ultima Reactor',
 1521: 'Solar Pendant',
 1522: 'Icebrand / Snow Spirit’s Scarf',
 1523: 'Shock Whip / Thunder God’s Earrings',
 1525: 'Sylph’s Tiara',
 1527: 'Lightbringer / Halo Ring',
 1528: 'Demon’s Ring',
 1529: 'Sasuke’s Blade / Precognizant Beads',
 1530: 'Wizard’s Rod / Zephyr Cloak',
 1531: 'Ninja Gear / Mirage Jacket',
 1532: 'Flametongue',
 1535: 'R’lyeh Text',
 1537: 'Mjollnir',
 1539: 'Genji Armor',
 1551: 'Masamune / Mirage Robe',
 1552: 'Arcturus'}


def protected_rewards(mastery, excluded):
    result = {}
    for row in mastery.values():
        if row['ID'] in excluded:
            continue
        for grant in row['detailData']:
            kind = grant['parameterType'].split('::')[-1]
            if kind in ('ActiveSkill', 'PassiveSkill'):
                result.setdefault((kind, grant['params'][0]), []).append(
                    {'vision': row['ID'], 'rank': row['Level']})
    return result


def revise(catalog, rows, english, player_recipe):
    """Idempotent revision, using only native equipment or enemy skill donors."""
    native = {v['ID']: v for v in rows('Skill/DT_SkillData').values()}
    names = {v['id']: v for v in english['skills']}
    effects = {v['id']: v for v in english['effects']}
    equipment = {}
    for name, row in rows('Item/DT_EquipmentItemData').items():
        for identity in row['passiveList']:
            if identity != -1:
                equipment.setdefault(identity, []).append({'id': row['ID'], 'name': name})
    enemies = {}
    for name, row in rows('Unit/DT_UnitParameter').items():
        for identity in row.get('passiveSkillList', []):
            if row['ID'] < 13000 and identity != -1:
                enemies.setdefault(identity, []).append({'id': row['ID'], 'name': name})
    excluded = {int(v) for v in catalog['excludedVisionIds']}
    protected = protected_rewards(rows('Item/Vision/DT_VisionSynchroMasteryData'), excluded)
    replacements = []
    used = set()
    for preset in catalog['presets']:
        unit = preset['profile']
        for field in ('awakening', 'synchro'):
            for tier in unit[field]:
                for kind, identity, *_ in tier:
                    source = unit['skills'].get(str(identity), {}).get('from', identity) if kind == 'ActiveSkill' else identity
                    if (kind, source) not in protected:
                        used.add((kind, source))
    for preset in catalog['presets']:
        unit = preset['profile']
        if unit.get('sephiraRecipe', 0) >= 5:
            replacements.extend(preset.get('rewardReplacements', []))
            continue
        changed = []
        for field in ('awakening', 'synchro'):
            for rank, tier in enumerate(unit[field]):
                for index, grant in enumerate(tier):
                    kind, identity = grant[:2]
                    source = unit['skills'].get(str(identity), {}).get('from', identity) if kind == 'ActiveSkill' else identity
                    if (kind, source) not in protected:
                        continue
                    entry = {'preset': preset['id'], 'field': field, 'rank': rank,
                             'oldKind': kind, 'oldId': identity, 'oldSource': source,
                             'protectedOwners': protected[kind, source]}
                    if source in PASSIVES:
                        target = PASSIVES[source]
                        if target not in equipment and target not in enemies:
                            raise ValueError(f'No equipment/enemy source for passive {target}')
                        replacement = ['PassiveSkill', target, -1]
                        entry.update(source=target, equipment=equipment.get(target, []), enemies=enemies.get(target, []))
                        label, desc = LABELS[target]
                        unit.setdefault('sephiraPassiveText', {})[str(target)] = {'name': label, 'desc': desc}
                    else:
                        spec = copy.deepcopy(ACTIVES[kind, source])
                        base = 445000 + (unit['id']-13100)*100
                        occupied = {int(k)+o for k in unit['skills'] for o in (0, 1, 2)}
                        slot = next(n for n in range(1, 32) if not occupied.intersection({base+n*3+o for o in (0, 1, 2)}))
                        target, audit = player_recipe(unit, slot, spec, native, names, effects)
                        audit['unlock'] = [field, rank]
                        preset['balance']['playerCopies'].append(audit)
                        replacement = ['ActiveSkill', target, -1]
                        entry.update(source=spec[0])
                    new_source = entry['source']
                    if (replacement[0], new_source) in used: raise ValueError(f'Duplicate replacement source {new_source}')
                    if (replacement[0], new_source) in protected: raise ValueError(f'Protected replacement source {new_source}')
                    used.add((replacement[0], new_source))
                    tier[index] = replacement
                    entry['newGrant'] = replacement
                    changed.append(entry)
                    if kind == 'ActiveSkill' and str(identity) in unit['skills']:
                        del unit['skills'][str(identity)]
                        preset['balance']['playerCopies'] = [x for x in preset['balance']['playerCopies'] if x['id'] != identity]
        preset['rewardReplacements'] = changed
        replaced_passives = {r['oldSource']: r for r in changed if r['oldKind'] == 'PassiveSkill'}
        preset['balance']['additionalPassives'] = [
            replaced_passives[s]['newGrant'][1] if s in replaced_passives else s
            for s in preset['balance']['additionalPassives']
            if s not in replaced_passives or replaced_passives[s]['newGrant'][0] == 'PassiveSkill']
        unit['sephiraRecipe'] = 5
        for field, prefix in (('awakening', ''), ('synchro', 'mr')):
            for kind, suffix in (('ActiveSkill', 'ActiveCount'), ('PassiveSkill', 'PassiveCount')):
                key = prefix+suffix if prefix else suffix[0].lower()+suffix[1:]
                preset['balance'][key] = sum(g[0] == kind for tier in unit[field] for g in tier)
        replacements.extend(changed)
    catalog['protectedMrRewards'] = [dict(kind=kind, source=identity, owners=owners)
        for (kind, identity), owners in sorted(protected.items())]
    for preset in catalog['presets']:
        unit = preset['profile']
        for field in ('awakening', 'synchro'):
            for tier in unit[field]:
                for kind, identity, *_ in tier:
                    source = unit['skills'].get(str(identity), {}).get('from', identity) if kind == 'ActiveSkill' else identity
                    if (kind, source) in protected:
                        raise ValueError(f"{preset['id']}: kept vision MR reward {kind} {source}")
        if any(('ActiveSkill', recipe['from']) in protected for recipe in unit['skills'].values()):
            raise ValueError(f"{preset['id']}: protected MR source in a private recipe")
    return replacements


def describe_changes(catalog, english):
    """Human-readable audit; precise table IDs remain in the bundled catalog."""
    from pathlib import Path
    skills = {s['id']: s['name'] for s in english['skills']}
    passives = {s['id']: s['name'] for s in english['passives']}
    visions = {s['id']: s['name'] for s in english['visions']}
    lines = ['# Sephira reward source correction', '',
        'Historical revision-5 source audit. Revision 6 subsequently curates these bonuses into five passives per vision; some extras below are intentionally removed. See [the current passive allocation](SEPHIRA_PASSIVE_MASTERY.md). Active recipes and the protected-source exclusions are retained.', '',
        'Recipe revision 5 replaces 52 rewards from the original visions you are keeping: 44 MR grants and eight awakening grants. The replacement keeps each grant in its existing rank. All 291 grants from the 15 excluded originals remain available, alongside the existing awakening quotas, five learned MR rewards, permanent stats and challenge budgets.', '',
        'The protected pool includes all 55 learned MR rewards from Amelia, Victoria, Camille, Leah, Ayaka, Charlotte, Aileen, Terra, Lightning, Y’shtola and Sephiroth. No active copy or passive grant in the presets uses one of those sources.', '',
        'Replacements use 36 equipment bonuses, one enemy defense bonus and 15 bounded enemy skills. Bonus effects retain native parameters and conditions; private copies supply English text and a 20-AP minimum for formerly zero-cost equipment bonuses. Active copies retain the player limits and native visual-mode controls. These are starting balance values; live testing remains necessary.', '',
        'Apply **MR and acquisition update**, then rebuild/install. The migration backs up the roster and preserves unrelated edits and saved revision-4 acquisition choices. It also handles reassigned IDs and occupied custom-skill slots.', '',
        '| Vision | Rank | Removed reward | Kept original | Replacement | Other source |',
        '|---|---|---|---|---|---|']
    for preset in catalog['presets']:
        unit = preset['profile']
        for r in preset['rewardReplacements']:
            old = (skills if r['oldKind']=='ActiveSkill' else passives)[r['oldSource']]
            owner = ', '.join(visions[o['vision']] for o in r['protectedOwners'])
            if r['newGrant'][0]=='PassiveSkill':
                name = LABELS[r['source']][0]
                source = EQUIPMENT_NAMES[r['source']] if r['equipment'] else 'Liquid Thunder / Dabih minion defense'
                source += f" (bonus {r['source']})"
            else:
                recipe = unit['skills'][str(r['newGrant'][1])]
                name = recipe['en']
                source = 'Enemy ' + skills[r['source']] + f" ({r['source']})"
            rank = 'MR ' + str(r['rank']) if r['field']=='synchro' else 'Awakening ' + str(r['rank']+1)
            lines.append(f"| {preset['name']} | {rank} | {old} | {owner} | {name} | {source} |")
    Path(__file__).resolve().parents[1].joinpath('docs/SEPHIRA_REWARD_CHANGES.md').write_text('\n'.join(lines)+'\n')
