"""Opt-in original vision grants, bounded MR and a repeatable shop battle."""
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


def settings(root):
    path = Path(root) / CONFIG
    return validate_settings(json.loads(path.read_bytes())) if path.is_file() else {
        'schema': 1, 'maxMr': False, 'practiceBattle': False}


def validate_settings(value):
    if (not isinstance(value, dict) or not {'schema', 'maxMr'} <= set(value)
            or set(value) - {'schema', 'maxMr', 'practiceBattle'}
            or type(value['schema']) is not int or value['schema'] != 1 or type(value['maxMr']) is not bool
            or type(value.get('practiceBattle', False)) is not bool):
        raise ValueError('Invalid vision testing settings.')
    return {'schema': 1, 'maxMr': value['maxMr'], 'practiceBattle': value.get('practiceBattle', False)}


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
    if controls['practiceBattle']:
        prepare_practice(table, rows, value)
    return tables


def prepare_practice(table, rows, ap):
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
            or town.get('doMovementEncount') or town.get('battleStage') != -1
            or not any(v.get('ID') == 5 and v.get('battleLevelList')
                       for v in rows('Asset/Battle/Stage/CDT_BtlStageAsset_Demo').values())):
        raise ValueError('The Mitra map or native plains battle stage is unavailable.')
    groups = rows(GROUP)
    donor = next(((k, v) for k, v in groups.items() if v.get('ID') == 1026), None)
    if (PRACTICE in groups or any(v.get('ID') == PRACTICE_ID for v in groups.values()) or not donor
            or donor[1].get('UnitIdList') != [20, 22, 22] or len(donor[1].get('locationIdList', [])) != 3
            or donor[1].get('battleEventId') != -1 or donor[1].get('battleFinishEventId')
            or donor[1].get('battleFinishEscapeEventId') or donor[1].get('battleFinishLoseEventId')
            or donor[1]['battleFinishTransition']['mapId'] != -1
            or donor[1]['battleFinishTransition'].get('bDoAutoSave')):
        raise ValueError('The native three-enemy encounter template changed.')
    units = rows('Unit/DT_UnitParameter')
    for uid, level in ((20, 7), (22, 8)):
        enemies = [v for v in units.values() if v.get('ID') == uid]
        if len(enemies) != 1 or enemies[0].get('Category') != 'Enemy' or enemies[0].get('Level') != level:
            raise ValueError('The native level 7–8 practice enemies are unavailable.')
    for rel in (SHOP_EVENT, COMPOSITE):
        table(rel)['set'].append({'row': SHOP_WOMAN, 'set': {'encountGroupId': PRACTICE_ID}})
    # Mitra normally has no battle backdrop. Supply the demo's existing plains
    # stage without enabling random encounters or changing the shop/map actors.
    for rel in (MAP, MAP_COMPOSITE):
        table(rel)['set'].append({'row': '01Gra_20', 'set': {'battleStage': 5}})
    table(GROUP)['add'].append({'row': PRACTICE, 'cloneFrom': donor[0], 'set': {
        'ID': PRACTICE_ID, 'CanEscape': True, 'probabilityOfSuccessfulEscape': 100.0,
        'isResultSkipOnWin': False, 'isResultSkipOnLose': False,
        'ap': donor[1]['ap'] if ap is None else ap}})


def expected_edits(root, units, rows):
    tables = prepare({}, units, root, rows)
    return {(rel, e['row']): e['set'] for rel, t in tables.items() for e in t['set']}


def field_delta(original, desired, prefix=''):
    changes = {}
    for key, value in desired.items():
        path = prefix + key
        if original[key] == value: continue
        if isinstance(value, dict): changes.update(field_delta(original[key], value, path + '.'))
        else: changes[path] = copy.deepcopy(value)
    return changes


def apply_fields(row, fields):
    result = copy.deepcopy(row)
    for path, value in fields.items():
        target = result; names = path.split('.')
        for name in names[:-1]:
            match = re.fullmatch(r'(\w+)\[(\d+)\]', name)
            target = target[match[1]][int(match[2])] if match else target[name]
        target[names[-1]] = copy.deepcopy(value)
    return result


def check_rows(original, built, operation):
    expected = copy.deepcopy(original)
    for e in operation['set']: expected[e['row']] = apply_fields(expected[e['row']], e['set'])
    for e in operation['add']: expected[e['row']] = apply_fields(original[e['cloneFrom']], e['set'])
    if built != expected:
        raise ValueError('Studio testing changed an unrelated row or lost its grant/reward/battle settings.')


def verify(root, tool, usmap):
    root = Path(root)
    units = json.loads((root / 'mods/EstherTsukiko/units.json').read_bytes())
    def rows(rel): return json.loads((root / 'extracted/rows' / (rel + '.json')).read_bytes())['rows']
    operations = prepare({}, units, root, rows)
    work = root / 'build/vision-testing'; work.mkdir(parents=True, exist_ok=True)
    for rel, operation in operations.items():
        target = work / (rel.replace('/', '_') + '.json')
        subprocess.run(tool + ['rows', str(root / 'build/visions_mod/assets' / (operation['asset'] + '.uasset')),
                               str(target), '--usmap', usmap], check=True, capture_output=True)
        check_rows(rows(rel), json.loads(target.read_text(encoding='utf-8-sig'))['rows'], operation)
    if operations: print('OK: original vision acquisition, MR and shop battle testing tables verified')


def register(app, env):
    from fastapi import HTTPException
    @app.get('/api/testing')
    def get_settings():
        try: return settings(env['ROOT'])
        except (OSError, ValueError) as e: raise HTTPException(422, str(e)) from e
    @app.put('/api/testing')
    def put_settings(value: dict):
        try:
            if 'practiceBattle' not in value:
                value = dict(value, practiceBattle=settings(env['ROOT'])['practiceBattle'])
            value = validate_settings(value)
            # Same build-state lock used by the roster API, when available.
            if env.get('state', {}).get('running'):
                raise ValueError('Wait for the current build to finish.')
            path = Path(env['ROOT']) / CONFIG; path.parent.mkdir(parents=True, exist_ok=True)
            if value['maxMr'] or value['practiceBattle']:
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
