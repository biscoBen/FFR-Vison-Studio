"""Native Atom soundtrack from the installed game's cave music cue."""
import copy
import json
from pathlib import Path
import hashlib
import subprocess
import tempfile
import zipfile
import struct

CUE_NAME = 'BGM_PP_EVENT_VISIONS_INST'
CUE_DONOR = 'FFRS/Content/Sound/Cri/Bgm/BGM_PP/BGM_PP_BATTLE1_Cue'
CUE = 'FFRS/Content/Sound/Cri/Studio/Studio_FinaCaveMusic_Cue'
SHEET = 'FFRS/Content/Sound/Cri/Studio/Studio_FinaCaveMusic'
BANK_DONOR = 'FFRS/Content/Sound/Cri/Se/SE_PP/SE_BTL_PP/SE_BTL_PP'
SOUND = 'FFRS/Content/Sequencer/Battle/Skill/440110/440111/Track/SEQ_Battle_440111_Sound_001'
NATIVE_START, NATIVE_END = 48000, 363503
FADE_IN_SECONDS, FADE_OUT_SECONDS = .4, .8


def fade_audio(raw):
    """Soften only the ends of the proven 6.4-second stereo PCM recording.

    Keep every sample position and the untouched middle, then use the existing
    ADX encoder/muxer. Smoothstep reaches silence without a sharp gain change.
    No wave-module dependency is available in the frozen engine.
    """
    if len(raw)<12 or raw[:4]!=b'RIFF' or raw[8:12]!=b'WAVE':
        raise ValueError('Invalid cave music WAV for fading.')
    pos=12;fmt=None;data=None
    while pos+8<=len(raw):
        kind=raw[pos:pos+4];size=struct.unpack_from('<I',raw,pos+4)[0];start=pos+8
        if start+size>len(raw):raise ValueError('Incomplete cave music WAV for fading.')
        if kind==b'fmt ':fmt=raw[start:start+size]
        elif kind==b'data':data=(start,size)
        pos=start+size+(size&1)
    if (fmt is None or len(fmt)<16 or struct.unpack_from('<HHIIHH',fmt)!=(1,2,48000,192000,4,16)
            or data is None or data[1]!=307200*4):
        raise ValueError('Cave music fades require the decoded 6.4-second stereo PCM recording.')
    result=bytearray(raw);start,size=data;frames=size//4
    for count,reverse in ((round(FADE_IN_SECONDS*48000),False),(round(FADE_OUT_SECONDS*48000),True)):
        for index in range(count):
            x=index/(count-1);gain=x*x*(3-2*x)
            offset=start+(frames-1-index if reverse else index)*4
            left,right=struct.unpack_from('<hh',raw,offset)
            struct.pack_into('<hh',result,offset,round(left*gain),round(right*gain))
    return bytes(result)


def recording(env):
    """Cache only the original six-second HCA prefix; never re-encode its frames."""
    import _ffr_cave_music_preview as preview
    import _ffr_deck_sync as sync
    root=Path(env['ROOT']);identity=sync.game_identity(Path(env['ffrenv'].game_root()))
    key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()+Path(preview.__file__).read_bytes()).hexdigest()[:24]
    folder=root/'build/fina-cinematic/native-score';folder.mkdir(parents=True,exist_ok=True)
    target=folder/(key+'.hca');marker=target.with_suffix('.json')
    if target.is_file() and marker.is_file():
        try:
            saved=json.loads(marker.read_bytes())
            if saved['sha256']==hashlib.sha256(target.read_bytes()).hexdigest():return target,int(saved['subkey'])
        except (ValueError,KeyError,TypeError):pass
    raw,subkey=preview.read_recording(root,env['ffrenv']);clip=preview.trim_hca(raw)
    target.write_bytes(clip);marker.write_text(json.dumps({'sha256':hashlib.sha256(clip).hexdigest(),'subkey':subkey}))
    return target,subkey


def native_bank(native,clip,subkey,name):
    """Use native one-shot metadata with the game's unchanged encrypted HCA frames."""
    from ffbe_effects import acb_native,hca_host
    from ffbe_effects.acb_cues import utf
    import _ffr_sephira_lb_audio
    # The adapter supplies the proven one-shot structure. Its temporary sound
    # is replaced before serialization; only the original cave frames ship.
    for path,stub in _ffr_sephira_lb_audio.payload()[1].items():
        if not path.endswith('.hca'):continue
        try:hca_host.validate_layout(stub);break
        except ValueError:continue
    else:raise ValueError('The native sound metadata template is unavailable.')
    rec={'sourceWaveId':0,'name':CUE_NAME,'durationMs':6400,'samples':307200,
         'sampleRate':48000,'channels':2,'sourceCueId':1,'variation':0}
    bank=acb_native.build(b'',native,name,[rec],gain=1.0,raw_waves={0:stub})
    header=utf(bank)[1][0];header['AwbFile']=acb_native.encode_awb([clip],subkey)
    result=acb_native.encode_table('Header',acb_native.schema(bank),[header])
    check=utf(result)[1][0]
    if list(acb_native.awb_files(check['AwbFile']).values())!=[clip]:raise ValueError('The native cave score changed a source frame.')
    return result


