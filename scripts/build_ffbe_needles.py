"""Reproduce the isolated FFBE visual payload from the preserved source files.

Pass the tools/ffbe_effects directory at the converter commit in provenance.json.
The converter is a development dependency; Studio ships only its checked output.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'scripts/fixtures/ffbe_needles'
NAME = 'ffbe_needles_test'


def compose(single, rows):
    spawns = [list(map(int, s.split(':'))) for s in rows['F_EFFECT_GROUP_MST'][0]['5A8SmwyC'].split(',')]
    frames = [[] for _ in range(max(s[0] for s in spawns) + len(single['frames']))]
    for start, effect, reverse, reserved, xm, ym, x, y in spawns:
        if effect != 1002460 or reverse != 99999999 or (xm, ym) != (2, 2):
            raise ValueError('The source effect placement requires another adapter.')
        for i, parts in enumerate(single['frames']):
            for part in parts:
                p = copy.deepcopy(part)
                p['pos'][0] += x * single['pixelsPerUnit']
                p['pos'][1] -= y * single['pixelsPerUnit']
                frames[start+i].append(p)
    return {**single, 'frameCount': len(frames), 'frames': frames}


def build(converter, work, output):
    provenance = json.loads((SOURCE / 'provenance.json').read_bytes())
    for name, digest in provenance['files'].items():
        if hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() != digest:
            raise ValueError('FFBE source checksum mismatch: ' + name)
    if hashlib.sha256(Path(__file__).with_name('ffbe_model_placement.py').read_bytes()).hexdigest() != provenance['placementAdapterSha256']:
        raise ValueError('The positioning adapter differs from the retained conversion provenance.')
    sys.path.insert(0, str(converter))
    import ibmb, render
    from ffbe_model_placement import install
    install(ibmb)
    render.render(str(SOURCE / 'atk_nail1_white.bmb'), str(work / 'single'), [str(SOURCE)],
                  size=512, step=1, max_frames=30, particles=64, doc=True, ppu_fixed=2.4)
    single = json.loads((work / 'single/doc.json').read_bytes())
    doc = compose(single, json.loads((SOURCE / 'source-rows.json').read_bytes()))
    sys.path.insert(0, str(converter))
    import to_ss6
    spec = to_ss6.convert(doc, str(work / 'ss6'), NAME, min_frames=270)
    # Build 15 cannot serialize the newer object-valued PartsColor keys.
    # Identity Mul affects material selection, not source colors; retain the
    # older writer's standard Mix/Add material path for this prototype.
    for anim in spec['animations']:
        for part in anim['parts'].values(): part.pop('PartsColor', None)
    audit = spec['conversionAudit']
    if audit['atlasPages'] != 1 or audit['droppedSpriteFrames'] or audit['shrunkSpriteFrames']:
        raise ValueError('The prototype must retain every source particle on one atlas.')
    files = {'spec.json': (json.dumps(spec, indent=1) + '\n').encode(),
             'tex.bgra': (work / 'ss6/tex.bgra').read_bytes(),
             'audio.json': (SOURCE / 'audio.json').read_bytes(),
             'needle.hca': (SOURCE / 'needle.hca').read_bytes()}
    manifest = {'schema': 1, 'name': NAME, 'source': provenance, 'conversion': audit,
                'files': {k: hashlib.sha256(v).hexdigest() for k, v in files.items()}}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in {**files, 'manifest.json': (json.dumps(manifest, indent=2)+'\n').encode()}.items():
            info = zipfile.ZipInfo(name, (2026, 10, 17, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    print(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--converter', required=True, type=Path)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=ROOT/'assets/existing_visions/payload/ffbe_needles.zip')
    args = parser.parse_args()
    build(args.converter, args.work, args.output)
