"""Optional vision challenges: private enemies, native choices, victory-only grants.

The saved Acquisition choice is authoritative. Disabled/deleted/moved visions
never spawn a challenge enemy or receive an acquisition reward.
"""
import copy
import json
from pathlib import Path
import math

DATA = 'sephira_challenges.json'
PREFIX = 'Studio_SephiraChallenge_'
EVENT = 'Event/TalkEvent/LegendEvent/DT_TalkEventData_LegendEvent'
COMPOSITE = 'Event/TalkEvent/CDT_TalkEventData_Demo'
UNIT = 'Unit/DT_UnitParameter'
AI = 'Unit/AI/DT_BtlUnitAIParameter'
ASSET = 'Asset/Battle/Unit/DT_BtlUnitAsset'
DESIGN = 'Battle/Unit/DT_BtlUnitDesignParameter'
GROUP = 'Encount/DT_BattleGroup'
SKILL = 'Skill/DT_SkillData'
CHOICES = 'UI/Common/Dialog/DT_DIalogChoice'
STAGE = 'Asset/Battle/Stage/DT_BtlStageAsset'
STAGE_COMPOSITE = 'Asset/Battle/Stage/CDT_BtlStageAsset_Demo'
AI_ASSETS = ('Asset/Battle/AI/DT_BtlUnitAIAsset', 'Asset/Battle/AI/DT_CompositeBtlUnitAIAsset')
SEQUENCE = 'Sequencer/Event/StudioSephira/'

# Story/dungeon boss anchors. Exclude scripted unwinnable fights, boss parts,
# superbosses and the low-stat actor used by the emperor's cutscene.
CURVE_DONORS = [401, 447, 409, 459, 411, 426, 452, 428, 421, 443, 420, 458]
PARAMETERS = ['MaxHitPoint', 'MaxMagicPoint', 'MaxBreakPoint', 'Attack',
              'Defence', 'Intelligence', 'Mind', 'Agility']


def data():
    value = json.loads(Path(__file__).with_name(DATA).read_bytes())
    if value.get('schema') != 1: raise ValueError('Unsupported Sephira challenge catalog.')
    return value


def route(unit):
    value = unit.get('studioAcquisition') or {}
    if value.get('version') != 3: return None
    import _ffr_sephira
    member = _ffr_sephira.membership(unit)
    if (member is None or not member['enabled'] or member['preset'] in _ffr_sephira.RETIRED
            or set(value) != {'version', 'location', 'random', 'hideSpoilers', 'cave'}
            or value['random'] is not False or type(value['hideSpoilers']) is not bool or value['cave'] is not None):
        raise ValueError('Invalid Sephira challenge acquisition. Reapply the MR and acquisition update.')
    location = value['location']
    if location == 'sephira_folka_shop':
        if member['preset'] != 'folka': raise ValueError('The story shop belongs to Folka.')
        return 'folka_shop'
    origins = {str(v['origin']) for v in data()['encounters']}
    if not isinstance(location, str) or location.removeprefix('sephira_') not in origins:
        raise ValueError('Unknown Sephira challenge crystal.')
    return int(location.removeprefix('sephira_'))


def plans(units):
    chosen = {}
    for unit in units:
        origin = route(unit)
        if origin is None or origin == 'folka_shop': continue
        chosen.setdefault(origin, []).append(unit)
    result = []
    for spec in data()['encounters']:
        members = chosen.get(spec['origin'], [])
        if not members: continue
        ids = [u['id'] for u in members]
        if len(ids) != len(set(ids)) or len(members) > 3:
            raise ValueError('A Sephira challenge needs one to three distinct visions.')
        result.append((spec, sorted(members, key=lambda u: u['id'])))
    return result


def cave_snapshot():
    return copy.deepcopy(data()['wilhelmCave'])


def boss_id(unit):
    # Allocated vision identity, not list order or localized name.
    return 28000 + unit['id'] - 13500


def skill_base(unit): return 800000 + (unit['id'] - 13500) * 1000


def curve(rows, level):
    """Interpolate native boss curves around the approved level-10 Fina test."""
    if type(level) is not int or not 1 <= level <= 60:
        raise ValueError('Sephira challenge level is outside the reviewed native curve.')
    import _ffr_fina_boss as fina
    native = {v['ID']: v for v in rows(UNIT).values()}
    anchors = {10: dict(fina.STATS)}
    for identity in CURVE_DONORS:
        row = native.get(identity)
        if not row or row.get('Category') != 'Boss': raise ValueError('Missing native boss curve anchor: ' + str(identity))
        anchors[row['Level']] = {k: row[k] for k in PARAMETERS}
    levels = sorted(anchors)
    # Native encounters vary in composition. Preserve an increasing single-boss
    # budget instead of inheriting a later scripted boss's unusually low stat.
    for previous, current in zip(levels, levels[1:]):
        for key in PARAMETERS: anchors[current][key] = max(anchors[current][key], anchors[previous][key])
    if level < levels[0]:
        return {k: max(1, round(anchors[levels[0]][k] * level / levels[0])) for k in PARAMETERS}
    lower = max(v for v in levels if v <= level)
    upper = min((v for v in levels if v >= level), default=levels[-1])
    if lower == upper: return {k: anchors[lower][k] for k in PARAMETERS}
    ratio = (level - lower) / (upper - lower)
    return {k: round(anchors[lower][k] + ratio * (anchors[upper][k] - anchors[lower][k])) for k in PARAMETERS}


def team_stats(rows, level, units):
    total = curve(rows, level)
    weights = [1.15 if any('Defender' in r for r in u['roles']) else
               .85 if any('Healer' in r for r in u['roles']) else 1.0 for u in units]
    budgets = []
    for i, (unit, weight) in enumerate(zip(units, weights)):
        row = dict(total)
        # Divide durability and per-action damage across the whole opposing team.
        row['MaxHitPoint'] = round(total['MaxHitPoint'] * weight / sum(weights))
        row['MaxBreakPoint'] = max(60, round(total['MaxBreakPoint'] * weight / sum(weights)))
        row.update(Level=level, LevelParamId=-1)
        # Keep the established shared durability budget. Hybrid kits need both
        # offensive stats; the same 15% speed adjustment applies to each role.
        for field in ('Attack', 'Intelligence'): row[field] = round(total[field] * 1.5)
        row['Agility'] = round(total['Agility'] * 1.15)
        budgets.append(row)
    budgets[-1]['MaxHitPoint'] += total['MaxHitPoint'] - sum(r['MaxHitPoint'] for r in budgets)
    return budgets


