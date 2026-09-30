"""Verify bundled files, or explicitly refresh manifests after reviewed source edits."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / 'assets/crystal_fina'


def manifest(root, feature=None):
    files = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in sorted(root.rglob('*')) if path.is_file() and path != root / 'manifest.json'
             and '__pycache__' not in path.parts and path.suffix != '.pyc'}
    result = {'schema': 1, 'files': files}
    if feature:
        result['feature'] = feature
    return result


def verify(update=False):
    payload = ROOT / 'engine/payload'
    for directory, feature in ((payload, None), (ROOT, 'custom.crystal_fina.v1')):
        expected = manifest(directory, feature)
        target = directory / 'manifest.json'
        if update:
            target.write_text(json.dumps(expected, indent=2) + '\n', encoding='utf-8')
        elif json.loads(target.read_text(encoding='utf-8')) != expected:
            raise ValueError('Crystal Fina bundle differs from its manifest: ' + str(target))
    profile = json.loads((ROOT / 'profile.json').read_text(encoding='utf-8'))
    assert profile['ffbe']['id'] == '99887755552703'
    assert profile['lb_custom']['en'] == 'Crystal Restoration'
    return len(manifest(ROOT)['files'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update', action='store_true')
    args = parser.parse_args()
    print(f'Crystal Fina: {verify(args.update)} files verified.')
