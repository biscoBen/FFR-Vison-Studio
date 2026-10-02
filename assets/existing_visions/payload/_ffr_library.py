"""Identify exact unused catalogue duplicates without deleting any game rows."""
import copy
import json
import re
from pathlib import Path

_cached = None
DEFINITIONS = {'Skill/DT_SkillData.json', 'Skill/DT_PassiveSkillData.json', 'Skill/DT_SkillEffectData.json'}

# These select presentation, menus, debug lists or alternate target modes;
# they do not change the combat mechanics of the selected skill. The user
# explicitly prefers the verified copy when only the map/menu effect differs.
LIBRARY_METADATA = {
    'ID', 'SortId', 'Name', 'Description', 'SkillIcon', 'hasUnit',
    'belongCommandList', 'commandIdBelongDebuggingAllSkills',
    'skillIdAfterModeChange', 'isApplyAllMag', 'mapEffectType',
    'voiceLabel', 'selfSkillActivateVoiceLabel', 'isStopVoiceOnEnemyTarget',
    'playSequencerId', 'totalDamageDisplayRule',
}


def verified_skill(entry):
    return (bool(entry.get('seq')) and entry.get('hasUnit') == 'All'
            and entry.get('attr') in ('Ability', 'Magic', 'MagicSword')
            and entry['id'] < 460000)


def default_owners(catalog, rows, raw):
    """Read actual original vision grants, commands, levels and target twins.

    Enemy/script references never count as default vision ownership. Cached
    awakening grants remain useful when an optional table is unavailable.
    """
    visions = {v['id']: v for v in catalog.get('visions', [])}
    owners = {kind: {} for kind in raw}
    loaded = {}
    complete = True
    def add(kind, sid, vid):
        if type(sid) is int and sid > 0 and vid in visions:
            owners[kind].setdefault(sid, set()).add(vid)
    def grants(vid, tiers):
        for tier in tiers:
            for grant in tier:
                if len(grant) < 2: continue
                if str(grant[0]).split('::')[-1] == 'ActiveSkill': add('skills', grant[1], vid)
                elif str(grant[0]).split('::')[-1] == 'PassiveSkill': add('passives', grant[1], vid)
    def optional(rel):
        if rel not in loaded:
            try: loaded[rel] = rows(rel)
            except FileNotFoundError: loaded[rel] = {}
        return loaded[rel]
    commands = {}
    for vid, vision in visions.items():
        grants(vid, vision.get('awakening', []))
        grants(vid, vision.get('synchro', []))
        add('skills', vision.get('finishBlow'), vid)
        if vision.get('commandId') is not None:
            commands.setdefault(vision['commandId'], set()).add(vid)
    for item in optional('Item/Vision/DT_VisionItemData').values():
        vid = item.get('ID')
        if vid not in visions: continue
        add('skills', item.get('finishBlowSkill'), vid)
        if item.get('CommandId') is not None:
            commands.setdefault(item['CommandId'], set()).add(vid)
    for command in optional('Skill/DT_CommandSkillData').values():
        vid = command.get('unitIdToUseSkill')
        if vid in visions and command.get('ID') is not None:
            commands.setdefault(command['ID'], set()).add(vid)
    for rel in ('Item/Vision/DT_VisionAwakeningMasteryData', 'Item/Vision/DT_VisionSynchroMasteryData'):
        for row in optional(rel).values():
            grants(row.get('ID'), [[[d.get('parameterType', ''), *(d.get('params') or [])]
                                  for d in row.get('detailData', [])]])
    levels = {r.get('ID'): r.get('DataTable') for r in optional('Unit/LevelParameter/DT_UnitLevelParameterList').values()}
    for unit in optional('Unit/DT_UnitParameter').values():
        vid = unit.get('ID')
        if vid not in visions: continue
        for sid in unit.get('passiveSkillList') or []: add('passives', sid, vid)
        table = levels.get(unit.get('LevelParamId')) or visions[vid].get('levelTable')
        if isinstance(table, str):
            found = False
            for sub in ('Vision', 'Playable', 'summon'):
                level_rows = optional(f'Unit/LevelParameter/{sub}/{table}')
                found = found or bool(level_rows)
                for level in level_rows.values():
                    for sid in level.get('AddSkills') or []: add('skills', sid, vid)
            complete = complete and found
    for row in raw['skills'].values():
        for command in row.get('belongCommandList') or []:
            for vid in commands.get(command, []): add('skills', row['ID'], vid)
    for entry in catalog.get('skills', []):
        for vid, vision in visions.items():
            if entry.get('hasUnit') == vision.get('name'):
                add('skills', entry['id'], vid)
    # A learned skill can expose a different single/all-target row at runtime.
    by_id = {r['ID']: r for r in raw['skills'].values()}
    pending = [(sid, vid) for sid, ids in owners['skills'].items() for vid in ids]
    seen = set()
    while pending:
        sid, vid = pending.pop()
        if (sid, vid) in seen: continue
        seen.add((sid, vid))
        twin = by_id.get(sid, {}).get('skillIdAfterModeChange')
        if type(twin) is int and twin in by_id:
            add('skills', twin, vid); pending.append((twin, vid))
    if visions:
        # Missing original MR/level/base-unit rows cannot prove an ID unused.
        for rel in ('Unit/DT_UnitParameter', 'Item/Vision/DT_VisionAwakeningMasteryData',
                    'Item/Vision/DT_VisionSynchroMasteryData'):
            complete = complete and set(visions).issubset({r.get('ID') for r in optional(rel).values()})
    return ({kind: {str(sid): [visions[vid]['name'] for vid in sorted(ids)]
                    for sid, ids in assigned.items()} for kind, assigned in owners.items()}, complete)