def kit(unit, rows, team_size):
    """All learned active skills are private, bounded enemy copies.

    Unsafe player-only actions (Mimic, doublecast, summons, gil/item commands,
    revival) remain learned on the player vision but are not selected by AI.
    """
    native = {v['ID']: (k, v) for k, v in rows(SKILL).items()}
    chosen = []
    for field in ('awakening', 'synchro'):
        chosen.extend(g[1] for tier in unit[field] for g in tier if g[0] == 'ActiveSkill')
    result = []
    settings = data()['kits'][unit['sephiraVision']['preset']]
    basic = settings.get('basic', 500010)
    for index, identity in enumerate([0, *dict.fromkeys(chosen)]):
        recipe = (unit.get('skills') or {}).get(identity, (unit.get('skills') or {}).get(str(identity), {}))
        source = recipe.get('from', identity) if identity else basic
        if source not in native: raise ValueError('Missing vision boss skill source: ' + str(source))
        key, original = native[source]
        import _ffr_testing as testing
        row = testing.apply_fields(original, recipe.get('set', {}))
        enemy_id = skill_base(unit) + index * 10
        if enemy_id in native: raise ValueError('Sephira enemy skill identity is occupied.')
        row.update(ID=enemy_id, SortId=enemy_id, Cost=0, hasUnit='All', belongCommandList=[912],
                   commandIdBelongDebuggingAllSkills=[912, -1], skillIdAfterModeChange=-1,
                   isApplyAllMag=False, playSequencerId=-1, sequencerIdWhenTargetFriendlies=-1,
                   voiceLabel='None', selfSkillActivateVoiceLabel='None', isRemovable=False)
        if recipe.get('en'): row['Name'] = recipe['en']
        if identity == 0 and basic == 500010: row.update(Name='Attack', element='None', magnification=12)
        elif identity == 0 and settings.get('basicName'): row['Name'] = settings['basicName']
        healing = row['parameterVariationType'] == 'Increase' and row['parameterType'] == 'HitPoint'
        damaging = row['parameterVariationType'] == 'Decrease' and row['DamageType'] in ('Magic', 'Physic')
        if healing:
            # A threshold-gated self heal is bounded to 15% of this boss's share.
            row.update(TargetType='Self', defaultTargetRelation='Friendlies', damageCalcType='TargetMaxHPRatio', magnification=15)
        elif damaging:
            if row['damageCalcType'] not in ('Physic', 'Magic', 'MPAbsorb'):
                row['damageCalcType'] = 'Physic' if row['DamageType'] == 'Physic' else 'Magic'
            cap = 40 if row['TargetType'] in ('Group', 'All', 'SingleAndGroup') else 60
            multiplier = 1.75 if source == settings['attacks'][-1] else 1.5
            row['magnification'] = max(1, round(min(row['magnification'], cap) * multiplier / team_size))
            row['magnification'] = max(1, round(row['magnification'] * settings.get('potencyMultipliers', {}).get(str(source), data().get('potencyScale', 1))))
        import _ffr_testing as testing
        result.append({'id': enemy_id, 'learned': identity, 'source': source, 'clone': key,
                       'name': PREFIX + str(unit['id']) + '_Skill_' + str(index),
                       'fields': testing.field_delta(original, row), 'visuals': recipe.get('visuals', source),
                       'healing': healing, 'damaging': damaging})
    return result


def rotation(unit, recipes, index):
    spec = data()['kits'][unit['sephiraVision']['preset']]
    by_source = {r['source']: r for r in recipes}
    attack = recipes[0]
    def find(identity):
        return by_source.get(identity) or attack
    first, second, special = [find(v) for v in spec['attacks']]
    utility = find(spec.get('utility', 0))
    # Stagger the partners' signatures rather than bursting on the same turn.
    actions = [attack, first, utility, attack, second, attack, first, special]
    offset = (index * 3) % len(actions)
    actions = actions[offset:] + actions[:offset]
    return actions


def casual_actions(unit, recipes, index):
    """The game's simpler AI must have the same bounded offensive choices.

    Exclude heals: their scripted low-HP guard does not run in this path. The
    native Probability entries are independent weights, not cumulative limits.
    """
    actions = [r for r in rotation(unit, recipes, index) if not r['healing']]
    counts = {r['id']: sum(a['id'] == r['id'] for a in actions) for r in actions}
    # Integer percentages round-trip exactly through the native float32 table;
    # repeating fractions would fail the build's strict native readback check.
    choices = [{'SkillId': identity, 'Probability': float(round(count * 100 / len(actions)))}
               for identity, count in counts.items()]
    choices[0]['Probability'] += 100 - sum(c['Probability'] for c in choices)
    return choices


def _source(rows, rel, identity):
    matches = [(k, v) for k, v in rows(rel).items() if v.get('ID') == identity]
    if len(matches) != 1: raise ValueError(f'Sephira challenge needs native {rel} ID {identity}.')
    return matches[0]


def _add(table, rows, rel, identity, donor, name, fields):
    if name in rows(rel) or any(v.get('ID') == identity for v in rows(rel).values()) or any(
            e['row'] == name or e['set'].get('ID') == identity for e in table(rel)['add']):
        raise ValueError('Sephira challenge identity is occupied: ' + rel + '/' + str(identity))
    key, _ = _source(rows, rel, donor)
    table(rel)['add'].append({'row': name, 'cloneFrom': key, 'set': {'ID': identity, **fields}})


