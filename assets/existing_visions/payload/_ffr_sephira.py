"""Keep optional Sephira presets editable while excluding disabled entries from builds."""

import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile

FIELD = 'sephiraVision'
RETIRED = {'great_dragon'}
PASSIVE = 'Skill/DT_PassiveSkillData'
EFFECT = 'Skill/DT_SkillEffectData'
CONFIG = 'mods/EstherTsukiko/sephira-settings.json'


def validate_settings(value):
    required = {'schema', 'useBorrowedSkillVisuals'}
    if (not isinstance(value, dict) or not required <= set(value)
            or set(value) - required - {'shopAcquisitionOverride'}
            or type(value['schema']) is not int or value['schema'] != 1
            or type(value['useBorrowedSkillVisuals']) is not bool
            or ('shopAcquisitionOverride' in value and type(value['shopAcquisitionOverride']) is not bool)):
        raise ValueError('Invalid Sephira skill visual settings.')
    return dict(value)


def settings(root):
    path = Path(root) / CONFIG
    return validate_settings(json.loads(path.read_bytes())) if path.is_file() else {
        'schema': 1, 'useBorrowedSkillVisuals': True}


def visual_units(units, root, rows=None):
    """Choose original visual sources only in the ephemeral build specification.

    Match known preset source/donor pairs, independent of allocated private IDs
    and recipe revisions. Preserve explicitly edited donors and authored sequences.
    Saved recipes keep the borrowed donors so turning the setting on restores them.
    """
    result = copy.deepcopy(units)
    controls = settings(root)
    if controls.get('shopAcquisitionOverride', False):
        for unit in result:
            value = membership(unit)
            if value is not None and value['enabled'] and value['preset'] not in RETIRED:
                unit['studioAcquisition'] = {'version': 1, 'location': 'mitra_shop',
                                            'random': False, 'hideSpoilers': True}
                unit['price'] = 1
    if controls['useBorrowedSkillVisuals']:
        return result
    policy = json.loads(Path(__file__).with_name('sephira_visuals.json').read_bytes())
    if policy.get('schema') != 1:
        raise ValueError('Unsupported Sephira visual policy.')
    sources = {v['ID']: v for v in rows('Skill/DT_SkillData').values()} if rows else {}
    for unit in result:
        value = membership(unit)
        if value is None:
            continue
        donors = policy['presets'].get(value['preset'], {})
        for recipe in (unit.get('skills') or {}).values():
            if (not recipe or recipe.get('clone_sequence')
                    or recipe.get('tint') is not None or recipe.get('motion')
                    or str(recipe.get('from')) not in donors
                    or recipe.get('visuals') != donors.get(str(recipe.get('from')))):
                continue
            recipe['visuals'] = recipe['from']
            # Some native sources play a shared sequence without owning an asset
            # row. Remove only our default pointer overrides, retaining any
            # explicit user-selected pointer and every combat setting.
            source = sources.get(recipe['from'], {})
            for field in ('playSequencerId', 'sequencerIdWhenTargetFriendlies'):
                if field in source and (recipe.get('set') or {}).get(field) == -1:
                    recipe['set'][field] = source[field]
            # A missing demo source must stay missing even with library repairs
            # enabled. A newly available native source timeline still wins.
            recipe['_sephiraSourceVisuals'] = True
    return result


def register(app, env):
    from fastapi import HTTPException

    @app.get('/api/sephira/settings')
    def get_settings():
        try: return settings(env['ROOT'])
        except (OSError, ValueError) as e: raise HTTPException(422, str(e)) from e

    @app.put('/api/sephira/settings')
    def put_settings(value: dict):
        try:
            value = validate_settings(value)
            current = settings(env['ROOT'])
            if 'shopAcquisitionOverride' not in value and 'shopAcquisitionOverride' in current:
                value['shopAcquisitionOverride'] = current['shopAcquisitionOverride']
            if env.get('state', {}).get('running'):
                raise ValueError('Wait for the current build to finish.')
            path = Path(env['ROOT']) / CONFIG
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix='sephira-settings-', dir=path.parent)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(value, f); f.flush(); os.fsync(f.fileno())
                os.replace(temporary, path)
            finally:
                Path(temporary).unlink(missing_ok=True)
            return value
        except (OSError, ValueError) as e: raise HTTPException(422, str(e)) from e