def movie_audio(env, pictures):
    """Cache a local six-second stereo ADX copy of the installed cave recording."""
    root=Path(env['ROOT'])
    try:
        import _ffr_cave_music_preview as preview
        import _ffr_movie_audio as movie
        wave=fade_audio(preview.audio(root,env['ffrenv']))
        archive=root/'tools/cave_music_preview.zip'
        identity=hashlib.sha256(pictures+wave+archive.read_bytes()+Path(movie.__file__).read_bytes()).hexdigest()
        folder=root/'build/fina-cinematic/native-audio';folder.mkdir(parents=True,exist_ok=True)
        target=folder/(identity[:24]+'.usm');marker=target.with_suffix('.json')
        if target.is_file() and marker.is_file():
            expected=json.loads(marker.read_bytes())
            if expected.get('sha256')==hashlib.sha256(target.read_bytes()).hexdigest():return target
        with tempfile.TemporaryDirectory(prefix='encode-',dir=folder) as temporary:
            work=Path(temporary)
            with zipfile.ZipFile(archive) as z:
                for name in ('VGAudio.dll','encode.ps1'):(work/name).write_bytes(z.read(name))
            source=work/'cave.wav';source.write_bytes(wave);encoded=work/'cave.adx'
            result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass',
                                   '-File',str(work/'encode.ps1'),str(source),str(encoded),str(work/'VGAudio.dll')],capture_output=True)
            if result.returncode:
                detail=(result.stderr or result.stdout).decode('utf-8',errors='replace').strip()
                raise ValueError('The installed cave recording could not be encoded as native stereo ADX: '+detail[:2000])
            data, report=movie.with_soundtrack(pictures,encoded.read_bytes())
        temporary=target.with_suffix('.tmp');temporary.write_bytes(data);temporary.replace(target)
        marker.write_text(json.dumps({'schema':1,'sha256':hashlib.sha256(data).hexdigest(),'report':report}))
        print('  Crystal Fina: cached cave music with a 0.4-second fade in and 0.8-second fade out in the native stereo ADX movie.',flush=True)
        return target
    except Exception as error:
        print('  ! Crystal Fina movie soundtrack unavailable: '+type(error).__name__+': '+str(error),flush=True)
        return None


def author(view, start, end, duration):
    """Keep the native cooked Atom graph and retime its typed cached ranges.

    Templates refer to section objects, so disable donor cues there, retaining
    valid indices/dependency graphs. One native section carries the cave cue.
    The monotone transform updates cached evaluation ranges as well as sections.
    """
    import _ffr_crystal_cave as assets
    result = copy.deepcopy(view)
    sections = [e for e in result['Exports'] if e['ClassIndex'] < 0 and
                result['Imports'][-e['ClassIndex']-1]['ObjectName'] == 'MovieSceneAtomSection']
    if len(sections) != 5 or start != NATIVE_START or not start < end < NATIVE_END:
        raise ValueError('Unsupported native Crystal Fina Atom soundtrack template.')
    def tick(value):
        if value <= start: return value
        if value >= NATIVE_END: return value + end - NATIVE_END
        return start + round((value - start) * (end - start) / (NATIVE_END - start))
    def retime(value):
        if isinstance(value, list):
            for item in value: retime(item)
        elif isinstance(value, dict):
            if value.get('$type') == 'UAssetAPI.UnrealTypes.FFrameNumber, UAssetAPI':
                value['Value'] = tick(value['Value'])
            else:
                for item in value.values(): retime(item)
    active = []
    for section in sections:
        prop = assets.property_data(section, 'Sound')
        cue = result['Imports'][-prop['Value']-1]
        if cue['ObjectName'] == 'SE_BTL_SLB_FF7R_CLOUD_Cue': active.append(section)
        else: prop['Value'] = 0
    if len(active) != 1: raise ValueError('The native movie music section changed.')
    section, = active
    bounds = assets.property_data(section, 'SectionRange')['Value'][0]['Value']
    if (bounds['LowerBound']['Value']['Value'], bounds['UpperBound']['Value']['Value']) != (start, NATIVE_END):
        raise ValueError('The native music section range changed.')
    retime(result['Exports'])
    cue = result['Imports'][-assets.property_data(section, 'Sound')['Value']-1]
    result['Imports'][-cue['OuterIndex']-1]['ObjectName'] = CUE.replace('FFRS/Content/', '/Game/')
    cue['ObjectName'] = Path(CUE).name
    assets.set_value(section, 'bContinueSoundWhenSequenceIsEnd', False)
    # Keep native preloading and its cooked evaluation flags. The explicit
    # start offset is zero, so the song begins at its first sample.
    offset = copy.deepcopy(assets.property_data(section, 'PreRollFrames'))
    offset['Name'] = 'StartFrameOffset'; offset['Value'][0]['Name'] = 'StartFrameOffset'
    offset['Value'][0]['Value']['Value'] = 0
    section['Data'].append(offset)
    scene, = [e for e in result['Exports'] if e['ClassIndex'] < 0 and
              result['Imports'][-e['ClassIndex']-1]['ObjectName'] == 'MovieScene']
    playback = assets.property_data(scene, 'PlaybackRange')['Value'][0]['Value']
    playback['UpperBound']['Value']['Value'] = duration
    assets.names(result, [result['Imports'], result['Exports']])
    return result