def prepare_enemies(table, rows, spec, units):
    _, donor = _source(rows, UNIT, 401)
    for index, (unit, stats) in enumerate(zip(units, team_stats(rows, spec['level'], units))):
        identity, name = boss_id(unit), PREFIX + str(unit['id'])
        resistances = {k: 'eResistance::None' for k in donor['ElementResistanceList']}
        for element, resistance in data()['kits'][unit['sephiraVision']['preset']].get('resistances', {}).items():
            key = 'eElement::' + element
            if key not in resistances or resistance not in ('Halved', 'Weakness'):
                raise ValueError('Unsupported challenge resistance: ' + element)
            resistances[key] = 'eResistance::' + resistance
        _add(table, rows, UNIT, identity, 401, name, {**stats,
            'Name': unit['en'], 'Description': 'Sephira crystal challenge',
            'SortId': identity, 'SaveId': identity, 'FaceIconId': unit['id'],
            'Category': 'Boss', 'Sex': 'Female', 'Race': 'Human', 'IsBoss': True, 'IsAccent': False,
            'HitPoint': 0, 'MagicPoint': stats['MaxMagicPoint'], 'Breakpoint': 0, 'LimitBurstPoint': 0,
            'ElementResistanceList': resistances,
            'passiveSkillList': [], 'WeaponId': -1, 'ArmorId': -1, 'AccessoryIdList': [], 'VisionId': -1,
            # Native boss rewards use a reciprocal rate: 1 is guaranteed.
            # 100 made the previous result-screen attempt a one-in-100 drop.
            'Experience': 0, 'Money': 0, 'DropNormalItem': unit['id'], 'DropNormalItemRate': 1,
            'DropRareItem': -1, 'DropRareItemRate': 0, 'StealNormalItem': -1, 'StealRareItem': -1,
            'StealItemRate': 0, 'BattleVoiceLabel': 'None'})
        base = f'/Game/Chara/summon/summon{unit["id"]}/summon{unit["id"]}'
        if str((unit.get('ffbe') or {}).get('id')) == '99887755552703':
            import _ffr_fina_battle as fina
            base = '/Game/' + fina.package(unit, 'FinaNative' + str(unit['id']))
        _add(table, rows, ASSET, identity, unit['donor'], name, {
            'animationAssetList[0].Ss6Project': base,
            'animationAssetList[0].textureBaseColor': base + '_tex',
            'animationAssetList[0].textureNormal': base + '_normal',
            'animationAssetList[0].textureMetallicRoughness': base + '_mreo',
            'animationAssetList[0].isVisionCharacter': False,
            'animationAssetList[0].Material': '/Game/BP/Map/Unit/Material/CharaPBR/M_Ss_Component_PBRBattle'})
        scale = float(_source(rows, DESIGN, unit['donor'])[1]['Scale'])
        _add(table, rows, DESIGN, identity, unit['donor'], name, {
            'Scale': round((scale if scale > 0 else 1) * 1.3, 6), 'attachEffectSacle': 1.0,
            'isSpecialDeadAnim': False, 'isFlipH': True})
        recipes = kit(unit, rows, len(units))
        for recipe in recipes:
            # Only fields present in the native schema, plus localized strings.
            table(SKILL)['add'].append({'row': recipe['name'], 'cloneFrom': recipe['clone'], 'set': recipe['fields']})
            for rel in ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo'):
                for offset in (0, 1, 2):
                    visual = recipe['visuals'] + offset
                    if any(v.get('ID') == visual for v in rows(rel).values()):
                        _add(table, rows, rel, recipe['id'] + offset, visual,
                             recipe['name'] + '_Visual_' + str(offset), {})
            rel = 'Battle/Sequencer/DT_BtlHitEffectData'
            variants = [(key, value) for key, value in rows(rel).items() if value.get('ID') == recipe['visuals']]
            if variants and (any(v.get('ID') == recipe['id'] for v in rows(rel).values())
                    or any(e['set'].get('ID') == recipe['id'] for e in table(rel)['add'])):
                raise ValueError('Challenge hit-effect identity is occupied.')
            for variant, (key, _) in enumerate(variants):
                table(rel)['add'].append({'row': recipe['name'] + '_Hit_' + str(variant),
                    'cloneFrom': key, 'set': {'ID': recipe['id']}})
        ids = [r['id'] for r in recipes]
        random_actions = casual_actions(unit, recipes, index)
        _add(table, rows, AI, identity, 401, name, {'aiId': identity, 'fightSkillId': ids[0],
            'silenceFightId': ids[0], 'chaseSkillId': -1, 'counterSkillIdList': [-1, -1],
            'highRiskSkillIdList': [-1, -1],
            'skillRandData1': random_actions,
            'skillRandData2': copy.deepcopy(random_actions)})
        for rel in AI_ASSETS:
            package = 'BP/Battle/AI/Studio/BP_' + name
            _add(table, rows, rel, identity, 401, name, {'UnitAIClass': '/Game/' + package + '.BP_' + name + '_C'})


def prepare(tables, units, root, rows):
    selected = plans(units)
    if not selected and not any(route(u) == 'folka_shop' for u in units): return
    source, cache = rows, {}
    def rows(rel):
        if rel not in cache: cache[rel] = source(rel)
        return cache[rel]
    def table(rel): return tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})
    for spec, members in selected:
        prepare_enemies(table, rows, spec, members)
        prepare_encounter(table, rows, spec, members, root, units)
    prepare_shop(table, rows, units)
    # The patcher clones from its current table. Retain populated native donors
    # until every private row is authored, then replace the repeat entry points.
    for rel, plan in tables.items():
        if rel in (EVENT, COMPOSITE):
            native = rows(rel)
            plan['add'].sort(key=lambda e: e['row'] in native)


def prepare_encounter(table, rows, spec, units, root, roster):
    # Authored after the native placement audit; no fallback to a guessed shrine.
    import _ffr_testing as testing
    name = PREFIX + str(spec['origin'])
    donor_key, donor = _source(rows, GROUP, 1026)
    if any(donor.get(k) for k in ('battleFinishEventId', 'battleFinishEscapeEventId', 'battleFinishLoseEventId')):
        raise ValueError('The story-free battle group donor changed.')
    group_id = 27500 + spec['index']
    _add(table, rows, GROUP, group_id, 1026, name, {
        'UnitIdList': [boss_id(u) for u in units], 'locationIdList': {1: [10], 2: [6, 15], 3: [20, 6, 15]}[len(units)],
        'CanEscape': True, 'probabilityOfSuccessfulEscape': 100.0,
        # Inherit all three verified empty finish-event names. The native patcher
        # cannot insert a new empty FString into an FName name map.
        'ap': 0, 'isResultSkipOnWin': False, 'isResultSkipOnLose': False})
    # Menus, ownership checks and return-to-field routing are authored from
    # the inspected original repeat events, never the original acquisition row.
    _events(table, rows, spec, units, group_id, root, roster)


