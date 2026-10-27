"""Replace Rikku's Vaan-bound MR7 with the approved native item bonus."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def revise(catalog):
    preset = next(p for p in catalog['presets'] if p['id'] == 'rikku')
    unit = preset['profile']
    if unit.get('sephiraKitRevision', 0) >= 1:
        return catalog
    before = ['PassiveSkill', 1435, -1]
    after = ['PassiveSkill', 1044, -1]
    assert unit['synchro'][7] == [before]
    preset['pharmacologyKitBefore'] = copy.deepcopy(unit)
    unit['synchro'][7] = [after]
    unit['sephiraKitRevision'] = 1
    preset['kitUpdate'] = {'version': 1, 'mrOnly': True, 'managed': [],
                           'mr': [{'rank': 7, 'from': before, 'to': after}],
                           'masterDescriptions': []}
    return catalog


if __name__ == '__main__':
    path = ROOT / 'assets/sephira_visions/catalog.json'
    path.write_text(json.dumps(revise(json.loads(path.read_bytes())), indent=2) + '\n')
