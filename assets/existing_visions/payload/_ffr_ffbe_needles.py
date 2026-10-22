"""Opt-in, source-backed FFBE 1,000 Needles visual; no skill mechanics edits."""
import hashlib
import io
import json
from pathlib import Path
import zipfile

NAME = 'ffbe_needles_test'
ASSET = 'FFRS/Content/Sequencer/Battle/Skill/500270/500271/SEQ_Studio_FFBE_Needles_Master'
PROJECT = '/Game/Chara/effect/' + NAME + '/' + NAME
RELS = ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo')


def payload():
    with zipfile.ZipFile(io.BytesIO(Path(__file__).with_name('ffbe_needles.zip').read_bytes())) as archive:
        if sorted(archive.namelist()) != ['audio.json', 'manifest.json', 'needle.hca', 'spec.json', 'tex.bgra']:
            raise ValueError('Invalid FFBE Needles payload members.')
        manifest = json.loads(archive.read('manifest.json'))
        files = {k: archive.read(k) for k in ('spec.json', 'tex.bgra', 'audio.json', 'needle.hca')}
    if (manifest.get('schema') != 1 or manifest.get('name') != NAME
            or manifest.get('files') != {k: hashlib.sha256(v).hexdigest() for k, v in files.items()}):
        raise ValueError('FFBE Needles payload checksum mismatch.')
    spec = json.loads(files['spec.json'])
    w, h = map(int, spec['pixelSize'])
    if w <= 0 or h <= 0 or len(files['tex.bgra']) != w*h*4:
        raise ValueError('Invalid FFBE Needles atlas.')
    return files, manifest


def schedule():
    events = []
    def at(frame, event, **fields):
        events.append({'time': frame * 400, 'set': {'EventType': event, **fields}})
    def anim(frame, name, loops=1):
        at(frame, 'UnitPlayAnimByName', Unit_PlayAnimByName_AnimationName=name,
           Unit_PlayAnimByName_InStartFrame=0, Unit_PlayAnimByName_InPlayRate=1.0,
           Unit_PlayAnimByName_InLoopCount=loops)
    anim(0, 'command')
    anim(40, 'attack_A')
    at(40, 'SsActorSpawnSpriteStudioActor', SsActor_SsData={
        'spriteStudioID': NAME, 'ssPlayerAsset': {'path': PROJECT, 'class': 'Ss6Project'},
        'AnimPackName': NAME, 'AnimationName': 'effect', 'PartName': 'Null_center',
        'addLocation': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'bDisableFollowing': True, 'bSpawnRelativeTarget': True})
    at(41, 'SsActorMoveToTargetToSsID', SsActor_MoveToTarget_ID=NAME,
       SsActor_MoveToTarget_targetPointID=-1, SsActor_MoveToTarget_frame=0,
       SsActor_MoveToTarget_partName='Null_center',
       SsActor_MoveToTarget_plusOffset={'x': 0.0, 'y': 0.0, 'z': 0.0},
       SsActor_MoveToTarget_RelativeActionUnit=False,
       SsActor_MoveToTarget_Height=0.0, SsActor_MoveToTarget_Length=0.0)
    files, _ = payload()
    audio = json.loads(files['audio.json'])
    # Original group cue 99 repeats every two source frames. This is cosmetic:
    # keep the game's one fixed-damage reaction, independently of sound pulses.
    for frame in range(0, 40, 2):
        at(40 + frame, 'SoundPlayHitSound', Sound_PlayHitSound_CueSheetName=audio_bank_name(),
           Sound_PlayHitSound_playLabel=audio['recordings'][0]['name'])
    # Eleven cosmetic spawns must still produce exactly one native damage hit.
    at(92, 'OtherReaction', Other_Reaction_Id=-1, Otber_Reaction_ReactionNum=-1,
       Otber_Reaction_bReturnIdleMotion=True, Otber_Reaction_bChangeColor=True)
    at(102, 'SsActorDestroyToSsID', SsActor_Destroy_ID=NAME)
    anim(106, 'idle', 0)
    # Last source sound starts at frame 78 and has a 568 ms recording. Leave
    # its tail inside playback, independently of visual destruction at 102.
    return {'duration': 120 * 400, 'events': sorted(events, key=lambda e: e['time'])}


def audio_bank_name():
    return 'Studio_FFBE_Needles_SE'