def _events(table, rows, spec, units, group_id, root, roster):
    import _ffr_testing as testing
    import _ffr_crystal_cave as caves
    parent, composite = rows(EVENT), rows(COMPOSITE)
    grant = composite.get(spec['grantEvent'], {})
    if not any(i['ID'] == spec['origin'] and i['Num'] > 0 for i in grant.get('ObtainItemList', [])):
        raise ValueError('The original vision acquisition changed: ' + spec['name'])
    proof = spec['unlock'].split('|', 1)[1]
    completion = grant
    if spec.get('completionEvent'):
        if not any(e.get('Condition') == '' and e.get('EventId') == spec['completionEvent']
                   for e in grant.get('ContinuousEventList', [])):
            raise ValueError('The original vision completion chain changed: ' + spec['name'])
        completion = composite.get(spec['completionEvent'], {})
    if proof.startswith('{flag:'):
        valid = int(proof.removeprefix('{flag:').removesuffix('}')) in completion.get('OnFlagList', [])
    else:
        progress, value = proof.removeprefix('{progress:').split('}>=')
        valid = any(p['ID'] == int(progress) and p['Value'] == int(value) for p in completion.get('ProgressList', []))
    if not valid: raise ValueError('The original vision completion check changed: ' + spec['name'])
    name = PREFIX + str(spec['origin'])
    clean = testing.apply_fields(composite['C01_ArijigokuEncount'], {
        'Description': name, 'encountGroupId': -1, 'IsGetOffVehicle': False,
        'MapStartupSettings.ChangeBGM': 'NotChange',
        'RestoreSoundVolumeSettings.IsRevertValume': False,
        'TalkEventDataTable': 'None', 'EventSequence': 'None', 'EventBlueprint': 'None',
        'IsHiddenFieldUI': False, 'LoadingScreenSetting': 'None',
        'IsSetAutoSave': False, 'IsSetForceAutoSave': False,
        'OnFlagList': [], 'OffFlagList': [], 'ProgressList': [],
        'ContinuousEventList': [], 'ChoicesBranchEventList': [], 'ObtainItemList': []})
    donors = {'choice': 'Int_LegendEV_Retry_Start_01_01',
              'link': 'Int_LegendEV_01_06_VisionGet', 'grant': 'Int_LegendEV_01_07',
              'empty': 'Int_LegendEV_Retry_Cancel'}
    def event(key, fields, kind='empty', replace=False, destination=EVENT):
        donor = donors[kind]
        if replace:
            # Production shrine repeat rows must clone inside their own parent.
            donor = f'Int_LegendEV_{spec["legend"]:02d}_06_VisionGet'
        desired = testing.apply_fields(clean, fields)
        for rel in (destination, COMPOSITE):
            if key in rows(rel) and not replace: raise ValueError('Challenge event identity is occupied: ' + key)
            # A cave's acquisition row was already created by the cave builder.
            # Replace its free grant instead of retaining a second acquisition.
            table(rel)['add'][:] = [e for e in table(rel)['add'] if e['row'] != key]
            if destination != EVENT:
                # The donor belongs to the legend parent; insert in that parent
                # and the composite, then link the cave's existing row below.
                raise ValueError('Unexpected challenge event parent.')
            table(rel)['add'].append({'row': key, 'cloneFrom': donor,
                'set': testing.field_delta(parent[donor], desired)})
    # Each conditional is mutually exclusive. No quest flag is set by a
    # challenge: only the game's original grant can satisfy these gates.
    unlock = spec['unlock']
    locked = f'{{item:{spec["origin"]}}}==0&' + (
        proof.replace('>=', '<') if '>=' in proof else '!' + proof)
    missing = '|'.join(f'{{item:{u["id"]}}}==0' for u in units)
    complete = '&'.join(f'{{item:{u["id"]}}}>0' for u in units)
    def links(a, yes, b, no): return [{'Condition': a, 'EventId': yes}, {'Condition': b, 'EventId': no}]
    event(name, {'ContinuousEventList': links(unlock, name + '_Available', locked, name + '_Locked')}, 'link')
    event(name + '_Available', {'ContinuousEventList': links(missing, name + '_Menu', complete, name + '_Done')}, 'link')
    # Recheck the prerequisite immediately before entering battle.
    event(name + '_Start', {'ContinuousEventList': links(unlock, name + '_Fight', locked, name + '_Locked')}, 'link')
    event(name + '_Fight', {'encountGroupId': group_id})
    event(name + '_Close', {})
    choice_key = next(k for k, v in rows(CHOICES).items() if v.get('ChoiceTextList'))
    replay = spec.get('retry')
    memory = replay[:-2] + '02' if replay else None
    def menu(suffix, labels, targets):
        key = name + suffix
        if key in rows(CHOICES): raise ValueError('Challenge dialog identity is occupied.')
        table(CHOICES)['add'].append({'row': key, 'cloneFrom': choice_key, 'set': {
            'ChoiceTag.TagName': 'UI.Dialog.Choice.' + key, 'ChoiceTextList': labels,
            'DefaultIndex': 0, 'CancelIndex': len(labels)-1, 'ChoiceDialogType': 'Normal'}})
        event(key, {'EventSequence': '/Game/' + SEQUENCE + 'SEQ_' + key,
            'ChoicesBranchEventList': [{'Index': i, 'EventList': [{'Condition': '', 'EventId': t}]}
                                       for i, t in enumerate(targets)]}, 'choice')
    labels = ['Challenge ' + ' & '.join(u['en'] for u in units) + f' (level {spec["level"]})']
    targets = [name + '_Start']
    if memory: labels.append('Recall ' + spec['name']); targets.append(memory)
    menu('_Menu', labels + ['Leave'], targets + [name + '_Close'])
    menu('_Locked', ['Obtain ' + spec['name'] + ' first', 'Leave'], [name + '_Close'] * 2)
    labels, targets = ['These visions have already joined you'], [name + '_Close']
    if memory: labels.append('Recall ' + spec['name']); targets.append(memory)
    menu('_Done', labels + ['Leave'], targets + [name + '_Close'])
    if replay:
        if replay not in parent or parent[replay] != composite[replay]:
            raise ValueError('The original shrine repeat event changed: ' + replay)
        event(replay, {'ContinuousEventList': links(unlock, name + '_Available', locked, name + '_Locked')}, 'link', replace=True)
    if spec['origin'] == 13062:
        cave_plans, _ = caves.cave_plans(roster, root, rows)
        for entries in cave_plans:
            for unit, cave in entries:
                if route(unit) != 13062: continue
                # Keep the tested interaction lifecycle, remove its free reward
                # and transition, and delegate to the guarded challenge.
                for rel in (testing.EVENT, COMPOSITE):
                    original = next(e for e in table(rel)['add'] if e['row'] == cave.event)
                    desired = testing.apply_fields(clean, {'ContinuousEventList': [{'Condition': '', 'EventId': name}]})
                    link = 'C01_014_03'
                    original.update(cloneFrom=link, set=testing.field_delta(rows(rel)[link], desired))
        map_rel, map_row = caves.MAP, cave.name
    else:
        map_rel, map_row = spec['mapTable'], spec['mapRow']
    stage_id = group_id
    for rel in (STAGE, STAGE_COMPOSITE):
        _add(table, rows, rel, stage_id, spec['stage'], name, {'isLoadLevelInstance': True})
    for rel in (map_rel, caves.COMPOSITE):
        # Mitra's practice mode already supplies a private instance-loaded
        # stage. Keep it so Christine and the existing vendor tests coexist.
        if spec.get('crystalInteraction') and map_row == '01Gra_20' and any(
                e['row'] == map_row and 'battleStage' in e['set'] for e in table(rel)['set']):
            continue
        additions = [e for e in table(rel)['add'] if e['row'] == map_row]
        if additions: additions[0]['set']['battleStage'] = stage_id
        else: table(rel)['set'].append({'row': map_row, 'set': {'battleStage': stage_id}})


