"""Play the installed cave cue on a native Atom timeline; never reencode BGM."""
import copy
import json
from pathlib import Path

CUE_NAME = 'BGM_PP_DUNGEON_CAVE1'
CUE_DONOR = 'FFRS/Content/Sound/Cri/Bgm/BGM_PP/BGM_PP_BATTLE1_Cue'
CUE = 'FFRS/Content/Sound/Cri/Studio/Studio_FinaCaveMusic_Cue'
SOUND = 'FFRS/Content/Sequencer/Battle/Skill/440110/440111/Track/SEQ_Battle_440111_Sound_001'
NATIVE_START, NATIVE_END = 48000, 363503


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
    """Private cue references the installed BGM_PP sheet and streamed audio."""
    import _ffr_crystal_cave as assets
    run, tool, usmap = env['run'], env['FFRDT'], env['USMAP']
    out = Path(env['OUT'])
    clone(native(CUE_DONOR), CUE,
          [(Path(CUE_DONOR).name, Path(CUE).name)])
    cue_asset = out / (CUE + '.uasset'); cue_json = work / 'cave-cue.json'
    run([*tool, 'tojson', str(cue_asset), str(cue_json), '--usmap', usmap])
    cue = json.loads(cue_json.read_text(encoding='utf-8-sig'))
    owner, = cue['Exports']
    if assets.property_data(owner, 'CueName')['Value'] != 'BGM_PP_BATTLE1':
        raise ValueError('The native cave music cue template changed.')
    assets.set_value(owner, 'CueName', CUE_NAME)
    assets.set_value(owner, 'FirstWaveDuration', 3277372 / 48000)
    assets.names(cue, cue['Exports'])
    cue_json.write_text(json.dumps(cue), encoding='utf-8')
    run([*tool, 'fromjson', str(cue_json), str(cue_asset), '--usmap', usmap])
    clone(native(SOUND), child, [('SEQ_Battle_440111_Sound_001', Path(child).name)])
    target = out / (child + '.uasset'); dump = work / 'cave-soundtrack.json'
    run([*tool, 'tojson', str(target), str(dump), '--usmap', usmap])
    before = json.loads(dump.read_text(encoding='utf-8-sig'))
    authored = author(before, start, end, duration)
    dump.write_text(json.dumps(authored), encoding='utf-8')
    run([*tool, 'fromjson', str(dump), str(target), '--usmap', usmap])
    run([*tool, 'tojson', str(target), str(dump), '--usmap', usmap])
    assets.check_level(authored, json.loads(dump.read_text(encoding='utf-8-sig')))
