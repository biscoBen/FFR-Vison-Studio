"""Verify the managed native-vision extension, or refresh after reviewed edits."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / 'assets/existing_visions'


def verify(update=False):
    for root in (ROOT / 'payload', ROOT):
        files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(root.rglob('*')) if p.is_file() and p != root / 'manifest.json'
                 and '__pycache__' not in p.parts and p.suffix != '.pyc'}
        value = {'schema': 1, 'files': files}
        manifest = root / 'manifest.json'
        if update: manifest.write_text(json.dumps(value, indent=2) + '\n')
        elif json.loads(manifest.read_bytes()) != value: raise ValueError('Existing vision bundle checksum mismatch.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--update', action='store_true')
    verify(parser.parse_args().update)
    print('Existing vision extension verified.')
