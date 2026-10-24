"""Opt-in original vision grants, bounded MR and a repeatable shop battle."""
import _ffr_build_cache
import copy
import json
import os
import re
from pathlib import Path
import subprocess
import tempfile

GROUP = 'Encount/DT_BattleGroup'
EVENT = 'Event/TalkEvent/MainEvent/DT_TalkEventData_Chapter01'
COMPOSITE = 'Event/TalkEvent/CDT_TalkEventData_Demo'
COMMON = 'Event/BattleEvent/DT_BtlCmnEventDataBundle'
NAME = 'Studio_TestNativeVisions'
CONFIG = 'mods/EstherTsukiko/testing.json'
SHOP_EVENT = 'Event/TalkEvent/FreeTalk/01Gra/DT_TalkEventData_Town_01Gra_20'
# The shop's "Potions, Phoenix Downs..." conversation resolves to talk block
# 6 / Town_01Gra_20_120. NPC display names and sprite IDs do not identify it.
SHOP_WOMAN = 'DT_Town_010Gra_20_0920_8'
MAP = 'Map/MapData/DT_MapData_01Gra'
MAP_COMPOSITE = 'Map/CDT_MapData_Demo'
PRACTICE = 'Studio_PracticeBattle'
PRACTICE_ID = 29990
STAGE = 'Asset/Battle/Stage/DT_BtlStageAsset'
STAGE_COMPOSITE = 'Asset/Battle/Stage/CDT_BtlStageAsset_Demo'
CHOICES = 'UI/Common/Dialog/DT_DIalogChoice'
CHOICE_FOLDER = 'FFRS/Content/Sequencer/Event/StudioPractice/'
OPPONENTS = (
    ('standard', 'Usual enemies (levels 7-8)', 20, 7),
    ('cactuar', 'Cactuar (level 30): 1,000 Needles', 38, 30),
    ('watcher', 'Watcher (level 26): Atomic Ray', 188, 26),
    ('ganymede', 'Ganymede (level 70): Atomic Ray', 196, 70),
    ('malbodoom', 'Malbodoom (level 40): Bad Breath', 257, 40),
    ('malboro', 'Malboro Marquis (level 53): Bad Breath', 258, 53),
    ('gigantuar', 'Gigantuar (level 40): 10,000 Needles', 352, 40),
    ('sheratan', 'Sheratan (level 50): Alluring Pollen', 641, 50),
    ('alpherg', 'Alpherg (level 50): Bubble Breath', 651, 50),
    ('bomb', 'Bomb (level 12): Self-Destruct', 24, 12),
    ('wood_eyes', 'Wood Eyes (level 11): Constrict', 23, 11),
    ('white_peak', 'White Peak (level 15): White Wind', 283, 15),
    ('crystal_fina', 'Crystal Fina (level 10): vision boss test', 29670, 10),
)


def settings(root):
    path = Path(root) / CONFIG
    return validate_settings(json.loads(path.read_bytes())) if path.is_file() else {
        'schema': 1, 'maxMr': False, 'practiceBattle': False, 'practiceEncounter': 'standard', 'surviveAtOne': False, 'ffbeNeedles': False, 'finaCinematic': False, 'crystalCave': False, 'crystalCaveTest': False, 'fieldLeader': False}


def validate_settings(value):
    # Accept and discard the removed diagnostic switches in older configs.
    # Crystal Fina Test now always uses transparent glass with rotation.
    if (not isinstance(value, dict) or not {'schema', 'maxMr'} <= set(value)
            or set(value) - {'schema', 'maxMr', 'practiceBattle', 'practiceEncounter', 'surviveAtOne', 'ffbeNeedles', 'finaCinematic', 'crystalCave', 'crystalCaveTest', 'crystalCaveTestSolid', 'crystalCaveTestRotate', 'fieldLeader'}
            or type(value['schema']) is not int or value['schema'] != 1 or type(value['maxMr']) is not bool
            or type(value.get('practiceBattle', False)) is not bool
            or type(value.get('surviveAtOne', False)) is not bool
            or type(value.get('ffbeNeedles', False)) is not bool
            or type(value.get('finaCinematic', False)) is not bool
            or value.get('practiceEncounter', 'standard') not in ('standard', 'cactuar')
            or type(value.get('crystalCave', False)) is not bool
            or type(value.get('crystalCaveTest', False)) is not bool
            or type(value.get('crystalCaveTestSolid', True)) is not bool
            or type(value.get('crystalCaveTestRotate', False)) is not bool
            or (value.get('crystalCave', False) and value.get('crystalCaveTest', False))
            or type(value.get('fieldLeader', False)) is not bool):
        raise ValueError('Invalid vision testing settings.')
    return {'schema': 1, 'maxMr': value['maxMr'], 'practiceBattle': value.get('practiceBattle', False),
            'practiceEncounter': value.get('practiceEncounter', 'standard'), 'surviveAtOne': value.get('surviveAtOne', False), 'ffbeNeedles': value.get('ffbeNeedles', False), 'finaCinematic': value.get('finaCinematic', False),
            'crystalCave': value.get('crystalCave', False), 'crystalCaveTest': value.get('crystalCaveTest', False),
            'fieldLeader': value.get('fieldLeader', False)}