def prepare_shop(table, rows, units):
    chosen = [u for u in units if route(u) == 'folka_shop']
    if not chosen: return
    if len(chosen) != 1: raise ValueError('Folka needs one story-shop identity.')
    story = rows(COMPOSITE).get(data()['folkaEvent'], {})
    if not any(p['ID'] == 0 and p['Value'] == 3150 for p in story.get('ProgressList', [])):
        raise ValueError('The Olderion guardian story unlock changed; collect a new native reference.')
    unit, = chosen
    rel = 'Shop/DT_ShopList'
    matches = [(k, v) for k, v in rows(rel).items() if v['ShopID'] == 10]
    if len(matches) != 1: raise ValueError('The Olderion item shop is unavailable.')
    key, original = matches[0]
    import _ffr_testing as testing
    current = copy.deepcopy(original)
    for edit in table(rel)['set']:
        if edit['row'] == key: current = testing.apply_fields(current, edit['set'])
    items = copy.deepcopy(current['ItemList'])
    if any(i['ItemId'] == unit['id'] for i in items): raise ValueError('Folka is already in the native shop dump.')
    sources = {}
    for name in ('Consumables', 'Equipment', 'Artifact', 'Seed', 'Valuable'):
        for value in rows('Item/DT_' + name + 'ItemData').values(): sources[value['ID']] = value
    sources.update({u['id']: {'buyingPrice': u['price']} for u in units if type(u.get('price')) is int})
    prices = []
    for item in items:
        if item['ItemId'] == -1: continue
        source = sources.get(item['ItemId'])
        if source is None: raise ValueError('Cannot determine a native Olderion shop price: ' + str(item['ItemId']))
        prices.append(math.ceil(source['buyingPrice'] * item['PriceRatio']))
    price = max(prices, default=0) * 2
    if price <= 0: raise ValueError('The native Olderion price baseline is unavailable.')
    if unit['price'] <= 0: raise ValueError('Give Folka a positive base price before building her story shop.')
    import struct
    ratio = struct.unpack('<f', struct.pack('<f', price / unit['price']))[0]
    entry = dict(items[0], ItemId=unit['id'], Condition=data()['folkaUnlock'], MaxOrderNum=1, PriceRatio=ratio)
    empty = next((i for i, item in enumerate(items) if item['ItemId'] == -1), None)
    if empty is None: items.append(entry)
    else: items[empty] = entry
    table(rel)['set'][:] = [e for e in table(rel)['set'] if e['row'] != key]
    table(rel)['set'].append({'row': key, 'set': {'ItemList': items}})


def needs_enemy_motion(unit):
    origin = route(unit)
    return origin is not None and origin != 'folka_shop'


def enemy_motion_for(units, identity):
    import _ffr_sephira
    return any(str(u.get('id')) == str(identity) and needs_enemy_motion(u)
               for u in _ffr_sephira.active_units(units))


def final_rows(rel, expected, units, root):
    if rel not in AI_ASSETS: return expected
    expected = copy.deepcopy(expected)
    for _, members in plans(units):
        for unit in members:
            name = PREFIX + str(unit['id'])
            expected[name]['UnitAIClass'] = 'BP_' + name + '_C'
    return expected


_CHECKED_CRYSTALS = {}


