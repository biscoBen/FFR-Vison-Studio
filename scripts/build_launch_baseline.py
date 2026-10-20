"""Build small launch comparison metadata from the previously supplied demo reference."""
import argparse
import gzip
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
PAYLOAD = ROOT / 'assets/existing_visions/payload'
sys.path.insert(0, str(PAYLOAD))
import _ffr_launch as launch


def build(reference, rows, catalog, output):
    native = json.loads((reference / 'native-container-index.json').read_text(encoding='utf-8-sig'))
    containers = {r['name']: {'size': r['bytes'], **({'sha256': r['utocSha256']} if r['utocSha256'] else {})}
                  for r in native['nativeContainers']}
    identity = {'schema': 1, 'sha256': launch.digest(containers), 'containers': containers}
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        legacy = reference / 'legacy'
        (root/'extracted').mkdir()
        # No raw copyrighted assets are copied into the packaged metadata.
        try: (root/'extracted/legacy').symlink_to(legacy, target_is_directory=True)
        except OSError: raise RuntimeError('Run this metadata builder where source directory links are supported.')
        for source in rows.glob('*.json'):
            matches = list((legacy/'FFRS/Content/Datatable').rglob(source.stem+'.uasset'))
            if len(matches) != 1: continue
            relative = matches[0].relative_to(legacy/'FFRS/Content/Datatable').with_suffix('.json')
            if not any(('Datatable/'+relative.as_posix()).startswith(s) for s in launch.TABLE_SCOPE): continue
            target = root/'extracted/rows'/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        shutil.copy2(reference/'game-asset-index.txt', root/'extracted/utoc_filelist.tsv')
        result = launch.summarize(root, identity, json.loads(catalog.read_text(encoding='utf-8-sig')))
        result['source'] = 'User-supplied Skill-Routing-Reference-20261016-213210-7ca510; native source only'
        result['adoptionRows'] = {'extracted/rows/'+p.relative_to(root/'extracted/rows').as_posix(): launch.transfer.sha(p)
                                  for p in (root/'extracted/rows').rglob('*.json')}
        output.write_bytes(gzip.compress(json.dumps(result, ensure_ascii=False, sort_keys=True).encode(), mtime=0))
        print(json.dumps({'bytes': output.stat().st_size,'tables':len(result['tables']),'skills':len(result['skills']),
                          'assets':len(result['inventory']),'timelineFiles':len(result['timelineFiles'])}))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',type=Path,required=True);p.add_argument('--rows',type=Path,required=True)
    p.add_argument('--catalog',type=Path,required=True);p.add_argument('--output',type=Path,default=PAYLOAD/'launch_demo.json.gz')
    a=p.parse_args();build(a.reference,a.rows,a.catalog,a.output)