def reward(rows):
    totals = {}
    for row in rows('Item/Vision/DT_VisionSynchroMasteryData').values():
        point = row['masteryPoint']
        if type(point) is not int or not 0 <= point <= 32767:
            raise ValueError('The native MR thresholds cannot provide a bounded test reward.')
        totals[row['ID']] = totals.get(row['ID'], 0) + point
    value = max(totals.values(), default=0)
    # Cover both cumulative thresholds and per-rank costs without an overflow-sized reward.
    if not 0 < value <= 32767:
        raise ValueError('The native MR total exceeds the bounded test reward range.')
    return value


def ensure_assets(root, extract):
    import _ffr_fina_cinematic
    _ffr_fina_cinematic.ensure_assets(root, extract)
    if settings(root)['practiceBattle']:
        path = Path(root) / 'extracted/legacy/FFRS/Content/Datatable' / (CHOICES + '.uasset')
        if not path.is_file(): extract('Datatable/' + CHOICES)
        if not path.is_file(): raise ValueError('The native opponent choice table could not be extracted.')


def prepare(tables, units, root, rows):
    selected = []
    for u in units:
        if 'testAcquire' in u and (type(u['testAcquire']) is not bool or not u.get('native')):
            raise ValueError('Test acquisition requires an original vision identity.')
        if u.get('testAcquire'):
            import _ffr_existingvisions as native
            native.validate(u, rows)
            selected.append(u['id'])
    if len(selected) != len(set(selected)):
        raise ValueError('Duplicate original vision test acquisition.')
    def table(rel):
        return tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})
    if selected:
        events = rows(COMPOSITE); parent = rows(EVENT); common = rows(COMMON)
        if NAME in events or NAME in parent or NAME in common:
            raise ValueError('The test event identity already exists in the original game tables.')
        # This original event has no timeline, dialogue, Blueprint or story flags.
        donor = events['C01_ArijigokuEncount']
        if (any(donor[k] != 'None' for k in ('TalkEventDataTable', 'EventSequence', 'EventBlueprint'))
                or any(donor[k] for k in ('OnFlagList', 'OffFlagList', 'FlagList', 'ProgressList',
                                         'ContinuousEventList', 'ObtainItemList', 'InitUnitDataList'))):
            raise ValueError('The native grant-event template changed; no test event was built.')
        updates = {'Description': 'Studio clean-save vision testing', 'encountGroupId': -1,
                   'IsGetOffVehicle': False, 'IsHiddenFieldUI': False, 'LoadingScreenSetting': 'None',
                   'MapStartupSettings.ChangeBGM': 'NotChange',
                   'RestoreSoundVolumeSettings.IsRevertValume': False,
                   'ObtainItemList': [{'Condition': f'{{item:{vid}}}==0', 'ID': vid, 'Num': 1, 'Text': ''}
                                      for vid in sorted(selected)]}
        # The serializer needs a populated struct-array donor. This is the
        # game's original Rain/Tronn vision grant; replace ALL its story state
        # with the checked no-op template before adding our selected items.
        grant = events['C01_014_03']
        if not grant.get('ObtainItemList') or parent.get('C01_014_03') != grant:
            raise ValueError('The native vision-grant template is unavailable.')
        desired = apply_fields(donor, updates)
        updates = field_delta(grant, desired)
        # CompositeDataTable rebuilds its runtime map from ParentTables. Patch
        # the registered parent AND its cooked composite cache, as for skill assets.
        for rel in (EVENT, COMPOSITE):
            table(rel)['add'].append({'row': NAME, 'cloneFrom': 'C01_014_03', 'set': copy.deepcopy(updates)})
        key, source = next((k, v) for k, v in common.items() if v['eventCondition'] == 'BattleBegin')
        event = copy.deepcopy(source['eventDataList'][0])
        if len(source['eventDataList']) != 1 or len(event['playSetting']['EventList']) != 1 or event['ParameterList']:
            raise ValueError('The native common battle-event template changed.')
        event['playSetting']['Condition'] = '|'.join(f'{{item:{vid}}}==0' for vid in sorted(selected))
        event['playSetting']['EventList'][0]['EventId'] = NAME
        table(COMMON)['add'].append({'row': NAME, 'cloneFrom': key, 'set': {
            'eventDataList[0].playSetting.Condition': event['playSetting']['Condition'],
            'eventDataList[0].playSetting.EventList[0].EventId': NAME}})
    controls = settings(root)
    value = reward(rows) if controls['maxMr'] else None
    if value is not None:
        for key, original in rows(GROUP).items():
            if type(original.get('ap')) is not int:
                raise ValueError('A native battle MR reward is missing.')
            table(GROUP)['set'].append({'row': key, 'set': {'ap': value}})
    if controls['surviveAtOne']:
        prepare_survival(table, rows)
    if controls['practiceBattle']:
        import _ffr_fina_boss
        _ffr_fina_boss.prepare(table, rows, units)
        prepare_practice(table, rows, value)
    import _ffr_crystal_cave
    _ffr_crystal_cave.prepare(tables, units, root, rows)
    import _ffr_shrine_challenges
    _ffr_shrine_challenges.prepare(tables, units, root, rows)
    import _ffr_field_leader
    _ffr_field_leader.prepare(tables, units, root, rows)
    return tables