def button_interaction(view, owner_id):
    """Convert only this repeat crystal to the native confirm-button class.

    The overlap class has three extra native fields; changing an interaction
    enum on that class still starts its event when the player enters the box.
    Keep its actor/component indices, event movement, conditions and placement.
    Append the new class/archetype imports so unrelated story actors retain
    their original references.
    """
    import _ffr_crystal_cave as caves
    old = 'BP_MapGimmick_EventTrigger'
    new = 'BP_MapGimmick_InteractEventTrigger'
    package = '/Game/BP/Map/Gimmick/' + old
    owner = view['Exports'][owner_id - 1]
    identity = owner['ClassIndex']
    if identity >= 0 or view['Imports'][-identity - 1]['ObjectName'] != old + '_C':
        raise ValueError('The native repeat-crystal trigger class changed.')
    original = copy.deepcopy(view['Imports'])
    def belongs(index):
        if index >= 0: return False
        item = original[-index - 1]
        return (item['ObjectName'] == package or item.get('ClassPackage') == package
                or belongs(item['OuterIndex']))
    imported = {}
    def ref(index):
        if index >= 0 or not belongs(index): return index
        if index not in imported:
            item = copy.deepcopy(original[-index - 1])
            for key, value in item.items():
                if isinstance(value, str): item[key] = value.replace(old, new)
            item['OuterIndex'] = ref(item['OuterIndex'])
            try: target = -(view['Imports'].index(item) + 1)
            except ValueError:
                view['Imports'].append(item); target = -len(view['Imports'])
            imported[index] = target
        return imported[index]
    def remap(value):
        if isinstance(value, list): return [remap(v) for v in value]
        if not isinstance(value, dict): return value
        result = {k: remap(v) for k, v in value.items()}
        if value.get('$type', '').split('.')[-1] == 'ObjectPropertyData, UAssetAPI':
            result['Value'] = ref(value['Value'])
        if 'Delegate' in value and 'Object' in value: result['Object'] = ref(value['Object'])
        return result
    def owned(index):
        return index == owner_id or index > 0 and owned(view['Exports'][index - 1]['OuterIndex'])
    for index, item in enumerate(view['Exports'], 1):
        if not owned(index): continue
        item['Data'] = remap(item['Data'])
        for key in ('ClassIndex', 'SuperIndex', 'TemplateIndex'):
            item[key] = ref(item[key])
        for key in ('SerializationBeforeSerializationDependencies', 'CreateBeforeSerializationDependencies',
                    'SerializationBeforeCreateDependencies', 'CreateBeforeCreateDependencies'):
            item[key] = [ref(i) for i in item[key]]
        view['DependsMap'][index - 1] = [ref(i) for i in (view['DependsMap'][index - 1] or [])]
    owner['Data'] = [p for p in owner['Data'] if p['Name'] not in
                    ('m_MoveTargetPoint', 'm_MoveType', 'm_EventPreActionInfo', 'm_MapInteractType', 'interactType')]
    for name in ('m_MapInteractType', 'interactType'):
        owner['Data'].append(caves.data_property(name, 'Check_Gimmick', 'EnumPropertyData',
                                                EnumType='eMapInteractType', InnerType='ByteProperty'))
    caves.names(view, [view['Imports'], owner['Data']])


def shrine_view(original, spec):
    import _ffr_crystal_cave as caves
    view = copy.deepcopy(original)
    owners = []
    for index, item in enumerate(view['Exports'], 1):
        events = next((p for p in item.get('Data', []) if p['Name'] == 'm_EventList'), None)
        if events and any(caves.property_data(e, 'EventId')['Value'] == spec['retry'] for e in events['Value']):
            owners.append(index)
    if len(owners) != 1: raise ValueError('Expected one native repeat crystal for ' + spec['mapRow'])
    button_interaction(view, owners[0])
    return view


def crystal_package(spec):
    if spec.get('crystalInteraction'): return spec['crystalInteraction']['mapPackage']
    if spec.get('retry'):
        row = spec['mapRow']
        return f'Map/Com/00Com/{row}/EV/Com_{row}_EV'
    return None


def asset_reader(env, work):
    legacy, root = Path(env['LEGACY']), Path(env['ROOT'])
    def read(package, suffix='.uasset'):
        source = legacy / ('FFRS/Content/' + package + suffix)
        if not source.is_file():
            env['run'](env['ffrenv'].py(str(root/'tools/extract_legacy.py'), '--filter', package))
        if not source.is_file(): raise ValueError('Missing native challenge asset: ' + package)
        dump = work / (Path(package).name + '-original.json')
        env['run']([*env['FFRDT'], 'tojson', str(source), str(dump), '--usmap', env['USMAP']])
        return json.loads(dump.read_text(encoding='utf-8-sig'))
    return read


def crystal_key(env, spec):
    return (str(Path(env['ROOT']).resolve()),str(Path(env['OUT']).resolve()),spec['origin'])


def preflight(units, env):
    """Validate native cave writes before spending time on thirty sprites."""
    _CHECKED_CRYSTALS.clear()
    for spec,_ in plans(units):
        if not crystal_package(spec):continue
        env.get('stage', lambda text: print('##stage '+text,flush=True))('Checking cave interactions before sprite conversion')
        work=Path(env['BUILD'])/'sephira-challenges';work.mkdir(parents=True,exist_ok=True)
        build_crystal_interaction(env,work,asset_reader(env,work),spec)
        room=crystal_package(spec)
        target=Path(env['OUT'])/('FFRS/Content/'+room+'.umap')
        import _ffr_build_cache
        _CHECKED_CRYSTALS[crystal_key(env,spec)]=[(target.with_suffix(ext),_ffr_build_cache.sha(target.with_suffix(ext)))
                                               for ext in ('.umap','.uexp')]


def checked_crystal(env,spec):
    files=_CHECKED_CRYSTALS.pop(crystal_key(env,spec),None)
    if not files:return False
    import _ffr_build_cache
    return all(p.is_file() and _ffr_build_cache.sha(p)==expected for p,expected in files)


