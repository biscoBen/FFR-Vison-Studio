"""Opt-in clean-save testing with original vision items and bounded native AP."""
import copy
import json
import os
import re
from pathlib import Path
import subprocess
import tempfile

GROUP = 'Encount/DT_BattleGroup'
EVENT = 'Event/TalkEvent/CDT_TalkEventData_Demo'
COMMON = 'Event/BattleEvent/DT_BtlCmnEventDataBundle'
NAME = 'Studio_TestNativeVisions'
CONFIG = 'mods/EstherTsukiko/testing.json'


def settings(root):
    path = Path(root) / CONFIG
    return validate_settings(json.loads(path.read_bytes())) if path.is_file() else {'schema': 1, 'maxMr': False}


def validate_settings(value):
    if (not isinstance(value, dict) or set(value) != {'schema', 'maxMr'}
            or type(value['schema']) is not int or value['schema'] != 1 or type(value['maxMr']) is not bool):
        raise ValueError('Invalid vision testing settings.')
    return value


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
        events = rows(EVENT); common = rows(COMMON)
        if NAME in events or NAME in common:
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
        if not grant.get('ObtainItemList'):
            raise ValueError('The native vision-grant template is unavailable.')
        desired = apply_fields(donor, updates)
        updates = field_delta(grant, desired)
        table(EVENT)['add'].append({'row': NAME, 'cloneFrom': 'C01_014_03', 'set': updates})
        key, source = next((k, v) for k, v in common.items() if v['eventCondition'] == 'BattleBegin')
        event = copy.deepcopy(source['eventDataList'][0])
        if len(source['eventDataList']) != 1 or len(event['playSetting']['EventList']) != 1 or event['ParameterList']:
            raise ValueError('The native common battle-event template changed.')
        event['playSetting']['Condition'] = '|'.join(f'{{item:{vid}}}==0' for vid in sorted(selected))
        event['playSetting']['EventList'][0]['EventId'] = NAME
        table(COMMON)['add'].append({'row': NAME, 'cloneFrom': key, 'set': {
            'eventDataList[0].playSetting.Condition': event['playSetting']['Condition'],
            'eventDataList[0].playSetting.EventList[0].EventId': NAME}})
    if settings(root)['maxMr']:
        value = reward(rows)
        for key, original in rows(GROUP).items():
            if type(original.get('ap')) is not int:
                raise ValueError('A native battle MR reward is missing.')
            table(GROUP)['set'].append({'row': key, 'set': {'ap': value}})
    return tables


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
        raise ValueError('Native vision testing changed an unrelated row or lost its grant/reward settings.')


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
    if operations: print('OK: original vision acquisition and bounded MR testing tables verified')


def register(app, env):
    from fastapi import HTTPException
    @app.get('/api/testing')
    def get_settings():
        try: return settings(env['ROOT'])
        except (OSError, ValueError) as e: raise HTTPException(422, str(e)) from e
    @app.put('/api/testing')
    def put_settings(value: dict):
        try:
            value = validate_settings(value)
            # Same build-state lock used by the roster API, when available.
            if env.get('state', {}).get('running'):
                raise ValueError('Wait for the current build to finish.')
            path = Path(env['ROOT']) / CONFIG; path.parent.mkdir(parents=True, exist_ok=True)
            if value['maxMr']:
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
