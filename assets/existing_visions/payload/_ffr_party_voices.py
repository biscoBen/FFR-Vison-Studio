"""Replace authored party attack/LB voice cues without changing their timelines."""
import copy
import json
import math
from pathlib import Path
import re

import _ffr_party as party

SKILLS = 'Skill/DT_SkillData'
COMMANDS = 'Unit/DT_UnitBattleCmd'
PLAN = 'build/party-voices/sequence-plan.json'


def selected(units):
    return [party.validate(u) for u in units if u.get('battleVoice') is not None and u['battleVoice'] != u['id']]


def profile(id):
    data = json.loads(Path(__file__).with_name('party_voice_cues.json').read_bytes())
    if data['version'] != 1: raise ValueError('Unsupported party voice cue inventory.')
    return data['speakers'][party.voice_label(id)]


def voice_skills(u, rows):
    skills = rows(SKILLS); by_id = {v['ID']: v for v in skills.values()}
    command = rows(COMMANDS).get(u['jp'], {})
    attacks = [by_id[e['SkillId']] for e in command.get('detailData', [])
               if e.get('SkillId') in by_id and by_id[e['SkillId']].get('skillAttrType') == 'Fight']
    if command.get('ID') != u['id'] or len(attacks) != 1 or attacks[0].get('hasUnit') in (None, 'None'):
        raise ValueError('The original party attack command changed; its authored voices cannot be patched safely.')
    owner = attacks[0]['hasUnit']
    return [(attacks[0]['ID'], 'attack')] + [(s['ID'], 'lb') for s in skills.values()
            if s.get('skillAttrType') == 'LimitBurst' and s.get('hasUnit') == owner]


def import_name(data, index):
    imports = data.get('Imports', [])
    return imports[-index - 1].get('ObjectName') if type(index) is int and -len(imports) <= index < 0 else None


def sounds(data):
    for index, export in enumerate(data.get('Exports', [])):
        if import_name(data, export.get('ClassIndex')) != 'MovieSceneAtomSection': continue
        props = {p['Name']: p for p in export.get('Data', [])}
        cue = import_name(data, props.get('Sound', {}).get('Value'))
        if not cue: continue
        start = 0
        if 'SectionRange' in props:
            start = props['SectionRange']['Value'][0]['Value']['LowerBound']['Value']['Value']
        yield export['ObjectName'], cue, start, index


def prepare(objects, clones, post_objects, units, root, rows, extract, dumps):
    chosen = selected(units)
    if not chosen: return
    root = Path(root); legacy = root / 'extracted/legacy'; content = legacy / 'FFRS/Content'
    assets = {v['ID']: v for rel in ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo') for v in rows(rel).values()}
    changes = []; generated = {}; seen = set(); copied_tracks = set()
    for u in chosen:
        speaker = profile(u['battleVoice']); old_label = party.voice_label(u['id'])
        for sid, kind in voice_skills(u, rows):
            for seq in range(sid, sid + 4):
                master = assets.get(seq, {}).get('LevelSequence', 'None')
                if master == 'None': continue
                if not re.fullmatch(r'/Game/Sequencer/Battle/Skill/[0-9/]+/SEQ_Battle_\d+_Master', master):
                    raise ValueError('The party attack/LB sequence path changed; its voices cannot be patched safely.')
                relative = Path(master.removeprefix('/Game/')).parent; folder = content / relative
                if not (folder / (master.rsplit('/', 1)[1] + '.uasset')).is_file(): extract(relative.as_posix() + '/')
                if not (folder / (master.rsplit('/', 1)[1] + '.uasset')).is_file():
                    raise ValueError('The original party attack/LB sequence is unavailable. Prepare the game files again.')
                events = []
                for path in sorted(folder.rglob('*_Sound*.uasset')):
                    data, _ = dumps(str(path))
                    if not data: raise ValueError('The original party attack/LB sound track could not be decoded.')
                    for export, cue, start, index in sounds(data):
                        # Match the actual speaker token, never music, impacts or story voice banks.
                        if not re.fullmatch(r'VO_BTL_[A-Za-z0-9_]*' + old_label + r'(?:_[A-Za-z0-9]+)*_Cue', cue): continue
                        if kind == 'attack' and not cue.startswith('VO_BTL_ATK_'): continue
                        # SDK object edits address the first matching name. Native
                        # templates can repeat that name under another Outer.
                        # Reject a later voice export instead of changing a
                        # different section that happens to share its name.
                        first = next(i for i, e in enumerate(data['Exports']) if e['ObjectName'] == export)
                        if index != first: raise ValueError('The party voice section has an ambiguous native export name.')
                        asset = 'FFRS/Content/' + path.relative_to(content).with_suffix('').as_posix()
                        if (asset, export) not in seen: events.append((start, asset, export, cue, index))
                events.sort(key=lambda e: (e[0], e[1], e[2]))
                variants = {duel: [e for e in events if e[3].endswith('_DUEL_Cue') == duel] for duel in (False, True)}
                for event in events:
                    _, asset, export, old_cue, index = event
                    group = variants[old_cue.endswith('_DUEL_Cue')]
                    phase = 'attack' if kind == 'attack' else 'opening' if event == group[0] else 'finish' if event == group[-1] else 'release' if re.search(r'_\d{6}_\d+(?:_DUEL)?_Cue$', old_cue) else 'attack'
                    cue = speaker[phase]; label = party.voice_label(u['battleVoice'])
                    name = f'StudioPartyVoice_{label}_{phase}_Cue'
                    target = f'FFRS/Content/Sound/StudioPartyVoice/{label}/{name}'
                    if target not in generated:
                        original_bank = 'VO_BTL_' + old_label; bank = 'VO_BTL_' + label
                        template = f'FFRS/Content/Sound/Cri/Voice/VO_BTL/{original_bank}/{old_cue}'
                        if not (legacy / (template + '.uasset')).is_file(): extract(template.removeprefix('FFRS/Content/'))
                        if not (legacy / (template + '.uasset')).is_file(): raise ValueError('The native battle voice cue template is missing.')
                        view, _ = dumps(str(legacy / (template + '.uasset')))
                        original = next((e for e in view.get('Exports', []) if e.get('ObjectName') == old_cue), {})
                        props = {p['Name']: p['Value'] for p in original.get('Data', [])}
                        if (import_name(view, original.get('ClassIndex')) != 'SoundAtomCue'
                                or import_name(view, props.get('CueSheet')) != original_bank or 'CueName' not in props):
                            raise ValueError('The native battle voice cue layout changed.')
                        edits = {'CueName': cue['name']}
                        if cue['duration'] > 0: edits.update(Duration=cue['duration'], FirstWaveDuration=cue['duration'])
                        clones.append({'from': template, 'to': target, 'rename': [[old_cue, name], [original_bank, bank]]})
                        post_objects.append({'asset': target, 'export': name, 'set': edits})
                        generated[target] = {'asset': target, 'export': name, 'bank': bank, 'set': edits}
                    new_path = target.replace('FFRS/Content/', '/Game/')
                    # The initial patch reads each object from LEGACY. Clone the
                    # track once, then edit OUT in place so later sections cannot
                    # overwrite earlier replacements in the same package.
                    if asset not in copied_tracks:
                        clones.append({'from': asset, 'to': asset, 'rename': []})
                        copied_tracks.add(asset)
                    post_objects.append({'asset': asset, 'export': export, 'set': {'Sound': new_path}})
                    changes.append({'asset': asset, 'export': export, 'export_index': index, 'old': old_cue, 'new': new_path, 'target': u['id'], 'source': u['battleVoice']})
                    seen.add((asset, export))
        print(f'  {u["en"]}: authored attack/LB voices follow {party.identity(u["battleVoice"])[2]}; effects and timing retained.')
    path = root / PLAN; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'version': 1, 'selection': [[u['id'], u['battleVoice']] for u in chosen],
                                'changes': changes, 'cues': list(generated.values())}, indent=2), encoding='utf-8')