def prepare_audio(tables, root, extract):
    import ffbe_audio
    files, _ = payload()
    folder = Path(root) / 'build/ffbe-needles-audio'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / 'audio.json'; path.write_bytes(files['audio.json'])
    doc = json.loads(files['audio.json'])
    sample, = doc['waves'].values()
    samples = folder / 'samples'; samples.mkdir(exist_ok=True)
    (samples / (sample['sha256'] + '.hca')).write_bytes(files['needle.hca'])
    shell = Path(root) / 'extracted/legacy' / (ffbe_audio.SHELL + '.uasset')
    if not shell.is_file(): extract(ffbe_audio.SHELL.replace('FFRS/Content/', ''))
    if not shell.is_file(): raise ValueError('The native audio bank template could not be extracted.')
    # Reuse the proven host-format HCA adapter, including the installed game's
    # key/routing. Do not ship an entire mobile sound bank or alter native audio.
    bank = {'path': str(path), 'sha256': hashlib.sha256(files['audio.json']).hexdigest(),
            'name': audio_bank_name(), 'asset': 'FFRS/Content/Sound/FFBE/' + audio_bank_name(),
            'audioManifest': doc, 'cues': {int(k): v for k, v in doc['cues'].items()},
            'mode': 'native', 'recordings': doc['recordings'], 'gain': 0.15,
            'waveformProfile': {'revision': 1, 'version': 0x300,
                'key': ffbe_audio.hca_host.key_from_config(ffbe_audio.host_config({}))}}
    for rel in ('Asset/Sound/DT_SoundCueSheetAsset', 'Asset/Sound/CDT_SoundCueSheetAsset_Demo'):
        tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})['add'].append({
            'row': bank['name'], 'cloneFrom': 'SE_BTL', 'set': {
                'CueSheetName': bank['name'], 'pCueSheet': bank['asset'].replace('FFRS/Content/', '/Game/')}})
    return bank


def prepare(tables, clones, jobs, root, rows, extract):
    import _ffr_testing
    if not _ffr_testing.settings(root)['ffbeNeedles']: return
    import _ffr_game_tables
    native = _ffr_game_tables.reader(root, rows)
    if native.available('Asset/Skill/DT_SkillAsset_Prod') and any(
            r['ID'] in (500270, 500271, 500272) for r in native(RELS[0]).values()):
        print('  1,000 Needles: using the full game native timeline; optional FFBE test import skipped.')
        return
    import ffbe_resonance
    definitions = [v for v in rows('Skill/DT_SkillData').values() if v.get('ID') == 500270]
    expected = ('Ability', 'Physic', 'Fixed', 'Single', 'Enemies')
    keys = ('skillAttrType', 'DamageType', 'damageCalcType', 'TargetType', 'defaultTargetRelation')
    if (len(definitions) != 1 or tuple(str(definitions[0].get(k)).split('::')[-1] for k in keys) != expected
            or definitions[0].get('hitCount') != 1 or definitions[0].get('magnification') != 1000
            or definitions[0].get('playSequencerId') != -1):
        raise ValueError('The original 1,000 Needles definition changed; disable the FFBE visual test.')
    additions = []
    for rel in RELS:
        original = rows(rel)
        occupied = {v['ID'] for v in original.values()}
        occupied.update(v['set'].get('ID') for v in tables.get(rel, {}).get('add', []))
        if occupied & {500270, 500271, 500272}:
            raise ValueError('1,000 Needles already has a timeline; disable the FFBE visual test to retain it.')
        donors = [k for k, v in original.items() if v.get('ID') == 440111]
        if len(donors) != 1: raise ValueError('The battle timeline template is unavailable.')
        additions.append((rel, donors[0]))
    payload()  # Fail before staging a partial import.
    bank = prepare_audio(tables, root, extract)
    source = Path(root) / 'extracted/legacy' / (ffbe_resonance.SHELL + '.uasset')
    if not source.is_file(): extract('Sequencer/Battle/Skill/440110/440111/')
    if not source.is_file(): raise ValueError('The battle timeline shell could not be extracted.')
    clones.append({'from': ffbe_resonance.SHELL, 'to': ASSET,
                   'rename': [['SEQ_Battle_440111_Cut_000', Path(ASSET).name]]})
    jobs.append({'asset': ASSET, 'plan': schedule(), 'audio': bank, 'kind': 'skill_motion'})
    for rel, donor in additions:
        table = tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})
        for variant in (500271, 500272):
            table['add'].append({'row': 'Studio_FFBE_Needles_' + str(variant), 'cloneFrom': donor,
                'set': {'ID': variant, 'LevelSequence': ASSET.replace('FFRS/Content/', '/Game/'),
                        'soundSequence': 'None', 'bChangeNearClipPlane': False}})
    print('  FFBE 1,000 Needles visual test: original BMB art, 11 flashes, one native hit; ally/enemy routes.')


