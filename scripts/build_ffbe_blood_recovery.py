"""Prepare Scartio's selected Blood Recovery layers, without bundling the library."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
LAYERS = (('back', '5014470', 40, 1), ('front', '5014480', 40, -1), ('flash', '5001960', 100, -2))


def build(engine, converter, bank, definition, work, output):
    sys.path.insert(0, str(ROOT / 'assets/existing_visions/payload'))
    sys.path.insert(0, str(converter))
    from _ffr_ffbe_library import Library
    from _ffr_native_skills import digest
    import to_ss6
    from ffbe_effects import acb_native
    from PIL import Image
    library = Library(engine)
    library.cache = work / 'library'
    library.cache.mkdir(parents=True, exist_ok=True)
    members = {}; layers = []
    for role, identity, start, depth in LAYERS:
        raw = library.conversion_archive(identity)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            doc = json.loads(archive.read('doc.json'))
            def texture(name):
                with Image.open(io.BytesIO(archive.read(name))) as image:
                    return image.convert('RGBA')
            to_ss6.load_texture = texture
            name = 'sephira_blood_' + role
            folder = work / role
            spec = to_ss6.convert(doc, str(folder), name, max_units=1000000,
                                  max_cell_size=128, min_frames=180)
        for animation in spec['animations']:
            for part in animation['parts'].values(): part.pop('PartsColor', None)
        audit = spec['conversionAudit']
        if audit['atlasPages'] != 1 or audit['droppedSpriteFrames'] or audit['shrunkSpriteFrames']:
            raise ValueError('Blood Recovery must retain every source sprite on each layer atlas.')
        members[role + '/spec.json'] = (json.dumps(spec, separators=(',', ':')) + '\n').encode()
        members[role + '/tex.bgra'] = (folder / 'tex.bgra').read_bytes()
        layers.append({'role': role, 'name': name, 'effectId': identity, 'start': start,
                       'length': len(doc['frames']), 'depth': depth, 'conversion': audit})
    source = bank.read_bytes()
    recordings = acb_native.recordings(source, [25], {25: 'se_magic_heal_1'})
    recording, = recordings
    wave = acb_native.awb_files(acb_native.utf(source)[1][0]['AwbFile'])[recording['sourceWaveId']]
    sha = hashlib.sha256(wave).hexdigest()
    audio = {'schema': 'ffr-audio-1', 'recordings': recordings,
             'cues': {'25': {'name': 'se_magic_heal_1', 'cueIndex': 24,
                             'durationMs': recording['durationMs']}},
             'waves': {str(recording['sourceWaveId']): {'sha256': sha}},
             'sourceBankSha256': hashlib.sha256(source).hexdigest()}
    members['audio.json'] = (json.dumps(audio, indent=2) + '\n').encode()
    members['needle.hca'] = wave  # shared audio adapter's single-recording payload contract
    native = json.loads(definition.read_text(encoding='utf-8-sig'))
    native = native.get('rows', native)
    native = next(r for r in native.values() if r['ID'] == 501530)
    manifest = {'schema': 1, 'name': 'sephira_blood_recovery', 'ability': 231688,
                'owner': 'Scartio', 'source': library.manifest['source'], 'layers': layers,
                'nativeDefinitionSha256': digest(native),
                'timeline': '100:5001930:2:4:0&40:5016130:1:1:0&40:5016120:2:1:0',
                'soundFrames': [41, 41], 'hitFrame': 100, 'sourceFps': 60,
                'converterSha256': hashlib.sha256(Path(to_ss6.__file__).read_bytes()).hexdigest(),
                'limits': ['Offline particle simulation; live FFBE parity is unverified.',
                           'Mesh cells resampled to 128 pixels; world sizes and every sprite frame retained.',
                           'Front/back layers use separate actors with small depth offsets; the flash is target anchored.'],
                'files': {k: hashlib.sha256(v).hexdigest() for k, v in members.items()}}
    members['manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, raw in members.items():
            info = zipfile.ZipInfo(name, (2026, 10, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, raw)
    print(json.dumps({'bytes': output.stat().st_size, 'layers': layers}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('engine', 'converter', 'bank', 'definition', 'work', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    build(**vars(args))
