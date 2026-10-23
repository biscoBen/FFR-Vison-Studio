"""Original Memorial LB cues for managed visions; gameplay timing is untouched."""
from functools import lru_cache
import hashlib
import io
import json
import math
import copy
from pathlib import Path
import re
import zipfile

REVISION = 'memorial-v208-lb-2'


def validate(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        metadata = json.loads(archive.read('manifest.json'))
        expected = set(metadata.get('files', {})) | {'manifest.json'}
        if (metadata.get('schema') != 1 or metadata.get('revision') != REVISION
                or set(names) != expected or len(names) != len(expected)
                or len(metadata.get('profiles', {})) != 30):
            raise ValueError('Invalid Sephira LB audio archive.')
        files = {}
        for name, digest in metadata['files'].items():
            if name not in ('audio/SE.json', 'audio/System.json') and not re.fullmatch(r'audio/samples/[0-9a-f]{64}\.hca', name):
                raise ValueError('Invalid Sephira LB audio path.')
            data = archive.read(name)
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('Sephira LB recording checksum mismatch: ' + name)
            files[name] = data
        for name in ('SE', 'System'):
            doc = json.loads(files['audio/' + name + '.json'])
            if doc.get('schema') != 'ffr-audio-1' or not doc.get('recordings'):
                raise ValueError('Missing Sephira LB recordings.')
            for sample in doc['waves'].values():
                if 'audio/samples/' + sample['sha256'] + '.hca' not in files:
                    raise ValueError('Missing Sephira LB sample.')
        return metadata, files


@lru_cache(maxsize=1)
def payload():
    return validate(Path(__file__).with_name('sephira_lb_audio.zip').read_bytes())


def selected(unit, skill):
    import _ffr_sephira
    member = _ffr_sephira.runtime_membership(unit)
    if member is None: return None
    metadata, _ = payload()
    profile = metadata['profiles'].get(member['preset'])
    if (profile is None or str((unit.get('ffbe') or {}).get('id')) != profile['form']
            or str(skill.get('ffbe_lb_id', profile['lbId'])) != profile['lbId']
            or skill.get('presentation', 'ffbe') != 'ffbe'
            or skill.get('audio') == 'experimental'
            or any(skill.get(k) for k in ('audio_bank', 'audio_system_bank'))
            or skill.get('sephiraAudio') == 1 and skill.get('audio') == 'none'):
        return None
    return profile


def prepare(unit, skill, source, table):
    import ffbe_audio
    profile = selected(unit, skill)
    if profile is None: return ffbe_audio.prepare(unit, skill, source, table)
    metadata, files = payload()
    root = Path(ffbe_audio.ROOT) / 'build/sephira-lb-audio'
    # Content-addressed shared samples are small and independent of the optional
    # animation library. Repair a missing/changed cache file, never a game asset.
    for name, raw in files.items():
        path = root / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != metadata['files'][name]:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    settings = dict(skill, audio='native', audio_codec='host',
                    audio_bank=str(root / 'audio/SE.json'), audio_system_bank=str(root / 'audio/System.json'))
    # The sprite's effect-group sound clock is independent of regional damage
    # formulas, movement and support types. Do not overwrite source hit data.
    audible = [s for s in profile['sounds'] if s['flags'] == ['1']]
    sound_source = dict(source or {}, sounds=audible)
    bank, events = ffbe_audio.prepare(unit, settings, sound_source, table)
    print(f"  {unit['key']}: FFBE LB audio, {len(audible)} attack cues + " +
          ('opening cue' if skill.get('lb_charge', True) else 'opening disabled'))
    if profile['status'] == 'opening_only': print('  ! ' + unit['key'] + ': ' + profile['reason'])
    return bank, events


def align_reactions(plan, unit, skill, sounds):
    """Place approved impact clips on existing application keys, never add hits.

    An alignment hint survives the engine audio adapter's recording selection.
    All ordinary source soundtracks and non-managed units retain their clocks.
    """
    if selected(unit, skill) is None: return plan
    aligned = [s for s in sounds if s.get('alignment') == 'reaction']
    if not aligned: return plan
    result = copy.deepcopy(plan)
    reactions = sorted({e['time'] for e in result['events'] if e['set']['EventType'] == 'OtherReaction'})
    if not reactions: raise ValueError('No existing LB application marker for the requested sound.')
    for sound in aligned:
        def matches(event):
            fields = event['set']
            return (fields['EventType'] == 'SoundPlayHitSound'
                    and fields['Sound_PlayHitSound_CueSheetName'] == sound['bank']
                    and fields['Sound_PlayHitSound_playLabel'] == sound['cueName'])
        result['events'] = [e for e in result['events'] if not matches(e)]
        for tick in reactions:
            result['events'].append({'time': tick, 'set': {'EventType': 'SoundPlayHitSound',
                'Sound_PlayHitSound_CueSheetName': sound['bank'],
                'Sound_PlayHitSound_playLabel': sound['cueName']}})
        end = reactions[-1] + math.ceil(sound['durationMs'] * 24)
        result['duration'] = max(result['duration'], end + 2400)
    result['events'].sort(key=lambda e: e['time'])
    return result
