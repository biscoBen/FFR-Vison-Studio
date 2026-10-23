"""Optional illustrated movie before Crystal Fina's existing FFBE LB.

Native movie/spawn/compiled bindings are cloned in binary. Only the private
children contain battle events. The source heal, motion and audio move together.
"""
import copy
from functools import lru_cache
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

REVISION = 'crystal-fina-film-2'
SPRITE = '99887755552703'
START = 48000
END = START + 192 * 800
NATIVE_END = 363200
NATIVE_DURATION = 480000
NATIVE = 'FFRS/Content/Sequencer/Battle/Skill/440110/440111/'
MASTER = NATIVE + 'SEQ_Battle_440111_Master'
MOVIE = 'FFRS/Content/Movies/Skill/MV_Skill440110'
PRIVATE = 'FFRS/Content/Movies/Studio/CrystalFina_Test'
# FileManaMovie paths are relative to CRI's Streams directory, not Content.
# Verified against the installed Cloud movie in the returned full-game pak.
VIDEO = 'FFRS/Content/Streams/Movies/Studio/CrystalFina_Test.usm'
SCORE = 'studio_crystal_fina_intro'
MASTER_HASHES = {'.uasset': '1bde55f872f45d69527802dac5cfb0a7b6aacab22852d3cbb99f3e897d655550',
                 '.uexp': '4db420158204dde62c0f0892667209c726e454f97457dfa2af3855eb49da474e'}