def prepare_survival(table, rows):
    """Native damage-time reprieve: unlimited uses, no damage or healing edits."""
    passive_rel, effect_rel, unit_rel = 'Skill/DT_PassiveSkillData', 'Skill/DT_SkillEffectData', 'Unit/DT_UnitParameter'
    passives, effects, units = rows(passive_rel), rows(effect_rel), rows(unit_rel)
    def source(data, identity):
        found = [(k, v) for k, v in data.items() if v.get('ID') == identity]
        if len(found) != 1: raise ValueError('Native survival test template unavailable: ' + str(identity))
        return found[0]
    pk, passive = source(passives, 1259)
    ek, effect = source(effects, 1359)
    dk, death = source(effects, 1411)
    if (effect['EffectType'] != 'Reprieve' or effect['ParamList'][:2] != [0, -1]
            or effect['activationCondition']['Condition'] != 'None'
            or effect['activationProbability'] != 100 or effect['effectEndActionNum'] != -1
            or passive['effectBundleList'][0]['effectId'] != 1359
            or passive['effectBundleList'][0]['passiveSkillAddTiming'] != 'SpawnUnit'
            or death['EffectType'] != 'AddStatusConditionRegist' or death['ParamList'][:2] != [13, 1000]):
        raise ValueError('Native survival semantics changed; the test was not applied.')
    for rel, data, identities in ((passive_rel, passives, {29660}), (effect_rel, effects, {29661, 29662})):
        if any(v.get('ID') in identities for v in data.values()) or any(
                v['set'].get('ID') in identities for v in table(rel)['add']):
            raise ValueError('A survival test identity is already occupied.')
    for key, identity, name in ((ek, 29661, 'Reprieve'), (dk, 29662, 'DeathResistance')):
        table(effect_rel)['add'].append({'row': 'Studio_Test_' + name, 'cloneFrom': key,
            'set': {'ID': identity, 'isUnremovable': True}})
    bundles = copy.deepcopy(passive['effectBundleList'])
    bundles[0]['effectId'] = 29661
    bundles[1] = copy.deepcopy(bundles[0]); bundles[1]['effectId'] = 29662
    table(passive_rel)['add'].append({'row': 'Studio_TestSurvival', 'cloneFrom': pk, 'set': {
        'ID': 29660, 'SortId': 29660, 'Name': 'Testing: survive at 1 HP',
        'Description': 'Survive lethal damage at 1 HP while testing. Damage and healing are unchanged.',
        'effectBundleList': bundles, 'isRemovable': False, 'equipCost': 0, 'bBattleOnly': True}})
    playable = [(k, v) for k, v in units.items() if v.get('Category') == 'Playable']
    if not {1001, 1002} <= {v['ID'] for _, v in playable}:
        raise ValueError('The native party survival targets are unavailable.')
    for key, original in playable:
        current = copy.deepcopy(original)
        for edit in table(unit_rel)['set']:
            if edit['row'] == key: current = apply_fields(current, edit['set'])
        skills = current['passiveSkillList']
        if 29660 not in skills:
            table(unit_rel)['set'].append({'row': key, 'set': {'passiveSkillList': [*skills, 29660]}})