def build(env):
    import _ffr_testing
    if not _ffr_testing.settings(env['ROOT'])['ffbeNeedles']: return
    files, manifest = payload()
    folder = Path(env['BUILD']) / 'ffbe-needles'
    folder.mkdir(parents=True, exist_ok=True)
    for name, data in files.items(): (folder / name).write_bytes(data)
    donor = Path(env['LEGACY']) / 'FFRS/Content/Chara/summon/summon13110/summon13110.uasset'
    if not donor.is_file():
        env['run'](env['ffrenv'].py(str(Path(env['ROOT']) / 'tools/extract_legacy.py'),
                                  '--filter', 'Chara/summon/summon13110/'))
    if not donor.is_file(): raise ValueError('The effect project template could not be extracted.')
    env['build_effect_project'](NAME, str(folder), 13110)
    # Read back the actual cooked events and evaluation times, before packing.
    timeline = Path(env['OUT']) / (ASSET + '.uasset')
    view, events = folder / 'sequence.json', folder / 'events.json'
    for command, target in (('tojson', view), ('seqdump', events)):
        env['run']([*env['FFRDT'], command, str(timeline), str(target), '--usmap', env['USMAP']])
    verify_sequence(json.loads(view.read_text(encoding='utf-8-sig')),
                    json.loads(events.read_text(encoding='utf-8-sig')))
    (folder / 'source.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print('  OK: FFBE Needles cooked reference, target, single hit, cleanup and compiled event times verified.')


def verify_sequence(view, events):
    import ffbe_resonance as seq
    def cls(e): return view['Imports'][-e['ClassIndex']-1]['ObjectName'] if e['ClassIndex'] < 0 else ''
    sections = [e for e in view['Exports'] if cls(e) == 'MovieSceneEventTriggerSection'
                and any(p['Name'] == 'EventChannel' and any(k['Name'] == 'KeyTimes' and k['Value']
                        for k in p['Value']) for p in e['Data'])]
    if len(sections) != 1: raise ValueError('FFBE Needles has an unexpected event track.')
    channel = seq.child(sections[0]['Data'], 'EventChannel')
    times = seq.child(channel, 'KeyTimes')
    # FrameNumber is nested in the cooked property wrappers.
    def number(v):
        while isinstance(v, (dict, list)):
            v = v['Value'] if isinstance(v, dict) else v[0]
        return v
    times = [number(t) for t in times]
    functions = [seq.child(k['Value'], 'Ptrs', 'Function') for k in seq.child(channel, 'KeyValues')]
    by_id = {int(k.split(':')[0]): v for k, v in events.items()}
    plan = schedule()
    if times != [e['time'] for e in plan['events']]: raise ValueError('FFBE Needles event times changed.')
    for fn, expected in zip(functions, plan['events']):
        actual = by_id[fn]; fields = expected['set']
        for key, value in fields.items():
            if key == 'SsActor_SsData':
                data = actual.get(key, {})
                important = {k: v for k, v in value.items() if k not in ('addLocation', 'ssPlayerAsset')}
                if any(data.get(k) != v for k, v in important.items()) or data.get('ssPlayerAsset') != 'import:' + NAME:
                    raise ValueError('FFBE Needles lost its effect project/target placement.')
            elif isinstance(value, dict):
                if any(actual.get(key, {}).get(k, 0) != v for k, v in value.items()):
                    raise ValueError('FFBE Needles event vector changed.')
            elif actual.get(key, 0) != value:
                raise ValueError('FFBE Needles event field changed: ' + key)
    imports = view['Imports']
    if not any(i['ObjectName'] == NAME and i['ClassName'] == 'Ss6Project'
               and imports[-i['OuterIndex']-1]['ObjectName'] == PROJECT for i in imports if i['OuterIndex'] < 0):
        raise ValueError('FFBE Needles project import does not resolve.')
    compiled, = [e for e in view['Exports'] if cls(e) == 'MovieSceneCompiledData']
    field = seq.child(compiled['Data'], 'EntityComponentField')
    tree = seq.child(field, 'OneShotEntityTree')[0]['Value']['SerializedData']
    scheduled = sorted({e['time'] for e in plan['events']})
    nodes = tree['ChildNodes']['Items']
    if (len(seq.child(field, 'Entities')) != len(plan['events'])
            or [n['Range']['LowerBound']['Value']['Value'] for n in nodes] != scheduled
            or [n['Range']['UpperBound']['Value']['Value'] for n in nodes] != scheduled):
        raise ValueError('FFBE Needles compiled playback times changed.')
