"""Restore audited player routes using only each skill's own native packages."""
import copy
import hashlib
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def prepare(tables, clones, selected, root, rows, extract, support):
    policy = json.loads(Path(__file__).with_name('native_skill_repairs.json').read_bytes())
    if policy.get('schema') != 1: raise ValueError('Unsupported native skill repair audit.')
    wanted = {sid: policy['skills'][str(sid)] for sid in selected if str(sid) in policy['skills']}
    if not wanted or not support: return {}
    rels = ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo')
    originals = {rel: rows(rel) for rel in rels}
    definitions = {r['ID']: r for r in rows('Skill/DT_SkillData').values()}
    reports = {}; legacy = Path(root) / 'extracted/legacy/FFRS/Content'
    for sid, rule in sorted(wanted.items()):
        if any((u.get('skills') or {}).get(str(sid), (u.get('skills') or {}).get(sid)) for u in selected[sid]):
            continue  # Explicit custom presentations retain precedence.
        if any(any(r['ID'] == sid + 1 for r in data.values()) or
               any(r.get('set', {}).get('ID') == sid + 1 for r in tables.get(rel, {}).get('add', []))
               for rel, data in originals.items()):
            continue  # Native routes supplied by a later game always win.
        reason = None; donors = {}
        if digest(definitions.get(sid)) != rule['definitionSha256']:
            reason = 'Original skill definition differs from the audited demo.'
        for rel, data in originals.items():
            found = [(key, row) for key, row in data.items() if row['ID'] == sid + 2]
            if len(found) != 1 or digest(found[0][1]) != rule['bindingSha256']:
                reason = 'Original native binding differs from the audited demo.'
            else: donors[rel] = found[0]
        folder = legacy / rule['folder']
        if not reason and not all((folder / path).is_file() for path in rule['files']):
            extract(rule['folder'] + '/')
        if not reason and any(not (folder / path).is_file() or hashlib.sha256((folder / path).read_bytes()).hexdigest() != sha
                              for path, sha in rule['files'].items()):
            reason = 'Native timeline bytes differ from the audited demo or are missing.'
        if reason:
            reports[sid] = {'id': sid, 'status': 'native_repair_unresolved', 'reason': reason}
            print(f'  {rule["name"]}: native repair skipped: {reason}')
            continue
        source = rule['sourceSequence']; target = sid + 1
        binding = support['clone'](donors[rels[0]][1], source, sid, target, (), clones,
                                   support['objects'], (), {}, support['bytecode'])
        target_folder = binding['LevelSequence'].split('/Game/', 1)[1].rsplit('/', 1)[0]
        def copied(path):
            return 'FFRS/Content/' + target_folder + '/' + path.removesuffix('.uasset').replace(f'SEQ_Battle_{source}', f'SEQ_Battle_{target}')
        for edit in rule['motionEdits']:
            asset = copied(edit['file'])
            support['bytecode'].append({'asset': asset,
                'export': edit['function'].replace(f'SEQ_Battle_{source}', f'SEQ_Battle_{target}'), 'set': copy.deepcopy(edit['set'])})
            support['objects'].append({'asset': asset, 'export': asset.rsplit('/', 1)[1], 'set': {'Signature': 'new'}})
        for track in rule['enableTracks']:
            asset = copied(track['file'])
            support['objects'].extend([{'asset': asset, 'export': track['export'], 'set': {'bIsEvalDisabled': False, 'Signature': 'new'}},
                                       {'asset': asset, 'export': asset.rsplit('/', 1)[1], 'set': {'Signature': 'new'}}])
        for rel, (key, _) in donors.items():
            tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})['add'].append({
                'row': f'Studio_NativeAlly_{sid}', 'cloneFrom': key, 'set': {'ID': target, **binding}})
        reports[sid] = {'id': sid, 'status': 'native_ally_variant', 'sourceSequence': source, 'sequence': target,
                        'motionEdits': len(rule['motionEdits']), 'enabledTracks': len(rule['enableTracks']), 'inGameValidated': False}
        print(f'  {rule["name"]}: native ally route {target}; own effects/hit timing retained.')
    return reports
