"""Give Sephira's private skills their own guarded original player timelines.

Only the original source is used. Native/global skill rows and enemy routes are
untouched; this is independent of the optional borrowed-visuals/library switches.
"""
import copy
import hashlib
import json
from pathlib import Path

from _ffr_native_skills import digest

RELS = ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo')
POLICY = 'sephira_native_presentations.json'


def selections(units):
    import _ffr_sephira
    for unit in units:
        if _ffr_sephira.runtime_membership(unit) is None: continue
        for identity, recipe in (unit.get('skills') or {}).items():
            if (not recipe or recipe.get('visuals', recipe['from']) != recipe['from']
                    or recipe.get('clone_sequence') or recipe.get('tint') is not None
                    or recipe.get('motion') or recipe.get('sequence_edits')):
                continue
            yield int(identity), recipe, unit


def replace_added(tables, rel, donor, identity, name, fields):
    plan = tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})
    matches = [r for r in plan['add'] if r.get('set', {}).get('ID') == identity]
    if len(matches) > 1: raise ValueError('Ambiguous Sephira private presentation: ' + str(identity))
    if matches:
        matches[0]['cloneFrom'] = donor
        matches[0]['set'].update(copy.deepcopy(fields))
    else:
        plan['add'].append({'row': name, 'cloneFrom': donor, 'set': {'ID': identity, **copy.deepcopy(fields)}})


def direction_edits(rule, recipe, native):
    relation = str(recipe.get('set', {}).get('defaultTargetRelation', native.get('defaultTargetRelation'))).split('::')[-1]
    original = str(native.get('defaultTargetRelation')).split('::')[-1]
    if rule.get('nativePlayerVariant') and relation == original: return []
    # These are the native named group points, not arbitrary actor/particle IDs.
    # Preserve an existing player presentation; only adapt a transplanted enemy
    # route or a recipe that deliberately changes the recipient relationship.
    def destination(value):
        if relation == 'Enemies' and value == 2: return 18
        if relation == 'Friendlies' and value in (0, 18): return 2
        return value
    edits = []
    for event in rule.get('pointEvents', []):
        fields = {}; target = event.get('target')
        if target is not None and destination(target) != target:
            fields['Effect_SpawnTarget_ID'] = destination(target)
        for field, point in event.get('look', {}).items():
            if destination(point) != point: fields[field] = {'LookAtTargetID': destination(point)}
        if fields: edits.append({'file': event['file'], 'function': event['function'], 'set': fields})
    return edits


