"""Explicitly selected FFBE Blood Recovery for Snow White's private skill only."""
import hashlib
import json
from pathlib import Path
import zipfile

import _ffr_ffbe_needles as shared

ASSET = 'FFRS/Content/Sequencer/Battle/StudioSephiraFFBE/SEQ_Studio_BloodRecovery'
BANK = 'Studio_BloodRecovery_SE'


def selected(unit, recipe):
    import _ffr_sephira
    member = _ffr_sephira.membership(unit)
    return (member is not None and member['preset'] == 'snow_white'
            and recipe.get('from') == 501530 and recipe.get('visuals', 501530) in (501530, 210020)
            and not any(recipe.get(k) for k in ('clone_sequence', 'motion', 'sequence_edits'))
            and recipe.get('tint') is None
            and all(recipe.get('set', {}).get(k, -1) == -1
                    for k in ('playSequencerId', 'sequencerIdWhenTargetFriendlies')))


def payload():
    expected = {'manifest.json', 'audio.json', 'needle.hca',
                *(role + '/' + suffix for role in ('front', 'back', 'flash') for suffix in ('spec.json', 'tex.bgra'))}
    with zipfile.ZipFile(Path(__file__).with_name('sephira_blood_recovery.zip')) as archive:
        if len(archive.namelist()) != len(expected) or set(archive.namelist()) != expected:
            raise ValueError('Invalid Blood Recovery payload members.')
        files = {name: archive.read(name) for name in expected - {'manifest.json'}}
        manifest = json.loads(archive.read('manifest.json'))
    if (manifest.get('schema') != 1 or manifest.get('ability') != 231688
            or manifest.get('files') != {k: hashlib.sha256(v).hexdigest() for k, v in files.items()}):
        raise ValueError('Blood Recovery payload checksum mismatch.')
    for layer in manifest['layers']:
        role = layer['role']; spec = json.loads(files[role + '/spec.json'])
        width, height = map(int, spec['pixelSize'])
        if min(width, height) <= 0 or len(files[role + '/tex.bgra']) != width * height * 4:
            raise ValueError('Invalid Blood Recovery atlas.')
    return files, manifest


def schedule():
    files, manifest = payload(); events = []
    def at(frame, kind, **fields):
        events.append({'time': frame * 400, 'set': {'EventType': kind, **fields}})
    def anim(frame, name, loops=1):
        at(frame, 'UnitPlayAnimByName', Unit_PlayAnimByName_AnimationName=name,
           Unit_PlayAnimByName_InStartFrame=0, Unit_PlayAnimByName_InPlayRate=1.0,
           Unit_PlayAnimByName_InLoopCount=loops)
    anim(0, 'magic_idle'); anim(40, 'magic_attack')
    for layer in manifest['layers']:
        name = layer['name']
        at(layer['start'], 'SsActorSpawnSpriteStudioActor', SsActor_SsData={
            'spriteStudioID': name, 'ssPlayerAsset': {'path': '/Game/Chara/effect/' + name + '/' + name, 'class': 'Ss6Project'},
            'AnimPackName': name, 'AnimationName': 'effect', 'PartName': 'Null_root',
            'addLocation': {'x': float(layer['depth']), 'y': 0.0, 'z': 0.0},
            'bDisableFollowing': False, 'bSpawnRelativeTarget': False})
        at(layer['start'] + layer['length'] + 1, 'SsActorDestroyToSsID', SsActor_Destroy_ID=name)
    cue = json.loads(files['audio.json'])['recordings'][0]['name']
    for frame in manifest['soundFrames']:
        at(frame, 'SoundPlayHitSound', Sound_PlayHitSound_CueSheetName=BANK, Sound_PlayHitSound_playLabel=cue)
    at(manifest['hitFrame'], 'OtherReaction', Other_Reaction_Id=-1, Otber_Reaction_ReactionNum=-1,
       Otber_Reaction_bReturnIdleMotion=False, Otber_Reaction_bChangeColor=False)
    anim(162, 'idle', 0)
    return {'duration': 180 * 400, 'events': sorted(events, key=lambda e: e['time'])}