def integers(value):
    if type(value) is int: yield value
    elif isinstance(value, dict):
        for item in value.values(): yield from integers(item)
    elif isinstance(value, list):
        for item in value: yield from integers(item)


def other_unit_sources(catalog, rows, raw, root):
    """Confirmed usage by non-vision units, including enemies and base party.

    Never infer an owner from a skill name, row name, voice or nearby integer.
    Source labels describe usage, not playable compatibility or verification.
    """
    loaded = {}
    def optional(rel):
        if rel not in loaded:
            try: loaded[rel] = rows(rel)
            except FileNotFoundError: loaded[rel] = {}
        return loaded[rel]
    loc = {}
    for rel in ('extracted/locres_en.json', 'data/locres_en.json'):
        path = Path(root) / rel
        if path.exists():
            loc = json.loads(path.read_bytes()); break
    def english(value):
        return (isinstance(value, str) and bool(re.search(r'[A-Za-z]', value))
                and not re.search(r'[\u3040-\u30ff\u3400-\u9fff]', value))
    def name(unit):
        value = unit.get('Name')
        if isinstance(value, dict):
            namespace = str(value.get('table') or '').split('/')[-1].split('.')[-1]
            value = loc.get(namespace, {}).get(value.get('key'))
        # The same canonical localization key used by the original game.
        if not english(value): value = loc.get('ST_UnitName', {}).get(f"UnitName{unit.get('ID')}")
        return value.strip() if english(value) else None
    default_ids = {v['id'] for v in catalog.get('visions', [])}
    units = {u['ID']: u for u in optional('Unit/DT_UnitParameter').values()
             if type(u.get('ID')) is int and u['ID'] not in default_ids}
    labels = {uid: name(u) for uid, u in units.items()}
    assigned = {kind: {} for kind in raw}
    available_ids = {kind: {row['ID'] for row in definitions.values()} for kind, definitions in raw.items()}
    def add(kind, sid, uid):
        if type(sid) is int and sid in available_ids[kind] and labels.get(uid):
            assigned[kind].setdefault(sid, set()).add(uid)
    commands = {}
    for command in optional('Skill/DT_CommandSkillData').values():
        uid = command.get('unitIdToUseSkill')
        if uid in units: commands.setdefault(command.get('ID'), set()).add(uid)
    for row in raw['skills'].values():
        for command in row.get('belongCommandList') or []:
            for uid in commands.get(command, []): add('skills', row['ID'], uid)
    levels = {r.get('ID'): r.get('DataTable') for r in optional('Unit/LevelParameter/DT_UnitLevelParameterList').values()}
    level_paths = {}
    for directory, suffix in ((Path(root) / 'extracted/rows', '.json'),
                              (Path(root) / 'extracted/legacy/FFRS/Content/Datatable', '.uasset')):
        for path in (directory / 'Unit/LevelParameter').rglob('*' + suffix):
            level_paths.setdefault(path.stem, set()).add(path.relative_to(directory).with_suffix('').as_posix())
    for uid, unit in units.items():
        for sid in unit.get('passiveSkillList') or []: add('passives', sid, uid)
        table = levels.get(unit.get('LevelParamId'))
        if isinstance(table, str):
            basename = table.replace('\\', '/').split('/')[-1].split('.')[0]
            candidates = level_paths.get(basename, set())
            normalized = table.replace('\\', '/').split('.')[0]
            prefix = '/Game/Datatable/'
            if normalized.startswith(prefix):
                candidates = candidates & {normalized[len(prefix):]}
            elif len(candidates) != 1:
                candidates = set()  # An ambiguous basename does not prove usage.
            for rel in sorted(candidates):
                for level in optional(rel).values():
                    for sid in level.get('AddSkills') or []: add('skills', sid, uid)
    def ai_skills(value):
        if isinstance(value, dict):
            for key, child in value.items():
                normalized = key.replace('_', '').lower()
                if normalized in ('skillid', 'useskillid', 'activeskillid', 'skillids', 'skillidlist', 'skilllist'):
                    if type(child) is int: yield child
                    elif isinstance(child, list):
                        yield from (i for i in child if type(i) is int)
                yield from ai_skills(child)
        elif isinstance(value, list):
            for item in value: yield from ai_skills(item)
    linked_ai = {}
    for uid, unit in units.items():
        for key, value in unit.items():
            if key.replace('_', '').lower() in ('aiid', 'aiparamid', 'aiparameterid', 'btlunitaiparameterid') and type(value) is int:
                linked_ai.setdefault(value, set()).add(uid)
    for row in optional('Unit/AI/DT_BtlUnitAIParameter').values():
        uid = row.get('UnitId', row.get('unitId'))
        assigned_units = {uid} if uid in units else linked_ai.get(row.get('ID'), set())
        for uid in assigned_units:
            for sid in ai_skills(row): add('skills', sid, uid)
    # Follow actual alternate target references, with cycle protection.
    by_id = {r['ID']: r for r in raw['skills'].values()}
    pending = [(sid, uid) for sid, ids in assigned['skills'].items() for uid in ids]
    seen = set()
    while pending:
        sid, uid = pending.pop()
        if (sid, uid) in seen: continue
        seen.add((sid, uid))
        twin = by_id.get(sid, {}).get('skillIdAfterModeChange')
        if type(twin) is int and twin in by_id:
            add('skills', twin, uid); pending.append((twin, uid))
    return {kind: {str(sid): sorted({labels[uid] for uid in ids}) for sid, ids in sources.items()}
            for kind, sources in assigned.items()}