def check_active_child(master, suffix='Effect_000'):
    """Reject a disabled parent: a valid sound child alone cannot make music play."""
    import _ffr_crystal_cave as assets
    sections=[]
    for i,e in enumerate(master['Exports'],1):
        for p in e.get('Data',[]) if isinstance(e.get('Data'),list) else []:
            if p['Name']=='SubSequence' and p['Value']<0:
                imp=master['Imports'][-p['Value']-1]
                if imp['ObjectName'].endswith('_'+suffix): sections.append(i)
    tracks=[e for e in master['Exports'] if isinstance(e.get('Data'),list)
            and any(p['Name']=='Sections' and any(x['Value'] in sections for x in p['Value']) for p in e['Data'])]
    if len(sections)!=1 or len(tracks)!=1 or any(p['Name']=='bIsEvalDisabled' and p['Value'] for p in tracks[0]['Data']):
        raise ValueError('The Crystal Fina soundtrack parent track is disabled or changed.')


def build(child, env, work, native, clone, start, end, duration):
    """Private embedded native recording avoids Mana decoding and BGM stream state."""
    import _ffr_crystal_cave as assets
    import ffbe_audio
    run, tool, usmap = env['run'], env['FFRDT'], env['USMAP']
    out = Path(env['OUT'])
    clip,subkey=recording(env)
    source=native(ffbe_audio.SHELL).with_suffix('.uexp').read_bytes();at=source.index(b'@UTF')
    source=source[at:at+int.from_bytes(source[at+4:at+8],'big')+8]
    acb=native_bank(source,clip.read_bytes(),subkey,Path(SHEET).name)
    bank=work/'native-cave-score.acb';bank.write_bytes(acb)
    plan=work/'native-cave-bank.json';plan.write_text(json.dumps({'legacyRoot':str(env['LEGACY']),'outRoot':str(out),
        'atomBanks':[{'from':ffbe_audio.SHELL,'to':SHEET,'acb':str(bank),'sha256':hashlib.sha256(acb).hexdigest(),
                      'cues':[{'id':1,'name':CUE_NAME,'durationMs':6400}]}]}))
    run([*tool,'patch',str(plan),'--usmap',usmap])
    clone(native(CUE_DONOR), CUE,
          [(Path(CUE_DONOR).name, Path(CUE).name),
           ('/Game/Sound/Cri/Bgm/BGM_PP/BGM_PP',SHEET.replace('FFRS/Content/','/Game/')),
           ('BGM_PP',Path(SHEET).name)])
    cue_asset = out / (CUE + '.uasset'); cue_json = work / 'cave-cue.json'
    run([*tool, 'tojson', str(cue_asset), str(cue_json), '--usmap', usmap])
    cue = json.loads(cue_json.read_text(encoding='utf-8-sig'))
    owner, = cue['Exports']
    assets.set_value(owner, 'CueName', CUE_NAME)
    for field in ('Duration','FirstWaveDuration'):
        if any(p['Name']==field for p in owner['Data']):assets.set_value(owner,field,6.4)
    assets.names(cue, cue['Exports'])
    cue_json.write_text(json.dumps(cue), encoding='utf-8')
    run([*tool, 'fromjson', str(cue_json), str(cue_asset), '--usmap', usmap])
    run([*tool,'tojson',str(cue_asset),str(cue_json),'--usmap',usmap])
    checked=json.loads(cue_json.read_text(encoding='utf-8-sig'))
    from _ffr_party_voices import import_name
    props={p['Name']:p['Value'] for p in checked['Exports'][0]['Data']}
    sheet=checked['Imports'][-props['CueSheet']-1]
    if (props['CueName']!=CUE_NAME or sheet['ObjectName']!=Path(SHEET).name
            or import_name(checked,sheet['OuterIndex'])!=SHEET.replace('FFRS/Content/','/Game/')):
        raise ValueError('The Fina music cue does not reference its private recording.')
    clone(native(SOUND), child, [('SEQ_Battle_440111_Sound_001', Path(child).name)])
    target = out / (child + '.uasset'); dump = work / 'cave-soundtrack.json'
    run([*tool, 'tojson', str(target), str(dump), '--usmap', usmap])
    before = json.loads(dump.read_text(encoding='utf-8-sig'))
    authored = author(before, start, end, duration)
    dump.write_text(json.dumps(authored), encoding='utf-8')
    run([*tool, 'fromjson', str(dump), str(target), '--usmap', usmap])
    run([*tool, 'tojson', str(target), str(dump), '--usmap', usmap])
    assets.check_level(authored, json.loads(dump.read_text(encoding='utf-8-sig')))
    print('  Crystal Fina: original cave music from 0:00; native HCA frames, private one-shot cue, no audio re-encoding.', flush=True)