def prepare_practice(table, rows, ap, encounter='standard'):
    """Keep the woman's dialogue and party; launch a private, story-free encounter."""
    parent = rows(SHOP_EVENT); combined = rows(COMPOSITE)
    woman = parent.get(SHOP_WOMAN)
    if (not woman or combined.get(SHOP_WOMAN) != woman or woman.get('ArgList') != {'id': '6'}
            or woman.get('encountGroupId') != -1 or woman.get('OverwriteBattleParty')
            or any(woman.get(k) for k in ('OnFlagList', 'OffFlagList', 'FlagList', 'ProgressList',
                                        'ContinuousEventList', 'ChoicesBranchEventList', 'ObtainItemList',
                                        'ConsumeItemList', 'InitUnitDataList', 'ChangeUnitJoinStatusList'))
            or woman.get('IsSetAutoSave') or woman.get('IsSetForceAutoSave')
            or woman.get('IsForceUpdateProgress') or woman['TransitionLocation']['mapId'] != -1):
        raise ValueError('The Mitra Young Woman interaction changed; no practice battle was built.')
    maps = rows(MAP); map_combined = rows(MAP_COMPOSITE)
    town = maps.get('01Gra_20')
    if (not town or town.get('ID') != 2000 or map_combined.get('01Gra_20') != town
            or town.get('doMovementEncount') or town.get('battleStage') != -1):
        raise ValueError('The Mitra map is unavailable.')
    stages = rows(STAGE); stage_combined = rows(STAGE_COMPOSITE)
    plains = [(k, v) for k, v in stages.items() if v.get('ID') == 5]
    if (len(plains) != 1 or stage_combined.get(plains[0][0]) != plains[0][1]
            or plains[0][1].get('battleLevelList') != [
                '/Game/Map/Btl/00Com/00Com_60/LT/Btl_00Com_60_01_LT',
                '/Game/Map/Btl/00Com/00Com_60/BG/Btl_00Com_60_BG0']
            or type(plains[0][1].get('isLoadLevelInstance')) is not bool
            or any(PRACTICE in t or any(v.get('ID') == PRACTICE_ID for v in t.values())
                   for t in (stages, stage_combined))):
        raise ValueError('The native plains battle stage is unavailable or its practice identity conflicts.')
    groups = rows(GROUP)
    donors = [(k, v) for k, v in groups.items() if v.get('ID') == 1026]
    if len(donors) != 1:
        raise ValueError('The native practice encounter template is unavailable.')
    donor_key, donor = donors[0]
    if (donor.get('UnitIdList') != [20, 22, 22] or donor.get('locationIdList') != [20, 6, 15]
            or donor.get('battleEventId') != -1 or donor.get('battleFinishEventId')
            or donor.get('battleFinishEscapeEventId') or donor.get('battleFinishLoseEventId')
            or donor['battleFinishTransition']['mapId'] != -1
            or donor['battleFinishTransition'].get('bDoAutoSave')):
        raise ValueError('The native practice encounter template changed.')
    units = rows('Unit/DT_UnitParameter')
    by_id = {v['ID']: v for v in units.values()}
    for _, _, uid, level in OPPONENTS:
        if uid == 29670: continue  # Private boss, validated by its own builder.
        opponent = by_id.get(uid, {})
        # Boss is a separate native category, including Gigantuar and the
        # twelve-arms bosses. Keep that category and every enemy row intact.
        if opponent.get('Category') not in ('Enemy', 'Boss') or opponent.get('Level') != level:
            raise ValueError(f'Native practice opponent {uid} requires an Enemy/Boss at level {level}; '
                             f"found category={opponent.get('Category')}, level={opponent.get('Level')}.")
    if by_id.get(20, {}).get('Level') != 7 or by_id.get(22, {}).get('Level') != 8:
        raise ValueError('The usual practice enemies changed.')
    for index, (key, label, uid, level) in enumerate(OPPONENTS):
        name, identity = PRACTICE + '_' + key, PRACTICE_ID + index
        if name in groups or any(v.get('ID') == identity for v in groups.values()):
            raise ValueError('A practice encounter identity is already occupied.')
        table(GROUP)['add'].append({'row': name, 'cloneFrom': donor_key, 'set': {
            'ID': identity, 'UnitIdList': [20, 22, 22] if key == 'standard' else [uid],
            'locationIdList': [20, 6, 15] if key == 'standard' else [10],
            'CanEscape': True, 'probabilityOfSuccessfulEscape': 100.0,
            'isResultSkipOnWin': False, 'isResultSkipOnLose': False,
            'ap': donor['ap'] if ap is None else ap}})
    prepare_practice_dialog(table, rows, woman)
    # The ordinary plains stage uses preloaded streaming levels. Mitra has no
    # battle sublevels, so choosing that ID alone cannot supply a backdrop.
    # Instance-load a private clone of its existing lighting/background levels;
    # keep the shared plains row and every normal encounter unchanged. Patch
    # both tables so runtime composite reconstruction retains the private stage.
    for rel in (STAGE, STAGE_COMPOSITE):
        table(rel)['add'].append({'row': PRACTICE, 'cloneFrom': plains[0][0], 'set': {
            'ID': PRACTICE_ID, 'isLoadLevelInstance': True}})
    for rel in (MAP, MAP_COMPOSITE):
        table(rel)['set'].append({'row': '01Gra_20', 'set': {'battleStage': PRACTICE_ID}})


def expected_edits(root, units, rows):
    tables = verification_operations(root, units, rows)
    expected = {}
    for rel, table in tables.items():
        original = rows(rel)
        for e in table['add']:
            if e['row'] in original:
                desired = apply_fields(original[e['cloneFrom']], e['set'])
                expected[(rel, e['row'])] = field_delta(original[e['row']], desired)
        for e in table['set']: expected.setdefault((rel, e['row']), {}).update(e['set'])
    return expected


def prepare_practice_dialog(table, rows, woman):
    """Native paged choice dialog; each branch is a private story-free event."""
    parent, composite, choices = rows(SHOP_EVENT), rows(COMPOSITE), rows(CHOICES)
    inn_key = 'DT_Town_010Gra_20_0920_5'
    inn = parent.get(inn_key)
    if not inn or composite.get(inn_key) != inn or not inn.get('ChoicesBranchEventList'):
        raise ValueError('The native choice branch template is unavailable.')
    link_key = 'DT_Town_010Gra_20_0930_1'
    link = parent.get(link_key)
    if not link or composite.get(link_key) != link or not link.get('ContinuousEventList'):
        raise ValueError('The native continuous-event template is unavailable.')
    templates = [(k, v) for k, v in choices.items() if v.get('ChoiceTextList')]
    if not templates:
        raise ValueError('The native choice dialog template is unavailable.')
    choice_key = templates[0][0]
    def event(name, updates):
        if name in parent or name in composite: raise ValueError('Practice dialog identity conflict.')
        desired = apply_fields(woman, {'TalkEventDataTable': 'None', 'EventSequence': 'None',
            'ChoicesBranchEventList': [], 'ContinuousEventList': [], **updates})
        edits = field_delta(inn, desired)
        for rel in (SHOP_EVENT, COMPOSITE):
            table(rel)['add'].append({'row': name, 'cloneFrom': inn_key, 'set': copy.deepcopy(edits)})
    pages = (len(OPPONENTS) + 1) // 2
    for page in range(pages):
        name = PRACTICE + '_Menu_' + chr(65 + page)
        tag = 'UI.Dialog.Choice.' + name
        if name in choices: raise ValueError('Practice choice identity conflict.')
        pair = OPPONENTS[page*2:page*2+2]
        table(CHOICES)['add'].append({'row': name, 'cloneFrom': choice_key, 'set': {
            'ChoiceTag.TagName': tag, 'ChoiceTextList': [p[1] for p in pair] + [
                'More opponents (' + str((page+1) % pages + 1) + '/' + str(pages) + ')', 'Cancel'],
            'DefaultIndex': 0, 'CancelIndex': len(pair) + 1, 'ChoiceDialogType': 'Normal'}})
        targets = [PRACTICE + '_' + p[0] for p in pair] + [PRACTICE + '_Menu_' + chr(65 + (page+1) % pages)]
        event(name, {'EventSequence': (CHOICE_FOLDER + 'SEQ_' + name).replace('FFRS/Content/', '/Game/'),
            'ChoicesBranchEventList': [{'Index': i, 'EventList': [{'Condition': '', 'EventId': target}]}
                                       for i, target in enumerate(targets)]})
    for index, (key, _, _, _) in enumerate(OPPONENTS):
        event(PRACTICE + '_' + key, {'encountGroupId': PRACTICE_ID + index})
    # ffr-dt cannot create structs in an empty array. Replace this existing
    # row from a populated continuous-event donor, then restore EVERY field
    # of the original woman except our unconditional menu link. In particular,
    # none of the donor's quest flags, progress or request changes may survive.
    desired = apply_fields(woman, {
        'ContinuousEventList': [{'Condition': '', 'EventId': PRACTICE + '_Menu_A'}]})
    for rel in (SHOP_EVENT, COMPOSITE):
        table(rel)['add'].append({'row': SHOP_WOMAN, 'cloneFrom': link_key,
                                 'set': field_delta(link, desired)})


