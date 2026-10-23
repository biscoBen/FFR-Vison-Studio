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
    for index, identity in enumerate([0, *dict.fromkeys(chosen)]):
        recipe = (unit.get('skills') or {}).get(identity, (unit.get('skills') or {}).get(str(identity), {}))
        source = recipe.get('from', identity) if identity else 500010
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
        if identity == 0: row.update(Name='Attack', element='None', magnification=12)
        healing = row['parameterVariationType'] == 'Increase' and row['parameterType'] == 'HitPoint'
        damaging = row['parameterVariationType'] == 'Decrease' and row['DamageType'] in ('Magic', 'Physic')
        if healing:
            # A threshold-gated self heal is bounded to 15% of this boss's share.
            row.update(TargetType='Self', defaultTargetRelation='Friendlies', damageCalcType='TargetMaxHPRatio', magnification=15)
        elif damaging:
            if row['damageCalcType'] not in ('Physic', 'Magic', 'MPAbsorb'):
                row['damageCalcType'] = 'Physic' if row['DamageType'] == 'Physic' else 'Magic'
            cap = 40 if row['TargetType'] in ('Group', 'All', 'SingleAndGroup') else 60
            row['magnification'] = max(1, round(min(row['magnification'], cap) / team_size))
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
        _add(table, rows, UNIT, identity, 401, name, {**stats,
            'Name': unit['en'], 'Description': 'Sephira crystal challenge',
            'SortId': identity, 'SaveId': identity, 'FaceIconId': unit['id'],
            'Category': 'Boss', 'Sex': 'Female', 'Race': 'Human', 'IsBoss': True, 'IsAccent': False,
            'HitPoint': 0, 'MagicPoint': stats['MaxMagicPoint'], 'Breakpoint': 0, 'LimitBurstPoint': 0,
            'ElementResistanceList': {k: 'eResistance::None' for k in donor['ElementResistanceList']},
            'passiveSkillList': [], 'WeaponId': -1, 'ArmorId': -1, 'AccessoryIdList': [], 'VisionId': -1,
            'Experience': 0, 'Money': 0, 'DropNormalItem': -1, 'DropNormalItemRate': 0,
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
        _add(table, rows, AI, identity, 401, name, {'aiId': identity, 'fightSkillId': ids[0],
            'silenceFightId': ids[0], 'chaseSkillId': -1, 'counterSkillIdList': [-1, -1],
            'highRiskSkillIdList': [-1, -1],
            'skillRandData1': [{'SkillId': ids[0], 'Probability': 100.0}],
            'skillRandData2': [{'SkillId': v, 'Probability': 0.0} for v in ids]})
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
        'battleFinishEventId': name + '_Win',
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
    if proof.startswith('{flag:'):
        valid = int(proof.removeprefix('{flag:').removesuffix('}')) in grant['OnFlagList']
    else:
        progress, value = proof.removeprefix('{progress:').split('}>=')
        valid = any(p['ID'] == int(progress) and p['Value'] == int(value) for p in grant['ProgressList'])
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
    event(name + '_Win', {'ContinuousEventList': links(unlock, name + '_Grant', locked, name + '_Close')}, 'link')
    event(name + '_Grant', {
        'EventSequence': '/Game/' + SEQUENCE + 'SEQ_Grant', 'IsOpenDialogByFinishEvent': True,
        'ObtainItemList': [{'Condition': f'{{item:{u["id"]}}}==0', 'ID': u['id'], 'Num': 1, 'Text': ''} for u in units]}, 'grant')
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
    if spec.get('returnEntry'):
        # Tronn's crystal room is blocked on the user's revisit. Offer the
        # guarded challenge in the secret cave behind Rain's house instead.
        # Distribute the conjunction over the native OR alternatives so both
        # ownership and original completion flags require a missing reward.
        ready = '|'.join(f'{gate}&{reward}' for gate in unlock.split('|') for reward in missing.split('|'))
        entry = name + '_Return'
        event(entry, {'ContinuousEventList': links(ready, name + '_Menu',
            locked + '|' + complete, name + '_Close')}, 'link')
        destination = spec['returnEntry']
        for rel in (destination['mapTable'], caves.COMPOSITE):
            original = rows(rel).get(destination['mapRow'], {})
            starts = original.get('startupEventList')
            if (original.get('ID') != destination['map'] or not isinstance(starts, list)
                    or any(not isinstance(s, dict) or s.get('EventId') == entry for s in starts)):
                raise ValueError('The secret cave behind Rain\'s house changed; collect a new native reference.')
            # startupEventList is a native struct array, even though the row
            # dump hides its type when empty. Clone a populated row, restore
            # every field of the cave and then append the conditional entry.
            donor = '01Gra_20'
            template = rows(rel).get(donor, {})
            if not template.get('startupEventList'):
                raise ValueError('The native map startup-event template is unavailable.')
            desired = copy.deepcopy(original)
            desired['startupEventList'] = [*starts, {'Condition': ready, 'EventId': entry}]
            fields = testing.field_delta(template, desired)
            # Row dumps represent string-table FText as a dictionary. Native
            # Name is a TextProperty, so restore it whole, never Name.key.
            fields = {k: v for k, v in fields.items() if not k.startswith('Name.')}
            fields['Name'] = copy.deepcopy(desired['Name'])
            table(rel)['add'].append({'row': destination['mapRow'], 'cloneFrom': donor,
                                     'set': fields})
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


def build(units, env):
    selected = plans(units)
    if not selected: return
    import _ffr_testing as testing
    import _ffr_fina_boss as fina
    import _ffr_crystal_cave as caves
    legacy, out, root = (Path(env[k]) for k in ('LEGACY', 'OUT', 'ROOT'))
    work = Path(env['BUILD']) / 'sephira-challenges'; work.mkdir(parents=True, exist_ok=True)
    def read(package, suffix='.uasset'):
        source = legacy / ('FFRS/Content/' + package + suffix)
        if not source.is_file():
            env['run'](env['ffrenv'].py(str(root/'tools/extract_legacy.py'), '--filter', package))
        if not source.is_file(): raise ValueError('Missing native challenge asset: ' + package)
        dump = work / (Path(package).name + '-original.json')
        env['run']([*env['FFRDT'], 'tojson', str(source), str(dump), '--usmap', env['USMAP']])
        return json.loads(dump.read_text(encoding='utf-8-sig'))
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
    testing.build_choices(env, [PREFIX + str(spec['origin']) + suffix
        for spec, _ in selected for suffix in ('_Menu', '_Locked', '_Done')],
        'FFRS/Content/' + SEQUENCE, 'sephira-dialogs')
    # One small footer-driven sequence grants the current event's conditional
    # rewards. It is referenced exclusively by victorious challenge groups.
    source = read(caves.GRANT_DONOR)
    from dataclasses import replace
    grant_spec = replace(caves.CaveSpec(), package=SEQUENCE + 'SEQ', name='SEQ')
    grant = caves.grant_sequence(source, grant_spec)
    destination = out / ('FFRS/Content/' + SEQUENCE + 'SEQ_Grant.uasset')
    destination.parent.mkdir(parents=True, exist_ok=True)
    dump = work / 'grant.json'; dump.write_text(json.dumps(grant), encoding='utf-8')
    env['run']([*env['FFRDT'], 'fromjson', str(dump), str(destination), '--usmap', env['USMAP']])
    env['run']([*env['FFRDT'], 'tojson', str(destination), str(dump), '--usmap', env['USMAP']])
    caves.check_level(grant, json.loads(dump.read_text(encoding='utf-8-sig')))
    if any(spec['origin'] == 13024 and not spec.get('returnEntry') for spec, _ in selected):
        build_tronn_interaction(env, work, read)
    for spec, members in selected:
        stats = team_stats(env['rows'], spec['level'], members)
        print(f'  {spec["name"]} challenge: level {spec["level"]}, ' + ', '.join(u['en'] for u in members)
              + f'; combined HP {sum(s["MaxHitPoint"] for s in stats):,}; original acquisition required; victory-only rewards.')


def build_tronn_interaction(env, work, read):
    """Tronn's story shrine has no native repeat actor; add a private stream.

    Reuse the adjacent-crystal interaction from WoL's identical shrine layout,
    retaining the original revisit map, background, lighting and exits.
    """
    import _ffr_crystal_cave as caves
    donor = 'Map/Com/00Com/00Com_223/EV/Com_00Com_223_EV'
    room = 'Map/Com/00Com/00Com_237/Com_00Com_237_PL'
    source = read(donor, '.umap'); original = read(room, '.umap')
    # Read BP declarations before editing: opaque RawExports are never aliased
    # to their C++ parents or written back after property-index guesses.
    blueprint = read('BP/Map/Gimmick/BP_MapGimmick_EventTrigger')
    _, cl = caves.export(blueprint, 'BP_MapGimmick_EventTrigger_C')
    mapping = work/'tronn-mappings.usmap'
    mapping.write_bytes(caves.map_mappings(Path(env['USMAP']).read_bytes(), {cl['ObjectName']: (blueprint, cl)}))
    path = Path(env['LEGACY']) / ('FFRS/Content/' + donor + '.umap'); decoded = work/'tronn-trigger.json'
    env['run']([*env['FFRDT'], 'tojson', str(path), str(decoded), '--usmap', str(mapping)])
    source = json.loads(decoded.read_text(encoding='utf-8-sig'))
    views = tronn_views(original, source)
    for rel, view in views.items():
        caves.names(view, view['Exports'])
        dump = work/(Path(rel).name+'-built.json'); dump.write_text(json.dumps(view), encoding='utf-8')
        target = Path(env['OUT'])/('FFRS/Content/'+rel+'.umap'); target.parent.mkdir(parents=True, exist_ok=True)
        env['run']([*env['FFRDT'], 'fromjson', str(dump), str(target), '--usmap', str(mapping)])
        env['run']([*env['FFRDT'], 'tojson', str(target), str(dump), '--usmap', str(mapping)])
        caves.check_level(view, json.loads(dump.read_text(encoding='utf-8-sig')))


def tronn_views(original, source):
    import _ffr_crystal_cave as caves
    original = copy.deepcopy(original)
    donor = 'Map/Com/00Com/00Com_223/EV/Com_00Com_223_EV'
    room = 'Map/Com/00Com/00Com_237/Com_00Com_237_PL'
    package = SEQUENCE + 'Studio_TronnCrystal_EV'
    trigger = caves.private_level(source, '/Game/' + donor, '/Game/' + package)
    _, actor = caves.export(trigger, 'BP_MapGimmick_EventTrigger_C_1')
    caves.set_value(actor, 'm_UniqueId', 27500)
    events = caves.property_data(actor, 'm_EventList')['Value']
    if len(events) != 1: raise ValueError('The native shrine crystal interaction changed.')
    caves.set_value(events[0], 'EventId', PREFIX + '13024')
    # The talk event performs the ownership gate, including already-open saves.
    caves.set_value(events[0], 'Condition', '')
    # Event IDs ending in an integer are numbered FNames; register their base
    # as well as the full text before JSON deserialization.
    caves.names(trigger, PREFIX.rstrip('_'))
    # The native revisit room has dynamic BG/LT streams. Make a separate native
    # ULevelStreamingAlwaysLoaded declaration using their shared WorldAsset
    # property; leave both original streams and their class imports untouched.
    streaming = copy.deepcopy(original)
    stream = next(e for e in streaming['Exports'] if e['ClassIndex'] < 0
        and streaming['Imports'][-e['ClassIndex']-1]['ObjectName'] == 'LevelStreamingDynamic')
    if {p['Name'] for p in stream['Data']} != {'WorldAsset', 'LevelColor'}:
        raise ValueError('The native shrine streaming declaration changed.')
    streaming['Imports'][-stream['ClassIndex']-1]['ObjectName'] = 'LevelStreamingAlwaysLoaded'
    template = streaming['Imports'][-stream['TemplateIndex']-1]
    template.update(ObjectName='Default__LevelStreamingAlwaysLoaded', ClassName='LevelStreamingAlwaysLoaded')
    caves.add_collision_stream(original, Path(room).name, streaming, package)
    return {package: trigger, room: original}
