"""Restore audited player routes using only each skill's own native packages."""
import copy
import hashlib
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


RELS = ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo')


def eligible(sid, rule, owners, originals, tables):
    if any((u.get('skills') or {}).get(str(sid), (u.get('skills') or {}).get(sid)) for u in owners):
        return False  # Explicit custom presentations retain precedence.
    targets = (sid + 1, sid + 2) if rule.get('retainEnemyRoute') else (sid + 1,)
    return not any(any(r['ID'] in targets for r in data.values()) or
                   any(r.get('set', {}).get('ID') in targets for r in tables.get(rel, {}).get('add', []))
                   for rel, data in originals.items())


def audit(sid, rule, definitions, originals, root, rows, extract=None):
    """The builder and verifier use the same original-input guards."""
    reason = None; donors = {}
    if digest(definitions.get(sid)) != rule['definitionSha256']:
        reason = 'Original skill definition differs from the audited demo.'
    source_binding = rule.get('sourceBinding', sid + 2)
    for rel, data in originals.items():
        found = [(key, row) for key, row in data.items() if row['ID'] == source_binding]
        if len(found) != 1 or digest(found[0][1]) != rule['bindingSha256']:
            reason = 'Original native binding differs from the audited demo.'
        else: donors[rel] = found[0]
    if rule.get('pointTargets'):
        try: points = {r['ID']: r for r in rows('Battle/Sequencer/DT_BtlSkillPointTargetData').values()}
        except (KeyError, OSError): points = {}
        if any(digest(points.get(int(key))) != sha for key, sha in rule['pointTargets'].items()):
            reason = 'Native battle target points differ from the audited demo.'
    folder = Path(root) / 'extracted/legacy/FFRS/Content' / rule['folder']
    if not reason and extract and not all((folder / path).is_file() for path in rule['files']):
        extract(rule['folder'] + '/')
    if not reason and any(not (folder / path).is_file() or hashlib.sha256((folder / path).read_bytes()).hexdigest() != sha
                          for path, sha in rule['files'].items()):
        reason = 'Native timeline bytes differ from the audited demo or are missing.'
    return reason, donors


def expected_definition_edits(root, units, rows):
    """Gate on successful repairs; derive allowed values from audited originals."""
    import _ffr_animation_repair
    selected, _ = _ffr_animation_repair.repair_selection(units)
    policy = json.loads(Path(__file__).with_name('native_skill_repairs.json').read_bytes())
    wanted = {sid: policy['skills'][str(sid)] for sid in selected
              if policy['skills'].get(str(sid), {}).get('definitionSet')}
    if not wanted: return {}
    report = Path(root) / 'build/animation-repair-report.json'
    if not report.is_file(): return {}
    recorded = json.loads(report.read_bytes())
    if recorded.get('schema') != 1: return {}
    completed = {r['id']: r for r in recorded.get('skills', []) if r.get('status') == 'native_ally_variant'}
    originals = {rel: rows(rel) for rel in RELS}
    definitions = {r['ID']: r for r in rows('Skill/DT_SkillData').values()}
    keys = {r['ID']: key for key, r in rows('Skill/DT_SkillData').items()}
    result = {}
    for sid, rule in wanted.items():
        entry = completed.get(sid, {})
        if (entry.get('sequence'), entry.get('enemySequence'), entry.get('sourceSequence')) != (
                sid + 1, sid + 2, rule['sourceSequence']): continue
        if not eligible(sid, rule, selected[sid], originals, {}): continue
        reason, _ = audit(sid, rule, definitions, originals, root, rows)
        if not reason: result[('Skill/DT_SkillData', keys[sid])] = copy.deepcopy(rule['definitionSet'])
    return result


def prepare(tables, clones, selected, root, rows, extract, support):
    policy = json.loads(Path(__file__).with_name('native_skill_repairs.json').read_bytes())
    if policy.get('schema') != 1: raise ValueError('Unsupported native skill repair audit.')
    wanted = {sid: policy['skills'][str(sid)] for sid in selected if str(sid) in policy['skills']}
    if not wanted or not support: return {}
    rels = RELS
    originals = {rel: rows(rel) for rel in rels}
    definitions = {r['ID']: r for r in rows('Skill/DT_SkillData').values()}
    keys = {r['ID']: key for key, r in rows('Skill/DT_SkillData').items()}
    reports = {}
    for sid, rule in sorted(wanted.items()):
        if not eligible(sid, rule, selected[sid], originals, tables): continue
        reason, donors = audit(sid, rule, definitions, originals, root, rows, extract)
        if rule.get('definitionSet') and any(e['row'] == keys.get(sid) and
                any(k in e['set'] for k in rule['definitionSet'])
                for e in tables.get('Skill/DT_SkillData', {}).get('set', [])):
            reason = 'An explicit presentation field edit already exists.'
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
        for edit in [*rule['motionEdits'], *rule.get('effectEdits', [])]:
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
            if rule.get('retainEnemyRoute'):
                # The original explicit pointer bypassed caster-side routing.
                # Its enemy route still resolves to the exact original package.
                tables[rel]['add'].append({'row': f'Studio_NativeEnemy_{sid}', 'cloneFrom': key,
                                          'set': {'ID': sid + 2}})
        if rule.get('definitionSet'):
            tables.setdefault('Skill/DT_SkillData', {'asset': 'FFRS/Content/Datatable/Skill/DT_SkillData',
                'add': [], 'set': []})['set'].append({'row': keys[sid], 'set': copy.deepcopy(rule['definitionSet'])})
        reports[sid] = {'id': sid, 'status': 'native_ally_variant', 'sourceSequence': source, 'sequence': target,
                        'motionEdits': len(rule['motionEdits']), 'effectEdits': len(rule.get('effectEdits', [])),
                        'enabledTracks': len(rule['enableTracks']), 'inGameValidated': False}
        if rule.get('retainEnemyRoute'): reports[sid]['enemySequence'] = sid + 2
        print(f'  {rule["name"]}: native ally route {target}; own effects/hit timing retained.')
    return reports