# Effect ID, semantic type, parameter index, original value, replacement kind.
# These are identified command/LB fields, not a search/replace of all numbers.
BINDINGS = {
    1406: (15125, 'AddBaseBreakDmg', 1, 200, 'command'),
    1410: (19024, 'DominantPower', 0, 102, 'command'),
    1411: (12902, 'DamageMultiplier', 2, 102, 'command'),
    1418: (12206, 'CriticalRateVariation', 5, 440110, 'lb'),
    1420: (13103, 'CriticalRateVariation', 6, 110, 'command'),
    1432: (61000, 'CostVariation', 4, 123, 'command'),
    1433: (12926, 'DmgMulRetaliation', 3, 440240, 'lb'),
    1443: (54220, 'RepeatAction', 7, 202, 'command'),
    1448: (12942, 'AquaTerraSword', 1, 205, 'command'),
    1454: (15127, 'BreakDmgByProtect', 1, 207, 'command'),
}


# Saved-game compatibility: freeze the preset/conditional seeds and existing
# label positions. Append later explicit labels only within their reserved range.
# Skill IDs 1000..1999 are passive IDs; command/active/master
# lookups classify IDs before searching their respective native tables.
_PASSIVE_PRESETS = ('a2', 'christine', 'crystal_fina', 'barusa', 'fran', 'lunafreya', 'minfilia', 'folka', 'fryevia', 'lenneth', 'lila', 'mystea', 'reberta', 'snow_white', 'aria', 'eiko', 'alice', 'mog', 'lilith', 'freya', 'trance_terra', 'ariana', 'elephim', 'jade', 'primm', 'relm', 'rikku', 'nalu', 'elza', 'lunera')
_PASSIVE_CONDITIONALS = (1406, 1410, 1411, 1418, 1420, 1432, 1433, 1443, 1448, 1454)
_PASSIVE_LABELS = (('crystal_fina', 1551), ('crystal_fina', 1552), ('lunafreya', 1510), ('lunafreya', 1517), ('folka', 1535), ('fryevia', 1522), ('mystea', 1530), ('mystea', 1274), ('mystea', 1513), ('reberta', 1507), ('aria', 1527), ('aria', 1519), ('eiko', 1498), ('eiko', 1373), ('alice', 1481), ('alice', 1531), ('mog', 1511), ('freya', 1529), ('freya', 1516), ('freya', 1497), ('freya', 1539), ('trance_terra', 1532), ('ariana', 1515), ('ariana', 1499), ('ariana', 1518), ('primm', 1521), ('primm', 1525), ('relm', 1500), ('rikku', 1009), ('nalu', 1523), ('nalu', 1537), ('nalu', 1496), ('elza', 1528), ('elza', 1495), ('elza', 1506), ('elza', 1276), ('lunera', 1051))
_PASSIVE_KEYS = [(preset, sid) for preset in _PASSIVE_PRESETS for sid in _PASSIVE_CONDITIONALS] + list(_PASSIVE_LABELS)
_PRIVATE_PASSIVES = {key: 1600 + index for index, key in enumerate(_PASSIVE_KEYS)}
_FALLBACK_FIRST = 1970


def private_passive_id(preset, source):
    key = (preset, source)
    if key in _PRIVATE_PASSIVES: return _PRIVATE_PASSIVES[key]
    # Preserve support for explicitly edited/imported membership names without
    # reassigning any bundled preset when another preset is disabled.
    import hashlib
    first = _FALLBACK_FIRST
    return first + int.from_bytes(hashlib.sha256(f'{preset}:{source}'.encode()).digest()[:4], 'big') % (2000 - first)


def player_units(units, rows):
    """Normalize private learned commands and pure healing outside battle.

    Saved recipes, IDs, numeric power/cost and the native donors stay unchanged.
    Explicit edits to these presentation/availability fields retain precedence.
    """
    result = copy.deepcopy(units)
    selected = [u for u in result if membership(u) is not None and u.get('skills')]
    if not selected: return result
    native = {r['ID']: r for r in rows('Skill/DT_SkillData').values()}
    for unit in selected:
        learned = {g[1] for tier in unit.get('synchro', []) for g in tier if g[0] == 'ActiveSkill'}
        command = unit['command']['id']
        for identity, recipe in unit['skills'].items():
            source = native.get(recipe.get('from'))
            if not source or recipe.get('resonance'): continue
            import _ffr_sephira_ffbe
            if _ffr_sephira_ffbe.selected(unit, recipe): recipe['visuals'] = recipe['from']
            fields = recipe.setdefault('set', {})
            if int(identity) in learned and fields.get('belongCommandList') == [command]:
                fields['belongCommandList'] = [1]
                if fields.get('commandIdBelongDebuggingAllSkills') == [command, -1]:
                    fields['commandIdBelongDebuggingAllSkills'] = [901 if source.get('skillAttrType') == 'Magic' else 900, -1]
            effective = dict(source, **fields)
            if (effective.get('skillEffectType') == 'DamageAndRecovery'
                    and effective.get('parameterVariationType') == 'Increase'
                    and effective.get('parameterType') == 'HitPoint'
                    and effective.get('defaultTargetRelation') == 'Friendlies'
                    and effective.get('defaultTargetState') == 'Alive'
                    and effective.get('damageCalcType') in ('Magic', 'Fixed', 'TargetMaxHPRatio')):
                fields.setdefault('availableLocation', 'Anywhere')
                fields.setdefault('mapEffectType', 'RecoveryHP')
                fields.setdefault('isTargetIgnoreSelf', False)
                if effective.get('damageCalcType') == 'Magic' and effective.get('DamageType') == 'None':
                    fields.setdefault('DamageType', 'Magic')
    return result