def variant_fields(named):
    """Report differing values, including fields omitted from the UI catalog."""
    def leaves(value, prefix=''):
        if isinstance(value, dict) and value:
            return {path: item for key, item in value.items()
                    for path, item in leaves(item, f'{prefix}.{key}' if prefix else key).items()}
        if isinstance(value, list) and value:
            return {path: item for index, item in enumerate(value)
                    for path, item in leaves(item, f'{prefix}.{index}').items()}
        return {prefix: value}
    result = {}
    for versions in named.values():
        if len(versions) < 2: continue
        flattened = {sid: leaves(data) for sid, data in versions}
        keys = sorted({key for fields in flattened.values() for key in fields})
        changed = [key for key in keys if len({json.dumps([key in fields, fields.get(key)], sort_keys=True)
                   for fields in flattened.values()}) > 1]
        if not changed: continue
        for sid, data in versions:
            notes = []
            for key in changed:
                fields = flattened[sid]
                note = {'field': key, 'value': fields.get(key), 'missing': key not in fields}
                if key.startswith('effectBundleList.'):
                    index = int(key.split('.')[1])
                    bundle = data.get('effectBundleList', [])
                    if index < len(bundle) and isinstance(bundle[index].get('effectId'), dict):
                        note['effectType'] = bundle[index]['effectId']['mechanics'].get('EffectType')
                notes.append(note)
            result[str(sid)] = notes
    return result