def build(units, env):
    selected = plans(units)
    if not selected: return
    import _ffr_testing as testing
    import _ffr_fina_boss as fina
    import _ffr_crystal_cave as caves
    legacy, out, root = (Path(env[k]) for k in ('LEGACY', 'OUT', 'ROOT'))
    work = Path(env['BUILD']) / 'sephira-challenges'; work.mkdir(parents=True, exist_ok=True)
    read = asset_reader(env, work)
    # Clone AI packages through the patcher so their imported paths, generated
    # class, CDO and dependency lists retain the native serialization contract.
    source = legacy / ('FFRS/Content/' + fina.DONOR_AI + '.uasset')
    if not source.is_file(): read(fina.DONOR_AI)
    clones = []
    for spec, members in selected:
        for unit in members:
            name = 'BP_' + PREFIX + str(unit['id'])
            clones.append({'from': 'FFRS/Content/' + fina.DONOR_AI,
                'to': 'FFRS/Content/BP/Battle/AI/Studio/' + name,
                'rename': [[Path(fina.DONOR_AI).name, name]]})
    patch = work / 'ai-clones.json'
    patch.write_text(json.dumps({'legacyRoot': str(legacy), 'outRoot': str(out), 'clones': clones}), encoding='utf-8')
    env['run']([*env['FFRDT'], 'patch', str(patch), '--usmap', env['USMAP']])
    for spec, members in selected:
        for index, unit in enumerate(members):
            name = 'BP_' + PREFIX + str(unit['id'])
            target = out / ('FFRS/Content/BP/Battle/AI/Studio/' + name + '.uasset')
            dump = work / (name + '.json')
            env['run']([*env['FFRDT'], 'tojson', str(target), str(dump), '--usmap', env['USMAP']])
            actions = rotation(unit, kit(unit, env['rows'], len(members)), index)
            authored = fina.author_ai(json.loads(dump.read_text(encoding='utf-8-sig')), actions)
            dump.write_text(json.dumps(authored, ensure_ascii=False), encoding='utf-8')
            env['run']([*env['FFRDT'], 'fromjson', str(dump), str(target), '--usmap', env['USMAP']])
            env['run']([*env['FFRDT'], 'tojson', str(target), str(dump), '--usmap', env['USMAP']])
            actual = json.loads(dump.read_text(encoding='utf-8-sig'))
            for field in ('ScriptBytecode', 'ScriptBytecodeSize'):
                before = next(e[field] for e in authored['Exports'] if e['ObjectName'] == 'ThinkInner')
                after = next(e[field] for e in actual['Exports'] if e['ObjectName'] == 'ThinkInner')
                if before != after: raise ValueError('Vision boss AI failed native serialization: ' + name)
    env.get('stage', lambda text: print('##stage '+text,flush=True))('Building challenge menus')
    testing.build_choices(env, [PREFIX + str(spec['origin']) + suffix
        for spec, _ in selected for suffix in ('_Menu', '_Locked', '_Done')],
        'FFRS/Content/' + SEQUENCE, 'sephira-dialogs')
    # Each private boss carries its vision as guaranteed ordinary loot. There
    # is no post-battle event or acquisition sequence to hold the field fade.
    for spec, _ in selected:
        if crystal_package(spec) and not checked_crystal(env,spec):
            env.get('stage', lambda text: print('##stage '+text,flush=True))('Building crystal button interaction')
            build_crystal_interaction(env, work, read, spec)
    for spec, members in selected:
        stats = team_stats(env['rows'], spec['level'], members)
        print(f'  {spec["name"]} challenge: level {spec["level"]}, ' + ', '.join(u['en'] for u in members)
              + f'; combined HP {sum(s["MaxHitPoint"] for s in stats):,}; original acquisition required; victory-only rewards.')


def christine_views(original, source, background, spec):
    """Add one persistent crystal and an input interaction to the native cave.

    Append to the persistent cave world, independent of optional gimmick streams.
    Keep its original export/import/name indices and story actors. The talk
    event owns every acquisition check; no new streaming level is required.
    """
    import _ffr_crystal_cave as caves
    destination = spec['crystalInteraction']
    room = destination['mapPackage']
    donor = 'Map/Com/00Com/00Com_223/EV/Com_00Com_223_EV'
    package = SEQUENCE + 'Studio_ChristineCrystal_EV'
    trigger = caves.private_level(source, '/Game/' + donor, '/Game/' + package)
    owner_id, owner = caves.export(trigger, 'BP_MapGimmick_EventTrigger_C_1')
    caves.set_value(owner, 'm_UniqueId', 27500)
    events = caves.property_data(owner, 'm_EventList')['Value']
    if len(events) != 1: raise ValueError('The native crystal interaction changed.')
    caves.set_value(events[0], 'EventId', PREFIX + str(spec['origin']))
    caves.set_value(events[0], 'Condition', '')
    # Flag 147 is cleared by C01_015_01. Use the persistent acquisition/story
    # condition for both appearance and interaction, including existing saves.
    owner['Data'] += [caves.data_property('VisibleCondition', spec['unlock'], 'StrPropertyData'),
        caves.data_property('m_FlagCondition', spec['unlock'], 'StrPropertyData'),
        caves.data_property('bIsBeginPlaySycnVisibleCall', True, 'BoolPropertyData')]
    point_id = caves.property_data(owner, 'm_MoveTargetPoint')['Value']
    point = trigger['Exports'][point_id - 1]
    caves.set_value(point, 'm_Direction', 'North')
    box = trigger['Exports'][caves.property_data(owner, 'm_pRootBoxComponent')['Value'] - 1]
    caves.vector(box, 'RelativeLocation', destination['position'])
    extent = copy.deepcopy(caves.property_data(box, 'RelativeLocation'))
    extent['Name'] = 'BoxExtent'; extent['Value'][0]['Name'] = 'BoxExtent'
    box['Data'].append(extent)
    caves.vector(box, 'RelativeScale3D', (1.0, 1.0, 1.0))
    caves.vector(box, 'BoxExtent', (180.0, 200.0, 220.0))
    point_root = trigger['Exports'][caves.property_data(point, 'RootComponent')['Value'] - 1]
    caves.vector(point_root, 'RelativeLocation', destination['approach'])
    button_interaction(trigger, owner_id)
    # A single native blue shrine crystal, with its original material. Mesh 002
    # is the other shrine crystal, not a second layer of the same object.
    crystal = copy.deepcopy(background)
    actor_id, mesh_id = caves.clear_crystals(crystal)['SM_Env_Com_magicstone001']
    level_id, level = caves.export(trigger, 'PersistentLevel')
    roots = {actor_id: owner_id, caves.export(crystal, 'PersistentLevel')[0]: level_id,
             caves.export(crystal, 'Com_00Com_217_01_BG')[0]: caves.export(trigger, Path(package).name)[0]}
    mapping = caves.clone_graph(trigger, crystal, [mesh_id], roots)
    mesh = trigger['Exports'][mapping[mesh_id] - 1]
    mesh['ObjectName'] = 'Studio_ChristineCrystal'
    # This component belongs to the conditionally visible interaction actor.
    # A static mesh moved from another cooked map must not retain its baked
    # visibility ID: the destination's culling data can otherwise hide it.
    root_box = caves.property_data(owner, 'm_pRootBoxComponent')['Value']
    mesh['Data'] = [p for p in mesh['Data'] if p['Name'] not in
                    ('AttachParent', 'Mobility', 'VisibilityId', 'bIsValidTextureStreamingBuiltData', 'CreationMethod')]
    mesh['Data'] += [caves.data_property('AttachParent', root_box, 'ObjectPropertyData'),
        caves.data_property('Mobility', 'Movable', 'EnumPropertyData', EnumType='EComponentMobility', InnerType='ByteProperty'),
        caves.data_property('CreationMethod', 'Instance', 'EnumPropertyData', EnumType='EComponentCreationMethod', InnerType='ByteProperty'),
        caves.data_property('VisibilityId', -1, 'IntPropertyData'),
        caves.data_property('bIsValidTextureStreamingBuiltData', False, 'BoolPropertyData')]
    owner['Data'].append(caves.data_property('InstanceComponents', [
        caves.data_property('0', mapping[mesh_id], 'ObjectPropertyData')], 'ArrayPropertyData', ArrayType='ObjectProperty'))
    caves.vector(mesh, 'RelativeLocation', (0.0, 0.0, 0.0))
    caves.vector(mesh, 'RelativeScale3D', (2.0, 2.0, 2.0))
    caves.actors(trigger, [caves.export(trigger, 'CPP_MuchaWorldSetting')[0], 0,
                           owner_id, point_id])
    caves.names(trigger, [trigger['Exports'], PREFIX.rstrip('_')])
    # The persistent world loads on every visit, including older saves.
    # Keep all native streaming declarations and actors at their original indices.
    room_view = copy.deepcopy(original)
    native_level_id, native_level = caves.export(room_view, 'PersistentLevel')
    native_world = next(i for i,e in enumerate(room_view['Exports'],1)
                        if e['ObjectName'] == Path(room).name)
    roots = {level_id:native_level_id, caves.export(trigger, Path(package).name)[0]:native_world}
    for name in ('CPP_MuchaWorldSetting', 'Model_0', 'NavigationSystemModuleConfig_0'):
        roots[caves.export(trigger,name)[0]] = caves.export(room_view,name)[0]
    indices = [i for i,e in enumerate(trigger['Exports'],1) if i not in roots]
    appended = caves.clone_graph(room_view,trigger,indices,roots)
    caves.actors(room_view, native_level['Actors'] + [appended[i] for i in
                 (owner_id,point_id)])
    caves.names(room_view, [room_view['Exports'], PREFIX.rstrip('_')])
    caves.check_object_names(room_view)
    return {room: room_view}