def validate(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        manifest = json.loads(archive.read('manifest.json'))
        expected = {'spec.json', 'movie.usm', 'score.hca', 'audio.json', 'preview.mp4', 'poster.jpg'}
        if (manifest.get('schema') != 1 or manifest.get('revision') != REVISION
                or set(manifest.get('files', {})) != expected
                or set(names) != expected | {'manifest.json'} or len(names) != 7):
            raise ValueError('Invalid Crystal Fina movie archive.')
        files = {name: archive.read(name) for name in expected}
        if manifest['files'] != {n: hashlib.sha256(v).hexdigest() for n, v in files.items()}:
            raise ValueError('Crystal Fina movie checksum mismatch.')
    spec = json.loads(files['spec.json'])
    if (spec.get('revision') != REVISION or (spec.get('width'), spec.get('height'), spec.get('fps'), spec.get('frames')) != (1920, 1080, 30, 192)
            or spec.get('opaqueAlpha') is not True or spec.get('alphaCodec') != 'SofdecPrime'
            or not files['movie.usm'].startswith(b'CRID') or not files['score.hca'].startswith(b'HCA\0\x02\0')
            or files['preview.mp4'][4:8] != b'ftyp' or not files['poster.jpg'].startswith(b'\xff\xd8')):
        raise ValueError('Unsupported Crystal Fina movie format.')
    return spec, files


@lru_cache(maxsize=1)
def payload():
    return validate(Path(__file__).with_name('fina_cinematic.zip').read_bytes())


def enabled(root):
    import _ffr_testing
    return _ffr_testing.settings(root)['finaCinematic']


def matches(unit):
    return (not unit.get('party') and not unit.get('native')
            and str((unit.get('ffbe') or {}).get('id')) == SPRITE
            and (unit.get('lb_custom') or {}).get('presentation', 'ffbe') == 'ffbe')


def ensure_assets(root, extract):
    if not enabled(root): return
    for rel in (MASTER, MOVIE, MOVIE + '_vp9'):
        path = Path(root) / 'extracted/legacy' / (rel + '.uasset')
        if not path.is_file(): extract(rel.removeprefix('FFRS/Content/'))
        if not path.is_file(): raise ValueError('The selected game is missing the Crystal Fina movie test template: ' + rel)
    master = Path(root) / 'extracted/legacy' / (MASTER + '.uasset')
    for suffix, digest in MASTER_HASHES.items():
        if hashlib.sha256(master.with_suffix(suffix).read_bytes()).hexdigest() != digest:
            raise ValueError('The native movie template changed. Turn off Test Crystal Fina cinematic until this game build is checked.')


def cache(root):
    spec, files = payload()
    folder = Path(root) / 'build/fina-cinematic/media'
    digest = hashlib.sha256(files['score.hca']).hexdigest()
    for name in ('audio.json', 'score.hca'):
        target = folder / ('samples/' + digest + '.hca' if name == 'score.hca' else name)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() or target.read_bytes() != files[name]: target.write_bytes(files[name])
    return folder


def attach_audio(unit, skill, bank, events, table):
    import ffbe_audio
    if (not matches(unit) or not enabled(ffbe_audio.ROOT)
            or skill.get('audio') == 'none' and skill.get('sephiraAudio') == 1
            or skill.get('audio') == 'experimental'
            or any(skill.get(k) for k in ('audio_bank', 'audio_system_bank'))):
        return bank, events
    settings = dict(skill, audio='native', audio_codec='host', lb_charge=False,
                    audio_bank=str(cache(ffbe_audio.ROOT) / 'audio.json'))
    intro, sounds = ffbe_audio.prepare(unit, settings,
        {'sounds': [{'frame': 0, 'cueId': 1, 'role': 'fina_cinematic'}]}, table)
    if not intro or not sounds: raise ValueError('Crystal Fina cinematic score could not be prepared.')
    if bank:
        bank = {**bank, 'additionalBanks': [*bank.get('additionalBanks', []), intro]}
    else: bank = intro
    return bank, [*events, *sounds]


def continuation(plan):
    """Shift an already-correct LB as one unit. Never manufacture a heal/hit."""
    result = copy.deepcopy(plan)
    starts = [e['time'] for e in result['events']
              if e['set'].get('Unit_PlayAnimByName_AnimationName') == 'LB1']
    if len(starts) != 1: raise ValueError('Crystal Fina needs one existing LB motion.')
    shift = END - starts[0]
    if shift < 0 or result['duration'] + shift > NATIVE_DURATION:
        raise ValueError('Crystal Fina LB exceeds the tested movie wrapper duration.')
    for event in result['events']:
        event['time'] += shift
        label = event['set'].get('Sound_PlayHitSound_playLabel', '')
        if label.startswith(SCORE + '__'): event['time'] = START
        if label.startswith('se_battle_limitopen_1__'): event['time'] = 0
    def at(tick, kind, **fields):
        result['events'].append({'time': tick, 'set': {'EventType': kind, **fields}})
    at(0, 'PostSetDefaultColorGrading', Post_SetDefaultColorGrading_Frame=0)
    at(1, 'CameraSetDefault', Camera_SetDefault_Frame=0, Camera_SetDefault_IsRotation=True,
       Camera_SetDefault_IsLocation=True, Camera_SetDefault_IsZoomInOut=True)
    at(2, 'OtherSetGameSpeed', Other_SetGameSpeed_TimeDilation=1.0)
    # The native Cloud wrapper switches the battle UI through UISetVisibility,
    # retaining movie visibility. Toggling the movie widget alone skips that
    # native presentation transition even when Mana is already decoding.
    at(START, 'UISetVisibility', UI_SetVisibillity_IsVisibility=False,
       UI_SetVisibillityMovie_IsVisibility=True)
    at(END, 'UISetVisibility', UI_SetVisibillity_IsVisibility=True,
       UI_SetVisibillityMovie_IsVisibility=True)
    result['duration'] += shift
    result['events'].sort(key=lambda e: e['time'])
    return result


def evaluation_updates(asset):
    """Invalidate donor evaluation caches after changing movie/spawn timing.

    Preserve opaque compiled bytes and binding locators, but give the edited
    sequence/tracks/sections fresh signatures so Unreal rebuilds evaluation.
    The ordinary engine movie-removal path uses this same native mechanism.
    """
    exports = (Path(asset).name, 'MovieScene_0', 'MovieSceneManaSection_1',
               'MovieSceneManaTrack_1', 'MovieSceneSpawnSection_0', 'MovieSceneSpawnTrack_1')
    return [{'asset': asset, 'export': export, 'set': {'Signature': 'new'}} for export in exports]


def prepare_pak(root, ffrenv, run, video=None):
    """retoc writes cooked assets; loose CRI files travel in its companion pak.

    retoc leaves an existing companion pak intact. Recreate our pak before every
    enabled build, and empty it once when disabling. Never touch another mod.
    """
    root = Path(root)
    folder = root / 'build/fina-cinematic'
    marker = folder / 'pak-managed.json'
    if video is None and not marker.is_file(): return
    stage = folder / 'pak-input'
    obsolete = stage / (PRIVATE + '.usm')
    if obsolete.is_file(): obsolete.unlink()
    target = stage / VIDEO
    target.parent.mkdir(parents=True, exist_ok=True)
    if video is None:
        if target.exists(): target.unlink()
    else: target.write_bytes(video)
    destination = root / 'build/out' / ('zzz_' + ffrenv.MOD_NAME + '_P.pak')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = folder / 'companion.pak'
    repak = root / 'tools/repak/repak.exe'
    run([str(repak), 'pack', '--version', 'V11', '--mount-point', '../../../', str(stage), str(temporary)])
    os.replace(temporary, destination)
    if video is None: marker.unlink()
    else: marker.write_text(json.dumps({'schema': 1, 'revision': REVISION, 'file': VIDEO,
                                      'sha256': hashlib.sha256(video).hexdigest()}), encoding='utf-8')


def build(units, env):
    root, legacy, out = (Path(env[n]) for n in ('ROOT', 'LEGACY', 'OUT'))
    run, tool, usmap = env['run'], env['FFRDT'], env['USMAP']
    selected = [u for u in units if matches(u)] if enabled(root) else []
    if not selected:
        prepare_pak(root, env['ffrenv'], run)
        return
    if len(selected) != 1: raise ValueError('Select one Crystal Fina for the cinematic test.')
    unit = selected[0]
    # Same private LB ID allocation as the engine, never a native donor ID.
    sid = env['lb_id'](unit['id'])
    job, = [j for j in env['authored_sequences'] if f'/Skill/{sid}/{sid + 1}/' in j['asset']]
    plan = continuation(job['plan'])
    spec, files = payload()
    work = root / 'build/fina-cinematic'; work.mkdir(parents=True, exist_ok=True)
    def patch(label, **fields):
        recipe = work / (label + '.json')
        recipe.write_text(json.dumps({'legacyRoot': str(out), 'outRoot': str(out), **fields}), encoding='utf-8')
        run([*tool, 'patch', str(recipe), '--usmap', usmap])
    def native(rel):
        path = legacy / (rel + '.uasset')
        if not path.is_file():
            run(env['ffrenv'].py(str(root / 'tools/extract_legacy.py'), '--filter', rel.removeprefix('FFRS/Content/')))
        if not path.is_file(): raise ValueError('Missing native cinematic template: ' + rel)
        return path
    def clone(source, destination, renames=()):
        target = out / (destination + '.uasset'); target.parent.mkdir(parents=True, exist_ok=True)
        run([*tool, 'clone-package', str(source), str(target),
             '/Game/' + source.with_suffix('').as_posix().split('/FFRS/Content/', 1)[1],
             destination.replace('FFRS/Content/', '/Game/'),
             *[a + '=' + b for a, b in renames], '--usmap', usmap])
    master = native(MASTER)
    # Save Fina's event-only shell as three private children before replacing its
    # root with the native movie master. Cached binding IDs stay binary-native.
    import ffbe_resonance
    for suffix in ('Cut_000', 'Effect_000', 'Sound_001'):
        child = (Path(job['asset']).parent / 'Track' / f'SEQ_Battle_{sid + 1}_{suffix}').as_posix()
        clone(native(ffbe_resonance.SHELL), child,
              [('SEQ_Battle_440111_Cut_000', Path(child).name)])
        child_plan = plan if suffix == 'Cut_000' else {'duration': plan['duration'], 'events': [{'time': 0, 'set': {'EventType': 'None'}}]}
        ffbe_resonance.build({'asset': child, 'plan': child_plan}, str(out), str(work), tool, usmap, run)
    rename = [('440110', str(sid)), ('440111', str(sid + 1)),
              ('/Game/Movies/Skill/MV_Skill440110', PRIVATE.replace('FFRS/Content/', '/Game/')),
              ('MV_Skill440110', Path(PRIVATE).name)]
    # Movie source paths use their own rename rules, separate from skill IDs.
    clone(master, job['asset'], rename[2:] + rename[:2])
    patch('root-inert', bytecode=[{'asset': job['asset'], 'export': '*', 'set': {'EventType': 'None'}}],
          objects=[{'asset': job['asset'], 'export': 'MovieScene_0', 'set': {'MarkedFrames': []}}])
    # Separate patch invocations read the prior result. First shorten the movie
    # window, then resize only the later root/subsequence range ends.
    patch('movie-duration', frames=[{'asset': job['asset'], 'after': NATIVE_END, 'delta': END - NATIVE_END}])
    shortened = NATIVE_DURATION + END - NATIVE_END
    patch('lb-duration', frames=[{'asset': job['asset'], 'after': shortened, 'delta': plan['duration'] - shortened}])
    patch('refresh-evaluation', objects=evaluation_updates(job['asset']))
    for suffix in ('', '_vp9'):
        source = native(MOVIE + suffix)
        clone(source, PRIVATE + suffix, [('/Game/Movies/Skill/MV_Skill440110', PRIVATE.replace('FFRS/Content/', '/Game/')),
                                        ('MV_Skill440110', Path(PRIVATE).name)])
        target = out / (PRIVATE + suffix + '.uasset')
        description = work / ('movie-properties' + suffix + '.json')
        run([*tool, 'tojson', str(target), str(description), '--usmap', usmap])
        view = json.loads(description.read_text(encoding='utf-8-sig'))
        # These two simple movie descriptors have one ordinary export, no
        # director locator, Blueprint bytecode or opaque compiled track data.
        # IntPoint's native [width,height] requires its typed JSON representation.
        if len(view['Exports']) != 1 or not isinstance(view['Exports'][0].get('Data'), list):
            raise ValueError('Unexpected native movie descriptor.')
        def prop(data, name): return next(p for p in data if p['Name'] == name)
        data = view['Exports'][0]['Data']
        # The native UI material samples a separate alpha component texture.
        # Keep its native Sofdec alpha track and describe our matching opaque
        # pictures, rather than leaving the material with no opacity source.
        for field in ('VideoTracks', 'AlphaTracks'):
            track, = prop(data, field)['Value']
            for name in ('TextureDimensions', 'DisplayDimensions'):
                prop(track['Value'], name)['Value'][0]['Value'] = [spec['width'], spec['height']]
            for name, value in (('FrameRate', spec['fps']), ('TotalFrames', spec['frames'])):
                prop(track['Value'], name)['Value'] = value
        fields = {'AudioTracks': [], 'bIsAlpha': True}
        if suffix:
            maximum = ((spec['maxPictureDataSize'] + 2047) // 2048 + 1) * 2048
            fields.update(FilePath='Movies/Studio/CrystalFina_Test.usm', MinBufferSize=maximum * 4,
                          MaxChunkSize=maximum, MaxPictureDataSize=spec['maxPictureDataSize'])
        for name, value in fields.items(): prop(data, name)['Value'] = value
        description.write_text(json.dumps(view), encoding='utf-8')
        run([*tool, 'fromjson', str(description), str(target), '--usmap', usmap])
    prepare_pak(root, env['ffrenv'], run, files['movie.usm'])
    (work / 'timeline.json').write_text(json.dumps({'schema': 1, 'movieStart': START, 'movieEnd': END,
        'duration': plan['duration'], 'asset': job['asset'], 'plan': plan}), encoding='utf-8')
    print('  Crystal Fina: optional 6.4-second illustrated cinematic before her existing LB (in-game test required).')


def register(app):
    @app.get('/crystal-fina-cinematic')
    def page():
        from fastapi.responses import HTMLResponse
        return HTMLResponse('''<!doctype html><meta name="viewport" content="width=device-width"><title>Crystal Fina cinematic test</title>
        <style>body{background:#11212b;color:#f8f7ef;font:18px system-ui;max-width:1100px;margin:32px auto;padding:0 20px}video{width:100%;background:black}a{color:#c6e8ff}</style>
        <h1>Crystal Fina cinematic test</h1><video controls preload="metadata" poster="/api/testing/fina-cinematic/poster"><source src="/api/testing/fina-cinematic/preview" type="video/mp4"></video>
        <p>A 6.4-second illustrated intro: a wide shot moves closer while the intact crystal turns, ending with Fina opening her red eyes. In game it leads into Fina’s existing LB animation and cure sound.</p>
        <p>Turn on <b>Test Crystal Fina cinematic</b> in Studio, include Crystal Fina, rebuild/install and restart the game. Use her resonance to test playback. Turn the switch off and rebuild/install to remove the intro.</p>
        <p>The browser shows the movie and its original score. In-game timing, playback and transitions still need testing.</p>''')
    @app.get('/api/testing/fina-cinematic/preview')
    def preview():
        from fastapi.responses import Response
        return Response(payload()[1]['preview.mp4'], media_type='video/mp4')
    @app.get('/api/testing/fina-cinematic/poster')
    def poster():
        from fastapi.responses import Response
        return Response(payload()[1]['poster.jpg'], media_type='image/jpeg')