def prepare(tables, clones, jobs, units, root, rows, extract):
    chosen = [(int(sid), recipe, unit) for unit in units for sid, recipe in (unit.get('skills') or {}).items()
              if selected(unit, recipe)]
    if not chosen: return
    from _ffr_native_skills import digest
    import ffbe_resonance
    files, manifest = payload()
    native = next((r for r in rows('Skill/DT_SkillData').values() if r['ID'] == 501530), None)
    if digest(native) != manifest['nativeDefinitionSha256']:
        raise ValueError('Blood Recovery native definition changed; review the selected FFBE presentation.')
    additions = []
    for rel in shared.RELS:
        source = rows(rel); occupied = {r['ID'] for r in source.values()}
        occupied.update(r.get('set', {}).get('ID') for r in tables.get(rel, {}).get('add', []))
        donor, = [key for key, row in source.items() if row['ID'] == 440111]
        for sid, _, _ in chosen:
            if occupied & {sid + 1, sid + 2}: raise ValueError('Blood Recovery private route is already occupied.')
            additions.append((rel, donor, sid))
    shell = Path(root) / 'extracted/legacy' / (ffbe_resonance.SHELL + '.uasset')
    if not shell.is_file(): extract('Sequencer/Battle/Skill/440110/440111/')
    if not shell.is_file(): raise ValueError('Blood Recovery battle timeline shell is unavailable.')
    bank = shared.prepare_audio(tables, root, extract, files=files, bank_name=BANK, folder_name='blood-recovery-audio')
    clones.append({'from': ffbe_resonance.SHELL, 'to': ASSET,
                   'rename': [['SEQ_Battle_440111_Cut_000', Path(ASSET).name]]})
    jobs.append({'asset': ASSET, 'plan': schedule(), 'audio': bank, 'kind': 'skill_motion'})
    for rel, donor, sid in additions:
        table = tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})
        for variant in (sid + 1, sid + 2):
            table['add'].append({'row': 'Studio_BloodRecovery_' + str(variant), 'cloneFrom': donor,
                                 'set': {'ID': variant, 'LevelSequence': ASSET.replace('FFRS/Content/', '/Game/'),
                                         'soundSequence': 'None', 'bChangeNearClipPlane': False}})
    print('  Snow White / Blood Recovery: selected FFBE Scartio layers and original healing sound; mechanics retained.')


def build(units, env):
    if not any(selected(unit, recipe) for unit in units for recipe in (unit.get('skills') or {}).values()): return
    files, manifest = payload(); folder = Path(env['BUILD']) / 'sephira-blood-recovery'
    donor = Path(env['LEGACY']) / 'FFRS/Content/Chara/summon/summon13110/summon13110.uasset'
    if not donor.is_file():
        env['run'](env['ffrenv'].py(str(Path(env['ROOT']) / 'tools/extract_legacy.py'), '--filter', 'Chara/summon/summon13110/'))
    if not donor.is_file(): raise ValueError('Blood Recovery effect project template is unavailable.')
    for layer in manifest['layers']:
        target = folder / layer['role']; target.mkdir(parents=True, exist_ok=True)
        for suffix in ('spec.json', 'tex.bgra'): (target / suffix).write_bytes(files[layer['role'] + '/' + suffix])
        env['build_effect_project'](layer['name'], str(target), 13110)
    timeline = Path(env['OUT']) / (ASSET + '.uasset')
    view, events = folder / 'sequence.json', folder / 'events.json'
    for command, target in (('tojson', view), ('seqdump', events)):
        env['run']([*env['FFRDT'], command, str(timeline), str(target), '--usmap', env['USMAP']])
    shared.verify_sequence(json.loads(view.read_text(encoding='utf-8-sig')),
                           json.loads(events.read_text(encoding='utf-8-sig')), plan=schedule(),
                           projects={layer['name']: '/Game/Chara/effect/' + layer['name'] + '/' + layer['name']
                                     for layer in manifest['layers']})
    (folder / 'source.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