def analyze(catalog, root, row_loader=None):
    """Compare complete extracted mechanics, not just names or descriptions."""
    base = Path(root) / 'extracted/rows'
    def rows(rel):
        path = base / (rel + '.json')
        if not path.exists() and row_loader and (Path(root) / 'extracted/legacy/FFRS/Content/Datatable' / (rel + '.uasset')).exists():
            return row_loader(rel)  # Use the SDK to convert prepared legacy tables on demand.
        return json.loads(path.read_bytes())['rows']
    raw = {'skills': rows('Skill/DT_SkillData'), 'passives': rows('Skill/DT_PassiveSkillData')}
    effects = {r['ID']: r for r in rows('Skill/DT_SkillEffectData').values()}
    ids = {kind: {int(r['id']) for r in catalog[kind]} for kind in raw}
    referenced = set()
    for path in base.rglob('*.json'):
        if path.relative_to(base).as_posix() in DEFINITIONS: continue
        # Conservatively retain any ID used in an original game table, including
        # default abilities, MR, equipment, enemies and scripted encounters.
        referenced.update(integers(json.loads(path.read_bytes())))
    def mechanics(row):
        return {k: copy.deepcopy(v) for k, v in row.items() if k not in ('ID', 'SortId', 'Name', 'Description')}
    owners, complete = default_owners(catalog, rows, raw)
    sources = other_unit_sources(catalog, rows, raw, root)
    result = {'schema': 2, 'available': True, 'groups': {}, 'variants': {},
              'protected': {k: sorted(v & referenced) for k, v in ids.items()},
              'owners': owners, 'sources': sources, 'ownersComplete': complete, 'details': {}, 'verifiedMatches': {}, 'combatVariants': {}}
    for kind, definitions in raw.items():
        by_id = {v['ID']: v for v in definitions.values()}; groups = {}; named = {}; combat_groups = {}; combat_named = {}; details = {}
        for entry in catalog[kind]:
            row = by_id.get(entry['id'])
            if row is None: continue
            data = mechanics(row)
            if 'effectBundleList' in data:
                for bundle in data['effectBundleList']:
                    eid = bundle.get('effectId')
                    if eid in effects:
                        bundle['effectId'] = {'mechanics': mechanics(effects[eid])}
            name = entry.get('name', '').strip().casefold()
            key = json.dumps([name, data], sort_keys=True, ensure_ascii=False)
            groups.setdefault(key, []).append(entry['id'])
            if name: named.setdefault(name, []).append((entry['id'], data))
            details[str(entry['id'])] = data
            combat = {k: v for k, v in data.items() if k not in LIBRARY_METADATA}
            if name: combat_named.setdefault(name, []).append((entry['id'], combat))
            if kind == 'skills':
                combat_groups.setdefault(json.dumps([name, combat], sort_keys=True, ensure_ascii=False), []).append(entry)
        result['groups'][kind] = [sorted(v) for v in groups.values() if len(v) > 1]
        result['variants'][kind] = variant_fields(named)
        result['details'][kind] = details
        result['combatVariants'][kind] = variant_fields(combat_named)
        matches = {}
        for group in combat_groups.values():
            verified = sorted(e['id'] for e in group if verified_skill(e))
            if verified:
                for entry in group:
                    if not verified_skill(entry): matches[str(entry['id'])] = verified
        result['verifiedMatches'][kind] = matches
    return result


def install(catalog_module, root):
    original = catalog_module.load
    def load(*args, **kwargs):
        global _cached
        catalog = original(*args, **kwargs)
        base = Path(root) / 'extracted/rows'
        files = sorted(base.rglob('*.json')) + [p for p in (
            Path(root) / 'extracted/locres_en.json', Path(root) / 'data/locres_en.json'
        ) if p.exists()]
        fingerprint = (tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in files),
                       json.dumps({k: catalog.get(k, []) for k in ('skills', 'passives', 'visions')}, sort_keys=True))
        try:
            if _cached is None or _cached[0] != fingerprint:
                _cached = fingerprint, analyze(catalog, root, getattr(catalog_module, 'rows', None))
            metadata = _cached[1]
        except (OSError, ValueError, KeyError):
            metadata = {'schema': 1, 'available': False, 'groups': {}, 'protected': {}}
        from _ffr_animation_repair import effect_policy
        return {**catalog, 'duplicatePolicy': metadata, 'animationPolicy': effect_policy(catalog)}
    catalog_module.load = load