def check_track(original, built, changes):
    """Read back every export property, allowing only the planned Sound changes."""
    expected = {c['export_index']: c for c in changes}
    def normalized(data, replace):
        exports = []
        for index, e in enumerate(data['Exports']):
            props = copy.deepcopy(e.get('Data', []))
            for p in props:
                if p['Name'] == 'Sound':
                    p['Value'] = import_name(data, p['Value'])
                    if replace and index in expected:
                        if e['ObjectName'] != expected[index]['export'] or p['Value'] != expected[index]['old']: raise ValueError('The original fixed voice cue changed.')
                        p['Value'] = expected[index]['new'].rsplit('/', 1)[1]
            exports.append((e['ObjectName'], e.get('OuterIndex'), props))
        return exports
    if normalized(original, True) != normalized(built, False):
        raise ValueError('A party voice section failed verification, or unrelated audio/timing changed.')
    for export, cue, _, index in sounds(built):
        if index not in expected: continue
        imp = next(i for i in built['Imports'] if i['ObjectName'] == cue)
        if import_name(built, imp['OuterIndex']) != expected[index]['new']:
            raise ValueError('A party voice section points to the wrong cue package.')


def verify(root, tool, usmap, units):
    import subprocess
    root = Path(root); work = root / 'build/party-voices'; plan = json.loads((root / PLAN).read_bytes())
    if plan.get('version') != 1 or plan['selection'] != [[u['id'], u['battleVoice']] for u in selected(units)]:
        raise ValueError('The party voice build does not match the saved selection.')
    def read(asset, base):
        path = work / 'verify-view.json'
        subprocess.run(tool + ['tojson', str(root / base / (asset + '.uasset')), str(path), '--usmap', usmap], check=True, capture_output=True)
        return json.loads(path.read_text(encoding='utf-8-sig'))
    for asset in sorted({c['asset'] for c in plan['changes']}):
        check_track(read(asset, 'extracted/legacy'), read(asset, 'build/visions_mod/assets'), [c for c in plan['changes'] if c['asset'] == asset])
    for cue in plan['cues']:
        data = read(cue['asset'], 'build/visions_mod/assets')
        export = next(e for e in data['Exports'] if e['ObjectName'] == cue['export'])
        props = {p['Name']: p['Value'] for p in export.get('Data', [])}
        if import_name(data, export['ClassIndex']) != 'SoundAtomCue' or import_name(data, props['CueSheet']) != cue['bank']:
            raise ValueError('A party voice cue has the wrong bank or native class.')
        bank_import = next(i for i in data['Imports'] if i['ObjectName'] == cue['bank'])
        if import_name(data, bank_import['OuterIndex']) != f'/Game/Sound/Cri/Voice/VO_BTL/{cue["bank"]}/{cue["bank"]}':
            raise ValueError('A party voice cue points outside the selected native bank.')
        if any(not math.isclose(props.get(k, -1), v, abs_tol=1e-5) if isinstance(v, float) else props.get(k) != v for k, v in cue['set'].items()): raise ValueError('A party voice cue has the wrong recording or duration.')
    print(f'OK: {len(plan["changes"])} authored attack/LB voice sections and {len(plan["cues"])} native-bank cue references verified')