def author_practice_choice(asset, tag):
    """An unbound native talk-director track: open choices, wait, finish.

    Use the small event-only shell, not a story sequence with actors/cameras.
    The native talk manager records the choice and dispatches the event branches.
    """
    import ffbe_resonance as seq
    seq.author(asset, {'duration': 1200, 'events': [
        {'time': 0, 'set': {'EventType': 'OtherReaction'}},
        {'time': 400, 'set': {'EventType': 'UnitPlayAnimByName'}}]})
    imports, exports = asset['Imports'], asset['Exports']
    def cls(e): return imports[-e['ClassIndex']-1]['ObjectName'] if e['ClassIndex'] < 0 else ''
    native_outer = next(i['OuterIndex'] for i in imports if i['ObjectName'] == 'CPP_BtlLevelSequenceDirector')
    for item in imports:
        if item['ObjectName'] == 'BP_BtlLevelSequenceDirector_C':
            item.update(ObjectName='CPP_TalkEventSequenceDirector', OuterIndex=native_outer,
                        ClassPackage='/Script/CoreUObject', ClassName='Class')
        elif item['ObjectName'] == 'Default__BP_BtlLevelSequenceDirector_C':
            item.update(ObjectName='Default__CPP_TalkEventSequenceDirector', OuterIndex=native_outer,
                        ClassPackage='/Script/mucha', ClassName='CPP_TalkEventSequenceDirector')
    director = next(i+1 for i, v in enumerate(imports) if v['ObjectName'] == 'CPP_TalkEventSequenceDirector')
    def imp(name, outer, class_name='Object'):
        imports.append({'$type': 'UAssetAPI.Import, UAssetAPI', 'ObjectName': name, 'OuterIndex': outer,
            'ClassPackage': '/Script/CoreUObject', 'ClassName': class_name, 'PackageName': None, 'bImportOptional': False})
        return -len(imports)
    open_choice, wait = imp('OpenChoiceDialog', -director), imp('DialogWait', -director)
    tag_struct = next((-i-1 for i, v in enumerate(imports) if v['ObjectName'] == 'GameplayTag'), None)
    if tag_struct is None:
        tags_package = imp('/Script/GameplayTags', 0, 'Package')
        tag_struct = imp('GameplayTag', tags_package, 'ScriptStruct')
    def expression(name, **kwargs):
        return {'$type': 'UAssetAPI.Kismet.Bytecode.Expressions.' + name + ', UAssetAPI', **kwargs}
    ending = [expression('EX_Return', ReturnExpression=expression('EX_Nothing')), expression('EX_EndOfScript')]
    # Remove every inherited battle-event call, including unscheduled functions.
    for e in exports:
        if cls(e) == 'Function':
            e['ScriptBytecode'] = copy.deepcopy(ending); e['ScriptBytecodeRaw'] = None
            e['ScriptBytecodeSize'] = 3
            e['LoadedProperties'] = []
        elif e['ObjectName'].startswith('Default__'):
            e['Data'] = []
    scene, = [e for e in exports if cls(e) == 'MovieScene']
    root, = [e for e in exports if cls(e) == 'LevelSequence']
    # JSON does not preserve UniversalObjectLocator's private state. This
    # sequence deliberately has no actors: remove the locator completely.
    references = seq.child(root['Data'], 'BindingReferences')
    seq.replace_array(seq.prop(references, 'SortedReferences'), [])
    binding, = seq.child(scene['Data'], 'ObjectBindings')
    tracks = copy.deepcopy(seq.prop(binding['Value'], 'Tracks'))
    scene['Data'].append(tracks)
    seq.replace_array(seq.prop(scene['Data'], 'ObjectBindings'), [])
    seq.replace_array(seq.prop(scene['Data'], 'Possessables'), [])
    section = next(e for e in exports if cls(e) == 'MovieSceneEventTriggerSection'
        and any(p['Name'] == 'EventChannel' and seq.child(p['Value'], 'KeyValues') for p in e['Data']))
    values = seq.child(section['Data'], 'EventChannel', 'KeyValues')
    for i, value in enumerate(values):
        ptrs = seq.child(value['Value'], 'Ptrs')
        fn = seq.child(ptrs, 'Function')
        pointer = seq.prop(ptrs, 'BoundObjectProperty')['Value']
        pointer.update(Path=[], ResolvedOwner=0)
        params = [] if i else [expression('EX_StructConst', Struct=tag_struct, StructSize=12,
            Value=[expression('EX_NameConst', Value=tag)])]
        exports[fn-1]['ScriptBytecode'] = [expression('EX_FinalFunction', StackNode=wait if i else open_choice,
                                                     Parameters=params), *copy.deepcopy(ending)]
        exports[fn-1]['ScriptBytecodeSize'] = 13 if i else 40
        exports[fn-1]['CreateBeforeSerializationDependencies'] = [wait] if i else [open_choice, tag_struct]
    compiled, = [e for e in exports if cls(e) == 'MovieSceneCompiledData']
    metadata = seq.child(compiled['Data'], 'EntityComponentField', 'SharedMetaData')[0]['Value']
    seq.child(metadata, 'ObjectBindingID')[0]['Value'] = '{00000000-0000-0000-0000-000000000000}'
    for name in ('CPP_TalkEventSequenceDirector', 'Default__CPP_TalkEventSequenceDirector',
                 '/Script/mucha', '/Script/GameplayTags', 'Class', 'ScriptStruct', 'OpenChoiceDialog', 'DialogWait', 'GameplayTag', tag):
        if name not in asset['NameMap']: asset['NameMap'].append(name)
    # IoStore preserves only this prefix, leaving script FName indices intact.
    # The inherited shell retained 36 names; our choice tag is appended at 79.
    # Keep every name, in its original order, so the runtime can load the call.
    asset['NamesReferencedFromExportDataCount'] = len(asset['NameMap'])
    return asset


