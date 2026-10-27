"""The user's Libra/MR rearrangement; append to the earlier saved-roster migration."""
import copy
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REWARDS = {
    'minfilia': {1: ('ActiveSkill', 210220), 3: ('ActiveSkill', 400240),
                 5: ('PassiveSkill', 1465), 7: ('PassiveSkill', 1343), 9: ('PassiveSkill', 1412)},
    'barusa': {1: ('PassiveSkill', 1336)},
    'primm': {1: ('PassiveSkill', 1526), 9: ('PassiveSkill', 1038)},
    'trance_terra': {1: ('PassiveSkill', 1011)},
}
PASSIVE_DELTAS = {'minfilia': -1, 'barusa': -1, 'primm': 1, 'trance_terra': 1}
MR_RANK_OVERRIDES = {('minfilia', 400240): 3}
EARTH_LABEL = {'name': 'Imbue Earth', 'desc': 'Add earth to non-elemental standard attacks and battle skills.'}


def revise(catalog, coverage, rows):
    native = {r['ID']: r for r in rows('Skill/DT_PassiveSkillData').values()}
    for preset in catalog['presets']:
        key = preset['id']
        if key not in REWARDS: continue
        unit = preset['profile']
        target = 1 if key == 'primm' else 2
        if unit.get('sephiraMrRevision', 0) >= target: continue
        before = copy.deepcopy(unit)
        old_balance = copy.deepcopy(preset['awakeningBalance'])
        operations = []
        for rank, (kind, identity) in REWARDS[key].items():
            previous = unit['synchro'][rank][0]
            desired = [kind, identity, -1]
            if previous != desired:
                operations.append({'rank': rank, 'from': copy.deepcopy(previous), 'to': desired})
                unit['synchro'][rank][0] = list(desired)
        remove, add, move = [], [], []
        if key == 'barusa':
            for tier in unit['awakening']:
                tier[:] = [g for g in tier if g[:2] != ['PassiveSkill', 1336]]
            remove = [[1, 'PassiveSkill', 1336]]
        if key == 'trance_terra':
            identity, = [int(sid) for sid, r in unit['skills'].items() if r['from'] == 505540]
            grant = next(g for g in unit['awakening'][2] if g[:2] == ['ActiveSkill', identity])
            unit['awakening'][2].remove(grant)
            unit['awakening'][3].append(grant)
            move = [[505540, 2, 3]]
            add = [[2, 'PassiveSkill', 1038]]
        if key == 'primm':
            add = [[3, 'PassiveSkill', 1460]]
            unit.setdefault('sephiraPassiveText', {})['1526'] = copy.deepcopy(EARTH_LABEL)
        for rank, kind, identity in add:
            unit['awakening'][rank].append([kind, identity, -1])
        step = {'version': target, 'mr': operations, 'remove': remove, 'add': add,
                'move': move, 'exactAwakeningRanks': True}
        if key == 'primm': step['passiveText'] = {'1526': copy.deepcopy(EARTH_LABEL)}
        if preset.get('mrRestoration'):
            prior = preset['mrRestoration']
            first = {k: copy.deepcopy(prior[k]) for k in ('version', 'mr', 'remove', 'add')}
            prior['steps'] = [first, step]
            prior['version'] = target
        else:
            preset['mrRestoration'] = {**step,
                'before': {f: copy.deepcopy(before[f]) for f in ('awakening', 'synchro')},
                'beforeAwakeningBalance': old_balance}
        unit['sephiraMrRevision'] = target
        passive = [g[1] for f in ('awakening', 'synchro') for t in unit[f] for g in t if g[0] == 'PassiveSkill']
        assert len(passive) == len(set(passive)), key
        assert all(len(t) <= 8 for t in unit['awakening']), key
        budget = preset['awakeningBalance']
        budget.update(totalPassiveCount=len(passive), equipCost=sum(native[s]['equipCost'] or 20 for s in passive),
            requestedPassiveDelta=PASSIVE_DELTAS[key],
            grants=[{'rank': r, 'id': g[1]} for r, t in enumerate(unit['awakening']) for g in t if g[0] == 'PassiveSkill'])
        assert len(passive) == budget['nativePassiveCount'] + PASSIVE_DELTAS[key], key
        assert .8 * budget['nativeEquipCost'] <= budget['equipCost'] <= 1.2 * budget['nativeEquipCost'], key
        balance = preset['balance']
        for field, count_key in (('awakening', 'activeCount'), ('synchro', 'mrActiveCount')):
            balance[count_key] = sum(g[0] == 'ActiveSkill' for tier in unit[field] for g in tier)
        for field, count_key in (('awakening', 'passiveCount'), ('synchro', 'mrPassiveCount')):
            balance[count_key] = sum(g[0] == 'PassiveSkill' for tier in unit[field] for g in tier)
        balance['kitCount'] = sum(map(len, unit['awakening']))
        balance['totalSkillCount'] = balance['kitCount'] + 5
        for recipe in balance['playerCopies']:
            recipe['unlock'] = next(([f, r] for f in ('awakening', 'synchro') for r, tier in enumerate(unit[f])
                if any(g[:2] == ['ActiveSkill', recipe['id']] for g in tier)), None)
        assert all(unit[f] == before[f] for f in before if f not in ('awakening', 'synchro', 'sephiraMrRevision', 'sephiraPassiveText'))
    for entry in coverage['entries']:
        replacement = {1336: 'barusa', 1038: 'primm', 1011: 'trance_terra', 1526: 'primm'}
        if entry['kind'] == 'PassiveSkill' and entry['id'] in replacement:
            entry['assignedTo'] = replacement[entry['id']]
    choices = [g for p in catalog['presets'] for t in p['profile']['synchro'] for g in t]
    catalog['passiveCuration'].update(mrActiveCount=sum(g[0] == 'ActiveSkill' for g in choices),
        mrPassiveCount=sum(g[0] == 'PassiveSkill' for g in choices),
        distinctCount=len({g[1] for g in choices if g[0] == 'PassiveSkill'}))
    policy = {'schema': 1, 'presets': {}}
    for preset in catalog['presets']:
        if not preset.get('mrRestoration'): continue
        update = preset['mrRestoration']
        policy['presets'][preset['id']] = {k: copy.deepcopy(update[k]) for k in
            ('version', 'mr', 'remove', 'add', 'move', 'exactAwakeningRanks', 'passiveText', 'steps') if k in update}
    (ROOT/'assets/existing_visions/payload/sephira_mr_restoration.json').write_text(json.dumps(policy, indent=2)+'\n')
    return catalog


if __name__ == '__main__':
    catalog_path = ROOT/'assets/sephira_visions/catalog.json'
    coverage_path = ROOT/'assets/sephira_visions/native_coverage.json'
    data = ROOT/'scripts/fixtures/sephira_challenges/rows.json.gz'
    raw = json.loads(gzip.decompress(data.read_bytes()))
    # Use the original captured rows, never a second combat-data copy.
    source = raw
    catalog = json.loads(catalog_path.read_bytes()); coverage = json.loads(coverage_path.read_bytes())
    revise(catalog, coverage, lambda rel: source[rel])
    catalog_path.write_text(json.dumps(catalog, indent=2)+'\n')
    coverage_path.write_text(json.dumps(coverage, indent=2)+'\n')