def membership(unit):
    value = unit.get(FIELD)
    if value is None:
        return None
    if (not isinstance(value, dict) or set(value) != {'version', 'preset', 'enabled'}
            or value.get('version') != 1 or type(value.get('enabled')) is not bool
            or not isinstance(value.get('preset'), str) or not value['preset']
            or unit.get('native') is not None or unit.get('party') is not None):
        raise ValueError('Invalid Sephira vision membership. Restore its saved character config.')
    return value


def active_units(units):
    """Filter before sprite generation, acquisition, animations and verification.

    Keep the full saved roster intact so disabling the collection never deletes
    edits or reuses its IDs. Untagged user entries and native overrides pass through.
    """
    result = []
    seen = set()
    for unit in units:
        value = membership(unit)
        if value is not None:
            if value['preset'] in seen:
                raise ValueError('Duplicate Sephira preset in the saved roster.')
            seen.add(value['preset'])
            if not value['enabled'] or value['preset'] in RETIRED:
                continue
        result.append(unit)
    return result


def native_motion_for(units, identity):
    return any(str(u.get('id')) == str(identity) and membership(u) is not None
               for u in active_units(units))


def native_motion_names(unit):
    value = membership(unit)
    if value is None: return []
    policy = json.loads(Path(__file__).with_name('sephira_native_presentations.json').read_bytes())
    return policy.get('modelMotions', {}).get(value['preset'], [])


def verify_runtime_rows(root, tool, usmap, units, rows):
    """Read back every selected kit's grants before converting any sprites."""
    selected = [u for u in units if membership(u) is not None]
    if not selected: return
    root = Path(root); work = root / 'build/sephira-reward-check'; work.mkdir(parents=True, exist_ok=True)
    rels = ('Skill/DT_SkillData', PASSIVE, 'Skill/DT_MasterSkillData',
            'Item/Vision/DT_VisionAwakeningMasteryData', 'Item/Vision/DT_VisionSynchroMasteryData')
    built = {}
    for rel in rels:
        target = work / (rel.replace('/', '_') + '.json')
        subprocess.run(tool + ['rows', str(root / 'build/visions_mod/assets/FFRS/Content/Datatable' / (rel + '.uasset')),
                               str(target), '--usmap', usmap], check=True, capture_output=True)
        built[rel] = json.loads(target.read_text(encoding='utf-8-sig'))['rows']
    lookups = {kind: {r['ID']: r for r in built[rel].values()} for kind, rel in (
        ('ActiveSkill', rels[0]), ('PassiveSkill', PASSIVE), ('MasterSkill', rels[2]))}
    for unit in selected:
        for field, rel in [('awakening', rels[3]), ('synchro', rels[4])]:
            for rank, grants in enumerate(unit[field]):
                found = [r for r in built[rel].values() if r['ID'] == unit['id'] and r['Level'] == rank]
                if len(found) != 1: raise ValueError(f'{unit["en"]}: missing {field} rank {rank}.')
                actual = [[g['parameterType'], *g['params']] for g in found[0]['detailData'] if g['parameterType'] != 'None']
                expected = [[*g[:2], g[2] if len(g) > 2 else -1] for g in grants]
                if actual != expected: raise ValueError(f'{unit["en"]}: incorrect {field} rank {rank}; rebuild its reward data.')
                for kind, identity, *_ in grants:
                    if kind not in lookups: continue
                    value = lookups[kind].get(identity)
                    if not value or value.get('Name') in (None, '', 'None'):
                        raise ValueError(f'{unit["en"]}: {field} rank {rank} has an unnamed or unavailable {kind} {identity}.')
                    if kind == 'PassiveSkill' and not 1000 <= identity < 2000:
                        raise ValueError(f'{unit["en"]}: passive {identity} is outside the game\'s passive lookup range.')
        for identity, recipe in (unit.get('skills') or {}).items():
            actual = lookups['ActiveSkill'].get(int(identity))
            if not actual: raise ValueError(f'{unit["en"]}: custom skill {identity} was not written.')
            for field in ('belongCommandList', 'availableLocation', 'mapEffectType', 'isTargetIgnoreSelf'):
                if field in recipe.get('set', {}) and actual.get(field) != recipe['set'][field]:
                    raise ValueError(f'{unit["en"]} / {recipe["en"]}: {field} did not survive serialization.')
    print(f'OK: all awakening/MR rewards, skill names and learned-command availability checked for {len(selected)} Sephira visions')


