"""Identify exact unused catalogue duplicates without deleting any game rows."""
import copy
import json
from pathlib import Path

_cached = None
DEFINITIONS = {'Skill/DT_SkillData.json', 'Skill/DT_PassiveSkillData.json', 'Skill/DT_SkillEffectData.json'}


def integers(value):
    if type(value) is int: yield value
    elif isinstance(value, dict):
        for item in value.values(): yield from integers(item)
    elif isinstance(value, list):
        for item in value: yield from integers(item)


def analyze(catalog, root):
    """Compare complete extracted mechanics, not just names or descriptions."""
    base = Path(root) / 'extracted/rows'
    def rows(rel): return json.loads((base / (rel + '.json')).read_bytes())['rows']
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
    result = {'schema': 1, 'available': True, 'groups': {}, 'protected': {k: sorted(v & referenced) for k, v in ids.items()}}
    for kind, definitions in raw.items():
        by_id = {v['ID']: v for v in definitions.values()}; groups = {}
        for entry in catalog[kind]:
            row = by_id.get(entry['id'])
            if row is None: continue
            data = mechanics(row)
            if 'effectBundleList' in data:
                for bundle in data['effectBundleList']:
                    eid = bundle.get('effectId')
                    if eid in effects:
                        bundle['effectId'] = {'mechanics': mechanics(effects[eid])}
            key = json.dumps([entry.get('name', '').strip().casefold(), data], sort_keys=True, ensure_ascii=False)
            groups.setdefault(key, []).append(entry['id'])
        result['groups'][kind] = [sorted(v) for v in groups.values() if len(v) > 1]
    return result


def install(catalog_module, root):
    original = catalog_module.load
    def load(*args, **kwargs):
        global _cached
        catalog = original(*args, **kwargs)
        base = Path(root) / 'extracted/rows'
        files = sorted(base.rglob('*.json'))
        fingerprint = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in files)
        try:
            if _cached is None or _cached[0] != fingerprint:
                _cached = fingerprint, analyze(catalog, root)
            metadata = _cached[1]
        except (OSError, ValueError, KeyError):
            metadata = {'schema': 1, 'available': False, 'groups': {}, 'protected': {}}
        return {**catalog, 'duplicatePolicy': metadata}
    catalog_module.load = load