def build_christine_interaction(env, work, read, spec):
    import _ffr_crystal_cave as caves
    donor = 'Map/Com/00Com/00Com_223/EV/Com_00Com_223_EV'
    room = spec['crystalInteraction']['mapPackage']
    original = read(room, '.umap')
    background = read(caves.ROOM_BG, '.umap')
    blueprint = read('BP/Map/Gimmick/BP_MapGimmick_EventTrigger')
    _, cl = caves.export(blueprint, 'BP_MapGimmick_EventTrigger_C')
    mapping = work / 'christine-mappings.usmap'
    mapping.write_bytes(caves.map_mappings(Path(env['USMAP']).read_bytes(), {cl['ObjectName']: (blueprint, cl)}))
    read(donor, '.umap')  # Ensure the native template is extracted.
    decoded = work / 'christine-trigger.json'
    env['run']([*env['FFRDT'], 'tojson', str(Path(env['LEGACY']) / ('FFRS/Content/' + donor + '.umap')),
                str(decoded), '--usmap', str(mapping)])
    source = json.loads(decoded.read_text(encoding='utf-8-sig'))
    views = christine_views(original, source, background, spec)
    write_crystal_views(views, env, work)


def build_crystal_interaction(env, work, read, spec):
    if spec.get('crystalInteraction'):
        return build_christine_interaction(env, work, read, spec)
    import _ffr_crystal_cave as caves
    package = crystal_package(spec)
    blueprint = read('BP/Map/Gimmick/BP_MapGimmick_EventTrigger')
    _, cl = caves.export(blueprint, 'BP_MapGimmick_EventTrigger_C')
    mapping = work / 'repeat-crystal-mappings.usmap'
    mapping.write_bytes(caves.map_mappings(Path(env['USMAP']).read_bytes(), {cl['ObjectName']: (blueprint, cl)}))
    read(package, '.umap')
    decoded = work / (Path(package).name + '-trigger.json')
    env['run']([*env['FFRDT'], 'tojson', str(Path(env['LEGACY']) / ('FFRS/Content/' + package + '.umap')),
                str(decoded), '--usmap', str(mapping)])
    view = shrine_view(json.loads(decoded.read_text(encoding='utf-8-sig')), spec)
    write_crystal_views({package: view}, env, work)


def write_crystal_views(views, env, work):
    import _ffr_crystal_cave as caves
    # The native GD can decode additional Blueprint actors when their packages
    # are already extracted. JSON serialization needs those exact declarations
    # too, including inherited fields; the trigger-only mapping is insufficient.
    mapping = caves.blueprint_mappings(views, env, work)
    for rel, view in views.items():
        caves.names(view, view['Exports'])
        # Numbered actor names serialize as a base FName plus an instance
        # number. The old class no longer supplies that base when Christine's
        # actor is imported into the cave with the new interaction class.
        caves.names(view, [e['ObjectName'].rsplit('_', 1)[0] for e in view['Exports']
                           if e['ObjectName'].rsplit('_', 1)[-1].isdigit()])
        dump = work / (Path(rel).name + '-built.json'); dump.write_text(json.dumps(view), encoding='utf-8')
        target = Path(env['OUT']) / ('FFRS/Content/' + rel + '.umap'); target.parent.mkdir(parents=True, exist_ok=True)
        env['run']([*env['FFRDT'], 'fromjson', str(dump), str(target), '--usmap', str(mapping)])
        env['run']([*env['FFRDT'], 'tojson', str(target), str(dump), '--usmap', str(mapping)])
        caves.check_level(view, json.loads(dump.read_text(encoding='utf-8-sig')))