def bind_units(units, rows):
    """Private equivalents follow allocated IDs, including imported/reset kits.

    Native originals and saved configs remain unchanged. Ordinary stat/status
    parameters, skill-specific bonuses and equip costs are retained verbatim.
    """
    result = copy.deepcopy(units)
    if not any(membership(u) is not None for u in result): return result
    passives = {v['ID']: (k, v) for k, v in rows(PASSIVE).items()}
    effects = {v['ID']: (k, v) for k, v in rows(EFFECT).items()}
    native_skills = {v['ID'] for v in rows('Skill/DT_SkillData').values()}
    allocated = {}
    for u in result:
        value = membership(u)
        if value is None: continue
        owned = {int(sid) for sid in u.get('skills', {})}
        if u.get('lb_custom'): owned.add(440000 + (u['id'] - 13099) * 10)
        if native_skills & owned:
            raise ValueError('A Sephira custom skill/LB ID overlaps the game catalog. Reset this preset in Studio to allocate safe IDs.')
        private = {}
        labels = u.get('sephiraPassiveText') or {}
        for field in ['awakening', 'synchro']:
            for tier in u[field]:
                for g in tier:
                    if g[0] == 'PassiveSkill' and str(g[1]) in labels:
                        sid = g[1]
                        pk, passive = passives[sid]
                        new_sid = private_passive_id(value['preset'], sid)
                        owner = (value['preset'], sid)
                        if new_sid in allocated and allocated[new_sid] != owner:
                            raise ValueError('Edited Sephira passive identities collide; change the duplicated custom membership.')
                        allocated[new_sid] = owner
                        if new_sid in passives:
                            raise ValueError('Sephira private passive ID overlaps the game catalog.')
                        label = labels[str(sid)]
                        fields = {'ID': new_sid, 'Name': label['name'], 'Description': label['desc']}
                        # Item-granted imbues/evasion can have zero equip cost;
                        # learned equivalents use the native 20-AP utility tier.
                        if passive['equipCost'] == 0: fields['equipCost'] = 20
                        private[sid] = {'passive': {'row': f"Studio_Sephira_{u['id']}_Passive_{sid}",
                            'cloneFrom': pk, 'set': fields}}
                        g[1] = new_sid
                        continue
                    if g[0] != 'PassiveSkill' or g[1] not in BINDINGS: continue
                    sid = g[1]
                    eid, kind, index, original, replacement = BINDINGS[sid]
                    pk, passive = passives[sid]; ek, effect = effects[eid]
                    if effect['EffectType'] != kind or effect['ParamList'][index] != original:
                        raise ValueError(f'Native passive {sid} changed; re-audit Sephira owner bindings for this game version.')
                    new_sid = private_passive_id(value['preset'], sid)
                    owner = (value['preset'], sid)
                    if new_sid in allocated and allocated[new_sid] != owner:
                        raise ValueError('Edited Sephira passive identities collide; change the duplicated custom membership.')
                    allocated[new_sid] = owner
                    new_eid = u['id'] * 10000 + eid
                    if new_sid in passives or new_eid in effects:
                        raise ValueError('Sephira private IDs overlap the game catalog; re-audit this game version.')
                    bundles = copy.deepcopy(passive['effectBundleList'])
                    for b in bundles:
                        if b['effectId'] == eid: b['effectId'] = new_eid
                    params = list(effect['ParamList'])
                    params[index] = u['command']['id'] if replacement == 'command' else (440000 + (u['id'] - 13099) * 10 if u.get('lb_custom') else u['lb'])
                    private[sid] = {
                        'passive': {'row': f"Studio_Sephira_{u['id']}_Passive_{sid}", 'cloneFrom': pk,
                                    'set': {'ID': new_sid, 'effectBundleList': bundles}},
                        'effect': {'row': f"Studio_Sephira_{u['id']}_Effect_{eid}", 'cloneFrom': ek,
                                   'set': {'ID': new_eid, 'ParamList': params}}}
                    g[1] = new_sid
        u['_sephiraBindings'] = list(private.values())
    return result


def prepare(tables, units):
    for u in units:
        for binding in u.get('_sephiraBindings', []):
            for rel, key in [(EFFECT, 'effect'), (PASSIVE, 'passive')]:
                if key not in binding: continue
                tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})['add'].append(binding[key])
