"""Keep optional Sephira presets editable while excluding disabled entries from builds."""

import copy
import json
import os
from pathlib import Path
import tempfile

FIELD = 'sephiraVision'
RETIRED = {'great_dragon'}
PASSIVE = 'Skill/DT_PassiveSkillData'
EFFECT = 'Skill/DT_SkillEffectData'
CONFIG = 'mods/EstherTsukiko/sephira-settings.json'


def validate_settings(value):
    if (not isinstance(value, dict) or set(value) != {'schema', 'useBorrowedSkillVisuals'}
            or type(value['schema']) is not int or value['schema'] != 1
            or type(value['useBorrowedSkillVisuals']) is not bool):
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
    if settings(root)['useBorrowedSkillVisuals']:
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
    for u in result:
        value = membership(u)
        if value is None: continue
        owned = {int(sid) for sid in u.get('skills', {})}
        if u.get('lb_custom'): owned.add(440000 + (u['id'] - 13099) * 10)
        if native_skills & owned:
            raise ValueError('A Sephira custom skill/LB ID overlaps the game catalog. Reset this preset in Studio to allocate safe IDs.')
        private = {}
        for field in ['awakening', 'synchro']:
            for tier in u[field]:
                for g in tier:
                    if g[0] != 'PassiveSkill' or g[1] not in BINDINGS: continue
                    sid = g[1]
                    eid, kind, index, original, replacement = BINDINGS[sid]
                    pk, passive = passives[sid]; ek, effect = effects[eid]
                    if effect['EffectType'] != kind or effect['ParamList'][index] != original:
                        raise ValueError(f'Native passive {sid} changed; re-audit Sephira owner bindings for this game version.')
                    new_sid = u['id'] * 10000 + sid
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
                tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})['add'].append(binding[key])
