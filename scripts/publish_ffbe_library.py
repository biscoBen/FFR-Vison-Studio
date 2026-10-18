"""Publish immutable optional library packs once, separately from Studio updates."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets/existing_visions/payload'))
from _ffr_ffbe_download import RELEASE_TAG
REPOSITORY='biscoBen/FFR-Vison-Studio'


def command(*args):return subprocess.check_output(['gh',*args],text=True)


def publish():
    directory=ROOT/'assets/ffbe_library';manifest=json.loads((directory/'manifest.json').read_bytes())
    expected={p['name']:p for p in manifest['packs']}
    raw=(directory/'manifest.json').read_bytes();expected['manifest.json']={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    result=subprocess.run(['gh','api',f'repos/{REPOSITORY}/releases/tags/{RELEASE_TAG}'],capture_output=True,text=True)
    if result.returncode:
        if '404' not in result.stderr:raise RuntimeError('Cannot inspect the independent library release.')
        with tempfile.TemporaryDirectory() as tmp:
            notes=Path(tmp)/'notes.txt';notes.write_text('Optional FFBE Memorial v208 animation and sound library. Downloaded only after choosing Download library in Studio. Packs are immutable and reused across app updates.\n',encoding='utf-8')
            command('release','create',RELEASE_TAG,'--repo',REPOSITORY,'--prerelease','--latest=false','--target',os.environ['COMMIT_SHA'],'--title','FFBE animation library v208 (optional download)','--notes-file',str(notes))
        release=json.loads(command('api',f'repos/{REPOSITORY}/releases/tags/{RELEASE_TAG}'))
    else:release=json.loads(result.stdout)
    existing={a['name']:a for a in release['assets']}
    missing=[]
    for name,record in expected.items():
        asset=existing.get(name)
        if asset:
            if asset['state']!='uploaded' or asset['size']!=record['bytes'] or asset.get('digest')!='sha256:'+record['sha256']:
                raise RuntimeError('Existing independent library asset differs: '+name)
        else:missing.append(name)
    def upload(name):
        path=directory/name
        with path.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
        if actual!=expected[name]['sha256']:raise ValueError('Source library asset changed: '+name)
        command('release','upload',RELEASE_TAG,str(path),'--repo',REPOSITORY)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(upload,missing))
    release=json.loads(command('api',f'repos/{REPOSITORY}/releases/tags/{RELEASE_TAG}'))
    actual={a['name']:a for a in release['assets']}
    for name,record in expected.items():
        assert actual[name]['state']=='uploaded' and actual[name]['size']==record['bytes']
        assert actual[name]['digest']=='sha256:'+record['sha256'],name
    print(f'Independent library ready: {len(expected)-1} immutable packs; {len(missing)} uploads this run.')


if __name__=='__main__':publish()
