"""Package only the selected visions' original Memorial LB recordings and cues.

Requires decoded v208 masters, SE/System.acb, and the compatible engine tools.
The three HFR recordings need offline conversion to mono HCA without HFR; pass
their checksum-reviewed replacements as <cue ID>-reencoded.hca. No conversion
or download is performed on the player's computer.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
APK_SHA = '9d21fc8b61c9900eaacb1c2ddef2cabcad1e97d2dc720be16ac09b06fc0086b4'
CONVERTED = {91, 96, 215}


def build(source, engine_tools, converted, output):
    sys.path.insert(0, str(engine_tools))
    from ffbe_effects.acb_cues import cues, utf
    from ffbe_effects import acb_native, hca_host
    apk = source / 'FFBE-Memorial-EN-Global-Events-v208.apk'
    with apk.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != APK_SHA:
            raise ValueError('This audio source is not the supplied v208 APK.')
    catalog = json.loads((ROOT / 'assets/sephira_visions/catalog.json').read_bytes())
    lbs = {r['PR2HIc71']: r for r in json.loads((source / 'F_LIMITBURST_MST-memorial.json').read_bytes())}
    groups = {r['qIy86WvJ']: r for r in json.loads((source / 'F_EFFECT_GROUP_MST-memorial.json').read_bytes())}
    profiles = {}; selected = set(); files = {}; banks = {}
    for preset in catalog['presets']:
        form = preset['profile']['ffbe']['id']; lb = lbs.get(form)
        # Fran's second variant is the selected Shatterheart damage animation;
        # its first variant contains the old, silent initial-hit presentation.
        variant = 1 if preset['id'] == 'fran' else 0
        sounds = []; timeline = []
        if lb:
            timeline = lb['5A8SmwyC'].split('@')[variant].split('&')
            for entry in timeline:
                offset, gid, *_ = entry.split(':')
                for sound in filter(None, groups[gid].get('1fVZ3rKd', '').split(',')):
                    frame, cue, *flags = sound.split(':')
                    if not cue: raise ValueError('Missing source cue ID')
                    sounds.append({'frame': int(offset) + int(frame), 'cueId': int(cue),
                                   'groupId': gid, 'groupFrame': int(offset),
                                   'cueFrame': int(frame), 'flags': flags})
            sounds.sort(key=lambda e: e['frame'])
        # Flag 2 is a stop instruction, not a recording to play. In these LBs
        # every stop refers to a cue never started by the selected variant.
        starts = {s['cueId'] for s in sounds if s['flags'] == ['1']}
        stops = {s['cueId'] for s in sounds if s['flags'] == ['2']}
        if starts & stops or any(s['flags'] not in (['1'], ['2']) for s in sounds):
            raise ValueError('LB needs an explicit stop/flag adapter: ' + preset['id'])
        selected.update(starts)
        profiles[preset['id']] = {'form': form, 'lbId': form, 'name': preset['name'],
            'sourceName': lb['G4L0YIB2'] if lb else None, 'variant': variant,
            'timeline': timeline, 'sounds': sounds,
            'status': 'original_cues' if starts else 'opening_only',
            'reason': None if starts else ('The custom Crystal Fina sequence has no original FFBE LB audio.'
                if preset['id'] == 'crystal_fina' else 'This exact form/LB is absent from the supplied Memorial masters.')}
    for bank_name, ids in [('SE', selected), ('System', {45})]:
        path = source / 'memorial-source' / (bank_name + '.acb'); raw = path.read_bytes()
        index = cues(path); waves = acb_native.awb_files(utf(raw)[1][0]['AwbFile'])
        recordings = acb_native.recordings(raw, ids - {355}, {cid: index[cid]['name'] for cid in ids})
        # Ice Slash has three random alternatives, each with two simultaneous
        # waves. The reviewed offline mixes retain both layers in each variant.
        if 355 in ids:
            for variation in range(3):
                sample = (converted / f'355-v{variation + 1}-reencoded.hca').read_bytes()
                count = int.from_bytes(sample[16:20], 'big') * 1024 - int.from_bytes(sample[20:22], 'big') - int.from_bytes(sample[22:24], 'big')
                rate = int.from_bytes(sample[13:16], 'big')
                recordings.append({'sourceCueId': 355, 'variation': variation,
                    'sourceWaveIndex': -1, 'sourceWaveId': 100000 + variation,
                    'name': index[355]['name'] + f'__v{variation + 1}',
                    'durationMs': math.ceil(count * 1000 / rate), 'sourceEncodeType': 2,
                    'channels': sample[12], 'sampleRate': rate, 'samples': count,
                    'conversion': {'method': 'Original simultaneous layers mixed per random variant; VGAudio 2.2.1 Highest HCA',
                                   'layers': 2, 'mixGain': 0.5}})
        manifest = {'schema': 'ffr-audio-1', 'cues': {}, 'recordings': recordings,
                    'waves': {}, 'sourceBankSha256': hashlib.sha256(raw).hexdigest()}
        for cid in sorted(ids):
            entry = index[cid]
            manifest['cues'][str(cid)] = {'name': entry['name'], 'cueIndex': entry['cueIndex'],
                'durationMs': max(r['durationMs'] for r in recordings if r['sourceCueId'] == cid)}
        for recording in recordings:
            cid = recording['sourceCueId']; wid = recording['sourceWaveId']
            sample = ((converted / f"355-v{recording['variation'] + 1}-reencoded.hca").read_bytes()
                      if cid == 355 else waves[wid])
            original_hash = hashlib.sha256(sample).hexdigest()
            if bank_name == 'SE' and cid in CONVERTED or bank_name == 'System' and cid == 45:
                sample = (converted / f'{cid}-reencoded.hca').read_bytes()
                samples = int.from_bytes(sample[16:20], 'big') * 1024 - int.from_bytes(sample[20:22], 'big') - int.from_bytes(sample[22:24], 'big')
                rate = int.from_bytes(sample[13:16], 'big')
                if sample[12] != recording['channels'] or rate != recording['sampleRate'] or samples != recording['samples']:
                    raise ValueError('Converted recording changed channels/rate/sample count')
                recording['conversion'] = {'sourceSha256': original_hash,
                    'method': 'FFmpeg PCM decode; VGAudio 2.2.1 Highest HCA encode without HFR',
                    'sourceDelaySamples': 128, 'sampleCount': samples}
                recording['sourceEncodeType'] = 2
                recording['durationMs'] = math.ceil(samples * 1000 / rate)
            hca_host.validate_layout(sample)
            digest = hashlib.sha256(sample).hexdigest()
            manifest['waves'][str(wid)] = {'sha256': digest}
            files['audio/samples/' + digest + '.hca'] = sample
        files['audio/' + bank_name + '.json'] = json.dumps(manifest, separators=(',', ':')).encode()
        banks[bank_name] = manifest['sourceBankSha256']
    metadata = {'schema': 1, 'revision': 'memorial-v208-lb-1', 'sourceApkSha256': APK_SHA,
                'sourceMasters': {name: hashlib.sha256((source / (name + '-memorial.json')).read_bytes()).hexdigest()
                                  for name in ('F_LIMITBURST_MST', 'F_EFFECT_GROUP_MST')},
                'sourceBanks': banks, 'profiles': profiles,
                'files': {k: hashlib.sha256(v).hexdigest() for k, v in sorted(files.items())}}
    files['manifest.json'] = json.dumps(metadata, indent=2, ensure_ascii=False).encode()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 23, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    print(len(profiles), 'visions;', sum(p['status'] == 'original_cues' for p in profiles.values()),
          'original LB soundtracks;', len(selected), 'attack cues;', len(files), 'files;', output.stat().st_size, 'bytes')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'engine-tools', 'converted', 'output'): p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); build(a.source, a.engine_tools, a.converted, a.output)