def prepare(tables, clones, units, root, rows, extract, support):
    chosen = list(selections(units))
    if not chosen: return []
    policy = json.loads(Path(__file__).with_name(POLICY).read_bytes())
    if policy.get('schema') != 1: raise ValueError('Unsupported Sephira native presentation policy.')
    definitions = {r['ID']: r for r in rows('Skill/DT_SkillData').values()}
    assets = {rel: {r['ID']: (k, r) for k, r in rows(rel).items()} for rel in RELS}
    reactions = {r['ID']: (k, r) for k, r in rows('Battle/Sequencer/DT_BtlHitEffectData').items()}
    verified = set(); reports = []
    for sid, recipe, unit in chosen:
        source = recipe['from']; rule = policy['skills'].get(str(source))
        entry = {'id': sid, 'source': source, 'vision': unit['en'], 'name': recipe['en'], 'inGameValidated': False}
        reports.append(entry)
        import _ffr_sephira_ffbe
        if _ffr_sephira_ffbe.selected(unit, recipe):
            entry.update(status='approved_ffbe_presentation', reason='Selected FFBE Blood Recovery from Scartio.')
            continue
        if not rule:
            entry.update(status='unresolved', reason='No native source timeline in the collected full game.')
            continue
        if not support:
            entry.update(status='unresolved', reason='Native sequence cloning support is unavailable.')
            continue
        native = definitions.get(source)
        # Explicit user pointer overrides remain authoritative.
        if native and any(recipe.get('set', {}).get(k, -1) not in (-1, native.get(k, -1))
                          for k in ('playSequencerId', 'sequencerIdWhenTargetFriendlies')):
            entry.update(status='user_presentation', reason='Explicit sequencer pointer retained.')
            continue
        if native is None:
            entry.update(status='unresolved', reason='The original source definition is unavailable.')
            continue
        if digest(native) != rule['definitionSha256']:
            raise ValueError(f'{unit["en"]} / {recipe["en"]}: the original skill definition changed; re-audit its own animation.')
        origin = rule.get('originBinding')
        if origin and any(origin['ID'] not in data or digest(data[origin['ID']][1]) != origin['sha256']
                          for data in assets.values()):
            raise ValueError(f'{unit["en"]} / {recipe["en"]}: the original source no longer points to its audited player/enemy family.')
        donors = {rel: data.get(rule['sourceBinding']) for rel, data in assets.items()}
        if any(not donor for donor in donors.values()):
            entry.update(status='unresolved', reason='The original source binding is unavailable.')
            continue
        if any(digest(donor[1]) != rule['bindingSha256'] for donor in donors.values()):
            raise ValueError(f'{unit["en"]} / {recipe["en"]}: the original animation binding changed; re-audit it.')
        if source not in verified:
            if rule.get('pointTargets'):
                points = {r['ID']: r for r in rows('Battle/Sequencer/DT_BtlSkillPointTargetData').values()}
                if any(digest(points.get(int(key))) != sha for key, sha in rule['pointTargets'].items()):
                    raise ValueError(f'{unit["en"]} / {recipe["en"]}: original effect target points changed; re-audit their direction.')
            folder = Path(root) / 'extracted/legacy/FFRS/Content' / rule['folder']
            if not all((folder / name).is_file() for name in rule['files']): extract(rule['folder'] + '/')
            if any(not (folder / name).is_file() or hashlib.sha256((folder / name).read_bytes()).hexdigest() != expected
                   for name, expected in rule['files'].items()):
                raise ValueError(f'{unit["en"]} / {recipe["en"]}: original timeline bytes are missing or changed; prepare the selected game again.')
            verified.add(source)
        if any('could not be decoded' in flag for flag in rule['flags']):
            entry.update(status='unresolved', reason='; '.join(rule['flags']))
            continue
        target = sid + 1
        if any(target in data for data in assets.values()):
            raise ValueError('A Sephira private player route overlaps an original skill: ' + str(target))
        edits = None
        if len(rule['reactionIds']) == 1 and rule['reactionIds'][0] in reactions:
            reaction_id, = rule['reactionIds']
            edits = {kind: [{'match': {'EventType': 'OtherReaction', 'Other_Reaction_Id': reaction_id},
                             'set': {'Other_Reaction_Id': sid}}] for kind in ('master', 'cut', 'effect', 'sound')}
            replace_added(tables, 'Battle/Sequencer/DT_BtlHitEffectData', reactions[reaction_id][0], sid,
                          f'Studio_Sephira_Impact_{sid}', {'ID': sid})
        binding = support['clone'](donors[RELS[0]][1], rule['sourceSequence'], sid, target, (), clones,
                                    support['objects'], (), edits, support['bytecode'])
        target_folder = binding['LevelSequence'].removeprefix('/Game/').rsplit('/', 1)[0]
        def copied(name):
            return 'FFRS/Content/' + target_folder + '/' + name.removesuffix('.uasset').replace(
                f'SEQ_Battle_{rule["sourceSequence"]}', f'SEQ_Battle_{target}')
        directions = direction_edits(rule, recipe, native)
        for change in rule['motionEdits'] + rule['effectEdits'] + directions:
            asset = copied(change['file'])
            support['bytecode'].append({'asset': asset, 'export': change['function'].replace(
                f'SEQ_Battle_{rule["sourceSequence"]}', f'SEQ_Battle_{target}'), 'set': copy.deepcopy(change['set'])})
            support['objects'].append({'asset': asset, 'export': Path(asset).name, 'set': {'Signature': 'new'}})
        for track in rule['enableTracks']:
            asset = copied(track['file'])
            support['objects'].extend([
                {'asset': asset, 'export': track['export'], 'set': {'bIsEvalDisabled': False, 'Signature': 'new'}},
                {'asset': asset, 'export': Path(asset).name, 'set': {'Signature': 'new'}}])
        for rel, (key, _) in donors.items():
            replace_added(tables, rel, key, target, f'Studio_Sephira_Player_{sid}', {'ID': target, **binding})
        # Source pointers such as Absolute Zero bypass caster-side lookup.
        # Restore ordinary routing so players use our +1 copy while challenge
        # enemies still use the untouched original +2 route.
        skill = next((r for r in tables.get('Skill/DT_SkillData', {}).get('add', [])
                      if r.get('set', {}).get('ID') == sid), None)
        if not skill: raise ValueError('The private Sephira skill recipe is missing: ' + str(sid))
        skill['set']['playSequencerId'] = -1
        if skill['set'].get('sequencerIdWhenTargetFriendlies', -1) != -1:
            skill['set']['sequencerIdWhenTargetFriendlies'] = -1
        entry.update(status='own_source_player_route', sequence=target, enabledMotionTracks=len(rule['enableTracks']),
                     nativePlayerVariant=rule.get('nativePlayerVariant', False), directionEdits=len(directions), sourceFlags=rule['flags'])
    report = Path(root) / 'build/sephira-animation-report.json'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({'schema': 1, 'inGameValidated': False, 'skills': reports}, indent=2) + '\n', encoding='utf-8')
    unresolved = [r for r in reports if r['status'] == 'unresolved' or r.get('sourceFlags')]
    for entry in unresolved:
        print(f'  ! {entry["vision"]} / {entry["name"]}: original presentation needs review: '
              + entry.get('reason', '; '.join(entry.get('sourceFlags', []))))
    print(f'  Sephira original skill presentations: {sum(r["status"] == "own_source_player_route" for r in reports)} private player routes; '
          f'{len(unresolved)} source presentations flagged for review. Audit: {report}')
    return reports