def build_practice(env):
    if not settings(env['ROOT'])['practiceBattle']: return
    import _ffr_fina_boss
    _ffr_fina_boss.build(env)
    build_choices(env, [PRACTICE + '_Menu_' + chr(65 + page)
        for page in range((len(OPPONENTS)+1)//2)], CHOICE_FOLDER, 'practice-dialog')
    print(f'  Shop practice: {(len(OPPONENTS)+1)//2} native choice pages, {len(OPPONENTS)} opponents, cancel without battle.')


def build_choices(env, names, folder, work_label):
    """Build private native dialogs and verify their cooked director bindings."""
    import ffbe_resonance as seq
    legacy, out, work = Path(env['LEGACY']), Path(env['OUT']), Path(env['BUILD']) / work_label
    shell = legacy / (seq.SHELL + '.uasset')
    if not shell.is_file():
        env['run'](env['ffrenv'].py(str(Path(env['ROOT'])/'tools/extract_legacy.py'),
                                   '--filter', 'Sequencer/Battle/Skill/440110/440111/'))
    if not shell.is_file(): raise ValueError('The practice choice sequence template is unavailable.')
    work.mkdir(parents=True, exist_ok=True)
    for name in names:
        destination = folder + 'SEQ_' + name
        patch = work / (name + '-clone.json')
        patch.write_text(json.dumps({'legacyRoot': str(legacy), 'outRoot': str(out), 'clones': [{
            'from': seq.SHELL, 'to': destination, 'rename': [['SEQ_Battle_440111_Cut_000', 'SEQ_' + name]]}]}), encoding='utf-8')
        env['run']([*env['FFRDT'], 'patch', str(patch), '--usmap', env['USMAP']])
        dump = work / (name + '.json')
        env['run']([*env['FFRDT'], 'tojson', str(out/(destination+'.uasset')), str(dump), '--usmap', env['USMAP']])
        asset = author_practice_choice(json.loads(dump.read_text(encoding='utf-8-sig')), 'UI.Dialog.Choice.' + name)
        dump.write_text(json.dumps(asset, ensure_ascii=False), encoding='utf-8')
        env['run']([*env['FFRDT'], 'fromjson', str(dump), str(out/(destination+'.uasset')), '--usmap', env['USMAP']])
        env['run']([*env['FFRDT'], 'tojson', str(out/(destination+'.uasset')), str(dump), '--usmap', env['USMAP']])
        verify_practice_choice(json.loads(dump.read_text(encoding='utf-8-sig')), 'UI.Dialog.Choice.' + name)


def verify_practice_choice(asset, tag):
    import ffbe_resonance as seq
    count = asset.get('NamesReferencedFromExportDataCount')
    if (type(count) is not int or not 0 < count <= len(asset['NameMap'])
            or tag not in asset['NameMap'][:count]):
        raise ValueError('Practice choices would lose script names during IoStore packing.')
    exports, imports = asset['Exports'], asset['Imports']
    def cls(e): return imports[-e['ClassIndex']-1]['ObjectName'] if e['ClassIndex'] < 0 else ''
    director, = [e for e in exports if cls(e) == 'BlueprintGeneratedClass']
    if director['SuperStruct'] >= 0 or imports[-director['SuperStruct']-1]['ObjectName'] != 'CPP_TalkEventSequenceDirector':
        raise ValueError('Practice choices lost their native talk director.')
    scene, = [e for e in exports if cls(e) == 'MovieScene']
    if seq.child(scene['Data'], 'ObjectBindings') or seq.child(scene['Data'], 'Possessables'):
        raise ValueError('Practice choices retained an actor binding.')
    track, = seq.child(scene['Data'], 'Tracks')
    section_ref, = seq.child(exports[track['Value']-1]['Data'], 'Sections')
    channel = seq.child(exports[section_ref['Value']-1]['Data'], 'EventChannel')
    def number(v):
        while isinstance(v, (dict, list)): v = v['Value'] if isinstance(v, dict) else v[0]
        return v
    if [number(t) for t in seq.child(channel, 'KeyTimes')] != [0, 400]:
        raise ValueError('Practice choice event times changed.')
    values = seq.child(channel, 'KeyValues')
    if len(values) != 2: raise ValueError('Practice choice event count changed.')
    for index, value in enumerate(values):
        ptrs = seq.child(value['Value'], 'Ptrs')
        if seq.child(ptrs, 'BoundObjectProperty')['Path']:
            raise ValueError('Practice choice still requires a battle actor.')
        code = exports[seq.child(ptrs, 'Function')-1]['ScriptBytecode']
        call = code[0]
        if (not call['$type'].split(',')[0].endswith('EX_FinalFunction')
                or imports[-call['StackNode']-1]['ObjectName'] != ('DialogWait' if index else 'OpenChoiceDialog')
                or len(code) != 3):
            raise ValueError('Practice choice lost its native open/wait call.')
        if not index and call['Parameters'][0]['Value'][0]['Value'] != tag:
            raise ValueError('Practice choices reference the wrong page.')
    compiled, = [e for e in exports if cls(e) == 'MovieSceneCompiledData']
    field = seq.child(compiled['Data'], 'EntityComponentField')
    if seq.child(seq.child(field, 'SharedMetaData')[0]['Value'], 'ObjectBindingID')[0]['Value'] != '{00000000-0000-0000-0000-000000000000}':
        raise ValueError('Practice choice compiled metadata retained a battle actor.')
    nodes = seq.child(field, 'OneShotEntityTree')[0]['Value']['SerializedData']['ChildNodes']['Items']
    if len(seq.child(field, 'Entities')) != 2 or [n['Range']['LowerBound']['Value']['Value'] for n in nodes] != [0, 400]:
        raise ValueError('Practice choice compiled playback times changed.')


def field_delta(original, desired, prefix=''):
    changes = {}
    for key, value in desired.items():
        path = prefix + key
        if original[key] == value: continue
        # Talk-event ArgList is a native map, not a struct. ffr-dt updates
        # existing map keys through the whole property, never dotted paths.
        if isinstance(value, dict) and key != 'ArgList':
            changes.update(field_delta(original[key], value, path + '.'))
        else: changes[path] = copy.deepcopy(value)
    return changes


def apply_fields(row, fields):
    result = copy.deepcopy(row)
    def assign(current, value):
        # Native structs/maps update supplied fields/keys; struct arrays clone
        # their first element before applying each item's supplied fields.
        if isinstance(current, dict) and isinstance(value, dict):
            merged = copy.deepcopy(current)
            for key, item in value.items(): merged[key] = assign(current.get(key), item)
            return merged
        if isinstance(current, list) and isinstance(value, list):
            return [assign(current[0] if current else None, item) for item in value]
        return copy.deepcopy(value)
    for path, value in fields.items():
        target = result; names = path.split('.')
        for name in names[:-1]:
            match = re.fullmatch(r'(\w+)\[(\d+)\]', name)
            target = target[match[1]][int(match[2])] if match else target[name]
        match = re.fullmatch(r'(\w+)\[(\d+)\]', names[-1])
        if match:
            target[match[1]][int(match[2])] = assign(target[match[1]][int(match[2])], value)
        else:
            target[names[-1]] = assign(target.get(names[-1]), value)
    return result


def equivalent(a, b):
    """The native serializer can emit signed floating zero as a string."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equivalent(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equivalent(x, y) for x, y in zip(a, b))
    if type(a) is str and a in ('+0', '-0') and type(b) in (int, float): return b == 0
    if type(b) is str and b in ('+0', '-0') and type(a) in (int, float): return a == 0
    return a == b


def check_rows(original, built, operation, plan=None, finalize=None):
    expected = copy.deepcopy(original)
    # The shared table also contains imported visions, native edits and private
    # passives/effects from the rest of this build. Check their complete recipe,
    # then independently impose the testing settings recomputed from config.
    if plan is not None:
        for e in plan.get('add', []): expected[e['row']] = apply_fields(expected[e['cloneFrom']], e['set'])
        for e in plan.get('set', []): expected[e['row']] = apply_fields(expected[e['row']], e['set'])
    for e in operation['add']: expected[e['row']] = apply_fields(original[e['cloneFrom']], e['set'])
    for e in operation['set']: expected[e['row']] = apply_fields(expected[e['row']], e['set'])
    if finalize is not None: expected = finalize(expected)
    if not equivalent(built, expected):
        missing = sorted(expected.keys() - built.keys())
        extra = sorted(built.keys() - expected.keys())
        changed = sorted(k for k in expected.keys() & built.keys() if not equivalent(expected[k], built[k]))
        detail = '; '.join(f'{label}: {", ".join(keys[:5])}'
                           for label, keys in (('missing', missing), ('extra', extra), ('changed', changed)) if keys)
        raise ValueError('Studio testing changed an unrelated row or lost its grant/reward/battle settings. ' + detail)


def verify_table_recipe(root, tool, usmap):
    """Run acquisition/testing and shop checks before expensive asset work.

    Reuse the independent validators rather than interpreting every upstream
    patch field: native row export flattens hard references and wraps vectors.
    Later scene builders intentionally finalize some rows; the final verifier
    still checks their completed presentation and generated assets.
    """
    verify(root, tool, usmap, before_assets=True)
    import _ffr_crystal_cave
    _ffr_crystal_cave.verify_shops(root, tool, usmap)
    print('OK: acquisition/testing and shop tables checked before sprite conversion and packing', flush=True)


def verification_operations(root, units, rows):
    import _ffr_game_tables
    rows = _ffr_game_tables.reader(root, rows)
    operations = prepare({}, units, root, rows)
    import _ffr_overworld
    # The cave adds its NPC to the same table as party field replacements.
    # Verify their complete combined result rather than treating either as unrelated.
    if _ffr_overworld.TABLE in operations:
        _ffr_overworld.prepare(operations, [u for u in units if u.get('party')], rows)
    return _ffr_game_tables.normalize(root, operations, rows)


def verify(root, tool, usmap, *, before_assets=False):
    root = Path(root)
    units = json.loads((root / 'mods/EstherTsukiko/units.json').read_bytes())
    import _ffr_sephira
    def rows(rel): return json.loads((root / 'extracted/rows' / (rel + '.json')).read_bytes())['rows']
    # Recompute the same ephemeral visual/acquisition choices as the builder.
    # Saved recipes deliberately retain borrowed donors and normal locations.
    import _ffr_game_tables
    units = _ffr_sephira.visual_units(_ffr_sephira.active_units(units), root,
                                     _ffr_game_tables.reader(root, rows))
    units = _ffr_sephira.player_units(units, _ffr_game_tables.reader(root, rows))
    operations = verification_operations(root, units, rows)
    plans = []
    if operations:
        try: plans = json.loads((root / 'build/visions_mod/patch.json').read_bytes())['tables']
        except (OSError, ValueError, KeyError) as error:
            raise ValueError('The complete build recipe is unavailable; rebuild the mod before verifying testing tables.') from error
    work = root / 'build/vision-testing'; work.mkdir(parents=True, exist_ok=True)
    for rel, operation in operations.items():
        matches = [plan for plan in plans if plan['asset'] == operation['asset']]
        if len(matches) != 1:
            raise ValueError('The build recipe must contain one testing table: ' + rel)
        target = work / (rel.replace('/', '_') + '.json')
        _ffr_build_cache.subprocess_run(tool + ['rows', str(root / 'build/visions_mod/assets' / (operation['asset'] + '.uasset')),
                               str(target), '--usmap', usmap], check=True, capture_output=True)
        try:
            import _ffr_fina_boss
            import _ffr_shrine_challenges
            def finalize(expected):
                if before_assets and rel not in _ffr_fina_boss.AI_ASSETS:
                    return expected
                return _ffr_shrine_challenges.final_rows(rel,
                    _ffr_fina_boss.final_rows(rel, expected, units, root), units, root)
            check_rows(rows(rel), json.loads(target.read_text(encoding='utf-8-sig'))['rows'],
                       operation, matches[0], finalize)
        except ValueError as error:
            raise ValueError(f'{rel}: {error}') from error
    if operations: print('OK: original vision acquisition, MR and shop battle testing tables verified')


def register(app, env):
    from fastapi import HTTPException
    import _ffr_fina_cinematic
    _ffr_fina_cinematic.register(app, env)
    @app.get('/api/testing')
    def get_settings():
        try: return settings(env['ROOT'])
        except (OSError, ValueError) as e: raise HTTPException(422, str(e)) from e
    @app.put('/api/testing')
    def put_settings(value: dict):
        try:
            for flag in ('practiceBattle', 'practiceEncounter', 'surviveAtOne', 'ffbeNeedles', 'finaCinematic', 'crystalCave', 'crystalCaveTest', 'fieldLeader'):
                if flag not in value:
                    value = dict(value, **{flag: settings(env['ROOT'])[flag]})
            value = validate_settings(value)
            # Same build-state lock used by the roster API, when available.
            if env.get('state', {}).get('running'):
                raise ValueError('Wait for the current build to finish.')
            path = Path(env['ROOT']) / CONFIG; path.parent.mkdir(parents=True, exist_ok=True)
            if any(value[flag] for flag in ('maxMr', 'practiceBattle', 'surviveAtOne', 'ffbeNeedles', 'crystalCave', 'crystalCaveTest', 'fieldLeader')):
                # An explicit empty roster prevents the engine's legacy five-unit
                # fallback when MR testing is the only requested mod. Never overwrite.
                spec = path.parent / 'units.json'
                try:
                    with spec.open('x', encoding='utf-8') as f: json.dump([], f)
                except FileExistsError: pass
            fd, temp = tempfile.mkstemp(prefix='testing-', dir=path.parent)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f: json.dump(value, f); f.flush(); os.fsync(f.fileno())
                os.replace(temp, path)
            finally:
                if os.path.exists(temp): os.unlink(temp)
            return value
        except (OSError, ValueError) as e: raise HTTPException(422, str(e)) from e
